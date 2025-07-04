# 주식 종목 관리 API 사용 예제

## API 실행
```bash
python main.py
```

## 주식 종목 API 사용 예제

### 1. 모든 주식 종목 조회
```bash
curl -X GET "http://localhost:8000/stocks"
```

### 2. 새로운 주식 종목 추가
```bash
curl -X POST "http://localhost:8000/stocks" \
     -H "Content-Type: application/json" \
     -d '{
       "code": "373220",
       "name": "LG에너지솔루션",
       "market": "KOSPI",
       "target_price": 500000,
       "stop_loss_percent": 10.0,
       "target_profit_percent": 20.0,
       "memo": "배터리 관련주"
     }'
```

### 3. 특정 주식 종목 조회 (ID로)
```bash
curl -X GET "http://localhost:8000/stocks/1"
```

### 4. 특정 주식 종목 조회 (종목코드로)
```bash
curl -X GET "http://localhost:8000/stocks/code/005930"
```

### 5. 주식 종목 정보 수정
```bash
curl -X PUT "http://localhost:8000/stocks/1" \
     -H "Content-Type: application/json" \
     -d '{
       "code": "005930",
       "name": "삼성전자",
       "market": "KOSPI",
       "target_price": 85000,
       "stop_loss_percent": 8.0,
       "target_profit_percent": 25.0,
       "memo": "반도체 대장주 - 목표가 상향"
     }'
```

### 6. 특정 시장의 주식 종목들 조회
```bash
curl -X GET "http://localhost:8000/stocks/market/KOSPI"
```

### 7. 주식 종목 삭제
```bash
curl -X DELETE "http://localhost:8000/stocks/1"
```

## 주식 데이터 모델

```json
{
  "id": 1,
  "code": "005930",                    // 종목 코드
  "name": "삼성전자",                  // 종목명
  "market": "KOSPI",                   // 시장 (KOSPI, KOSDAQ, NASDAQ 등)
  "target_price": 80000,               // 매수목표가
  "stop_loss_percent": 10.0,           // 손절 퍼센트
  "target_profit_percent": 20.0,       // 익절 퍼센트
  "memo": "반도체 대장주",             // 메모
  "created_at": "2025-07-04T...",      // 생성일시
  "updated_at": "2025-07-04T..."       // 수정일시
}
```

## 주요 기능

1. **CRUD 기능**: 주식 종목의 생성, 조회, 수정, 삭제
2. **JSON 파일 저장**: 데이터베이스 없이 간단하게 JSON 파일로 데이터 저장
3. **종목 코드 검색**: 종목 코드로 빠른 검색 가능
4. **시장별 필터링**: 특정 시장(KOSPI, KOSDAQ 등)의 종목들만 조회
5. **중복 방지**: 동일한 종목 코드 중복 등록 방지
6. **타임스탬프**: 생성/수정 시간 자동 기록
7. **매매 계획 관리**: 목표가, 손절/익절 퍼센트 관리

## 샘플 데이터

앱 실행 시 다음 샘플 데이터가 자동으로 생성됩니다:
- 삼성전자 (005930) - 목표가: 80,000원, 손절: 10%, 익절: 20%
- SK하이닉스 (000660) - 목표가: 150,000원, 손절: 8%, 익절: 15%
- NAVER (035420) - 목표가: 200,000원, 손절: 12%, 익절: 25%

## API 문서

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
