from fastapi import FastAPI, Request
import os
import requests
from datetime import datetime, timezone

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TV_WEBHOOK_SECRET = "dessston"  # фиксированный секрет

bot_enabled = True


def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text})


@app.api_route("/tv-signal", methods=["POST"])
async def webhook(request: Request):
    global bot_enabled
    data = await request.json()

    # Проверяем секрет
    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    # Проверяем время сигнала
    try:
        tv_time = datetime.fromisoformat(data["time"].replace("Z", "+00:00"))  # ISO8601 в datetime
        now = datetime.now(timezone.utc)
        delay = (now - tv_time).total_seconds()
        if delay > 120:  # более 2 минут задержки
            print(f"Сигнал отклонен (задержка {delay} сек):", data)
            return {"status": "ignored", "reason": "too late"}
    except Exception as e:
        print("Ошибка парсинга времени:", e)

    # Отправляем сигнал в Telegram, если бот включен
    if bot_enabled:
        message = f"{data['symbol']} | {data['interval']} | {data['signal']} | Price: {data['price']}"
        send_telegram(TELEGRAM_CHAT_ID, message)
        print("Сигнал отправлен:", message)
    else:
        print("Сигнал получен, но бот выключен.")

    return {"status": "ok"}
