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

# Монеты для управления
TOKENS = {
    "Main": ["BTCUSDT.P", "ETHUSDT.P", "SOLUSDT.P", "XRPUSDT.P"],
    "DEFI": ["AAVEUSDT.P", "ENAUSDT.P", "HYPEUSDT.P", "JTOUSDT.P", "JUPUSDT.P", "LDOUSDT.P", "LINKUSDT.P", "UNIUSDT.P"],
    "Meme": ["1000PEPEUSDT.P","DOGEUSDT.P","FARTCOINUSDT.P","ORDIUSDT.P","PENGUUSDT.P","POPUSDT.P","PUMPUSDT.P","WIFUSDT.P"],
    "AI": ["AI16ZUSDT.P","ARCUSDT.P","FHEUSDT.P","API3USDT.P"],
    "Layer 1 & 2": ["APTUSDT.P","AVAXUSDT.P","BCHUSDT.P","BNBUSDT.P","OPUSDT.P","SEIUSDT.P","SUIUSDT.P","TIAUSDT.P","WLDUSDT.P"],
    "Lst": ["LDOUSDT.P","LAYERUSDT.P","FXSUSDT.P"]
}

# Состояние монет (вкл/выкл)
token_state = {k: {t: True for t in v} for k,v in TOKENS.items()}


def send_telegram(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    requests.post(url, data=data)


# Панель управления ботом
def send_control_panel(chat_id=None):
    keyboard = {
        "inline_keyboard": [
            [{"text": "Bot On✅", "callback_data": "enable"},
             {"text": "Bot Off❌", "callback_data": "disable"},
             {"text": "Status ℹ️", "callback_data": "status"}],
            [{"text": "Tokens", "callback_data": "tokens"}]
        ]
    }
    targets = ADMIN_IDS if chat_id is None else [chat_id]
    for admin_id in targets:
        send_telegram(admin_id, "Управление ботом:", reply_markup=keyboard)


# Панель токенов
def send_tokens_panel(chat_id):
    keyboard = {"inline_keyboard": []}
    for sector, coins in TOKENS.items():
        row = []
        for coin in coins:
            mark = "✅" if token_state[sector][coin] else "❌"
            row.append({"text": f"{coin} {mark}", "callback_data": f"token|{sector}|{coin}"})
            keyboard["inline_keyboard"].append([{"text": f"{coin} {mark}", "callback_data": f"token|{sector}|{coin}"}])
    keyboard["inline_keyboard"].append([{"text": "Назад 🔙", "callback_data": "back"}])
    send_telegram(ADMIN_IDS[0], "Выберите токены:", reply_markup=keyboard)
    send_telegram(ADMIN_IDS[1], "Выберите токены:", reply_markup=keyboard)


# ----------------- Обработчик callback -----------------
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
            send_telegram(chat_id, "⛔ У вас нет прав управления ботом.")
            return {"ok": True}

        if action == "enable":
            bot_enabled = True
            send_telegram(chat_id, "✅ Бот включен. Сигналы отправляются.")
            send_control_panel(chat_id)
        elif action == "disable":
            bot_enabled = False
            send_telegram(chat_id, "⛔ Бот выключен. Сигналы не отправляются.")
            send_control_panel(chat_id)
        elif action == "status":
            status = "включен ✅" if bot_enabled else "выключен ⛔"
            send_telegram(chat_id, f"Статус бота: {status}")
            send_control_panel(chat_id)
        elif action == "tokens":
            send_tokens_panel(chat_id)
        elif action.startswith("token|"):
            _, sector, coin = action.split("|")
            token_state[sector][coin] = not token_state[sector][coin]
            send_tokens_panel(chat_id)
        elif action == "back":
            send_control_panel(chat_id)

    elif "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_id = data["message"]["from"]["id"]
        text = data["message"]["text"].strip().lower()

        if user_id not in ADMIN_IDS:
            return {"status": "error", "message": "Unauthorized"}

        if text == "/start":
            send_control_panel(chat_id)
        elif text == "/tokens":
            send_tokens_panel(chat_id)

    return {"ok": True}


# ----------------- TradingView сигналы -----------------
@app.api_route("/tv-signal", methods=["POST"])
async def webhook(request: Request):
    global bot_enabled
    data = await request.json()

    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    if bot_enabled:
        symbol = data["symbol"]
        interval = data["interval"]
        signal = data["signal"]
        price = data["price"]

        # Проверяем состояние монеты
        for sector, coins in token_state.items():
            if symbol in coins and coins[symbol]:
                message = f"{symbol} | {interval} | {signal} | Price: {price}"
                send_telegram(TELEGRAM_CHAT_ID, message)
                print("Сигнал отправлен:", message)
    else:
        print("Сигнал получен, но бот выключен.")

    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    send_control_panel()
