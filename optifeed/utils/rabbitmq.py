import json

import pika

from optifeed.utils.config import RABBIT_HOST, RABBIT_PASS, RABBIT_USER
from optifeed.utils.logger import logger


def publish_task(task: dict):
    try:
        with pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBIT_HOST,
                credentials=pika.PlainCredentials(RABBIT_USER, RABBIT_PASS),
            )
        ) as connection:
            channel = connection.channel()
            channel.queue_declare(queue="tasks")
            channel.basic_publish(
                exchange="",
                routing_key="tasks",
                body=json.dumps(task, ensure_ascii=False),
                properties=pika.BasicProperties(delivery_mode=2),  # persistent
            )
            logger.debug(f"📤 Published task to RabbitMQ: {task}")

    except Exception as e:
        logger.error(f"❌ Failed to publish task to RabbitMQ: {e}", exc_info=True)
