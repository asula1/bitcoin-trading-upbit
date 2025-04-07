#!/usr/bin/env python3
import os
import logging
import sys
import configparser
from datetime import datetime

from src.upbit_api import UpbitAPI

# 로거 설정
def setup_logger():
    logger = logging.getLogger("test_trade")
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
    logger.info(f"계좌 정보: {accounts}")
    
    # KRW 잔고 확인
    krw_balance = 0
    for account in accounts:
        if account['currency'] == 'KRW':
            krw_balance = float(account['balance'])
            logger.info(f"KRW 잔고: {krw_balance:,.0f}원")
            break
    
    # 시장 정보 조회
    logger.info("BTC 시장 정보 조회 중...")
    ticker = api.get_ticker("KRW-BTC")
    if ticker:
        current_price = ticker[0]['trade_price']
        logger.info(f"BTC 현재가: {current_price:,.0f}원")
    
    # 최소 구매 금액 (1,000원)으로 테스트
    test_amount = 10000
    
    # 구매 가능 여부 확인
    if krw_balance < test_amount:
        logger.error(f"테스트 매수 불가: 잔고 부족 (필요금액: {test_amount:,.0f}원, 현재잔고: {krw_balance:,.0f}원)")
        sys.exit(1)
    
    try:
        # 테스트 매수 실행
        logger.info(f"테스트 매수 실행: {test_amount:,.0f}원")
        buy_result = api.buy_market_order("KRW-BTC", test_amount)
        
        if 'error' in buy_result:
            logger.error(f"매수 실패: {buy_result}")
            sys.exit(1)
        
        logger.info(f"매수 성공: {buy_result}")
        
        # 매수 후 계좌 정보 확인 (API 지연을 고려하여 약간의 대기 시간 추가)
        import time
        logger.info("매수 주문 처리 중... (3초 대기)")
        time.sleep(3)
        
        accounts_after_buy = api.get_accounts()
        
        # BTC 보유량 확인
        btc_balance = 0
        for account in accounts_after_buy:
            if account['currency'] == 'BTC':
                btc_balance = float(account['balance'])
                btc_avg_price = float(account['avg_buy_price'])
                logger.info(f"BTC 보유량: {btc_balance} (평균 매수가: {btc_avg_price:,.0f}원)")
                break
                
        # BTC 잔고가 0인 경우, 주문 상태 확인
        if btc_balance == 0:
            logger.warning("BTC 잔고가 0입니다. 주문 상태를 확인합니다.")
            if 'uuid' in buy_result:
                order_info = api.get_order(buy_result['uuid'])
                logger.info(f"주문 상태: {order_info}")
                
                # 체결 대기 중인 경우 주문 취소
                if order_info.get('state') == 'wait':
                    logger.warning("주문이 아직 체결되지 않았습니다. 주문을 취소합니다.")
                    # 주문 취소 코드 필요
                    sys.exit(0)
        
        # 테스트 매도 실행
        if btc_balance > 0:
            logger.info(f"테스트 매도 실행: {btc_balance} BTC")
            sell_result = api.sell_market_order("KRW-BTC", btc_balance)
            
            if 'error' in sell_result:
                logger.error(f"매도 실패: {sell_result}")
                sys.exit(1)
            
            logger.info(f"매도 성공: {sell_result}")
            
            # 매도 후 계좌 정보 확인
            accounts_after_sell = api.get_accounts()
            for account in accounts_after_sell:
                if account['currency'] == 'KRW':
                    krw_after = float(account['balance'])
                    logger.info(f"최종 KRW 잔고: {krw_after:,.0f}원")
                    break
    except Exception as e:
        logger.error(f"거래 중 오류 발생: {str(e)}")
        logger.error(f"상세 오류: ", exc_info=True)
        sys.exit(1)
    
    logger.info("테스트 완료!")

if __name__ == "__main__":
    main()