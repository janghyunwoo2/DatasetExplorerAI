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

# 1. Bedrock 임베딩 객체 생성
embeddings = BedrockEmbeddings(
    client=boto3.client(
        service_name="bedrock-runtime",
        region_name=os.getenv("AWS_REGION")
    ),
    model_id="amazon.titan-embed-text-v1"
)

# 2. 기존 FAISS 데이터베이스 로드
# 절대 경로로 설정 (Web/Back_end에서도 접근 가능)
import os
script_dir = os.path.dirname(os.path.abspath(__file__))  # rag_store.py 파일 위치
DB_PATH = os.path.join(script_dir, "faiss_dataset_db")

try:
    vector_db = FAISS.load_local(
        DB_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )
    print(f"[OK] FAISS DB 로드 완료: {DB_PATH}")
except Exception as e:
    print(f"[ERROR] FAISS DB 로드 실패: {e}")
    raise

# 3. 질의 > 검색(키워드, 질의) > 유사도 순으로 후보 K개 반환
def search_stores(query: str, k: int=5):
    """
    FAISS DB에서 유사도 검색 수행 후 최신 데이터 우선 정렬
    
    Args:
        query: 검색 쿼리 (예: "의료 데이터")
        k: 반환할 결과 개수 (기본값: 5)
    
    Returns:
        검색 결과 문자열 (목록명, 제공기관, URL 포함, 최신순 정렬)
    """
    from datetime import datetime
    
    # 유사도 검색 (k*2개 가져와서 정렬 후 k개 반환)
    docs = vector_db.similarity_search(query, k=k*2)
    
    # 수정일 기준 정렬 (최신 순)
    def parse_date(date_str):
        """날짜 문자열을 datetime 객체로 변환"""
        if not date_str or date_str == 'N/A':
            return datetime.min
        try:
            # 다양한 날짜 형식 처리
            for fmt in ['%Y-%m-%d', '%Y%m%d', '%Y.%m.%d']:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except:
                    continue
            return datetime.min
        except:
            return datetime.min
    
    # 수정일 기준 정렬
    sorted_docs = sorted(
        docs,
        key=lambda x: parse_date(x.metadata.get('수정일', '')),
        reverse=True  # 최신순
    )
    
    # 상위 k개만 선택
    final_docs = sorted_docs[:k]
    
    results = []
    for i, doc in enumerate(final_docs, 1):
        result = f"{i}. {doc.metadata.get('목록명', 'N/A')}\n"
        result += f"   제공기관: {doc.metadata.get('제공기관', 'N/A')}\n"
        result += f"   분류: {doc.metadata.get('분류체계', 'N/A')}\n"
        result += f"   수정일: {doc.metadata.get('수정일', 'N/A')}\n"
        result += f"   URL: {doc.metadata.get('URL', 'N/A')}"
        results.append(result)
    
    return "\n\n".join(results)