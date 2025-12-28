
### **🚀 도커 빌드 & 실행 가이드: FastAPI 백엔드 + Streamlit 프론트엔드**

**현재 작업 디렉토리**는 `dataset-explorer-agent/` 프로젝트 루트여야 해.

#### **1. 도커 이미지 빌드**

각 애플리케이션의 Dockerfile을 사용하여 이미지를 빌드합니다. `.`은 **빌드 컨텍스트**로 현재 디렉토리(프로젝트 루트)를 의미합니다.

*   **FastAPI 백엔드 이미지 빌드:**
    ```bash
    docker build --build-arg PYTHON_VERSION=3.11 -f devops/dockerfiles/backend.Dockerfile -t dataset-explorer-backend:latest .
    ```
*   **Streamlit 프론트엔드 이미지 빌드:**
    ```bash
    docker build --build-arg PYTHON_VERSION=3.11 -f devops/dockerfiles/frontend.Dockerfile -t dataset-explorer-frontend:latest .
    ```

#### **2. 빌드된 도커 이미지 확인**

생성된 이미지 목록을 확인합니다.

```bash
docker images
```

`dataset-explorer-backend`와 `dataset-explorer-frontend` 이미지가 보이면 성공입니다.

#### **3. 도커 컨테이너 실행**

빌드된 이미지를 사용하여 컨테이너를 실행합니다. **포트 매핑(`-p`)**이 중요합니다!

*   **FastAPI 백엔드 컨테이너 실행:** (컨테이너 내부 8000번 포트 ➡️ 호스트 8000번 포트 연결)
    ```bash
    docker run -p 8000:8000 --name dataset-explorer-backend-app dataset-explorer-backend:latest
    ```
*   **Streamlit 프론트엔드 컨테이너 실행:** (컨테이너 내부 8501번 포트 ➡️ 호스트 8501번 포트 연결)
    ```bash
    docker run -p 8501:8501 --name dataset-explorer-frontend-app dataset-explorer-frontend:latest
    ```

#### **4. 애플리케이션 접속 (웹 브라우저)**

컨테이너가 실행된 후 웹 브라우저를 열어 각 애플리케이션에 접속합니다.

*   **FastAPI 백엔드:**
    *   **Swagger UI (API 문서):** `http://localhost:8000/docs`
    *   **루트 엔드포인트:** `http://localhost:8000/` (FastAPI 코드에 따라 다를 수 있음)
*   **Streamlit 프론트엔드:**
    *   **Streamlit 앱:** `http://localhost:8501`
