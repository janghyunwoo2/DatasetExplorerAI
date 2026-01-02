'''
랭그래프 기반 LLM 사용에 대한 모듈
'''
from dotenv import load_dotenv
import os
load_dotenv()

from typing import TypedDict, List
from langgraph.graph import StateGraph, END, MessagesState, START
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_aws import ChatBedrockConverse, ChatBedrock
from langgraph.prebuilt import ToolNode, tools_condition
from tools import rag_search

# 1. LLM 모델 구성
llm = ChatBedrockConverse(
    model       = os.getenv("BEDROCK_MODEL_ID"),
    region_name = os.getenv("AWS_REGION"),
    temperature = 0.1,
    max_tokens  = 1000
    )
# 2. 외부 도구 가져오기 및 LLM 등록
tools = [rag_search]
llm_with_tools = llm.bind_tools(tools)

# 3. 퓨샷 프롬프트 - 응답 형식 가이드 (패턴 영향 최소화)
examples = [
    {
        "input": "환경 데이터 추천해줘",
        "output": 
"""
1. **해양환경공단_해양환경 정보**
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

few_shot_prompt = FewShotChatMessagePromptTemplate(
    examples=examples,
    example_prompt=example_format
)
# 4. 시스템 프롬프트 - RAG 우선 전략
final_prompt = ChatPromptTemplate.from_messages([
    ('system', '''당신은 "Dataset Explorer Agent"입니다. 공공데이터 포털(data.go.kr)의 데이터셋을 추천하는 전문 에이전트입니다.

**핵심 원칙**:
1. 사용자가 데이터셋을 요청하면 **먼저 RAG 검색 도구를 사용**하여 공공데이터 포털을 검색하세요
2. RAG 검색 결과가 있으면 그 결과를 기반으로 답변하세요
3. RAG 검색 결과가 없지만 자체 지식에 관련 정보가 있으면 자체 지식으로 답변하세요
4. RAG에도 없고 자체 지식에도 없으면 "해당 주제의 데이터셋을 찾을 수 없습니다"라고 답변하세요

**우선순위**:
1순위: RAG 도구로 공공데이터 포털 검색
2순위: 자체 지식 (RAG에 없을 때만)
3순위: "데이터 없음" 응답

**예외 (RAG 불필요)**:
- 데이터 전처리, 활용 방법 등 일반적인 질문
- 이미 제시된 데이터셋 간 비교

**응답 형식** (RAG 검색 결과):
1. **데이터셋명**
   - 제공기관: XXX
   - 분류: XXX
   - 수정일: YYYY-MM-DD
   - URL: https://www.data.go.kr/...

**중요**:
- 데이터셋 요청 시 RAG 도구를 우선 사용하세요
- 검색 결과에 수정일을 반드시 포함하여 최신성 표시

정확한 정보 제공이 목표입니다.'''),
    
    # 응답 형식 가이드
    few_shot_prompt,
    ('human', '{messages}')
])

# 5. 랭그래프 상태 (커스텀)
from typing import Optional

class AgentState(TypedDict, total=False):
    messages: List[BaseMessage]
    _route: Optional[str]

# 6. 노드 정의
    # 6-1. 사용자의 질의를 받고 생각하는 단계 구성(메뉴추천 +도구사용여부 결정)
def thinking_node(state:AgentState):
        # 6-1-1. 현재 상태의 프롬프트 실제 내용 획득(페르소나+퓨삿+사용자질의)
    messages = state["messages"]
        # 6-1-2. 랭체인 구성(prompt+llm) > 랭그래프 특정 노드에 랭체인 결합
    chain = final_prompt | llm_with_tools
        # 6-1.3. LLM 질의요청
    res = chain.invoke({"messages":messages})
    return {"messages":[res]}

    # 6-2. 강제 RAG 호출 노드
def tool_node(state:AgentState):
    """
    데이터셋 검색 시 강제로 RAG를 호출
    """
    messages = state["messages"]
    user_query = None
    
    #사용자 메시지 찾기
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_query = msg.content
            break
    
    # RAG 검색 실행
    if user_query:
        print(f"🔍 RAG 검색 실행: {user_query}")
        tool_output = rag_search.invoke({"query": user_query, "k": 5})
    else:
        last_msg = messages[-1]
        if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
            tool = last_msg.tool_calls[0]
            tool_output = rag_search.invoke(tool["args"])
        else:
            tool_output = "검색할 쿼리를 찾을 수 없습니다."
    
    return {"messages":[
        HumanMessage(content=f"""사용자 질문: {user_query}

[공공데이터 포털 검색결과]:
{tool_output}

**필수 지침 - 반드시 따르세요**:
1. 검색 결과와 사용자 질문의 주제가 일치하는지 판단하세요.

2. 주제가 불일치하면:
   "죄송합니다. 공공데이터 포털에서 해당 주제의 데이터셋을 찾을 수 없습니다."

3. 주제가 일치하면 **반드시 다음 형식**으로 답변하세요:
   1. **데이터셋명**
      - 제공기관: XXX
      - 분류: XXX
      - 수정일: YYYY-MM-DD
      - URL: https://www.data.go.kr/... (필수!)
   
   **중요**: URL은 절대 생략하면 안 됩니다! 모든 데이터셋에 URL을 반드시 포함하세요.""")
    ]}

    # 6-3. 검색결과를 바탕으로 최종답변(추론) 생성
def final_answer_node(state:AgentState):
    # 최종 프롬프트 획득
    final_msg = state["messages"]
    print("final_msg", final_msg)
    # LLM 질의 > tool 필요없음
    res = llm.invoke(final_msg)  # res 변수 정의 추가
    return {"messages": [res]}


# 6-0. 초기 라우팅 노드
def initial_routing_node(state:AgentState):
    """
    데이터셋 검색 키워드 감지 → RAG 사용
    키워드 없음 → 일반 질문 (thinking)
    """
    messages = state["messages"]
    
    # 첫 번째 HumanMessage 찾기
    user_query = ""
    for msg in messages:
        if isinstance(msg, HumanMessage):
            user_query = msg.content.lower()
            print(f"[ROUTING] 사용자 쿼리: {msg.content}")
            break
    
    # 데이터셋 검색 키워드 (포괄적)
    dataset_keywords = [
        # 동사
        "찾아", "찾기", "찾고", "찾을", "찾는",
        "추천", "추천해", "추천하", 
        "검색", "검색해",
        "보여", "보여줘", "보여주",
        "알려", "알려줘", "알려주",
        "구해", "구할", "구하고", "구하는",
        "원해", "원하는", "원하",
        "필요", "필요해", "필요한",
        "있어", "있나", "있는지", "있을",
        "줘", "주세요",
        # 명사
        "데이터", "데이타", "data", "dataset",
        "정보", "info", "information",
        "자료", "자료집",
        "통계", "통계자료", "통계치",
        "목록", "리스트", "list",
        "db", "database", "DB",
        # 기타
        "뭐", "무엇", "어디", "어떤"
    ]
    
    # 데이터셋 키워드가 있으면 RAG 사용
    if any(keyword in user_query for keyword in dataset_keywords):
        print("[ROUTING] 데이터셋 검색 감지 -> tools (RAG 사용)")
        return {"messages": messages, "_route": "tools"}
    
    # 키워드 없으면 일반 질문
    print("[ROUTING] 일반 질문 -> thinking")
    return {"messages": messages, "_route": "thinking"}


# 7. 랭그래프 연결
workflow = StateGraph(AgentState)
workflow.add_node("routing", initial_routing_node)
workflow.add_node("thinking", thinking_node)
workflow.add_node("tools", tool_node)
workflow.add_node("final_answer", final_answer_node)
workflow.set_entry_point("routing")

# 라우팅 조건
def route_decision(state:AgentState):
    route = state.get("_route", "thinking")
    print(f"[ROUTE] -> {route}")
    return route

workflow.add_conditional_edges(
    "routing",
    route_decision,
    {"thinking": "thinking", "tools": "tools"}
)

# thinking 후
def check_after_thinking(state:AgentState):
    last_msg = state["messages"][-1]
    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
        return "tools"
    return END

workflow.add_conditional_edges("thinking", check_after_thinking)
workflow.add_edge("tools", "final_answer")
workflow.add_edge("final_answer", END)

# 8. 컴파일
graph_object = workflow.compile()