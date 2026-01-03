'''
MCP 기반 RAG 에이전트 모듈
LangChain MCP Adapter를 사용하여 외부 MCP 서버의 도구를 호출합니다.
'''
from dotenv import load_dotenv
import os
import asyncio
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate, MessagesPlaceholder
from langchain_aws import ChatBedrockConverse
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

# 1. LLM 등 기본 설정 (기존과 동일)
llm = ChatBedrockConverse(
    model       = os.getenv("BEDROCK_MODEL_ID"),
    region_name = os.getenv("AWS_REGION"),
    temperature = 0.1,
    max_tokens  = 1000
)

# [MCP 연결 설정]
# MCP 서버 스크립트 경로
current_dir = os.path.dirname(os.path.abspath(__file__))
mcp_server_script = os.path.join(current_dir, "mcp_server", "run_mcp_server.py") # [수정] 파일명 변경

import sys

mcp_server_params = StdioServerParameters( # [수정] 변수명 변경 (server_params -> mcp_server_params)
    command=sys.executable, # 현재 실행 중인 파이썬 인터프리터 사용
    args=[mcp_server_script],
    env=os.environ.copy()
)

async def call_mcp_tool(tool_name: str, arguments: dict):
    """
    MCP 서버에 연결하여 도구를 실행하고 결과를 받아옵니다.
    매 호출마다 연결을 맺고 끊습니다 (Stateless).
    """
    async with stdio_client(mcp_server_params) as (read, write): # [수정] 변수명 반영
        async with ClientSession(read, write) as session:
            # 도구 초기화
            await session.initialize()
            
            # 도구 실행 요청
            result = await session.call_tool(tool_name, arguments)
            
            # 결과 반환 (첫 번째 텍스트 콘텐츠)
            if result.content and len(result.content) > 0:
                return result.content[0].text
            return "도구 실행 결과가 비어있습니다."

# ... (프롬프트 설정 섹션은 기존 agent_with_garph.py와 동일하게 유지) ...
# 3. 퓨샷 프롬프트
examples = [
    {
        "input": "환경 데이터 추천해줘",
        "output": """1. **해양환경공단_해양환경 정보**
   - 제공기관: 해양환경공단
   - 분류: 환경기상 - 해양환경
   - 수정일: 2025-09-02
   - URL: https://www.data.go.kr/data/15002978/fileData.do

2. **해양환경공단_국가해양생태계종합조사 정보**
   - 제공기관: 해양환경공단
   - 분류: 환경기상 - 해양환경
   - 수정일: 2025-09-02
   - URL: https://www.data.go.kr/data/15012624/fileData.do"""
    }
]

example_format = ChatPromptTemplate.from_messages([
    ('human', "{input}"),
    ('ai', "{output}")
])

# 3. 퓨샷 프롬프트 (정의 복구)
few_shot_prompt = FewShotChatMessagePromptTemplate(
    examples=examples,
    example_prompt=example_format
)

# 4. 시스템 프롬프트
# 4. 시스템 프롬프트
final_prompt = ChatPromptTemplate.from_messages([
    ('system', '''당신은 "Dataset Explorer Agent"입니다. 공공데이터 포털(data.go.kr)의 데이터셋을 추천하는 전문 에이전트입니다.

**핵심 원칙**:
1. 사용자가 데이터셋을 요청하면 **반드시 MCP 도구(search_dataset)를 사용**하여 검색하세요.
2. 검색 결과가 있으면 그 결과를 기반으로 답변하세요.

**[매우 중요] 출처 표기 원칙**:
모든 답변의 **맨 마지막 줄**에 반드시 아래 태그 중 하나를 붙여야 합니다. 예외는 없습니다.

1. **MCP 도구(search_dataset)의 검색 결과를 인용한 경우**:
   > **[🔍 출처: 내부 데이터베이스 (FAISS)]**

2. **도구를 사용하지 않고 내 지식으로 답변한 경우 (인사, 일반 대화 등)**:
   > **[🤖 출처: AI 일반 지식]**

**응답 형식** (검색 결과 기반):
1. **데이터셋명**
   - 제공기관: XXX
   - 분류: XXX
   - 수정일: YYYY-MM-DD
   - URL: https://www.data.go.kr/...
'''),
    few_shot_prompt,
    MessagesPlaceholder(variable_name="messages")
])
# 5. 상태 정의
class AgentState(TypedDict, total=False):
    messages: List[BaseMessage]

