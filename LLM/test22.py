import boto3
import os
from dotenv import load_dotenv

# 현재 파일 위치 기준으로 최상위 폴더의 .env 로드
current_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(current_dir, "..", ".env")
load_dotenv(dotenv_path)

def ask_claude(user_query):
    try:
        client = boto3.client(
            service_name="bedrock-runtime",
            region_name=os.getenv("AWS_REGION"),
            #aws_session_token=os.getenv("AWS_BEARER_TOKEN_BEDROCK")
        )
        
        response = client.converse(
            modelId=os.getenv("BEDROCK_MODEL_ID"),
            messages=[{"role": "user", "content": [{"text": user_query}]}],
            inferenceConfig={"maxTokens": 1024, "temperature": 0.5}
        )
        return response['output']['message']['content'][0]['text']
    except Exception as e:
        return f"❌ LLM 엔진 에러: {str(e)}"
    

# --- 코드 맨 밑에 추가 ---
if __name__ == "__main__":
    print("🚀 Claude 엔진 테스트를 시작합니다...")
    test_result = ask_claude("반가워! 내 이름은 Dell이야. 내 이름을 포함해서 인사해줘.")
    print("-" * 30)
    print(f"🤖 답변: {test_result}")
    print("-" * 30)