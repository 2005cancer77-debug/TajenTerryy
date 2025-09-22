import os
import csv
import random
from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN", "")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET", "")

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    print("[WARN] CHANNEL_ACCESS_TOKEN or CHANNEL_SECRET not set. Set environment variables before deploying.")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN) if CHANNEL_ACCESS_TOKEN else None
handler = WebhookHandler(CHANNEL_SECRET) if CHANNEL_SECRET else None

app = Flask(__name__)

def load_mapping(path="data/departments.csv"):
    """Load CSV using utf-8-sig to strip BOM, and print debug for the first few rows."""
    mapping = []
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                mapping.append(row)
                if i < 3:
                    print(f"[DEBUG] row={row}")
        print(f"[INFO] Loaded {len(mapping)} rows from {path}")
    except Exception as e:
        print(f"[ERROR] Failed to read {path}: {e}")
    return mapping

MAPPING = load_mapping()

# Funny fallback lines shown when no keyword matched
FALLBACKS = [
    "我還在練功，試試更精準的關鍵字？像：休學、獎學金、宿舍、校曆。",
    "嗯…這題我還不太懂 😅 可以改用「休學」「加退選」「宿舍」「交通」嗎？",
    "我找不到對應單位 QQ。可試：教務處、學務處、總務處、圖書館。",
    "想找誰？丟關鍵字給我吧～例如：借書、場地借用、請假、選課、地圖。",
    "笑死，我不知道欸",
    "我不知道，還是你問前面那個學長",
    "我不知道，還是你問前面那個學姐",
    "我不知道，還是你問前面的同學",
    "你可以問男朋友啊",
    "你問女朋友好了",
]

def find_reply(user_text: str):
    t = (user_text or "").strip().lower()
    # 1) 關鍵字命中
    for row in MAPPING:
        kws = [k.strip().lower() for k in (row.get("keywords", "") or "").split("|") if k.strip()]
        for kw in kws:
            if kw and kw in t:
                unit = row.get("unit", "").strip() or "（未填單位）"
                ext = (row.get("ext", "") or "").strip() or "N/A"
                url = row.get("url", "") or "（無）"
                return f"你可以洽詢（分機：{ext}）。\n網址：{url}"
    # 2) 單位名稱命中
    for row in MAPPING:
        unit_l = (row.get("unit","") or "").strip().lower()
        if unit_l and unit_l in t:
            unit = row.get("unit", "").strip() or "（未填單位）"
            ext = (row.get("ext", "") or "").strip() or "N/A"
            url = row.get("url", "") or "（無）"
            return f"你可以洽詢（分機：{ext}）。\n網址：{url}"
    # 找不到
    return None

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

    if reply_text is None:
        print(f"[NO_MATCH] {user_text}")
        fallback = random.choice(FALLBACKS)
        quick_items = [
            QuickReplyButton(action=MessageAction(label="休學",      text="休學")),
            QuickReplyButton(action=MessageAction(label="獎學金",    text="獎學金")),
            QuickReplyButton(action=MessageAction(label="宿舍",      text="宿舍")),
            QuickReplyButton(action=MessageAction(label="加退選",    text="加退選")),
            QuickReplyButton(action=MessageAction(label="校曆",      text="校務行事曆")),
            QuickReplyButton(action=MessageAction(label="交通",      text="交通資訊")),
            QuickReplyButton(action=MessageAction(label="地圖",      text="校園導覽／地圖")),
            QuickReplyButton(action=MessageAction(label="學生系統",  text="學生資訊系統")),
        ]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=fallback, quick_reply=QuickReply(items=quick_items))
        )
        return

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
