import json
import urllib.error

from research_agent import health


class _Response:
    def __init__(self, payload):
        self._data = json.dumps(payload).encode()

    def read(self, *args):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _serve(monkeypatch, payload):
    monkeypatch.setattr(health.urllib.request, "urlopen", lambda *a, **k: _Response(payload))


def test_model_installed(monkeypatch):
    _serve(monkeypatch, {"models": [{"name": "qwen3:8b"}, {"name": "llama3.1:latest"}]})
    assert health.check_ollama("qwen3:8b") is None
    assert health.check_ollama("llama3.1") is None  # ":latest" is implied


def test_model_missing(monkeypatch):
    _serve(monkeypatch, {"models": [{"name": "qwen3:8b"}]})
    assert "ollama pull mistral" in health.check_ollama("mistral")


def test_ollama_down(monkeypatch):
    def boom(*args, **kwargs):
        raise urllib.error.URLError("refused")

    monkeypatch.setattr(health.urllib.request, "urlopen", boom)
    assert "ollama serve" in health.check_ollama("qwen3:8b")
