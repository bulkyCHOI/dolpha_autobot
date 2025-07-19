#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한국투자증권 API 계좌 정보 테스트 스크립트
"""

import sys
import os

# tradingBot 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'tradingBot'))

try:
    import KIS_Common as Common
    import KIS_API_Helper_KR as KisKR
    import json
    import requests
except ImportError as e:
    print(f"모듈 임포트 오류: {e}")
    sys.exit(1)

def test_token_generation():
    """토큰 생성 테스트"""
    print("=== 토큰 생성 테스트 ===")
    try:
        # 모의계좌 모드로 설정
        Common.SetChangeMode("VIRTUAL")
        
        # 토큰 생성 시도
        token = Common.MakeToken("VIRTUAL")
        if token != "FAIL":
            print(f"✅ 토큰 생성 성공: {token[:20]}...")
            return True
        else:
            print("❌ 토큰 생성 실패")
            return False
    except Exception as e:
        print(f"❌ 토큰 생성 오류: {e}")
        return False

def test_account_info():
    """계좌 정보 테스트"""
    print("\n=== 계좌 정보 확인 ===")
    try:
        app_key = Common.GetAppKey("VIRTUAL")
        app_secret = Common.GetAppSecret("VIRTUAL")
        account_no = Common.GetAccountNo("VIRTUAL")
        prdt_cd = Common.GetPrdtNo("VIRTUAL")
        url = Common.GetUrlBase("VIRTUAL")
        
        print(f"APP_KEY: {app_key[:10]}...")
        print(f"APP_SECRET: {app_secret[:10]}...")
        print(f"계좌번호: {account_no}")
        print(f"상품코드: {prdt_cd}")
        print(f"URL: {url}")
        
        return True
    except Exception as e:
        print(f"❌ 계좌 정보 조회 오류: {e}")
        return False

def test_balance_api():
    """잔고 조회 API 직접 테스트"""
    print("\n=== 잔고 조회 API 테스트 ===")
    try:
        # 모의계좌 설정
        Common.SetChangeMode("VIRTUAL")
        
        # 토큰 가져오기
        token = Common.GetToken("VIRTUAL")
        
        # API 호출 정보
        app_key = Common.GetAppKey("VIRTUAL")
        app_secret = Common.GetAppSecret("VIRTUAL")
        account_no = Common.GetAccountNo("VIRTUAL")
        prdt_cd = Common.GetPrdtNo("VIRTUAL")
        url = Common.GetUrlBase("VIRTUAL")
        
        # 헤더 설정
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": app_key,
            "appsecret": app_secret,
            "tr_id": "VTTC8434R",  # 모의투자 잔고 조회
            "custtype": "P"
        }
        
        # 파라미터 설정
        params = {
            "CANO": account_no,
            "ACNT_PRDT_CD": prdt_cd,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        
        # API 호출
        api_url = f"{url}/uapi/domestic-stock/v1/trading/inquire-balance"
        print(f"API URL: {api_url}")
        print(f"계좌번호: {account_no}")
        print(f"상품코드: {prdt_cd}")
        
        response = requests.get(api_url, headers=headers, params=params)
        
        print(f"응답 코드: {response.status_code}")
        print(f"응답 내용: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("rt_cd") == "0":
                print("✅ 잔고 조회 성공!")
                return True
            else:
                print(f"❌ API 오류: {result}")
                return False
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 잔고 조회 오류: {e}")
        return False

def test_kis_kr_balance():
    """KIS_API_Helper_KR을 통한 잔고 조회 테스트"""
    print("\n=== KIS_API_Helper_KR 잔고 조회 테스트 ===")
    try:
        Common.SetChangeMode("VIRTUAL")
        balance = KisKR.GetBalance()
        print(f"✅ 잔고 조회 성공: {balance}")
        return True
    except Exception as e:
        print(f"❌ KIS_API_Helper_KR 잔고 조회 오류: {e}")
        return False

def main():
    """메인 함수"""
    print("한국투자증권 API 계좌 진단 시작\n")
    
    # 1. 계좌 정보 확인
    if not test_account_info():
        print("계좌 정보 확인 실패. myStockInfo.yaml 파일을 확인하세요.")
        return
    
    # 2. 토큰 생성 테스트
    if not test_token_generation():
        print("토큰 생성 실패. APP_KEY와 APP_SECRET을 확인하세요.")
        return
    
    # 3. 직접 API 호출 테스트
    test_balance_api()
    
    # 4. KIS_API_Helper_KR 테스트
    test_kis_kr_balance()
    
    print("\n=== 진단 완료 ===")
    print("\n📋 문제 해결 가이드:")
    print("1. 계좌번호가 8자리인지 확인")
    print("2. 모의투자 계좌가 활성화되어 있는지 확인")
    print("3. APP_KEY/SECRET이 모의투자용인지 확인")
    print("4. 한국투자증권 홈페이지에서 API 사용 설정 확인")

if __name__ == "__main__":
    main()