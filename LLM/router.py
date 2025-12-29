# 판단 모듈
# 데이터셋을 vectordb에서 찾을것인가? llm으로 찾을것인가?

import json
from bedrock_utils import get_bedrock_client

def analyze_user_intent(user_query):
    client = get_bedrock_client()
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    system_prompt = """
    너는 데이터 탐험가야. 질문을 분석해서 JSON으로만 답해.
    형식: {"intent": "API 또는 VECTOR_DB", "keywords": ["키워드"]}
    """

    response = client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": user_query}]}],
        system=[{"text": system_prompt}]
    )
    
    return response['output']['message']['content'][0]['text']