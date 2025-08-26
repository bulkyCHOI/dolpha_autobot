# 간단한 FastAPI 애플리케이션

이 프로젝트는 FastAPI를 사용한 간단한 RESTful API 애플리케이션입니다.

## 기능

- **상품 관리**: CRUD 기능을 제공합니다
- **사용자 관리**: 사용자 등록 및 조회 기능을 제공합니다
- **API 문서**: Swagger UI와 ReDoc 자동 생성
- **헬스 체크**: API 상태 모니터링

## 설치 및 실행

### 1. 가상환경 생성 (선택사항)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 애플리케이션 실행
```bash
python main.py
```

또는

```bash
uvicorn main:app --reload
```

## systemd 서비스로 자동 실행 설정

애플리케이션을 시스템 서비스로 등록하여 부팅시 자동으로 시작되고, 프로세스가 종료되면 자동으로 재시작되도록 설정할 수 있습니다.

### 1. 가상환경 설정 (필수)
```bash
# autobot 디렉토리로 이동
cd /home/dolpha/dolpha_project/autobot

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. systemd 서비스 파일 복사
```bash
# 서비스 파일을 시스템 디렉토리로 복사
sudo cp autobot.service /etc/systemd/system/
sudo cp autobot_ec2.service /etc/systemd/system/autobot.service

# 적절한 권한 설정
sudo chmod 644 /etc/systemd/system/autobot.service
```

### 3. 서비스 등록 및 시작
```bash
# systemd 데몬 설정 다시 로드
sudo systemctl daemon-reload

# 부팅시 자동 시작 설정
sudo systemctl enable autobot.service

# 서비스 시작
sudo systemctl start autobot.service
```

### 4. 서비스 관리 명령어
```bash
# 서비스 상태 확인
sudo systemctl status autobot.service

# 서비스 중지
sudo systemctl stop autobot.service

# 서비스 재시작
sudo systemctl restart autobot.service

# 로그 확인
sudo journalctl -u autobot.service -f

# 부팅시 자동 시작 해제
sudo systemctl disable autobot.service
```

### 5. 서비스 설정 파일 (autobot.service)
```ini
[Unit]
Description=Dolpha Autobot FastAPI Service
After=network.target

[Service]
Type=simple
User=dolpha
Group=dolpha
WorkingDirectory=/home/dolpha/dolpha_project/autobot
Environment=PATH=/home/dolpha/dolpha_project/autobot/venv/bin
ExecStart=/home/dolpha/dolpha_project/autobot/venv/bin/python main.py
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 서비스 등록 후 접속 정보
- 서버 주소: http://localhost:8080 또는 http://0.0.0.0:8080
- API 문서: http://localhost:8080/docs
- ReDoc 문서: http://localhost:8080/redoc

## API 엔드포인트

### 기본
- `GET /` - 홈페이지
- `GET /health` - 헬스 체크
- `GET /docs` - Swagger UI 문서
- `GET /redoc` - ReDoc 문서

### 상품 관리
- `GET /items` - 모든 상품 조회
- `POST /items` - 새 상품 생성
- `GET /items/{item_id}` - 특정 상품 조회
- `PUT /items/{item_id}` - 상품 수정
- `DELETE /items/{item_id}` - 상품 삭제

### 사용자 관리
- `GET /users` - 모든 사용자 조회
- `POST /users` - 새 사용자 생성
- `GET /users/{user_id}` - 특정 사용자 조회

## 사용 예제

### 상품 생성
```bash
curl -X POST "http://localhost:8000/items" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "노트북",
       "description": "고성능 게이밍 노트북",
       "price": 1500000,
       "is_available": true
     }'
```

### 사용자 생성
```bash
curl -X POST "http://localhost:8000/users" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "홍길동",
       "email": "hong@example.com"
     }'
```

## 개발 모드에서 실행

개발 모드에서 자동 리로드를 원할 경우:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

애플리케이션이 실행되면 다음 URL에서 확인할 수 있습니다:
- 홈페이지: http://localhost:8000
- API 문서: http://localhost:8000/docs
- ReDoc 문서: http://localhost:8000/redoc

# EC2에서는 80, 443, 22 3개 포트만 허용되어 있으므로 추가 허용을 해야함
ping(ICMP)과 8080 포트 접속을 위해 보안 그룹에서 인바운드 규칙을 추가합니다.

보안 그룹 확인:
EC2 대시보드 > Instances > 인스턴스 선택 > Security 탭 > Security groups 클릭.
Inbound rules 확인.
  8080 포트 허용:
  Add rule:
  Type: Custom TCP
  Port range: 8080
  Source: 0.0.0.0/0 또는 특정 IP.
  Description: "FastAPI 8080 access".
  저장.


# EC2에 autobot 등록
crontab에 /tradingBot/script.sh를 등록
크론탭 실행 기본 폴더는 ~/ 즉 home이므로 소스코드내 상대경로를 잘못 읽게 되어 스크립트 파일을 실행하는 형태로 변경
script.sh 파일내 아래 항목 참조하여 등록
# script파일 권한 추가
# chmod +x /var/autobot/dolpha_autobot/tradingBot/script.sh
# 크론탭 등록
# * * * * * /var/autobot/dolpha_autobot/tradingBot/script.sh

---

# 매매복기 CSV 동기화 시스템

autobot에서 생성되는 `trading_summary.csv` 파일을 실시간으로 감시하여 Django 백엔드 데이터베이스에 자동 동기화하는 시스템입니다.

