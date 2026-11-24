# memory.py - everything about remembering the conversation
import json
import requests
from config import URL, CHAT_MODEL, SYSTEM_PROMPT, SUMMARY_PROMPT, MEMORY_FILE

history = [{"role": "system", "content": SYSTEM_PROMPT}]
summary_cache = {"covered": 0, "text": ""}                   # saved summary


def trim_history(messages, max_messages=6):
    system = [m for m in messages if m["role"] == "system"]  # keep the system message
    others = [m for m in messages if m["role"] != "system"]  # all chat messages
    return system + others[-max_messages:]                   # system + last N messages


def summarize(messages):
    text = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)  # CHANGED (v2): clear labels
    resp = requests.post(URL, json={
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": SUMMARY_PROMPT},                # CHANGED (v2): better prompt
            {"role": "user", "content": "Conversation:\n" + text},       # CHANGED (v2): marked as data
        ],
        "stream": False,
        "options": {"temperature": 0},                                    # NEW (v2): predictable output
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
    recent = trim_history(others, max_messages)              # CHANGED (v2): last N chat messages only
    system_msg = {"role": "system", "content": SYSTEM_PROMPT}  # NEW (v2): rules always from config
    if not old:                                              # nothing dropped yet
        return [system_msg] + recent
    summary_msg = {"role": "system", "content": f"Summary of earlier conversation: {update_summary(old)}"}
    return [system_msg, summary_msg] + recent                # CHANGED (v2): system + summary + recent, clear order


def save_chat():
    with open(MEMORY_FILE, "w") as f:
        json.dump({"history": history, "summary": summary_cache}, f, indent=2)


def load_chat():
    try:
        with open(MEMORY_FILE) as f:
            data = json.load(f)
        chat_only = [m for m in data["history"] if m["role"] != "system"]       # NEW (v2): ignore saved system messages
        history[:] = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_only  # CHANGED (v2): system prompt always from config
        summary_cache.update(data["summary"])                # replace summary contents
        print(f"[loaded {len(chat_only)} chat messages from {MEMORY_FILE.name}]")  # CHANGED (v2): count chat messages only
    except FileNotFoundError:
        print("[no saved chat found, starting fresh]")