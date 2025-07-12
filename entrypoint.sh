#!/bin/bash
set -e

if [ -z "$SERVICE" ]; then
  echo "❌ SERVICE environment variable is not set!"
  exit 1
fi

echo "🚀 Starting service: $SERVICE"

# Vérifie que uv est dispo
if ! command -v uv &> /dev/null; then
  echo "❌ 'uv' not found. Make sure it's installed and in PATH."
  exit 1
fi

case "$SERVICE" in

  fastapi)
    uv run uvicorn optifeed.api.app:app --host 0.0.0.0 --port 8100
    ;;

  worker)
    uv run -m optifeed.worker.worker
    ;;

  scheduler)
    echo "🗓️ Setting up cron jobs for summary and alerts..."

    cat <<EOF > /etc/cron.d/pipeline-cron
# Set PATH for uv and Python binaries
PATH=/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Daily summary at noon
0 12 * * * root uv run -m optifeed.pipeline.daily_summary >> /proc/1/fd/1 2>&1

# Alerts at 6am and 6pm
0 6  * * * root uv run -m optifeed.pipeline.alerts >> /proc/1/fd/1 2>&1
0 18 * * * root uv run -m optifeed.pipeline.alerts >> /proc/1/fd/1 2>&1
EOF

    chmod 0644 /etc/cron.d/pipeline-cron

    echo "⏱️ Starting cron daemon..."
    cron -f
    ;;

  *)
    echo "❌ Unknown service: $SERVICE"
    exit 1
    ;;

esac
echo "✅ Service $SERVICE started successfully."
