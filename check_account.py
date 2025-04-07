#!/usr/bin/env python3
import os
import logging
import sys
import configparser
from datetime import datetime

from src.upbit_api import UpbitAPI

# 로거 설정
def setup_logger():
    logger = logging.getLogger("check_account")
    logger.setLevel(logging.INFO)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 포맷 설정
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(console_handler)
    
    return logger

def main():
    logger = setup_logger()
    
    # 설정 파일 로드
    config = configparser.ConfigParser()
    config.read('config/config.ini')
    
    # 환경 변수에서 API 키 확인
    access_key = os.environ.get('UPBIT_ACCESS_KEY') or config['API']['access_key']
    secret_key = os.environ.get('UPBIT_SECRET_KEY') or config['API']['secret_key']
    
    if access_key == 'YOUR_UPBIT_ACCESS_KEY_HERE' or secret_key == 'YOUR_UPBIT_SECRET_KEY_HERE':
        logger.error("Upbit API 키가 설정되어 있지 않습니다. 환경 변수 또는 config.ini 파일에 설정해야 합니다!")
        sys.exit(1)
    
    # API 객체 생성
    api = UpbitAPI(access_key, secret_key)
    
    # 계좌 조회
    logger.info("계좌 정보 조회 중...")
    accounts = api.get_accounts()
    
    logger.info("=== 계좌 정보 ===")
    for account in accounts:
        currency = account['currency']
        balance = float(account['balance'])
        locked = float(account['locked'])
        avg_buy_price = float(account['avg_buy_price']) if account['avg_buy_price'] else 0
        
        if currency == 'KRW':
            logger.info(f"KRW 잔고: {balance:,.0f}원 (잠금: {locked:,.0f}원)")
        else:
            # 현재가 조회
            ticker = api.get_ticker(f"KRW-{currency}")
            current_price = ticker[0]['trade_price'] if ticker else 0
            
            # 원화 가치 계산
            krw_value = balance * current_price
            profit_loss = ((current_price / avg_buy_price) - 1) * 100 if avg_buy_price > 0 else 0
            
            logger.info(f"{currency}: {balance} 개 ({krw_value:,.0f}원)")
            logger.info(f"  - 평균 매수가: {avg_buy_price:,.0f}원")
            logger.info(f"  - 현재가: {current_price:,.0f}원")
            logger.info(f"  - 손익률: {profit_loss:.2f}%")
    
    # BTC 시장 정보 조회
    logger.info("\n=== 시장 정보 ===")
    ticker = api.get_ticker("KRW-BTC")
    if ticker:
        logger.info(f"BTC 현재가: {ticker[0]['trade_price']:,.0f}원")
        logger.info(f"24시간 변동률: {ticker[0]['signed_change_rate']*100:.2f}%")
        logger.info(f"24시간 거래량: {ticker[0]['acc_trade_volume_24h']:.4f} BTC")
        logger.info(f"24시간 거래대금: {ticker[0]['acc_trade_price_24h']:,.0f}원")

if __name__ == "__main__":
    main()