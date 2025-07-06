from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from optifeed.utils.logger import logger
from optifeed.utils.rabbitmq import publish_task

app = FastAPI()


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    logger.debug(f"🤖 Received webhook: {data}")

    publish_task(
        {
            "type": "ask",
            "data": data,
        }
    )
    return JSONResponse(content={"ok": True})
