import os
import csv
from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN", "")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET", "")

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    print("[WARN] CHANNEL_ACCESS_TOKEN or CHANNEL_SECRET not set. Set environment variables before deploying.")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN) if CHANNEL_ACCESS_TOKEN else None
handler = WebhookHandler(CHANNEL_SECRET) if CHANNEL_SECRET else None

app = Flask(__name__)

def load_mapping(path="data/departments.csv"):
    mapping = []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                mapping.append(row)
    except FileNotFoundError:
        print(f"[WARN] mapping file not found at {path}. Using fallback rules.")
    return mapping

MAPPING = load_mapping()

def find_reply(user_text: str) -> str:
    t = (user_text or "").strip().lower()
    for row in MAPPING:
        kws = [k.strip().lower() for k in (row.get("keywords", "")).split("|") if k.strip()]
        for kw in kws:
            if kw and kw in t:
                return f"你可以洽詢【{row.get('unit','')}】（分機：{row.get('ext','')}）。\n網址：{row.get('url','') or '（無）'}"
    for row in MAPPING:
        unit = (row.get("unit","") or "").lower()
        if unit and unit in t:
            return f"你可以洽詢【{row.get('unit','')}】（分機：{row.get('ext','')}）。\n網址：{row.get('url','') or '（無）'}"
    return "請輸入關鍵字（例：休學、獎學金、宿舍、加退選）。我會告訴你該找哪個處室與分機。"

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/callback", methods=['POST'])
def callback():
    if handler is None or line_bot_api is None:
        abort(500, description="LINE credentials not configured.")
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text or ""
    reply_text = find_reply(user_text)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
