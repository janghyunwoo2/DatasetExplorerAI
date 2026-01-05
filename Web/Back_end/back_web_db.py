from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, AIMessage
import os
import sys
import pymysql  # 1. 통역사(라이브러리) 불러오기
from dotenv import load_dotenv

# LLM 경로 및 에이전트 설정 (기존 코드 유지)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
llm_path = os.path.join(project_root, "LLM")
sys.path.insert(0, llm_path)

load_dotenv()
app = FastAPI(title="데이터셋 탐험가 AI")

# --- 2. MySQL 접속 정보 설정 (제시된 변수 그대로 사용) ---
db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '1234',  # 아까 성공했던 비밀번호
    'port': 3306,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor  # 결과값을 딕셔너리 형태로 편하게 받기 위한 설정
}

# --- 3. 데이터베이스 및 테이블 초기화 함수 ---
# 서버가 켜질 때 DB와 테이블이 없으면 자동으로 만들어줍니다.
def init_db():
    # 처음에 DB 자체를 만들기 위해 연결
    conn = pymysql.connect(host=db_config['host'], user=db_config['user'], 
                           password=db_config['password'], port=db_config['port'])
    with conn.cursor() as cursor:
        cursor.execute("CREATE DATABASE IF NOT EXISTS explorer_db")
    conn.close()

    # 만들어진 explorer_db에 접속해서 테이블 생성
    conn = pymysql.connect(**db_config, database='explorer_db')
    with conn.cursor() as cursor:
        # 유저 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username VARCHAR(50) PRIMARY KEY,
                password VARCHAR(100)
            )
        """)
        # 대화 기록 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50),
                role VARCHAR(20),
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()
    conn.close()

init_db()  # 서버 실행 시 초기화 실행

# --- 데이터 형식 정의 (기존 유지) ---
class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    username: str
    question: str

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- 4. 기능 수정 (SQL 적용) ---

@app.get("/history/{username}")
async def get_history(username: str):
    conn = pymysql.connect(**db_config, database='explorer_db')
    try:
        with conn.cursor() as cursor:
            # 해당 유저의 대화 내용을 시간순으로 가져옵니다.
            sql = "SELECT role, content FROM chat_history WHERE username = %s ORDER BY created_at"
            cursor.execute(sql, (username,))
            history = cursor.fetchall()
            return {"history": history}
    finally:
        conn.close()

@app.post("/login")
async def login_endpoint(req: LoginRequest):
    conn = pymysql.connect(**db_config, database='explorer_db')
    try:
        with conn.cursor() as cursor:
            # 1. 유저가 있는지 확인
            cursor.execute("SELECT password FROM users WHERE username = %s", (req.username,))
            user = cursor.fetchone()

            if user:
                # 유저가 있다면 비번 확인
                if user['password'] == req.password:
                    return {"message": "로그인 성공", "user": req.username}
                else:
                    raise HTTPException(status_code=401, detail="비밀번호가 틀렸습니다.")
            else:
                # 2. 유저가 없다면 신규 가입
                cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (req.username, req.password))
                conn.commit()
                return {"message": "신규 계정 생성 및 로그인 성공", "user": req.username}
    finally:
        conn.close()

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    conn = pymysql.connect(**db_config, database='explorer_db')
    try:
        # 1. 이전 대화 맥락을 DB에서 가져오기 (AI에게 전달용)
        with conn.cursor() as cursor:
            cursor.execute("SELECT role, content FROM chat_history WHERE username = %s ORDER BY created_at", (req.username,))
            past_messages = cursor.fetchall()

        messages_for_ai = []
        for msg in past_messages:
            if msg["role"] == "user":
                messages_for_ai.append(HumanMessage(content=msg["content"]))
            else:
                messages_for_ai.append(AIMessage(content=msg["content"]))
        
        # 현재 질문 추가
        messages_for_ai.append(HumanMessage(content=req.question))

        # AI 답변 생성
        final_state = graph_object.invoke({"messages": messages_for_ai}, config={"recursion_limit": 5})
        ai_res = final_state["messages"][-1].content

        # 2. 질문과 답변을 DB에 저장
        with conn.cursor() as cursor:
            sql = "INSERT INTO chat_history (username, role, content) VALUES (%s, %s, %s)"
            cursor.execute(sql, (req.username, "user", req.question))
            cursor.execute(sql, (req.username, "assistant", ai_res))
            conn.commit()

        return {"response": ai_res}
    except Exception as e:
        return {"response": f"백엔드 오류: {str(e)}"}
    finally:
        conn.close()