#!/usr/bin/env python3
import os
import requests
import time
import subprocess

# ─── Configuration ─────────────────────────────────────────────────────────────
BOT_TOKEN       = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID         = int(os.getenv("TELEGRAM_CHAT_ID"))

# Telegram API endpoint to fetch updates
TELE_GET_UPDATES = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

def get_updates():
    """Fetch incoming updates from Telegram."""
    r = requests.get(TELE_GET_UPDATES, timeout=10)
    data = r.json()
    return data.get("result", []) if data.get("ok") else []

def trigger_login_check():
    """Run your login_check.py script as a subprocess."""
    print("🔄 Running login_check.py…")
    proc = subprocess.run(
        ["python", "login_check.py"],
        capture_output=True,
        text=True
    )
    print(proc.stdout)
    if proc.returncode != 0:
        print("❌ login_check.py failed:")
        print(proc.stderr)

def main():
    now = time.time()
    for upd in get_updates():
        msg  = upd.get("message", {})
        text = msg.get("text", "").strip()
        chat = msg.get("chat", {}).get("id")

        # If it's exactly /dispatch from your chat, trigger it immediately
        if chat == CHAT_ID and text == "/dispatch":
            print("✅ /dispatch received, firing login_check.py…")
            trigger_login_check()

if __name__ == "__main__":
    main()
