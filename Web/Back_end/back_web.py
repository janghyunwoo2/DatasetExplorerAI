# 1. 필요한 도구들 가져오기
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, AIMessage
import os
import json
from dotenv import load_dotenv

# 2. 외부 파일(그래프 설계도) 및 환경 변수 로드
from agent_with_garph import * 
load_dotenv()

# --- 대화 저장소 설정 ---
# 대화 내용을 저장할 파일의 이름입니다.
HISTORY_FILE = "chat_history.json"

# [설명] 서버가 처음 켜질 때, 기존에 저장된 채팅 파일을 읽어옵니다.
if os.path.exists(HISTORY_FILE):
    # 파일이 이미 있다면(과거 기록이 있다면) 열어서 내용을 가져옵니다.
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        chat_db = json.load(f)
else:
    # 파일이 없다면(처음 실행한다면) 빈 사전{}을 만듭니다.
    chat_db = {}

# 3. 데이터 형식 정의 (사용자가 보낼 데이터의 모양)
class LoginRequest(BaseModel):
    username: str # 사용자 이름
    password: str # 비밀번호

class ChatRequest(BaseModel):
    username: str # 질문하는 사람의 이름
    question: str # 질문 내용

# 4. FastAPI 앱 설정
app = FastAPI(title="데이터셋 탐험가 AI")

# 5. 보안 설정 (브라우저에서 접속 가능하도록 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 7. 로그인 처리 (간단한 예시)
@app.post("/login")
async def login_endpoint(req: LoginRequest):
    if req.username == "admin" and req.password == "1234":
        return {"message": "로그인 성공", "user": req.username}
    else:
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 틀렸습니다.")

# 6. 실제 대화 처리 및 기록 저장 구간
@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        user_id = req.username # 질문한 유저의 이름을 가져옵니다.
        user_q = req.question  # 질문 내용을 가져옵니다.

        # [핵심] 이 사용자의 대화방이 처음이라면 빈 리스트를 만들어줍니다.
        if user_id not in chat_db:
            chat_db[user_id] = []

        # 사용자의 질문을 'user' 역할로 저장합니다.
        chat_db[user_id].append({"role": "user", "content": user_q})

        # [설명] AI가 과거 대화를 이해할 수 있도록 LangChain 형식으로 변환합니다.
        messages_for_ai = []
        for msg in chat_db[user_id]:
            if msg["role"] == "user":
                # 사용자의 말은 HumanMessage로 변환
                messages_for_ai.append(HumanMessage(content=msg["content"]))
            else:
                # AI의 답변은 AIMessage로 변환
                messages_for_ai.append(AIMessage(content=msg["content"]))

        # AI에게 질문을 던집니다. (기록이 포함된 상태)
        prompt = {"messages": messages_for_ai}
        final_state = graph_object.invoke(prompt, config={"recursion_limit": 5})
        
        # AI의 답변 추출
        ai_res = final_state["messages"][-1].content

        # [핵심] AI의 답변도 이 사용자의 기록에 추가합니다.
        chat_db[user_id].append({"role": "assistant", "content": ai_res})

        # [중요] 업데이트된 대화 기록을 파일(JSON)에 실제로 저장합니다.
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            # chat_db 내용을 파일에 씁니다. (한글이 깨지지 않게 ensure_ascii=False 사용)
            json.dump(chat_db, f, ensure_ascii=False, indent=4)

        return {"response": ai_res}
        
    except Exception as e:
        print(f"에러 발생: {e}")
        return {"response": f"백엔드 오류가 발생했습니다: {str(e)}"}