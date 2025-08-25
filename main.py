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

# -------------------- Монеты по секциям --------------------
SECTIONS = {
    "Main": ["BTCUSDT.P", "ETHUSDT.P", "SOLUSDT.P", "XRPUSDT.P"],
    "DEFI": ["AAVEUSDT.P", "ENAUSDT.P", "HYPEUSDT.P", "JTOUSDT.P", "JUPUSDT.P", "LDOUSDT.P", "LINKUSDT.P", "UNIUSDT.P"],
    "Meme": ["1000PEPEUSDT.P", "DOGEUSDT.P", "FARTCOINUSDT.P", "ORDIUSDT.P", "PENGUUSDT.P", "POPUSDT.P", "PUMPUSDT.P", "WIFUSDT.P"],
    "AI": ["AI16ZUSDT.P", "ARCUSDT.P", "FHEUSDT.P", "API3USDT.P"],
    "Layer 1 & 2": ["APTUSDT.P", "AVAXUSDT.P", "BCHUSDT.P", "BNBUSDT.P", "OPUSDT.P", "SEIUSDT.P", "SUIUSDT.P", "TIAUSDT.P", "WLDUSDT.P"],
    "Lst": ["LDOUSDT.P", "LAYERUSDT.P", "FXSUSDT.P"]
}

# Отслеживаем, какие монеты включены
enabled_coins = {coin: True for section in SECTIONS.values() for coin in section}

# -------------------- Функция отправки сообщений --------------------
def send_telegram(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    requests.post(url, data=data)

# -------------------- Панель управления --------------------
def get_main_menu():
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "Bot On✅", "callback_data": "bot_on"},
                {"text": "Bot Off❌", "callback_data": "bot_off"},
                {"text": "Status ℹ️", "callback_data": "bot_status"}
            ],
            [{"text": "Tokens", "callback_data": "tokens"}]
        ]
    }
    return keyboard

def get_sections_menu():
    keyboard = {"inline_keyboard": [[{"text": section, "callback_data": f"section_{section}"}] for section in SECTIONS.keys()]}
    keyboard["inline_keyboard"].append([{"text": "Back 🔙", "callback_data": "back_main"}])
    return keyboard

def get_tokens_menu(section):
    keyboard = []
    for coin in SECTIONS[section]:
        symbol = "✅" if enabled_coins[coin] else "❌"
        keyboard.append([{"text": f"{coin} {symbol}", "callback_data": f"toggle_{coin}"}])
    keyboard.append([{"text": "Back 🔙", "callback_data": "back_sections"}])
    return {"inline_keyboard": keyboard}

def send_control_panel():
    for admin_id in ADMIN_IDS:
        send_telegram(admin_id, "Главное меню управления ботом:", reply_markup=get_main_menu())

# -------------------- Обработчик сигналов от TradingView --------------------
@app.api_route("/tv-signal", methods=["POST"])
async def webhook(request: Request):
    data = await request.json()
    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    if bot_enabled and enabled_coins.get(data["symbol"], False):
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

    if "callback_query" not in data:
        return {"ok": True}
    query = data["callback_query"]
    chat_id = query["message"]["chat"]["id"]
    user_id = query["from"]["id"]
    action = query["data"]

    if user_id not in ADMIN_IDS:
        send_telegram(chat_id, "⛔ У вас нет прав управления ботом.")
        return {"ok": True}

    # -------------------- Главные кнопки --------------------
    if action == "bot_on":
        bot_enabled = True
        send_telegram(chat_id, "✅ Бот включен. Сигналы отправляются.", reply_markup=get_main_menu())
    elif action == "bot_off":
        bot_enabled = False
        send_telegram(chat_id, "⛔ Бот выключен. Сигналы не отправляются.", reply_markup=get_main_menu())
    elif action == "bot_status":
        status = "включен ✅" if bot_enabled else "выключен ⛔"
        send_telegram(chat_id, f"Статус бота: {status}", reply_markup=get_main_menu())
    elif action == "tokens":
        send_telegram(chat_id, "Выберите секцию токенов:", reply_markup=get_sections_menu())
    # -------------------- Секции --------------------
    elif action.startswith("section_"):
        section = action.replace("section_", "")
        send_telegram(chat_id, f"Монеты секции {section}:", reply_markup=get_tokens_menu(section))
    elif action.startswith("toggle_"):
        coin = action.replace("toggle_", "")
        enabled_coins[coin] = not enabled_coins[coin]
        # Меняем только галочку, не отправляем новых сообщений
    elif action == "back_main":
        send_telegram(chat_id, "Главное меню управления ботом:", reply_markup=get_main_menu())
    elif action == "back_sections":
        send_telegram(chat_id, "Выберите секцию токенов:", reply_markup=get_sections_menu())

    return {"ok": True}

# -------------------- При запуске отправляем панель управления --------------------
@app.on_event("startup")
async def startup_event():
    send_control_panel()
