# 1. 필요한 모듈 가져오기
from fastapi import FastAPI
from pydantic import BaseModel # 데이터를 담는 그릇(모델)을 만들기 위한 도구
from fastapi.middleware.cors import CORSMiddleware # 보안 허용을 위한 도구
from langchain_aws import ChatBedrock # AWS Bedrock을 쓰기 위한 도구
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import BedrockEmbeddings
from langchain_classic.chains import create_retrieval_chain
        

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

# 1. AI 모델 설정 (두뇌 준비)
# model_id는 사용할 AI의 이름입니다. 'anthropic.claude-3-sonnet' 등을 사용합니다.
llm = ChatBedrock(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    model_kwargs={"temperature": 0.1} # 0에 가까울수록 AI가 헛소리를 안 하고 정확해집니다.
)

# 2. AI에게 시킬 일 정의 (프롬프트 엔지니어링)
from langchain_core.prompts import ChatPromptTemplate

prompt_template = ChatPromptTemplate.from_messages([
    ("system", "당신은 데이터셋 전문가입니다. 사용자의 질문에 친절하게 답하세요."),
    ("user", "{input}")
])

# 1. 저장해둔 벡터 DB 불러오기
# (실제로 데이터를 수집해서 저장했다는 가정하에 진행합니다)
embeddings = BedrockEmbeddings() 
vector_db = FAISS.load_local("my_dataset_index", embeddings, allow_dangerous_deserialization=True)

# 2. 검색기(Retriever) 만들기
# 질문과 가장 비슷한 데이터셋 3개를 찾아오는 '검색 요원'입니다.
retriever = vector_db.as_retriever(search_kwargs={"k": 3})


# 1. 문서 요약 체인 만들기 (AI가 찾은 정보를 읽고 대답하는 로직)
combine_docs_chain = create_stuff_documents_chain(llm, prompt_template)

# 2. 최종 RAG 체인 (검색 요원 + 요약 로직 합치기)
rag_chain = create_retrieval_chain(retriever, combine_docs_chain)

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    # 사용자의 질문을 RAG 체인에 넣습니다.
    # invoke()는 "자, 이제 일 시작해!"라고 명령하는 함수입니다.
    response = rag_chain.invoke({"input": req.question})
    
    # AI가 최종적으로 생성한 답변은 'answer'라는 키에 담겨 있습니다.
    return {"response": response["answer"]}