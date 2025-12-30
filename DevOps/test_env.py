import pandas as pd
import os
import google.generativeai as genai
from dotenv import load_dotenv

# .env 로드
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
api_key = os.getenv("GOOGLE_API_KEY")

print("--- 1. CSV 인코딩 테스트 ---")
csv_path = r"c:\Users\Jang_home\Desktop\git tool\DatasetExplorerAI\DevOps\etl\data\공공데이터활용지원센터_공공데이터포털 목록개방현황_20251130.csv"

encodings = ['utf-8', 'cp949', 'euc-kr']
for enc in encodings:
    try:
        df = pd.read_csv(csv_path, encoding=enc, nrows=1)
        print(f"✅ {enc} 성공!")
        break
    except Exception as e:
        print(f"❌ {enc} 실패: {e}")

print("\n--- 2. Gemini 모델 리스트 테스트 ---")
try:
    genai.configure(api_key=api_key)
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    print(f"✅ 가용 모델: {models}")
except Exception as e:
    print(f"❌ 모델 리스트 획득 실패: {e}")

print("\n--- 3. Gemini 직접 호출 테스트 ---")
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content('hi')
    print(f"✅ gemini-1.5-flash 응답 성공: {response.text}")
except Exception as e:
    print(f"❌ gemini-1.5-flash 호출 실패: {e}")
