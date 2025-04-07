import numpy as np
import pandas as pd
from datetime import datetime

class DataAnalyzer:
    def __init__(self):
        pass
    
    def preprocess_candles(self, candles):
        """캔들 데이터 전처리"""
        df = pd.DataFrame(candles)
        df = df.sort_values(by='timestamp', ascending=True).reset_index(drop=True)
        df['datetime'] = pd.to_datetime(df['candle_date_time_kst'])
        return df
    
    def calculate_indicators(self, df):
        """기술적 지표 계산"""
        # 이동평균선 (MA)
        df['ma5'] = df['trade_price'].rolling(window=5).mean()
        df['ma10'] = df['trade_price'].rolling(window=10).mean()
        df['ma20'] = df['trade_price'].rolling(window=20).mean()
        df['ma60'] = df['trade_price'].rolling(window=60).mean()
        df['ma120'] = df['trade_price'].rolling(window=120).mean()
        
        # 볼린저 밴드 (Bollinger Bands)
        df['ma20_std'] = df['trade_price'].rolling(window=20).std()
        df['upper_band'] = df['ma20'] + (df['ma20_std'] * 2)
        df['lower_band'] = df['ma20'] - (df['ma20_std'] * 2)
        
        # 상대강도지수 (RSI)
        delta = df['trade_price'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        df['ema12'] = df['trade_price'].ewm(span=12, adjust=False).mean()
        df['ema26'] = df['trade_price'].ewm(span=26, adjust=False).mean()
        df['macd'] = df['ema12'] - df['ema26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    def analyze_trend(self, df):
        """추세 분석"""
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        trend = {
            'current_price': latest['trade_price'],
            'price_change': latest['trade_price'] - prev['trade_price'],
            'ma_trend': {
                'above_ma5': latest['trade_price'] > latest['ma5'],
                'above_ma20': latest['trade_price'] > latest['ma20'],
                'above_ma60': latest['trade_price'] > latest['ma60'],
                'ma5_above_ma20': latest['ma5'] > latest['ma20'],
                'ma20_above_ma60': latest['ma20'] > latest['ma60'],
            },
            'bb_position': (latest['trade_price'] - latest['lower_band']) / (latest['upper_band'] - latest['lower_band']),
            'rsi': latest['rsi'],
            'macd': {
                'macd': latest['macd'],
                'signal': latest['macd_signal'],
                'hist': latest['macd_hist'],
                'bullish_crossover': prev['macd'] < prev['macd_signal'] and latest['macd'] > latest['macd_signal'],
                'bearish_crossover': prev['macd'] > prev['macd_signal'] and latest['macd'] < latest['macd_signal'],
            },
            'candle_data': df  # 캔들 데이터 전체를 추가
        }
        
        return trend
    
    def calculate_volatility_target_price(self, df, k=0.5):
        """변동성 돌파 전략의 목표 매수가 계산"""
        if len(df) < 2:
            return None
        
        last_day = df.iloc[-2]  # 전일 데이터
        today_open = df.iloc[-1]['opening_price']  # 당일 시가
        
        # 목표가 = 당일 시가 + (전일 고가 - 전일 저가) * k
        target_price = today_open + (last_day['high_price'] - last_day['low_price']) * k
        
        return target_price
    
    def backtest_strategy(self, df, strategy, initial_capital=1000000):
        """전략 백테스팅"""
        # 백테스팅 결과 저장 데이터프레임
        results = pd.DataFrame(index=df.index)
        results['price'] = df['trade_price']
        results['signal'] = 'hold'  # 초기값은 모두 홀드
        
        # 포지션 및 자본금 추적
        position = False
        capital = initial_capital
        buy_price = 0
        buy_count = 0
        sell_count = 0
        total_profit = 0
        
        # 각 날짜/시간에 대해 신호 생성 및 포지션 추적
        for i in range(20, len(df)):  # 기술적 지표 계산에 필요한 데이터 확보를 위해 20개 이후부터 시작
            subset = df.iloc[:i+1]
            trend = self.analyze_trend(subset)
            
            current_price = df.iloc[i]['trade_price']
            
            if isinstance(strategy, str) and strategy == 'volatility_breakout':
                # 변동성 돌파 전략 구현
                if i > 0:  # 전일 데이터가 있어야 계산 가능
                    k = 0.5  # 기본 k값
                    yesterday = df.iloc[i-1]
                    today_open = df.iloc[i]['opening_price']
                    target_price = today_open + (yesterday['high_price'] - yesterday['low_price']) * k
                    
                    # 당일 고가가 목표가 이상이면 매수 신호
                    if df.iloc[i]['high_price'] >= target_price and not position:
                        results.iloc[i, results.columns.get_loc('signal')] = 'buy'
                        position = True
                        buy_price = target_price
                        buy_count += 1
                    
                    # 다음날 시가에 매도
                    elif position and i < len(df) - 1:
                        next_day_open = df.iloc[i+1]['opening_price'] if i+1 < len(df) else current_price
                        results.iloc[i, results.columns.get_loc('signal')] = 'sell'
                        position = False
                        profit = (next_day_open - buy_price) / buy_price
                        total_profit += profit
                        sell_count += 1
            else:
                # 일반 전략의 경우 (MA, RSI, MACD 등)
                signal = strategy.generate_signal(trend, current_price)
                
                if signal == 'buy' and not position:
                    results.iloc[i, results.columns.get_loc('signal')] = 'buy'
                    position = True
                    buy_price = current_price
                    buy_count += 1
                
                elif signal == 'sell' and position:
                    results.iloc[i, results.columns.get_loc('signal')] = 'sell'
                    position = False
                    profit = (current_price - buy_price) / buy_price
                    total_profit += profit
                    sell_count += 1
        
        # 마지막 거래 이후 포지션이 남아있는 경우 청산 (마지막 가격으로)
        if position:
            last_price = df.iloc[-1]['trade_price']
            profit = (last_price - buy_price) / buy_price
            total_profit += profit
            sell_count += 1
        
        # 최종 수익률 계산
        final_capital = capital * (1 + total_profit)
        total_return = (final_capital - initial_capital) / initial_capital * 100
        
        stats = {
            'initial_capital': initial_capital,
            'final_capital': final_capital,
            'total_return': total_return,
            'buy_count': buy_count,
            'sell_count': sell_count,
            'win_rate': None  # 승률 계산은 좀 더 복잡한 로직이 필요
        }
        
        return results, stats