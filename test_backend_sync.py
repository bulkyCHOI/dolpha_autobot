#!/usr/bin/env python3
"""
Backend API 연동 테스트 및 기존 CSV 데이터 동기화
"""

import os
import csv
import sys
from datetime import datetime

# tradingBot 모듈을 import하기 위한 path 설정
sys.path.append(os.path.join(os.path.dirname(__file__), 'tradingBot'))

from tradingBot.backend_api_client import backend_client


def read_csv_data():
    """CSV 파일에서 데이터를 읽어옵니다."""
    csv_file = "tradingBot/trading_summary.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV 파일이 없습니다: {csv_file}")
        return []
    
    data = []
    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 데이터 타입 변환
                record = {
                    'stock_code': row.get('stock_code', ''),
                    'stock_name': row.get('stock_name', ''),
                    'first_entry_date': row.get('first_entry_date') if row.get('first_entry_date') else '',
                    'last_exit_date': row.get('last_exit_date') if row.get('last_exit_date') else '',
                    'total_buy_amount': int(float(row.get('total_buy_amount', 0))),
                    'total_sell_amount': int(float(row.get('total_sell_amount', 0))),
                    'total_profit_loss': int(float(row.get('total_profit_loss', 0))),
                    'profit_loss_percent': float(row.get('profit_loss_percent', 0.0)),
                    'max_drawdown': float(row.get('max_drawdown')) if row.get('max_drawdown') and row.get('max_drawdown') != '' else None,
                    'holding_days': float(row.get('holding_days', 0.0)),
                    'entry_count': int(float(row.get('entry_count', 0))),
                    'exit_count': int(float(row.get('exit_count', 0))),
                    'trading_mode': row.get('trading_mode', 'manual'),
                    'win_rate': float(row.get('win_rate', 0.0)),
                    'avg_holding_days': float(row.get('avg_holding_days', 0.0)),
                    'max_profit_percent': float(row.get('max_profit_percent')) if row.get('max_profit_percent') and row.get('max_profit_percent') != '' else None,
                    'final_status': row.get('final_status', 'CLOSED')
                }
                data.append(record)
                
        print(f"✅ CSV 파일에서 {len(data)}개 레코드를 읽었습니다.")
        return data
        
    except Exception as e:
        print(f"❌ CSV 파일 읽기 오류: {e}")
        return []


def test_backend_connection():
    """Backend 서버 연결을 테스트합니다."""
    print("🔗 Backend 서버 연결 테스트...")
    
    if backend_client.test_connection():
        print("✅ Backend 서버 연결 성공")
        return True
    else:
        print("❌ Backend 서버 연결 실패")
        return False


def sync_data_to_backend(data):
    """CSV 데이터를 Backend로 동기화합니다."""
    if not data:
        print("❌ 동기화할 데이터가 없습니다.")
        return
    
    print(f"📤 {len(data)}개 레코드를 Backend로 동기화 중...")
    
    success_count = 0
    fail_count = 0
    
    for record in data:
        try:
            success = backend_client.send_trading_summary(record)
            if success:
                print(f"✅ {record['stock_name']} ({record['stock_code']}) 동기화 성공")
                success_count += 1
            else:
                print(f"❌ {record['stock_name']} ({record['stock_code']}) 동기화 실패")
                fail_count += 1
        except Exception as e:
            print(f"❌ {record['stock_name']} ({record['stock_code']}) 동기화 오류: {e}")
            fail_count += 1
    
    print(f"\n📊 동기화 결과:")
    print(f"   성공: {success_count}개")
    print(f"   실패: {fail_count}개")
    print(f"   총합: {len(data)}개")


def main():
    """메인 함수"""
    print("🚀 Backend API 연동 테스트 및 CSV 데이터 동기화")
    print("=" * 60)
    
    # 1. Backend 연결 테스트
    if not test_backend_connection():
        print("Backend 서버가 실행되지 않았습니다. Django 서버를 시작하세요.")
        return
    
    # 2. CSV 데이터 읽기
    data = read_csv_data()
    if not data:
        print("동기화할 데이터가 없습니다.")
        return
    
    # 3. 데이터 동기화
    sync_data_to_backend(data)
    
    print("\n✨ 동기화 작업 완료!")


if __name__ == "__main__":
    main()