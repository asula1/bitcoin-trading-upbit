#!/usr/bin/env python3
import os
import logging
import sys
import configparser
import time
from datetime import datetime

from src.upbit_api import UpbitAPI

# 로거 설정
def setup_logger():
    logger = logging.getLogger("test_sell")
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
    
    # API 키 가져오기
    access_key = config['API']['access_key']
    secret_key = config['API']['secret_key']
    
    if access_key == 'YOUR_UPBIT_ACCESS_KEY_HERE' or secret_key == 'YOUR_UPBIT_SECRET_KEY_HERE':
        logger.error("config.ini 파일에 Upbit API 키를 설정해야 합니다!")
        sys.exit(1)
    
    # API 객체 생성
    api = UpbitAPI(access_key, secret_key)
    
    # 계좌 조회
    logger.info("계좌 정보 조회 중...")
    accounts = api.get_accounts()
    
    # BTC 보유량 확인
    btc_balance = 0
    btc_avg_price = 0
    
    for account in accounts:
        if account['currency'] == 'BTC':
            btc_balance = float(account['balance'])
            btc_avg_price = float(account['avg_buy_price']) if account['avg_buy_price'] else 0
            logger.info(f"BTC 보유량: {btc_balance} (평균 매수가: {btc_avg_price:,.0f}원)")
            break
    
    if btc_balance <= 0:
        logger.error("매도할 BTC가 없습니다.")
        sys.exit(1)
    
    try:
        # 현재가 확인
        ticker = api.get_ticker("KRW-BTC")
        current_price = ticker[0]['trade_price'] if ticker else 0
        logger.info(f"BTC 현재가: {current_price:,.0f}원")
        
        # 손익률 계산
        profit_loss = ((current_price / btc_avg_price) - 1) * 100 if btc_avg_price > 0 else 0
        logger.info(f"예상 손익률: {profit_loss:.2f}%")
        
        # 자동 실행 모드
        logger.info(f"BTC {btc_balance}개를 시장가로 매도합니다.")
        
        # 테스트 매도 실행
        logger.info(f"매도 실행: {btc_balance} BTC")
        sell_result = api.sell_market_order("KRW-BTC", btc_balance)
        
        if 'error' in sell_result:
            logger.error(f"매도 실패: {sell_result}")
            sys.exit(1)
        
        logger.info(f"매도 주문 성공: {sell_result}")
        
        # 매도 후 계좌 정보 확인
        logger.info("매도 주문 처리 중... (3초 대기)")
        time.sleep(3)
        
        accounts_after_sell = api.get_accounts()
        for account in accounts_after_sell:
            if account['currency'] == 'KRW':
                krw_after = float(account['balance'])
                logger.info(f"최종 KRW 잔고: {krw_after:,.0f}원")
                break
    
    except Exception as e:
        logger.error(f"거래 중 오류 발생: {e}")
        logger.error("상세 오류: ", exc_info=True)
        sys.exit(1)
    
    logger.info("테스트 완료!")

if __name__ == "__main__":
    main()