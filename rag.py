# rag.py - storing company documents, searching them, and answering from them
import requests
from config import URL, EMBED_URL, CHAT_MODEL, EMBED_MODEL

doc_store = []                                               # list of {"text", "vector"}


def get_embedding(text):
    resp = requests.post(EMBED_URL, json={
        "model": EMBED_MODEL,
        "input": text,
    })
    return resp.json()["embeddings"][0]                      # the vector (list of numbers)


def similarity(a, b):                                        # score: closer to 1 = more similar
    dot = sum(x * y for x, y in zip(a, b))                   # how much they point the same way
    len_a = sum(x * x for x in a) ** 0.5                     # length of vector a
    len_b = sum(x * x for x in b) ** 0.5                     # length of vector b
    return dot / (len_a * len_b)


def add_document(text):
    doc_store.append({"text": text, "vector": get_embedding(text)})


def load_documents(path):                                    # NEW function
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:                                         # skip empty lines
                add_document(line)
    print(f"[loaded {len(doc_store)} documents from {path.name}]")


def search(query, top_k=2):
    q_vec = get_embedding(query)                             # turn the question into a vector
    scored = [(similarity(q_vec, d["vector"]), d["text"]) for d in doc_store]
    scored.sort(key=lambda pair: pair[0], reverse=True)      # highest score first
    return scored[:top_k]                                    # best matches only


def rag_ask(question):
    results = search(question)                               # 1. Retrieve
    context = "\n".join(f"- {text}" for score, text in results)
    messages = [                                             # 2. Augment
        {"role": "system", "content":
            "Answer using the information below. "
            "If the answer is not there, say you don't know.\n\n"
            "Information:\n" + context},
        {"role": "user", "content": question},
    ]
    resp = requests.post(URL, json={                         # 3. Generate
        "model": CHAT_MODEL,
        "messages": messages,
        "stream": False,
    })
    reply = resp.json()["message"]["content"]
    print(f"   [context used:\n{context}]")                  # so you can see what was sent
    print("AI:", reply)
    return reply

def facts_message(question, top_k=2):                        # NEW (v3): company facts as a system message
    results = search(question, top_k)                        # find the best matching facts
    facts = "\n".join(f"- {text}" for score, text in results)
    return {"role": "system", "content":
            "Company facts (use them only if they help answer the question):\n" + facts}