import json
import time

import google.generativeai as genai
import pika

from optifeed.telegram.telegram import send_telegram_message
from optifeed.utils.config import (
    ADMIN_USER,
    GOOGLE_API_KEY,
    LLM_MODEL,
    RABBIT_HOST,
    RABBIT_PASS,
    RABBIT_USER,
    TELEGRAM_BOT_USERNAME,
)
from optifeed.utils.logger import logger

# --- Gemini model setup
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(LLM_MODEL)

# --- Prompts
BASE_PROMPT = """
You are a helpful assistant that answers questions based on the provided context.
You will receive a question and you should provide a concise and accurate answer.
Make sure to keep your responses short and to the point.
If the question is not clear, ask for clarification.
Answer with a little bit of humor when you can.
"""


# --- Gemini interaction
def ask_something(prompt: str) -> str:
    """Ask a question to the Gemini model and return the response."""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"❌ Gemini API error: {e}")
        return "❌ Error processing your request. Please try again later."


# --- Task processing
def process_task(task: dict):
    """Process a task from RabbitMQ."""
    logger.debug(f"🚀 Processing task: {task}")
    match task.get("type"):
        case "ask":
            query = task["data"].get("message", {}).get("text", "")
            if TELEGRAM_BOT_USERNAME not in query:
                logger.debug("🔍 Query ignored: does not mention bot username.")
                return

            if query.startswith("/ping"):
                send_telegram_message("🏓 Pong!")
            else:
                prompt = BASE_PROMPT
                if task.get("data").get("message").get("from").get("id") == int(
                    ADMIN_USER
                ):
                    prompt += "\nYou're talking to the admin so call it 'my lord' or other fancy name/title."
                response = ask_something(f"{prompt}\n\nQuestion: {query}")
                send_telegram_message(response)

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
