# # devops/deploy/deploy.sh
# #!/bin/bash

# # 배포 디렉토리 (EC2에 프로젝트 코드가 클론된 경로)
# # GitHub Actions에서 SSH로 접속 시 이 경로를 기반으로 작업하게 됨
# DEPLOY_DIR="/home/ubuntu/dataset-explorer-agent" # EC2 사용자 이름과 프로젝트 경로에 맞게 수정 (예: ec2-user)

# echo "EC2에서 배포 스크립트 실행 시작..."
# cd $DEPLOY_DIR || { echo "ERROR: 배포 디렉토리로 이동할 수 없습니다."; exit 1; }

# # 최신 코드를 git pull (새로운 docker-compose.yml이나 Dockerfile 변경 사항 적용)
# echo "최신 코드 PULL..."
# git pull origin develop || { echo "ERROR: Git pull 실패."; exit 1; }

# # Docker Hub 로그인
# echo "Docker Hub 로그인 중..."
# # secrets.DOCKER_USERNAME과 secrets.DOCKER_PASSWORD는 GitHub Secrets에 저장되어 있어야 함
# echo "${DOCKER_PASSWORD}" | docker login --username "${DOCKER_USERNAME}" --password-stdin || { echo "ERROR: Docker Hub 로그인 실패."; exit 1; }

# # 기존 서비스 중지 (이 시점에 서비스가 잠시 중단됨)
# echo "기존 서비스 중지 중..."
# docker-compose -f devops/docker-compose.yml down || true # 오류 무시 (최초 실행 시 컨테이너가 없을 수 있음)

# # 최신 Docker 이미지들을 Docker Hub에서 풀
# echo "최신 Docker 이미지 PULL 중..."
# docker-compose -f devops/docker-compose.yml pull || { echo "ERROR: Docker 이미지 풀 실패."; exit 1; }

# # 서비스 빌드 및 재시작 (업데이트된 이미지로)
# # --build 옵션은 docker-compose.yml에 build 지시자가 있을 경우 유용.
# # 이미지 빌드가 필요 없으면 생략 가능하지만, 일단 포함.
# echo "서비스 재빌드 및 재시작 중..."
# docker-compose -f devops/docker-compose.yml up -d --build || { echo "ERROR: Docker Compose 서비스 시작 실패."; exit 1; }

# echo "배포 완료! Streamlit 앱은 EC2의 8501 포트로 접속 가능합니다."
# echo "예시: http://EC2_PUBLIC_IP:8501"
