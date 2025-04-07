#!/bin/bash

# Docker Compose를 사용하여 컨테이너 빌드 및 실행
docker-compose up -d

echo "Bitcoin Trading Bot이 백그라운드에서 실행 중입니다."
echo "대시보드에 접속하려면 브라우저에서 http://localhost:80 을 열어주세요."
echo "로그를 확인하려면 다음 명령어를 사용하세요: docker-compose logs -f"