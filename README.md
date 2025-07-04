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
