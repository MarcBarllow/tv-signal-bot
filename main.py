from fastapi import FastAPI, Request
import os
import requests

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET")  # dessston

# Обработчик POST на любом пути, который Render точно пропускает
@app.api_route("/tv-signal", methods=["POST"])
async def webhook(request: Request):
    data = await request.json()

    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    message = f"{data['symbol']} | {data['interval']} | {data['signal']} | Price: {data['price']}"
    print("Telegram message:", message)

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})

    return {"status": "ok"}
# -------------------- Ping endpoint --------------------
@app.post("/ping")
async def ping_endpoint(request: Request):
    data = await request.json()
    print("Ping received:", data)  # логируем ping, Telegram не трогаем
    return {"status": "ok"}
