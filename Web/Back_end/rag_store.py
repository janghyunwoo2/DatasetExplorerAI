'''
- RAG 기반 검색 기능 제공
- FAISS 등록된 정보를 벡터 형태로 제공
- 유사도 검색 기능 기본 제공
- LLM이 사용자 질의를 보고 직저 단변이 불가할 경우 > 도구 사용 요청 > RAG 통해 검색 > 내용 제공
'''
from langchain_community.vectorstores import FAISS
from langchain_aws import BedrockEmbeddings
import boto3
import os
from dotenv import load_dotenv
load_dotenv()

# 1. bedrock 임베딩 객체 생성
tokenizer = BedrockEmbeddings(
    client   = boto3.client(service_name ="bedrock-runtime",
                             region_name = os.getenv("AWS_REGION")),
    model_id = "amazon.titan-embed-text-v1"
)
# 2. 더미 데이터
data = [
    "데이터셋 제공 : 공공데이터 포털, 특징 : 한국어 지원, CSV 파일, URL : https://www.data.go.kr/data/15062804/fileData.do"
    "데이터셋 제공 : Google Dataset Search, 특징 : 한국어 지원, URL : https://datasetsearch.research.google.com/",
    "데이터셋 제공 : Kaggle Datasets, 특징 : 한국어 미지원, URL : https://www.kaggle.com/datasets",
    "데이터셋 제공 : UCI Machine Learning Repository, 특징 : 한국어 미지원, URL : https://archive.ics.uci.edu/ml/index.php"
]
# 3. 데이터 > 벡터화 > FAISS 저장
vector_db = FAISS.from_texts(data,embedding=tokenizer)

# 4. 질의 > 검색(키워드, 질의) > 유사도 순으로 후보 K개 반환
def search_stores(query:str, k:int=2):
    docs = vector_db.similarity_search(query,k)
    return "\n".join([ doc.page_content for doc in docs ])