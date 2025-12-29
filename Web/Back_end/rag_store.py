'''
- RAG 기반 검색 기능 제공
- FAISS 등록된 식당/메뉴/가격 정보를 벡터 형태로 제공
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
# 2. 더미 음식점 데이터 (차후, 실데이터 교체 필요)
data = [
    "가게명: 스파이시 웍, 메뉴: 마라탕, 꿔바로우, 특징: 아주 매움, 스트레스 풀림, 가격: 15000원",
    "가게명: 헬시 샐러드, 메뉴: 닭가슴살 샐러드, 샌드위치, 특징: 다이어트, 가벼움, 신선함, 가격: 9000원",
    "가게명: 엄마손 백반, 메뉴: 김치찌개, 제육볶음, 특징: 집밥 스타일, 가성비, 든든함, 가격: 8000원",
    "가게명: 골든 스시, 메뉴: 초밥 세트, 우동, 특징: 고급스러움, 깔끔함, 월급날 추천, 가격: 25000원",
    "가게명: 해장국 천국, 메뉴: 뼈해장국, 순대국, 특징: 국물 진함, 비 오는 날 추천, 가격: 10000원"
]
# 3. 데이터 > 벡터화 > FAISS 저장
vector_db = FAISS.from_texts(data,embedding=tokenizer)

# 4. 질의 > 검색(키워드, 질의) > 유사도 순으로 후보 K개 반환
def search_stores(query:str, k:int=2):
    docs = vector_db.similarity_search(query,k)
    return "\n".join([ doc.page_content for doc in docs ])