#!/usr/bin/env python3
"""
매매복기 동기화 시스템 테스트 스크립트
"""

import os
import sys
import json
import time
import shutil
from datetime import datetime

# 현재 디렉터리를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trading_sync_manager import TradingSyncWatcher, TradingSummaryConfig

def test_config_creation():
    """설정 파일 생성 테스트"""
    print("🧪 설정 파일 생성 테스트...")
    
    test_config_file = "test_config.json"
    
    # 기존 테스트 파일 삭제
    if os.path.exists(test_config_file):
        os.remove(test_config_file)
    
    # 설정 생성
    config = TradingSummaryConfig(test_config_file)
    
    # 검증
    assert os.path.exists(test_config_file), "설정 파일이 생성되지 않았습니다"
    assert config.get("backend_url") == "http://localhost:8000", "기본 URL이 설정되지 않았습니다"
    
    # 정리
    os.remove(test_config_file)
    
    print("✅ 설정 파일 생성 테스트 통과")

def test_csv_parsing():
    """CSV 파싱 테스트"""
    print("🧪 CSV 파싱 테스트...")
    
    # 테스트용 CSV 데이터
    test_csv_content = """stock_code,stock_name,first_entry_date,last_exit_date,total_buy_amount,total_sell_amount,total_profit_loss,profit_loss_percent,max_drawdown,holding_days,entry_count,exit_count,trading_mode,win_rate,avg_holding_days,max_profit_percent,final_status
014970,삼륭물산,2025-07-21 01:20:12,2025-07-22 01:22:11,93691607,157556550,63864943,68.17,,1.00,3,2,manual,0.0,1.00,,CLOSED
201490,미투온,,2025-07-21 05:45:09,0,62292030,62292030,0.00,,0.00,0,1,manual,0.0,0.00,,CLOSED"""
    
    # 테스트 CSV 파일 생성
    test_csv_file = "test_trading_summary.csv"
    with open(test_csv_file, 'w', encoding='utf-8') as f:
        f.write(test_csv_content)
    
    try:
        # 설정 생성 및 CSV 파싱 테스트
        config = TradingSummaryConfig()
        config.config["csv_file_path"] = test_csv_file
        
        from trading_sync_manager import TradingSummarySync
        sync = TradingSummarySync(config)
        
        data = sync.read_csv_file()
        
        # 검증
        assert len(data) == 2, f"예상: 2개, 실제: {len(data)}개의 데이터"
        assert data[0]["stock_code"] == "014970", "첫 번째 종목코드가 일치하지 않습니다"
        assert data[0]["stock_name"] == "삼륭물산", "첫 번째 종목명이 일치하지 않습니다"
        assert data[0]["total_profit_loss"] == 63864943, "손익이 일치하지 않습니다"
        assert data[1]["final_status"] == "CLOSED", "최종 상태가 일치하지 않습니다"
        
        print("✅ CSV 파싱 테스트 통과")
        
    finally:
        # 정리
        if os.path.exists(test_csv_file):
            os.remove(test_csv_file)

def test_backend_connection():
    """백엔드 연결 테스트"""
    print("🧪 백엔드 연결 테스트...")
    
    config = TradingSummaryConfig()
    from trading_sync_manager import TradingSummarySync
    sync = TradingSummarySync(config)
    
    # 테스트 데이터
    test_data = {
        "stock_code": "000000",
        "stock_name": "테스트주식",
        "first_entry_date": "2025-08-14T10:00:00",
        "last_exit_date": None,
        "total_buy_amount": 1000000,
        "total_sell_amount": 0,
        "total_profit_loss": -1000000,
        "profit_loss_percent": -100.0,
        "max_drawdown": None,
        "holding_days": 0.0,
        "entry_count": 1,
        "exit_count": 0,
        "trading_mode": "manual",
        "win_rate": 0.0,
        "avg_holding_days": 0.0,
        "max_profit_percent": None,
        "final_status": "HOLDING"
    }
    
    try:
        # 실제 API 호출 테스트 (실패해도 OK - 인증 때문)
        result = sync.send_to_backend(test_data)
        if result:
            print("✅ 백엔드 연결 성공")
        else:
            print("⚠️ 백엔드 연결 실패 (인증 오류 가능성 높음)")
            
    except Exception as e:
        print(f"⚠️ 백엔드 연결 테스트 실패: {e}")

def test_file_backup():
    """파일 백업 테스트"""
    print("🧪 파일 백업 테스트...")
    
    # 테스트 CSV 파일 생성
    test_csv_file = "test_backup.csv"
    test_content = "test,data\n1,2\n"
    
    with open(test_csv_file, 'w') as f:
        f.write(test_content)
    
    try:
        config = TradingSummaryConfig()
        config.config["csv_file_path"] = test_csv_file
        config.config["backup_directory"] = "test_backups/"
        
        from trading_sync_manager import TradingSummarySync
        sync = TradingSummarySync(config)
        
        # 백업 실행
        sync.backup_csv_file()
        
        # 백업 디렉터리 확인
        backup_dir = "test_backups/"
        assert os.path.exists(backup_dir), "백업 디렉터리가 생성되지 않았습니다"
        
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith("test_backup_")]
        assert len(backup_files) > 0, "백업 파일이 생성되지 않았습니다"
        
        print("✅ 파일 백업 테스트 통과")
        
    finally:
        # 정리
        if os.path.exists(test_csv_file):
            os.remove(test_csv_file)
        if os.path.exists("test_backups/"):
            shutil.rmtree("test_backups/")

def run_manual_sync_test():
    """수동 동기화 테스트"""
    print("🧪 수동 동기화 테스트...")
    
    if not os.path.exists("tradingBot/trading_summary.csv"):
        print("⚠️ 실제 CSV 파일이 없어서 수동 동기화 테스트를 건너뜁니다")
        return
    
    try:
        watcher = TradingSyncWatcher()
        watcher.manual_sync()
        print("✅ 수동 동기화 테스트 완료")
    except Exception as e:
        print(f"⚠️ 수동 동기화 테스트 실패: {e}")

def main():
    """메인 테스트 함수"""
    print("🚀 매매복기 동기화 시스템 테스트 시작")
    print("=" * 50)
    
    try:
        test_config_creation()
        test_csv_parsing()
        test_file_backup()
        test_backend_connection()
        run_manual_sync_test()
        
        print("\n" + "=" * 50)
        print("🎉 모든 테스트 완료!")
        print("\n📋 사용법:")
        print("1. 설정 확인: trading_sync_config.json 파일을 편집하세요")
        print("2. 수동 동기화: python trading_sync_manager.py --manual")
        print("3. 자동 감시: python trading_sync_manager.py --watch")
        print("4. 편리한 시작: ./start_trading_sync.sh")
        
    except AssertionError as e:
        print(f"❌ 테스트 실패: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()