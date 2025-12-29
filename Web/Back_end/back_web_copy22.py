import sys
import os
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# 경로 설정 (기존과 동일)
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from LLM.test22 import ask_claude

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# [핵심 수정] 프론트엔드가 보낸 {"prompt": "..."}를 받기 위해 이름을 'prompt'로 맞춥니다.
class ChatRequest(BaseModel):
    prompt: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # 이제 request.prompt 로 데이터를 꺼낼 수 있습니다.
    print(f"📥 [백엔드 수신 확인]: {request.prompt}")
    
    answer = ask_claude(request.prompt)
    
    print(f"📤 [백엔드 응답 완료]")
    return {"answer": answer}