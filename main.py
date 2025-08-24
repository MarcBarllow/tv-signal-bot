# main.py
from fastapi import FastAPI, Request
import os
import requests

app = FastAPI()

# ----------------- Переменные окружения -----------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")          # токен от BotFather
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")      # chat_id канала (-100XXXX для приватного)
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET")    # секрет, например "dessston"

# ----------------- Обработчик POST -----------------
@app.post("/")  # обработка POST на корень URL
async def webhook(request: Request):
    data = await request.json()

    # Проверка секрета
    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    # Формируем сообщение для Telegram
    message = f"{data['symbol']} | {data['interval']} | {data['signal']} | Price: {data['price']}"
    print("Telegram message:", message)  # для логов Render

    # Отправляем в Telegram
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=payload)

    return {"status": "ok"}
