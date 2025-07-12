import json
import re
from typing import Optional

import google.generativeai as genai

from optifeed.utils.config import DEFAULT_LLM_MODEL, GOOGLE_API_KEY
from optifeed.utils.logger import logger

# --- Prompts
BASE_PROMPT = """
You are a helpful and funny assistant that answers questions based on the provided context.
You will receive a question and you should provide a concise and accurate answer in the language of the question.
Make sure to keep your responses short and to the point.
If the question is not clear, ask for clarification.
"""


# --- Gemini interaction
def ask_something(prompt: str, model=DEFAULT_LLM_MODEL) -> str:
    """Ask a question to the Gemini model and return the response."""
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        llm = genai.GenerativeModel(model)
        response = llm.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"❌ Gemini API error: {e}")
        return "❌ Error processing your request. Please try again later."


def parse_gemini_json(text: str) -> Optional[dict]:
    """Remove markdown ```json ... ``` if present and parse JSON."""
    try:
        cleaned = re.sub(r"^```json|^```|```$", "", text.strip(), flags=re.MULTILINE)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON decode failed: {e}")
        return None
