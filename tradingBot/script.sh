#!/bin/bash
cd /var/autobot/dolpha_autobot/tradingBot
/var/autobot/dolpha_autobot/venv/bin/python /var/autobot/dolpha_autobot/tradingBot/autoTrading_Bot.py >> /var/autobot/dolpha_autobot/tradingBot/cron_temp.log 2>&1

# script파일 권한 추가
# chmod +x /var/autobot/dolpha_autobot/tradingBot/script.sh
# 크론탭 등록
# * * * * * /var/autobot/dolpha_autobot/tradingBot/script.sh



