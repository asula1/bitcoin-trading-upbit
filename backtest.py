import os
import sys
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import configparser

from src.upbit_api import UpbitAPI
from src.data_analyzer import DataAnalyzer
from src.trading_strategies import (
    MACrossStrategy, RSIStrategy, MACDStrategy, BollingerBandStrategy,
    VolatilityBreakoutStrategy, PercentageStrategy, CombinedStrategy,
    find_best_k_and_coin
)

def parse_args():
    """명령행 인자 파싱"""
    parser = argparse.ArgumentParser(description="Bitcoin Trading Strategy Backtesting")
    parser.add_argument("--config", type=str, default="config/config.ini", help="설정 파일 경로")
    parser.add_argument("--market", type=str, default="KRW-BTC", help="분석할 마켓 (예: KRW-BTC)")
    parser.add_argument("--strategy", type=str, choices=["ma", "rsi", "macd", "bb", "volatility", "percentage", "combined"], 
                       default="combined", help="백테스팅할 전략")
    parser.add_argument("--days", type=int, default=30, help="분석 기간 (일)")
    parser.add_argument("--initial-capital", type=int, default=1000000, help="초기 자본금 (원)")
    parser.add_argument("--find-best", action="store_true", help="최적의 코인과 K값 찾기")
    parser.add_argument("--k", type=float, default=0.5, help="변동성 돌파 전략의 K값 (0.1~0.9)")
    parser.add_argument("--compare-all", action="store_true", help="모든 전략 비교")
    
    return parser.parse_args()

