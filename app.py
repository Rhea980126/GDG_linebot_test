import os
from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage)
from linebot.exceptions import InvalidSignatureError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import logging
import requests

load_dotenv()

line_token = os.getenv('LINE_TOKEN')
line_secret = os.getenv('LINE_SECRET')

if not line_token or not line_secret:
    raise ValueError("LINE_TOKEN 或 LINE_SECRET 未設置")

line_bot_api = LineBotApi(line_token)
handler = WebhookHandler(line_secret)

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

TARGET_USER_ID = "Uc24eaf6e2cfca14939d663f652cc65bc"

PUSH_MESSAGE_1 = "咪比回家了嗎 (つ'ω')つ\n「吃飽了」直接去洗澡\n「買回家吃」吃完後直接去洗澡～\n「還在外面」等等再聊呢\n\n洗完澡回覆「洗完了」\n回「晚上休息」查看晚上休息的時間計畫"

PUSH_MESSAGE_2 = "今天也是很棒的一天喔\n又到該睡覺的時間了(๑˘ ˘๑)\n把今天學到的東西和心情寫下來吧\n也可以記錄明天要做的事喔\n\n咪比晚安囉...(¦3ꇤ[▓▓]"

def send_evening_message():
    line_bot_api.push_message(
        TARGET_USER_ID,
        TextSendMessage(text=PUSH_MESSAGE_1)
    )
    app.logger.info("傍晚推播已發送")

def send_night_message():
    line_bot_api.push_message(
        TARGET_USER_ID,
        TextSendMessage(text=PUSH_MESSAGE_2)
    )
    app.logger.info("晚安推播已發送")

taiwan_tz = pytz.timezone('Asia/Taipei')
scheduler = BackgroundScheduler()
scheduler.add_job(
    send_evening_message,
    CronTrigger(day_of_week='mon-fri', hour=17, minute=40, timezone=taiwan_tz)
)
scheduler.add_job(
    send_night_message,
    CronTrigger(hour=23, minute=0, timezone=taiwan_tz)
)
scheduler.start()

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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    app.logger.info(f"User ID: {user_id}")

    # 已讀標記
    mark_as_read_token = event.message.mark_as_read_token
    if mark_as_read_token:
        requests.post(
            "https://api.line.me/v2/bot/message/markAsRead/token",
            headers={
                "Authorization": f"Bearer {line_token}",
                "Content-Type": "application/json"
            },
            json={"markAsReadToken": mark_as_read_token}
        )
        app.logger.info("已讀標記完成")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
