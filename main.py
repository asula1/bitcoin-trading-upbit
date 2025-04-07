import os
import sys
import time
import configparser
import argparse
import logging
from logging.handlers import RotatingFileHandler

from src.upbit_api import UpbitAPI
from src.data_analyzer import DataAnalyzer
from src.trading_strategies import (
    MACrossStrategy, RSIStrategy, MACDStrategy, BollingerBandStrategy, 
    VolatilityBreakoutStrategy, PercentageStrategy, CombinedStrategy,
    find_best_k_and_coin
)
from src.trading_bot import TradingBot

def setup_logger(name):
    """로거 설정"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 로그 디렉토리 확인 및 생성
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 파일 핸들러
    file_handler = RotatingFileHandler('logs/main.log', maxBytes=10*1024*1024, backupCount=5)
    file_handler.setLevel(logging.INFO)
    
    # 포맷 설정
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def parse_args():
    """명령행 인자 파싱"""
    parser = argparse.ArgumentParser(description='Bitcoin Automated Trading Bot')
    parser.add_argument('--config', type=str, default='config/config.ini', help='설정 파일 경로')
    parser.add_argument('--market', type=str, help='거래 마켓 (예: KRW-BTC)')
    parser.add_argument('--interval', type=int, help='거래 간격 (초)')
    parser.add_argument('--strategy', type=str, 
                        choices=['ma', 'rsi', 'macd', 'bb', 'volatility', 'percentage', 'combined'], 
                        help='거래 전략 선택')
    parser.add_argument('--k', type=float, help='변동성 돌파 전략의 K값 (0.1~0.9)')
    parser.add_argument('--slack', type=str, help='슬랙 웹훅 URL')
    parser.add_argument('--find-best', action='store_true', help='최적의 코인과 K값 찾기')
    parser.add_argument('--backtest', action='store_true', help='백테스트 모드 (backtest.py 실행)')
    
    return parser.parse_args()

def load_config(config_path):
    """설정 파일 로드"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    
    config = configparser.ConfigParser()
    config.read(config_path)
    
    return config

def get_strategy_params(strategy_name, config, k=None):
    """전략 파라미터 준비"""
    params = {}
    
    if strategy_name == 'ma':
        params['short_window'] = config.getint('STRATEGY', 'short_ma', fallback=5)
        params['long_window'] = config.getint('STRATEGY', 'long_ma', fallback=20)
    
    elif strategy_name == 'rsi':
        params['oversold'] = config.getint('STRATEGY', 'rsi_oversold', fallback=30)
        params['overbought'] = config.getint('STRATEGY', 'rsi_overbought', fallback=70)
    
    elif strategy_name in ['volatility', 'percentage']:
        params['k'] = k or config.getfloat('STRATEGY', 'k', fallback=0.5)
        
        if strategy_name == 'percentage':
            params['buy_pct'] = config.getfloat('STRATEGY', 'buy_pct', fallback=0.20)
            params['sell_pct'] = config.getfloat('STRATEGY', 'sell_pct', fallback=0.05)
    
    # 매수 금액 비율 설정
    params['buy_amount_pct'] = config.getfloat('TRADING', 'buy_amount_pct', fallback=0.3)
    
    return params

def main():
    """메인 함수"""
    # 로거 설정
    logger = setup_logger('main')
    
    # 명령행 인자 파싱
    args = parse_args()
    
    try:
        # 설정 파일 로드
        config = load_config(args.config)
        
        # API 키 확인
        access_key = config['API']['access_key']
        secret_key = config['API']['secret_key']
        
        if access_key == 'YOUR_UPBIT_ACCESS_KEY_HERE' or secret_key == 'YOUR_UPBIT_SECRET_KEY_HERE':
            logger.error("config.ini 파일에 Upbit API 키를 설정해야 합니다!")
            sys.exit(1)
        
        # 슬랙 웹훅 URL
        slack_webhook_url = args.slack or config.get('NOTIFICATION', 'slack_webhook_url', fallback=None)
        
        # 백테스트 모드
        if args.backtest:
            logger.info("백테스트 모드 실행 중...")
            os.system(f"python backtest.py --config {args.config}")
            sys.exit(0)
        
        # API 객체 생성
        api = UpbitAPI(access_key, secret_key)
        
        # 최적의 코인 및 K값 찾기
        if args.find_best:
            logger.info("최적의 코인 및 K값 찾는 중...")
            # 주요 코인 목록
            coins = [
                "KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-BCH", "KRW-EOS", 
                "KRW-TRX", "KRW-ADA", "KRW-LTC", "KRW-LINK", "KRW-DOT"
            ]
            best_coin, best_k, best_profit = find_best_k_and_coin(api, coins)
            logger.info(f"최적의 코인: {best_coin}, K값: {best_k}, 수익률: {best_profit:.2f}")
            
            # 최적의 코인으로 설정
            market = best_coin
            k_value = best_k
        else:
            # 거래 설정
            market = args.market or config['TRADING']['market']
            k_value = args.k or config.getfloat('STRATEGY', 'k', fallback=0.5)
        
        # 거래 간격 및 전략
        interval = args.interval or config.getint('TRADING', 'interval')
        strategy_name = args.strategy or config['TRADING']['strategy']
        
        # 전략 파라미터 준비
        strategy_params = get_strategy_params(strategy_name, config, k_value)
        
        # GUI 대시보드 실행 (별도 프로세스)
        logger.info("GUI 대시보드 실행 중...")
        import subprocess
        import threading
        
        def run_dashboard():
            dashboard_process = subprocess.Popen(["streamlit", "run", "dashboard.py"], 
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE)
            logger.info("GUI 대시보드가 시작되었습니다.")
            # 5초 후 브라우저 열기
            time.sleep(5)
            import webbrowser
            webbrowser.open('http://localhost:8501')
        
        # 대시보드 스레드 시작
        dashboard_thread = threading.Thread(target=run_dashboard)
        dashboard_thread.daemon = True  # 메인 프로그램 종료시 같이 종료
        dashboard_thread.start()
        
        # 트레이딩 봇 생성 및 실행
        bot = TradingBot(
            access_key, secret_key, 
            market=market, 
            strategy=strategy_name,
            strategy_params=strategy_params,
            slack_webhook_url=slack_webhook_url
        )
        
        logger.info(f"비트코인 자동매매 봇 시작 - 마켓: {market}, 전략: {strategy_name}, 간격: {interval}초")
        
        # 실제 트레이딩 실행
        bot.run(interval=interval)
    
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("사용자에 의한 프로그램 종료")
    
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()