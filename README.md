# DatasetExplorerAI
프로젝트명: AI 기반 "데이터셋 탐험가 에이전트" (Dataset Explorer Agent) - 핵심 목표: 사용자가 원하는 데이터셋을 빠르고 효율적으로 찾고 이해할 수 있도록 돕는 지능형 Agent 기반 웹 서비스를 개발한다.

- 선행 작업
    - github 메인 프로젝트 fork해와서 로컬에 clone 하기

- 필요한 라이브러리 설치
    ```
    pip install -r requirements.txt
    ```

- venv 생성 및 실행
    ```
    python -m venv env
    env/Scripts/Activate (실행하기)
    deactivate (나가기)
    ```

- 백엔드 : back_web.py  
    py파일이 있는 곳 까지 이동한 후 명령어 실행하기
    ```
    uvicorn back_web:app --reload --port 8000
    ```
- 프런트 : front_web.py
    ```
    streamlit run front_web.py
    ```
    