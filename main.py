from fastapi import FastAPI, Request
import os, requests, json

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET")
ADMIN_IDS = [8200781854, 885033881]

bot_enabled = True
token_status = {}  # словарь токенов и их статуса: True=вкл, False=выкл

SECTIONS = {
    "Main": ["BTCUSDT.P", "ETHUSDT.P", "SOLUSDT.P", "XRPUSDT.P"],
    "DEFI": ["AAVEUSDT.P","ENAUSDT.P","HYPEUSDT.P","JTOUSDT.P","JUPUSDT.P","LDOUSDT.P","LINKUSDT.P","UNIUSDT.P"],
    "Meme": ["1000PEPEUSDT.P","DOGEUSDT.P","FARTUSDT.P","ORDIUSDT.P","PENGUUSDT.P","POPUSDT.P","PUMPUSDT.P","WIFUSDT.P"],
    "AI": ["AI16ZUSDT.P","ARCUSDT.P","FHEUSDT.P","API3USDT.P"],
    "Layer 1 & 2": ["APTUSDT.P","AVAXUSDT.P","BCHUSDT.P","BNBUSDT.P","OPUSDT.P","SEIUSDT.P","SUIUSDT.P","TIAUSDT.P","WLDUSDT.P"],
    "Lst": ["LDOUSDT.P","LAYERUSDT.P","FXSUSDT.P"]
}

# Инициализация статусов токенов
for section in SECTIONS:
    for token in SECTIONS[section]:
        token_status[token] = True

def send_telegram(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    requests.post(url, data=data)

def build_section_buttons(section_name):
    keyboard = []
    for token in SECTIONS[section_name]:
        emoji = "✅" if token_status[token] else "❌"
        keyboard.append([{"text": f"{token} {emoji}", "callback_data": f"toggle_{token}"}])
    keyboard.append([{"text": "Назад ◀️", "callback_data": "back_main"}])
    return {"inline_keyboard": keyboard}

def main_control_panel():
    keyboard = [
        [{"text":"Bot On✅","callback_data":"enable"}],
        [{"text":"Bot Off❌","callback_data":"disable"}],
        [{"text":"Status ℹ️","callback_data":"status"}],
        [{"text":"Tokens","callback_data":"tokens"}]
    ]
    return {"inline_keyboard": keyboard}

@app.api_route("/tv-signal", methods=["POST"])
async def webhook(request: Request):
    global bot_enabled
    data = await request.json()
    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}
    if not bot_enabled: return {"status": "ok"}

    symbol = data['symbol']
    if token_status.get(symbol, True):
        message = f"{symbol} | {data['interval']} | {data['signal']} | Price: {data['price']}"
        send_telegram(os.getenv("TELEGRAM_CHAT_ID"), message)
        print("Сигнал отправлен:", message)
    return {"status": "ok"}

@app.post("/bot-control")
async def bot_control(request: Request):
    global bot_enabled
    data = await request.json()

    if "callback_query" not in data: return {"ok": True}
    query = data["callback_query"]
    chat_id = query["message"]["chat"]["id"]
    user_id = query["from"]["id"]
    action = query["data"]

    if user_id not in ADMIN_IDS:
        send_telegram(chat_id,"⛔ У вас нет прав")
        return {"ok": True}

    if action=="enable":
        bot_enabled=True
        send_telegram(chat_id,"✅ Бот включен",reply_markup=main_control_panel())
    elif action=="disable":
        bot_enabled=False
        send_telegram(chat_id,"⛔ Бот выключен",reply_markup=main_control_panel())
    elif action=="status":
        status = "включен ✅" if bot_enabled else "выключен ⛔"
        send_telegram(chat_id,f"Статус бота: {status}",reply_markup=main_control_panel())
    elif action=="tokens":
        keyboard = [{"text": sec,"callback_data": f"section_{sec}"}] for sec in SECTIONS
        send_telegram(chat_id,"Выберите секцию:",reply_markup={"inline_keyboard": keyboard})
    elif action.startswith("section_"):
        section_name = action.replace("section_","")
        send_telegram(chat_id,f"Токены {section_name}:",reply_markup=build_section_buttons(section_name))
    elif action.startswith("toggle_"):
        token = action.replace("toggle_","")
        token_status[token] = not token_status[token]
        # обновляем панель, не отправляя лишнее сообщение
        section_name = next((s for s in SECTIONS if token in SECTIONS[s]), None)
        if section_name:
            send_telegram(chat_id,f"Токены {section_name}:",reply_markup=build_section_buttons(section_name))
    elif action=="back_main":
        send_telegram(chat_id,"Главное меню:",reply_markup=main_control_panel())

    return {"ok": True}

@app.on_event("startup")
async def startup_event():
    for admin_id in ADMIN_IDS:
        send_telegram(admin_id,"Панель управления ботом:",reply_markup=main_control_panel())
        
