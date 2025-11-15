import os
from typing import Any

from dotenv import load_dotenv
import google.generativeai as genai  # type: ignore[import]

load_dotenv()


def _configure() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set")
    genai.configure(api_key=api_key)


def generate(model: str, prompt: str, **kwargs: Any) -> str:
    _configure()
    gmodel = genai.GenerativeModel(model)
    result = gmodel.generate_content(prompt, **kwargs)
    # google-generativeai returns .text for simple generations
    return (getattr(result, "text", None) or "").strip()


