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
from tools_t3 import rag_search

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

# 3. 퓨샷 프롬프트 > 참고용
examples =[
    {"input":"러닝 인구 데이터 찾아줘","output":"국가통계포털을 추천드립니다."},
    {"input":"국내 카페 지역 분포 데이터 찾아줘","output":"공공데이터 포털을 추천드립니다. 이외에도 카카오맵/네이버지도API를 통해 수집 가능합니다."}
]
example_format = ChatPromptTemplate.from_messages([
  ('human',"{input}"),
  ('ai',"{output}")
])
few_shot_prompt = FewShotChatMessagePromptTemplate(
  examples       = examples,
  example_prompt = example_format
)
# 4. 시스템 프롬프트
final_prompt = ChatPromptTemplate.from_messages([
    # 페르소나
    # 도구사용 > 현재 RAG > RAG에는 LLM이 모르는 식당정보가 준비됨
    ('system','''당신은 개발자에게 데이터셋을 제공하는 데이터 탐색 전문가입니다.
    사용자의 요청에 맞는 데이터셋을 추천하고, 필요하면 도구를 사용하여 데이터셋 출처를 찾으세요
    다음 지침을 엄격히 준수하여 답변하세요:
    1. 데이터 검색 시 반드시 '공공데이터포털(data.go.kr)'을 가장 먼저 확인하고 언급하세요.
    2. 만약 공공데이터포털에 원하는 데이터가 없거나 부족할 경우에만 국가통계포털(KOSIS), 구글데이터셋, 캐글데이터셋 출처를 차례대로 제안하세요.
    3. 답변은 항상 친절하고 전문적인 톤을 유지하세요.
    '''),
    # 퓨샷
    few_shot_prompt,
    ('human','{messages}')
])

# 5. 랭그래프 상태 (커스텀)
class AgentState(TypedDict):
    messages: List[BaseMessage]

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

    # 6-2. LLM이 도구사용을 결정 > 실제로 도구 사용 - RAG 호출(간단한 MCP개념)
def tool_node(state:AgentState):
    # 툴 사용 > RAG 이용한 검색증강
    last_msg = state["messages"][-1]
    # 툴 사용 체크
    if last_msg.tool_calls:
        tool = last_msg.tool_calls[0] # 등록된 도구가 1개 => 인덱스번호 0번
        tool_output = rag_search.invoke(tool["args"])
        # 검색 증강(벡터db 검색 > 유사도 1개 획득(가게) > 응답)
        # 사내 데이터 검색

    return {"messages":[
        HumanMessage(content=f"[사내데이터 검색결과]:{tool_output}\n 제공된 정보를 기반으로 최종 답변을 해주세요.")
    ]}

    # 6-3. 검색결과를 바탕으로 최종답변(추론) 생성
def final_answer_node(state:AgentState):
    # 최종 프롬프트 획득
    final_msg = state["messages"]
    print("final_msg",final_msg)
    # LLM 질의 > tool 필요없음
    res = llm.invoke(final_msg)
    return {"messages":[res]}


# 7. 랭그래프 연결
workflow = StateGraph(AgentState) # 에이전트 상태 그래프 연동
workflow.add_node("thinking",     thinking_node)
workflow.add_node("tools",        tool_node)
workflow.add_node("final_answer", final_answer_node)
workflow.set_entry_point("thinking") # 사용자 질의 후 최초 invoke 진입할 노드

def check_tool_node(state:AgentState): # 도구 사용여부 체크(LLM은 도구사용 거의 X)
    # LLM 마지막 응답 결과 추출 - 대화내용 중 마지막 내용은 LLM 대답
    last_msg = state["messages"][-1]
    print("1차 노드 수행 후 LLM 응답값 :", last_msg)
    print("1차 노드 수행 후 도구 사용여부 :", last_msg.tool_calls)
    if last_msg.tool_calls:
        return "tools" # 커스텀 지정값
    return END # LLM 답변으로 충분하다. 도구 사용 X, 대화 마무리
    
workflow.add_conditional_edges("thinking", check_tool_node) # 조건부 에지
workflow.add_edge("tools","final_answer")
workflow.add_edge("final_answer", END) # 추론과정 마무리

# 8. 랭그래프 컴파일 -> 워크 플로우 객체
# 랭그래프객체 => 전역변수
graph_object = workflow.compile()