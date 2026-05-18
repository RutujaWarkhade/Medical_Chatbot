# chat_storage.py

import json
import os
from datetime import datetime

CHAT_FILE = "chat_sessions.json"


def load_all_chats():
    if os.path.exists(CHAT_FILE):
        try:
            with open(CHAT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_all_chats(data):
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_user_chats(user_email):
    data = load_all_chats()
    return data.get(user_email, {})


def save_user_chats(user_email, chats):
    data = load_all_chats()
    data[user_email] = chats
    save_all_chats(data)


def create_chat_session(user_email):
    chats = load_user_chats(user_email)

    session_id = str(int(datetime.now().timestamp()))

    chats[session_id] = {
        "title": "New Chat",
        "messages": [],
        "created_at": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }

    save_user_chats(user_email, chats)

    return session_id


def add_chat_message(user_email, session_id, role, content, extra=None):
    chats = load_user_chats(user_email)

    if session_id not in chats:
        return

    msg = {
        "role": role,
        "content": content,
        "extra": extra or {}
    }

    chats[session_id]["messages"].append(msg)

    # Auto update title from first user message
    user_msgs = [
        m for m in chats[session_id]["messages"]
        if m["role"] == "user"
    ]

    if len(user_msgs) == 1:
        title = user_msgs[0]["content"][:40]
        chats[session_id]["title"] = (
            title + ("..." if len(user_msgs[0]["content"]) > 40 else "")
        )

    save_user_chats(user_email, chats)


def delete_chat_session(user_email, session_id):
    chats = load_user_chats(user_email)

    if session_id in chats:
        del chats[session_id]

    save_user_chats(user_email, chats)