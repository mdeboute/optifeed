#!/bin/bash
set -e
echo "Starting service: $SERVICE"

if [ "$SERVICE" = "fastapi" ]; then
    uv run uvicorn optifeed.api.app:app --host 0.0.0.0 --port 8000 --reload
elif [ "$SERVICE" = "worker" ]; then
    uv run -m optifeed.worker.worker
elif [ "$SERVICE" = "scheduler" ]; then
    echo "0 12 * * * PYTHONPATH=/app uv run -m optifeed.pipeline >> /proc/1/fd/1 2>&1" > /etc/cron.d/pipeline-cron
    chmod 0644 /etc/cron.d/pipeline-cron
    crontab /etc/cron.d/pipeline-cron
    cron -f
else
    echo "Unknown service: $SERVICE"
    exit 1
fi
