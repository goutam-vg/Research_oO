"""Settings shared by the CLI, the web app and the agent (standard library only)."""

import os

DEFAULT_MODEL = "qwen3:8b"
DEFAULT_BASE_URL = "http://localhost:11434"
LENGTH_CHOICES = ("short", "medium", "long")
FORMAT_CHOICES = ("txt", "md")


def get_model_name(override: str | None = None) -> str:
    return override or os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)


def get_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
