# My AI Learnings 📘

Simple notes on everything learned while building my chatbot.
Read top to bottom, or jump to a topic.

---

## 1. Basic Words

- **AI model / LLM** (Large Language Model): the "brain" that reads text and writes replies. Example: `llama3.2`.
- **Open-source model**: a model anyone can download and run for free.
- **Parameters**: the learned numbers inside a model. More parameters = smarter but heavier. `llama3.2` (3B) = 3 billion.
- **Ollama**: a free tool that downloads and runs open-source models on my own computer.
- **Running locally**: the model runs on my machine, so my data (company policies) never leaves my computer.

---

## 2. Talking to the Model from Code

- Ollama runs a **local server** (a background program waiting for requests) at `http://localhost:11434`.
- **Endpoint**: a specific address on the server for a specific job.
  - `/api/chat` → get a reply
  - `/api/embed` → get an embedding
- We send a **request** using the `requests` library and get back a **response** in **JSON** (text format that looks like a Python dictionary).
- `"stream": False` → wait and get the full reply at once (instead of word by word).
- The reply text is at: `data["message"]["content"]`

---

## 3. Messages and Roles

The model receives a list of messages. Each message has a **role**:

- `system` → hidden rules for the bot (e.g. "You are a friendly assistant. Keep answers short.")
- `user` → what I typed
- `assistant` → what the bot replied

```python
messages = [
    {"role": "system", "content": "You are a friendly assistant."},
    {"role": "user", "content": "Hi"},
]
```

- **System prompt**: the system message. It controls the bot's personality and rules.

---

## 4. Tokens and Context Window

- **Token**: a small piece of text (roughly ¾ of a word). Models read and write in tokens.
- **Context window** (`num_ctx`): the maximum tokens the model can read at once.
  - If input is bigger, Ollama silently cuts part of it → the bot "forgets".
- `prompt_eval_count` in the response = how many tokens the model read.

---

## 5. Memory (Chat History)

- **Important fact: the model has NO memory.** Every request is fresh.
- To "remember", we send the past conversation (`history`) every time.
- Problem: history keeps growing → too many tokens.

**Fix 1 – Sliding window** (`trim_history`)
- Keep the system message + only the last N messages.
- Downside: older messages are completely lost.

**Fix 2 – Summary** (`summarize`, `update_summary`)
- Old messages that fall out of the window are turned into a short summary.
- Send: system + summary + recent messages (`build_context`).
- **Summary cache**: we remember which messages are already summarized, so we only summarize new ones.

**Fix 3 – Saving to a file** (`save_chat`, `load_chat`)
- History and summary are saved to `chat_memory.json` after every reply.
- On restart, `load_chat()` loads them back.

---

## 6. Embeddings

- **Embedding**: turning text into a **vector** (a list of numbers that represents its meaning).
- Texts with similar meaning get similar vectors, even with different words.
  - "How many holidays do workers get?" ≈ "Employees get 20 paid leave days."
- We use a separate **embedding model**: `nomic-embed-text`.
- **Rule**: questions and documents must use the **same** embedding model (each model has its own "meaning map").

**Similarity** (`similarity`)
- **Cosine similarity**: a score showing how close two vectors are.
- Closer to 1 = more similar meaning.

---

## 7. RAG (Retrieval-Augmented Generation)

**Why:** the model doesn't know my company's policies. RAG gives it the right facts at question time.

**Steps** (`rag_ask`)
1. **Retrieve** → embed the question, find the most similar documents (`search`).
2. **Augment** → put those documents into the system message.
3. **Generate** → the model answers using them.

**Useful terms**
- **Document store** (`doc_store`): our list of texts + their vectors.
- **top_k**: how many best matches to return (we use 2).
- **Hallucination**: when the model confidently makes up an answer. We reduce it by saying "If the answer is not there, say you don't know."

**Two models, two jobs**
- Embedding model = librarian (finds the right pages).
- Chat model = expert (reads the pages and answers).
- The embedding doesn't "understand" the question. It only helps find matching documents.

---

## 8. Providing Company Documents

**Now (v1):** one fact per line in `data/company_info.txt`. `load_documents()` reads and embeds each line at startup.

