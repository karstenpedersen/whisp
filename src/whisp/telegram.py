import os

import httpx
from dotenv import load_dotenv

TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
CHAT_ID_ENV = "TELEGRAM_CHAT_ID"


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


def get_bot_id():
    token = _env(TOKEN_ENV)
    r = httpx.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)

    for u in r.json()["result"]:
        return u["message"]["chat"]["id"]

    return None


def send_message(text: str) -> None:
    token = _env(TOKEN_ENV)
    r = httpx.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": _env(CHAT_ID_ENV), "text": text},
        timeout=10,
    )
    r.raise_for_status()
