# data_loader.py
import pandas as pd

file_path = "C:\Users\Dell3571\Desktop\projects\DatasetExplorerAI\archive\공공데이터활용지원센터_공공데이터포털 목록개방현황_20251130.csv"

def check_csv_structure(path):
    print(f"🔍 '{path}' 파일을 분석 중...")
    
    # 여러 인코딩 방식을 순서대로 시도해봅니다.
    encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']
    
    for encoding in encodings:
        try:
            # nrows=5로 조금 더 넉넉하게 읽어봅니다.
            df = pd.read_csv(path, encoding=encoding, nrows=5)
            
            print(f"\n✅ 성공! 사용된 인코딩: {encoding}")
            print("\n✅ 찾은 컬럼(칸) 목록:")
            print("-" * 40)
            for i, col in enumerate(df.columns):
                print(f"{i+1:2d}. {col}")
            print("-" * 40)
            
            print("\n✅ 데이터 샘플 (첫 줄):")
            print(df.iloc[0].to_dict()) # 첫 줄 데이터를 사전 형태로 보기 좋게 출력
            return # 성공하면 함수 종료
            
        except UnicodeDecodeError:
            continue # 실패하면 다음 인코딩으로 시도
        except Exception as e:
            print(f"❌ 에러 발생: {e}")
            return

    print("❌ 모든 인코딩 시도가 실패했습니다. 파일 형식을 확인해주세요.")

if __name__ == "__main__":
    check_csv_structure(file_path)