import requests

# 우리가 이미 성공했던 그 주소입니다!
url = 'https://api.odcloud.kr/api/15077093/v1/dataset'
SERVICE_KEY = "5048d6cd756445387f46dfbf5b5c506d5bc6a61f59b35a22e8793166d87cb279"

params = {
    'page': 1,
    'perPage': 5,
    'serviceKey': SERVICE_KEY,
    # ODCloud API의 비밀 병기: 특정 필드에 조건을 거는 방식입니다.
    #'cond[title::LIKE]': '주차장' ,
    'cond[keywords::LIKE]': '주차장'
}

try:
    response = requests.get(url, params=params)
    print(f"📡 보낸 주소 확인: {response.url}")
    
    if response.status_code == 200:
        data = response.json()
        items = data.get('data', [])
        print(f"✅ 검색 결과: {len(items)}건 발견!")
        print(f"📊 서버가 '주차장'으로 골라낸 전체 개수: {data.get('matchCount')}개")
        for item in items:
            print(f"- 제목: {item['title']}")
    else:
        print(f"❌ 실패: {response.status_code}")
except Exception as e:
    print(f"⚠️ 에러: {e}")