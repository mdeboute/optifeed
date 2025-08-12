import json
import time
from collections import defaultdict
from typing import Dict, List

import pika
from pydantic_ai import ModelMessage

from optifeed.telegram.telegram import send_telegram_message
from optifeed.utils.config import (
    ADMIN_USER,
    RABBIT_HOST,
    RABBIT_PASS,
    RABBIT_USER,
    TELEGRAM_BOT_USERNAME,
)
from optifeed.utils.llm import ask_something
from optifeed.utils.logger import logger

# In-memory storage for conversation history (per user)
# Key: user_id, Value: list of ModelMessage objects
conversation_history: Dict[int, List[ModelMessage]] = defaultdict(list)

# Context management settings
MAX_CONTEXT_LENGTH = 8000  # Maximum characters in context
MIN_MESSAGES_TO_KEEP = 4  # Always keep at least this many recent messages
MAX_MESSAGES = 50  # Hard limit on message count


def estimate_context_length(messages: List[ModelMessage]) -> int:
    """Estimate the total character count of the conversation history."""
    return sum(len(msg.content) for msg in messages)


def trim_history_by_context(messages: List[ModelMessage]) -> List[ModelMessage]:
    """Trim history to fit within context length while preserving recent messages."""
    if not messages:
        return messages

    # Always keep minimum recent messages regardless of length
    if len(messages) <= MIN_MESSAGES_TO_KEEP:
        return messages

    current_length = estimate_context_length(messages)

    # If under limit, return as-is
    if current_length <= MAX_CONTEXT_LENGTH:
        return messages

    # Start from the end (most recent) and work backwards
    trimmed_messages = []
    current_length = 0

    # Keep recent messages that fit within context
    for message in reversed(messages):
        message_length = len(message.content)
        if current_length + message_length <= MAX_CONTEXT_LENGTH:
            trimmed_messages.insert(0, message)
            current_length += message_length
        else:
            # If we have enough messages, stop here
            if len(trimmed_messages) >= MIN_MESSAGES_TO_KEEP:
                break

    # Ensure we have at least MIN_MESSAGES_TO_KEEP
    if (
        len(trimmed_messages) < MIN_MESSAGES_TO_KEEP
        and len(messages) >= MIN_MESSAGES_TO_KEEP
    ):
        trimmed_messages = messages[-MIN_MESSAGES_TO_KEEP:]

    logger.debug(
        f"🧹 Trimmed history: {len(messages)} -> {len(trimmed_messages)} messages, "
        f"{estimate_context_length(messages)} -> {estimate_context_length(trimmed_messages)} chars"
    )

    return trimmed_messages


def get_user_history(user_id: int) -> List[ModelMessage]:
    """Get conversation history for a specific user."""
    return conversation_history[user_id]


def add_to_history(user_id: int, role: str, content: str):
    """Add a message to user's conversation history with intelligent trimming."""
    message = ModelMessage(role=role, content=content)
    conversation_history[user_id].append(message)

    # Apply context-aware trimming
    conversation_history[user_id] = trim_history_by_context(
        conversation_history[user_id]
    )

    # Hard limit on message count as backup
    if len(conversation_history[user_id]) > MAX_MESSAGES:
        conversation_history[user_id] = conversation_history[user_id][-MAX_MESSAGES:]


def clear_user_history(user_id: int):
    """Clear conversation history for a specific user."""
    conversation_history[user_id] = []


# --- Task processing
def process_task(task: dict):
    """Process a task from RabbitMQ."""
    logger.debug(f"🚀 Processing task: {task}")
    match task.get("type"):
        case "ask":
            message_data = task["data"].get("message", {})
            query = message_data.get("text", "")
            user_id = message_data.get("from", {}).get("id")

            if not user_id:
                logger.warning("⚠️ No user ID found in message")
                return

            if TELEGRAM_BOT_USERNAME not in query:
                logger.debug("🔍 Query ignored: does not mention bot username.")
                return

            # Handle special commands
            if query.startswith("/ping"):
                response = "🏓 Pong!"
                send_telegram_message(response)
                # Don't add ping/pong to history
                return
            elif query.startswith("/clear"):
                clear_user_history(user_id)
                response = "🧹 Conversation history cleared!"
                send_telegram_message(response)
                return
            elif query.startswith("/history"):
                history = get_user_history(user_id)
                if not history:
                    response = "📝 No conversation history yet."
                else:
                    context_length = estimate_context_length(history)
                    response = f"📝 History: {len(history)} messages, ~{context_length} characters"
                send_telegram_message(response)
                return

            # Get user's conversation history
            user_history = get_user_history(user_id)

            # Prepare the prompt
            prompt = query
            if user_id == int(ADMIN_USER):
                prompt += "\nYou're talking to the admin so call it 'my lord' or other fancy name/title."

            # Add user's question to history before processing
            add_to_history(user_id, "user", query)

            try:
                # Ask the LLM with conversation history
                result = ask_something(
                    f"Question: {prompt}", message_history=user_history
                )
                response = result.output

                # Add assistant's response to history
                add_to_history(user_id, "assistant", response)

                # Send response
                send_telegram_message(response)

                # Log context info
                final_history = get_user_history(user_id)
                context_length = estimate_context_length(final_history)
                logger.info(
                    f"✅ Processed question for user {user_id}: {len(final_history)} messages, "
                    f"~{context_length} chars context"
                )

            except Exception as e:
                logger.error(f"❌ Error processing LLM request: {e}", exc_info=True)
                error_response = (
                    "❌ Sorry, I encountered an error processing your request."
                )
                send_telegram_message(error_response)

        case "alert":
            message = task.get("message", "⚠️ Empty message")
            send_telegram_message(message)
            logger.info(f"✅ Sent alert to chat_id {task.get('chat_id')}")

        case _:
            logger.warning(f"⚠️ Unknown task type: {task.get('type')}")


# --- RabbitMQ consumer callback
def callback(ch, method, properties, body):
    """Callback function for RabbitMQ messages."""
    try:
        task = json.loads(body)
        process_task(task)
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to decode JSON task: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error processing task: {e}", exc_info=True)
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)


# --- Worker start with retry
def start_worker():
    """Start the RabbitMQ worker with retry logic."""
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    params = pika.ConnectionParameters(RABBIT_HOST, 5672, "/", credentials)

    for attempt in range(1, 16):
        try:
            logger.info(
                f"🔌 Trying to connect to RabbitMQ at {RABBIT_HOST}:5672 (attempt {attempt})..."
            )
            connection = pika.BlockingConnection(params)
            logger.info("✅ Connected to RabbitMQ.")
            break
        except pika.exceptions.AMQPConnectionError as e:
            logger.warning(f"⚠️ Connection failed: {e}, retrying in 3s...")
            time.sleep(3)
    else:
        logger.critical(
            "❌ Failed to connect to RabbitMQ after several attempts. Exiting."
        )
        return

    channel = connection.channel()
    channel.queue_declare(queue="tasks")
    channel.basic_consume(queue="tasks", on_message_callback=callback)
    logger.info("🐇 Worker started. Waiting for tasks...")
    channel.start_consuming()


if __name__ == "__main__":
    start_worker()
