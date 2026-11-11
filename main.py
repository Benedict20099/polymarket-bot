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
    """Sends an alert message via Telegram safely."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing!")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": True  # Prevents long link preview cards in Telegram
    }
    try:
        response = requests.post(url, json=payload)
        res_data = response.json()
        if not res_data.get("ok"):
            print(f"Failed to send Telegram message: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def notify_bot_startup():
    """Sends a one-time startup notification to Telegram."""
    wallet_list_str = "\n".join([f"• {w[:6]}...{w[-4:]}" for w in TARGET_WALLETS])
    startup_msg = (
        "🟢 Polymarket Copy-Trading Bot is ACTIVE!\n\n"
        f"Tracking {len(TARGET_WALLETS)} target wallet(s):\n"
        f"{wallet_list_str}\n\n"
        "Status: 24/7 Monitoring Online"
    )
    send_telegram_message(startup_msg)

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
                            
                            # Extract market slug or condition id to build a direct link
                            slug = activity.get("slug") or activity.get("marketSlug")
                            if slug:
                                market_link = f"https://polymarket.com/market/{slug}"
                            else:
                                market_link = "https://polymarket.com"
                            
                            msg = (
                                f"🚨 New Polymarket Activity!\n\n"
                                f"👤 Wallet: {wallet[:6]}...{wallet[-4:]}\n"
                                f"📊 Market: {title}\n"
                                f"Action: {side} | Size: {size} | Price: {price}\n\n"
                                f"🔗 View Market: {market_link}"
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
    
    print("Sending startup notification to Telegram...")
    notify_bot_startup()
    
    print("Starting wallet monitoring loop...")
    check_wallets()
