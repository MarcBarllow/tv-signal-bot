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

# -------------------- Секции и монеты --------------------
sections = {
    "Main": ["BTCUSDT.P", "ETHUSDT.P", "XRPUSDT.P", "SOLUSDT.P"],
    "DEFI": ["AAVEUSDT.P", "ENAUSDT.P", "HYPEUSDT.P", "JTOUSDT.P", "JUPUSDT.P", "LDOUSDT.P", "LINKUSDT.P", "UNIUSDT.P"],
    "Meme": ["1000PEPEUSDT.P", "DOGEUSDT.P", "FARTCOINUSDT.P", "ORDIUSDT.P", "PENGUUSDT.P", "POPUSDT.P", "PUMPUSDT.P", "WIFUSDT.P"],
    "AI": ["AI16ZUSDT.P", "ARCUSDT.P", "FHEUSDT.P", "API3USDT.P"],
    "Layer 1 & 2": ["APTUSDT.P", "AVAXUSDT.P", "BCHUSDT.P", "BNBUSDT.P", "OPUSDT.P", "SEIUSDT.P", "SUIUSDT.P", "TIAUSDT.P", "WLDUSDT.P", "LSTUSDT.P"],
    "Lst": ["LDOUSDT.P", "LAYERUSDT.P", "FXSUSDT.P"]
}

# словарь с состоянием монет (True = включена, False = выключена)
coin_status = {coin: True for sec in sections.values() for coin in sec}

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
            [{"text": "Включить ✅", "callback_data": "enable"}],
            [{"text": "Выключить ❌", "callback_data": "disable"}],
            [{"text": "Статус ℹ️", "callback_data": "status"}],
            [{"text": "Tokens", "callback_data": "tokens"}]
        ]
    }
    for admin_id in ADMIN_IDS:
        send_telegram(admin_id, "Управление ботом:", reply_markup=keyboard)

# -------------------- Панель монет --------------------
def send_section_panel(chat_id):
    keyboard = [[{"text": sec, "callback_data": f"section:{sec}"}] for sec in sections.keys()]
    keyboard.append([{"text": "Назад ◀️", "callback_data": "back"}])
    send_telegram(chat_id, "Выберите секцию:", reply_markup={"inline_keyboard": keyboard})

def send_coin_panel(chat_id, section_name):
    keyboard = []
    for coin in sections[section_name]:
        status = "✅" if coin_status[coin] else "❌"
        keyboard.append([{"text": f"{coin} {status}", "callback_data": f"coin:{coin}"}])
    keyboard.append([{"text": "Назад ◀️", "callback_data": "back_to_sections"}])
    send_telegram(chat_id, f"{section_name} монеты:", reply_markup={"inline_keyboard": keyboard})

# -------------------- Обработчик сигналов от TradingView --------------------
@app.api_route("/tv-signal", methods=["POST"])
async def webhook(request: Request):
    global bot_enabled
    data = await request.json()

    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    coin = data['symbol']
    if bot_enabled and coin_status.get(coin, True):
        message = f"{coin} | {data['interval']} | {data['signal']} | Price: {data['price']}"
        send_telegram(TELEGRAM_CHAT_ID, message)
        print("Сигнал отправлен:", message)
    else:
        print(f"Сигнал для {coin} не отправлен: бот выключен или монета отключена.")

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

    # callback от кнопок
    if "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        user_id = query["from"]["id"]
        action = query["data"]

        if user_id not in ADMIN_IDS:
            send_telegram(chat_id, "⛔ У вас нет прав управления ботом.")
            return {"ok": True}

        # Блок управления ботом
        if action == "enable":
            bot_enabled = True
            send_telegram(chat_id, "✅ Бот включен. Сигналы отправляются.")
            send_control_panel()
        elif action == "disable":
            bot_enabled = False
            send_telegram(chat_id, "⛔ Бот выключен. Сигналы не отправляются.")
            send_control_panel()
        elif action == "status":
            status = "включен ✅" if bot_enabled else "выключен ⛔"
            send_telegram(chat_id, f"Статус бота: {status}")
        # Открытие панели секций
        elif action == "tokens":
            send_section_panel(chat_id)
        # Выбор секции
        elif action.startswith("section:"):
            section = action.split(":")[1]
            send_coin_panel(chat_id, section)
        # Выбор монеты
        elif action.startswith("coin:"):
            coin = action.split(":")[1]
            coin_status[coin] = not coin_status[coin]  # меняем галочку/крестик
            send_coin_panel(chat_id, next(sec for sec, coins in sections.items() if coin in coins))
        # Кнопка назад
        elif action == "back":
            send_control_panel()
        elif action == "back_to_sections":
            send_section_panel(chat_id)

    return {"ok": True}

# -------------------- При запуске --------------------
@app.on_event("startup")
async def startup_event():
    send_control_panel()
