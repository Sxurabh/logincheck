#!/usr/bin/env python3
import os, requests, time

# ─── Configuration ─────────────────────────────────────────────────────────────
BOT_TOKEN        = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID          = int(os.getenv("TELEGRAM_CHAT_ID"))
GHUB_TOKEN     = os.getenv("GHUB_TOKEN")
OWNER            = os.getenv("GHUB_OWNER")
REPO             = os.getenv("GHUB_REPO")
WORKFLOW_FILE    = os.getenv("GHUB_WORKFLOW_FILE")  # e.g. "selenium-login.yml"
REF              = os.getenv("GHUB_REF", "main")

TELE_GET_UPDATES = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
GH_DISPATCH_URL  = (
    f"https://api.github.com/repos/{OWNER}/{REPO}"
    f"/actions/workflows/{WORKFLOW_FILE}/dispatches"
)

def get_updates():
    r = requests.get(TELE_GET_UPDATES, timeout=10)
    data = r.json()
    return data.get("result", []) if data.get("ok") else []

def trigger_workflow():
    headers = {
        "Authorization": f"token {GHUB_TOKEN}",
        "Accept":        "application/vnd.github.v3+json"
    }
    payload = {"ref": REF}
    r = requests.post(GH_DISPATCH_URL, json=payload, headers=headers, timeout=10)
    r.raise_for_status()
    print("✅ Workflow dispatched")

def main():
    now = time.time()
    for upd in get_updates():
        msg = upd.get("message") or {}
        text = msg.get("text","").strip()
        date = msg.get("date", 0)
        chat = msg.get("chat",{}).get("id")
        # only within last 5 minutes, your chat & exact "/dispatch"
        if chat == CHAT_ID and text == "/dispatch" and now - date < 300:
            print("🔄 /dispatch received, firing workflow…")
            trigger_workflow()

if __name__ == "__main__":
    main()
