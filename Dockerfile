FROM python:3.13-slim

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
COPY credentials.json /app/
COPY token.json /app/
COPY *.flag /app/

RUN uv sync

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
