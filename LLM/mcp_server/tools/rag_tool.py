import sys
import os

# 상위 폴더(LLM)의 모듈을 가져오기 위해 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__)) # plugins
mcp_server_dir = os.path.dirname(current_dir) # mcp_server
llm_dir = os.path.dirname(mcp_server_dir) # LLM
sys.path.append(llm_dir)

# 기존 RAG 로직 가져오기
from rag_store import search_stores

def search_dataset(query: str, k: int = 5) -> str:
    """
    공공데이터 포털의 데이터셋을 검색합니다.
    
    Args:
        query: 검색할 키워드 (예: "환경", "교통", "의료" 등)
        k: 검색할 결과 개수 (기본값: 5)
    """
    try:
        # 기존 search_stores 함수 재사용
        res = search_stores(query, k)
        return res if res else "검색 결과가 없습니다."
    except Exception as e:
        return f"검색 중 오류 발생: {str(e)}"

# 플러그인 등록 함수
def register(mcp):
    """MCP 서버에 도구를 등록합니다."""
    mcp.tool()(search_dataset)
