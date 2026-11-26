# chat.py - the interactive chat loop
import json
import requests
from config import URL, CHAT_MODEL
from memory import history, build_context, save_chat
from rag import facts_message


def ask():
    while True:
        user_msg = input("You: ")
        if user_msg == "quit":
            break
        history.append({"role": "user", "content": user_msg})
        messages = build_context(history)                    # NEW (v3): memory part (system + summary + recent)
        messages.insert(-1, facts_message(user_msg))         # NEW (v3): company facts just before the newest question
        resp = requests.post(URL, json={
            "model": CHAT_MODEL,
            "messages": messages,

            "stream": False,
            "options": {"num_ctx": 2560},
        })
        data = resp.json()                                   # convert reply to a dictionary
        print(json.dumps(data, indent=2))                    # look at the full raw response
        reply = data["message"]["content"]
        history.append({"role": "assistant", "content": reply})
        save_chat()
        print("AI:", reply)
        print(f"   [messages: {len(history)}, tokens read: {data['prompt_eval_count']}]")
    return reply