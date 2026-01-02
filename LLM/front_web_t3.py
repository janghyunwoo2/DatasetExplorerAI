import streamlit as st
import requests as req
import os

#a = 1
#print('사용자 입력후 엔티치면 계속 전체가 구동되는지 점검-')#, a)

# 전역설정
API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000/chat") # fastapi 주소
st.set_page_config(page_title='데이터셋 탐험가 AI 에이전트')#, page_icon='')
st.title('데이터셋 탐험가 AI 에이전트')
st.caption('원하는 데이터셋의 특징을 입력하면, Agent가 이를 이해하고 관련 데이터셋을 탐색합니다.')

# session state 초기화 -> 현재 코드가 몇번이고 재실행되더라고 데이터 유지,전역
if "messages" not in st.session_state: # 최초에는 아무것도 없음(1회만 수행됨)
    st.session_state.messages = [
        # 페르소나는 백엔드에서 구성
        {
            'role':'assistant',
            'content':'안녕하세요! 어떤 데이터셋이 필요하신가요?<br>(특징, 키워드 등을 통해 관련 데이터셋을 제공해 드립니다.)'
        }
    ]

# 이전 대화 내용 화면 출력
for msg in st.session_state.messages:
    # 존재하는 모든 대화 내용을 출력
    with st.chat_message(msg['role']): # assistant or user
        st.markdown(msg['content'], unsafe_allow_html=True)

# ui
# st.chat_input() -> 화면단에서 작성후 엔티치면 자동 호출됨
#prompt = st.chat_input('현재 상황을 자세히 입력하세요...')
#print( prompt )
# a += 1
#if prompt:
# 입력값을 받아서 -> 존재하면-> 작업 진행
# 대입 표현식(혹은 왈러스 연산자)
if prompt := st.chat_input('현재 상황을 자세히 입력하세요...') :
    # 사용자 질의 처리 진행
    # 1. 사용자의 입력 내용을 전역 상태 관리 변수에 추가
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    # 2. 사용자 입력후(방금 세션상태 변수에 추가된 내용) -> 마크다운표기
    # 화면에 방금 추가된 내용을 바로 반영하여 출력해라
    # st.chat_message('user') : 글 배경창 구성
    with st.chat_message('user'): # user로 고정햇음
        st.markdown(prompt) # 화면에 텍스트 내용을 출력한다!!
        pass

    # 3. LLM에게 문의 -> 서버 요청 -> bedrock 요청 -> bedrock 응답 
    #    -> 서버 응답 -> assistant의 응답
    with st.chat_message('assistant'):
        # msg_holder = st.empty()
        # msg_holder.markdown('데이터셋을 탐색하는 중입니다...🔍')
        with st.spinner('데이터셋을 탐색하는 중입니다...🔍'):
            # 3-1. 서버측 사용자의 질의 전송
            result = None     
            try:
                res = req.post(API_URL, json={"question":prompt})  
                if res.status_code == 200: # 응답 성공
                    result = res.json().get('response','응답 없음')                
                else:
                    result = f'서버측 오류 {res.status_code}'
                # 추후, 백엔드 구성후 교체
                #import time
                #time.sleep(2) # 서버 통신 시간을 시뮬레이션
                #res = "더미 응답 : 치킨으로 가보세요!!"
            except Exception as e:
                # 더미 구성
                print( e )
                result = "서버와 연결할 수 없습니다. 백엔드 서버가 켜져 있는지 확인해 주세요."
        # 3-2. 화면처리
        st.markdown( result )
        # 3-3. 전역 상태 관리 변수에 추가
        st.session_state.messages.append({
            "role":"assistant",
            "content":result
        })
        pass

    pass