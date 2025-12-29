'''
각종 툴을 모은 모듈
'''
from langchain_core.tools import tool
from rag_store import search_stores

@tool
def rag_search(cate:str) -> str :
    '''
    특정 메뉴 카테고리 입력 받고, RAG 이용 > 유사도 검색 > 실제 식당 정보 등 반환
    '''
    # RAG 검색
    res = search_stores(cate) # 기본 2개
    return res if res else "관련 식당 정보를 찾을 수 없습니다."
