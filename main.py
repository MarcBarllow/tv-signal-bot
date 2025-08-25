from fastapi import FastAPI, Request
import os
import requests
import json

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET")  # dessston

ADMIN_IDS = [8200781854, 885033881] 
bot_enabled = True

# -------------------- Токены --------------------
SECTIONS = {
    "Main": ["BTCUSDT.P", "ETHUSDT.P", "SOLUSDT.P", "XRPUSDT.P"],
    "DEFI": ["AAVEUSDT.P", "ENAUSDT.P", "HYPEUSDT.P", "JTOUSDT.P", "JUPUSDT.P", "LDOUSDT.P", "LINKUSDT.P", "UNIUSDT.P"],
    "Meme": ["1000PEPEUSDT.P", "DOGEUSDT.P", "FARTCOINUSDT.P", "ORDIUSDT.P", "PENGUUSDT.P", "POPUSDT.P", "PUMPUSDT.P", "WIFUSDT.P"],
    "AI": ["AI16ZUSDT.P", "ARCUSDT.P", "FHEUSDT.P", "API3USDT.P"],
    "Layer 1 & 2": ["APTUSDT.P", "AVAXUSDT.P", "BCHUSDT.P", "BNBUSDT.P", "OPUSDT.P", "SEIUSDT.P", "SUIUSDT.P", "TIAUSDT.P", "WLDUSDT.P"],
    "Lst": ["LDOUSDT.P", "LAYERUSDT.P", "FXSUSDT.P"]
}

# Состояние токенов: True = включен
token_states = {token: True for section in SECTIONS.values() for token in section}

# -------------------- Функция отправки сообщений --------------------
def send_telegram(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    requests.post(url, data=data)

# -------------------- Панель управления ботом --------------------
def send_control_panel():
    keyboard = {
        "inline_keyboard": [
            [{"text": "Bot On ✅", "callback_data": "enable"}],
            [{"text": "Bot Off ❌", "callback_data": "disable"}],
            [{"text": "Status ℹ️", "callback_data": "status"}],
            [{"text": "Tokens", "callback_data": "tokens"}]
        ]
    }
    for admin_id in ADMIN_IDS:
        send_telegram(admin_id, "Управление ботом:", reply_markup=keyboard)

# -------------------- Клавиатура токенов --------------------
def build_token_keyboard(section_tokens):
    keyboard = []
    row = []
    for i, token in enumerate(section_tokens, 1):
        state = "✅" if token_states.get(token, True) else "❌"
        row.append({"text": f"{token} {state}", "callback_data": token})
        if i % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([{"text": "Назад 🔙", "callback_data": "back"}])
    return {"inline_keyboard": keyboard}

def send_section_panel(chat_id, section_tokens, message_id=None):
    keyboard = build_token_keyboard(section_tokens)
    if message_id:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/editMessageReplyMarkup", data={
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": json.dumps(keyboard)
        })
    else:
        send_telegram(chat_id, "Выберите токены:", reply_markup=keyboard)

# -------------------- Вспомогательные функции --------------------
def toggle_token(token):
    token_states[token] = not token_states.get(token, True)

def get_section_tokens(token):
    for section in SECTIONS.values():
        if token in section:
            return section
    return []

# -------------------- Обработчик сигналов от TradingView --------------------
@app.api_route("/tv-signal", methods=["POST"])
async def webhook(request: Request):
    global bot_enabled
    data = await request.json()
    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    if bot_enabled and token_states.get(data["symbol"], False):
        message = f"{data['symbol']} | {data['interval']} | {data['signal']} | Price: {data['price']}"
        for admin_id in ADMIN_IDS:
            send_telegram(admin_id, message)
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

# -------------------- Управление ботом через команды и кнопки --------------------
@app.post("/bot-control")
async def bot_control(request: Request):
    global bot_enabled
    data = await request.json()

    # Callback кнопок
    if "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        user_id = query["from"]["id"]
        action = query["data"]
        message_id = query["message"]["message_id"]

        if user_id not in ADMIN_IDS:
            send_telegram(chat_id, "⛔ У вас нет прав управления ботом.")
            return {"ok": True}

        if action == "enable":
            bot_enabled = True
            send_control_panel()
        elif action == "disable":
            bot_enabled = False
            send_control_panel()
        elif action == "status":
            status = "включен ✅" if bot_enabled else "выключен ⛔"
            send_telegram(chat_id, f"Статус бота: {status}")
        elif action == "tokens":
            # Показываем секции
            keyboard = {"inline_keyboard": [[{"text": s, "callback_data": f"section_{s}"}] for s in SECTIONS.keys()]}
            keyboard["inline_keyboard"].append([{"text": "Назад 🔙", "callback_data": "back"}])
            send_telegram(chat_id, "Выберите секцию:", reply_markup=keyboard)
        elif action.startswith("section_"):
            section_name = action.replace("section_", "")
            send_section_panel(chat_id, SECTIONS[section_name], message_id=message_id)
        elif action in token_states:
            toggle_token(action)
            section_tokens = get_section_tokens(action)
            send_section_panel(chat_id, section_tokens, message_id=message_id)
        elif action == "back":
            send_control_panel()

    # Текстовые команды
    elif "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_id = data["message"]["from"]["id"]
        text = data["message"]["text"].strip().lower()
        if user_id not in ADMIN_IDS:
            return {"status": "error", "message": "Unauthorized"}

        if text == "/on":
            bot_enabled = True
            send_control_panel()
        elif text == "/off":
            bot_enabled = False
            send_control_panel()
        elif text == "/status":
            status = "включен ✅" if bot_enabled else "выключен ⛔"
            send_telegram(chat_id, f"Статус бота: {status}")
        elif text == "/tokens":
            keyboard = {"inline_keyboard": [[{"text": s, "callback_data": f"section_{s}"}] for s in SECTIONS.keys()]}
            keyboard["inline_keyboard"].append([{"text": "Назад 🔙", "callback_data": "back"}])
            send_telegram(chat_id, "Выберите секцию:", reply_markup=keyboard)

    return {"ok": True}

# -------------------- При запуске --------------------
@app.on_event("startup")
async def startup_event():
    send_control_panel()
