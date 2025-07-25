from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STOCKS_FILE = "stocks.json"
TRADING_CONFIGS_FILE = "trading_configs.json"
class Stock(BaseModel):
    id: Optional[int] = None
    code: str
    name: str
    market: str
    target_price: Optional[float] = None
    stop_loss_percent: Optional[float] = None
    target_profit_percent: Optional[float] = None
    memo: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AutoTradingConfig(BaseModel):
    id: Optional[int] = None
    stock_code: str
    stock_name: str
    trading_mode: str
    strategy_type: str = 'mtt'  # 'mtt' or 'weekly_high'
    max_loss: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    pyramiding_count: int = 0
    entry_point: Optional[float] = None
    pyramiding_entries: List[str] = []
    positions: List[float] = []
    user_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_active: bool = True


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


def load_trading_configs():
    """JSON 파일에서 자동매매 설정 데이터를 로드합니다."""
    if not os.path.exists(TRADING_CONFIGS_FILE):
        return []
    try:
        with open(TRADING_CONFIGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_trading_configs(configs_data):
    """자동매매 설정 데이터를 JSON 파일에 저장합니다."""
    with open(TRADING_CONFIGS_FILE, "w", encoding="utf-8") as f:
        json.dump(configs_data, f, ensure_ascii=False, indent=2)


def get_next_config_id():
    """다음 자동매매 설정 ID를 생성합니다."""
    configs_data = load_trading_configs()
    if not configs_data:
        return 1
    return max(config["id"] for config in configs_data) + 1


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
                
                <div class="endpoint">
                    <h3>🤖 자동매매 설정 관리</h3>
                    <p><strong>GET</strong> <code>/trading-configs</code> - 모든 자동매매 설정 조회</p>
                    <p><strong>POST</strong> <code>/trading-configs</code> - 새 자동매매 설정 추가</p>
                    <p><strong>GET</strong> <code>/trading-configs/{user_id}</code> - 사용자별 설정 조회</p>
                    <p><strong>PUT</strong> <code>/trading-configs/{config_id}</code> - 설정 수정</p>
                    <p><strong>DELETE</strong> <code>/trading-configs/{config_id}</code> - 설정 삭제</p>
                    <p><strong>DELETE</strong> <code>/trading-configs/user/{user_id}/stock/{stock_code}</code> - 사용자별 종목별 설정 삭제</p>
                    <p><strong>POST</strong> <code>/trading-configs/{config_id}/toggle</code> - 활성화/비활성화</p>
                    <p><strong>POST</strong> <code>/trading-configs/user/{user_id}/stock/{stock_code}/toggle</code> - 사용자별 종목별 활성화/비활성화</p>
                </div>
                
                <p><a href="/docs">📖 Swagger UI 문서 보기</a></p>
            </div>
        </body>
    </html>
    """


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
            updated_stock.id = stock_id
            updated_stock.created_at = stock.get("created_at")
            updated_stock.updated_at = datetime.now().isoformat()

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


@app.get("/trading-configs", response_model=List[AutoTradingConfig])
async def get_all_trading_configs():
    """모든 자동매매 설정을 조회합니다."""
    configs_data = load_trading_configs()
    return configs_data


@app.get("/trading-configs/stock/{stock_code}", response_model=AutoTradingConfig)
async def get_trading_config_by_stock(stock_code: str, user_id: str = None):
    """특정 종목의 자동매매 설정을 조회합니다."""
    configs_data = load_trading_configs()
    
    for config in configs_data:
        if config["stock_code"] == stock_code and config["is_active"]:
            if user_id is None or config["user_id"] == user_id:
                return config
    
    return None


@app.get("/trading-configs/user/{user_id}/stock/{stock_code}")
async def get_user_stock_config(user_id: str, stock_code: str):
    """특정 사용자의 특정 종목 설정을 조회합니다."""
    configs_data = load_trading_configs()
    
    user_configs = []
    for config in configs_data:
        if config["user_id"] == user_id and config["stock_code"] == stock_code:
            user_configs.append(config)
    
    if not user_configs:
        return {"config": None, "message": "설정이 없습니다"}
    
    active_config = None
    latest_config = None
    
    for config in user_configs:
        if config["is_active"]:
            active_config = config
        if latest_config is None or config["updated_at"] > latest_config["updated_at"]:
            latest_config = config
    
    result_config = active_config if active_config else latest_config
    
    return {
        "config": result_config,
        "message": "활성 설정" if active_config else "비활성 설정",
        "total_configs": len(user_configs)
    }


@app.post("/trading-configs", response_model=AutoTradingConfig)
async def create_or_update_trading_config(config: AutoTradingConfig):
    """자동매매 설정을 생성하거나 업데이트합니다."""
    try:
        configs_data = load_trading_configs()

        existing_config_index = None
        for i, existing_config in enumerate(configs_data):
            if (existing_config["user_id"] == config.user_id and 
                existing_config["stock_code"] == config.stock_code and
                existing_config.get("strategy_type", "mtt") == config.strategy_type):
                existing_config_index = i
                break

        # 설정을 딕셔너리로 변환
        config_dict = config.dict()
        
        if existing_config_index is not None:
            existing_config = configs_data[existing_config_index]
            config_dict["id"] = existing_config["id"]
            config_dict["created_at"] = existing_config["created_at"]
            config_dict["updated_at"] = datetime.now().isoformat()
            
            configs_data[existing_config_index] = config_dict
        else:
            config_dict["id"] = get_next_config_id()
            config_dict["created_at"] = datetime.now().isoformat()
            config_dict["updated_at"] = datetime.now().isoformat()
            
            configs_data.append(config_dict)

        save_trading_configs(configs_data)

        return config
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"설정 처리 오류: {str(e)}")


@app.get("/trading-configs/{user_id}", response_model=List[AutoTradingConfig])
async def get_user_trading_configs(user_id: str, strategy_type: Optional[str] = None):
    """사용자별 자동매매 설정을 조회합니다. (strategy_type 필터 지원)"""
    configs_data = load_trading_configs()
    user_configs = [
        config for config in configs_data 
        if config["user_id"] == user_id
    ]
    
    # strategy_type 필터링
    if strategy_type:
        user_configs = [
            config for config in user_configs
            if config.get("strategy_type", "mtt") == strategy_type
        ]
    
    return user_configs


@app.put("/trading-configs/{config_id}", response_model=AutoTradingConfig)
async def update_trading_config(config_id: int, updated_config: AutoTradingConfig):
    """자동매매 설정을 수정합니다."""
    configs_data = load_trading_configs()

    for i, config in enumerate(configs_data):
        if config["id"] == config_id:
            updated_config.id = config_id
            updated_config.created_at = config.get("created_at")
            updated_config.updated_at = datetime.now().isoformat()

            for j, other_config in enumerate(configs_data):
                if (i != j and 
                    other_config["user_id"] == updated_config.user_id and
                    other_config["stock_code"] == updated_config.stock_code and
                    other_config["is_active"] and updated_config.is_active):
                    raise HTTPException(
                        status_code=400,
                        detail=f"사용자 '{updated_config.user_id}'의 종목 '{updated_config.stock_code}' 활성 설정이 이미 존재합니다"
                    )

            # 설정을 딕셔너리로 변환
            config_dict = updated_config.dict()
            
            configs_data[i] = config_dict
            save_trading_configs(configs_data)
            return updated_config

    raise HTTPException(
        status_code=404, 
        detail=f"ID {config_id}인 자동매매 설정을 찾을 수 없습니다"
    )


@app.delete("/trading-configs/{config_id}")
async def delete_trading_config(config_id: int):
    """자동매매 설정을 삭제합니다."""
    configs_data = load_trading_configs()

    for i, config in enumerate(configs_data):
        if config["id"] == config_id:
            deleted_config = configs_data.pop(i)
            save_trading_configs(configs_data)
            return {
                "message": f"자동매매 설정 '{deleted_config['stock_name']} ({deleted_config['stock_code']})'이 삭제되었습니다"
            }

    raise HTTPException(
        status_code=404, 
        detail=f"ID {config_id}인 자동매매 설정을 찾을 수 없습니다"
    )


@app.delete("/trading-configs/user/{user_id}/stock/{stock_code}")
async def delete_trading_config_by_user_stock(user_id: str, stock_code: str, strategy_type: Optional[str] = None):
    """특정 사용자의 특정 종목 자동매매 설정을 삭제합니다. (strategy_type 필터 지원)"""
    configs_data = load_trading_configs()
    
    deleted_configs = []
    filtered_configs = []
    
    for config in configs_data:
        if (config["user_id"] == user_id and config["stock_code"] == stock_code):
            # strategy_type이 지정된 경우 해당 전략만 삭제
            if strategy_type and config.get("strategy_type", "mtt") != strategy_type:
                filtered_configs.append(config)
            else:
                deleted_configs.append(config)
        else:
            filtered_configs.append(config)
    
    if deleted_configs:
        save_trading_configs(filtered_configs)
        
        stock_name = deleted_configs[0]['stock_name']
        return {
            "success": True,
            "message": f"{stock_name} ({stock_code}) 자동매매 설정 {len(deleted_configs)}개가 삭제되었습니다"
        }
    
    raise HTTPException(
        status_code=404, 
        detail=f"사용자 {user_id}의 {stock_code} 자동매매 설정을 찾을 수 없습니다"
    )


@app.get("/health")
async def health_check():
    """API 상태를 확인합니다."""
    return {"status": "healthy", "message": "API가 정상적으로 작동중입니다"}


if __name__ == "__main__":
    initialize_sample_data()
    uvicorn.run(app, host="0.0.0.0", port=8080)
