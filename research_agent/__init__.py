"""ResearchAgentPy: a local AI research agent that summarizes topics with references."""

from dotenv import find_dotenv, load_dotenv

__version__ = "0.2.0"

# Load settings from a .env file in the current directory (if there is one).
load_dotenv(find_dotenv(usecwd=True))
