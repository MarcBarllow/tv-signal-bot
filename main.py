from fastapi import FastAPI, Request
import os
import requests
from datetime import datetime, timezone

app = FastAPI()

# -------------------- Настройки --------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET")  # dessston

# -------------------- Функция отправки сообщений --------------------
def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text})

# -------------------- Обработчик сигналов от TradingView --------------------
@app.api_route("/tv-signal", methods=["POST"])
async def webhook(request: Request):
    data = await request.json()

    # Проверка секрета
    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    # Проверка времени сигнала (не старше 2 минут)
    if "time" in data:
        try:
            signal_time = datetime.fromisoformat(data["time"])
        except Exception:
            return {"status": "error", "message": "Invalid time format"}

        now = datetime.now(timezone.utc)
        if (now - signal_time).total_seconds() > 120:  # 2 минуты
            print("Старый сигнал, пропускаем:", data)
            return {"status": "ignored", "message": "Signal too old"}

    # Формируем сообщение для Telegram
    message = f"{data['symbol']} | {data['interval']} | {data['signal']} | Price: {data['price']}"
    send_telegram(TELEGRAM_CHAT_ID, message)
    print("Сигнал отправлен:", message)

    return {"status": "ok"}

# -------------------- Ping endpoint --------------------
@app.post("/ping")
async def ping_endpoint(request: Request):
    data = await request.json()
    print("Ping received:", data)
    return {"status": "ok"}
