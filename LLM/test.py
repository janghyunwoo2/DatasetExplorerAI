import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

bedrock_client = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.getenv("AWS_REGION"),
    aws_session_token=os.getenv("AWS_BEARER_TOKEN_BEDROCK")
)

def ask_aws_bedrock_claude_mcp_style(user_query):
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    # 1. 메시지 구성
    messages = [
        {
            "role": "user",
            "content": [{"text": user_query}]
        }
    ]

    try:
        # 2. Converse API 호출
        response = bedrock_client.converse(
            modelId=model_id,
            messages=messages,
            inferenceConfig={
                "maxTokens": 1024,
                "temperature": 0.5,
            }
        )

        # 3. 답변 추출
        response_text = response['output']['message']['content'][0]['text']
        return response_text

    except Exception as e:
        return f"❌ 에러 발생: {e}"

# ---------------------------------------------------------
# [수정된 부분] 따릉이 더미 데이터
# ---------------------------------------------------------
mock_chat = "서울시 따릉이 대여소 위치랑 실시간 대여 가능 수량 데이터를 API로 받고 싶어. 어떤 데이터셋을 검색해야 돼?"

print(f"💬 사용자 질문(더미): {mock_chat}")
print("🤖 Claude 분석 중 (따릉이 탐색)...")

answer = ask_aws_bedrock_claude_mcp_style(mock_chat)

print("-" * 30)
print(f"✅ AI 답변:\n{answer}")