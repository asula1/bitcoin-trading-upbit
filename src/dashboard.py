import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import json
import datetime
import os
import configparser
from datetime import datetime, timedelta

from src.upbit_api import UpbitAPI
from src.data_analyzer import DataAnalyzer
from src.trading_strategies import MACrossStrategy, RSIStrategy, MACDStrategy, BollingerBandStrategy, CombinedStrategy
from src.trading_bot import TradingBot

# 설정 파일 로드
def load_config():
    config = configparser.ConfigParser()
    config.read('config/config.ini')
    return config

# 업비트 API 키 가져오기
def get_api_keys():
    # 환경변수에서 API 키 가져오기 (Docker 환경과 .env 파일을 위한 설정)
    access_key = os.environ.get('UPBIT_ACCESS_KEY') 
    secret_key = os.environ.get('UPBIT_SECRET_KEY')
    
    # 환경변수가 없으면 config.ini에서 가져오기
    if not access_key or not secret_key:
        config = load_config()
        access_key = config['API']['access_key']
        secret_key = config['API']['secret_key']
    
    return access_key, secret_key

# 계좌 정보 가져오기
def get_account_info():
    access_key, secret_key = get_api_keys()
    api = UpbitAPI(access_key, secret_key)
    
    # 계정 정보가 없으면 수동으로 최소 데이터 생성 (디버깅용)
    accounts = api.get_accounts()
    if not accounts or len(accounts) == 0:
        print("API에서 계정 정보를 가져오지 못했습니다. 테스트 데이터 사용")
        # 테스트 데이터 생성
        accounts = [
            {
                'currency': 'KRW',
                'balance': '99990.40248407',
                'locked': '0',
                'avg_buy_price': '0',
                'avg_buy_price_modified': True,
                'unit_currency': 'KRW'
            }
        ]
    
    # 로그를 출력하여 제대로 가져왔는지 확인
    print(f"계정 정보: {accounts}")
    return accounts

# 최근 거래 기록 가져오기 (로그 파일에서)
def get_recent_trades(limit=10):
    trades = []
    logs_dir = 'logs'
    
    if not os.path.exists(logs_dir):
        return []
    
    log_files = [f for f in os.listdir(logs_dir) if f.startswith('trading_') and f.endswith('.log')]
    log_files.sort(reverse=True)
    
    for log_file in log_files:
        try:
            with open(os.path.join(logs_dir, log_file), 'r') as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if '매수 주문 성공' in line or '매도 주문 성공' in line:
                        timestamp = line.split(' - ')[0]
                        action = '매수' if '매수 주문 성공' in line else '매도'
                        trades.append({'timestamp': timestamp, 'action': action, 'details': line.strip()})
                        if len(trades) >= limit:
                            return trades
        except Exception as e:
            continue
    
    return trades

# 캔들 데이터 가져오기
def get_candle_data(market='KRW-BTC', count=100):
    access_key, secret_key = get_api_keys()
    api = UpbitAPI(access_key, secret_key)
    analyzer = DataAnalyzer()
    
    # 15분 캔들 가져오기
    candles = api.get_minute_candles(market, unit=15, count=count)
    
    # 데이터 전처리
    df = analyzer.preprocess_candles(candles)
    
    # 지표 계산
    df = analyzer.calculate_indicators(df)
    
    return df

