import numpy as np
import pandas as pd
from datetime import datetime, time

class MACrossStrategy:
    """이동평균선 교차 전략"""
    
    def __init__(self, short_window=5, long_window=20):
        self.short_window = short_window
        self.long_window = long_window
        self.position = None
    
    def generate_signal(self, trend):
        signal = 'hold'
        
        # 단기 이동평균이 장기 이동평균을 상향돌파 (골든 크로스)
        if (not trend['ma_trend']['ma5_above_ma20'] and 
            trend['ma_trend']['above_ma5'] and 
            trend['ma_trend']['above_ma20']):
            signal = 'buy'
        
        # 단기 이동평균이 장기 이동평균을 하향돌파 (데드 크로스)
        elif (trend['ma_trend']['ma5_above_ma20'] and 
              not trend['ma_trend']['above_ma5'] and 
              not trend['ma_trend']['above_ma20']):
            signal = 'sell'
        
        return signal


class RSIStrategy:
    """RSI 전략"""
    
    def __init__(self, oversold=30, overbought=70):
        self.oversold = oversold
        self.overbought = overbought
        self.position = None
    
    def generate_signal(self, trend):
        signal = 'hold'
        
        # 과매도 구간에서 매수
        if trend['rsi'] < self.oversold:
            signal = 'buy'
        
        # 과매수 구간에서 매도
        elif trend['rsi'] > self.overbought:
            signal = 'sell'
        
        return signal


class MACDStrategy:
    """MACD 전략"""
    
    def __init__(self):
        self.position = None
    
    def generate_signal(self, trend):
        signal = 'hold'
        
        # MACD 선이 시그널 선을 상향돌파 (골든 크로스)
        if trend['macd']['bullish_crossover']:
            signal = 'buy'
        
        # MACD 선이 시그널 선을 하향돌파 (데드 크로스)
        elif trend['macd']['bearish_crossover']:
            signal = 'sell'
        
        return signal


class BollingerBandStrategy:
    """볼린저 밴드 전략"""
    
    def __init__(self):
        self.position = None
    
    def generate_signal(self, trend):
        signal = 'hold'
        
        # 가격이 하단 밴드에 접근하면 매수
        if trend['bb_position'] < 0.05:
            signal = 'buy'
        
        # 가격이 상단 밴드에 접근하면 매도
        elif trend['bb_position'] > 0.95:
            signal = 'sell'
        
        return signal


class VolatilityBreakoutStrategy:
    """변동성 돌파 전략"""
    
    def __init__(self, k=0.5):
        self.k = k
        self.position = None
        self.target_price = None
        self.buy_time = None
        
    def set_target_price(self, df):
        """목표 매수가격을 설정"""
        # 전일 고가와 저가의 변동폭 계산
        previous = df.iloc[-2]
        today_open = df.iloc[-1]['opening_price']
        # 매수 목표가 = 당일 시가 + (전일 고가 - 전일 저가) * k
        target = today_open + (previous['high_price'] - previous['low_price']) * self.k
        self.target_price = target
        return target
    
    def generate_signal(self, trend, current_price, current_time=None):
        signal = 'hold'
        
        if current_time is None:
            current_time = datetime.now().time()
        
        # 9:00~09:05에는 매도 신호 (일봉 기준 리셋 시간)
        if time(9, 0) <= current_time <= time(9, 5):
            signal = 'sell'
            self.target_price = None
            return signal
        
        # 목표가가 설정되지 않았다면 설정
        if self.target_price is None and trend.get('candle_data') is not None:
            self.set_target_price(trend['candle_data'])
        
        # 현재가가 목표가 이상이면 매수 신호
        if self.target_price is not None and current_price >= self.target_price:
            signal = 'buy'
        
        return signal


