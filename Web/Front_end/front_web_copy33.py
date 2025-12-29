import streamlit as st
import requests

# 1. 페이지 제목 및 레이아웃 설정
st.set_page_config(page_title="따릉이 데이터 탐험가", page_icon="🚲")
st.title("🚲 데이터셋 탐험가 에이전트")
st.caption("FastAPI와 Claude 3.5 Sonnet을 이용한 데이터 질의응답 시스템")
st.markdown("---")

# 2. 채팅창 구현
if prompt := st.chat_input("Claude에게 궁금한 점을 물어보세요!"):
    
    # 사용자가 입력한 메시지 화면에 표시
    with st.chat_message("user"):
        st.write(prompt)

    # 어시스턴트(AI)의 답변 영역
    with st.chat_message("assistant"):
        with st.spinner("백엔드 서버를 통해 Claude의 답변을 가져오는 중..."):
            try:
                # [중요] 백엔드(main_api)의 /chat 엔드포인트로 데이터 전송
                # 백엔드 코드의 ChatRequest 규격에 맞춰 "prompt" 키를 사용합니다.
                response = requests.post(
                    "http://127.0.0.1:8000/chat",
                    json={"prompt": prompt},
                    timeout=60  # LLM의 긴 답변을 고려하여 60초 대기
                )
                
                # 응답 성공 시 (HTTP 200)
                if response.status_code == 200:
                    # 백엔드에서 리턴한 {"answer": "..."} 데이터 추출
                    answer = response.json().get("answer")
                    st.write(answer)
                else:
                    st.error(f"❌ 백엔드 응답 실패 (코드: {response.status_code})")
                    st.info("백엔드 터미널 창의 에러 메시지를 확인해 주세요.")

            except requests.exceptions.ConnectionError:
                st.error("❌ 백엔드 서버(FastAPI)에 연결할 수 없습니다.")
                st.info("Uvicorn 서버가 http://127.0.0.1:8000 에서 실행 중인지 확인하세요.")
            except Exception as e:
                st.error(f"❌ 오류 발생: {e}")

# 하단 안내 문구
st.sidebar.info("백엔드 서버가 켜져 있어야 정상적으로 작동합니다.")