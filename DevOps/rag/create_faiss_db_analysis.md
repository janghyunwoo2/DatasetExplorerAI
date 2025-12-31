# 📊 `create_faiss_db.py` 코드 분석

## 🎯 전체 구조 (5단계)

```
[1/5] Bedrock 초기화 → [2/5] CSV 읽기 → [3/5] 배치 처리 → [4/5] 병합 → [5/5] 테스트
```

---

## 📝 단계별 상세 분석

### **[1/5] Bedrock 임베딩 초기화** (27-36줄)

```python
embeddings = BedrockEmbeddings(
    client=boto3.client(
        service_name="bedrock-runtime",
        region_name=os.getenv("AWS_REGION")
    ),
    model_id="amazon.titan-embed-text-v1"
)
```

**목적:**
- AWS Bedrock의 Titan 임베딩 모델 초기화
- 텍스트를 벡터로 변환하는 엔진 준비

**중요 포인트:**
- `.env` 파일에서 `AWS_REGION` 가져옴
- `amazon.titan-embed-text-v1` 모델 사용

---

### **[2/5] CSV 데이터 읽기** (38-77줄)

```python
for idx, row in enumerate(reader):
    description = row.get('설명', '')
    if not description.strip():
        description = f"{row.get('목록명', '')} {row.get('키워드', '')}"
```

**핵심 전략:**
- ✅ **설명 필드만 임베딩** (`page_content`)
- ✅ **나머지는 메타데이터** 저장 (목록명, 제공기관, URL 등)

**왜 이렇게?**
1. 설명이 검색에 가장 중요
2. 메타데이터는 임베딩 안 해도 검색 결과에 포함 가능
3. API 호출 효율성 ↑

**Document 구조:**
```python
Document(
    page_content="데이터셋 설명...",  # 임베딩됨
    metadata={
        "목록명": "...",
        "제공기관": "...",
        "URL": "...",
        # ... 12개 필드
    }
)
```

---

### **[3/5] 배치 처리** (79-116줄)

```python
BATCH_SIZE = 100  # 100개씩 처리
total_batches = 32  # 3,143개 → 32개 배치

for batch_idx in range(total_batches):
    batch_docs = documents[start_idx:end_idx]
    
    # 배치별 FAISS DB 생성
    batch_db = FAISS.from_documents(
        documents=batch_docs,
        embedding=embeddings
    )
    
    # 임시 저장
    batch_db.save_local(f"temp_batches/batch_{batch_idx}")
```

**배치 처리 이유:**
1. **메모리 효율**: 한 번에 전체 처리 시 메모리 부족 가능
2. **안정성**: 중간에 실패해도 이미 처리된 배치는 저장됨
3. **진행 상황 확인**: 각 배치마다 진행률 표시

**저장 위치:**
```
DevOps/rag/data/temp_batches/
├── batch_0/
├── batch_1/
├── ...
└── batch_31/
```

---

### **[4/5] 배치 병합** (118-159줄)

```python
# 첫 번째 배치 로드
final_db = FAISS.load_local(batch_db_paths[0], embeddings)

# 나머지 배치 병합
for batch_path in batch_db_paths[1:]:
    batch_db = FAISS.load_local(batch_path, embeddings)
    final_db.merge_from(batch_db)  # 핵심!
```

**`merge_from()` 메서드:**
- FAISS의 벡터 인덱스를 병합
- 모든 Document를 하나의 DB로 통합

**최종 저장:**
```python
final_db.save_local("DevOps/rag/data/faiss_dataset_db")
```

**정리:**
```python
shutil.rmtree(temp_dir)  # 임시 배치 폴더 삭제
```

---

### **[5/5] 테스트 검색** (161-182줄)

```python
test_query = "의료 데이터"
test_results = final_db.similarity_search(test_query, k=5)

for doc in test_results:
    print(doc.metadata.get('목록명'))
    print(doc.metadata.get('제공기관'))
```

**검증 항목:**
- ✅ DB 로드 성공
- ✅ 검색 기능 작동
- ✅ 메타데이터 정상 반환

---

## 💡 핵심 설계 포인트

### 1️⃣ **효율적 임베딩**
```
설명 필드만 임베딩 → API 호출 최소화
나머지는 메타데이터 → 검색 결과에 포함
```

### 2️⃣ **배치 처리 전략**
```
3,143개 → 32개 배치(100개씩)
각 배치 저장 → 안정성 ↑
모두 병합 → 하나의 DB
```

### 3️⃣ **FAISS 특징**
- 페이스북이 개발한 고속 유사도 검색 라이브러리
- 벡터 간 코사인 유사도로 검색
- `similarity_search(query, k=5)` → 상위 5개 반환

---

## 🎯 실행 흐름 요약

```
CSV 읽기 (3,143행)
    ↓
Document 생성 (설명 + 메타데이터)
    ↓
배치 1~32 (100개씩)
    ↓
각 배치 임베딩 & 저장
    ↓
32개 배치 병합
    ↓
최종 FAISS DB 저장
    ↓
테스트 검색
```

---

## 📌 주요 변수

| 변수 | 값 | 설명 |
|------|-----|------|
| `BATCH_SIZE` | 100 | 배치당 Document 수 |
| `total_batches` | 32 | 총 배치 개수 |
| `csv_file_path` | `split_data_01.csv` | 입력 CSV |
| `final_save_path` | `faiss_dataset_db` | 최종 저장 위치 |
| `temp_dir` | `temp_batches/` | 임시 저장 폴더 |

---

## 🔑 핵심 코드 스니펫

### Bedrock 초기화
```python
embeddings = BedrockEmbeddings(
    client=boto3.client(
        service_name="bedrock-runtime",
        region_name=os.getenv("AWS_REGION")
    ),
    model_id="amazon.titan-embed-text-v1"
)
```

### Document 생성
```python
doc = Document(
    page_content=description,  # 설명만 임베딩
    metadata={
        "목록명": row.get('목록명'),
        "제공기관": row.get('제공기관'),
        "URL": row.get('목록 URL'),
        # ... 기타 필드
    }
)
```

### 배치 처리
```python
for batch_idx in range(total_batches):
    batch_docs = documents[start_idx:end_idx]
    batch_db = FAISS.from_documents(batch_docs, embeddings)
    batch_db.save_local(f"{temp_dir}/batch_{batch_idx}")
```

### 병합
```python
final_db = FAISS.load_local(batch_db_paths[0], embeddings)
for batch_path in batch_db_paths[1:]:
    batch_db = FAISS.load_local(batch_path, embeddings)
    final_db.merge_from(batch_db)
```

### 검색
```python
results = final_db.similarity_search(query, k=5)
for doc in results:
    print(doc.metadata.get('목록명'))
    print(doc.page_content)
```

---

## 📚 참고 자료

- **FAISS**: https://github.com/facebookresearch/faiss
- **LangChain**: https://python.langchain.com/
- **AWS Bedrock**: https://aws.amazon.com/bedrock/