class PercentageStrategy:
    """퍼센트 기반 매매 전략"""
    
    def __init__(self, buy_pct=0.20, sell_pct=0.05, k=0.5):
        self.buy_pct = buy_pct  # 매수 추가 시점 (평균 매수가 대비 -20%)
        self.sell_pct = sell_pct  # 매도 시점 (평균 매수가 대비 +5%)
        self.k = k
        self.vb_strategy = VolatilityBreakoutStrategy(k=k)
        self.position = None
    
    def generate_signal(self, trend, current_price, avg_buy_price=None, current_time=None):
        # 기본 변동성 돌파 전략 신호
        vb_signal = self.vb_strategy.generate_signal(trend, current_price, current_time)
        
        # 보유 중이 아닐 때 (매수 판단)
        if avg_buy_price is None or avg_buy_price == 0:
            return vb_signal
        
        # 이미 보유 중일 때 (추가 매수 또는 매도 판단)
        price_change_pct = (current_price - avg_buy_price) / avg_buy_price
        
        # 수익률이 sell_pct 이상이면 매도
        if price_change_pct >= self.sell_pct:
            return 'sell'
        
        # 손실률이 buy_pct 이상이면 추가 매수
        if price_change_pct <= -self.buy_pct and vb_signal != 'sell':
            return 'buy'
        
        return vb_signal


class CombinedStrategy:
    """복합 전략"""
    
    def __init__(self):
        self.ma_strategy = MACrossStrategy()
        self.rsi_strategy = RSIStrategy()
        self.macd_strategy = MACDStrategy()
        self.bb_strategy = BollingerBandStrategy()
        self.vb_strategy = VolatilityBreakoutStrategy()
        self.position = None
    
    def generate_signal(self, trend, current_price=None, avg_buy_price=None, current_time=None):
        if current_price is None:
            current_price = trend['current_price']
        
        ma_signal = self.ma_strategy.generate_signal(trend)
        rsi_signal = self.rsi_strategy.generate_signal(trend)
        macd_signal = self.macd_strategy.generate_signal(trend)
        bb_signal = self.bb_strategy.generate_signal(trend)
        vb_signal = self.vb_strategy.generate_signal(trend, current_price, current_time)
        
        buy_count = sum(1 for signal in [ma_signal, rsi_signal, macd_signal, bb_signal, vb_signal] if signal == 'buy')
        sell_count = sum(1 for signal in [ma_signal, rsi_signal, macd_signal, bb_signal, vb_signal] if signal == 'sell')
        
        # 복합 신호 생성 (투표 방식)
        if buy_count >= 3 and buy_count > sell_count:
            return 'buy'
        elif sell_count >= 3 and sell_count > buy_count:
            return 'sell'
        else:
            return 'hold'


# 최적의 k값과 코인을 찾는 함수
def find_best_k_and_coin(api, coins, days=7, k_range=None):
    """
    여러 코인과 k값에 대해 백테스팅하여 최적의 조합을 찾음
    
    Args:
        api: UpbitAPI 객체
        coins: 분석할 코인 목록 (예: ['KRW-BTC', 'KRW-ETH', ...])
        days: 분석할 기간 (일)
        k_range: 테스트할 k값 범위 (예: [0.1, 0.2, ..., 0.9])
    
    Returns:
        best_coin: 최적의 코인
        best_k: 최적의 k값
        best_profit: 최대 수익률
    """
    if k_range is None:
        k_range = [round(0.1 * i, 1) for i in range(5, 10)]  # 0.5 ~ 0.9
    
    best_profit = -float('inf')
    best_coin = None
    best_k = None
    
    for coin in coins:
        # 일봉 데이터 가져오기
        candles = api.get_day_candles(coin, count=days+1)
        
        for k in k_range:
            profit = 0
            strategy = VolatilityBreakoutStrategy(k=k)
            
            for i in range(1, len(candles)):
                yesterday = candles[i]
                today = candles[i-1]
                
                # 시가 기준 변동성 돌파 전략
                open_price = today['opening_price']
                high_price = today['high_price']
                
                # 목표가 계산
                target_price = open_price + (yesterday['high_price'] - yesterday['low_price']) * k
                
                # 목표가에 도달했는지 확인
                if high_price >= target_price:
                    # 매수 후 종가에 매도했을 때의 수익률
                    profit += (today['trade_price'] - target_price) / target_price
            
            if profit > best_profit:
                best_profit = profit
                best_coin = coin
                best_k = k
    
    return best_coin, best_k, best_profit