#!/bin/bash

# 스크립트 위치 기준으로 경로 설정
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# 가상환경 활성화
source venv/bin/activate

# 대시보드 실행
streamlit run dashboard.py