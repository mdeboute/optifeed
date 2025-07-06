FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y curl cron && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/app
ENV PATH="/root/.local/bin:${PATH}"

COPY optifeed /app/optifeed
COPY pyproject.toml /app/
COPY .env /app/.env

RUN uv sync

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
