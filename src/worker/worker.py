import json

import pika

from telegram.telegram import send_telegram_message
from utils.config import RABBIT_HOST, RABBIT_PASS, RABBIT_USER
from utils.logger import logger


def process_task(task: dict):
    logger.debug(f"🚀 Processing task: {task}")

    task_type = task.get("type")
    if task_type == "ask":
        query = task.get("query")
        if query and query.startswith("/"):
            send_telegram_message(f"❓ Command received: {query}")
    elif task_type == "alert":
        send_telegram_message(task.get("message", "⚠️ Empty message"))
        logger.info(f"✅ Sent alert to chat_id {task.get('chat_id')}")
    else:
        logger.warning(f"⚠️ Unknown task type: {task_type}")


def callback(ch, method, properties, body):
    try:
        task = json.loads(body)
        process_task(task)
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to decode JSON task: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error processing task: {e}", exc_info=True)
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)


def start_worker():
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(RABBIT_HOST, 5672, "/", credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue="tasks")
    channel.basic_consume(queue="tasks", on_message_callback=callback)
    logger.info("🐇 Worker started. Waiting for tasks...")
    channel.start_consuming()


if __name__ == "__main__":
    start_worker()