**For real documents (future), the ingestion pipeline:**
1. **Collect** files in a folder.
2. **Extract** plain text from PDF / Word.
3. **Chunk** → cut long text into small pieces, with a little **overlap** (repeat a bit of the previous piece so nothing is cut off).
4. **Embed** each chunk.
5. **Store** chunks + vectors (later in a **vector database**, a database made for fast vector search).
6. **Track source** → remember which file each chunk came from.

---

## 9. Project Structure

```
my_chatbot/
├── main.py          ← starting point (run this)
├── config.py        ← all settings
├── memory.py        ← chat memory
├── rag.py           ← company document search
├── chat.py          ← chat loop
├── data/            ← company facts + saved chat
├── requirements.txt ← libraries needed
├── README.md        ← how to set up and run
└── learnings.md     ← this file
```

- **Module**: any `.py` file whose functions can be used by another file.
- **import**: borrow functions from another module. `from memory import save_chat`
- **Entry point**: the file you run to start (`main.py`).
- `if __name__ == "__main__":` → run this code only when the file is started directly.
- **config file**: settings in one place, so changing a model name = editing one line.
- **Separation of concerns**: each file has one job.
  - Memory = "What did we talk about?" (changes every message)
  - RAG = "What does the company say?" (changes only when documents change)
  - `chat.py` is the manager that will combine both.
- **requirements.txt**: install all libraries with `pip install -r requirements.txt`.

---

## 10. Reading the Ollama Response (Debugging)

The full response has useful numbers for finding slowness:

- `total_duration` → total time for the request
- `load_duration` → time to load the model into memory
- `prompt_eval_count` → tokens the model read (my input)
- `prompt_eval_duration` → time spent reading the input
- `eval_count` → tokens the model wrote (its reply)
- `eval_duration` → time spent writing the reply
- **Times are in nanoseconds** (1 second = 1,000,000,000 ns). Example: `5394926458` ≈ 5.4 seconds.
- Writing the reply is usually the slowest part, so longer replies = slower.

---

## 11. Lessons From Testing Memory

- **Saved ≠ remembered.** The chat can be loaded from the file, but the model only "knows" what we send it in this request.
- **Models have a default habit** of saying "I can't remember you", even when the past chat is in the messages. The system prompt should tell the bot that it does have the earlier conversation.
- **Small models write weak summaries.** `llama3.2` (3B) can make summaries that are wrong or miss facts (like names). If a fact is lost in the summary, it's lost for the bot.
- **Sliding window drops early facts.** My name was in message #1. With a 6-message window, it fell out quickly, and only the summary could carry it.
- **Saved file can lose the system prompt.** `load_chat()` replaces the whole history with the file. If the file has no system message, the bot runs with no rules after a restart.
- **Code assumptions can break silently.** `build_context()` assumes the first message is the system message. Without it, the summary gets inserted in the wrong place.
- **Wrong answers pollute memory.** When the bot wrongly says "our conversation just started", that reply is saved in history. The summarizer then reads it and repeats the mistake. Bad output becomes bad memory.
- **Debug tip**: when the bot forgets, check 3 things:
  1. Is the fact in `chat_memory.json`?
  2. Is it in the recent messages or in the summary?
  3. Did the model ignore it even though it was sent?

---

## 12. Why the Summary Goes Bad

What I saw: each new summary got worse. The last one was written as if the bot were talking ("I'm a chatbot... I don't have any information about you").

**Reasons**
- **Small model**: a 3B model doesn't follow instructions well.
- **Vague prompt**: "2-3 short sentences" forces the model to drop details. It's a story, not a list of facts.
- **Photocopy of a photocopy**: every turn, the old summary is summarized again. Each copy loses a bit more, until facts disappear.
- **Too frequent**: the window moves every turn, so the summary is rewritten every turn = more chances to lose facts (and slower).
- **Role confusion**: the model reads "user: ... assistant: ..." text and starts writing as the assistant instead of as a note-taker.
- **Garbage in, garbage out**: the bot's wrong replies ("I don't know you") are in the input, so the summary repeats them.

**Ways to fix (for v2)**
- Better summary prompt: ask for a **bullet list of facts**, written in third person ("The user's name is Taniya"), and say "keep every fact from the previous summary".
- **Temperature 0**: temperature controls randomness. 0 = most predictable output, better for summaries.
- **Separate facts memory**: store key facts (like my name) in their own list that never gets summarized away.
- **Summarize less often**: e.g. only when 6 new messages have dropped out, not every turn.

