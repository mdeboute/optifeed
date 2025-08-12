import subprocess
import time

import schedule

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
    logger.info("📡 Running alerts")
    try:
        subprocess.run(["uv", "run", "-m", "optifeed.pipeline.alerts"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ alerts failed: {e}")


# Schedule the jobs
schedule.every().day.at("14:00").do(run_summary)
schedule.every().day.at("14:00").do(run_alerts)

logger.info("🗓️ Scheduler started. Waiting for jobs...")

while True:
    schedule.run_pending()
    time.sleep(30)