## 주요 기능

- **실시간 파일 감시**: CSV 파일 변경 시 자동 감지
- **자동 데이터 동기화**: 변경된 데이터를 Backend API로 전송
- **에러 처리 및 재시도**: 네트워크 오류 시 자동 재시도
- **백업 기능**: CSV 파일 자동 백업
- **설정 관리**: JSON 설정 파일로 유연한 구성

## 설치 및 설정

### 1. 필요한 패키지 설치
```bash
# autobot 디렉터리로 이동
cd /path/to/autobot

# 가상환경 활성화 (이미 설정된 경우)
source venv/bin/activate

# watchdog 패키지 설치
pip install watchdog==6.0.0
```

### 2. 설정 파일 구성
`trading_sync_config.json` 파일을 편집하여 환경에 맞게 설정:

```json
{
  "backend_url": "http://localhost:8000",
  "api_key": "",
  "user_id": 1,
  "sync_enabled": true,
  "retry_count": 3,
  "retry_delay": 5,
  "debounce_delay": 5,
  "csv_file_path": "tradingBot/trading_summary.csv",
  "backup_enabled": true,
  "backup_directory": "backups/"
}
```

**설정 항목 설명:**
- `backend_url`: Django 백엔드 서버 URL
- `api_key`: API 인증 키 (JWT 토큰)
- `user_id`: 데이터를 저장할 사용자 ID
- `sync_enabled`: 동기화 활성화 여부
- `retry_count`: 실패 시 재시도 횟수
- `retry_delay`: 재시도 간격 (초)
- `debounce_delay`: 파일 변경 감지 딜레이 (초)
- `csv_file_path`: 감시할 CSV 파일 경로
- `backup_enabled`: 백업 기능 활성화 여부
- `backup_directory`: 백업 파일 저장 디렉터리

## 사용법

### 1. 테스트 실행
```bash
# 동기화 시스템 테스트
python test_trading_sync.py
```

### 2. 수동 동기화
```bash
# 현재 CSV 파일의 모든 데이터를 한 번에 동기화
python trading_sync_manager.py --manual
```

### 3. 자동 파일 감시 시작
```bash
# CSV 파일 변경을 실시간으로 감시하고 자동 동기화
python trading_sync_manager.py --watch
```

### 4. 편리한 시작 스크립트
```bash
# 환경 설정 및 자동 시작
./start_trading_sync.sh
```

## 자동 실행 설정 (systemd 서비스)

### 1. 서비스 파일 생성
`/etc/systemd/system/trading-sync.service` 파일을 생성:

```ini
[Unit]
Description=Trading Summary CSV Sync Service
After=network.target

[Service]
Type=simple
User=dolpha
Group=dolpha
WorkingDirectory=/home/dolpha/dolpha_project/autobot
Environment=PATH=/home/dolpha/dolpha_project/autobot/venv/bin
ExecStart=/home/dolpha/dolpha_project/autobot/venv/bin/python trading_sync_manager.py --watch
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. 서비스 등록 및 시작
```bash
# systemd 설정 다시 로드
sudo systemctl daemon-reload

# 부팅 시 자동 시작 설정
sudo systemctl enable trading-sync.service

# 서비스 시작
sudo systemctl start trading-sync.service

# 서비스 상태 확인
sudo systemctl status trading-sync.service

# 로그 확인
sudo journalctl -u trading-sync.service -f
```

## 로그 및 모니터링

### 로그 파일
- `trading_sync.log`: 동기화 시스템 로그
- `backups/`: CSV 파일 백업 디렉터리

### 로그 예시
```
2025-08-14 10:30:15 - INFO - CSV 파일 감시 시작: tradingBot/trading_summary.csv
2025-08-14 10:35:22 - INFO - CSV 파일 변경 감지: tradingBot/trading_summary.csv
2025-08-14 10:35:23 - INFO - CSV 파일 백업 완료: backups/trading_summary_20250814_103523.csv
2025-08-14 10:35:24 - INFO - 데이터 전송 성공: 014970 - 삼륭물산
2025-08-14 10:35:25 - INFO - 전체 동기화 완료: 15/15 성공
```

## 문제 해결

### 자주 발생하는 문제

1. **인증 오류 (401)**
   - `api_key` 설정 확인
   - JWT 토큰 유효성 확인

2. **CSV 파일을 찾을 수 없음**
   - `csv_file_path` 경로 확인
   - 파일 권한 확인

3. **백엔드 서버 연결 실패**
   - `backend_url` 설정 확인
   - Django 서버 실행 상태 확인

4. **데이터 형식 오류**
   - CSV 파일 형식 검증
   - 날짜 형식 확인 (YYYY-MM-DD HH:MM:SS)

### 디버깅

```bash
# 상세 로그와 함께 실행
python trading_sync_manager.py --watch --debug

# 설정 파일 유효성 검사
python -c "import json; print(json.load(open('trading_sync_config.json')))"

# 백엔드 서버 연결 테스트
curl -X GET http://localhost:8000/api/hello
```

## API 연동

매매복기 동기화 시스템은 다음 Django API 엔드포인트를 사용합니다:

- `POST /api/trading-summary`: 매매복기 데이터 생성/업데이트
- `GET /api/trading-summary-stats`: 통계 정보 조회

자세한 API 사양은 Django 프로젝트의 `backend/dolpha/api_trading_reviews.py` 파일을 참조하세요.



