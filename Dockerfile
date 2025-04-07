FROM python:3.11-slim

WORKDIR /app

# 필요한 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1

# 로그 디렉토리 생성
RUN mkdir -p /app/logs

# 실행 스크립트에 실행 권한 부여
RUN chmod +x run.sh run_dashboard.sh run_backtest.sh

# Streamlit 설정 - 80 포트 사용
RUN mkdir -p /root/.streamlit
RUN echo "\
[server]\n\
port = 80\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
" > /root/.streamlit/config.toml

# 80 포트 노출 (Streamlit 대시보드용)
EXPOSE 80

# 진입점 설정
ENTRYPOINT ["/bin/bash"]

# 기본 명령 (자동매매 봇 실행)
CMD ["./run.sh"]