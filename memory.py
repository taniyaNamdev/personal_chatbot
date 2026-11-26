# memory.py - everything about remembering the conversation
import json
import requests
from config import URL, CHAT_MODEL, SYSTEM_PROMPT, MEMORY_FILE

history = [{"role": "system", "content": SYSTEM_PROMPT}]
summary_cache = {"covered": 0, "text": ""}                   # saved summary


def trim_history(messages, max_messages=6):
    system = [m for m in messages if m["role"] == "system"]  # keep the system message
    others = [m for m in messages if m["role"] != "system"]  # all chat messages
    return system + others[-max_messages:]                   # system + last N messages


def summarize(messages):
    text = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    resp = requests.post(URL, json={
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": "Summarize this conversation in 2-3 short sentences. Always keep important facts like names."},
            {"role": "user", "content": text},
        ],
        "stream": False,
    })
    summary = resp.json()["message"]["content"]
    print(f"   [summary: {summary}]")                        # so you can see it
    return summary


def update_summary(old):
    new_msgs = old[summary_cache["covered"]:]                # only messages not yet summarized
    if not new_msgs:                                         # nothing new, reuse saved summary
        return summary_cache["text"]
    if summary_cache["text"]:                                # include previous summary
        new_msgs = [{"role": "system", "content": f"Previous summary: {summary_cache['text']}"}] + new_msgs
    summary_cache["text"] = summarize(new_msgs)              # make updated summary
    summary_cache["covered"] = len(old)                      # remember how many are now summarized
    return summary_cache["text"]


def build_context(messages, max_messages=6):
    others = [m for m in messages if m["role"] != "system"]
    old = others[:-max_messages]                             # messages that will be dropped
    trimmed = trim_history(messages, max_messages)           # reuse our sliding window
    if not old:                                              # nothing dropped yet
        return trimmed
    summary_msg = {"role": "system", "content": f"Summary of earlier conversation: {update_summary(old)}"}
    return trimmed[:1] + [summary_msg] + trimmed[1:]         # system + summary + recent


def save_chat():
    with open(MEMORY_FILE, "w") as f:
        json.dump({"history": history, "summary": summary_cache}, f, indent=2)


def load_chat():
    try:
        with open(MEMORY_FILE) as f:
            data = json.load(f)
        history[:] = data["history"]                         # replace history contents
        summary_cache.update(data["summary"])                # replace summary contents
        print(f"[loaded {len(history)} messages from {MEMORY_FILE.name}]")
    except FileNotFoundError:
        print("[no saved chat found, starting fresh]")