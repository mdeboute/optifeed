#!/bin/bash
set -e

if [ -z "$SERVICE" ]; then
  echo "❌ SERVICE environment variable is not set!"
  exit 1
fi

echo "🚀 Starting service: $SERVICE"

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
    uv run -m optifeed.pipeline.scheduler
    ;;

  *)
    echo "❌ Unknown service: $SERVICE"
    exit 1
    ;;
esac
