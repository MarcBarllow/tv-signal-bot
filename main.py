from fastapi import FastAPI, Request
import os
import requests
from datetime import datetime, timezone
import json

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET")  # dessston

# -------------------- Отправка сообщений --------------------
def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text})

# -------------------- Обработчик сигналов --------------------
@app.api_route("/tv-signal", methods=["POST"])
async def tv_signal(request: Request):
    data = await request.json()

    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    # Фильтр задержки сигналов > 2 минут
    signal_time = datetime.fromisoformat(data["time"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    if (now - signal_time).total_seconds() > 120:
        print("Сигнал пропущен из-за задержки:", data)
        return {"status": "ignored", "message": "Signal too old"}

    message = f"{data['symbol']} | {data['interval']} | {data['signal']} | Price: {data['price']}"
    send_telegram(TELEGRAM_CHAT_ID, message)
    print("Telegram message:", message)

    return {"status": "ok"}

# -------------------- Ping endpoint --------------------
@app.post("/ping")
async def ping(request: Request):
    data = await request.json()
    print("Ping received:", data)
    return {"status": "ok"}
