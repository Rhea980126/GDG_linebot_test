import os
from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage)
from linebot.exceptions import InvalidSignatureError
import logging

# 加載 .env 文件中的變數
load_dotenv()

# 從環境變數中讀取 LINE 的 Channel Access Token 和 Channel Secret
line_token = os.getenv('LINE_TOKEN')
line_secret = os.getenv('LINE_SECRET')

# 檢查是否設置了環境變數
if not line_token or not line_secret:
    raise ValueError("LINE_TOKEN 或 LINE_SECRET 未設置")

# 初始化 LineBotApi 和 WebhookHandler
line_bot_api = LineBotApi(line_token)
handler = WebhookHandler(line_secret)

# 創建 Flask 應用
app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

# 處理 LINE Webhook 回調
@app.route("/", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 新增：Push Message 路由
@app.route("/push", methods=['POST'])
def push_message():
    data = request.get_json()
    user_id = data.get('user_id')
    message = data.get('message')
    line_bot_api.push_message(
        user_id,
        TextSendMessage(text=message)
    )
    return 'OK'

# 處理收到的文字訊息（同時印出 User ID）
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    app.logger.info(f"User ID: {user_id}")  # 在 Render log 可以看到

    user_message = event.message.text
    reply_text = "你說了：" + user_message
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
