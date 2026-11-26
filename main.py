# main.py - starting point of the project. Run: python main.py
from config import DOCS_FILE
from memory import load_chat
from rag import load_documents, search, rag_ask
from chat import ask

if __name__ == "__main__":
    load_documents(DOCS_FILE)                                # load company documents first

    # --- Mode 1: chat with memory ---
    load_chat()
    ask()

    # --- Mode 2: test search scores ---
    # for score, text in search("How many holidays do workers get?"):
    #     print(round(score, 3), "-", text)

    # --- Mode 3: test RAG answers ---
    # rag_ask("How many holidays do workers get?")
    # rag_ask("Who started the company?")
    # rag_ask("What is the CEO's salary?")                     # not in our documents