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

# 3. 시스템 프롬프트 - thinking 노드용 (일반 대화 전용)
final_prompt = ChatPromptTemplate.from_messages([
    ('system', '''당신은 "Dataset Explorer Agent"입니다. 공공데이터 포털(data.go.kr)의 데이터셋을 추천하는 전문 에이전트입니다.

**중요: 이 노드는 일반 대화 전용입니다**
- 데이터셋 검색 도구(RAG)는 사용할 수 없습니다
- 일반적인 인사, 감사, 일상 대화만 처리하세요
-  **절대로 존재하지 않는 데이터셋을 만들어내지 마세요**

**응대 가이드**:

1. **일반 대화 (자연스럽게 응대)**:
   - 인사: "안녕하세요", "잘 지내?", "반가워요"
   - 감사: "고마워", "감사합니다"
   - 안부: "밥 먹었어?", "힘들어", "심심해"
   → 친절하게 응대하고 데이터셋 추천 서비스 안내

2. **애매한 질문** ("점심은?", "저녁", "날씨"):
   → "죄송하지만 저는 일반적인 질문에는 답변할 수 없습니다. 
      구체적인 데이터셋을 요청하시려면 '점심 관련 데이터 추천해줘' 같이 
      명확하게 질문해주세요!"

3. **명확한 데이터셋 요청** ("교육 데이터 찾아줘"):
   → 이 경우는 이 노드로 오지 않습니다 (라우팅 시스템이 처리)

**절대 금지**:
❌ 자체 지식으로 데이터셋 정보 제공
❌ 가짜 URL이나 데이터셋명 생성
❌ "~라는 데이터셋이 있습니다" 같은 답변

**허용**:
✅ 일반 대화 응대
✅ 데이터셋 검색 도움 안내
✅ "더 구체적으로 질문해주세요" 안내

목표: 친절하지만정확한 안내'''),
    ('human', '{messages}')
])

# 4. RAG 결과 분석용 프롬프트 - final_answer_node용
rag_result_prompt = ChatPromptTemplate.from_messages([
    ('system', '''당신은 RAG 검색 결과를 분석하는 전문가입니다.

**역할**: 공공데이터 포털 검색 결과와 사용자 질문을 비교하여 적절한 답변을 생성합니다.

**필수 지침**:
1. 검색 결과와 사용자 질문의 주제가 일치하는지 판단하세요

2. **주제가 불일치하면**:
   "죄송합니다. 공공데이터 포털에서 해당 주제의 데이터셋을 찾을 수 없습니다."

3. **주제가 일치하면** 반드시 다음 형식으로 답변:
   1. **데이터셋명**
      - 제공기관: XXX
      - 분류: XXX
      - 수정일: YYYY-MM-DD
      - URL: https://www.data.go.kr/... (필수!)

**중요**:
- URL은 절대 생략 금지
- 검색 결과에 없는 정보는 만들어내지 마세요
- 모든 데이터셋에 URL 필수 포함

목표: 정확하고 구조화된 데이터셋 정보 제공'''),
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
    
    # 검색 결과만 깔끔하게 반환 (프롬프트는 final_answer에서 처리)
    return {"messages":[
        HumanMessage(content=f"""사용자 질문: {user_query}

[공공데이터 포털 검색결과]:
{tool_output}""")
    ]}

    # 6-3. 검색결과를 바탕으로 최종답변(추론) 생성
def final_answer_node(state:AgentState):
    # RAG 결과 분석 프롬프트 체인 구성
    messages = state["messages"]
    chain = rag_result_prompt | llm
    res = chain.invoke({"messages": messages})
    return {"messages": [res]}


# 6-0. 초기 라우팅 노드
def initial_routing_node(state:AgentState):
    """
    데이터셋 검색 키워드 감지 → RAG 사용
    키워드 없음 → 일반 질문 (thinking)
    """
    messages = state["messages"]
    
    # 🔧 마지막(최신) HumanMessage 찾기 (웹 대화 히스토리 누적 대응)
    user_query = ""
    for msg in reversed(messages):  # 뒤에서부터 검색
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