"""Persistent JSON storage for warnings, rules, and muted users."""

import json
import os

STORAGE_FILE = os.path.join(os.path.dirname(__file__), "db", "storage.json")

_DEFAULTS = {
    "warnings": {},   # {chat_id: {user_id: count}}
    "rules":    {},   # {chat_id: "rules text"}
}


def _load() -> dict:
    if not os.path.exists(STORAGE_FILE):
        return {k: dict(v) for k, v in _DEFAULTS.items()}
    with open(STORAGE_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(STORAGE_FILE), exist_ok=True)
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Warnings ──────────────────────────────────────────────────────────────────

def get_warnings(chat_id: int, user_id: int) -> int:
    data = _load()
    return data["warnings"].get(str(chat_id), {}).get(str(user_id), 0)


def add_warning(chat_id: int, user_id: int) -> int:
    data = _load()
    chat = data["warnings"].setdefault(str(chat_id), {})
    chat[str(user_id)] = chat.get(str(user_id), 0) + 1
    _save(data)
    return chat[str(user_id)]


def reset_warnings(chat_id: int, user_id: int) -> None:
    data = _load()
    data["warnings"].get(str(chat_id), {}).pop(str(user_id), None)
    _save(data)


# ── Rules ─────────────────────────────────────────────────────────────────────

def get_rules(chat_id: int) -> str | None:
    return _load()["rules"].get(str(chat_id))


def set_rules(chat_id: int, text: str) -> None:
    data = _load()
    data["rules"][str(chat_id)] = text
    _save(data)
