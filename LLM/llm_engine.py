# llm_engine.py
from claude_client import get_claude_response

def ask_llm(prompt, task_type="analysis"):
    if task_type == "analysis":
        # 질문 분석을 위한 페르소나와 지시사항
        instruction = """
        너는 공공데이터 탐색 전문가야. 사용자의 질문을 분석해서 
        데이터셋 검색에 가장 적합한 핵심 키워드 3개를 쉼표(,)로 구분해서 뽑아줘.
        예: 서울시, 따릉이, 대여소
        """
        return get_claude_response(prompt, system_instruction=instruction)
    
    return get_claude_response(prompt)

# --- 여기서부터 테스트 코드 ---
if __name__ == "__main__":
    print("🚀 클로드 연동 테스트를 시작합니다...")
    
    # 테스트용 질문
    test_query = "요즘 배달 음식을 너무 많이 먹어서 식비가 걱정되는데 관련 통계가 있을까?"
    
    # 엔진 호출 (task_type을 analysis로 설정)
    result = ask_llm(test_query, task_type="analysis")
    
    print("\n" + "="*30)
    print(f"🔹 사용자 질문: {test_query}")
    print(f"🔸 클로드 분석 결과: {result}")
    print("="*30)
    
    if "에러" in result or "Error" in result:
        print("\n❌ 연동 실패: 에러 메시지를 확인하세요.")
    else:
        print("\n✅ 연동 성공! 클로드가 일을 하기 시작했습니다.")