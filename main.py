from fastapi import FastAPI, Request
import os
import requests
from binance.client import Client
from datetime import datetime, timezone
import json

app = FastAPI()

# -------------------- Конфиги --------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET")  # dessston

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

last_signal_time = {}  # {symbol: datetime}

# -------------------- Функция отправки сообщений --------------------
def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text})

# -------------------- Получение объёмов с Binance --------------------
def get_binance_volumes(symbol, interval):
    try:
        # Spot
        klines = client.get_klines(symbol=symbol.replace(".P", ""), interval=interval, limit=1)
        spot_vol = float(klines[0][5]) if klines else 0

        # Futures
        futures_klines = client.futures_klines(symbol=symbol.replace(".P", ""), interval=interval, limit=1)
        futures_vol = float(futures_klines[0][5]) if futures_klines else 0

        # Соотношение S/B (по свечам)
        buy_vol = max(float(klines[0][2]) - float(klines[0][1]), 0) if klines else 0
        sell_vol = max(float(klines[0][1]) - float(klines[0][2]), 0) if klines else 0
        total = buy_vol + sell_vol if buy_vol + sell_vol > 0 else 1
        buy_percent = round(buy_vol / total * 100)
        sell_percent = round(sell_vol / total * 100)

        return spot_vol, futures_vol, buy_percent, sell_percent

    except Exception as e:
        print("Error getting Binance volumes:", e)
        return 0,0,0,0

# -------------------- Вычисление Unusual Activity --------------------
def get_unusual_activity(symbol, current_time):
    if symbol in last_signal_time:
        delta_seconds = (current_time - last_signal_time[symbol]).total_seconds()
        unusual = f"+{int(delta_seconds)}s"
    else:
        unusual = ""
    last_signal_time[symbol] = current_time
    return unusual

# -------------------- Обработчик сигналов от TradingView --------------------
@app.post("/tv-signal")
async def tv_signal(request: Request):
    data = await request.json()
    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    symbol = data.get("symbol")
    interval = data.get("interval")
    signal = data.get("signal")
    price = data.get("price")
    signal_time_str = data.get("time") 
    spot_vol = data.get("spot_vol", "")
    futures_vol = data.get("futures_vol", "")
    unusual_activity = data.get("unusual_activity", "")
    sb = data.get("sb", "")

    try:
        signal_time = datetime.fromisoformat(signal_time_str.replace("Z", "+00:00")).astimezone(timezone.utc)
    except:
        signal_time = datetime.now(timezone.utc)

    # -------------------- Получаем объёмы и соотношение --------------------
    spot_vol, futures_vol, buy_percent, sell_percent = get_binance_volumes(symbol, interval)

    # -------------------- Unusual Activity --------------------
    unusual_activity = get_unusual_activity(symbol, signal_time)

    # -------------------- Формируем сообщение --------------------
    signal_emoji = "⬆️" if "BUY" in signal.upper() else "⬇️"
    message = (
        f"{symbol} | {interval} | {signal.upper()}{signal_emoji}\n"
        f"Price: {price}\n"
        f"Spot Vol: {spot_vol}\n"
        f"Futures Vol: {futures_vol}\n"
        f"Unusual Activity: {unusual_activity}\n"
        f"S/B: {buy_percent}/{sell_percent}"
    )

    # -------------------- Отправка в Telegram --------------------
    send_telegram(TELEGRAM_CHAT_ID, message)
    print("Sent signal:", message)

    return {"status": "ok"}
