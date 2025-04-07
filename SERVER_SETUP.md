# 서버 설치 및 실행 가이드

## 1. 코드 다운로드

```bash
# GitHub에서 코드 클론
git clone https://github.com/asula1/bitcoin-trading-upbit.git
cd bitcoin-trading-upbit
```

## 2. 설치 방법

### A. Docker 사용 (권장)

```bash
# Docker 및 Docker Compose 설치 (Ubuntu 기준)
sudo apt update
sudo apt install -y docker.io docker-compose

# Docker 권한 설정
sudo usermod -aG docker $USER
newgrp docker

# 도커 실행
docker-compose up -d
```

### B. 직접 설치

```bash
# Python 및 필요 패키지 설치
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 필요 패키지 설치
pip install -r requirements.txt

# 설정 파일 확인
# config/config.ini 파일에 API 키가 올바르게 설정되어 있는지 확인
```

## 3. 실행 방법

### A. Docker 사용

```bash
# 도커로 모든 서비스 실행
./run_docker.sh

# 도커 로그 확인
docker-compose logs -f

# 도커 중지
./stop_docker.sh
```

### B. 직접 실행

```bash
# 트레이딩 봇 실행
./run.sh

# 대시보드 실행 (포트 8501)
./run_dashboard.sh

# 백테스트 실행
./run_backtest.sh
```

## 4. 대시보드 접속

- Docker 사용 시: http://서버IP:80
- 직접 실행 시: http://서버IP:8501

## 5. 설정 변경

`config/config.ini` 파일을 수정하여 다음 설정을 변경할 수 있습니다:

- API 키 설정
- 거래 전략 선택
- 거래량 설정
- K값 조정 (변동성 돌파 전략)
- 매수/매도 비율 설정

## 6. 로그 확인

```bash
# 로그 파일 실시간 확인
tail -f logs/trading_*.log

# 또는 Docker 로그 확인
docker-compose logs -f
```

## 7. 문제 해결

### 실행 권한 오류
```bash
# 실행 스크립트에 권한 부여
chmod +x *.sh
```

### API 키 오류
API 키가 올바르게 설정되었는지 확인합니다:
```bash
# API 연결 테스트
./check_account.py
```

### 아키텍처 호환성 문제
서버 아키텍처가 ARM(예: Apple Silicon)인 경우 Docker 설정이 호환되는지 확인합니다.