**Speed evidence**
- `load_duration` was ~0.57 s on every request → the model was reloaded each time (because `num_ctx` differs between the chat call and the summary call).
- Longer replies were slower: 172 reply tokens took ~6.2 s, 84 tokens took ~3.1 s.

**Tip**: the saved memory is now polluted with wrong facts. For clean testing of v2, rename `chat_memory.json` to `chat_memory_old.json` and start fresh.

---

## 13. Prompt Writing Tips (from fixing the summary)

- **Give the model a role**: "You are a note-taker" → it stops acting like the chatbot.
- **Say the output format**: "bullet list of facts" works better than "2-3 sentences".
- **List clear rules**: short, one rule per line.
- **Show an example**: "e.g. 'The user's name is Taniya.'"
- **Say what NOT to do**: "Do not answer or continue the conversation."
- **Mark input as data**: "Conversation:" before the text, so the model reads it instead of replying to it.
- Small models need clearer, stricter prompts than big models.

---

## 14. How I'm Building This

- Start basic, then improve one version at a time.
- Every new version fixes a **limitation** of the previous one.
- Never remove working functions; only enhance them or add new ones.

### v1 Limitations Found
- Chat and RAG are separate (the chatbot can't use company facts).
- Company facts must be short single lines in one file.
- Can't read PDF / Word.
- Embeddings are recreated at every startup.
- Follow-up questions ("What about Saturday?") search poorly, because only the current question is embedded.
- Answers don't show their source.
- Terminal only.
- Seems to forget everything after restart (`load_chat()` is commented out in `main.py`, and only a few recent messages + summary are sent).
- Weak summaries from the small model can lose facts (like my name).
- The bot says "I can't remember you" even when the chat is loaded.
- Early facts (like my name) fall out of the 6-message window and depend on the weak summary.
- After a restart, the system prompt can go missing (`load_chat()` trusts the file completely), and the summary is then placed in the wrong position.
- Wrong bot replies get saved and then summarized, so mistakes spread into memory.
- The summary is rewritten every turn and gets worse each time (photocopy of a photocopy).
- Gets slow in long conversations (extra summary call every turn + model reloads when `num_ctx` differs between calls).

### Version History
- **v1**: basic project – chat with memory, saving chat, RAG on simple facts, organized into files.
- **v2 – step 1**: better summarizer.
  - *Limitation*: the summary lost facts (like my name) and started talking as the bot.
  - *Fix*: new `SUMMARY_PROMPT` in `config.py` (note-taker role, bullet facts, third person, keep previous facts, ignore "I don't know you"), clear `USER:` / `ASSISTANT:` labels, conversation marked as data, `temperature: 0`.
  - *Only changed*: `summarize()` in `memory.py` + one new setting in `config.py`.
  - *Result* ✅: summary became clean facts ("The user's name is Taniya.") and the bot recalled my name after a restart.
  - *Still open*: the bot still says "I don't have memories" (missing/weak system prompt), and `load_duration` shows the model still reloads each request.
- **v2 – step 2**: system prompt always safe.
  - *Limitation*: the saved file had no system message, and `load_chat()` copied the file as it was, so after a restart the bot had no rules (and `build_context()` put the summary in the wrong place).
  - *Fix*: `load_chat()` removes any saved system messages and always puts `SYSTEM_PROMPT` from `config.py` first.
  - *Bonus*: if I edit `SYSTEM_PROMPT` in `config.py`, the change now works even with an old saved chat.
  - *Lesson*: **don't fully trust saved data**. Rebuild important parts (like rules) from code/config.
- **v2 – step 3**: cleaner `build_context()` (my idea 💡).
  - *Limitation*: `build_context()` assumed the first message in history is the system message (`trimmed[:1]`). If that's ever not true, the summary lands in the wrong place, with no error.
  - *Fix*: build the context in a fixed order: system prompt from `config.py` → summary → recent messages. `trim_history()` is still reused for the recent messages.
  - *Lesson*: **one source of truth**. The rules live in one place (`config.py`), and the code no longer depends on the order of the saved history.