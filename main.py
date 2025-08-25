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

# -------------------- Состояние монет --------------------
MONETES_STATE = {
    # Main
    "BTCUSDT.P": True, "ETHUSDT.P": True, "SOLUSDT.P": True, "XRPUSDT.P": True,
    # DEFI
    "AAVEUSDT.P": True, "ENAUSDT.P": True, "HYPEUSDT.P": True, "JTOUSDT.P": True, "JUPUSDT.P": True, "LDOUSDT.P": True, "LINKUSDT.P": True, "UNIUSDT.P": True,
    # Meme
    "1000PEPEUSDT.P": True, "DOGEUSDT.P": True, "FARTCOINUSDT.P": True, "ORDIUSDT.P": True, "PENGUUSDT.P": True, "POPCATUSDT.P": True, "PUMPUSDT.P": True, "WIFUSDT.P": True,
    # AI
    "AI16ZUSDT.P": True, "ARCUSDT.P": True, "FHEUSDT.P": True, "API3USDT.P": True,
    # Layer 1 & 2
    "APTUSDT.P": True, "AVAXUSDT.P": True, "BCHUSDT.P": True, "BNBUSDT.P": True, "OPUSDT.P": True, "SEIUSDT.P": True, "SUIUSDT.P": True, "TIAUSDT.P": True, "WLDUSDT.P": True,
    # Lst
    "LDOUSDT.P": True, "LAYERUSDT.P": True, "FXSUSDT.P": True
}

# -------------------- Функция отправки сообщений --------------------
def send_telegram(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    requests.post(url, data=data)

# -------------------- Панель управления --------------------
def send_control_panel():
    keyboard = {
        "inline_keyboard": [
            [{"text": "Bot On ✅", "callback_data": "enable"}, 
             {"text": "Bot Off ❌", "callback_data": "disable"},
             {"text": "Status ℹ️", "callback_data": "status"}],
            [{"text": "Main", "callback_data": "section_Main"},
             {"text": "DEFI", "callback_data": "section_DEFI"},
             {"text": "Meme", "callback_data": "section_Meme"},
             {"text": "AI", "callback_data": "section_AI"},
             {"text": "Layer 1 & 2", "callback_data": "section_Layer"},
             {"text": "Lst", "callback_data": "section_Lst"}]
        ]
    }
    for admin_id in ADMIN_IDS:
        send_telegram(admin_id, "Управление ботом:", reply_markup=keyboard)

# -------------------- Обработчик сигналов TradingView --------------------
@app.api_route("/tv-signal", methods=["POST"])
async def webhook(request: Request):
    global bot_enabled
    data = await request.json()

    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    symbol = data["symbol"]
    message = f"{symbol} | {data['interval']} | {data['signal']} | Price: {data['price']}"

    if bot_enabled and MONETES_STATE.get(symbol, False):
        send_telegram(TELEGRAM_CHAT_ID, message)
        print("Сигнал отправлен:", message)
    else:
        print("Сигнал получен, но бот выключен или монета отключена.")

    return {"status": "ok"}

# -------------------- Ping --------------------
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

    # Callback от кнопок
    if "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        user_id = query["from"]["id"]
        action = query["data"]

        if user_id not in ADMIN_IDS:
            send_telegram(chat_id, "⛔ У вас нет прав управления ботом.")
            return {"ok": True}

        # Основное управление ботом
        if action == "enable":
            bot_enabled = True
            send_telegram(chat_id, "✅ Бот включен. Сигналы отправляются.")
        elif action == "disable":
            bot_enabled = False
            send_telegram(chat_id, "⛔ Бот выключен. Сигналы не отправляются.")
        elif action == "status":
            status = "включен ✅" if bot_enabled else "выключен ⛔"
            send_telegram(chat_id, f"Статус бота: {status}")

        # Секции монет
        elif action.startswith("section_"):
            section_name = action.split("_")[1]
            keyboard = []
            # Фильтруем монеты по секции
            for sym in MONETES_STATE:
                if section_name == "Main" and sym in ["BTCUSDT.P","ETHUSDT.P","SOLUSDT.P","XRPUSDT.P"]:
                    state = "✅" if MONETES_STATE[sym] else "❌"
                    keyboard.append([{"text": f"{sym} {state}", "callback_data": f"toggle_{sym}"}])
                elif section_name == "DEFI" and sym in ["AAVEUSDT.P","ENAUSDT.P","HYPEUSDT.P","JTOUSDT.P","JUPUSDT.P","LDOUSDT.P","LINKUSDT.P","UNIUSDT.P"]:
                    state = "✅" if MONETES_STATE[sym] else "❌"
                    keyboard.append([{"text": f"{sym} {state}", "callback_data": f"toggle_{sym}"}])
                elif section_name == "Meme" and sym in ["1000PEPEUSDT.P","DOGEUSDT.P","FARTCOINUSDT.P","ORDIUSDT.P","PENGUUSDT.P","POPCATUSDT.P","PUMPUSDT.P","WIFUSDT.P"]:
                    state = "✅" if MONETES_STATE[sym] else "❌"
                    keyboard.append([{"text": f"{sym} {state}", "callback_data": f"toggle_{sym}"}])
                elif section_name == "AI" and sym in ["AI16ZUSDT.P","ARCUSDT.P","FHEUSDT.P","API3USDT.P"]:
                    state = "✅" if MONETES_STATE[sym] else "❌"
                    keyboard.append([{"text": f"{sym} {state}", "callback_data": f"toggle_{sym}"}])
                elif section_name == "Layer" and sym in ["APTUSDT.P","AVAXUSDT.P","BCHUSDT.P","BNBUSDT.P","OPUSDT.P","SEIUSDT.P","SUIUSDT.P","TIAUSDT.P","WLDUSDT.P"]:
                    state = "✅" if MONETES_STATE[sym] else "❌"
                    keyboard.append([{"text": f"{sym} {state}", "callback_data": f"toggle_{sym}"}])
                elif section_name == "Lst" and sym in ["LDOUSDT.P","LAYERUSDT.P","FXSUSDT.P"]:
                    state = "✅" if MONETES_STATE[sym] else "❌"
                    keyboard.append([{"text": f"{sym} {state}", "callback_data": f"toggle_{sym}"}])

            # Кнопка назад
            keyboard.append([{"text": "Назад ⬅️", "callback_data": "back"}])
            send_telegram(chat_id, f"Монеты секции {section_name}:", reply_markup={"inline_keyboard": keyboard})

        # Toggle монет
        elif action.startswith("toggle_"):
            sym = action.split("_")[1]
            MONETES_STATE[sym] = not MONETES_STATE[sym]
            state = "включена ✅" if MONETES_STATE[sym] else "выключена ❌"
            send_telegram(chat_id, f"{sym} теперь {state}")

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
            send_telegram(chat_id, "✅ Бот включен. Сигналы отправляются.")
        elif text == "/off":
            bot_enabled = False
            send_telegram(chat_id, "⛔ Бот выключен. Сигналы не отправляются.")
        elif text == "/status":
            status = "включен ✅" if bot_enabled else "выключен ⛔"
            send_telegram(chat_id, f"Статус бота: {status}")
        elif text == "/tokens":
            send_control_panel()
        else:
            send_telegram(chat_id, "Команды: /on — включить, /off — выключить, /status — статус, /tokens — управление монетами")

    return {"ok": True}

# -------------------- При старте --------------------
@app.on_event("startup")
async def startup_event():
    send_control_panel()
