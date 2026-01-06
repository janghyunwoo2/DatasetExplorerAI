# CI/CD & DevOps 가이드

> Dataset Explorer AI Agent 배포 자동화

---

## 목차

1. [CI/CD 개요](#1-cicd-개요)
2. [GitHub Actions 워크플로우](#2-github-actions-워크플로우)
3. [Docker 구성](#3-docker-구성)
4. [배포 과정](#4-배포-과정)
5. [설정 가이드](#5-설정-가이드)

---

## 1. CI/CD 개요

### 배포 플로우

```
GitHub Push (main) 
    ↓
GitHub Actions 트리거
    ↓
Docker 이미지 빌드 (Backend + Frontend)
    ↓
Docker Hub 푸시
    ↓
EC2에 docker-compose.yml 복사
    ↓
SSH 접속하여 배포
    ↓
컨테이너 실행
```

### 기술 스택

- **CI/CD**: GitHub Actions
- **컨테이너**: Docker, Docker Compose
- **레지스트리**: Docker Hub
- **서버**: AWS EC2 (Ubuntu)
- **Backend**: FastAPI (Port 8000)
- **Frontend**: Streamlit (Port 8501)

---

## 2. GitHub Actions 워크플로우

### 파일 위치
> 📄 [.github/workflows/deploy.yml](file:///C:/Users/3571/Desktop/projects/DatasetExplorerAI/.github/workflows/deploy.yml)

### 트리거

```yaml
on:
  push:
    branches:
      - main  # main 브랜치 푸시 시 실행
  workflow_dispatch:  # 수동 실행 가능
```

### 주요 단계

#### Step 1: 코드 체크아웃

```yaml
- name: Checkout Code
  uses: actions/checkout@v4
```

#### Step 2: Docker Hub 로그인

```yaml
- name: Login to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKER_USERNAME }}
    password: ${{ secrets.DOCKER_PASSWORD }}
```

#### Step 3: Backend 빌드 & 푸시

```yaml
- name: Build & push FastAPI Docker Image
  run: |
    docker build -t ${{ env.DOCKER_HUB_USERNAME }}/${{ env.DOCKER_REPO_BACKEND }}:latest \
      -f ./DevOps/dockerfiles/backend.Dockerfile .
    docker push ${{ env.DOCKER_HUB_USERNAME }}/${{ env.DOCKER_REPO_BACKEND }}:latest
```

**핵심**:
- Build context: 프로젝트 루트 (`.`)
- Dockerfile: `./DevOps/dockerfiles/backend.Dockerfile`
- 이미지: `username/dataset-explorer-backend:latest`

#### Step 4: Frontend 빌드 & 푸시

```yaml
- name: Build & push Streamlit Docker Image
  run: |
    docker build -t ${{ env.DOCKER_HUB_USERNAME }}/${{ env.DOCKER_REPO_FRONTEND }}:latest \
      -f ./DevOps/dockerfiles/frontend.Dockerfile .
    docker push ${{ env.DOCKER_HUB_USERNAME }}/${{ env.DOCKER_REPO_FRONTEND }}:latest
```

#### Step 5: docker-compose.yml 복사

```yaml
- name: Copy docker-compose.yml to EC2
  uses: appleboy/scp-action@master
  with:
    host: ${{ secrets.EC2_HOST_IP }}
    username: ${{ secrets.EC2_USERNAME }}
    key: ${{ secrets.EC2_SSH_PRIVATE_KEY }}
    source: "./docker-compose.yml"
    target: "/home/${{ secrets.EC2_USERNAME }}/dataset-explorer-agent"
```

#### Step 6: EC2 배포

```yaml
- name: Docker-Compose Up to EC2 via ssh
  uses: appleboy/ssh-action@master
  with:
    script: |
      cd /home/${{ secrets.EC2_USERNAME }}/dataset-explorer-agent
      
      # 기존 컨테이너 정리
      docker-compose down
      
      # 최신 이미지 가져오기
      docker-compose pull
      
      # 새 컨테이너 실행
      docker-compose up -d --build --force-recreate --remove-orphans
      
      # 미사용 이미지 정리
      docker image prune -f
```

**핵심 명령어**:
- `docker-compose down`: 기존 컨테이너 중지 및 삭제
- `docker-compose pull`: Docker Hub에서 최신 이미지 다운로드
- `docker-compose up -d --build --force-recreate`: 새 컨테이너 실행
  - `-d`: 백그라운드 실행
  - `--build`: 이미지 재빌드 (필요 시)
  - `--force-recreate`: 강제 재생성
  - `--remove-orphans`: 고아 컨테이너 제거
- `docker image prune -f`: 미사용 이미지 삭제

---

## 3. Docker 구성

### 3-1. docker-compose.yml

> 📄 [docker-compose.yml](file:///C:/Users/3571/Desktop/projects/DatasetExplorerAI/docker-compose.yml)

```yaml
services:
  backend-service:
    image: ${DOCKER_HUB_USERNAME}/${DOCKER_REPO_BACKEND}:latest
    container_name: dataset_explorer_fastapi
    ports:
      - "8000:8000"
    environment:
      - AWS_REGION=${AWS_REGION}
      - BEDROCK_MODEL_ID=${BEDROCK_MODEL_ID}
      - AWS_BEARER_TOKEN_BEDROCK=${AWS_BEARER_TOKEN_BEDROCK}
    restart: always
    networks:
      - app-network

  frontend-service:
    image: ${DOCKER_HUB_USERNAME}/${DOCKER_REPO_FRONTEND}:latest
    container_name: dataset_explorer_streamlit
    ports:
      - "8501:8501"
    environment:
      - FASTAPI_URL=http://backend-service:8000
    restart: always
    depends_on:
      - backend-service
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

**핵심**:
- **Backend**: FastAPI (Port 8000)
- **Frontend**: Streamlit (Port 8501)
- **네트워크**: `app-network` (bridge)
- **Frontend → Backend 통신**: `http://backend-service:8000` (컨테이너 이름 사용)

---

### 3-2. Backend Dockerfile

> 📄 [DevOps/dockerfiles/backend.Dockerfile](file:///C:/Users/3571/Desktop/projects/DatasetExplorerAI/DevOps/dockerfiles/backend.Dockerfile)

```dockerfile
FROM python:3.11-slim-bullseye

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# LLM 폴더 복사 (back_web.py가 import)
COPY LLM/ ./LLM/

# Backend 코드 복사
COPY Web/Back_end/*.py ./Web/Back_end/

WORKDIR /app/Web/Back_end

# FastAPI 실행
CMD ["uvicorn", "back_web:app", "--host", "0.0.0.0", "--port", "8000"]
```

**핵심**:
- Base 이미지: `python:3.11-slim-bullseye`
- LLM 폴더 필수 (agent 코드 import)
- `--host 0.0.0.0`: 외부 접근 허용

---

### 3-3. Frontend Dockerfile

> 📄 [DevOps/dockerfiles/frontend.Dockerfile](file:///C:/Users/3571/Desktop/projects/DatasetExplorerAI/DevOps/dockerfiles/frontend.Dockerfile)

```dockerfile
FROM python:3.11-slim-bullseye

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Frontend 코드 복사
COPY Web/Front_end/*.py ./Web/Front_end/

WORKDIR /app/Web/Front_end

# Streamlit 실행
CMD ["streamlit", "run", "front_web.py", \
     "--server.port", "8501", \
     "--server.address", "0.0.0.0", \
     "--server.enableCORS", "false", \
     "--server.enableXsrfProtection", "false"]
```

**핵심**:
- Streamlit 설정:
  - `--server.port 8501`: 포트 지정
  - `--server.address 0.0.0.0`: 외부 접근 허용
  - `--server.enableCORS false`: CORS 비활성화
  - `--server.enableXsrfProtection false`: XSRF 보호 비활성화

---

## 4. 배포 과정

### 자동 배포 (CI/CD)

```bash
# 1. 코드 수정 후 Push
git add .
git commit -m "Update feature"
git push origin main

# 2. GitHub Actions 자동 실행
# - 이미지 빌드
# - Docker Hub 푸시
# - EC2 배포

# 3. 5-10분 후 배포 완료
# http://<EC2_IP>:8501 (Streamlit)
# http://<EC2_IP>:8000 (FastAPI)
```

### 수동 배포 (로컬)

#### 이미지 빌드

```bash
# Backend
docker build -t your-username/dataset-explorer-backend:latest \
  -f ./DevOps/dockerfiles/backend.Dockerfile .

# Frontend
docker build -t your-username/dataset-explorer-frontend:latest \
  -f ./DevOps/dockerfiles/frontend.Dockerfile .
```

#### 이미지 푸시

```bash
docker login
docker push your-username/dataset-explorer-backend:latest
docker push your-username/dataset-explorer-frontend:latest
```

#### EC2 배포

```bash
# SSH 접속
ssh -i your-key.pem ubuntu@your-ec2-ip

# 배포 디렉토리 이동
cd ~/dataset-explorer-agent

# 환경 변수 설정
export DOCKER_HUB_USERNAME="your-username"
export DOCKER_REPO_BACKEND="dataset-explorer-backend"
export DOCKER_REPO_FRONTEND="dataset-explorer-frontend"
export AWS_REGION="us-east-1"
export BEDROCK_MODEL_ID="google.gemma-3-27b-it"
export AWS_BEARER_TOKEN_BEDROCK="your-token"

# 배포
docker-compose down
docker-compose pull
docker-compose up -d --build --force-recreate
```

---

## 5. 설정 가이드

### GitHub Secrets 설정

Repository → Settings → Secrets and variables → Actions

| Secret 이름 | 설명 | 예시 |
|-------------|------|------|
| `DOCKER_USERNAME` | Docker Hub 사용자명 | `myusername` |
| `DOCKER_PASSWORD` | Docker Hub 토큰 | `dckr_pat_xxxxx` |
| `EC2_HOST_IP` | EC2 인스턴스 IP | `12.34.56.78` |
| `EC2_USERNAME` | EC2 사용자명 | `ubuntu` |
| `EC2_SSH_PRIVATE_KEY` | EC2 SSH 키 | `-----BEGIN RSA...` |
| `AWS_REGION` | AWS 리전 | `us-east-1` |
| `BEDROCK_MODEL_ID` | Bedrock 모델 ID | `google.gemma-3-27b-it` |
| `AWS_BEARER_TOKEN_BEDROCK` | AWS 인증 토큰 | `your-token` |

### EC2 초기 설정

```bash
# Docker 설치
sudo apt update
sudo apt install -y docker.io docker-compose

# Docker 권한 설정
sudo usermod -aG docker $USER
newgrp docker

# 배포 디렉토리 생성
mkdir -p ~/dataset-explorer-agent
```

---

## 6. 트러블슈팅

### 문제 1: 컨테이너가 실행되지 않음

```bash
# 로그 확인
docker logs dataset_explorer_fastapi
docker logs dataset_explorer_streamlit

# 컨테이너 상태 확인
docker ps -a
```

### 문제 2: 환경 변수 누락

```bash
# 환경 변수 확인
docker exec dataset_explorer_fastapi env | grep AWS
```

### 문제 3: 포트 충돌

```bash
# 포트 사용 확인
sudo netstat -tulpn | grep 8000
sudo netstat -tulpn | grep 8501

# 기존 프로세스 종료
sudo kill -9 <PID>
```

### 문제 4: 이미지 다운로드 실패

```bash
# Docker Hub 로그인 확인
docker login

# 이미지 수동 다운로드
docker pull your-username/dataset-explorer-backend:latest
docker pull your-username/dataset-explorer-frontend:latest
```

---

## 7. 모니터링

### 컨테이너 상태 확인

```bash
# 실행 중인 컨테이너
docker ps

# 상세 정보
docker inspect dataset_explorer_fastapi
docker inspect dataset_explorer_streamlit
```

### 리소스 사용량

```bash
# CPU, 메모리 사용량
docker stats
```

### 로그 확인

```bash
# 실시간 로그
docker logs -f dataset_explorer_fastapi
docker logs -f dataset_explorer_streamlit

# 최근 100줄
docker logs --tail 100 dataset_explorer_fastapi
```

---

## 8. 주요 명령어 요약

| 명령어 | 설명 |
|--------|------|
| `docker-compose up -d` | 컨테이너 백그라운드 실행 |
| `docker-compose down` | 컨테이너 중지 및 삭제 |
| `docker-compose pull` | 최신 이미지 다운로드 |
| `docker-compose logs` | 로그 확인 |
| `docker ps` | 실행 중인 컨테이너 확인 |
| `docker image prune -f` | 미사용 이미지 삭제 |
| `docker system prune -a` | 미사용 리소스 전체 삭제 |

---

## 핵심 요약

| 항목 | 내용 |
|------|------|
| **트리거** | `main` 브랜치 푸시 |
| **빌드** | Backend + Frontend Docker 이미지 |
| **레지스트리** | Docker Hub |
| **배포 대상** | AWS EC2 |
| **컨테이너** | FastAPI (8000) + Streamlit (8501) |
| **네트워크** | Docker bridge network |
| **소요 시간** | 5-10분 |

---

📄 **관련 파일**:
- [deploy.yml](.github/workflows/deploy.yml)
- [docker-compose.yml](docker-compose.yml)
- [backend.Dockerfile](DevOps/dockerfiles/backend.Dockerfile)
- [frontend.Dockerfile](DevOps/dockerfiles/frontend.Dockerfile)
