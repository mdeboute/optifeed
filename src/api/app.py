from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from utils.logger import logger
from utils.rabbitmq import publish_task

app = FastAPI()


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    logger.debug(f"🤖 Received webhook: {data}")

    message = data.get("message", {}).get("text")
    chat_id = data.get("message", {}).get("chat", {}).get("id")

    if not message or not chat_id:
        logger.warning("⚠️ Payload missing 'text' or 'chat_id'")
        return JSONResponse(content={"ok": False, "error": "Missing data"})

    publish_task({"type": "ask", "query": message, "chat_id": chat_id})
    return JSONResponse(content={"ok": True})
