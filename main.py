from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import json
import os
from datetime import datetime

# FastAPI 인스턴스 생성
app = FastAPI(
    title="주식 종목 관리 API",
    description="주식 종목 정보를 관리하는 FastAPI 애플리케이션",
    version="1.0.0",
)

# JSON 파일 경로
STOCKS_FILE = "stocks.json"


# 데이터 모델
class Stock(BaseModel):
    id: Optional[int] = None
    code: str  # 종목 코드 (예: "005930")
    name: str  # 종목명 (예: "삼성전자")
    market: str  # 시장 (KOSPI, KOSDAQ, NASDAQ 등)
    target_price: Optional[float] = None  # 매수목표가
    stop_loss_percent: Optional[float] = None  # 손절 %
    target_profit_percent: Optional[float] = None  # 익절 %
    memo: Optional[str] = None  # 메모
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# JSON 파일 헬퍼 함수들
def load_stocks():
    """JSON 파일에서 주식 데이터를 로드합니다."""
    if not os.path.exists(STOCKS_FILE):
        return []
    try:
        with open(STOCKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_stocks(stocks_data):
    """주식 데이터를 JSON 파일에 저장합니다."""
    with open(STOCKS_FILE, "w", encoding="utf-8") as f:
        json.dump(stocks_data, f, ensure_ascii=False, indent=2)


def get_next_stock_id():
    """다음 주식 ID를 생성합니다."""
    stocks_data = load_stocks()
    if not stocks_data:
        return 1
    return max(stock["id"] for stock in stocks_data) + 1


def initialize_sample_data():
    """샘플 주식 데이터를 초기화합니다."""
    stocks_data = load_stocks()
    if not stocks_data:  # 데이터가 없을 때만 샘플 데이터 추가
        sample_stocks = [
            {
                "id": 1,
                "code": "005930",
                "name": "삼성전자",
                "market": "KOSPI",
                "target_price": 80000,
                "stop_loss_percent": 10.0,
                "target_profit_percent": 20.0,
                "memo": "반도체 대장주",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
            {
                "id": 2,
                "code": "000660",
                "name": "SK하이닉스",
                "market": "KOSPI",
                "target_price": 150000,
                "stop_loss_percent": 8.0,
                "target_profit_percent": 15.0,
                "memo": "메모리 반도체",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
            {
                "id": 3,
                "code": "035420",
                "name": "NAVER",
                "market": "KOSPI",
                "target_price": 200000,
                "stop_loss_percent": 12.0,
                "target_profit_percent": 25.0,
                "memo": "IT 플랫폼",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
        ]
        save_stocks(sample_stocks)
        print("샘플 주식 데이터가 초기화되었습니다.")


# 루트 엔드포인트
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html>
        <head>
            <title>간단한 FastAPI</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
                h1 { color: #333; }
                code { background: #e8e8e8; padding: 2px 5px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 주식 종목 관리 API</h1>
                <p>다음 엔드포인트들을 사용할 수 있습니다:</p>
                
                <div class="endpoint">
                    <h3>📚 API 문서</h3>
                    <p><strong>GET</strong> <code>/docs</code> - Swagger UI 문서</p>
                    <p><strong>GET</strong> <code>/redoc</code> - ReDoc 문서</p>
                </div>
                
                <div class="endpoint">
                    <h3>📈 주식 종목 관리</h3>
                    <p><strong>GET</strong> <code>/stocks</code> - 모든 주식 종목 조회</p>
                    <p><strong>POST</strong> <code>/stocks</code> - 새 주식 종목 추가</p>
                    <p><strong>GET</strong> <code>/stocks/{stock_id}</code> - 특정 주식 종목 조회</p>
                    <p><strong>PUT</strong> <code>/stocks/{stock_id}</code> - 주식 종목 수정</p>
                    <p><strong>DELETE</strong> <code>/stocks/{stock_id}</code> - 주식 종목 삭제</p>
                    <p><strong>GET</strong> <code>/stocks/code/{code}</code> - 종목 코드로 조회</p>
                    <p><strong>GET</strong> <code>/stocks/market/{market}</code> - 시장별 조회</p>
                </div>
                
                <p><a href="/docs">📖 Swagger UI 문서 보기</a></p>
            </div>
        </body>
    </html>
    """


# 주식 종목 관련 엔드포인트
@app.get("/stocks", response_model=List[Stock])
async def get_stocks():
    """모든 주식 종목을 조회합니다."""
    stocks_data = load_stocks()
    return stocks_data


@app.post("/stocks", response_model=Stock)
async def create_stock(stock: Stock):
    """새로운 주식 종목을 추가합니다."""
    stocks_data = load_stocks()

    # 중복 종목 코드 확인
    for existing_stock in stocks_data:
        if existing_stock["code"] == stock.code:
            raise HTTPException(
                status_code=400, detail=f"종목 코드 '{stock.code}'가 이미 존재합니다"
            )

    # 새 주식 정보 생성
    stock.id = get_next_stock_id()
    stock.created_at = datetime.now().isoformat()
    stock.updated_at = datetime.now().isoformat()

    # 데이터 추가 및 저장
    stocks_data.append(stock.dict())
    save_stocks(stocks_data)

    return stock


@app.get("/stocks/{stock_id}", response_model=Stock)
async def get_stock(stock_id: int):
    """특정 주식 종목을 조회합니다."""
    stocks_data = load_stocks()

    for stock in stocks_data:
        if stock["id"] == stock_id:
            return stock

    raise HTTPException(
        status_code=404, detail=f"ID {stock_id}인 주식 종목을 찾을 수 없습니다"
    )


@app.get("/stocks/code/{code}", response_model=Stock)
async def get_stock_by_code(code: str):
    """종목 코드로 주식 종목을 조회합니다."""
    stocks_data = load_stocks()

    for stock in stocks_data:
        if stock["code"] == code:
            return stock

    raise HTTPException(
        status_code=404, detail=f"종목 코드 '{code}'를 찾을 수 없습니다"
    )


@app.put("/stocks/{stock_id}", response_model=Stock)
async def update_stock(stock_id: int, updated_stock: Stock):
    """주식 종목 정보를 수정합니다."""
    stocks_data = load_stocks()

    for i, stock in enumerate(stocks_data):
        if stock["id"] == stock_id:
            # 기존 정보 유지
            updated_stock.id = stock_id
            updated_stock.created_at = stock.get("created_at")
            updated_stock.updated_at = datetime.now().isoformat()

            # 다른 종목과 종목 코드 중복 확인
            for j, other_stock in enumerate(stocks_data):
                if i != j and other_stock["code"] == updated_stock.code:
                    raise HTTPException(
                        status_code=400,
                        detail=f"종목 코드 '{updated_stock.code}'가 이미 존재합니다",
                    )

            stocks_data[i] = updated_stock.dict()
            save_stocks(stocks_data)
            return updated_stock

    raise HTTPException(
        status_code=404, detail=f"ID {stock_id}인 주식 종목을 찾을 수 없습니다"
    )


@app.delete("/stocks/{stock_id}")
async def delete_stock(stock_id: int):
    """주식 종목을 삭제합니다."""
    stocks_data = load_stocks()

    for i, stock in enumerate(stocks_data):
        if stock["id"] == stock_id:
            deleted_stock = stocks_data.pop(i)
            save_stocks(stocks_data)
            return {
                "message": f"주식 종목 '{deleted_stock['name']} ({deleted_stock['code']})'이 삭제되었습니다"
            }

    raise HTTPException(
        status_code=404, detail=f"ID {stock_id}인 주식 종목을 찾을 수 없습니다"
    )


@app.get("/stocks/market/{market}", response_model=List[Stock])
async def get_stocks_by_market(market: str):
    """특정 시장의 주식 종목들을 조회합니다."""
    stocks_data = load_stocks()
    market_stocks = [
        stock for stock in stocks_data if stock["market"].upper() == market.upper()
    ]
    return market_stocks


# 헬스 체크 엔드포인트
@app.get("/health")
async def health_check():
    """API 상태를 확인합니다."""
    return {"status": "healthy", "message": "API가 정상적으로 작동중입니다"}


if __name__ == "__main__":
    # 샘플 데이터 초기화
    initialize_sample_data()

    uvicorn.run(app, host="0.0.0.0", port=8080)
