"""
매매복기 데이터 동기화 관리자
trading_summary.csv 파일 변경 감지 및 Backend API 동기화
"""

import os
import json
import time
import logging
import csv
import requests
from datetime import datetime
from typing import Dict, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradingSummaryConfig:
    """동기화 설정 관리"""
    
    def __init__(self, config_file: str = "trading_sync_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """설정 파일 로드"""
        default_config = {
            "backend_url": "http://localhost:8000",
            "api_key": "",
            "user_id": 1,  # 기본 사용자 ID
            "sync_enabled": True,
            "retry_count": 3,
            "retry_delay": 5,
            "debounce_delay": 5,
            "csv_file_path": "tradingBot/trading_summary.csv",
            "backup_enabled": True,
            "backup_directory": "backups/"
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                logger.error(f"설정 파일 로드 실패: {e}")
        else:
            # 기본 설정 파일 생성
            self.save_config(default_config)
        
        return default_config
    
    def save_config(self, config: Dict):
        """설정 파일 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"설정 파일 저장 실패: {e}")
    
    def get(self, key: str, default=None):
        """설정 값 조회"""
        return self.config.get(key, default)

class TradingSummarySync:
    """매매복기 데이터 동기화 메인 클래스"""
    
    def __init__(self, config: TradingSummaryConfig):
        self.config = config
        self.csv_path = config.get("csv_file_path")
        self.backend_url = config.get("backend_url")
        self.api_key = config.get("api_key")
        self.user_id = config.get("user_id")
        self.retry_count = config.get("retry_count", 3)
        self.retry_delay = config.get("retry_delay", 5)
        
    def parse_csv_row(self, row: Dict) -> Dict:
        """CSV 행을 API 형식으로 변환"""
        try:
            # 날짜 변환 헬퍼
            def parse_date(date_str):
                if not date_str or date_str.strip() == "":
                    return None
                try:
                    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").isoformat()
                except ValueError:
                    try:
                        return datetime.strptime(date_str, "%Y-%m-%d").isoformat()
                    except ValueError:
                        logger.warning(f"날짜 파싱 실패: {date_str}")
                        return None
            
            # 숫자 변환 헬퍼
            def parse_number(value, default=0):
                if not value or value.strip() == "":
                    return default
                try:
                    return float(value) if '.' in str(value) else int(value)
                except ValueError:
                    logger.warning(f"숫자 파싱 실패: {value}")
                    return default
            
            return {
                "stock_code": row.get("stock_code", "").strip(),
                "stock_name": row.get("stock_name", "").strip(),
                "first_entry_date": parse_date(row.get("first_entry_date")),
                "last_exit_date": parse_date(row.get("last_exit_date")),
                "total_buy_amount": parse_number(row.get("total_buy_amount"), 0),
                "total_sell_amount": parse_number(row.get("total_sell_amount"), 0),
                "total_profit_loss": parse_number(row.get("total_profit_loss"), 0),
                "profit_loss_percent": parse_number(row.get("profit_loss_percent"), 0.0),
                "max_drawdown": parse_number(row.get("max_drawdown")) if row.get("max_drawdown") else None,
                "holding_days": parse_number(row.get("holding_days"), 0.0),
                "entry_count": parse_number(row.get("entry_count"), 0),
                "exit_count": parse_number(row.get("exit_count"), 0),
                "trading_mode": row.get("trading_mode", "manual").strip(),
                "win_rate": parse_number(row.get("win_rate"), 0.0),
                "avg_holding_days": parse_number(row.get("avg_holding_days"), 0.0),
                "max_profit_percent": parse_number(row.get("max_profit_percent")) if row.get("max_profit_percent") else None,
                "final_status": row.get("final_status", "HOLDING").strip()
            }
        except Exception as e:
            logger.error(f"CSV 행 파싱 실패: {e}, 데이터: {row}")
            return None
    
    def read_csv_file(self) -> List[Dict]:
        """CSV 파일 읽기"""
        try:
            if not os.path.exists(self.csv_path):
                logger.warning(f"CSV 파일이 존재하지 않습니다: {self.csv_path}")
                return []
            
            data = []
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row_num, row in enumerate(reader, start=2):  # 헤더 제외
                    parsed_row = self.parse_csv_row(row)
                    if parsed_row and parsed_row["stock_code"]:  # 유효한 데이터만
                        data.append(parsed_row)
                    elif parsed_row:
                        logger.warning(f"빈 종목코드 감지 (행 {row_num}): {row}")
            
            logger.info(f"CSV 파일에서 {len(data)}개의 유효한 데이터 읽기 완료")
            return data
            
        except Exception as e:
            logger.error(f"CSV 파일 읽기 실패: {e}")
            return []
    
    def send_to_backend(self, data: Dict) -> bool:
        """Backend API로 데이터 전송"""
        try:
            headers = {
                'Content-Type': 'application/json'
            }
            
            # API 키가 있으면 Authorization 헤더 추가
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            url = f"{self.backend_url}/api/trading-summary"
            
            for attempt in range(self.retry_count):
                try:
                    response = requests.post(
                        url,
                        json=data,
                        headers=headers,
                        timeout=30
                    )
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"데이터 전송 성공: {data['stock_code']} - {data['stock_name']}")
                        return True
                    elif response.status_code == 401:
                        logger.error("인증 실패: API 키를 확인하세요")
                        return False
                    else:
                        logger.warning(f"API 응답 오류 (시도 {attempt + 1}/{self.retry_count}): {response.status_code} - {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"네트워크 오류 (시도 {attempt + 1}/{self.retry_count}): {e}")
                
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
            
            logger.error(f"데이터 전송 실패 (모든 재시도 완료): {data['stock_code']}")
            return False
            
        except Exception as e:
            logger.error(f"Backend 전송 중 예외 발생: {e}")
            return False
    
    def sync_all_data(self):
        """전체 데이터 동기화"""
        logger.info("전체 데이터 동기화 시작")
        
        data_list = self.read_csv_file()
        if not data_list:
            logger.warning("동기화할 데이터가 없습니다")
            return
        
        success_count = 0
        for data in data_list:
            if self.send_to_backend(data):
                success_count += 1
            time.sleep(0.1)  # API 호출 간격
        
        logger.info(f"전체 동기화 완료: {success_count}/{len(data_list)} 성공")
    
    def backup_csv_file(self):
        """CSV 파일 백업"""
        if not self.config.get("backup_enabled"):
            return
        
        try:
            backup_dir = self.config.get("backup_directory", "backups/")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"trading_summary_{timestamp}.csv")
            
            import shutil
            shutil.copy2(self.csv_path, backup_path)
            logger.info(f"CSV 파일 백업 완료: {backup_path}")
            
        except Exception as e:
            logger.error(f"CSV 파일 백업 실패: {e}")

