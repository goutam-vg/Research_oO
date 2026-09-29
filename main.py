"""Shortcut for: python main.py "your topic"  (same as: python -m research_agent)"""

from research_agent.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
