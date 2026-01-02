# devops/dockerfiles/frontend.Dockerfile
FROM python:3.11-slim-bullseye

# 작업 디렉토리 설정 (컨테이너 내부 경로)
WORKDIR /app

# requirements.txt 복사 및 설치 (프로젝트 루트의 requirements.txt 사용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Web/Front_end 폴더 복사
COPY Web/Front_end/*.py ./Web/Front_end/

# 작업 디렉토리를 Web/Front_end로 변경
WORKDIR /app/Web/Front_end

# Streamlit 애플리케이션 실행 명령
# 0.0.0.0으로 바인딩하여 컨테이너 외부에서 접근 가능하게 하고,
# --server.port 8501로 기본 포트 설정
CMD ["streamlit", "run", "front_web.py", "--server.port", "8501", "--server.address", "0.0.0.0", "--server.enableCORS", "false", "--server.enableXsrfProtection", "false"]