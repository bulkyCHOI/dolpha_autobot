!/bin/bash
cd /var/autobot/dolpha_autobot/tradingBot
/var/autobot/dolpha_autobot/venv/bin/python /var/autobot/dolpha_autobot/tradingBot/autoTrading_Bot.py >> /var/autobot/dolpha_autobot/tradingBot/cron_temp.log 2>&1

# 크론탭 등록
# * * * * * /var/autobot/dolpha_autobot/tradingBot/script.sh



