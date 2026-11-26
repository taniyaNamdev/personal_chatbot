# chat.py - the interactive chat loop
import json
import requests
from config import URL, CHAT_MODEL
from memory import history, build_context, save_chat


def ask():
    while True:
        user_msg = input("You: ")
        if user_msg == "quit":
            break
        history.append({"role": "user", "content": user_msg})
        resp = requests.post(URL, json={
            "model": CHAT_MODEL,
            "messages": build_context(history),
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