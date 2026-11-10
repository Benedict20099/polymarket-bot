import os
import time
import requests
from flask import Flask
from threading import Thread
from waitress import serve

# --- Flask Keep-Alive Server ---
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot is active and running!"


def run_flask():
  # Render expects the app to listen on port 10000 by default
  serve(app, host="0.0.0.0", port=10000)


def keep_alive():
  t = Thread(target=run_flask)
  t.daemon = True
  t.start()


# --- Configuration & Environment Variables ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TARGET_WALLET = os.environ.get("TARGET_WALLET")


def send_telegram_message(message):
  """Sends an alert message via Telegram."""
  if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("Telegram credentials missing!")
    return
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
  try:
    response = requests.post(url, json=payload)
    if not response.ok:
      print(f"Failed to send Telegram message: {response.text}")
  except Exception as e:
    print(f"Error sending Telegram message: {e}")


def main():
  print("Starting Polymarket Copy-Trading Bot...")
  send_telegram_message("🤖 *Polymarket Bot* has started successfully on Render!")

  # Start the web server in the background for health checks
  keep_alive()

  # Main bot polling loop
  while True:
    try:
      # Add your Polymarket API polling and copy-trading logic here
      print("Checking target wallet activity...")

      # Example placeholder loop interval (adjust as needed for your strategy)
      time.sleep(30)

    except Exception as e:
      error_msg = f"⚠️ *Bot Error encountered:* {str(e)}"
      print(error_msg)
      send_telegram_message(error_msg)
      time.sleep(10)


if __name__ == "__main__":
  main()
