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

ETFS = [
    {"name": "Nifty BeES", "yahoo": "NIFTYBEES.NS", "amfi": "120716", "ratio": 1.60},
    {"name": "Bank BeES", "yahoo": "BANKBEES.NS", "amfi": "120684", "ratio": 9.885},
    {"name": "Gold BeES", "yahoo": "GOLDBEES.NS", "amfi": "120503", "ratio": 1.1658},
    {"name": "Nifty Next 50", "yahoo": "JUNIORBEES.NS", "amfi": "120823", "ratio": 1.179},
]

def get_nav(amfi_code):
    url = f"https://api.mfapi.in/mf/{amfi_code}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return float(data['data'][0]['nav'])
    except:
        return None

def get_market_price(yahoo_symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        data = response.json()
        return float(data['chart']['result'][0]['meta']['regularMarketPrice'])
    except:
        return None

async def send_telegram(message):
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode='HTML')

def scan():
    print("Scanning all ETFs...")
    for etf in ETFS:
        nav = get_nav(etf['amfi'])
        price = get_market_price(etf['yahoo'])

        if not nav or not price:
            print(f"{etf['name']}: Could not fetch data")
            continue

        adjusted_nav = nav * etf['ratio']
        discrepancy = ((price - adjusted_nav) / adjusted_nav) * 100
        print(f"{etf['name']}: NAV ₹{adjusted_nav:.3f} | Price ₹{price} | Gap {discrepancy:.2f}%")

        if discrepancy > 0.5:
            message = (
                f"🚨 <b>{etf['name']} — PREMIUM ALERT</b>\n\n"
                f"📈 Market Price: ₹{price}\n"
                f"📊 NAV: ₹{adjusted_nav:.3f}\n"
                f"⚡ Gap: +{discrepancy:.2f}% (Trading at PREMIUM)\n\n"
                f"ETF is overpriced vs underlying assets.\n"
                f"Historically this gap closes within 1-2 sessions."
            )
            asyncio.run(send_telegram(message))
            print(f"{etf['name']}: Alert sent!")

        elif discrepancy < -0.5:
            message = (
                f"🟢 <b>{etf['name']} — DISCOUNT ALERT</b>\n\n"
                f"📉 Market Price: ₹{price}\n"
                f"📊 NAV: ₹{adjusted_nav:.3f}\n"
                f"⚡ Gap: {discrepancy:.2f}% (Trading at DISCOUNT)\n\n"
                f"ETF is cheaper than underlying assets.\n"
                f"Potential buy opportunity. Gap usually closes within 1-2 sessions."
            )
            asyncio.run(send_telegram(message))
            print(f"{etf['name']}: Alert sent!")

        else:
            print(f"{etf['name']}: No significant gap ({discrepancy:.2f}%)")

    print("Scan complete.\n")

scan()
schedule.every(5).minutes.do(scan)

while True:
    schedule.run_pending()
    time.sleep(1)
