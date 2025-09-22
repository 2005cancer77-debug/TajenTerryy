# LINE 校務導引 Chatbot（Python + Flask）

這是一個簡單的 LINE Bot，協助學生查詢該找哪個處室（含分機與網址）。

## 本機測試
```bash
pip install -r requirements.txt
export CHANNEL_SECRET="你的secret"
export CHANNEL_ACCESS_TOKEN="你的token"
python app.py
```

## Render/Heroku 部署
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Health Check Path: `/health`

## Webhook
設定 Webhook URL 為：
```
https://你的服務網址/callback
```
