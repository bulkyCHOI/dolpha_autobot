#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 봇 - trading_configs.json 기반 자동매매 실행

기능:
- trading_configs.json 파일에서 설정을 읽어와 자동매매 실행
- Manual/Turtle 모드에 따른 차별화된 매매 전략
- 피라미딩 매수 지원
- 리스크 관리 (손절/익절)
- 실계좌/모의계좌 선택 가능

실행: python autoTrading_Bot.py [REAL|VIRTUAL]
"""

import json
import sys
import os
import time
import csv
from datetime import datetime
from pytz import timezone
import traceback
import pprint
from backend_api_client import backend_client

# 현재 디렉토리에 tradingBot 모듈 추가 (현재 파일이 tradingBot 내부에 있으므로 상위 디렉토리 추가)
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    import KIS_Common as Common
    import KIS_API_Helper_KR as KisKR
    import pandas as pd
    import numpy as np
    import telegram_alert
except ImportError as e:
    print(f"모듈 임포트 오류: {e}")
    print("tradingBot 폴더의 파일들이 필요합니다.")
    sys.exit(1)


class AutoTradingBot:
    def __init__(self, mode="VIRTUAL"):
        """
        자동매매 봇 초기화
        Args:
            mode: "REAL" 또는 "VIRTUAL" (KIS API 모드용, 파일명에는 영향 없음)
        """
        self.mode = mode  # KIS API 모드 설정용으로만 사용
        self.trading_configs = []
        self.bot_name = "AutoTrading_Bot"

        # 매수 이력 관리 (종목코드: {'entries': [...], 'avg_price': float, 'entry_count': int})
        self.trade_history = {}
        self.history_file = "trade_history.json"  # 통합된 파일명

        # CSV 로그 파일 경로 (통합)
        self.trade_log_file = "trading_log.csv"
        self.summary_file = "trading_summary.csv"

        # 계좌 모드 설정 (KIS API용)
        Common.SetChangeMode(mode)
        print(f"[{datetime.now()}] 자동매매 봇 시작 - 모드: {mode}")

        # 설정 파일 로드
        self.load_configs()

        # 매수 이력 로드
        self.load_trade_history()

        # CSV 파일 초기화
        self.init_csv_files()

        # 텔레그램 알림 초기화
        self.init_telegram()

    def is_market_open(self):
        """
        장 시간 체크
        Returns:
            bool: 장이 열려있으면 True
        """
        try:
            now = datetime.now(timezone("Asia/Seoul"))
            current_time = now.strftime("%H%M")

            # 평일 체크 (월~금)
            if now.weekday() >= 5:  # 토요일(5), 일요일(6)
                return False

            # 장 시간: 09:00 ~ 15:30
            if "0900" <= current_time <= "1530":
                return True
            else:
                return False

        except Exception as e:
            print(f"시장 시간 체크 오류: {e}")
            return False

    def load_configs(self):
        """trading_configs.json 파일에서 설정 로드"""
        try:
            # autobot 폴더의 trading_configs.json 파일 경로
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "trading_configs.json"
            )
            with open(config_path, "r", encoding="utf-8") as f:
                all_configs = json.load(f)

            # 활성화된 설정만 필터링
            self.trading_configs = [
                config for config in all_configs if config.get("is_active", False)
            ]
            print(f"[{datetime.now()}] 활성 설정 {len(self.trading_configs)}개 로드됨")

        except Exception as e:
            print(f"설정 파일 로드 오류: {e}")
            self.trading_configs = []

    def load_trade_history(self):
        """매수 이력 로드"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.trade_history = json.load(f)
                print(
                    f"[{datetime.now()}] 매수 이력 로드됨: {len(self.trade_history)}개 종목"
                )
            else:
                self.trade_history = {}
                print(f"[{datetime.now()}] 새로운 매수 이력 파일 생성")
        except Exception as e:
            print(f"매수 이력 로드 오류: {e}")
            self.trade_history = {}

    def save_trade_history(self):
        """매수 이력 저장"""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.trade_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"매수 이력 저장 오류: {e}")

    def update_trade_history(
        self, stock_code, stock_name, buy_price, buy_quantity, entry_type="initial"
    ):
        """매수 이력 업데이트"""
        try:
            if stock_code not in self.trade_history:
                self.trade_history[stock_code] = {
                    "stock_name": stock_name,
                    "entries": [],
                    "avg_price": 0.0,
                    "total_quantity": 0,
                    "entry_count": 0,
                }

            # 매수 기록 추가
            self.trade_history[stock_code]["entries"].append(
                {
                    "price": buy_price,
                    "quantity": buy_quantity,
                    "timestamp": datetime.now().isoformat(),
                    "type": entry_type,
                }
            )

            # 평균 단가 및 총 수량 업데이트
            history = self.trade_history[stock_code]
            total_amount = sum(
                entry["price"] * entry["quantity"] for entry in history["entries"]
            )
            total_quantity = sum(entry["quantity"] for entry in history["entries"])

            history["avg_price"] = (
                total_amount / total_quantity if total_quantity > 0 else 0
            )
            history["total_quantity"] = total_quantity
            history["entry_count"] = len(history["entries"])

            # 파일 저장
            self.save_trade_history()

            print(
                f"[{stock_name}] 매수 이력 업데이트 - 평균단가: {history['avg_price']:,.0f}원, 총수량: {total_quantity}주"
            )

        except Exception as e:
            print(f"매수 이력 업데이트 오류: {e}")

    def get_last_entry_price(self, stock_code):
        """마지막 매수가 조회"""
        try:
            if (
                stock_code in self.trade_history
                and self.trade_history[stock_code]["entries"]
            ):
                return self.trade_history[stock_code]["entries"][-1]["price"]
            return None
        except Exception as e:
            print(f"마지막 매수가 조회 오류: {e}")
            return None

    def get_average_price(self, stock_code):
        """평균 매수가 조회"""
        try:
            if stock_code in self.trade_history:
                return self.trade_history[stock_code]["avg_price"]
            return None
        except Exception as e:
            print(f"평균 매수가 조회 오류: {e}")
            return None

    def get_entry_count(self, stock_code):
        """매수 횟수 조회"""
        try:
            if stock_code in self.trade_history:
                return self.trade_history[stock_code]["entry_count"]
            return 0
        except Exception as e:
            print(f"매수 횟수 조회 오류: {e}")
            return 0

    def init_csv_files(self):
        """CSV 파일 초기화 (헤더 생성)"""
        try:
            # 거래 로그 파일 헤더
            trade_log_headers = [
                "timestamp",
                "stock_code",
                "stock_name",
                "action",
                "price",
                "quantity",
                "amount",
                "entry_type",
                "reason",
                "avg_price",
                "total_quantity",
                "profit_loss",
                "profit_loss_percent",
                "trading_mode",
                "stop_loss",
                "take_profit",
                "pyramiding_count",
                "entry_point",
            ]

            # 거래 요약 파일 헤더
            summary_headers = [
                "stock_code",
                "stock_name",
                "first_entry_date",
                "last_exit_date",
                "total_buy_amount",
                "total_sell_amount",
                "total_profit_loss",
                "profit_loss_percent",
                "max_drawdown",
                "holding_days",
                "entry_count",
                "exit_count",
                "trading_mode",
                "win_rate",
                "avg_holding_days",
                "max_profit_percent",
                "final_status",
            ]

            # 거래 로그 파일이 없으면 헤더와 함께 생성
            if not os.path.exists(self.trade_log_file):
                with open(self.trade_log_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(trade_log_headers)
                print(f"[{datetime.now()}] 거래 로그 파일 생성: {self.trade_log_file}")

            # 거래 요약 파일이 없으면 헤더와 함께 생성
            if not os.path.exists(self.summary_file):
                with open(self.summary_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(summary_headers)
                print(f"[{datetime.now()}] 거래 요약 파일 생성: {self.summary_file}")

        except Exception as e:
            print(f"CSV 파일 초기화 오류: {e}")

    def log_trade(
        self,
        stock_code,
        stock_name,
        action,
        price,
        quantity,
        amount,
        entry_type,
        reason,
        avg_price=None,
        total_quantity=None,
        profit_loss=None,
        profit_loss_percent=None,
        config=None,
    ):
        """거래 로그 CSV 파일에 기록"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 설정 정보 추출
            trading_mode = config.get("trading_mode", "") if config else ""
            stop_loss = config.get("stop_loss", "") if config else ""
            take_profit = config.get("take_profit", "") if config else ""
            pyramiding_count = config.get("pyramiding_count", "") if config else ""
            entry_point = config.get("entry_point", "") if config else ""

            # 거래 로그 데이터
            trade_data = [
                timestamp,
                stock_code,
                stock_name,
                action,
                price,
                quantity,
                amount,
                entry_type,
                reason,
                avg_price or "",
                total_quantity or "",
                profit_loss or "",
                profit_loss_percent or "",
                trading_mode,
                stop_loss,
                take_profit,
                pyramiding_count,
                entry_point,
            ]

            # CSV 파일에 추가
            with open(self.trade_log_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(trade_data)

            print(
                f"[{stock_name}] 거래 로그 기록: {action} {quantity}주 @ {price:,.0f}원"
            )

        except Exception as e:
            print(f"거래 로그 기록 오류: {e}")

    def update_trading_summary(self, stock_code):
        """거래 요약 파일 업데이트"""
        try:
            # 기존 요약 데이터 읽기
            summary_data = {}
            if os.path.exists(self.summary_file):
                with open(self.summary_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        summary_data[row["stock_code"]] = row

            # 거래 로그에서 해당 종목 데이터 수집
            trades = []
            if os.path.exists(self.trade_log_file):
                with open(self.trade_log_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row["stock_code"] == stock_code:
                            trades.append(row)

            if not trades:
                return

            # 첫 번째 거래에서 기본 정보 추출
            first_trade = trades[0]
            stock_name = first_trade["stock_name"]
            trading_mode = first_trade["trading_mode"]

            # 매수/매도 거래 분리
            buy_trades = [t for t in trades if t["action"] == "BUY"]
            sell_trades = [t for t in trades if t["action"] == "SELL"]

            # 계산
            first_entry_date = buy_trades[0]["timestamp"] if buy_trades else ""
            last_exit_date = sell_trades[-1]["timestamp"] if sell_trades else ""

            total_buy_amount = sum(
                float(t["amount"]) for t in buy_trades if t["amount"]
            )
            total_sell_amount = sum(
                float(t["amount"]) for t in sell_trades if t["amount"]
            )

            total_profit_loss = total_sell_amount - total_buy_amount
            profit_loss_percent = (
                (total_profit_loss / total_buy_amount * 100)
                if total_buy_amount > 0
                else 0
            )

            entry_count = len(buy_trades)
            exit_count = len(sell_trades)

            # 보유일수 계산
            if first_entry_date and last_exit_date:
                first_dt = datetime.strptime(first_entry_date, "%Y-%m-%d %H:%M:%S")
                last_dt = datetime.strptime(last_exit_date, "%Y-%m-%d %H:%M:%S")
                holding_days = (last_dt - first_dt).total_seconds() / 86400  # 일 단위
            else:
                holding_days = 0

            # 현재 보유 상태 확인
            total_buy_quantity = sum(
                float(t["quantity"]) for t in buy_trades if t["quantity"]
            )
            total_sell_quantity = sum(
                float(t["quantity"]) for t in sell_trades if t["quantity"]
            )
            remaining_quantity = total_buy_quantity - total_sell_quantity

            if remaining_quantity > 0:
                final_status = "HOLDING"
            elif exit_count > 0:
                final_status = "CLOSED"
            else:
                final_status = "HOLDING"

            # 승률 계산 (익절 거래 / 전체 매도 거래)
            profitable_sells = sum(
                1
                for t in sell_trades
                if t["profit_loss"] and float(t["profit_loss"]) > 0
            )
            win_rate = (profitable_sells / len(sell_trades) * 100) if sell_trades else 0

            # 요약 데이터 업데이트
            summary_data[stock_code] = {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "first_entry_date": first_entry_date,
                "last_exit_date": last_exit_date,
                "total_buy_amount": f"{total_buy_amount:.0f}",
                "total_sell_amount": f"{total_sell_amount:.0f}",
                "total_profit_loss": f"{total_profit_loss:.0f}",
                "profit_loss_percent": f"{profit_loss_percent:.2f}",
                "max_drawdown": "",  # 추후 구현
                "holding_days": f"{holding_days:.2f}",
                "entry_count": entry_count,
                "exit_count": exit_count,
                "trading_mode": trading_mode,
                "win_rate": f"{win_rate:.1f}",
                "avg_holding_days": f"{holding_days:.2f}",
                "max_profit_percent": "",  # 추후 구현
                "final_status": final_status,
            }

            # CSV 파일 다시 쓰기
            headers = [
                "stock_code",
                "stock_name",
                "first_entry_date",
                "last_exit_date",
                "total_buy_amount",
                "total_sell_amount",
                "total_profit_loss",
                "profit_loss_percent",
                "max_drawdown",
                "holding_days",
                "entry_count",
                "exit_count",
                "trading_mode",
                "win_rate",
                "avg_holding_days",
                "max_profit_percent",
                "final_status",
            ]

            with open(self.summary_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                for data in summary_data.values():
                    writer.writerow(data)

            print(f"[{stock_name}] 거래 요약 업데이트 완료")
            
            # Backend API로 데이터 전송
            try:
                current_data = summary_data.get(stock_code, {})
                if current_data:
                    # Backend API 호출을 위한 데이터 변환
                    backend_data = {
                        'stock_code': current_data.get('stock_code', ''),
                        'stock_name': current_data.get('stock_name', ''),
                        'first_entry_date': current_data.get('first_entry_date', ''),
                        'last_exit_date': current_data.get('last_exit_date', ''),
                        'total_buy_amount': int(float(current_data.get('total_buy_amount', 0))),
                        'total_sell_amount': int(float(current_data.get('total_sell_amount', 0))),
                        'total_profit_loss': int(float(current_data.get('total_profit_loss', 0))),
                        'profit_loss_percent': float(current_data.get('profit_loss_percent', 0.0)),
                        'max_drawdown': float(current_data.get('max_drawdown')) if current_data.get('max_drawdown') and current_data.get('max_drawdown') != '' else None,
                        'holding_days': float(current_data.get('holding_days', 0.0)),
                        'entry_count': int(float(current_data.get('entry_count', 0))),
                        'exit_count': int(float(current_data.get('exit_count', 0))),
                        'trading_mode': current_data.get('trading_mode', 'manual'),
                        'win_rate': float(current_data.get('win_rate', 0.0)),
                        'avg_holding_days': float(current_data.get('avg_holding_days', 0.0)),
                        'max_profit_percent': float(current_data.get('max_profit_percent')) if current_data.get('max_profit_percent') and current_data.get('max_profit_percent') != '' else None,
                        'final_status': current_data.get('final_status', 'CLOSED')
                    }
                    
                    # Backend API 호출
                    success = backend_client.send_trading_summary(backend_data)
                    if success:
                        print(f"[{stock_name}] Backend DB 동기화 성공")
                    else:
                        print(f"[{stock_name}] Backend DB 동기화 실패")
            except Exception as api_error:
                print(f"[{stock_name}] Backend API 호출 오류: {api_error}")

        except Exception as e:
            print(f"거래 요약 업데이트 오류: {e}")
            import traceback

            traceback.print_exc()

    def init_telegram(self):
        """텔레그램 알림 초기화"""
        try:
            # 봇 시작 알림 # 매번 실행되서 OFF 최초 셋팅시 ON해서 테스트
            # self.send_telegram_message(
            #     f"🚀 자동매매 봇 시작\n\n"
            #     f"🏦 계좌: {self.mode}\n"
            #     f"📊 활성 종목: {len(self.trading_configs)}개\n"
            #     f"🕐 시작시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            # )
            print(f"[{datetime.now()}] 텔레그램 알림 초기화 완료")
        except Exception as e:
            print(f"텔레그램 초기화 오류: {e}")

    def send_telegram_message(self, message, is_urgent=False):
        """텔레그램 메시지 전송"""
        try:
            # telegram_alert 모듈 사용
            telegram_alert.SendMessage(message)

            if is_urgent:
                print(f"[긴급 알림] {message}")
            else:
                print(f"[알림] 텔레그램 메시지 전송 완료")

        except Exception as e:
            print(f"텔레그램 메시지 전송 오류: {e}")

    def send_trade_alert(
        self,
        action,
        stock_code,
        stock_name,
        price,
        quantity,
        amount,
        entry_type,
        reason,
        profit_loss=None,
        profit_loss_percent=None,
        avg_price=None,
        total_quantity=None,
        holding_days=None,
    ):
        """거래 관련 텔레그램 알림"""
        try:
            if action == "BUY":
                emoji = "🟢"
                title = "매수 주문 성공"

                message = (
                    f"{emoji} {title}\n\n"
                    f"📊 종목: {stock_name} ({stock_code})\n"
                    f"💰 매수가: {price:,.0f}원\n"
                    f"📈 수량: {quantity:,.0f}주\n"
                    f"💵 투자금액: {amount:,.0f}원\n"
                    f"🎯 유형: {entry_type}\n"
                    f"📅 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )

                if avg_price and total_quantity:
                    message += (
                        f"\n💡 평균단가: {avg_price:,.0f}원\n"
                        f"📊 총보유: {total_quantity:,.0f}주"
                    )

            elif action == "SELL":
                if profit_loss and profit_loss > 0:
                    emoji = "🔴"
                    title = "매도 주문 성공 (익절)"
                else:
                    emoji = "⚠️"
                    title = (
                        "매도 주문 성공 (손절)"
                        if "손절" in reason
                        else "매도 주문 성공"
                    )

                message = (
                    f"{emoji} {title}\n\n"
                    f"📊 종목: {stock_name} ({stock_code})\n"
                    f"💰 매도가: {price:,.0f}원\n"
                    f"📉 수량: {quantity:,.0f}주\n"
                    f"💵 매도금액: {amount:,.0f}원\n"
                    f"🎯 사유: {reason}\n"
                    f"📅 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )

                if profit_loss is not None and profit_loss_percent is not None:
                    profit_emoji = "💰" if profit_loss >= 0 else "💸"
                    profit_text = "수익" if profit_loss >= 0 else "손실"

                    message += f"\n{profit_emoji} {profit_text}: {profit_loss:+,.0f}원 ({profit_loss_percent:+.2f}%)\n"

                if holding_days:
                    if holding_days < 1:
                        holding_text = f"{holding_days * 24:.1f}시간"
                    else:
                        holding_text = f"{holding_days:.1f}일"
                    message += f"⏰ 보유기간: {holding_text}\n"

            self.send_telegram_message(message, is_urgent=True)

        except Exception as e:
            print(f"거래 알림 전송 오류: {e}")

    def send_error_alert(self, error_type, stock_code, stock_name, error_message):
        """오류 알림"""
        try:
            message = (
                f"⚠️ 시스템 오류 발생\n\n"
                f"🔸 오류유형: {error_type}\n"
                f"📊 종목: {stock_name} ({stock_code})\n"
                f"🔸 오류내용: {error_message}\n"
                f"📅 발생시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"🔄 자동 재시도 중..."
            )

            self.send_telegram_message(message, is_urgent=True)

        except Exception as e:
            print(f"오류 알림 전송 실패: {e}")

    def send_daily_summary(self):
        """일일 결산 알림"""
        try:
            # 오늘 거래 기록 조회
            today = datetime.now().strftime("%Y-%m-%d")
            trades_today = []

            if os.path.exists(self.trade_log_file):
                with open(self.trade_log_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row["timestamp"].startswith(today):
                            trades_today.append(row)

            if not trades_today:
                return

            # 통계 계산
            buy_trades = [t for t in trades_today if t["action"] == "BUY"]
            sell_trades = [t for t in trades_today if t["action"] == "SELL"]

            total_buy_amount = sum(
                float(t["amount"]) for t in buy_trades if t["amount"]
            )
            total_sell_amount = sum(
                float(t["amount"]) for t in sell_trades if t["amount"]
            )

            realized_profit = sum(
                float(t["profit_loss"])
                for t in sell_trades
                if t["profit_loss"] and t["profit_loss"] != ""
            )

            profitable_trades = sum(
                1
                for t in sell_trades
                if t["profit_loss"] and float(t["profit_loss"]) > 0
            )

            win_rate = (
                (profitable_trades / len(sell_trades) * 100) if sell_trades else 0
            )

            message = (
                f"🌅 장 마감 - 일일 결산\n\n"
                f"📅 거래일: {today}\n"
                f"🏦 계좌: {self.mode}\n\n"
                f"📊 오늘의 거래:\n"
                f"  ✅ 매수: {len(buy_trades)}건\n"
                f"  ✅ 매도: {len(sell_trades)}건\n\n"
                f"💰 오늘 수익:\n"
                f"  📈 실현손익: {realized_profit:+,.0f}원\n"
                f"  💵 거래금액: {total_buy_amount:,.0f}원\n\n"
                f"🏆 성과:\n"
                f"  📊 승률: {win_rate:.1f}% ({profitable_trades}/{len(sell_trades)})\n"
            )

            self.send_telegram_message(message)

        except Exception as e:
            print(f"일일 결산 알림 오류: {e}")

    def calculate_position_size(self, config):
        """
        매매모드에 따른 포지션 크기 계산
        - Manual 모드: 계좌잔고 * max_loss% / stop_loss%
        - Turtle 모드: (계좌잔고 * max_loss%) / (ATR * stop_loss배수 / 현재가)
        """
        try:
            balance = KisKR.GetBalance()
            total_money = float(balance["TotalMoney"])
            trading_mode = config.get("trading_mode", "manual")
            max_loss_percent = config.get("max_loss", 2.0) / 100  # 2% -> 0.02

            if trading_mode == "manual":
                # % 기반 계산 (기존 방식)
                stop_loss_percent = config.get("stop_loss", 8.0) / 100  # 8% -> 0.08
                position_amount = total_money * max_loss_percent / stop_loss_percent
                
                print(
                    f"[{config['stock_name']}] Manual 모드 - 계좌잔고: {total_money:,.0f}원, "
                    f"위험허용: {max_loss_percent*100:.1f}%, 손절: {stop_loss_percent*100:.1f}%, "
                    f"포지션: {position_amount:,.0f}원"
                )
                
            elif trading_mode == "turtle":
                # ATR 기반 계산 (새로운 방식)
                stock_code = config["stock_code"]
                atr = self.get_atr(stock_code, 14)
                
                if atr:
                    current_price = float(KisKR.GetCurrentPrice(stock_code))
                    stop_loss_multiplier = config.get("stop_loss", 2.0)  # ATR 배수
                    
                    # 위험 허용 금액
                    risk_amount = total_money * max_loss_percent
                    # ATR 기반 스톱로스 금액 (원)
                    stop_loss_amount = atr * stop_loss_multiplier
                    # 스톱로스 비율
                    stop_loss_ratio = stop_loss_amount / current_price
                    # 포지션 크기 계산
                    position_amount = risk_amount / stop_loss_ratio
                    
                    print(
                        f"[{config['stock_name']}] Turtle 모드 - 계좌잔고: {total_money:,.0f}원, "
                        f"위험허용: {risk_amount:,.0f}원, ATR: {atr:.1f}원, "
                        f"손절폭: {stop_loss_amount:,.0f}원({stop_loss_ratio*100:.1f}%), "
                        f"포지션: {position_amount:,.0f}원"
                    )
                else:
                    # ATR 계산 실패시 manual 방식으로 fallback
                    print(f"[{config['stock_name']}] ATR 계산 실패, Manual 방식으로 fallback")
                    stop_loss_percent = config.get("stop_loss", 2.0) / 100
                    position_amount = total_money * max_loss_percent / stop_loss_percent
                    
                    print(
                        f"[{config['stock_name']}] Fallback - 계좌잔고: {total_money:,.0f}원, "
                        f"포지션: {position_amount:,.0f}원"
                    )
            else:
                # 알 수 없는 모드의 경우 manual 방식으로 처리
                print(f"[{config['stock_name']}] 알 수 없는 매매모드: {trading_mode}, Manual 방식 적용")
                stop_loss_percent = config.get("stop_loss", 8.0) / 100
                position_amount = total_money * max_loss_percent / stop_loss_percent

            return position_amount

        except Exception as e:
            print(f"포지션 크기 계산 오류: {e}")
            return 0

    def calculate_pyramiding_amounts(self, config, total_amount):
        """
        피라미딩 수량 계산 - 각 차수별 증분 금액 반환
        """
        try:
            pyramiding_count = config.get("pyramiding_count", 0)
            positions = config.get("positions", [])

            if pyramiding_count <= 0 or not positions:
                return [total_amount]

            # 포지션 비율 정규화
            total_ratio = sum(positions[: pyramiding_count + 1])
            amounts = []

            for i in range(pyramiding_count + 1):
                if i < len(positions):
                    ratio = positions[i] / total_ratio
                    amount = total_amount * ratio
                    amounts.append(amount)

            return amounts

        except Exception as e:
            print(f"피라미딩 수량 계산 오류: {e}")
            return [total_amount]

    def get_current_entry_amount(self, config, total_amount):
        """
        현재 진입 차수에 해당하는 증분 금액 계산
        """
        try:
            stock_code = config["stock_code"]
            current_entry_count = self.get_entry_count(stock_code)

            # 피라미딩 금액 배열 계산
            amounts = self.calculate_pyramiding_amounts(config, total_amount)
            print(
                f"[{config['stock_name']}] 현재 진입 차수: {current_entry_count}, 금액 배열: {amounts}"
            )
            # 현재 진입 차수에 해당하는 금액 반환
            if current_entry_count < len(amounts):
                return amounts[current_entry_count]
            else:
                # 설정된 피라미딩 횟수를 초과한 경우
                return 0

        except Exception as e:
            print(f"현재 진입 금액 계산 오류: {e}")
            return total_amount

    def get_atr(self, stock_code, period=14):
        """
        ATR(Average True Range) 계산
        """
        try:
            df = Common.GetOhlcv("KR", stock_code, limit=period + 10)
            if df is None or len(df) < period:
                return None

            # True Range 계산
            df["h-l"] = df["high"] - df["low"]
            df["h-pc"] = abs(df["high"] - df["close"].shift(1))
            df["l-pc"] = abs(df["low"] - df["close"].shift(1))
            df["tr"] = df[["h-l", "h-pc", "l-pc"]].max(axis=1)

            # ATR 계산 (단순 이동평균)
            atr = df["tr"].rolling(window=period).mean().iloc[-1]
            return float(atr)

        except Exception as e:
            print(f"ATR 계산 오류 [{stock_code}]: {e}")
            return None

    def check_entry_conditions(self, config):
        """
        진입 조건 체크
        """
        try:
            stock_code = config["stock_code"]
            stock_name = config["stock_name"]
            trading_mode = config.get("trading_mode", "manual")

            # 현재가 조회
            current_price = float(KisKR.GetCurrentPrice(stock_code))

            # 보유 수량 확인
            my_stocks = KisKR.GetMyStockList()
            holding_amount = 0
            for stock in my_stocks:
                if stock["StockCode"] == stock_code:
                    holding_amount = int(stock["StockAmt"])
                    break

            # 이미 보유 중인 경우 피라미딩 체크
            if holding_amount > 0:
                print(
                    f"[{stock_name}] 보유 중 - 현재가: {current_price:,.0f}원, 보유수량: {holding_amount:,.0f}주"
                )
                print(
                    f"[{stock_name}] 피라미딩 조건 체크 - 현재가: {current_price:,.0f}원, 보유수량: {holding_amount:,.0f}주"
                )
                return self.check_pyramiding_conditions(
                    config, current_price, holding_amount
                )

            # 신규 진입 조건 체크
            # 여기서는 단순히 설정된 진입가격 기준으로 체크
            # 실제로는 더 복잡한 기술적 분석이 필요할 수 있음
            entry_point = config.get("entry_point", 0)
            print(
                f"[{stock_name}] 현재가: {current_price:,.0f}원, 진입가: {entry_point:,.0f}원"
            )
            if entry_point > 0 and current_price >= entry_point:
                print(
                    f"[{stock_name}] 신규 진입 조건 충족 - 현재가: {current_price:,.0f}원"
                )
                return True
            else:
                print(
                    f"[{stock_name}] 신규 진입 조건 불충족 - 현재가: {current_price:,.0f}원"
                )
                return False  # 임시로 False 반환

        except Exception as e:
            print(f"진입 조건 체크 오류 [{config['stock_name']}]: {e}")
            return False

    def check_pyramiding_conditions(self, config, current_price, holding_amount):
        """
        피라미딩 조건 체크
        """
        try:
            stock_code = config["stock_code"]
            stock_name = config["stock_name"]
            trading_mode = config.get("trading_mode", "manual")
            pyramiding_entries = config.get("pyramiding_entries", [])
            pyramiding_count = config.get("pyramiding_count", 0)

            if pyramiding_count <= 0 or not pyramiding_entries:
                print(f"[{stock_name}] 피라미딩 설정 없음")
                return False

            # 현재 매수 횟수 확인
            current_entry_count = self.get_entry_count(stock_code)

            # 이미 최대 피라미딩 횟수를 초과한 경우
            if current_entry_count > pyramiding_count:
                print(
                    f"[{stock_name}] 피라미딩 횟수 초과 ({current_entry_count} > {pyramiding_count})"
                )
                return False

            # 기준가 설정 (1차 진입시점)
            base_price = config.get("entry_point")
            if base_price is None:
                print(f"[{stock_name}] 기준가 설정 실패")
                return False

            # 다음 피라미딩 단계 확인
            next_entry_index = (
                current_entry_count  # 0부터 시작하므로 현재 카운트가 다음 인덱스
            )

            if next_entry_index >= len(pyramiding_entries):
                print(
                    f"[{stock_name}] 피라미딩 엔트리 설정 부족 ({next_entry_index} >= {len(pyramiding_entries)})"
                )
                return False

            entry_str = pyramiding_entries[next_entry_index].strip()
            if not entry_str:
                print(f"[{stock_name}] 피라미딩 엔트리 값 없음")
                return False

            if trading_mode == "manual":
                # % 기준 피라미딩
                try:
                    if entry_str.startswith("+"):
                        threshold_percent = float(entry_str[1:]) / 100
                    else:
                        threshold_percent = float(entry_str) / 100

                    # 기준가 대비 상승률 계산
                    price_change_percent = (current_price - base_price) / base_price

                    print(
                        f"[{stock_name}] 피라미딩 체크 - 기준가: {base_price:,.0f}원, 현재가: {current_price:,.0f}원"
                    )
                    print(
                        f"[{stock_name}] 상승률: {price_change_percent*100:.2f}%, 목표: {threshold_percent*100:.2f}%"
                    )

                    if price_change_percent >= threshold_percent:
                        print(
                            f"[{stock_name}] 피라미딩 조건 충족 - {next_entry_index + 1}차 매수"
                        )
                        return True
                    else:
                        print(f"[{stock_name}] 피라미딩 조건 불충족")
                        return False

                except ValueError:
                    print(f"[{stock_name}] 피라미딩 엔트리 값 오류: {entry_str}")
                    return False

            else:  # turtle 모드
                # ATR 기준 피라미딩
                atr = self.get_atr(stock_code)
                if atr is None:
                    print(f"[{stock_name}] ATR 계산 실패")
                    return False

                try:
                    atr_multiplier = float(entry_str)
                    threshold_price = base_price + (atr * atr_multiplier)

                    print(
                        f"[{stock_name}] ATR 피라미딩 체크 - 기준가: {base_price:,.0f}원, 현재가: {current_price:,.0f}원"
                    )
                    print(
                        f"[{stock_name}] ATR: {atr:.2f}, 목표가: {threshold_price:,.0f}원"
                    )

                    if current_price >= threshold_price:
                        print(
                            f"[{stock_name}] ATR 피라미딩 조건 충족 - {next_entry_index + 1}차 매수"
                        )
                        return True
                    else:
                        print(f"[{stock_name}] ATR 피라미딩 조건 불충족")
                        return False

                except ValueError:
                    print(f"[{stock_name}] ATR 피라미딩 엔트리 값 오류: {entry_str}")
                    return False

        except Exception as e:
            print(f"피라미딩 조건 체크 오류: {e}")
            return False

    def check_exit_conditions(self, config):
        """
        청산 조건 체크 (손절/익절)
        """
        try:
            stock_code = config["stock_code"]
            stock_name = config["stock_name"]
            trading_mode = config.get("trading_mode", "manual")
            stop_loss = config.get("stop_loss", 8.0)
            take_profit = config.get("take_profit", 24.0)

            # 보유 수량 확인
            my_stocks = KisKR.GetMyStockList()
            holding_amount = 0
            avg_price = 0

            for stock in my_stocks:
                if stock["StockCode"] == stock_code:
                    holding_amount = int(stock["StockAmt"])
                    avg_price = float(stock["StockAvgPrice"])
                    break

            if holding_amount <= 0:
                return False, None

            # 현재가 조회
            current_price = float(KisKR.GetCurrentPrice(stock_code))

            # 수익률 계산
            profit_percent = ((current_price - avg_price) / avg_price) * 100

            if trading_mode == "manual":
                # % 기준 손절/익절
                if profit_percent <= -stop_loss:
                    return True, "손절"
                elif profit_percent >= take_profit:
                    return True, "익절"
            else:  # turtle 모드
                # ATR 기준 손절/익절
                atr = self.get_atr(stock_code)
                if atr is not None:
                    stop_loss_price = avg_price - (atr * stop_loss)
                    take_profit_price = avg_price + (atr * take_profit)

                    if current_price <= stop_loss_price:
                        return True, "ATR 손절"
                    elif current_price >= take_profit_price:
                        return True, "ATR 익절"

            return False, None

        except Exception as e:
            print(f"청산 조건 체크 오류 [{config['stock_name']}]: {e}")
            return False, None

    def execute_buy_order(self, config, amount):
        """
        매수 주문 실행
        """
        try:
            stock_code = config["stock_code"]
            stock_name = config["stock_name"]
            current_price = float(KisKR.GetCurrentPrice(stock_code))

            # 매수 수량 계산 (원 -> 주)
            buy_quantity = int(amount / current_price)

            if buy_quantity <= 0:
                print(f"[{stock_name}] 매수 수량이 0입니다. 투자금액: {amount:,.0f}원")
                return False

            # 시장가 매수 주문
            result = KisKR.MakeBuyMarketOrder(stock_code, buy_quantity)

            if result:
                # 매수 이력 업데이트
                current_entry_count = self.get_entry_count(stock_code)
                entry_type = (
                    "initial"
                    if current_entry_count == 0
                    else f"pyramiding_{current_entry_count}"
                )

                self.update_trade_history(
                    stock_code, stock_name, current_price, buy_quantity, entry_type
                )

                # CSV 거래 로그 기록
                avg_price = self.get_average_price(stock_code)
                total_quantity = (
                    self.get_entry_count(stock_code) * buy_quantity
                )  # 간단 계산

                self.log_trade(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    action="BUY",
                    price=current_price,
                    quantity=buy_quantity,
                    amount=amount,
                    entry_type=entry_type,
                    reason=(
                        "신규진입" if entry_type == "initial" else f"{entry_type} 매수"
                    ),
                    avg_price=avg_price,
                    total_quantity=total_quantity,
                    config=config,
                )

                # 거래 요약 업데이트
                self.update_trading_summary(stock_code)

                # 텔레그램 알림 전송
                self.send_trade_alert(
                    action="BUY",
                    stock_code=stock_code,
                    stock_name=stock_name,
                    price=current_price,
                    quantity=buy_quantity,
                    amount=amount,
                    entry_type=entry_type,
                    reason=(
                        "신규진입" if entry_type == "initial" else f"{entry_type} 매수"
                    ),
                    avg_price=avg_price,
                    total_quantity=total_quantity,
                )

                print(
                    f"[{stock_name}] 매수 주문 성공 - 수량: {buy_quantity}주, 금액: {amount:,.0f}원"
                )
                return True
            else:
                # 매수 실패 알림
                self.send_error_alert(
                    error_type="매수 주문 실패",
                    stock_code=stock_code,
                    stock_name=stock_name,
                    error_message="시장가 매수 주문이 실패했습니다",
                )
                print(f"[{stock_name}] 매수 주문 실패")
                return False

        except Exception as e:
            # 매수 오류 알림
            self.send_error_alert(
                error_type="매수 주문 오류",
                stock_code=config.get("stock_code", ""),
                stock_name=config.get("stock_name", ""),
                error_message=str(e),
            )
            print(f"매수 주문 오류 [{config['stock_name']}]: {e}")
            return False

    def execute_sell_order(self, config, reason=""):
        """
        매도 주문 실행
        """
        try:
            stock_code = config["stock_code"]
            stock_name = config["stock_name"]

            # 보유 수량 확인
            my_stocks = KisKR.GetMyStockList()
            holding_amount = 0

            for stock in my_stocks:
                if stock["StockCode"] == stock_code:
                    holding_amount = int(stock["StockAmt"])
                    break

            if holding_amount <= 0:
                return False

            # 시장가 매도 주문
            result = KisKR.MakeSellMarketOrder(stock_code, holding_amount)

            if result:
                # 현재가 및 수익 계산
                current_price = float(KisKR.GetCurrentPrice(stock_code))
                sell_amount = current_price * holding_amount

                # 평균 매수가 조회
                avg_price = self.get_average_price(stock_code)

                # 수익 계산
                if avg_price:
                    profit_loss = sell_amount - (avg_price * holding_amount)
                    profit_loss_percent = (
                        profit_loss / (avg_price * holding_amount)
                    ) * 100
                else:
                    profit_loss = 0
                    profit_loss_percent = 0

                # CSV 거래 로그 기록
                self.log_trade(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    action="SELL",
                    price=current_price,
                    quantity=holding_amount,
                    amount=sell_amount,
                    entry_type="exit",
                    reason=reason,
                    avg_price=avg_price,
                    total_quantity=0,  # 전량 매도 후 0
                    profit_loss=profit_loss,
                    profit_loss_percent=profit_loss_percent,
                    config=config,
                )

                # 매수 이력 초기화 (전량 매도)
                if stock_code in self.trade_history:
                    del self.trade_history[stock_code]
                    self.save_trade_history()

                # 거래 요약 업데이트
                self.update_trading_summary(stock_code)

                # 보유기간 계산
                holding_days = None
                if (
                    stock_code in self.trade_history
                    and self.trade_history[stock_code]["entries"]
                ):
                    first_entry = self.trade_history[stock_code]["entries"][0]
                    first_time = datetime.fromisoformat(first_entry["timestamp"])
                    holding_days = (datetime.now() - first_time).total_seconds() / 86400

                # 텔레그램 알림 전송
                self.send_trade_alert(
                    action="SELL",
                    stock_code=stock_code,
                    stock_name=stock_name,
                    price=current_price,
                    quantity=holding_amount,
                    amount=sell_amount,
                    entry_type="exit",
                    reason=reason,
                    profit_loss=profit_loss,
                    profit_loss_percent=profit_loss_percent,
                    avg_price=avg_price,
                    total_quantity=0,
                    holding_days=holding_days,
                )

                print(
                    f"[{stock_name}] 매도 주문 성공 - 수량: {holding_amount}주, 사유: {reason}"
                )
                print(
                    f"[{stock_name}] 수익: {profit_loss:,.0f}원 ({profit_loss_percent:.2f}%)"
                )
                return True
            else:
                # 매도 실패 알림
                self.send_error_alert(
                    error_type="매도 주문 실패",
                    stock_code=stock_code,
                    stock_name=stock_name,
                    error_message="시장가 매도 주문이 실패했습니다",
                )
                print(f"[{stock_name}] 매도 주문 실패")
                return False

        except Exception as e:
            # 매도 오류 알림
            self.send_error_alert(
                error_type="매도 주문 오류",
                stock_code=config.get("stock_code", ""),
                stock_name=config.get("stock_name", ""),
                error_message=str(e),
            )
            print(f"매도 주문 오류 [{config['stock_name']}]: {e}")
            return False

    def run_trading_cycle(self):
        """
        1회 트레이딩 사이클 실행
        """
        try:
            print(f"\n[{datetime.now()}] === 트레이딩 사이클 시작 ===")

            # 장 시간 체크
            if not self.is_market_open():
                print("장 시간이 아닙니다. 종료합니다.")
                return

            # 잔고 확인
            balance = KisKR.GetBalance()
            print("--------------내 보유 잔고---------------------")
            pprint.pprint(balance)
            print("--------------------------------------------")
            ##########################################################
            print("--------------내 보유 주식---------------------")
            # 그리고 현재 이 계좌에서 보유한 주식 리스트를 가지고 옵니다!
            MyStockList = KisKR.GetMyStockList()
            pprint.pprint(MyStockList)
            print("--------------------------------------------")

            if balance is None or float(balance["TotalMoney"]) <= 0:
                print("잔고가 부족합니다. 매매를 중단합니다.")
                return

            # 각 설정에 대해 매매 로직 실행
            print("매매대상 종목 수:", len(self.trading_configs))
            for config in self.trading_configs:
                try:
                    stock_name = config["stock_name"]
                    print(f"\n[{stock_name}] 매매 체크 시작")

                    # 100ms 딜레이 추가
                    time.sleep(1)  # 500ms 딜레이

                    # 청산 조건 체크 (우선순위: 손절/익절)
                    should_exit, exit_reason = self.check_exit_conditions(config)
                    if should_exit:
                        self.execute_sell_order(config, exit_reason)
                        continue

                    # 진입 조건 체크
                    should_enter = self.check_entry_conditions(config)
                    if should_enter:
                        # 전체 포지션 크기 계산
                        position_amount = self.calculate_position_size(config)
                        if position_amount > 0:
                            # 현재 진입 차수에 해당하는 금액 계산
                            current_amount = self.get_current_entry_amount(
                                config, position_amount
                            )
                            if current_amount > 0:
                                # 현재 피라미딩 차수에 맞는 금액으로 매수
                                self.execute_buy_order(config, current_amount)
                            else:
                                print(
                                    f"[{config['stock_name']}] 피라미딩 한도 초과 또는 투자금액 부족"
                                )

                except Exception as e:
                    print(
                        f"개별 종목 처리 오류 [{config.get('stock_name', 'Unknown')}]: {e}"
                    )

            # 장 마감 시간(15:30)에 일일 결산 알림
            current_time = datetime.now().strftime("%H%M")
            if current_time == "1530":
                self.send_daily_summary()

            print(f"[{datetime.now()}] === 트레이딩 사이클 완료 ===\n")

        except Exception as e:
            # 시스템 오류 알림
            self.send_error_alert(
                error_type="트레이딩 사이클 오류",
                stock_code="SYSTEM",
                stock_name="시스템",
                error_message=str(e),
            )
            traceback.print_exc()
            print(f"트레이딩 사이클 오류: {e}")


def main():
    """메인 함수"""
    try:
        # 명령행 인수로 모드 설정
        mode = "VIRTUAL"  # 기본값
        if len(sys.argv) > 1:
            if sys.argv[1].upper() in ["REAL", "VIRTUAL"]:
                mode = sys.argv[1].upper()
            else:
                print("사용법: python autoTrading_Bot.py [REAL|VIRTUAL]")
                sys.exit(1)

        # 봇 초기화 및 실행
        bot = AutoTradingBot(mode)

        # 1회 실행 (crontab으로 1분마다 실행되므로)
        bot.run_trading_cycle()

    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
        try:
            # 종료 알림 (bot이 정의된 경우에만)
            if "bot" in locals():
                bot.send_telegram_message(
                    "⏹️ 자동매매 봇이 사용자에 의해 중단되었습니다."
                )
        except:
            pass
    except Exception as e:
        print(f"메인 함수 오류: {e}")
        try:
            # 오류 알림 (bot이 정의된 경우에만)
            if "bot" in locals():
                bot.send_error_alert("메인 함수 오류", "SYSTEM", "시스템", str(e))
        except:
            pass


if __name__ == "__main__":
    main()