# 6. 노드 정의

# 6-0. 라우팅 노드
def initial_routing_node(state: AgentState):
    messages = state["messages"]
    user_query = ""
    
    # [수정] 대화 히스토리 중 '가장 최근' 사용자 메시지를 확인해야 함
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_query = msg.content.lower()
            break
            
    dataset_keywords = ["찾아", "추천", "검색", "데이터", "자료", "목록", "알려줘"]
    
    print(f"\n🧠 [AI 사고 (Routing)] 사용자 입력 분석 중: '{user_query}'", flush=True)
    
    if any(keyword in user_query for keyword in dataset_keywords):
        print("   -> 💡 결정: '데이터 요청' 키워드 발견! -> [도구(Tools)] 사용", flush=True)
        return {"messages": messages, "_route": "tools"}
    
    print("   -> 💭 결정: 특별한 키워드 없음 -> [일반 대화(Thinking)] 진행", flush=True)
    return {"messages": messages, "_route": "thinking"}

# 6-1. Thinking Node (단순 대화)
def thinking_node(state: AgentState):
    messages = state["messages"]
    print(f"🤖 [AI 생성] 일반 지식으로 답변 생성 시작...", flush=True) # 터미널 로그 추가
    
    # [수정] 시스템 프롬프트 적용
    chain = final_prompt | llm
    res = chain.invoke({"messages": messages})
    return {"messages": [res]}

# 6-2. MCP Tool Node
async def tool_node(state: AgentState):
    messages = state["messages"]
    user_query = None
    
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_query = msg.content
            break
    
    tool_output = "검색할 쿼리가 없습니다."
    
    if user_query:
        print(f"🛠️ [MCP Tool] 도구 'search_dataset' 호출 준비 완료", flush=True)
        print(f"   -> 📥 입력 파라미터: query='{user_query}', k=5", flush=True)
        try:
            # [핵심] MCP 클라이언트를 통해 도구 호출 (비동기)
            tool_output = await call_mcp_tool("search_dataset", {"query": user_query, "k": 5})
            print(f"   -> ✅ 도구 실행 완료! 결과 길이: {len(tool_output)}자", flush=True)
        except Exception as e:
            tool_output = f"MCP 도구 호출 실패: {str(e)}"
            print(f"   -> ❌ 도구 실행 실패: {e}", flush=True)

    # 검색 결과를 컨텍스트에 포함
    return {"messages": [
        HumanMessage(content=f"""사용자 질문: {user_query}

[MCP 공공데이터 검색결과]:
{tool_output}

위 검색 결과를 바탕으로 사용자에게 데이터셋 정보를 정리해서 알려주세요.""")
    ]}

# 6-3. Final Answer Node
def final_answer_node(state: AgentState):
    final_msg = state["messages"]
    
    # [수정] 시스템 프롬프트 적용
    chain = final_prompt | llm
    res = chain.invoke({"messages": final_msg})
    return {"messages": [res]}

# 7. 그래프 연결
workflow = StateGraph(AgentState)
workflow.add_node("routing", initial_routing_node)
workflow.add_node("thinking", thinking_node)
workflow.add_node("tools", tool_node)
workflow.add_node("final_answer", final_answer_node)

workflow.set_entry_point("routing")

def route_decision(state: AgentState):
    return state.get("_route", "thinking")

workflow.add_conditional_edges("routing", route_decision, {"thinking": "thinking", "tools": "tools"})
workflow.add_edge("thinking", END) # 간단한 질문은 바로 종료
workflow.add_edge("tools", "final_answer")
workflow.add_edge("final_answer", END)

graph_object = workflow.compile()
