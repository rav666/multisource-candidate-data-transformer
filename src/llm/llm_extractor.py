"""
Calls Google Gemini to parse a resume into LLMResponse.

Requires GOOGLE_API_KEY in environment (or a .env file).
Falls back to returning an empty LLMResponse on any error so the pipeline never crashes on a bad/missing resume.
"""
import json
import logging
import os

import dotenv

from src.llm.llm_prompts import RESUME_SYSTEM_PROMPT
from src.models import LLMResponse

logger = logging.getLogger(__name__)

# Stable, widely-available Gemini model with structured-output support.
_DEFAULT_MODEL = "gemini-3.5-flash"


def call_llm(resume_text: str) -> LLMResponse:
    """Send resume text to Gemini and return a validated LLMResponse."""
    dotenv.load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY", "")

    if not api_key:
        logger.warning("GOOGLE_API_KEY not set — returning empty LLMResponse.")
        return LLMResponse()

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", _DEFAULT_MODEL), contents=resume_text,
            config=types.GenerateContentConfig(system_instruction=RESUME_SYSTEM_PROMPT,
                response_mime_type="application/json", response_schema=LLMResponse, temperature=0,
                # fully deterministic
            )
        )

        # Prefer the structured .parsed attribute; fall back to raw JSON text.
        if response.parsed:
            return response.parsed

        raw = response.text or "{}"
        data = json.loads(raw)
        return LLMResponse.model_validate(data)

    except Exception as exc:
        logger.error("LLM call failed: %s — returning empty LLMResponse.", exc)
        return LLMResponse()
