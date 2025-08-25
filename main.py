from fastapi import FastAPI, Request
import os
import requests

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET")  # dessston

ADMIN_IDS = [8200781854, 885033881] 
bot_enabled = True             


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


@app.post("/bot-control")
async def bot_control(request: Request):
    global bot_enabled
    data = await request.json()

    if "message" not in data or "text" not in data["message"]:
        return {"status": "error", "message": "Invalid payload"}

    chat_id = data["message"]["chat"]["id"]
    user_id = data["message"]["from"]["id"]
    text = data["message"]["text"].strip().lower()

    if user_id not in ADMIN_IDS:
        return {"status": "error", "message": "Unauthorized"}

    if text == "/on":
        bot_enabled = True
        send_telegram(chat_id, "✅ Бот включен. Сигналы отправляются.")
    elif text == "/off":
        bot_enabled = False
        send_telegram(chat_id, "⛔ Бот выключен. Сигналы не отправляются.")
    elif text == "/status":
        status = "включен ✅" if bot_enabled else "выключен ⛔"
        send_telegram(chat_id, f"Статус бота: {status}")
    else:
        send_telegram(chat_id, "Команды: /on — включить, /off — выключить, /status — статус")

    return {"status": "ok"}


def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text})
