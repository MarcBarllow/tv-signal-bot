from fastapi import FastAPI, Request
import os
import requests
import json

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET")  # dessston
ADMIN_IDS = [8200781854, 885033881]

bot_enabled = True

sections = {
    "Main": ["BTCUSDT.P", "ETHUSDT.P", "SOLUSDT.P", "XRPUSDT.P"],
    "DEFI": ["AAVEUSDT.P", "ENAUSDT.P", "HYPEUSDT.P", "JTOUSDT.P", "JUPUSDT.P", "LDOUSDT.P", "LINKUSDT.P", "UNIUSDT.P"],
    "Meme": ["1000PEPEUSDT.P", "DOGEUSDT.P", "FARTCOINUSDT.P", "ORDIUSDT.P", "PENGUUSDT.P", "POPUSDT.P", "PUMPUSDT.P", "WIFUSDT.P"],
    "AI": ["AI16ZUSDT.P", "ARCUSDT.P", "FHEUSDT.P", "API3USDT.P", "HYPEUSDT.P"],
    "Layer 1 & 2": ["APTUSDT.P", "AVAXUSDT.P", "BCHUSDT.P", "BNBUSDT.P", "OPUSDT.P", "SEIUSDT.P", "SUIUSDT.P", "TIAUSDT.P", "WLDUSDT.P"],
    "Lst": ["LDOUSDT.P", "LAYERUSDT.P", "FXSUSDT.P"]
}

coin_status = {coin: True for section in sections.values() for coin in section}


def send_telegram(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    requests.post(url, data=data)


def main_menu_keyboard():
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "Bot On✅", "callback_data": "bot_enable"},
                {"text": "Bot Off❌", "callback_data": "bot_disable"},
                {"text": "Status ℹ️", "callback_data": "bot_status"}
            ]
        ]
    }
    # Секции вертикально
    for section in sections.keys():
        keyboard["inline_keyboard"].append([{"text": section, "callback_data": f"section_{section}"}])
    return keyboard


def section_keyboard(section_name):
    keyboard = {"inline_keyboard": []}
    for coin in sections[section_name]:
        status = "✅" if coin_status[coin] else "❌"
        keyboard["inline_keyboard"].append([{"text": f"{coin} {status}", "callback_data": f"coin_{coin}_{section_name}"}])
    # Кнопка назад
    keyboard["inline_keyboard"].append([{"text": "Назад 🔙", "callback_data": "back_to_sections"}])
    return keyboard


@app.api_route("/tv-signal", methods=["POST"])
async def tv_signal(request: Request):
    global bot_enabled
    data = await request.json()
    if "secret" not in data or data["secret"] != TV_WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    if bot_enabled:
        message = f"{data['symbol']} | {data['interval']} | {data['signal']} | Price: {data['price']}"
        send_telegram(os.getenv("TELEGRAM_CHAT_ID"), message)
        print("Сигнал отправлен:", message)
    return {"status": "ok"}


@app.post("/bot-control")
async def bot_control(request: Request):
    global bot_enabled
    data = await request.json()

    if "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        user_id = query["from"]["id"]
        message_id = query["message"]["message_id"]
        action = query["data"]

        if user_id not in ADMIN_IDS:
            send_telegram(chat_id, "⛔ У вас нет прав управления ботом.")
            return {"ok": True}

        if action == "bot_enable":
            bot_enabled = True
            send_telegram(chat_id, "✅ Бот включен.", reply_markup=main_menu_keyboard())
        elif action == "bot_disable":
            bot_enabled = False
            send_telegram(chat_id, "⛔ Бот выключен.", reply_markup=main_menu_keyboard())
        elif action == "bot_status":
            status = "включен ✅" if bot_enabled else "выключен ⛔"
            send_telegram(chat_id, f"Статус бота: {status}", reply_markup=main_menu_keyboard())
        elif action.startswith("section_"):
            section_name = action.replace("section_", "")
            send_telegram(chat_id, f"Вы выбрали секцию: {section_name}", reply_markup=section_keyboard(section_name))
        elif action.startswith("coin_"):
            # Формат coin_<coin>_<section>
            parts = action.split("_")
            coin_name = parts[1]
            section_name = "_".join(parts[2:])
            coin_status[coin_name] = not coin_status[coin_name]  # меняем галочку
            # Обновляем кнопки inline
            keyboard = section_keyboard(section_name)
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/editMessageReplyMarkup"
            data = {
                "chat_id": chat_id,
                "message_id": message_id,
                "reply_markup": json.dumps(keyboard)
            }
            requests.post(url, data=data)
        elif action == "back_to_sections":
            send_telegram(chat_id, "Главное меню:", reply_markup=main_menu_keyboard())

    elif "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_id = data["message"]["from"]["id"]
        text = data["message"]["text"].strip().lower()
        if user_id not in ADMIN_IDS:
            return {"status": "error", "message": "Unauthorized"}
        if text == "/start":
            send_telegram(chat_id, "Главное меню:", reply_markup=main_menu_keyboard())

    return {"ok": True}


@app.on_event("startup")
async def startup_event():
    for admin_id in ADMIN_IDS:
        send_telegram(admin_id, "Главное меню:", reply_markup=main_menu_keyboard())
