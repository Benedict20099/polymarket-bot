import os
import time
import requests
from flask import Flask
from threading import Thread

# --- Flask Keep-Alive Server for Render ---
app = Flask('')

@app.route('/')
def home():
    return "Polymarket Copy-Trading Bot is Alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- Configuration & Environment Variables ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Load and split multiple comma-separated wallets into a clean list
target_wallet_env = os.environ.get("TARGET_WALLET", "")
TARGET_WALLETS = [w.strip() for w in target_wallet_env.split(",") if w.strip()]

def send_telegram_message(message):
    """Sends an alert message via Telegram safely without markdown parsing issues."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing!")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, json=payload)
        res_data = response.json()
        if not res_data.get("ok"):
            print(f"Failed to send Telegram message: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def check_wallets():
    """Polls Polymarket for new trades across all target wallets."""
    print(f"Started monitoring {len(TARGET_WALLETS)} wallet(s): {TARGET_WALLETS}")
    
    seen_txs = set()

    while True:
        for wallet in TARGET_WALLETS:
            try:
                url = f"https://data-api.polymarket.com/activity?user={wallet}&limit=5"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    activities = response.json()
                    for activity in activities:
                        tx_id = activity.get("transactionHash") or activity.get("id")
                        
                        if tx_id and tx_id not in seen_txs:
                            seen_txs.add(tx_id)
                            
                            if len(seen_txs) > 1000:
                                seen_txs.pop()
                                
                            title = activity.get("title", "Unknown Market")
                            side = activity.get("side", "TRADE")
                            size = activity.get("size", "N/A")
                            price = activity.get("price", "N/A")
                            
                            msg = (
                                f"🚨 New Polymarket Activity!\n\n"
                                f"👤 Wallet: {wallet[:6]}...{wallet[-4:]}\n"
                                f"📊 Market: {title}\n"
                                f"Action: {side} | Size: {size} | Price: {price}"
                            )
                            send_telegram_message(msg)
                else:
                    print(f"API error for wallet {wallet}: {response.status_code}")
            
            except Exception as e:
                print(f"Error checking wallet {wallet}: {e}")
                
        time.sleep(30)

if __name__ == "__main__":
    print("Starting Keep-Alive server...")
    keep_alive()
    
    print("Starting wallet monitoring loop...")
    check_wallets()

