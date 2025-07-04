# 주식 API 테스트 스크립트

import requests
import json

# API 기본 URL
BASE_URL = "http://localhost:8000"

def test_health():
    """헬스 체크 테스트"""
    response = requests.get(f"{BASE_URL}/health")
    print("✅ 헬스 체크:", response.json())

def test_get_all_stocks():
    """전체 주식 목록 조회"""
    response = requests.get(f"{BASE_URL}/stocks")
    print("✅ 전체 주식 목록:")
    for stock in response.json():
        print(f"  - {stock['name']} ({stock['code']}): 목표가 {stock.get('target_price', 'N/A')}")

def test_create_stock():
    """새로운 주식 종목 추가"""
    new_stock = {
        "code": "096770",
        "name": "SK이노베이션",
        "market": "KOSPI",
        "target_price": 120000,
        "stop_loss_percent": 15.0,
        "target_profit_percent": 30.0,
        "memo": "석유화학 및 배터리"
    }
    
    response = requests.post(f"{BASE_URL}/stocks", json=new_stock)
    if response.status_code == 200:
        print("✅ 새 주식 추가 성공:", response.json()['name'])
    else:
        print("❌ 주식 추가 실패:", response.json())

def test_get_stock_by_code():
    """종목 코드로 조회"""
    response = requests.get(f"{BASE_URL}/stocks/code/005930")
    if response.status_code == 200:
        stock = response.json()
        print(f"✅ 종목 조회 성공: {stock['name']} - 목표가: {stock.get('target_price', 'N/A')}")
    else:
        print("❌ 종목 조회 실패:", response.json())

def test_update_stock():
    """주식 정보 수정"""
    updated_data = {
        "code": "005930",
        "name": "삼성전자",
        "market": "KOSPI",
        "target_price": 85000,  # 목표가 수정
        "stop_loss_percent": 8.0,
        "target_profit_percent": 25.0,
        "memo": "반도체 대장주 - 목표가 상향 조정"
    }
    
    response = requests.put(f"{BASE_URL}/stocks/1", json=updated_data)
    if response.status_code == 200:
        print("✅ 주식 정보 수정 성공")
    else:
        print("❌ 주식 정보 수정 실패:", response.json())

def main():
    print("🚀 주식 API 테스트 시작\n")
    
    try:
        test_health()
        print()
        
        test_get_all_stocks()
        print()
        
        test_create_stock()
        print()
        
        test_get_stock_by_code()
        print()
        
        test_update_stock()
        print()
        
        print("📊 최종 주식 목록:")
        test_get_all_stocks()
        
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        print("서버 실행: python main.py")

if __name__ == "__main__":
    main()
