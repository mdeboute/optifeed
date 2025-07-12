
# 📈 Optifeed

**Optifeed** is an **intelligent Telegram bot** built to:

- **spot investment opportunities** from financial news and macro events,
- and provide **contextual analysis** of market trends.

It follows an **event-driven, modular architecture**, with future integrations planned for:

- **LLM (Gemini)** to perform deep semantic analysis,
- and a **vector database** for similarity search across news & reports.

---

## 🚀 Architecture overview

```mermaid
flowchart TD
    TG[Telegram User] --> BOT[Telegram Servers]
    BOT --> |Webhook POST| FASTAPI[FastAPI /webhook]
    FASTAPI --> RABBIT[RabbitMQ Queue]
    RABBIT --> WORKER[Worker Python]
    WORKER --> |POST /sendMessage| BOT
```

✅ The bot operates through a robust pipeline:

1. **Webhook (Telegram → FastAPI):** instantly receives user messages.
2. **FastAPI → RabbitMQ:** queues the request for asynchronous processing.
3. **RabbitMQ → Worker:** consumes tasks, runs vector searches + LLM analysis.
4. **Worker → Telegram:** sends polished responses back to the user.

---

## ⚙️ Tech stack

- **Python 3.13+**
- **FastAPI:** HTTP server handling Telegram webhooks
- **RabbitMQ** (via Docker): task queue broker
- **ChromaDB:** for future semantic vector search
- **Gemini API:** advanced LLM-driven analysis
- **ngrok:** for local development to expose FastAPI

---

## 🛠️ Local development

### 🚀 Prerequisites

- Python ≥3.13
- Docker + docker-compose
- ngrok (or cloudflared tunnel)

---

### 🔥 Start your stack

```bash
# Clone the repo & install Python deps
git clone https://github.com/your-user/optifeed.git
cd optifeed
uv sync
source .venv/bin/activate

# Start services
make build && make up
````

## ✅ Typical flow

1. A user sends a command like:

```
Ask something to @<bot_username>
```

2. Telegram POSTs it to `/webhook`.
3. FastAPI queues a task in RabbitMQ.
4. The worker picks it up and processes the request.
5. The bot replies:

```
✅ Bot: Here's what I found...
```

---

## 🚀 Roadmap & next steps

- [x] FastAPI + Telegram webhook integration
- [x] Async task processing via RabbitMQ
- [x] Rich contextual analysis with Gemini
- [ ] Integration with Chroma for vector similarity

---

## 🤝 Contributions

If you have cool ideas around financial NLP, sentiment scoring, or want to integrate more data sources — feel free to open an issue or PR!