# 차트 그리기
def plot_candle_chart(df):
    # 서브플롯 생성 (캔들차트 + 볼륨 + 기술적 지표)
    fig = make_subplots(rows=3, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.03, 
                        row_heights=[0.6, 0.2, 0.2],
                        subplot_titles=("BTC/KRW", "Volume", "Technical Indicators"))
    
    # 캔들스틱 차트
    fig.add_trace(go.Candlestick(
        x=df['datetime'],
        open=df['opening_price'], 
        high=df['high_price'],
        low=df['low_price'], 
        close=df['trade_price'],
        name='Candles'
    ), row=1, col=1)
    
    # 이동평균선
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['ma5'], name='MA5', line=dict(color='blue', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['ma20'], name='MA20', line=dict(color='orange', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['ma60'], name='MA60', line=dict(color='purple', width=1)), row=1, col=1)
    
    # 볼린저 밴드
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['upper_band'], name='Upper BB', line=dict(color='rgba(250, 0, 0, 0.3)', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['lower_band'], name='Lower BB', line=dict(color='rgba(0, 250, 0, 0.3)', width=1)), row=1, col=1)
    
    # 거래량 차트
    colors = ['green' if row['opening_price'] < row['trade_price'] else 'red' for _, row in df.iterrows()]
    fig.add_trace(go.Bar(x=df['datetime'], y=df['candle_acc_trade_volume'], name='Volume', marker_color=colors), row=2, col=1)
    
    # RSI 차트
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['rsi'], name='RSI', line=dict(color='blue', width=1)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['datetime'], y=[70] * len(df), name='Overbought', line=dict(color='red', width=1, dash='dash')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['datetime'], y=[30] * len(df), name='Oversold', line=dict(color='green', width=1, dash='dash')), row=3, col=1)
    
    # 레이아웃 설정
    fig.update_layout(
        title='Bitcoin Price Chart (KRW)',
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False,
        height=800,
        width=1000,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Y축 타이틀 설정
    fig.update_yaxes(title_text="Price (KRW)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1)
    
    return fig

# 자산 현황 차트
def plot_assets_chart(accounts):
    labels = []
    values = []
    
    for account in accounts:
        currency = account['currency']
        balance = float(account['balance'])
        
        if currency == 'KRW':
            labels.append('KRW (원화)')
            values.append(balance)
        else:
            # 현재가 조회
            access_key, secret_key = get_api_keys()
            api = UpbitAPI(access_key, secret_key)
            ticker = api.get_ticker(f'KRW-{currency}')
            
            if ticker and len(ticker) > 0:
                current_price = ticker[0]['trade_price']
                krw_value = balance * current_price
                labels.append(f'{currency} ({balance:.8f})')
                values.append(krw_value)
    
    # 파이 차트
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
    fig.update_layout(title_text='Portfolio Distribution')
    
    return fig

# 메인 대시보드 앱
def main():
    st.set_page_config(page_title="Bitcoin Trading Bot Dashboard", layout="wide")
    
    # 디버그 정보 출력 제거
    
    # Docker 내에서 실행될 때 서버 주소 설정
    # 최신 Streamlit 버전에서는 직접 서버 주소 설정이 불가능하므로 제거
    # 대신 Docker 환경에서 실행 여부만 확인
    if os.path.exists("/.dockerenv"):
        st.write("Docker 환경에서 실행 중입니다.")
    
    # 사이드바
    st.sidebar.title("Bitcoin Trading Bot")
    
    # 계정 정보
    st.sidebar.header("💰 계정 정보")
    accounts = get_account_info()
    
    # 디버그 정보 완전히 제거
    
    total_krw = 0
    total_asset_value = 0
    
    if accounts and len(accounts) > 0:
        for account in accounts:
            currency = account['currency']
            balance = float(account['balance'])
            
            if currency == 'KRW':
                total_krw = balance
                total_asset_value += balance
                # 원화 잔액 강조 표시 (배경색 변경)
                st.sidebar.markdown(f"""
                <div style="background-color:#222222;padding:12px;border-radius:5px;margin-bottom:10px;border:1px solid #444444">
                    <h3 style="margin:0;font-size:16px;color:#CCCCCC">원화(KRW) 잔액</h3>
                    <p style="font-size:20px;font-weight:bold;color:#00FF9D;margin:8px 0">{balance:,.0f}원</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # 코인 정보 표시
                try:
                    # 현재가 조회
                    access_key, secret_key = get_api_keys()
                    api = UpbitAPI(access_key, secret_key)
                    ticker = api.get_ticker(f'KRW-{currency}')
                    
                    if ticker and len(ticker) > 0:
                        current_price = ticker[0]['trade_price']
                        avg_buy_price = float(account['avg_buy_price'])
                        krw_value = balance * current_price
                        profit_loss = (current_price - avg_buy_price) / avg_buy_price * 100
                        
                        total_asset_value += krw_value
                        
                        # 수익률에 따라 색상 결정
                        color = "#00FF9D" if profit_loss >= 0 else "#FF5252"
                        
                        st.sidebar.markdown(f"""
                        <div style="background-color:#222222;padding:12px;border-radius:5px;margin-bottom:10px;border:1px solid #444444">
                            <h3 style="margin:0;font-size:16px;color:#CCCCCC">{currency} 보유량</h3>
                            <p style="font-size:16px;margin:8px 0;color:#FFFFFF">{balance:.8f} {currency}</p>
                            <p style="font-size:16px;margin:8px 0;color:#DDDDDD">평가금액: {krw_value:,.0f}원</p>
                            <p style="font-size:16px;margin:8px 0;color:#DDDDDD">매수가: {avg_buy_price:,.0f}원</p>
                            <p style="font-size:16px;margin:8px 0;color:#DDDDDD">현재가: {current_price:,.0f}원</p>
                            <p style="font-size:16px;font-weight:bold;color:{color};margin:8px 0">수익률: {profit_loss:.2f}%</p>
                        </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    st.sidebar.error(f"코인 정보 조회 중 오류: {e}")
    else:
        st.sidebar.error("계정 정보를 가져올 수 없습니다. API 키를 확인하세요.")
    
    # 총 자산가치 강조 표시 (다크모드)
    st.sidebar.markdown(f"""
    <div style="background-color:#111111;padding:15px;border-radius:5px;margin:15px 0;border:1px solid #555555">
        <h3 style="margin:0;font-size:18px;color:#AAAAAA">총 자산가치</h3>
        <p style="font-size:24px;font-weight:bold;color:#00CCFF;margin:10px 0">{total_asset_value:,.0f}원</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 전략 설정
    st.sidebar.header("전략 설정")
    
    strategy_option = st.sidebar.selectbox(
        "거래 전략 선택",
        ["이동평균선 교차 (MA Cross)", "RSI", "MACD", "볼린저 밴드", "복합 전략 (Combined)"]
    )
    
    interval_option = st.sidebar.selectbox(
        "거래 간격",
        [("1분", 60), ("5분", 300), ("15분", 900), ("30분", 1800), ("1시간", 3600)],
        format_func=lambda x: x[0]
    )
    
    # 자동 거래 설정
    st.sidebar.header("자동 거래 설정")
    auto_trading = st.sidebar.checkbox("자동 거래 활성화", value=False)
    
    if auto_trading:
        st.sidebar.warning("⚠️ 자동 거래가 활성화되었습니다. 실제 거래가 발생할 수 있습니다.")
        
        if st.sidebar.button("자동 거래 중지"):
            auto_trading = False
    
    # 메인 콘텐츠
    st.title("Bitcoin Trading Bot Dashboard")
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["차트 분석", "거래 기록", "포트폴리오"])
    
    with tab1:
        # 차트 분석 탭
        st.header("BTC/KRW 차트 분석")
        
        # 데이터 가져오기
        df = get_candle_data()
        
        # 현재가 및 주요 지표 표시
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            current_price = df.iloc[-1]['trade_price']
            previous_price = df.iloc[-2]['trade_price']
            price_change = (current_price - previous_price) / previous_price * 100
            price_color = "green" if price_change >= 0 else "red"
            
            st.metric(
                label="BTC 현재가", 
                value=f"{current_price:,.0f}원",
                delta=f"{price_change:.2f}%"
            )
        
        with col2:
            rsi = df.iloc[-1]['rsi']
            rsi_color = "red" if rsi > 70 else "green" if rsi < 30 else "black"
            
            st.metric(
                label="RSI", 
                value=f"{rsi:.2f}",
                delta=None
            )
        
        with col3:
            ma_cross = "골든 크로스" if df.iloc[-1]['ma5'] > df.iloc[-1]['ma20'] and df.iloc[-2]['ma5'] <= df.iloc[-2]['ma20'] else "데드 크로스" if df.iloc[-1]['ma5'] < df.iloc[-1]['ma20'] and df.iloc[-2]['ma5'] >= df.iloc[-2]['ma20'] else "없음"
            
            st.metric(
                label="MA 교차 신호", 
                value=ma_cross,
                delta=None
            )
        
        with col4:
            bb_pos = (df.iloc[-1]['trade_price'] - df.iloc[-1]['lower_band']) / (df.iloc[-1]['upper_band'] - df.iloc[-1]['lower_band'])
            bb_signal = "과매수" if bb_pos > 0.95 else "과매도" if bb_pos < 0.05 else "중립"
            
            st.metric(
                label="볼린저 밴드 위치", 
                value=f"{bb_pos:.2f}",
                delta=bb_signal
            )
        
        # 차트 그리기
        chart = plot_candle_chart(df)
        st.plotly_chart(chart, use_container_width=True)
        
        # 신호 분석
        st.subheader("신호 분석")
        
        # 최근 데이터에서 트렌드 분석
        analyzer = DataAnalyzer()
        trend = analyzer.analyze_trend(df)
        
        # 각 전략별 신호 생성
        ma_strategy = MACrossStrategy()
        rsi_strategy = RSIStrategy()
        macd_strategy = MACDStrategy()
        bb_strategy = BollingerBandStrategy()
        combined_strategy = CombinedStrategy()
        
        ma_signal = ma_strategy.generate_signal(trend)
        rsi_signal = rsi_strategy.generate_signal(trend)
        macd_signal = macd_strategy.generate_signal(trend)
        bb_signal = bb_strategy.generate_signal(trend)
        combined_signal = combined_strategy.generate_signal(trend)
        
        signal_col1, signal_col2, signal_col3, signal_col4, signal_col5 = st.columns(5)
        
        with signal_col1:
            signal_color = "green" if ma_signal == "buy" else "red" if ma_signal == "sell" else "gray"
            st.markdown(f"<div style='background-color: {signal_color}; padding: 10px; border-radius: 5px; text-align: center; color: white;'><h3>MA 신호</h3><h2>{ma_signal.upper()}</h2></div>", unsafe_allow_html=True)
        
        with signal_col2:
            signal_color = "green" if rsi_signal == "buy" else "red" if rsi_signal == "sell" else "gray"
            st.markdown(f"<div style='background-color: {signal_color}; padding: 10px; border-radius: 5px; text-align: center; color: white;'><h3>RSI 신호</h3><h2>{rsi_signal.upper()}</h2></div>", unsafe_allow_html=True)
        
        with signal_col3:
            signal_color = "green" if macd_signal == "buy" else "red" if macd_signal == "sell" else "gray"
            st.markdown(f"<div style='background-color: {signal_color}; padding: 10px; border-radius: 5px; text-align: center; color: white;'><h3>MACD 신호</h3><h2>{macd_signal.upper()}</h2></div>", unsafe_allow_html=True)
        
        with signal_col4:
            signal_color = "green" if bb_signal == "buy" else "red" if bb_signal == "sell" else "gray"
            st.markdown(f"<div style='background-color: {signal_color}; padding: 10px; border-radius: 5px; text-align: center; color: white;'><h3>BB 신호</h3><h2>{bb_signal.upper()}</h2></div>", unsafe_allow_html=True)
        
        with signal_col5:
            signal_color = "green" if combined_signal == "buy" else "red" if combined_signal == "sell" else "gray"
            st.markdown(f"<div style='background-color: {signal_color}; padding: 10px; border-radius: 5px; text-align: center; color: white;'><h3>복합 신호</h3><h2>{combined_signal.upper()}</h2></div>", unsafe_allow_html=True)
        
        # 수동 거래 옵션
        st.subheader("수동 거래")
        manual_col1, manual_col2, manual_col3 = st.columns(3)
        
        with manual_col1:
            # 초기값은 총 금액의 10%와 최소 주문금액 중 큰 값으로 설정
            initial_value = max(10000, int(total_krw * 0.1))
            # 계좌 잔액이 최소 주문금액보다 적을 경우 예외처리
            if total_krw < 10000:
                st.warning("계좌 잔액이 최소 주문금액(10,000원)보다 적습니다.")
                buy_amount = st.number_input("매수 금액 (KRW)", min_value=1000, max_value=int(max(total_krw, 1000)), value=int(max(total_krw, 1000)))
            else:
                buy_amount = st.number_input("매수 금액 (KRW)", min_value=10000, max_value=int(total_krw), value=initial_value)
        
        with manual_col2:
            st.write(" ")
            st.write(" ")
            if st.button("매수 실행", key="buy_button", type="primary"):
                access_key, secret_key = get_api_keys()
                api = UpbitAPI(access_key, secret_key)
                result = api.buy_market_order("KRW-BTC", buy_amount)
                st.success(f"매수 주문 실행: {buy_amount} KRW")
                time.sleep(1)
                st.rerun()
        
        with manual_col3:
            st.write(" ")
            st.write(" ")
            if st.button("매도 실행", key="sell_button", type="primary", help="보유한 모든 BTC를 매도합니다"):
                # BTC 보유량 확인
                btc_account = None
                for account in accounts:
                    if account['currency'] == 'BTC':
                        btc_account = account
                        break
                
                if btc_account and float(btc_account['balance']) > 0:
                    access_key, secret_key = get_api_keys()
                    api = UpbitAPI(access_key, secret_key)
                    result = api.sell_market_order("KRW-BTC", float(btc_account['balance']))
                    st.success(f"매도 주문 실행: {float(btc_account['balance'])} BTC")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("매도할 BTC가 없습니다.")
    
    with tab2:
        # 거래 기록 탭
        st.header("최근 거래 기록")
        trades = get_recent_trades()
        
        if trades:
            for trade in trades:
                col1, col2 = st.columns([1, 4])
                with col1:
                    if trade['action'] == '매수':
                        st.markdown("<span style='color: green; font-weight: bold;'>매수</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='color: red; font-weight: bold;'>매도</span>", unsafe_allow_html=True)
                with col2:
                    st.write(trade['details'])
                st.divider()
        else:
            st.info("아직 거래 기록이 없습니다.")
    
    with tab3:
        # 포트폴리오 탭
        st.header("포트폴리오 분석")
        
        # 자산 차트
        if accounts:
            portfolio_chart = plot_assets_chart(accounts)
            st.plotly_chart(portfolio_chart, use_container_width=True)
        else:
            st.info("계정 정보를 가져올 수 없습니다.")
    
    # 자동 갱신
    if auto_trading:
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    main()