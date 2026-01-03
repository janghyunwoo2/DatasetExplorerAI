import streamlit as st
import requests as req
import os

# 전역 설정 - FASTAPI_URL을 base URL로 사용
BASE_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
API_URL = f"{BASE_URL}/chat"
LOGIN_URL = f"{BASE_URL}/login"


st.set_page_config(page_title='데이터셋 탐험가 AI 에이전트')
st.title('데이터셋 탐험가 AI 에이전트')

# --- [추가] 로그인 상태를 관리하는 변수 초기화 ---
# 로그인이 되었는지, 누구인지 기억하기 위해 사용합니다.
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# 사이드바 구성
with st.sidebar:    
    st.header("로그인")
    
    # 로그인 전이라면 로그인 폼을 보여줍니다.
    if not st.session_state.logged_in:
        with st.form("login_form"):
            user_input = st.text_input("아이디")
            pass_input = st.text_input("비밀번호", type="password")
            submitted = st.form_submit_button("로그인")
            
            if submitted:
                try:
                    res = req.post(LOGIN_URL, json={"username": user_input, "password": pass_input})
                    if res.status_code == 200:
                        # [중요] 로그인이 성공하면 세션 상태에 저장합니다.
                        st.session_state.logged_in = True
                        st.session_state.username = user_input
                        
                        # [추가] 백엔드에서 과거 대화 기록을 가져옵니다.
                        try:
                            # API_URL에서 '/chat'을 떼고 '/history/{user_input}'을 붙임
                            history_url = API_URL.replace("/chat", f"/history/{user_input}")
                            hist_res = req.get(history_url)
                            
                            if hist_res.status_code == 200:
                                history_data = hist_res.json().get("history", [])
                                if history_data:
                                    st.session_state.messages = [
                                        {'role':'assistant', 'content':'안녕하세요! 어떤 데이터셋이 필요하신가요?'}
                                    ] + history_data
                        except Exception as e:
                            print(f"기록 불러오기 실패: {e}")

                        st.success(f"{user_input}님 환영합니다!")
                        st.rerun() # 화면을 새로고침하여 로그인 정보를 반영합니다.
                    else:
                        st.error(f"로그인 실패: {res.status_code}")
                except Exception as e:
                    st.error(f"연결 오류: {e}")
    else:
        # 로그인 후라면 로그아웃 버튼이나 사용자 정보를 보여줍니다.
        st.write(f"현재 접속 중: **{st.session_state.username}**")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.messages = [
                {'role':'assistant', 'content':'안녕하세요! 어떤 데이터셋이 필요하신가요?'}
            ]
            st.rerun()

# --- 대화 기록 초기화 ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {'role':'assistant', 'content':'안녕하세요! 어떤 데이터셋이 필요하신가요?'}
    ]

# 이전 대화 출력
for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'], unsafe_allow_html=True)

# --- 채팅 입력란 ---
if prompt := st.chat_input('현재 상황을 자세히 입력하세요...'):
    # 1. 로그인이 안 되어 있다면 입력을 막습니다.
    if not st.session_state.logged_in:
        st.warning("로그인 후에 대화를 시작할 수 있습니다.")
        st.stop()

    # 2. 사용자 메시지 화면 출력 및 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message('user'):
        st.markdown(prompt)

    # 3. AI 응답 처리
    with st.chat_message('assistant'):
        with st.spinner('데이터셋을 탐색하는 중입니다...🔍'):
            try:
                # [수정 포인트] 백엔드 설계도(ChatRequest)에 맞춰 username과 question을 모두 보냅니다.
                chat_data = {
                    "username": st.session_state.username, 
                    "question": prompt
                }
                res = req.post(API_URL, json=chat_data)
                
                if res.status_code == 200:
                    result = res.json().get('response', '응답 없음')
                else:
                    # 상세 에러 메시지를 확인하기 위해 res.text를 출력해볼 수 있습니다.
                    result = f'서버 오류: {res.status_code} - {res.text}'
            except Exception as e:
                result = f"연결 오류가 발생했습니다: {e}"

        # 4. 결과 출력 및 저장
        st.markdown(result)
        st.session_state.messages.append({"role": "assistant", "content": result})