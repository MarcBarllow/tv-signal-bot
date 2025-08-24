import os
import json
from fastapi import FastAPI, Request
from telegram import Bot

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET")
ALLOWED_SYMBOLS = os.getenv("ALLOWED_SYMBOLS", "BTCUSDT,ETHUSDT").split(",")
ALLOWED_INTERVAL = os.getenv("ALLOWED_INTERVAL", "15")
TRADING_START_HOUR = int(os.getenv("TRADING_START_HOUR", 8))
TRADING_END_HOUR = int(os.getenv("TRADING_END_HOUR", 22))

bot = Bot(TELEGRAM_TOKEN)
signals_enabled = True

@app.post("/webhook")
async def webhook(request: Request):
    global signals_enabled
    data = await request.json()

    if data.get("secret") != TV_WEBHOOK_SECRET:
        return {"status": "unauthorized"}

    symbol = data.get("symbol", "").upper().replace("BINANCE:", "")
    interval = data.get("interval", "")
    signal = data.get("signal", "").upper()
    price = data.get("price", "")

    from datetime import datetime
    hour = datetime.utcnow().hour + 3  # МСК
    if hour < TRADING_START_HOUR or hour >= TRADING_END_HOUR:
        return {"status": "out_of_time"}

    if signals_enabled and symbol in ALLOWED_SYMBOLS and interval == ALLOWED_INTERVAL:
        msg = f"🔔 Сигнал: <b>{signal}</b>\nМонета: <b>{symbol}</b>\nТФ: {interval}m\nЦена: {price}"
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode="HTML")

    return {"status": "ok"}

@app.get("/")
def root():
    return {"status": "bot running"}

@app.post("/start")
async def start_signals():
    global signals_enabled
    signals_enabled = True
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="✅ Сигналы ВКЛЮЧЕНЫ")
    return {"status": "started"}

@app.post("/stop")
async def stop_signals():
    global signals_enabled
    signals_enabled = False
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="⛔️ Сигналы ВЫКЛЮЧЕНЫ")
    return {"status": "stopped"}
