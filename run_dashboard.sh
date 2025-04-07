#!/bin/bash

# 스크립트 위치 기준으로 경로 설정
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Docker 환경에서는 가상환경 활성화 건너뛰기
if [ -d "venv" ]; then
    # 가상환경이 있으면 활성화
    source venv/bin/activate
fi

# Docker 환경에서 실행 여부 확인
if [ -f "/.dockerenv" ]; then
    # Docker 환경에서는 호스트 0.0.0.0으로 서버 실행
    streamlit run dashboard.py --server.address=0.0.0.0 --server.port=80
else
    # 일반 환경에서는 기본 설정으로 실행
    streamlit run dashboard.py
fi