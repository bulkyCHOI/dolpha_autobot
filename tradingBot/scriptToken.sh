!/bin/bash
cd /var/autobot/dolpha_autobot/tradingBot
/var/autobot/dolpha_autobot/venv/bin/python /var/autobot/dolpha_autobot/tradingBot/KIS_MakeToken.py

# script파일 권한 추가
# chmod +x /var/autobot/dolpha_autobot/tradingBot/scriptToken.sh
# 크론탭 등록
# * * * * * /var/autobot/dolpha_autobot/tradingBot/scriptToken.sh


