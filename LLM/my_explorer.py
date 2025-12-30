import json
from router import analyze_user_intent
# from vector_tool import search_vector_db  <- 나중에 생기면 추가

def run_explorer(user_input):
    print(f"🤔 사용자 질문 분석 중: {user_input}")
    
    # 1. 판단 로직 호출
    decision_text = analyze_user_intent(user_input)
    decision = json.loads(decision_text)
    
    intent = decision.get("intent")
    keywords = decision.get("keywords")
    
    print(f"🎯 판단 결과: {intent} (키워드: {keywords})")

    # 2. 결과에 따른 분기
    if intent == "API":
        return f"실시간 API로 '{keywords}' 데이터를 가져옵니다... (기능 구현 예정)"
    else:
        return f"내부 문서를 검색합니다... (기능 구현 예정)"

if __name__ == "__main__":
    query = "서울시 따릉이 실시간 대여 현황 찾아줘"
    result = run_explorer(query)
    print(f"\n✅ 최종 결과: {result}")