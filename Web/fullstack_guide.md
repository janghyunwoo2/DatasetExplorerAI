# 풀스택 (FastAPI + Streamlit) 가이드

> 📄 **Backend**: [Web/Back_end/back_web.py](file:///C:/Users/3571/Desktop/projects/DatasetExplorerAI/Web/Back_end/back_web.py)  
> 📄 **Frontend**: [Web/Front_end/front_web.py](file:///C:/Users/3571/Desktop/projects/DatasetExplorerAI/Web/Front_end/front_web.py)

---

## 목차

1. [시스템 개요](#1-시스템-개요)
2. [Backend (FastAPI)](#2-backend-fastapi)
3. [Frontend (Streamlit)](#3-frontend-streamlit)
4. [통신 구조](#4-통신-구조)
5. [실행 방법](#5-실행-방법)

---

## 1. 시스템 개요

### 아키텍처

```
Streamlit (8501)  <-- REST API -->  FastAPI (8000)  <-->  LangGraph Agent
```

### 핵심 기능

- **Backend (FastAPI)**: REST API 서버, Agent 연결, 사용자 인증
- **Frontend (Streamlit)**: 웹 UI, 채팅 인터페이스, 세션 관리

---

## 2. Backend (FastAPI)

### 2-1. 핵심 기능

#### LLM 폴더 Import ⭐⭐⭐

> 📄 [back_web.py:L10-L17](file:///C:/Users/3571/Desktop/projects/DatasetExplorerAI/Web/Back_end/back_web.py#L10-L17)

```python
# LLM 폴더 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))  # Web/Back_end
project_root = os.path.dirname(os.path.dirname(current_dir))  # DatasetExplorerAI
llm_path = os.path.join(project_root, "LLM")
sys.path.insert(0, llm_path)

# Agent 가져오기
from agent_with_garph import graph_object
```

**핵심**: 상대 경로로 LLM 폴더의 Agent import

#### 자동 회원가입 ⭐⭐

> 📄 [back_web.py:L70-L93](file:///C:/Users/3571/Desktop/projects/DatasetExplorerAI/Web/Back_end/back_web.py#L70-L93)

```python
@app.post("/login")
async def login_endpoint(req: LoginRequest):
    # 기존 사용자 → 비밀번호 확인
    if user_id in users_db:
        if users_db[user_id] == user_pw:
            return {"message": "로그인 성공"}
        else:
            raise HTTPException(status_code=401)
    
    # 신규 사용자 → 자동 등록
    else:
        users_db[user_id] = user_pw
        with open(USER_DB_FILE, "w") as f:
            json.dump(users_db, f, ensure_ascii=False, indent=4)
        return {"message": "신규 계정 생성 및 로그인 성공"}
```

#### 대화 처리 ⭐⭐⭐

> 📄 [back_web.py:L95-L127](file:///C:/Users/3571/Desktop/projects/DatasetExplorerAI/Web/Back_end/back_web.py#L95-L127)

```python
@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    # 1. 대화 히스토리 생성
    messages_for_ai = []
    for msg in chat_db[user_id]:
        if msg["role"] == "user":
            messages_for_ai.append(HumanMessage(content=msg["content"]))
        else:
            messages_for_ai.append(AIMessage(content=msg["content"]))
    
    # 2. Agent 호출
    prompt = {"messages": messages_for_ai}
    final_state = graph_object.invoke(prompt, config={"recursion_limit": 5})
    ai_res = final_state["messages"][-1].content
    
    # 3. 응답 저장
    chat_db[user_id].append({"role": "assistant", "content": ai_res})
    with open(HISTORY_FILE, "w") as f:
        json.dump(chat_db, f, ensure_ascii=False, indent=4)
    
    return {"response": ai_res}
```

### 2-2. API 엔드포인트

#### POST `/login` - 로그인/회원가입

```json
// Request
{
  "username": "user123",
  "password": "pass1234"
}

// Response
{
  "message": "로그인 성공",
  "user": "user123"
}
```

#### GET `/history/{username}` - 대화 기록 조회

```json
// Response
{
  "history": [
    {"role": "user", "content": "교육 데이터 찾아줘"},
    {"role": "assistant", "content": "..."}
  ]
}
```

#### POST `/chat` - 대화

```json
// Request
{
  "username": "user123",
  "question": "의료 데이터 추천해줘"
}

// Response
{
  "response": "1. **의료기관 개설현황**..."
}
```

---

## 3. Frontend (Streamlit)

### 3-1. 핵심 기능

#### 환경 변수 기반 연결 ⭐⭐

> 📄 [front_web.py:L5-L8](file:///C:/Users/3571/Desktop/projects/DatasetExplorerAI/Web/Front_end/front_web.py#L5-L8)

```python
# 환경 변수로 Backend URL 설정
BASE_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
API_URL = f"{BASE_URL}/chat"
LOGIN_URL = f"{BASE_URL}/login"
```

**효과**: 로컬/Docker 환경 자동 감지

#### 세션 상태 관리 ⭐⭐⭐

> 📄 [front_web.py:L14-L19](file:///C:/Users/3571/Desktop/projects/DatasetExplorerAI/Web/Front_end/front_web.py#L14-L19)

```python
# 로그인 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
```

#### 대화 기록 복원 ⭐⭐

> 📄 [front_web.py:L40-L53](file:///C:/Users/3571/Desktop/projects/DatasetExplorerAI/Web/Front_end/front_web.py#L40-L53)

```python
# 로그인 성공 시
st.session_state.logged_in = True

# 백엔드에서 과거 대화 기록 가져오기
history_url = f"{BASE_URL}/history/{user_input}"
hist_res = req.get(history_url)

if hist_res.status_code == 200:
    history_data = hist_res.json().get("history", [])
    st.session_state.messages = [
        {'role':'assistant', 'content':'안녕하세요!'}
    ] + history_data
```

### 3-2. 화면 구성

#### 사이드바 (로그인)

```python
with st.sidebar:
    st.header("로그인")
    
    # 로그인 전
    if not st.session_state.logged_in:
        with st.form("login_form"):
            user_input = st.text_input("아이디")
            pass_input = st.text_input("비밀번호", type="password")
            submitted = st.form_submit_button("로그인")
    
    # 로그인 후
    else:
        st.write(f"접속 중: **{st.session_state.username}**")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()
```

#### 메인 화면 (채팅)

```python
# 대화 출력
for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])

# 사용자 입력
if prompt := st.chat_input('질문을 입력하세요...'):
    # 로그인 확인
    if not st.session_state.logged_in:
        st.warning("로그인 후 대화 가능")
        st.stop()
    
    # API 호출
    res = req.post(API_URL, json={
        "username": st.session_state.username,
        "question": prompt
    })
    result = res.json().get('response')
    
    # 응답 출력
    st.markdown(result)
```

---

## 4. 통신 구조

### 로그인 플로우

```
Frontend                    Backend
   |                           |
   |-- POST /login ----------->|
   |   {username, password}    |
   |                           |
   |<---- 로그인 성공 ---------|
   |   {message, user}         |
   |                           |
   |-- GET /history/{user} --->|
   |                           |
   |<---- 대화 기록 ----------|
   |   {history: [...]}        |
```

### 대화 플로우

```
Frontend                    Backend                  Agent
   |                           |                       |
   |-- POST /chat ------------>|                       |
   |   {username, question}    |                       |
   |                           |-- invoke() ---------> |
   |                           |   messages            |
   |                           |                       |
   |                           |<---- AI response -----|
   |                           |                       |
   |<---- {response} ----------|                       |
   |                           |                       |
   |                           |-- save to JSON -----> |
```

---

## 5. 실행 방법

### 로컬 실행

#### Backend

```bash
cd Web/Back_end
uvicorn back_web:app --reload --port 8000
```

접속: http://localhost:8000  
API 문서: http://localhost:8000/docs

#### Frontend

```bash
cd Web/Front_end
streamlit run front_web.py
```

접속: http://localhost:8501

### Docker 실행

```bash
# 전체 실행
docker-compose up -d

# 접속
# Frontend: http://localhost:8501
# Backend: http://localhost:8000
```

### 환경 변수

**.env 파일**:
```bash
# Backend
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=google.gemma-3-27b-it
AWS_BEARER_TOKEN_BEDROCK=your-token

# Frontend (Docker 환경)
FASTAPI_URL=http://backend-service:8000
```

---

## 6. 데이터 저장

### Backend 저장 파일

| 파일 | 내용 | 저장 시점 |
|------|------|-----------|
| `chat_history.json` | 대화 내용 | 매 대화 종료 시 |
| `users.json` | 사용자 정보 | 로그인/회원가입 시 |

### 저장 형식

**chat_history.json**:
```json
{
  "user123": [
    {"role": "user", "content": "교육 데이터 찾아줘"},
    {"role": "assistant", "content": "..."}
  ]
}
```

**users.json**:
```json
{
  "admin": "1234",
  "user123": "pass1234"
}
```

---

## 핵심 요약

| 구분 | Backend | Frontend |
|------|---------|----------|
| **Framework** | FastAPI | Streamlit |
| **Port** | 8000 | 8501 |
| **주요 기능** | API 서버, Agent 연결 | 웹 UI, 채팅 |
| **인증** | 자동 회원가입 | 세션 상태 관리 |
| **저장** | JSON 파일 | 세션 (메모리) |
| **통신** | REST API | requests |
| **환경 변수** | AWS 인증 정보 | FASTAPI_URL |

---

📄 **코드**:
- [Web/Back_end/back_web.py](file:///C:/Users/3571/Desktop/projects/DatasetExplorerAI/Web/Back_end/back_web.py)
- [Web/Front_end/front_web.py](file:///C:/Users/3571/Desktop/projects/DatasetExplorerAI/Web/Front_end/front_web.py)
