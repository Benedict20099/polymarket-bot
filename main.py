import os
import time
import threading
from flask import Flask
import requests

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = "8567813293"

TARGET_WALLETS = [
    "0xf0318c32136c2db7fec88b84869aee6a1106c80c",
    "0x4f1d5ae26fc31472966e951af3183308736d8de2",
    "0x5a218c7ad04135830a45c41aaed7294df7809318"
]

POLL_INTERVAL = 15
processed_activity_ids = set()

@app.route('/')
def home():
    return "Polymarket Bot is Active!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def send_telegram_alert(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

def fetch_wallet_activity(wallet_address):
    url = f"https://data-api.polymarket.com/activity?user={wallet_address}&limit=5"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"Error checking {wallet_address}: {e}")
    return []

def process_trade(trade, wallet):
    trade_id = trade.get("id") or f"{trade.get('timestamp')}_{wallet}_{trade.get('conditionId')}"
    if trade_id in processed_activity_ids:
        return
    processed_activity_ids.add(trade_id)
    
    market_title = trade.get("title", "Polymarket Event")
    side = trade.get("side", "BUY").upper()
    outcome = trade.get("outcome", "")
    size = trade.get("size", 0)
    price = trade.get("price", 0)
    slug = trade.get("eventSlug", "")
    
    total_val = float(size) * float(price) if size and price else 0
    short_wallet = f"{wallet[:6]}...{wallet[-4:]}"
    market_url = f"https://polymarket.com/event/{slug}" if slug else "https://polymarket.com"

    msg = (
        f"🚨 *MANUAL TRADE SIGNAL*\n\n"
        f"👤 *Whale:* `{short_wallet}`\n"
        f"⚡ *Action:* `{side} {outcome}`\n"
        f"💰 *Price:* ${price:.2f} (Total: ${total_val:.2f} USDC)\n"
        f"📊 *Market:* {market_title}\n\n"
        f"🔗 [CLICK HERE TO PLACE TRADE]({market_url})"
    )
    send_telegram_alert(msg)

def bot_loop():
    print("Starting Bot Engine...")
    send_telegram_alert("🟢 *Replit Copy-Trading Bot Active!*")

    for wallet in TARGET_WALLETS:
        for act in fetch_wallet_activity(wallet):
            t_id = act.get("id") or f"{act.get('timestamp')}_{wallet}_{act.get('conditionId')}"
            processed_activity_ids.add(t_id)

    while True:
        for wallet in TARGET_WALLETS:
            activities = fetch_wallet_activity(wallet)
            for act in activities:
                process_trade(act, wallet)
            time.sleep(1)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    # Start bot loop in background thread
    threading.Thread(target=bot_loop, daemon=True).start()
    # Run Flask on main thread to satisfy Replit web server requirements
    run_flask()
