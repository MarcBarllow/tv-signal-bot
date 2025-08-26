from fastapi import FastAPI, Request
import os
import requests
from datetime import datetime, timezone, timedelta

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET")  # dessston

# Максимальный возраст сигнала в минутах
MAX_SIGNAL_AGE_MIN = 2

# -------------------- Функция отправки сообщений в Telegram --------------------
def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text})

# -------------------- Обработчик сигналов от TradingView --------------------
@app.api_route("/tv-signal", methods=["POST"])
async def tv_signal(request: Request):
    data = await request.json()

    # Проверка секрета
    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    # Проверка времени сигнала
    if "time" not in data:
        return {"status": "error", "message": "Missing time field"}

    try:
        signal_time = datetime.fromisoformat(data["time"].replace("Z", "+00:00"))
    except Exception:
        return {"status": "error", "message": "Invalid time format"}

    now = datetime.now(timezone.utc)
    age = now - signal_time
    if age > timedelta(minutes=MAX_SIGNAL_AGE_MIN):
        print(f"Сигнал {data['symbol']} пропущен, старше {MAX_SIGNAL_AGE_MIN} мин: {data}")
        return {"status": "ok", "message": "Signal too old, ignored"}

    # Формируем сообщение
    message = f"{data['symbol']} | {data['interval']} | {data['signal']} | Price: {data['price']}"
    send_telegram(TELEGRAM_CHAT_ID, message)
    print("Сигнал отправлен:", message)

    return {"status": "ok"}

# -------------------- Ping endpoint для тестов --------------------
@app.post("/ping")
async def ping_endpoint(request: Request):
    data = await request.json()
    print("Ping received:", data)
    return {"status": "ok"}
