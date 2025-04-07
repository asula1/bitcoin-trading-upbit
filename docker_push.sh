#!/bin/bash

# 현재 날짜 및 시간으로 태그 생성 (YYYYMMDD-HHMMSS 형식)
TAG_NAME=$(date +"%Y%m%d-%H%M%S")

# Docker Hub 계정
DOCKER_USERNAME="asula1"
DOCKER_REPO="auto-trading-upbit"
FULL_IMAGE_NAME="$DOCKER_USERNAME/$DOCKER_REPO:$TAG_NAME"

echo "==== Docker 이미지 빌드 및 푸시 ===="
echo "이미지: $FULL_IMAGE_NAME"

# 이미지 빌드
echo "1. 이미지 빌드 중..."
docker build -t $FULL_IMAGE_NAME .

# 로그인 과정
echo "2. Docker Hub 로그인..."
echo "사용자 이름: $DOCKER_USERNAME"
echo "비밀번호: 입력해주세요"
docker login -u $DOCKER_USERNAME

# 이미지 푸시
echo "3. Docker Hub에 이미지 푸시 중..."
docker push $FULL_IMAGE_NAME

# latest 태그 업데이트
echo "4. 'latest' 태그 업데이트 중..."
docker tag $FULL_IMAGE_NAME "$DOCKER_USERNAME/$DOCKER_REPO:latest"
docker push "$DOCKER_USERNAME/$DOCKER_REPO:latest"

echo "==== 완료 ===="
echo "이미지가 성공적으로 푸시되었습니다: $FULL_IMAGE_NAME"
echo "latest 태그도 업데이트되었습니다: $DOCKER_USERNAME/$DOCKER_REPO:latest"
echo "Docker Hub에서 확인: https://hub.docker.com/r/$DOCKER_USERNAME/$DOCKER_REPO"