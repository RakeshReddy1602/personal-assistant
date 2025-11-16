import json
import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv
import requests

load_dotenv()

def _ollama_base_url() -> str:
    if(os.getenv("OLLAMA_BASE_URL",None) is None):
        raise ValueError("OLLAMA_BASE_URL is not set")
    return os.getenv("OLLAMA_BASE_URL")


def generate(model: str, prompt: str, **kwargs: Any) -> str:
    url = f"{_ollama_base_url()}/api/generate"
    data: Dict[str, Any] = {"model": model, "prompt": prompt, "stream": False}
    data.update(kwargs)
    resp = requests.post(url, json=data, timeout=60)
    resp.raise_for_status()

    # /api/generate streams lines by default when stream=true; use stream=False for full text
    try:
        payload = resp.json()
        return payload.get("response", "")
    except ValueError:
        return resp.text


def generate_json(model: str, prompt: str, **kwargs: Any) -> Optional[Dict]:
    """Generate JSON response from Ollama."""
    response = generate(model, prompt, format="json", **kwargs)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return None
