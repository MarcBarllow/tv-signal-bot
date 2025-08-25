from fastapi import FastAPI, Request
import os
import requests
import json

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET")

ADMIN_IDS = [8200781854, 885033881]
bot_enabled = True

# -------------------- Состояние монет --------------------
coin_state = {
    "Main": {"BTCUSDT.P": True, "ETHUSDT.P": True, "SOLUSDT.P": True, "XRPUSDT.P": True},
    "DEFI": {"AAVEUSDT.P": True, "ENAUSDT.P": True, "HYPEUSDT.P": True, "JTOUSDT.P": True, "JUPUSDT.P": True, "LDOUSDT.P": True, "LINKUSDT.P": True, "UNIUSDT.P": True},
    "Meme": {"1000PEPEUSDT.P": True, "DOGEUSDT.P": True, "FARTUSDT.P": True, "ORDIUSDT.P": True, "PENGUUSDT.P": True, "POPUSDT.P": True, "PUMPUSDT.P": True, "WIFUSDT.P": True},
    "AI": {"AI16ZUSDT.P": True, "ARCUSDT.P": True, "FHEUSDT.P": True, "API3USDT.P": True},
    "Layer 1 & 2": {"APTUSDT.P": True, "AVAXUSDT.P": True, "BCHUSDT.P": True, "BNBUSDT.P": True, "OPUSDT.P": True, "SEIUSDT.P": True, "SUIUSDT.P": True, "TIAUSDT.P": True, "WLDUSDT.P": True},
    "Lst": {"LDOUSDT.P": True, "LAYERUSDT.P": True, "FXSUSDT.P": True}
}

# -------------------- Функция отправки сообщений --------------------
def send_telegram(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    requests.post(url, data=data)

# -------------------- Главное меню --------------------
def send_main_menu(chat_id):
    keyboard = {
        "inline_keyboard": [
            [{"text": "Bot On✅", "callback_data": "bot_on"}, {"text": "Bot Off❌", "callback_data": "bot_off"}, {"text": "Status ℹ️", "callback_data": "bot_status"}],
            [{"text": "Tokens", "callback_data": "tokens"}]
        ]
    }
    send_telegram(chat_id, "Главное меню:", reply_markup=keyboard)

# -------------------- Панель монет --------------------
def send_coin_panel(chat_id, section):
    coins = coin_state[section]
    keyboard = []
    for coin, state in coins.items():
        emoji = "✅" if state else "❌"
        keyboard.append([{"text": f"{coin} {emoji}", "callback_data": f"toggle_{section}_{coin}"}])
    keyboard.append([{"text": "Назад 🔙", "callback_data": "back"}])
    reply_markup = {"inline_keyboard": keyboard}
    send_telegram(chat_id, f"{section}:", reply_markup=reply_markup)

# -------------------- Обработчик сигналов от TV --------------------
@app.api_route("/tv-signal", methods=["POST"])
async def webhook(request: Request):
    global bot_enabled
    data = await request.json()
    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    if bot_enabled:
        message = f"{data['symbol']} | {data['interval']} | {data['signal']} | Price: {data['price']}"
        send_telegram(TELEGRAM_CHAT_ID, message)
        print("Сигнал отправлен:", message)
    return {"status": "ok"}

# -------------------- Управление ботом --------------------
@app.post("/bot-control")
async def bot_control(request: Request):
    global bot_enabled
    data = await request.json()

    if "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        user_id = query["from"]["id"]
        action = query["data"]

        if user_id not in ADMIN_IDS:
            return {"ok": True}

        if action == "bot_on":
            bot_enabled = True
            send_telegram(chat_id, "✅ Бот включен. Сигналы отправляются.")
            send_main_menu(chat_id)
        elif action == "bot_off":
            bot_enabled = False
            send_telegram(chat_id, "⛔ Бот выключен. Сигналы не отправляются.")
            send_main_menu(chat_id)
        elif action == "bot_status":
            status = "включен ✅" if bot_enabled else "выключен ⛔"
            send_telegram(chat_id, f"Статус бота: {status}")
        elif action == "tokens":
            for section in coin_state.keys():
                send_coin_panel(chat_id, section)
        elif action.startswith("toggle_"):
            _, section, coin = action.split("_", 2)
            coin_state[section][coin] = not coin_state[section][coin]
            send_coin_panel(chat_id, section)
        elif action == "back":
            send_main_menu(chat_id)

    elif "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_id = data["message"]["from"]["id"]
        text = data["message"]["text"].strip().lower()
        if user_id not in ADMIN_IDS:
            return {"status": "error", "message": "Unauthorized"}

        if text == "/on":
            bot_enabled = True
            send_telegram(chat_id, "✅ Бот включен. Сигналы отправляются.")
            send_main_menu(chat_id)
        elif text == "/off":
            bot_enabled = False
            send_telegram(chat_id, "⛔ Бот выключен. Сигналы не отправляются.")
            send_main_menu(chat_id)
        elif text == "/status":
            status = "включен ✅" if bot_enabled else "выключен ⛔"
            send_telegram(chat_id, f"Статус бота: {status}")
        elif text == "/start":
            send_main_menu(chat_id)

    return {"ok": True}

# -------------------- Ping --------------------
@app.post("/ping")
async def ping_endpoint(request: Request):
    data = await request.json()
    print("Ping received:", data)
    return {"status": "ok"}

# -------------------- Отправка панели при запуске --------------------
@app.on_event("startup")
async def startup_event():
    for admin_id in ADMIN_IDS:
        send_main_menu(admin_id)
