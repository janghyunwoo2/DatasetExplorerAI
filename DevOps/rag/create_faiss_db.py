"""
CSV 데이터를 FAISS 벡터 데이터베이스로 변환하는 스크립트 (배치 처리 버전)
- 100개씩 배치 처리하여 메모리 및 시간 효율성 향상
- 각 배치마다 중간 저장
- 모든 배치를 하나의 FAISS DB로 병합
"""

import os
import csv
import boto3
import shutil
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_aws import BedrockEmbeddings
from langchain_core.documents import Document

# 환경 변수 로드
load_dotenv('DevOps/rag/teacher/.env')

# 배치 사이즈 설정
BATCH_SIZE = 100

print("=" * 60)
print("FAISS 벡터 데이터베이스 생성 (배치 처리 방식)")
print("=" * 60)

# 1. Bedrock 임베딩 객체 생성
print("\n[1/5] Bedrock 임베딩 모델 초기화 중...")
embeddings = BedrockEmbeddings(
    client=boto3.client(
        service_name="bedrock-runtime",
        region_name=os.getenv("AWS_REGION")
    ),
    model_id="amazon.titan-embed-text-v1"
)
print("✅ 초기화 완료\n")

# 2. CSV 파일 읽기
csv_file_path = "DevOps/rag/data/split_data_01.csv"
print(f"[2/5] CSV 파일 읽는 중: {csv_file_path}")

documents = []
try:
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for idx, row in enumerate(reader):
            description = row.get('설명', '')
            if not description.strip():
                description = f"{row.get('목록명', '')} {row.get('키워드', '')}"
            
            metadata = {
                "목록키": row.get('목록키', ''),
                "목록유형": row.get('목록유형', ''),
                "목록명": row.get('목록명', ''),
                "제공기관": row.get('제공기관', ''),
                "제공기관코드": row.get('제공기관코드', ''),
                "분류체계": row.get('분류체계', ''),
                "키워드": row.get('키워드', ''),
                "업데이트주기": row.get('업데이트 주기', ''),
                "제공형태": row.get('제공형태', ''),
                "등록일": row.get('등록일', ''),
                "수정일": row.get('수정일', ''),
                "URL": row.get('목록 URL', ''),
                "확장자": row.get('확장자(데이터포맷)', ''),
                "source": csv_file_path,
                "row_index": idx
            }
            
            doc = Document(page_content=description, metadata=metadata)
            documents.append(doc)
    
    print(f"✅ 총 {len(documents)}개의 문서 생성 완료\n")
    
except Exception as e:
    print(f"❌ CSV 읽기 오류: {e}")
    exit(1)

# 3. 배치 처리로 FAISS DB 생성
print(f"[3/5] 배치 처리 시작 (배치 크기: {BATCH_SIZE}개)")
total_batches = (len(documents) + BATCH_SIZE - 1) // BATCH_SIZE
print(f"총 {total_batches}개의 배치로 처리합니다\n")

batch_db_paths = []
temp_dir = "DevOps/rag/data/temp_batches"
os.makedirs(temp_dir, exist_ok=True)

try:
    for batch_idx in range(total_batches):
        start_idx = batch_idx * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, len(documents))
        batch_docs = documents[start_idx:end_idx]
        
        print(f"배치 {batch_idx + 1}/{total_batches}: Document {start_idx+1}~{end_idx} 처리 중...")
        
        # 배치별 FAISS DB 생성
        batch_db = FAISS.from_documents(
            documents=batch_docs,
            embedding=embeddings
        )
        
        # 배치 저장
        batch_path = f"{temp_dir}/batch_{batch_idx}"
        batch_db.save_local(batch_path)
        batch_db_paths.append(batch_path)
        
        print(f"✅ 배치 {batch_idx + 1} 완료 및 저장: {batch_path}")
        print(f"   진행률: {end_idx}/{len(documents)} ({end_idx*100//len(documents)}%)\n")
    
    print("✅ 모든 배치 처리 완료!\n")
    
except Exception as e:
    print(f"❌ 배치 처리 오류: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 4. 모든 배치 병합
print(f"[4/5] FAISS 데이터베이스 병합 중...")
print(f"{len(batch_db_paths)}개의 배치를 하나로 병합합니다...\n")

try:
    # 첫 번째 배치 로드
    print("첫 번째 배치 로드 중...")
    final_db = FAISS.load_local(
        batch_db_paths[0],
        embeddings,
        allow_dangerous_deserialization=True
    )
    print(f"✅ 배치 1 로드 완료")
    
    # 나머지 배치 병합
    for i, batch_path in enumerate(batch_db_paths[1:], start=2):
        print(f"배치 {i} 병합 중...")
        batch_db = FAISS.load_local(
            batch_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
        final_db.merge_from(batch_db)
        print(f"✅ 배치 {i} 병합 완료")
    
    print("\n✅ 모든 배치 병합 완료!\n")
    
    # 최종 DB 저장
    final_save_path = "DevOps/rag/data/faiss_dataset_db"
    final_db.save_local(final_save_path)
    print(f"✅ 최종 FAISS DB 저장 완료: {final_save_path}\n")
    
    # 임시 배치 파일 삭제
    print("임시 배치 파일 정리 중...")
    shutil.rmtree(temp_dir)
    print("✅ 정리 완료\n")
    
except Exception as e:
    print(f"❌ 병합 오류: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 5. 테스트 검색
print("[5/5] 테스트 검색 수행")
print("-" * 60)

test_query = "의료 데이터"
test_results = final_db.similarity_search(test_query, k=5)

print(f"검색어: '{test_query}'")
print(f"검색 결과: {len(test_results)}건\n")

for i, doc in enumerate(test_results, 1):
    print(f"{i}. 📊 {doc.metadata.get('목록명', 'N/A')}")
    print(f"   🏢 제공기관: {doc.metadata.get('제공기관', 'N/A')}")
    print(f"   📁 분류: {doc.metadata.get('분류체계', 'N/A')}")
    print(f"   🔗 URL: {doc.metadata.get('URL', 'N/A')}")
    print()

print("=" * 60)
print("✅ 모든 작업 완료!")
print(f"최종 저장 위치: {final_save_path}")
print(f"총 문서 수: {len(documents)}")
print("=" * 60)
