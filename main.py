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

# -------------------- Словари токенов --------------------
tokens = {
    "Main": ["BTCUSDT.P", "ETHUSDT.P", "SOLUSDT.P", "XRPUSDT.P"],
    "DEFI": ["AAVEUSDT.P", "ENAUSDT.P", "HYPEUSDT.P", "JTOUSDT.P", "JUPUSDT.P", "LDOUSDT.P", "LINKUSDT.P", "UNIUSDT.P"],
    "Meme": ["1000PEPEUSDT.P", "DOGEUSDT.P", "FARTCOINUSDT.P", "ORDIUSDT.P", "PENGUUSDT.P", "POPUSDT.P", "PUMPUSDT.P", "WIFUSDT.P"],
    "AI": ["AI16ZUSDT.P", "ARCUSDT.P", "FHEUSDT.P", "API3USDT.P"],
    "Layer": ["APTUSDT.P", "AVAXUSDT.P", "BCHUSDT.P", "BNBUSDT.P", "OPUSDT.P", "SEIUSDT.P", "SUIUSDT.P", "TIAUSDT.P", "WLDUSDT.P"],
    "Lst": ["LDOUSDT.P", "LAYERUSDT.P", "FXSUSDT.P"]
}

tokens_status = {}
for section, t_list in tokens.items():
    for t in t_list:
        tokens_status[t] = True  # По умолчанию все включены

# -------------------- Функция отправки сообщений --------------------
def send_telegram(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    requests.post(url, data=data)

# -------------------- Удаление сообщения --------------------
def delete_message(chat_id, message_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteMessage"
    requests.post(url, data={"chat_id": chat_id, "message_id": message_id})

# -------------------- Панель управления --------------------
def send_control_panel(chat_id):
    keyboard = {
        "inline_keyboard": [
            [{"text": "Bot On ✅", "callback_data": "enable"}],
            [{"text": "Bot Off ❌", "callback_data": "disable"}],
            [{"text": "Status ℹ️", "callback_data": "status"}],
            [{"text": "Tokens", "callback_data": "tokens"}]
        ]
    }
    send_telegram(chat_id, "Управление ботом:", reply_markup=keyboard)

# -------------------- Панель токенов --------------------
def send_tokens_panel(chat_id):
    keyboard = [
        [{"text": "Main", "callback_data": "section_Main"}],
        [{"text": "DEFI", "callback_data": "section_DEFI"}],
        [{"text": "Meme", "callback_data": "section_Meme"}],
        [{"text": "AI", "callback_data": "section_AI"}],
        [{"text": "Layer 1 & 2", "callback_data": "section_Layer"}],
        [{"text": "Lst", "callback_data": "section_Lst"}],
        [{"text": "Назад 🔙", "callback_data": "back_main"}]
    ]
    send_telegram(chat_id, "Tokens:", reply_markup={"inline_keyboard": keyboard})

# -------------------- Список токенов в секции --------------------
def send_tokens_list(chat_id, section_name):
    keyboard = []
    for token in tokens[section_name]:
        emoji = "✅" if tokens_status[token] else "❌"
        keyboard.append([{"text": f"{token} {emoji}", "callback_data": f"toggle_{token}"}])
    keyboard.append([{"text": "Назад 🔙", "callback_data": "back_tokens"}])
    send_telegram(chat_id, f"{section_name} Tokens:", reply_markup={"inline_keyboard": keyboard})

# -------------------- Обработчик сигналов от TradingView --------------------
@app.api_route("/tv-signal", methods=["POST"])
async def webhook(request: Request):
    global bot_enabled
    data = await request.json()

    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    symbol = data["symbol"]
    if bot_enabled and tokens_status.get(symbol, True):
        message = f"{symbol} | {data['interval']} | {data['signal']} | Price: {data['price']}"
        send_telegram(TELEGRAM_CHAT_ID, message)
        print("Сигнал отправлен:", message)
    else:
        print("Сигнал получен, но бот выключен или токен отключен.")

    return {"status": "ok"}

# -------------------- Ping endpoint --------------------
@app.post("/ping")
async def ping_endpoint(request: Request):
    data = await request.json()
    print("Ping received:", data)
    return {"status": "ok"}

# -------------------- Управление ботом --------------------
@app.post("/bot-control")
async def bot_control(request: Request):
    global bot_enabled
    data = await request.json()

    chat_id = None
    message_id = None
    user_id = None
    action = None

    if "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        message_id = query["message"]["message_id"]
        user_id = query["from"]["id"]
        action = query["data"]
        # Удаляем предыдущую кнопку
        delete_message(chat_id, message_id)

        if user_id not in ADMIN_IDS:
            send_telegram(chat_id, "⛔ У вас нет прав управления ботом.")
            return {"ok": True}

        # ---------- Обработка действий ----------
        if action == "enable":
            bot_enabled = True
            send_telegram(chat_id, "✅ Бот включен. Сигналы отправляются.")
        elif action == "disable":
            bot_enabled = False
            send_telegram(chat_id, "⛔ Бот выключен. Сигналы не отправляются.")
        elif action == "status":
            status = "включен ✅" if bot_enabled else "выключен ⛔"
            send_telegram(chat_id, f"Статус бота: {status}")
        elif action.startswith("section_"):
            section = action.split("_")[1]
            send_tokens_list(chat_id, section)
        elif action.startswith("toggle_"):
            token = action.split("_")[1]
            tokens_status[token] = not tokens_status[token]
            send_tokens_list(chat_id, next(k for k,v in tokens.items() if token in v))
        elif action == "back_main":
            send_control_panel(chat_id)
        elif action == "back_tokens":
            send_tokens_panel(chat_id)

    elif "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_id = data["message"]["from"]["id"]
        text = data["message"]["text"].strip().lower()

        if user_id not in ADMIN_IDS:
            return {"status": "error", "message": "Unauthorized"}

        delete_message(chat_id, data["message"]["message_id"])

        if text == "/on":
            bot_enabled = True
            send_telegram(chat_id, "✅ Бот включен. Сигналы отправляются.")
        elif text == "/off":
            bot_enabled = False
            send_telegram(chat_id, "⛔ Бот выключен. Сигналы не отправляются.")
        elif text == "/status":
            status = "включен ✅" if bot_enabled else "выключен ⛔"
            send_telegram(chat_id, f"Статус бота: {status}")
        elif text == "/tokens":
            send_tokens_panel(chat_id)
        else:
            send_telegram(chat_id, "Команды: /on — включить, /off — выключить, /status — статус, /tokens — панель токенов")

    return {"ok": True}

# -------------------- При запуске --------------------
@app.on_event("startup")
async def startup_event():
    for admin_id in ADMIN_IDS:
        send_control_panel(admin_id)
