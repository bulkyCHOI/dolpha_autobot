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
