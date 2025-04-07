import time
import logging
import os
import json
import requests
from datetime import datetime, timedelta
import traceback

from src.upbit_api import UpbitAPI
from src.data_analyzer import DataAnalyzer
from src.trading_strategies import (
    MACrossStrategy, RSIStrategy, MACDStrategy, BollingerBandStrategy,
    VolatilityBreakoutStrategy, PercentageStrategy, CombinedStrategy
)

class TradingBot:
    def __init__(self, access_key, secret_key, market="KRW-BTC", strategy=None, 
                 strategy_params=None, slack_webhook_url=None):
        self.api = UpbitAPI(access_key, secret_key)
        self.market = market
        self.analyzer = DataAnalyzer()
        self.strategy_name = strategy if isinstance(strategy, str) else "combined"
        self.strategy_params = strategy_params or {}
        self.strategy = self._create_strategy()
        self.logger = self._setup_logger()
        self.position = self._get_current_position()
        self.slack_webhook_url = slack_webhook_url
        self.last_notification_time = None
        self.notification_cooldown = 3600  # 알림 발송 제한 시간 (초)
        
    def _setup_logger(self):
        logger = logging.getLogger("trading_bot")
        logger.setLevel(logging.INFO)
        
        # 로그 디렉토리 확인
        if not os.path.exists("logs"):
            os.makedirs("logs")
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 파일 핸들러
        today = datetime.now().strftime("%Y%m%d")
        file_handler = logging.FileHandler(f"logs/trading_{today}.log")
        file_handler.setLevel(logging.INFO)
        
        # 포맷 설정
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # 핸들러 추가
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def _create_strategy(self):
        """전략 객체 생성"""
        if self.strategy_name == "ma":
            short_window = self.strategy_params.get("short_window", 5)
            long_window = self.strategy_params.get("long_window", 20)
            return MACrossStrategy(short_window=short_window, long_window=long_window)
        
        elif self.strategy_name == "rsi":
            oversold = self.strategy_params.get("oversold", 30)
            overbought = self.strategy_params.get("overbought", 70)
            return RSIStrategy(oversold=oversold, overbought=overbought)
        
        elif self.strategy_name == "macd":
            return MACDStrategy()
        
        elif self.strategy_name == "bb":
            return BollingerBandStrategy()
        
        elif self.strategy_name == "volatility":
            k = self.strategy_params.get("k", 0.5)
            return VolatilityBreakoutStrategy(k=k)
        
        elif self.strategy_name == "percentage":
            k = self.strategy_params.get("k", 0.5)
            buy_pct = self.strategy_params.get("buy_pct", 0.20)
            sell_pct = self.strategy_params.get("sell_pct", 0.05)
            return PercentageStrategy(buy_pct=buy_pct, sell_pct=sell_pct, k=k)
        
        else:  # 기본값은 복합 전략
            return CombinedStrategy()
    
    def _get_current_position(self):
        """현재 포지션 확인"""
        accounts = self.api.get_accounts()
        
        position = {'has_position': False, 'volume': 0, 'avg_buy_price': 0}
        
        for account in accounts:
            if account['currency'] == self.market.split('-')[1]:
                if float(account['balance']) > 0:
                    position['has_position'] = True
                    position['volume'] = float(account['balance'])
                    position['avg_buy_price'] = float(account['avg_buy_price'])
                break
        
        return position
    
    def update_position(self):
        """포지션 업데이트"""
        self.position = self._get_current_position()
        self.logger.info(f"현재 포지션: {self.position}")
    
    def analyze_market(self):
        """시장 분석"""
        try:
            # 전략에 따라 다른 데이터 가져오기
            if isinstance(self.strategy, (VolatilityBreakoutStrategy, PercentageStrategy)):
                # 일봉 데이터 가져오기 (변동성 돌파 전략용)
                candles = self.api.get_day_candles(self.market, count=10)
            else:
                # 15분 캔들 데이터 가져오기 (다른 전략용)
                candles = self.api.get_minute_candles(self.market, unit=15, count=120)
            
            # 데이터 전처리
            df = self.analyzer.preprocess_candles(candles)
            
            # 지표 계산
            df = self.analyzer.calculate_indicators(df)
            
            # 추세 분석
            trend = self.analyzer.analyze_trend(df)
            
            self.logger.info(f"현재 가격: {trend['current_price']}, RSI: {trend['rsi']:.2f}, MACD: {trend['macd']['macd']:.2f}")
            
            return trend
        
        except Exception as e:
            self.logger.error(f"시장 분석 중 오류 발생: {e}")
            self.send_notification(f"🚨 시장 분석 오류: {e}")
            return None
    
    def send_notification(self, message):
        """슬랙으로 알림 전송"""
        if not self.slack_webhook_url:
            return
        
        # 알림 쿨다운 확인
        now = datetime.now()
        if (self.last_notification_time and 
            (now - self.last_notification_time).total_seconds() < self.notification_cooldown):
            return
        
        try:
            payload = {
                "text": message,
                "username": "TradingBot",
                "icon_emoji": ":chart_with_upwards_trend:"
            }
            
            response = requests.post(
                self.slack_webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                self.logger.error(f"슬랙 알림 전송 실패: {response.text}")
            else:
                self.last_notification_time = now
                
        except Exception as e:
            self.logger.error(f"슬랙 알림 전송 중 오류 발생: {e}")
    
    def execute_trade(self, signal, trend):
        """거래 실행"""
        current_price = trend['current_price']
        
        if signal == 'buy' and not self.position['has_position']:
            # 보유 현금 조회
            krw_account = None
            for account in self.api.get_accounts():
                if account['currency'] == 'KRW':
                    krw_account = account
                    break
            
            if not krw_account:
                error_msg = "KRW 계좌를 찾을 수 없습니다."
                self.logger.error(error_msg)
                self.send_notification(f"⚠️ {error_msg}")
                return
            
            krw_balance = float(krw_account['balance'])
            
            if krw_balance < 10000:  # 최소 주문 금액
                error_msg = f"매수에 필요한 KRW가 부족합니다: {krw_balance}"
                self.logger.warning(error_msg)
                self.send_notification(f"⚠️ {error_msg}")
                return
            
            # 매수 금액 설정 (가용 자산의 30%)
            buy_amount = self.strategy_params.get("buy_amount_pct", 0.3) * krw_balance
            
            # 시장가 매수 주문
            self.logger.info(f"매수 주문 실행: {buy_amount} KRW (가격: {current_price})")
            result = self.api.buy_market_order(self.market, buy_amount)
            
            if 'error' in result:
                error_msg = f"매수 주문 실패: {result['error']}"
                self.logger.error(error_msg)
                self.send_notification(f"🚨 {error_msg}")
                return
            
            self.logger.info(f"매수 주문 성공: {result}")
            self.send_notification(f"🟢 매수 체결: {self.market} - {buy_amount:,.0f}원 (가격: {current_price:,.0f}원)")
            time.sleep(2)  # API 요청 제한 방지
            self.update_position()
        
        elif signal == 'sell' and self.position['has_position']:
            # 시장가 매도 주문
            volume = self.position['volume']
            avg_buy_price = self.position['avg_buy_price']
            profit_pct = (current_price - avg_buy_price) / avg_buy_price * 100
            
            self.logger.info(f"매도 주문 실행: {volume} {self.market.split('-')[1]} (가격: {current_price}, 손익: {profit_pct:.2f}%)")
            result = self.api.sell_market_order(self.market, volume)
            
            if 'error' in result:
                error_msg = f"매도 주문 실패: {result['error']}"
                self.logger.error(error_msg)
                self.send_notification(f"🚨 {error_msg}")
                return
            
            self.logger.info(f"매도 주문 성공: {result}")
            
            # 수익/손실 이모지 설정
            emoji = "🔴" if profit_pct < 0 else "🟢"
            self.send_notification(f"{emoji} 매도 체결: {self.market} - {volume} 개 (가격: {current_price:,.0f}원, 손익: {profit_pct:.2f}%)")
            time.sleep(2)  # API 요청 제한 방지
            self.update_position()
    
    def run(self, interval=60):
        """봇 실행"""
        self.logger.info(f"Trading Bot 시작 - 마켓: {self.market}, 전략: {self.strategy_name}")
        self.send_notification(f"🤖 Trading Bot 시작 - 마켓: {self.market}, 전략: {self.strategy_name}")
        
        try:
            while True:
                # 시장 분석
                trend = self.analyze_market()
                
                if trend is None:
                    self.logger.warning("시장 데이터를 가져오는데 실패했습니다. 재시도 중...")
                    time.sleep(10)  # 짧은 대기 후 재시도
                    continue
                
                # 현재가 및 포지션 정보
                current_price = trend['current_price']
                avg_buy_price = self.position.get('avg_buy_price', 0)
                
                # 신호 생성
                if isinstance(self.strategy, (VolatilityBreakoutStrategy, PercentageStrategy)):
                    current_time = datetime.now().time()
                    signal = self.strategy.generate_signal(trend, current_price, avg_buy_price, current_time)
                else:
                    signal = self.strategy.generate_signal(trend)
                
                self.logger.info(f"생성된 신호: {signal}")
                
                # 거래 실행
                self.execute_trade(signal, trend)
                
                # 대기
                self.logger.info(f"{interval}초 대기 중...")
                time.sleep(interval)
        
        except KeyboardInterrupt:
            self.logger.info("사용자에 의한 프로그램 종료")
            self.send_notification("🛑 사용자에 의한 Trading Bot 종료")
        
        except Exception as e:
            error_msg = f"오류 발생: {e}"
            self.logger.error(error_msg, exc_info=True)
            self.send_notification(f"🚨 Trading Bot 오류: {error_msg}\n{traceback.format_exc()}")
            
        finally:
            self.logger.info("Trading Bot 종료")
            self.send_notification("🔄 Trading Bot 종료")