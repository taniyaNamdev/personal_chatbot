My Chatbot

A personal chatbot running on a local open-source model (Ollama), with chat memory and company-document search (RAG).

Setup
Install Ollama and pull the models: ollama pull llama3.2 ollama pull nomic-embed-text
Install Python libraries: pip install -r requirements.txt
Run

python main.py

Files
config.py : settings (URLs, model names, file paths, system prompt)
memory.py : chat history, summaries, save/load chat
rag.py : embeddings, document store, search, RAG answers
chat.py : interactive chat loop
main.py : starting point; pick a mode here
data/ : company documents and saved chat
