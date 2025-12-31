# devops/dockerfiles/backend.Dockerfile
FROM python:3.11-slim-bullseye

# 작업 디렉토리 설정 (컨테이너 내부 경로)
WORKDIR /app

# web/backend/requirements.txt 복사 및 설치 (build context가 web/backend이므로 ./로 접근)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# web/backend/main.py 복사 (build context가 web/backend이므로 ./로 접근)
# COPY Web/Back_end/back_web.py .
COPY Web/Back_end/*.py .

# FastAPI 애플리케이션 실행 명령
# 0.0.0.0으로 바인딩하여 컨테이너 외부에서 접근 가능하게 함
CMD ["uvicorn", "back_web:app", "--host", "0.0.0.0", "--port", "8000"]