from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from agent_with_garph import *

app = FastAPI(title="식사 메뉴 추천 에이전트")

class UserRequest(BaseModel):
    question:str

@app.post('/chat')
async def llm_endpoint( req:UserRequest):
    try:
        prompt = {"messages":[HumanMessage(content=req.question)]}
        # 재시도 컨셉 => 
        config = {"recursion_limit":5} # 최초 요청 실패하면 최대 5회까지 다시 시도함

        final_state = 랭그래프객체.invoke(prompt,config=config)
        res = final_state["messages"][-1].content
        return {"response":res}
    except Exception as e:
        return {"response":f"오류발생 {str(e)}"}