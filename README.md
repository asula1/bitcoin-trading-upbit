# 비트코인 자동매매 프로그램

업비트 API를 활용한 비트코인 자동매매 프로그램입니다.

## 기능

- 업비트 API를 통한 시장 데이터 수집
- 다양한 기술적 지표 분석 (이동평균선, RSI, MACD, 볼린저 밴드 등)
- 여러 매매 전략 지원
  - 이동평균선 교차 (Golden/Death Cross)
  - RSI (상대강도지수) 
  - MACD (이동평균수렴확산지수)
  - 볼린저 밴드
  - 변동성 돌파 전략 (K값 조정 가능)
  - 퍼센트 기반 매매 전략 (평균 매수가 대비 수익률/손실률 기반)
  - 복합 전략 (여러 전략의 투표 방식)
- 최적의 코인 및 K값 자동 찾기
- 백테스팅 기능으로 전략 성능 분석
- 실시간 매매 신호 생성 및 자동 매매 실행
- 슬랙을 통한 거래 알림 기능
- 로깅 시스템을 통한 거래 기록 관리
- Docker 컨테이너로 서버 환경에서 쉽게 실행 가능

## 설치 방법

### 일반 설치
1. 저장소 클론
```
git clone https://github.com/yourusername/bitcoin-trading-bot.git
cd bitcoin-trading-bot
```

2. 가상환경 생성 및 필요한 패키지 설치
```
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. 환경 설정
- `config/config.ini` 파일에 업비트 API 키 및 알림 설정을 입력하세요.
```
[API]
access_key = YOUR_UPBIT_ACCESS_KEY_HERE
secret_key = YOUR_UPBIT_SECRET_KEY_HERE

[NOTIFICATION]
slack_webhook_url = YOUR_SLACK_WEBHOOK_URL (선택사항)
```

### Docker를 이용한 설치
1. 저장소 클론
```
git clone https://github.com/yourusername/bitcoin-trading-bot.git
cd bitcoin-trading-bot
```

2. 환경 설정
- `config/config.ini` 파일에 업비트 API 키 및 알림 설정을 입력하세요.

3. Docker 컨테이너 빌드 및 실행
```
chmod +x run_docker.sh
./run_docker.sh
```

## 사용 방법

### 기본 실행

```
./run.sh
```

### 옵션 사용

- 설정 파일 경로 지정
```
python main.py --config path/to/config.ini
```

- 거래 마켓 지정
```
python main.py --market KRW-BTC
```

- 거래 간격 지정 (초 단위)
```
python main.py --interval 300
```

- 거래 전략 지정
```
python main.py --strategy volatility
```

- 변동성 돌파 전략의 K값 지정
```
python main.py --strategy volatility --k 0.5
```

- 슬랙 알림 URL 지정
```
python main.py --slack "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
```

- 최적의 코인 및 K값 찾기
```
python main.py --find-best
```

- 백테스트 모드 실행 
```
python main.py --backtest
```

또는 백테스트 스크립트 직접 실행:
```
./run_backtest.sh
```

### Docker 환경에서 실행

- Docker로 실행:
```
./run_docker.sh
```

- Docker 중지:
```
./stop_docker.sh
```

- Docker 로그 확인:
```
docker-compose logs -f
```

## 대시보드 접속

자동매매 프로그램을 실행하면 브라우저에서 대시보드에 접속할 수 있습니다:

- 일반 실행 시: http://localhost:8501
- Docker 실행 시: http://localhost:80 또는 http://서버IP:80

## 지원하는 전략

- `ma`: 이동평균선 교차 전략
- `rsi`: RSI(Relative Strength Index) 전략
- `macd`: MACD(Moving Average Convergence Divergence) 전략
- `bb`: 볼린저 밴드 전략
- `volatility`: 변동성 돌파 전략
- `percentage`: 퍼센트 기반 매매 전략
- `combined`: 복합 전략 (여러 전략의 투표 방식)

## 주의 사항

- 이 프로그램은 투자 조언을 제공하지 않습니다.
- 실제 자금으로 거래할 때는 주의하세요.
- API 키는 안전하게 보관하세요.
- 프로그램의 성능을 보장하지 않으며, 모든 거래는 사용자의 책임입니다.

## 라이선스

[MIT License](LICENSE)