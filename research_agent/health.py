"""Checks that Ollama is running and the model is installed (standard library only)."""

import json
import urllib.request

from research_agent.config import get_base_url


def installed_models(url: str | None = None, timeout: float = 3.0) -> list[str]:
    """Names of the models pulled into Ollama. Raises ConnectionError if unreachable."""
    url = (url or get_base_url()).rstrip("/")
    try:
        with urllib.request.urlopen(f"{url}/api/tags", timeout=timeout) as response:
            data = json.load(response)
    except (OSError, ValueError) as error:  # URLError is an OSError
        raise ConnectionError(
            f"Cannot reach Ollama at {url}. Start it with: ollama serve"
        ) from error
    names = {m.get("name") or m.get("model") for m in data.get("models", [])}
    return sorted(n for n in names if n)


def check_ollama(model: str, url: str | None = None) -> str | None:
    """Return a friendly error message, or None if Ollama is up and the model is installed."""
    try:
        names = installed_models(url)
    except ConnectionError as error:
        return str(error)
    if model in names or f"{model}:latest" in names:
        return None
    return f"Model '{model}' is not installed. Run: ollama pull {model}"
