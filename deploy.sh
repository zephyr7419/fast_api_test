#!/bin/bash

# 실패 시 스크립트 중단
set -e

# 환경 변수 설정
DOCKER_REGISTRY="your-docker-registry.com"  # 실제 레지스트리 주소로 변경 필요
IMAGE_NAME="fastapi-app"
IMAGE_TAG=$(git rev-parse --short HEAD)  # Git 커밋 해시를 태그로 사용
FULL_IMAGE_NAME="${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
LATEST_IMAGE_NAME="${DOCKER_REGISTRY}/${IMAGE_NAME}:latest"

# 도커 이미지 빌드
echo "Building Docker image: ${FULL_IMAGE_NAME}"
docker build -t ${FULL_IMAGE_NAME} -t ${LATEST_IMAGE_NAME} .

# 도커 이미지 푸시
echo "Pushing Docker image to registry"
docker push ${FULL_IMAGE_NAME}
docker push ${LATEST_IMAGE_NAME}

# 쿠버네티스 매니페스트의 이미지 태그 업데이트
echo "Updating Kubernetes manifests"
sed -i "s|image: .*fastapi-app:.*|image: ${FULL_IMAGE_NAME}|g" k8s/deployment.yaml

# 쿠버네티스 네임스페이스 생성 (없는 경우)
kubectl get namespace fastapi-namespace || kubectl create namespace fastapi-namespace

# 쿠버네티스에 배포
echo "Deploying to Kubernetes"
kubectl apply -k k8s/

echo "Deployment completed successfully!"
echo "You can access the application on any node's IP at port 30080"
