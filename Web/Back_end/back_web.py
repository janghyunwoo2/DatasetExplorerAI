# 1. 필요한 모듈 가져오기
from fastapi import FastAPI

# 2. FastAPI 객체 생성 -> 변수명 중요(기억)
app = FastAPI()

# 3. 라우팅 구성
# 라우팅 : 유저가 요청하면(url이 전달) 
# -> 이를 분석(해석) -> 어떤함수가 처리할지 연결(전달)
@app.post("/chat") # 요청이 하나 왔는데 get방식으로 홈페이지(/) 요청
def home():
    # 응답 -> dict 형태 -> json 형식
    return { "response":"hello fastapi!!"}