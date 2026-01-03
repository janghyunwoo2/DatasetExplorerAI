from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, AIMessage
import os
import json
import sys
from dotenv import load_dotenv

# LLM 폴더 경로 추가 (agent_with_garph.py를 불러오기 위해)
current_dir = os.path.dirname(os.path.abspath(__file__))  # Web/Back_end
project_root = os.path.dirname(os.path.dirname(current_dir))  # DatasetExplorerAI
llm_path = os.path.join(project_root, "LLM")
sys.path.insert(0, llm_path)

# ⭐ LLM 폴더에서 에이전트 가져오기 (MCP 적용 버전)
# LangChain Agent (MCP + LangGraph)
# [수정] 파일명 변경 반영 (agent_mcp -> agent_graph_mcp)
from agent_graph_mcp import graph_object
# from agent_with_garph import graph_object # (구버전 백업)

# 2. 환경 변수 로드 (.env 파일 읽기)
load_dotenv()

# 2. 앱 객체 생성
app = FastAPI(title="데이터셋 탐험가 AI")

# --- 저장소 파일 이름 설정 ---
HISTORY_FILE = "chat_history.json" # 대화 내용 저장용
USER_DB_FILE = "users.json"       # [추가] 사용자 아이디/비번 저장용

# [설명] 서버가 켜질 때 1번 실행: 기존 대화 기록 로드
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        chat_db = json.load(f)
else:
    chat_db = {}

# [추가] 서버가 켜질 때 2번 실행: 기존 유저 목록 로드
if os.path.exists(USER_DB_FILE):
    with open(USER_DB_FILE, "r", encoding="utf-8") as f:
        users_db = json.load(f)
else:
    # 파일이 없으면 기본 관리자만 있는 상태로 시작
    users_db = {"admin": "1234"}

# 3. 데이터 형식 정의
class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    username: str
    question: str

# 4. 보안 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 기능 시작 ---

# 5. 대화 기록 불러오기 기능
@app.get("/history/{username}")
async def get_history(username: str):
    # [수정] 요청 시마다 최신 파일 내용 읽기
    current_db = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                current_db = json.load(f)
        except:
            current_db = {}
            
    if username in current_db:
        return {"history": current_db[username]}
    return {"history": []}

# 6. [수정] 로그인 및 자동 회원가입 기능
@app.post("/login")
async def login_endpoint(req: LoginRequest):
    user_id = req.username
    user_pw = req.password

    # [로직 변경] 유저가 이미 있다면?
    if user_id in users_db:
        # 비밀번호가 맞는지 확인
        if users_db[user_id] == user_pw:
            return {"message": "로그인 성공", "user": user_id}
        else:
            # 아이디는 있는데 비번이 틀리면 에러!
            raise HTTPException(status_code=401, detail="비밀번호가 틀렸습니다.")
    
    # [로직 변경] 유저가 없다면? (신규 유저 자동 등록)
    else:
        # 장부(메모리)에 적고
        users_db[user_id] = user_pw
        # 파일(users.json)에도 바로 저장!
        with open(USER_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(users_db, f, ensure_ascii=False, indent=4)
        
        return {"message": "신규 계정 생성 및 로그인 성공", "user": user_id}


# 7. 대화 및 저장 기능
@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        user_id = req.username
        user_q = req.question

        # [수정] 요청 시마다 최신 파일 내용 읽기 (동기화)
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    chat_db = json.load(f)
            except:
                chat_db = {}
        else:
            chat_db = {}

        if user_id not in chat_db:
            chat_db[user_id] = []

        chat_db[user_id].append({"role": "user", "content": user_q})

        # [수정] 과거 기록 중 최근 8개만 가져와서 컨텍스트에 포함
        # 1. 현재 사용자 쿼리 저장 (이전 단계에서 이미 chat_db에 저장됨)
        
        # 2. 최근 8개 대화 추출 (방금 저장한 사용자 질문 포함)
        recent_history = chat_db[user_id][-8:] 
        
        messages_for_ai = []
        for msg in recent_history:
            if msg["role"] == "user":
                messages_for_ai.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages_for_ai.append(AIMessage(content=msg["content"]))
                
        # (주의: 이미 recent_history에 현재 질문이 포함되어 있으므로 별도로 추가 X)

        # AI에게 질문을 던집니다.
        prompt = {"messages": messages_for_ai}
        # [수정] MCP 에이전트(혹은 비동기 노드)를 위해 ainvoke 사용
        final_state = await graph_object.ainvoke(prompt, config={"recursion_limit": 5})
        
        # AI의 답변 추출
        ai_res = final_state["messages"][-1].content

        # [핵심] AI의 답변도 이 사용자의 기록에 추가합니다.
        chat_db[user_id].append({"role": "assistant", "content": ai_res})

        # 대화 내용도 파일(chat_history.json)에 저장!
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(chat_db, f, ensure_ascii=False, indent=4)

        return {"response": ai_res}
        
    except Exception as e:
        # [요청사항] 터미널에 에러 상세 출력
        print(f"🔥 백엔드 에러 발생: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return {"response": f"백엔드 오류: {str(e)}"}