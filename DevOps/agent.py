import os
import pandas as pd
import operator
from typing import TypedDict, Annotated, List, Union
from dotenv import load_dotenv

# LLM은 OpenAI를 사용하고, 임베딩은 기존 Google을 유지하거나 OpenAI로 교체 가능합니다.
# 여기서는 사용자의 요청에 따라 LLM을 OpenAI로 전환합니다.
from langchain_openai import ChatOpenAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# 프로젝트 루트의 .env 로드
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# 1. API 키 설정
google_api_key = os.getenv("GOOGLE_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

# 임베딩 모델 (기존 구글 인덱스가 있다면 유지, 없다면 새로 생성)
# 만약 임베딩 할당량도 문제라면 OpenAIEmbeddings로 교체할 수 있습니다.
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001", 
    google_api_key=google_api_key
)

# [변경] OpenAI 모델 설정
llm = ChatOpenAI(
    model="gpt-4o", # 또는 "gpt-4-turbo"
    openai_api_key=openai_api_key,
    temperature=0,
)

INDEX_PATH = "faiss_index"
CSV_PATH = r"c:\Users\Jang_home\Desktop\git tool\DatasetExplorerAI\DevOps\etl\data\공공데이터활용지원센터_공공데이터포털 목록개방현황_20251130.csv"

# 2. '초고속 도서관' 로직 (파일 로드 및 폴백)
def setup_library():
    """
    저장된 FAISS 인덱스를 불러옵니다. 없을 경우 키워드 검색(Pandas)으로 대체합니다.
    인덱스 생성은 'ingest_data.py'를 통해 별도로 수행합니다.
    """
    df = pd.read_csv(CSV_PATH, encoding='utf-8', low_memory=False)
    df['search_text'] = df.apply(lambda x: 
        f"데이터셋명: {str(x['목록명'])}, 설명: {str(x['설명'])}, 키워드: {str(x['키워드'])}, 제공기관: {str(x['제공기관'])}", 
        axis=1
    ).fillna("정보 없음")
    
    vector_db = None
    
    # 1. 파일에서 인덱스 로드 시도
    if os.path.exists(INDEX_PATH):
        try:
            print(f"--- [도서관] 로컬 인덱스 로드 중 ({INDEX_PATH}) ---")
            vector_db = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
            print("✅ 인덱스 로드 성공!")
        except Exception as e:
            print(f"⚠️ 인덱스 로드 실패: {e}")
    else:
        print(f"💡 [알림] 저장된 인덱스 폴더('{INDEX_PATH}')가 없습니다.")
        print(f"💡 'python ingest_data.py'를 실행하여 인덱스를 먼저 생성하면 훨씬 정확한 검색이 가능합니다.")
        print(f"💡 현재는 키워드 기반 폴백 모드로 동작합니다.")
    
    return vector_db, df

vector_db, full_df = setup_library()

# 3. 상태 및 노드 정의
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    found_info: str

def search_node(state: AgentState):
    print("\n--- [조사팀] 데이터셋 찾는 중 ---")
    query = state["messages"][-1].content
    
    if vector_db:
        try:
            docs = vector_db.similarity_search(query, k=3)
            info = "\n\n".join([doc.page_content for doc in docs])
            print("- 벡터 검색으로 결과를 찾았습니다.")
            return {"found_info": info}
        except:
            pass
            
    mask = full_df['search_text'].str.contains(query, case=False, na=False)
    matched = full_df[mask].head(3)
    
    if not matched.empty:
        info = "\n\n".join(matched['search_text'].tolist())
        print(f"- 키워드 검색으로 {len(matched)}개를 찾았습니다.")
    else:
        info = "관련된 데이터셋을 찾을 수 없습니다."
        
    return {"found_info": info}

def analyze_node(state: AgentState):
    print("--- [에이전트] 추천 답변 생성 중 (OpenAI 사용) ---")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 '데이터셋 탐험가 에이전트'입니다. 
        검색된 정보를 바탕으로 사용자에게 가장 적합한 데이터셋을 추천하세요.
        검색된 정보가 부족하더라도 아는 범위 내에서 최선을 다해 가이드하세요.
        """),
        ("placeholder", "{messages}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "messages": state["messages"],
        "found_info": state["found_info"]
    })
    
    return {"messages": [response]}

# 4. 그래프 구성
workflow = StateGraph(AgentState)
workflow.add_node("searcher", search_node)
workflow.add_node("analyzer", analyze_node)
workflow.set_entry_point("searcher")
workflow.add_edge("searcher", "analyzer")
workflow.add_edge("analyzer", END)
app = workflow.compile()

# 실행 테스트
if __name__ == "__main__":
    test_q = "날씨나 미세먼지 관련 데이터셋이 뭐야?"
    print(f"🚀 요청: {test_q}")
    
    inputs = {"messages": [HumanMessage(content=test_q)]}
    for output in app.stream(inputs):
        for key, value in output.items():
            if key == "analyzer":
                print(f"\n✅ 에이전트 추천 (OpenAI):\n{value['messages'][-1].content}")
