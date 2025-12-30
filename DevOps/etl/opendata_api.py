import requests
import json
import pprint # JSON 데이터를 예쁘게 출력하기 위해 사용해요. [【3】](https://codealone.tistory.com/51)
import os
from dotenv import load_dotenv
load_dotenv()

# --- 1. 필수 설정 ---
# 발급받으신 '일반인증키(Decoding)'을 여기에 입력해주세요.
# 공공데이터포털 '마이페이지 > 활용현황'에서 확인 가능해요!
SERVICE_KEY = os.getenv("OPENAPI_KEY")
print(SERVICE_KEY)
# 공공데이터포털 API의 기본 URL
BASE_URL = "https://api.odcloud.kr/api"

# --- 2. 호출하려는 특정 API의 엔드포인트(URL 경로) ---
# 이 부분은 '활용신청'한 API 서비스의 상세 페이지에서 확인해야 해요.
# 예시 엔드포인트 (Ref: 2에서 가져온 임의의 공공데이터 엔드포인트)
# 실제 사용하려는 API 서비스에 따라 '/서비스코드/버전/서비스_아이디' 형식으로 구성됩니다.
API_ENDPOINT = "/15062804/v1/uddi:9b49b1b0-6d33-458b-90a8-8edefa6ae757" 

# --- 3. 요청 파라미터 설정 ---
# API마다 필수 파라미터가 다를 수 있으니, API 명세서를 꼭 확인해주세요!
params = {
    'serviceKey': SERVICE_KEY,  # 필수: 발급받은 인증키
    'page': 1,                  # 선택: 요청할 페이지 번호 (기본값 1)
    'perPage': 10,              # 선택: 한 페이지당 결과 수 (기본값 10)
    'returnType': "json"        # 선택: 응답 데이터 형식 (xml, json 중 선택)
}

# --- 4. API 요청 보내기 ---
try:
    # BASE_URL과 API_ENDPOINT를 합쳐 최종 요청 URL을 만듭니다.
    full_url = BASE_URL + API_ENDPOINT
    print(f"🔗 요청 URL: {full_url}")
    print(f"⚙️ 요청 파라미터: {params}")

    # requests.get() 메서드로 GET 요청을 보냅니다.
    response = requests.get(full_url, params=params, timeout=10) # timeout 설정으로 무한 대기 방지

    # --- 5. 응답 확인 및 데이터 파싱 ---
    if response.status_code == 200: # HTTP 상태 코드가 200이면 성공적으로 응답을 받은 거예요.
        print("\n✅ API 요청 성공!")
        
        # 응답 내용을 JSON 형태로 파싱합니다.
        json_data = response.json()
        
        # pprint를 사용하여 파싱된 JSON 데이터를 보기 좋게 출력합니다. [【3】](https://codealone.tistory.com/51)
        pprint.pprint(json_data)
        
        # 여기에서 추출된 json_data를 현우님의 필요에 맞게 가공하거나 저장할 수 있어요.
        # 예시: 특정 키의 값만 가져오기
        # if "data" in json_data and isinstance(json_data["data"], list) and len(json_data["data"]) > 0:
        #     first_item = json_data["data"][0]
        #     print(f"\n첫 번째 데이터 항목: {first_item}")
        
    else:
        # 요청 실패 시 상태 코드와 에러 메시지를 출력합니다.
        print(f"\n❌ API 요청 실패! 상태 코드: {response.status_code}")
        print(f"🚨 응답 메시지: {response.text}")

except requests.exceptions.Timeout:
    print("\n⏰ 요청 시간 초과! 네트워크 연결 상태를 확인하거나 timeout 값을 늘려보세요.")
except requests.exceptions.RequestException as e:
    print(f"\n🚫 API 요청 중 예외 발생: {e}")
except json.JSONDecodeError as e:
    print(f"\n⚠️ JSON 파싱 오류! 응답 내용이 JSON 형식이 아닙니다. 오류: {e}")
    print(f"원시 응답 텍스트 (앞부분): {response.text[:500]}...") # 어떤 데이터가 왔는지 확인