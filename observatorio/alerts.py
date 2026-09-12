"""Avisos por Telegram (con botones para aprobar/descartar cuarentenas).

Si no hay token configurado, los avisos se imprimen por consola (y GitHub Actions los muestra como avisos).
"""
from __future__ import annotations

import html
import json

import requests

from . import config
from .util import session

API = "https://api.telegram.org/bot{token}/{method}"


def _creds() -> tuple[str | None, str | None]:
    return config.secret("TELEGRAM_BOT_TOKEN"), config.secret("TELEGRAM_CHAT_ID")


def enabled() -> bool:
    t, c = _creds()
    return bool(t and c)


def esc(s) -> str:
    return html.escape(str(s), quote=False)


def send(text: str, buttons: list[list[dict]] | None = None) -> bool:
    """Envía un mensaje HTML. `buttons` = filas de {text, callback_data}. Devuelve True si se envió."""
    token, chat = _creds()
    if not token or not chat:
        print("[aviso]", text)
        if config.in_github_actions():
            print(f"::warning::{text[:500]}")
        return False
    payload = {"chat_id": chat, "text": text[:4000], "parse_mode": "HTML", "disable_web_page_preview": True}
    if buttons:
        payload["reply_markup"] = json.dumps({"inline_keyboard": buttons})
    try:
        r = session().post(API.format(token=token, method="sendMessage"), data=payload, timeout=30)
        ok = r.ok and r.json().get("ok", False)
        if not ok:
            print("[aviso] Telegram rechazó el mensaje:", r.text[:300])
        return ok
    except requests.RequestException as e:
        print("[aviso] Telegram no disponible:", e)
        return False


def get_updates(offset: int) -> list[dict]:
    token, _ = _creds()
    if not token:
        return []
    try:
        r = session().get(API.format(token=token, method="getUpdates"),
                          params={"offset": offset, "timeout": 0}, timeout=30)
        return r.json().get("result", []) if r.ok else []
    except requests.RequestException:
        return []


def answer_callback(callback_id: str, text: str) -> None:
    token, _ = _creds()
    if not token:
        return
    try:
        session().post(API.format(token=token, method="answerCallbackQuery"),
                       data={"callback_query_id": callback_id, "text": text[:200]}, timeout=30)
    except requests.RequestException:
        pass
