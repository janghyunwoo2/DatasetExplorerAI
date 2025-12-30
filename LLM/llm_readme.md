# test.py
    - llm(aws bedrock - claude 3.5)과 연동되는지 확인
      - 임의의 프롬프트 생성 (mock_chat)
      - 답변까지 출력완료
      - python test.py


# test22.py
    - llm(aws bedrock - claude 3.5)연동 모듈화 연습
      - 임의의 프롬프트 -> 사용자 입력 프롬프트로 받아보기
        - back_web_copy22.py 생성
          - fastapi
        - front_web_copy33.py 생성
          - streamlit
      - streamlit에서 입력받은 채팅을 fastapi로 잘 받아온다.
      - llm에 받아온 채팅을 프롬프트로 잘 넘겨준다.
      - llm이준 답변을 잘 받아온다.
      - fastapi로 streamlit에 넘겨서 화면에 출력해준다.
  
# test33.py
    - 모듈화가 잘 되었는지 테스트 해보는 파일
      - test22.py에서 ask_aws_bedrock_claude 함수를 가져와서 llm과 연동이 잘 되는지 테스트


# my_explorer.py

# router.py

# bedrock_utils.py
    - aws bedrock 연결 모듈화 클로드 사용(anthropic.claude-3-5-sonnet-20240620-v1:0)