import os
import pandas as pd
import time
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS

# .env 로드
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

INDEX_PATH = "faiss_index"
CSV_PATH = r"c:\Users\Jang_home\Desktop\git tool\DatasetExplorerAI\DevOps\etl\data\공공데이터활용지원센터_공공데이터포털 목록개방현황_20251130.csv"

def ingest():
    print("🚀 FAISS 인덱스 사전 생성 시작...")
    
    # 1. 데이터 로드
    df = pd.read_csv(CSV_PATH, encoding='utf-8', low_memory=False)
    df['search_text'] = df.apply(lambda x: 
        f"데이터셋명: {str(x['목록명'])}, 설명: {str(x['설명'])}, 키워드: {str(x['키워드'])}, 제공기관: {str(x['제공기관'])}", 
        axis=1
    ).fillna("정보 없음")
    
    # 2. 임베딩 설정
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001", 
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # 3. 인덱싱 (할당량 이슈를 고려하여 100개만 먼저 시도)
    # 팁: 유료 계정 할당량이 충분하다면 [:2000] 등으로 늘려보세요.
    sample_size = 100 
    texts = df['search_text'].tolist()[:sample_size]
    
    print(f"📦 {len(texts)}개의 데이터를 벡터화합니다. (잠시만 기다려주세요...)")
    
    try:
        vector_db = FAISS.from_texts(texts, embedding=embeddings)
        vector_db.save_local(INDEX_PATH)
        print(f"✨ 성공! '{INDEX_PATH}' 폴더에 인덱스가 저장되었습니다.")
        print("이제 agent.py를 실행하면 이 파일을 즉시 불러옵니다.")
    except Exception as e:
        print(f"❌ 실패: {e}")
        print("💡 구글 API 할당량이 부족한 상태입니다. 잠시 후 다시 시도해주세요.")

if __name__ == "__main__":
    ingest()
