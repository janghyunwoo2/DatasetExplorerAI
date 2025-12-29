# 1. 필요한 모듈 가져오기
from fastapi import FastAPI
from pydantic import BaseModel # 데이터를 담는 그릇(모델)을 만들기 위한 도구
from fastapi.middleware.cors import CORSMiddleware # 보안 허용을 위한 도구

# 1. 프론트엔드에서 보낼 데이터의 형식을 정의합니다.
class ChatRequest(BaseModel):
    question: str  # "질문은 문자열(str)로 올 거야"라고 선언하는 것

# 2. FastAPI 객체 생성 -> 변수명 중요(기억)
app = FastAPI()

# 2. 다른 주소(Streamlit)에서 오는 요청을 허용하는 설정입니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 모든 주소의 접근을 허용함 (테스트용)
    allow_methods=["*"], # GET, POST 등 모든 통신 방식 허용
    allow_headers=["*"], # 모든 데이터 형식 허용
)

# 3. /chat 주소로 들어오는 POST 요청을 처리합니다.
@app.post("/chat")
def chat_endpoint(req: ChatRequest): # 위에서 만든 ChatRequest 그릇에 데이터를 담음
    
    # 사용자가 보낸 질문 출력 (터미널에서 확인용)
    print(f"사용자의 질문: {req.question}")
    
    # 여기에 나중에 LangChain이나 AI 로직이 들어갈 자리입니다.
    # 지금은 일단 잘 받았다는 의미로 대답을 돌려줍니다.
    ai_answer = f"백엔드에서 받은 답변: '{req.question}'에 대해 열심히 찾고 있어요!"
    
    return {"response": ai_answer}