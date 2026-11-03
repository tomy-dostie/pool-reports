"""Optional: post the morning summary to a chat. Set DISCORD_WEBHOOK or TELEGRAM_TOKEN + TELEGRAM_CHAT as repository secrets."""
import json
import os
import urllib.request


def _post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "User-Agent": "pool-reports/1.0"})
    urllib.request.urlopen(req, timeout=30).read()


def send(summary):
    sent = []
    hook = os.environ.get("DISCORD_WEBHOOK", "").strip()
    if hook:
        _post(hook, {"content": summary[:1900]})
        sent.append("discord")
    token, chat = os.environ.get("TELEGRAM_TOKEN", "").strip(), os.environ.get("TELEGRAM_CHAT", "").strip()
    if token and chat:
        _post(f"https://api.telegram.org/bot{token}/sendMessage", {"chat_id": chat, "text": summary[:3900]})
        sent.append("telegram")
    return sent
