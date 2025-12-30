# claude_client.py
import os
import anthropic
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수에서 가져오기
api_key = os.getenv("ANTHROPIC_API_KEY")
model_name = os.getenv("CLAUDE_MODEL")

client = anthropic.Anthropic(api_key=api_key)

def get_claude_response(prompt, system_instruction="너는 공공데이터 검색 전문가야."):
    try:
        message = client.messages.create(
            model=model_name,
            max_tokens=1024,
            system=system_instruction,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"Claude 연결 에러: {str(e)}"