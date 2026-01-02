"""
FAISS 데이터베이스 검증 스크립트
"""

import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_aws import BedrockEmbeddings
import boto3

# 환경 변수 로드
load_dotenv('DevOps/rag/teacher/.env')

print("=" * 60)
print("FAISS 데이터베이스 검증")
print("=" * 60)

# 1. Bedrock 임베딩 초기화
print("\n[1/3] Bedrock 임베딩 모델 초기화...")
embeddings = BedrockEmbeddings(
    client=boto3.client(
        service_name="bedrock-runtime",
        region_name=os.getenv("AWS_REGION")
    ),
    model_id="amazon.titan-embed-text-v1"
)
print("✅ 완료\n")

# 2. FAISS DB 로드
print("[2/3] FAISS 데이터베이스 로드 중...")
db_path = "DevOps/rag/data/faiss_dataset_db"

try:
    vector_db = FAISS.load_local(
        db_path,
        embeddings,
        allow_dangerous_deserialization=True
    )
    print(f"✅ 로드 완료: {db_path}\n")
except Exception as e:
    print(f"❌ 로드 실패: {e}")
    exit(1)

# 3. 테스트 검색
print("[3/3] 테스트 검색 수행")
print("-" * 60)

test_queries = [
    "의료 관련 데이터",
    "교통 정보",
    "환경 데이터"
]

for query in test_queries:
    print(f"\n🔍 검색어: '{query}'")
    results = vector_db.similarity_search(query, k=3)
    
    for i, doc in enumerate(results, 1):
        print(f"  {i}. {doc.metadata.get('목록명', 'N/A')[:50]}")
        print(f"     기관: {doc.metadata.get('제공기관', 'N/A')}")

print("\n" + "=" * 60)
print("✅ FAISS 데이터베이스 검증 완료!")
print("=" * 60)
