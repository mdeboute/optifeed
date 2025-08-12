import json
import re
from typing import Optional

from pydantic_ai import Agent, AgentRunResult, ModelMessage
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from optifeed.utils.config import DEFAULT_LLM_MODEL, GOOGLE_API_KEY
from optifeed.utils.logger import logger

INSTRUCTION_PROMPT = """
You are a helpful and funny assistant.
You will receive a question and you should provide a concise and accurate answer in the language of the question.
If the question is not clear, ask for clarification.
Don't use fancy format.
"""

PROVIDER = GoogleProvider(api_key=GOOGLE_API_KEY)
MODEL = GoogleModel(model_name=DEFAULT_LLM_MODEL, provider=PROVIDER)


def ask_something(
    prompt: str, message_history: list[ModelMessage] = None
) -> AgentRunResult[str]:
    """Ask Gemini a question with the provided prompt."""
    agent = Agent(model=MODEL, instructions=INSTRUCTION_PROMPT)
    result = agent.run_sync(user_prompt=prompt, message_history=message_history)
    return result


def parse_json_block(text: str) -> Optional[dict]:
    """Remove markdown ```json ... ``` if present and parse JSON."""
    try:
        cleaned = re.sub(r"^```json|^```|```$", "", text.strip(), flags=re.MULTILINE)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON decode failed: {e}")
        return None
