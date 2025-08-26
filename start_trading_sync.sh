#!/bin/bash

# 매매복기 CSV 동기화 서비스 시작 스크립트

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== 매매복기 CSV 동기화 서비스 시작 ==="

# Python 가상환경 활성화 (venv가 있는 경우)
if [ -d "venv" ]; then
    echo "Python 가상환경 활성화: venv"
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Python 가상환경 활성화: .venv"
    source .venv/bin/activate
else
    echo "가상환경을 찾을 수 없습니다. 시스템 Python을 사용합니다."
fi

# 필요한 패키지 설치 확인
echo "필요한 패키지 확인 중..."
python -c "import watchdog" 2>/dev/null || {
    echo "watchdog 패키지가 설치되지 않았습니다. 설치 중..."
    pip install watchdog==6.0.0
}

python -c "import requests" 2>/dev/null || {
    echo "requests 패키지가 설치되지 않았습니다. 설치 중..."
    pip install requests
}

# 설정 파일 확인
if [ ! -f "trading_sync_config.json" ]; then
    echo "❌ 설정 파일이 없습니다: trading_sync_config.json"
    echo "기본 설정 파일을 생성합니다..."
    python trading_sync_manager.py --manual > /dev/null 2>&1
fi

# CSV 파일 확인
if [ ! -f "tradingBot/trading_summary.csv" ]; then
    echo "❌ CSV 파일이 없습니다: tradingBot/trading_summary.csv"
    echo "CSV 파일을 생성한 후 다시 실행하세요."
    exit 1
fi

# 백엔드 서버 연결 테스트
echo "백엔드 서버 연결 테스트 중..."
python -c "
import requests
try:
    response = requests.get('http://localhost:8000/api/hello', timeout=5)
    print('✅ 백엔드 서버 연결 성공')
except Exception as e:
    print('❌ 백엔드 서버 연결 실패:', e)
    print('백엔드 서버가 실행 중인지 확인하세요.')
"

echo ""
echo "🚀 CSV 파일 감시 시작..."
echo "tradingBot/trading_summary.csv 파일 변경을 감시합니다."
echo "Ctrl+C로 종료할 수 있습니다."
echo ""

# 동기화 서비스 시작
python trading_sync_manager.py --watch