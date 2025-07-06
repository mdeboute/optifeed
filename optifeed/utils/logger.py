import sys

from loguru import logger

from optifeed.utils.config import LOG_FILE

logger.remove()  # remove default handler

logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    backtrace=True,
    diagnose=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)

logger.add(
    LOG_FILE,
    rotation="1 MB",
    retention="7 days",
    level="DEBUG",
    backtrace=True,
    diagnose=True,
    format="{time:YYYY-MM-DD HH:mm:ss} | {name}:{line} - {level} - {message}",
)
