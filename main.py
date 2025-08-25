from fastapi import FastAPI, Request
import os
import requests
import json

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET")  # dessston

ADMIN_IDS = [8200781854, 885033881] 
bot_enabled = True             


# -------------------- Функция отправки сообщений --------------------
def send_telegram(chat_id, text, reply_markup=None):
    # ---- Здесь формируется URL для Telegram ----
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    requests.post(url, data=data)  # <--- запрос к Telegram API


# -------------------- Панель управления --------------------
def send_control_panel():
    keyboard = {
        "inline_keyboard": [
            [{"text": "Включить ✅", "callback_data": "enable"}],
            [{"text": "Выключить ❌", "callback_data": "disable"}],
            [{"text": "Статус ℹ️", "callback_data": "status"}]
        ]
    }
    for admin_id in ADMIN_IDS:
        send_telegram(admin_id, "Управление ботом:", reply_markup=keyboard)  # <--- здесь тоже URL


# -------------------- Обработчик сигналов от TradingView --------------------
@app.api_route("/tv-signal", methods=["POST"])
async def webhook(request: Request):
    global bot_enabled
    data = await request.json()

    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    if bot_enabled:
        message = f"{data['symbol']} | {data['interval']} | {data['signal']} | Price: {data['price']}"
        send_telegram(TELEGRAM_CHAT_ID, message)  # <--- здесь URL для отправки сигнала
        print("Сигнал отправлен:", message)
    else:
        print("Сигнал получен, но бот выключен.")

    return {"status": "ok"}


# -------------------- Ping endpoint --------------------
@app.post("/ping")
async def ping_endpoint(request: Request):
    data = await request.json()
    print("Ping received:", data)
    return {"status": "ok"}


# -------------------- Управление ботом через команды и кнопки --------------------
@app.post("/bot-control")
async def bot_control(request: Request):
    global bot_enabled
    data = await request.json()

    # Обработка callback от кнопок
    if "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        user_id = query["from"]["id"]
        action = query["data"]

        if user_id not in ADMIN_IDS:
            send_telegram(chat_id, "⛔ У вас нет прав управления ботом.")  # <--- URL
            return {"ok": True}

        if action == "enable":
            bot_enabled = True
            send_telegram(chat_id, "✅ Бот включен. Сигналы отправляются.")  # <--- URL
        elif action == "disable":
            bot_enabled = False
            send_telegram(chat_id, "⛔ Бот выключен. Сигналы не отправляются.")  # <--- URL
        elif action == "status":
            status = "включен ✅" if bot_enabled else "выключен ⛔"
            send_telegram(chat_id, f"Статус бота: {status}")  # <--- URL

    # Обработка текстовых команд
    elif "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_id = data["message"]["from"]["id"]
        text = data["message"]["text"].strip().lower()

        if user_id not in ADMIN_IDS:
            return {"status": "error", "message": "Unauthorized"}

        if text == "/on":
            bot_enabled = True
            send_telegram(chat_id, "✅ Бот включен. Сигналы отправляются.")  # <--- URL
        elif text == "/off":
            bot_enabled = False
            send_telegram(chat_id, "⛔ Бот выключен. Сигналы не отправляются.")  # <--- URL
        elif text == "/status":
            status = "включен ✅" if bot_enabled else "выключен ⛔"
            send_telegram(chat_id, f"Статус бота: {status}")  # <--- URL
        else:
            send_telegram(chat_id, "Команды: /on — включить, /off — выключить, /status — статус")  # <--- URL

    return {"ok": True}


# -------------------- При запуске отправляем панель управления --------------------
@app.on_event("startup")
async def startup_event():
    send_control_panel()  # <--- URL через send_telegram для панели кнопок
