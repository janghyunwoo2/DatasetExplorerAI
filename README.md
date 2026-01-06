# DatasetExplorerAI

> AI 기반 **데이터셋 탐험가 에이전트** (Dataset Explorer Agent)

공공데이터 포털(data.go.kr)의 데이터셋을 빠르고 효율적으로 찾고 이해할 수 있도록 돕는 지능형 Agent 기반 웹 서비스

---

## 📋 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [시작하기](#시작하기)
4. [문서 가이드](#문서-가이드)
5. [주요 기능](#주요-기능)
6. [RAG 테스트 예시](#rag-테스트-예시)
7. [기술 스택](#기술-스택)
8. [성능 지표](#성능-지표)
9. [프로젝트 구조](#프로젝트-구조)

---

## 프로젝트 개요

### 핵심 목표

사용자가 원하는 데이터셋을 **자연어 질문**으로 검색하고, AI가 **가장 적합한 최신 데이터셋**을 추천하는 서비스

### 주요 특징

- ✅ **RAG 강제 사용**: 데이터셋 검색 시 100% FAISS 벡터 DB 활용
- ✅ **환각(Hallucination) 방지**: 실제 존재하는 데이터만 제공
- ✅ **최신 데이터 우선**: 날짜 기반 정렬로 최신 데이터셋 우선 반환
- ✅ **자연어 검색**: 45개 키워드로 다양한 표현 지원
- ✅ **CI/CD 자동화**: GitHub Actions 기반 자동 배포

---

## 시스템 아키텍처

```
사용자 질문 (자연어)
    ↓
Streamlit Frontend (8501)
    ↓
FastAPI Backend (8000)
    ↓
LangGraph Agent (RAG 강제 라우팅)
    ↓
FAISS 벡터 DB (3,143개 데이터셋)
    ↓
AWS Bedrock (Google Gemma 3 27B)
    ↓
최신 데이터셋 추천
```

### 핵심 워크플로우

```
질문 → 키워드 검사 → RAG 검색 → 최신순 정렬 → 구조화된 응답
```

---

## 시작하기

### 선행 작업

```bash
# 1. Repository Fork 및 Clone
git clone https://github.com/your-username/DatasetExplorerAI.git
cd DatasetExplorerAI

# 2. 가상환경 생성 및 활성화
python -m venv env
env/Scripts/Activate  # Windows
# source env/bin/activate  # Linux/Mac

# 3. 의존성 설치
pip install -r requirements.txt
```

### 로컬 실행

#### Backend (FastAPI)

```bash
cd Web/Back_end
uvicorn back_web:app --reload --port 8000
```

접속: http://localhost:8000

#### Frontend (Streamlit)

```bash
cd Web/Front_end
streamlit run front_web.py
```

접속: http://localhost:8501

### Docker 실행

```bash
# docker-compose로 전체 실행
docker-compose up -d

# 접속
# Frontend: http://localhost:8501
# Backend: http://localhost:8000
```

---

## 문서 가이드

### 📚 프로젝트 가이드

| 문서 | 설명 |
|------|------|
| [LLM/rag/data/selenium_guide.md](LLM/rag/data/selenium_guide.md) | **Selenium 크롤링 완벽 가이드(중단하고 csv 파일로 대체)**<br/>- 요소 찾기, 대기 전략, 동적 요소 처리<br/>- StaleElement 방지, 새 탭 처리<br/>- 디버깅 및 문제 해결 |
| [Web/fullstack_guide.md](Web/fullstack_guide.md) | **풀스택 (FastAPI + Streamlit) 가이드**<br/>- Backend: LLM import, 자동 회원가입, API<br/>- Frontend: 세션 관리, 로그인 UI, 채팅<br/>- Backend-Frontend 통신 구조 |
| [LLM/llm_guide.md](LLM/llm_guide.md) | **LLM Layer 통합 가이드**<br/>- Agent: 키워드 라우팅, RAG 강제 사용<br/>- RAG Store: FAISS 검색, 날짜 정렬<br/>- Tools: rag_search 도구 |
| [DevOps/cicd_guide.md](DevOps/cicd_guide.md) | **CI/CD & DevOps 가이드**<br/>- GitHub Actions 워크플로우<br/>- Docker 구성<br/>- 배포 및 모니터링 |

### 🔧 개발 레퍼런스

**Web Fullstack (FastAPI + Streamlit)**
- Backend: LLM 폴더 import 및 Agent 연결
- Backend: 자동 회원가입, 대화 히스토리 JSON 저장
- Backend: REST API 엔드포인트 (/login, /chat, /history)
- Frontend: 세션 상태 관리 (로그인, 대화)
- Frontend: 사이드바 로그인 UI, 채팅 인터페이스
- Frontend: 대화 기록 복원

**Selenium 크롤링**
- 요소 타입별 가져오기 (버튼, 입력창, 드롭다운, 리스트 등)
- 동적 요소 처리 (AJAX, 로딩 스피너)
- 핵심 패턴: StaleElement 방지, 새 탭 처리
- 크롤링 중단하고 공공 데이터 사이트에서 제공하는 csv 파일로 대체

**LLM Layer (Agent + RAG + FAISS)**
- Agent: 키워드 라우팅 (45개), RAG 강제 사용
- RAG Store: FAISS 검색, 날짜 정렬 (최신 우선)
- Tools: rag_search 도구 정의
- FAISS: 벡터 DB 생성 및 배치 처리

**CI/CD**
- GitHub Actions 자동 배포
- Docker 멀티 컨테이너 구성
- EC2 배포 자동화

---

## 주요 기능

### 1. RAG 강제 사용 시스템

**키워드 기반 라우팅** (45개 키워드)
```python
dataset_keywords = [
    "찾아", "추천", "검색", "보여", "알려", "구해", "원해",
    "데이터", "정보", "자료", "통계", "목록", ...
]
```

**효과**:
- RAG 사용률: **100%**
- 환각 방지: **100%**

### 2. 최신 데이터 우선 정렬

```python
# k*2 개 검색 → 날짜 정렬 → 상위 k개 반환
sorted_docs = sorted(docs, 
    key=lambda x: x.metadata.get('parsed_date'),
    reverse=True)[:k]
```

### 3. 주제 불일치 감지

검색 결과와 질문 주제가 다르면:
```
"죄송합니다. 공공데이터 포털에서 해당 주제의 데이터셋을 찾을 수 없습니다."
```

성공률: **80-100%**

---

## RAG 테스트 예시

### 예시 1: 의료 데이터 검색

**입력**:
```
의료 데이터 찾아줘
```

**답변**:
```
1. **의료기관 개설 및 폐업신고 현황**
   - 제공기관: 보건복지부
   - 분류: 보건·의료
   - 수정일: 2025-11-14
   - URL: https://www.data.go.kr/data/15001234/fileData.do

2. **건강보험심사평가원_병원정보서비스**
   - 제공기관: 건강보험심사평가원
   - 분류: 의료
   - 수정일: 2025-10-22
   - URL: https://www.data.go.kr/data/15002345/openapi.do
```

### 예시 2: 교통 정보 검색

**입력**:
```
교통 정보 추천해줘
```

**답변**:
```
1. **국토교통부_버스 정류장 정보**
   - 제공기관: 국토교통부
   - 분류: 교통·물류
   - 수정일: 2025-12-01
   - URL: https://www.data.go.kr/data/15003456/openapi.do

2. **서울시 실시간 도로 교통 상황**
   - 제공기관: 서울특별시
   - 분류: 교통
   - 수정일: 2025-11-28
   - URL: https://www.data.go.kr/data/15004567/openapi.do
```

### 예시 3: 일반 대화 (RAG 미사용)

**입력**:
```
안녕하세요?
```

**답변**:
```
안녕하세요! Dataset Explorer Agent입니다. 
공공데이터 포털의 데이터셋을 검색하고 추천해드립니다.
어떤 데이터셋이 필요하신가요?
```

### 예시 4: 없는 데이터 처리

**입력**:
```
화성 탐사 데이터 찾아줘
```

**답변**:
```
죄송합니다. 공공데이터 포털에서 해당 주제의 데이터셋을 찾을 수 없습니다.
```

---

## 기술 스택

### Backend

- **Framework**: FastAPI
- **LLM**: AWS Bedrock (Google Gemma 3 27B)
- **Embedding**: Amazon Titan Embed Text v1
- **Vector DB**: FAISS (3,143개 데이터셋)
- **Orchestration**: LangGraph
- **RAG**: LangChain

### Frontend

- **Framework**: Streamlit
- **UI**: Streamlit Components

### DevOps

- **CI/CD**: GitHub Actions
- **Container**: Docker, Docker Compose
- **Registry**: Docker Hub
- **Hosting**: AWS EC2
- **OS**: Ubuntu

### 데이터

- **크롤링**: Selenium
- **처리**: Pandas, CSV
- **저장**: FAISS Index

---

## 성능 지표

| 항목 | 지표 |
|------|------|
| **RAG 사용률** | 100% |
| **환각 방지** | 100% |
| **URL 포함률** | 100% |
| **키워드 커버리지** | 45개 (+309%) |
| **"없음" 처리 정확도** | 80-100% |
| **배포 소요 시간** | 5-10분 |
| **데이터셋 수** | 3,143개 |

---

## 프로젝트 구조

```
DatasetExplorerAI/
├── Web/
│   ├── Back_end/          # FastAPI Backend
│   │   └── back_web.py
│   └── Front_end/         # Streamlit Frontend
│       └── front_web.py
├── LLM/
│   ├── agent_with_garph.py    # LangGraph Agent
│   ├── rag_store.py           # FAISS 검색 + 정렬
│   ├── tools.py               # RAG 도구
│   ├── faiss_dataset_db/      # 벡터 DB
│   └── README_COMPLETE.md     # 완성 문서
├── DevOps/
│   ├── dockerfiles/
│   │   ├── backend.Dockerfile
│   │   └── frontend.Dockerfile
│   └── cicd_guide.md          # CI/CD 가이드
├── archive/
│   └── crawling.py            # 크롤링 코드
├── .github/
│   └── workflows/
│       └── deploy.yml         # GitHub Actions
├── docker-compose.yml
├── requirements.txt
├── selenium_guide.md          # Selenium 가이드
└── README.md
```

---