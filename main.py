# main.py
from fastapi import FastAPI, Request
import os
import requests

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET")  # например "dessston"

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    
    # Проверка секрета
    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    # Формируем сообщение для Telegram
    message = f"{data['symbol']} | {data['interval']} | {data['signal']} | Price: {data['price']}"
    
    # Отправляем в Telegram
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=payload)

    return {"status": "ok"}
