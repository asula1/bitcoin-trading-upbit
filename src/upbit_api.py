import os
import jwt
import uuid
import hashlib
import requests
import time
from urllib.parse import urlencode, unquote

class UpbitAPI:
    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key
        self.base_url = "https://api.upbit.com/v1"
    
    def _get_headers(self, query=None):
        if query:
            query_string = unquote(urlencode(query, doseq=True)).encode("utf-8")
            m = hashlib.sha512()
            m.update(query_string)
            query_hash = m.hexdigest()
            
            payload = {
                'access_key': self.access_key,
                'nonce': str(uuid.uuid4()),
                'query_hash': query_hash,
                'query_hash_alg': 'SHA512',
            }
        else:
            payload = {
                'access_key': self.access_key,
                'nonce': str(uuid.uuid4()),
            }
        
        jwt_token = jwt.encode(payload, self.secret_key)
        authorization = f"Bearer {jwt_token}"
        
        return {"Authorization": authorization}
    
    def get_accounts(self):
        """계좌 조회"""
        url = f"{self.base_url}/accounts"
        headers = self._get_headers()
        response = requests.get(url, headers=headers)
        return response.json()
    
    def get_ticker(self, markets):
        """현재가 조회"""
        url = f"{self.base_url}/ticker"
        params = {'markets': markets}
        response = requests.get(url, params=params)
        return response.json()
    
    def get_orderbook(self, markets):
        """호가 정보 조회"""
        url = f"{self.base_url}/orderbook"
        params = {'markets': markets}
        response = requests.get(url, params=params)
        return response.json()
    
    def get_minute_candles(self, market, unit=1, count=200):
        """분 캔들 조회"""
        url = f"{self.base_url}/candles/minutes/{unit}"
        params = {'market': market, 'count': count}
        response = requests.get(url, params=params)
        return response.json()
    
    def get_day_candles(self, market, count=200):
        """일 캔들 조회"""
        url = f"{self.base_url}/candles/days"
        params = {'market': market, 'count': count}
        response = requests.get(url, params=params)
        return response.json()
    
    def buy_market_order(self, market, price):
        """시장가 매수"""
        url = f"{self.base_url}/orders"
        query = {
            'market': market,
            'side': 'bid',
            'price': str(price),
            'ord_type': 'price',
        }
        headers = self._get_headers(query)
        response = requests.post(url, json=query, headers=headers)
        return response.json()
    
    def sell_market_order(self, market, volume):
        """시장가 매도"""
        url = f"{self.base_url}/orders"
        query = {
            'market': market,
            'side': 'ask',
            'volume': str(volume),
            'ord_type': 'market',
        }
        headers = self._get_headers(query)
        response = requests.post(url, json=query, headers=headers)
        return response.json()
    
    def get_order(self, uuid_value):
        """주문 조회"""
        url = f"{self.base_url}/order"
        query = {'uuid': uuid_value}
        headers = self._get_headers(query)
        response = requests.get(url, params=query, headers=headers)
        return response.json()