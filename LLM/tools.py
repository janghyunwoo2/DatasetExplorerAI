'''
각종 툴을 모은 모듈
'''
from langchain_core.tools import tool
from rag_store import search_stores

@tool
def rag_search(query: str, k: int = 5) -> str:
    '''
    데이터셋 검색 쿼리를 입력받고, FAISS RAG를 이용해 유사도 검색 수행
    
    Args:
        query: 검색할 데이터셋 키워드 (예: "의료", "교통", "환경")
        k: 반환할 데이터셋 개수 (기본값: 5)
    
    Returns:
        검색된 데이터셋 정보 (목록명, 제공기관, 분류, URL)
    '''
    try:
        # FAISS DB에서 RAG 검색 수행
        res = search_stores(query, k)
        return res if res else "관련 데이터셋 정보를 찾을 수 없습니다."
    except Exception as e:
        return f"검색 중 오류 발생: {str(e)}"
