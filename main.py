from fastapi import FastAPI, Request
import os
import requests
from datetime import datetime, timezone

app = FastAPI()

# -------------------- Конфиги --------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET")  # dessston

# -------------------- Функция отправки сообщений --------------------
def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text})

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

    # -------------------- Время сигнала --------------------
    try:
        signal_time = datetime.fromisoformat(signal_time_str.replace("Z", "+00:00")).astimezone(timezone.utc)
    except:
        signal_time = datetime.now(timezone.utc)

    # -------------------- Формируем текст --------------------
    message = f"{symbol} | {interval} | {signal} | Price: {price}"

    # -------------------- Отправляем в Telegram --------------------
    send_telegram(TELEGRAM_CHAT_ID, message)
    print("Sent signal:", message)

    return {"status": "ok"}

# ---- Пинг для хостинга ----
@app.get("/ping")
async def ping():
    return {"status": "ok"}
