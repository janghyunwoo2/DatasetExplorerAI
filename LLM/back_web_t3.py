# 1. 필요한 도구들 가져오기
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

# ⭐ 시현 님이 만든 그래프 파일에서 모든 내용을 가져옵니다.
# (파일 이름이 agent_with_garph.py 가 맞는지 꼭 확인하세요!)
from agent_with_garph_t3 import graph_object # 2. 환경 변수 로드 (.env 파일 읽기)
load_dotenv()

# 3. 데이터 형식 정의 (프론트엔드와 맞춤)
class ChatRequest(BaseModel):
    question: str

# 4. FastAPI 앱 설정
app = FastAPI(title="데이터셋 탐험가 AI")

# 5. 보안 설정 (Streamlit 연결 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 6. 실제 대화 처리 구간
@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        # 사용자의 질문을 그래프가 이해할 수 있는 형식으로 만듭니다.
        prompt = {"messages": [HumanMessage(content=req.question)]}
        
        # 5번까지 재시도 하도록 설정
        config = {"recursion_limit": 5} 

        # ⭐ [중요] agent_with_garph.py에서 만든 랭그래프 객체 변수명을 'graph'라고 가정합니다.
        # 만약 그 파일에서 변수명이 'app'이나 'workflow'라면 아래 이름을 그것으로 바꾸세요.
        final_state = graph_object.invoke(prompt, config=config)
        
        # 마지막 AI의 답변만 추출합니다.
        res = final_state["messages"][-1].content
        
        return {"response": res}
        
    except Exception as e:
        print(f"에러 발생: {e}")
        return {"response": f"백엔드 오류가 발생했습니다: {str(e)}"}