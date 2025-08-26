"""
Backend API 호출 클라이언트
"""
import requests
import json
from datetime import datetime
from typing import Dict, Optional


class BackendAPIClient:
    """Backend Django API와 통신하는 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:8000", user_id: int = 1):
        self.base_url = base_url.rstrip('/')
        self.user_id = user_id
        self.timeout = 10
        
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """HTTP 요청을 수행합니다."""
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {
                'Content-Type': 'application/json'
            }
            
            kwargs = {
                'timeout': self.timeout,
                'headers': headers
            }
            
            if data:
                kwargs['json'] = data
                
            response = requests.request(method, url, **kwargs)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"Backend API 오류 ({response.status_code}): {response.text}")
                return None
                
        except requests.RequestException as e:
            print(f"Backend API 요청 실패: {e}")
            return None
        except Exception as e:
            print(f"Backend API 예외: {e}")
            return None
    
    def send_trading_summary(self, trading_data: Dict) -> bool:
        """매매복기 데이터를 Backend로 전송합니다."""
        try:
            # user_id 추가
            trading_data['user_id'] = self.user_id
            
            # 날짜 문자열을 ISO 형식으로 변환
            for date_field in ['first_entry_date', 'last_exit_date']:
                if trading_data.get(date_field) and trading_data[date_field].strip():
                    try:
                        # CSV에서 읽어온 형식: "2025-07-21 01:20:12"
                        dt = datetime.strptime(trading_data[date_field], "%Y-%m-%d %H:%M:%S")
                        trading_data[date_field] = dt.isoformat()
                    except ValueError:
                        # 이미 ISO 형식이거나 다른 형식인 경우 그대로 유지
                        pass
                else:
                    # 빈 문자열이거나 None인 경우 None으로 설정
                    trading_data[date_field] = None
            
            result = self._make_request('POST', '/api/autobot/trading-summary', trading_data)
            
            if result:
                print(f"[{trading_data['stock_name']}] Backend DB 저장 성공")
                return True
            else:
                print(f"[{trading_data['stock_name']}] Backend DB 저장 실패")
                return False
                
        except Exception as e:
            print(f"Backend API 전송 오류: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Backend 서버 연결을 테스트합니다."""
        try:
            result = self._make_request('GET', '/api/hello')
            return result is not None
        except Exception:
            return False


# 전역 인스턴스
backend_client = BackendAPIClient()