"""Tests never call Ollama or the network. If LangChain is not installed, light stubs are
used so the suite runs anywhere (CI installs only pytest and python-dotenv)."""

import importlib
import sys
import types


def _missing(name: str) -> bool:
    try:
        importlib.import_module(name)
        return False
    except ImportError:
        return True


def _stub(name: str, **attrs) -> None:
    module = types.ModuleType(name)
    vars(module).update(attrs)
    sys.modules[name] = module


class _Anything:
    def __init__(self, *args, **kwargs):
        pass


class _Tool:
    def __init__(self, name, func, description=""):
        self.name, self.func, self.description = name, func, description

    def invoke(self, value):
        return self.func(value)


if _missing("dotenv"):
    _stub("dotenv", load_dotenv=lambda *a, **k: None, find_dotenv=lambda *a, **k: "")
if _missing("langchain"):
    _stub("langchain")
    _stub("langchain.agents", create_agent=lambda **kwargs: None)
if _missing("langchain_ollama"):
    _stub("langchain_ollama", ChatOllama=_Anything)
if _missing("langchain_community"):
    _stub("langchain_community")
    _stub(
        "langchain_community.utilities",
        DuckDuckGoSearchAPIWrapper=_Anything,
        WikipediaAPIWrapper=_Anything,
    )
if _missing("langchain_core"):
    _stub("langchain_core")
    _stub("langchain_core.tools", Tool=_Tool)
