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

# Статус монет (True = активна, False = отключена)
coin_status = {}

# -------------------- Список монет по секциям --------------------
sections = {
    "Main": ["BTCUSDT.P", "ETHUSDT.P", "SOLUSDT.P", "XRPUSDT.P"],
    "DEFI": ["AAVEUSDT.P","ENAUSDT.P","HYPEUSDT.P","JTOUSDT.P","JUPUSDT.P","LDOUSDT.P","LINKUSDT.P","UNIUSDT.P"],
    "Meme": ["1000PEPEUSDT.P","DOGEUSDT.P","FARTCOINUSDT.P","ORDIUSDT.P","PENGUUSDT.P","POPCATUSDT.P","PUMPUSDT.P","WIFUSDT.P"],
    "AI": ["AI16ZUSDT.P","ARCUSDT.P","FHEUSDT.P","API3USDT.P"],
    "Layer1&2": ["APTUSDT.P","AVAXUSDT.P","BCHUSDT.P","BNBUSDT.P","OPUSDT.P","SEIUSDT.P","SUIUSDT.P","TIAUSDT.P","WLDUSDT.P"],
    "Lst": ["LDOUSDT.P","LAYERUSDT.P","FXSUSDT.P"]
}

# Инициализация статуса монет
for sec_coins in sections.values():
    for coin in sec_coins:
        coin_status[coin] = True

# -------------------- Функция отправки сообщений --------------------
def send_telegram(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    requests.post(url, data=data)

# -------------------- Клавиатуры --------------------
def build_main_keyboard():
    keyboard = [
        [
            {"text": "Bot On ✅", "callback_data": "enable"},
            {"text": "Bot Off ❌", "callback_data": "disable"},
            {"text": "Status ℹ️", "callback_data": "status"}
        ],
        [
            {"text": "Tokens 🎯", "callback_data": "tokens"}
        ]
    ]
    return {"inline_keyboard": keyboard}

def build_tokens_keyboard(section=None):
    keyboard = []
    if section is None:
        # Главное меню секций
        row = []
        for sec in sections.keys():
            row.append({"text": sec, "callback_data": f"section_{sec}"})
            if len(row) >= 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([{"text": "Back ⬅️", "callback_data": "back"}])
    else:
        # Кнопки монет конкретной секции
        row = []
        for coin in sections[section]:
            emoji = "✅" if coin_status.get(coin, True) else "❌"
            row.append({"text": f"{coin} {emoji}", "callback_data": f"coin_{coin}"})
            if len(row) >= 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([{"text": "Back ⬅️", "callback_data": "tokens"}])
    return {"inline_keyboard": keyboard}

# -------------------- Панель управления --------------------
def send_control_panel():
    for admin_id in ADMIN_IDS:
        send_telegram(admin_id, "Управление ботом:", reply_markup=build_main_keyboard())

# -------------------- Обработчик сигналов от TradingView --------------------
@app.api_route("/tv-signal", methods=["POST"])
async def webhook(request: Request):
    global bot_enabled
    data = await request.json()

    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    coin = data["symbol"]
    if bot_enabled and coin_status.get(coin, True):
        message = f"{data['symbol']} | {data['interval']} | {data['signal']} | Price: {data['price']}"
        send_telegram(TELEGRAM_CHAT_ID, message)
        print("Сигнал отправлен:", message)
    else:
        print("Сигнал получен, но бот выключен или монета отключена.")

    return {"status": "ok"}

# -------------------- Ping endpoint --------------------
@app.post("/ping")
async def ping_endpoint(request: Request):
    data = await request.json()
    print("Ping received:", data)
    return {"status": "ok"}

# -------------------- Управление ботом через кнопки --------------------
@app.post("/bot-control")
async def bot_control(request: Request):
    global bot_enabled
    data = await request.json()

    chat_id = None
    user_id = None
    action = None

    # Обработка callback кнопок
    if "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        user_id = query["from"]["id"]
        action = query["data"]

        if user_id not in ADMIN_IDS:
            send_telegram(chat_id, "⛔ У вас нет прав управления ботом.")
            return {"ok": True}

        # Вкл/Выкл/Статус
        if action == "enable":
            bot_enabled = True
        elif action == "disable":
            bot_enabled = False
        elif action == "status":
            status = "включен ✅" if bot_enabled else "выключен ⛔"
            send_telegram(chat_id, f"Статус бота: {status}")
        elif action == "tokens":
            send_telegram(chat_id, "Выберите секцию:", reply_markup=build_tokens_keyboard())
        elif action.startswith("section_"):
            sec_name = action.replace("section_", "")
            send_telegram(chat_id, f"Секция {sec_name}:", reply_markup=build_tokens_keyboard(sec_name))
        elif action.startswith("coin_"):
            coin_name = action.replace("coin_", "")
            coin_status[coin_name] = not coin_status[coin_name]  # переключаем статус
            sec_name = None
            for sec, coins in sections.items():
                if coin_name in coins:
                    sec_name = sec
                    break
            if sec_name:
                send_telegram(chat_id, f"Секция {sec_name}:", reply_markup=build_tokens_keyboard(sec_name))
        elif action == "back":
            send_telegram(chat_id, "Главное меню:", reply_markup=build_main_keyboard())

    # Обработка текстовых команд
    elif "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_id = data["message"]["from"]["id"]
        text = data["message"]["text"].strip().lower()

        if user_id not in ADMIN_IDS:
            return {"status": "error", "message": "Unauthorized"}

        if text == "/on":
            bot_enabled = True
        elif text == "/off":
            bot_enabled = False
        elif text == "/status":
            status = "включен ✅" if bot_enabled else "выключен ⛔"
            send_telegram(chat_id, f"Статус бота: {status}")
        elif text == "/tokens":
            send_telegram(chat_id, "Выберите секцию:", reply_markup=build_tokens_keyboard())
        else:
            send_telegram(chat_id, "Команды: /on, /off, /status, /tokens")

    return {"ok": True}

# -------------------- При запуске отправляем панель управления --------------------
@app.on_event("startup")
async def startup_event():
    send_control_panel()
