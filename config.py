# config.py - all settings in one place (change values here, not inside the code)
from pathlib import Path

BASE_DIR = Path(__file__).parent                     # the project folder
DATA_DIR = BASE_DIR / "data"                         # where data files live

# Ollama server addresses
URL = "http://localhost:11434/api/chat"              # chat endpoint
EMBED_URL = "http://localhost:11434/api/embed"       # embedding endpoint

# Model names
CHAT_MODEL = "llama3.2"                              # model that writes replies
EMBED_MODEL = "nomic-embed-text"                     # model that turns text into vectors

# Bot behaviour
SYSTEM_PROMPT = "You are a friendly assistant. Keep answers short."

# Files
MEMORY_FILE = DATA_DIR / "chat_memory.json"          # where the chat is saved
DOCS_FILE = DATA_DIR / "company_info.txt"            # company documents, one fact per line