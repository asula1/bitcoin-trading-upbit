#!/bin/bash

# 스크립트 위치 기준으로 경로 설정
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Docker 환경에서는 가상환경 활성화 건너뛰기
if [ -d "venv" ]; then
    # 가상환경이 있으면 활성화
    source venv/bin/activate
fi

# 프로그램 실행
python main.py "$@"