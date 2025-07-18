import os
import subprocess
import time

import schedule

from optifeed.utils.config import ALERTS_ENABLED_FILE
from optifeed.utils.logger import logger


def run_summary():
    logger.info("📅 Running daily_summary")
    try:
        subprocess.run(
            ["uv", "run", "-m", "optifeed.pipeline.daily_summary"], check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ daily_summary failed: {e}")


def run_alerts():
    if not os.path.exists(ALERTS_ENABLED_FILE):
        logger.info("⚠️ Alerts are disabled. Skipping...")
        return
    logger.info("📡 Running alerts")
    try:
        subprocess.run(["uv", "run", "-m", "optifeed.pipeline.alerts"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ alerts failed: {e}")


# Schedule the jobs
schedule.every().day.at("12:00").do(run_summary)
schedule.every().day.at("06:00").do(run_alerts)
schedule.every().day.at("18:00").do(run_alerts)

logger.info("🗓️ Scheduler started. Waiting for jobs...")

while True:
    schedule.run_pending()
    time.sleep(30)