class CSVFileHandler(FileSystemEventHandler):
    """CSV 파일 변경 감지 핸들러"""
    
    def __init__(self, sync_manager: TradingSummarySync):
        self.sync_manager = sync_manager
        self.last_modified = 0
        self.debounce_delay = sync_manager.config.get("debounce_delay", 5)
        
    def on_modified(self, event):
        if event.is_directory:
            return
        
        if event.src_path.endswith('trading_summary.csv'):
            current_time = time.time()
            
            # 디바운스: 짧은 시간 내 연속 수정 이벤트 방지
            if current_time - self.last_modified < self.debounce_delay:
                return
            
            self.last_modified = current_time
            logger.info(f"CSV 파일 변경 감지: {event.src_path}")
            
            # 백업 생성
            self.sync_manager.backup_csv_file()
            
            # 동기화 실행
            self.sync_manager.sync_all_data()

class TradingSyncWatcher:
    """메인 감시자 클래스"""
    
    def __init__(self, config_file: str = "trading_sync_config.json"):
        self.config = TradingSummaryConfig(config_file)
        self.sync_manager = TradingSummarySync(self.config)
        self.observer = None
        
    def start_watching(self):
        """파일 감시 시작"""
        if not self.config.get("sync_enabled"):
            logger.info("동기화가 비활성화되어 있습니다")
            return
        
        csv_dir = os.path.dirname(self.sync_manager.csv_path)
        if not os.path.exists(csv_dir):
            logger.error(f"감시할 디렉터리가 존재하지 않습니다: {csv_dir}")
            return
        
        event_handler = CSVFileHandler(self.sync_manager)
        self.observer = Observer()
        self.observer.schedule(event_handler, path=csv_dir, recursive=False)
        
        try:
            self.observer.start()
            logger.info(f"CSV 파일 감시 시작: {csv_dir}/trading_summary.csv")
            logger.info("Ctrl+C로 종료하세요")
            
            # 시작 시 전체 동기화 실행
            logger.info("시작 시 전체 동기화 실행")
            self.sync_manager.sync_all_data()
            
            # 감시 유지
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("사용자에 의한 종료 요청")
            
        except Exception as e:
            logger.error(f"파일 감시 중 오류 발생: {e}")
        finally:
            if self.observer:
                self.observer.stop()
                self.observer.join()
                logger.info("파일 감시 종료")
    
    def manual_sync(self):
        """수동 동기화"""
        logger.info("수동 동기화 실행")
        self.sync_manager.sync_all_data()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='매매복기 CSV 파일 동기화')
    parser.add_argument('--config', default='trading_sync_config.json', help='설정 파일 경로')
    parser.add_argument('--manual', action='store_true', help='수동 동기화 실행')
    parser.add_argument('--watch', action='store_true', default=True, help='파일 감시 모드')
    
    args = parser.parse_args()
    
    watcher = TradingSyncWatcher(args.config)
    
    if args.manual:
        watcher.manual_sync()
    else:
        watcher.start_watching()