def load_config(config_path):
    """설정 파일 로드"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    
    config = configparser.ConfigParser()
    config.read(config_path)
    
    return config

def get_strategy(strategy_name, k=0.5):
    """전략 객체 생성"""
    if strategy_name == "ma":
        return MACrossStrategy()
    elif strategy_name == "rsi":
        return RSIStrategy()
    elif strategy_name == "macd":
        return MACDStrategy()
    elif strategy_name == "bb":
        return BollingerBandStrategy()
    elif strategy_name == "volatility":
        return VolatilityBreakoutStrategy(k=k)
    elif strategy_name == "percentage":
        return PercentageStrategy(k=k)
    elif strategy_name == "combined":
        return CombinedStrategy()
    else:
        return "volatility_breakout"  # 문자열 반환 (내장 백테스트 로직 사용)

def plot_backtest_results(df, results, stats, strategy_name):
    """백테스팅 결과 시각화"""
    # 결과 및 원본 데이터 합치기
    plot_df = pd.DataFrame(index=results.index)
    plot_df['price'] = df['trade_price']
    plot_df['signal'] = results['signal']
    
    # 매수/매도 시점 식별
    plot_df['buy_price'] = None
    plot_df['sell_price'] = None
    
    for i in range(len(plot_df)):
        if plot_df['signal'].iloc[i] == 'buy':
            plot_df['buy_price'].iloc[i] = plot_df['price'].iloc[i]
        elif plot_df['signal'].iloc[i] == 'sell':
            plot_df['sell_price'].iloc[i] = plot_df['price'].iloc[i]
    
    # 플롯 생성
    plt.figure(figsize=(14, 8))
    
    # 가격 차트
    plt.subplot(2, 1, 1)
    plt.plot(plot_df.index, plot_df['price'], label='Price', color='blue', alpha=0.7)
    plt.scatter(plot_df.index, plot_df['buy_price'], color='green', marker='^', label='Buy Signal')
    plt.scatter(plot_df.index, plot_df['sell_price'], color='red', marker='v', label='Sell Signal')
    
    plt.title(f'{strategy_name} Strategy Backtest Results')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 수익 차트
    plt.subplot(2, 1, 2)
    cumulative_returns = (1 + stats['total_return']/100) ** np.linspace(0, 1, len(plot_df))
    plt.plot(plot_df.index, cumulative_returns, label=f'Strategy Return: {stats["total_return"]:.2f}%', color='green')
    
    plt.ylabel('Cumulative Return')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 통계 정보 출력
    print("\n===== 백테스트 결과 =====")
    print(f"전략: {strategy_name}")
    print(f"초기 자본: {stats['initial_capital']:,.0f}원")
    print(f"최종 자본: {stats['final_capital']:,.0f}원")
    print(f"총 수익률: {stats['total_return']:.2f}%")
    print(f"매수 횟수: {stats['buy_count']}")
    print(f"매도 횟수: {stats['sell_count']}")
    print("========================\n")
    
    plt.savefig(f'backtest_{strategy_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    plt.show()

def compare_strategies(df, initial_capital=1000000, k=0.5):
    """여러 전략 백테스팅 및 비교"""
    analyzer = DataAnalyzer()
    strategies = {
        "MA Cross": MACrossStrategy(),
        "RSI": RSIStrategy(),
        "MACD": MACDStrategy(),
        "Bollinger Bands": BollingerBandStrategy(),
        "Volatility Breakout": VolatilityBreakoutStrategy(k=k),
        "Percentage": PercentageStrategy(k=k),
        "Combined": CombinedStrategy()
    }
    
    results = {}
    
    for name, strategy in strategies.items():
        backtest_results, stats = analyzer.backtest_strategy(df, strategy, initial_capital)
        results[name] = {
            'return': stats['total_return'],
            'trades': stats['buy_count'],
            'final_capital': stats['final_capital']
        }
    
    # 결과 데이터프레임 생성
    results_df = pd.DataFrame.from_dict(results, orient='index')
    results_df = results_df.sort_values('return', ascending=False)
    
    # 수익률 비교 시각화
    plt.figure(figsize=(12, 6))
    sns.barplot(x=results_df.index, y='return', data=results_df)
    plt.title('Strategy Performance Comparison')
    plt.ylabel('Return (%)')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 거래 횟수 비교 시각화
    plt.figure(figsize=(12, 6))
    sns.barplot(x=results_df.index, y='trades', data=results_df)
    plt.title('Number of Trades by Strategy')
    plt.ylabel('Trades')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 결과 출력
    print("\n===== 전략 비교 결과 =====")
    print(results_df)
    print("========================\n")
    
    # 최적의 전략 출력
    best_strategy = results_df.index[0]
    print(f"최적의 전략: {best_strategy} (수익률: {results_df.loc[best_strategy, 'return']:.2f}%)")
    
    plt.savefig(f'strategy_comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    plt.show()
    
    return results_df

def main():
    """메인 함수"""
    args = parse_args()
    
    try:
        # 설정 파일 로드
        config = load_config(args.config)
        
        # API 키 확인
        access_key = config['API']['access_key']
        secret_key = config['API']['secret_key']
        
        if access_key == 'YOUR_UPBIT_ACCESS_KEY_HERE' or secret_key == 'YOUR_UPBIT_SECRET_KEY_HERE':
            print("config.ini 파일에 Upbit API 키를 설정해야 합니다!")
            sys.exit(1)
        
        # API 객체 생성
        api = UpbitAPI(access_key, secret_key)
        analyzer = DataAnalyzer()
        
        # 최적의 코인 및 K값 찾기
        if args.find_best:
            print("최적의 코인 및 K값 찾는 중...")
            # 주요 코인 목록
            coins = [
                "KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-BCH", "KRW-EOS", 
                "KRW-TRX", "KRW-ADA", "KRW-LTC", "KRW-LINK", "KRW-DOT"
            ]
            best_coin, best_k, best_profit = find_best_k_and_coin(api, coins, days=args.days)
            print(f"최적의 코인: {best_coin}, K값: {best_k}, 수익률: {best_profit:.2f}")
            
            # 최적의 코인으로 설정
            args.market = best_coin
            args.k = best_k
        
        # 데이터 가져오기
        print(f"{args.market} 데이터 가져오는 중...")
        if args.strategy == "volatility" or args.strategy == "percentage":
            # 일봉 데이터 가져오기 (변동성 돌파 전략용)
            candles = api.get_day_candles(args.market, count=args.days+1)
        else:
            # 15분 캔들 데이터 가져오기 (다른 전략용)
            candles = api.get_minute_candles(args.market, unit=15, count=min(args.days*24*4, 200))
        
        # 데이터 전처리
        df = analyzer.preprocess_candles(candles)
        
        # 지표 계산
        df = analyzer.calculate_indicators(df)
        
        # 모든 전략 비교
        if args.compare_all:
            compare_strategies(df, args.initial_capital, args.k)
            return
        
        # 전략 생성
        strategy = get_strategy(args.strategy, args.k)
        
        # 백테스팅
        print(f"{args.strategy} 전략 백테스팅 중...")
        results, stats = analyzer.backtest_strategy(df, strategy, args.initial_capital)
        
        # 결과 시각화
        plot_backtest_results(df, results, stats, args.strategy)
        
    except FileNotFoundError as e:
        print(str(e))
        sys.exit(1)
    
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()