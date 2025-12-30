# 같은 폴더에 있는 test22.py에서 ask_claude 함수를 가져옵니다.
from test22 import ask_claude

'''
def run_test():
    print("🚀 LLM 폴더 내부에서 단독 테스트를 시작합니다...")
    
    # 함수 호출
    question = "모듈화 테스트 중이야. 같은 폴더 내 임포트가 잘 되었니?"
    response = ask_claude(question)
    
    print("-" * 30)
    print(f"🤖 결과: {response}")
    print("-" * 30)

if __name__ == "__main__":
    run_test()
'''

print("✅ 연결 완료:", ask_claude("1+5은?"))