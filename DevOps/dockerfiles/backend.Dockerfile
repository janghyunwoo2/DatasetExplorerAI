# devops/dockerfiles/backend.Dockerfile
FROM python:3.11-slim-bullseye

# 작업 디렉토리 설정 (컨테이너 내부 경로)
WORKDIR /app

# requirements.txt 복사 및 설치 (프로젝트 루트의 requirements.txt 사용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# LLM 폴더 복사 (back_web.py가 LLM 모듈을 import하므로 필수)
COPY LLM/ ./LLM/

# Web/Back_end 폴더 복사
COPY Web/Back_end/*.py ./Web/Back_end/

# 작업 디렉토리를 Web/Back_end로 변경
WORKDIR /app/Web/Back_end

# FastAPI 애플리케이션 실행 명령
# 0.0.0.0으로 바인딩하여 컨테이너 외부에서 접근 가능하게 함
CMD ["uvicorn", "back_web:app", "--host", "0.0.0.0", "--port", "8000"]