# -*- coding: utf-8 -*-
'''

관련 포스팅
https://blog.naver.com/zacra/223622479916
위 포스팅을 꼭 참고하세요!!!

'''
import telegram
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = int(os.getenv('TELEGRAM_CHAT_ID'))

bot = telegram.Bot(token=TOKEN)

async def send_telegram_alert(msg):
    await bot.send_message(chat_id=CHAT_ID, text=msg)


def SendMessage(msg):
    try:
        loop = asyncio.get_event_loop()  # 기존 이벤트 루프 가져오기
        if loop.is_running():  # 이미 이벤트 루프가 실행 중인 경우
            loop.create_task(send_telegram_alert(msg))  # 비동기 작업을 추가
        else:
            loop.run_until_complete(send_telegram_alert(msg))  # 새로운 이벤트 루프 실행
    except Exception as ex:
        print(ex)