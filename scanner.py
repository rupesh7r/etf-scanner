import requests
import schedule
import time
import os
from dotenv import load_dotenv
import asyncio
from telegram import Bot

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

NAV_TO_PRICE_RATIO = 1.60

def get_nav():
    url = "https://api.mfapi.in/mf/120716"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        nav = float(data['data'][0]['nav'])
        return nav * NAV_TO_PRICE_RATIO  # adjust to market price scale
    except:
        return None

def get_market_price():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/NIFTYBEES.NS"
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        data = response.json()
        price = data['chart']['result'][0]['meta']['regularMarketPrice']
        return float(price)
    except:
        return None

async def send_telegram(message):
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode='HTML')

def scan():
    print("Scanning...")
    nav = get_nav()
    price = get_market_price()

    if not nav or not price:
        print("Could not fetch data. Trying again next cycle.")
        return

    discrepancy = ((price - nav) / nav) * 100
    print(f"Adjusted NAV: ₹{nav:.3f} | Market Price: ₹{price} | Gap: {discrepancy:.2f}%")

    if discrepancy > 0.5:
        message = (
            f"🚨 <b>ETF ALERT — NIFTY BeES</b>\n\n"
            f"📈 Market Price: ₹{price}\n"
            f"📊 NAV: ₹{nav:.3f}\n"
            f"⚡ Gap: +{discrepancy:.2f}% (Trading at PREMIUM)\n\n"
            f"Historically this gap closes within 1-2 sessions."
        )
        asyncio.run(send_telegram(message))
        print("Alert sent!")

    elif discrepancy < -0.5:
        message = (
            f"🟢 <b>ETF ALERT — NIFTY BeES</b>\n\n"
            f"📉 Market Price: ₹{price}\n"
            f"📊 NAV: ₹{nav:.3f}\n"
            f"⚡ Gap: {discrepancy:.2f}% (Trading at DISCOUNT)\n\n"
            f"Potential buy opportunity. Gap usually closes within 1-2 sessions."
        )
        asyncio.run(send_telegram(message))
        print("Alert sent!")

    else:
        print(f"No significant gap. Gap is only {discrepancy:.2f}% — within normal range.")

scan()
schedule.every(5).minutes.do(scan)

while True:
    schedule.run_pending()
    time.sleep(1)
