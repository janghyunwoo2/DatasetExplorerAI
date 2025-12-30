import time
import pandas as pd
import os
import requests  # 웹 요청을 위해 추가
import json  # JSON 파싱을 위해 추가
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ----------------- 설정 -----------------
# 크롤링된 파일이 저장될 경로 (절대 경로로 지정해야 안정적입니다)
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloaded_data_files")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

BASE_URL = "https://www.data.go.kr/index.do"
DATA_TYPES = {
    "파일데이터": (By.CSS_SELECTOR, "#dTypeFILE > a"),
    "오픈API": (By.CSS_SELECTOR, "#dTypeAPI > a"),
    "표준데이터셋300": (By.CSS_SELECTOR, "#dTypeSTD > a"),
    "연계데이터": (By.CSS_SELECTOR, "#dTypeLINKED > a"),
}
MAX_PAGE_BLOCKS = 1  # 테스트를 위해 1 블록 (1~10페이지)만 순회하도록 설정
crawled_data_summary = []
# ---------------------------------------


def setup_chrome_options():
    """Chrome 옵션을 설정하고 다운로드 경로를 지정하는 함수"""
    options = webdriver.ChromeOptions()
    # 1. 자동 다운로드 및 경로 지정 설정
    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,  # 다운로드 확인 창 띄우지 않음
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    options.add_argument("--force-device-scale-factor=0.7")
    options.add_experimental_option("prefs", prefs)
    options.add_argument("window-size=1920x1080")
    options.add_argument("disable-gpu")
    # options.add_argument('headless') # 백그라운드 실행 시 주석 해제

    return options


# XPATH/CSS Selector 정의
LOCATORS = {  # searchFrm > div.input-box > button
    "검색_버튼": (By.CSS_SELECTOR, "#searchFrm > div.input-box > button"),
    # "카테고리_탭_템플릿": "//ul[contains(@class, 'data-tab') or contains(@class, 'tab_ty2')]//a[text()='{}']",
    "데이터_리스트_아이템": (
        By.CSS_SELECTOR,
        "#fileDataList > div.result-list > ul > li",
    ),
    "메타데이터_제목": (By.CSS_SELECTOR, "#contents > div.page-title-area > h2"),
    "메타데이터_초기_액션_버튼": (
        By.CSS_SELECTOR,
        "button.button.h36.dropbtn",
    ),
    "메타데이터_JSON_링크": (By.CSS_SELECTOR, "div.dropdown-content a[href*='.json']"),
    "데이터_리스트_아이템_실제_클릭_링크": (
        By.CSS_SELECTOR,
        "#fileDataList > div.result-list > ul > li > dl > dt > a",
    ),
    "다음_페이지_블록": (By.XPATH, "//div[@class='paginate']//a[@class='next']"),
    "페이지_링크_템플릿": (By.XPATH, "//div[@class='paginate']//a[text()='{}']"),
}


def process_detail_page(driver, data_type, item_title):
    summary = {}

    # 1. 상세 페이지 로딩 완료 확인 (선택 사항이지만 안정성 향상)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(LOCATORS["메타데이터_제목"])
        )
        print(f"          상세 페이지 로딩 확인 완료.")
    except Exception as e:
        print(f"          상세 페이지 로딩 확인 중 오류 발생: {e}")
        summary["에러"] = f"상세 페이지 로딩 오류: {e}"
        return summary

    try:
        # 현재 상세 페이지 탭 핸들을 저장 (새 탭이 열리므로)
        original_window = driver.current_window_handle

        # 1단계: 초기 액션 버튼 클릭 (드롭다운 트리거)
        print(f"          1단계: '초기 액션 버튼' 찾기 및 클릭 시도...")
        # initial_action_button = WebDriverWait(driver, 10).until(
        #     EC.element_to_be_clickable(LOCATORS["메타데이터_초기_액션_버튼"])
        # )
        # initial_action_button.click()
        # button.h36.dropbtn 클래스를 가진 모든 버튼을 찾습니다.
        all_dropbtn_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(LOCATORS["메타데이터_초기_액션_버튼"])
        )

        target_button = None
        if len(all_dropbtn_elements) == 1:
            # 대부분의 경우: 버튼이 하나일 때는 그걸 선택
            target_button = all_dropbtn_elements[0]
            print(f"          🔍 일반적인 초기 액션 버튼 하나를 찾았습니다.")
        elif len(all_dropbtn_elements) > 1:
            # 현우님! 여기가 핵심입니다!
            # '두 번째' 버튼이 항상 우리가 원하는 버튼인지 확인하고, 그렇다면 이렇게 선택합니다.
            target_button = all_dropbtn_elements[
                0
            ]  # 리스트의 0번은 첫 번째, 1번은 두 번째 요소
            print(
                f"          🔍 두 개 이상의 버튼 중 '두 번째' 초기 액션 버튼을 선택했습니다."
            )

        if target_button:
            # --- 여기부터 디버깅 코드 추가 ---
            print("\n--- target_button 디버깅 정보 ---")
            print(f"    - target_button 객체: {target_button}")
            print(f"    - 요소의 태그 이름: {target_button.tag_name}")
            print(f"    - 요소의 텍스트: '{target_button.text.strip()}'")
            print(f"    - 요소의 ID: {target_button.get_attribute('id')}")
            print(f"    - 요소의 Class: {target_button.get_attribute('class')}")
            print(
                f"    - 요소의 href (있다면): {target_button.get_attribute('href')}"
            )  # 버튼이라 href는 없겠지만 혹시나
            print(f"    - 요소가 화면에 보이는가?: {target_button.is_displayed()}")
            print(f"    - 요소가 활성화되어 있는가?: {target_button.is_enabled()}")
            print(
                f"    - 요소가 선택되어 있는가?: {target_button.is_selected()}"
            )  # 버튼이라 false겠지만 확인
            print(
                f"    - 요소의 전체 HTML (outerHTML): {target_button.get_attribute('outerHTML')}"
            )  # 버튼의 HTML 구조 확인
            print("---------------------------------")

            target_button.click()
            print(f"          '초기 액션 버튼' 클릭 완료. 드롭다운 대기 중...")
            time.sleep(1)
        else:
            print("          ❌ 클릭할 초기 액션 버튼을 찾지 못했습니다.")
            summary["에러"] = "초기 액션 버튼 찾기 실패"
            return summary

        print(f"          '초기 액션 버튼' 클릭 완료. 드롭다운 대기 중...")
        # 드롭다운 내용이 DOM에 추가되고 가시화될 시간을 잠시 기다려줍니다.
        time.sleep(1)

        # 2단계: 드롭다운에서 'schema.org' JSON 다운로드 링크 찾기 및 클릭
        print(f"          2단계: 'schema.org' JSON 다운로드 링크 찾기 및 클릭 시도...")
        # 이 링크는 첫 번째 버튼 클릭 후 나타나는 div.dropdown-content 내부에 있을 것으로 예상됩니다.
        final_json_link_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(LOCATORS["메타데이터_JSON_링크"])
        )

        # 최종 JSON 링크 클릭 (새 탭으로 열림)
        final_json_link_element.click()
        print(
            f"          'schema.org' JSON 다운로드 링크 클릭 완료. 새 탭 열림 대기 중..."
        )
        time.sleep(3)  # 새 탭이 완전히 열릴 시간을 충분히 줍니다.

        # 새롭게 열린 탭 핸들을 찾아 이동
        new_window = None
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                new_window = window_handle
                break

        if new_window:
            driver.switch_to.window(new_window)
            print(f"          새 탭으로 이동했습니다. URL: {driver.current_url}")

            # 새 탭의 페이지 소스(JSON 텍스트)를 가져와 파싱
            # 페이지 로딩이 완료될 때까지 기다렸다가 텍스트 추출
            json_text = (
                WebDriverWait(driver, 10)
                .until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                .text
            )

            try:
                json_data = json.loads(json_text)
                print(
                    f"          성공적으로 파싱된 JSON 데이터 (일부): \n{json_text[:500]}..."
                )

                # 추출된 JSON 데이터를 summary에 저장
                summary["데이터_유형"] = data_type
                summary["제목"] = item_title
                summary["크롤링_시간"] = time.strftime("%Y-%m-%d %H:%M:%S")
                summary["JSON_데이터"] = json_data

            except json.JSONDecodeError as e:
                print(f"          새 탭의 내용을 JSON으로 파싱하는 중 오류 발생: {e}")
                print(
                    f"          JSON 파싱 실패! 새 탭 내용 (앞부분): \n{json_text[:1000]}"
                )  # 파싱 실패 시 내용 출력
                summary["에러"] = f"JSON 파싱 오류: {e}"

            # 작업 완료 후 새 탭 닫기
            driver.close()

            # 원래 상세 페이지 탭으로 돌아가기
            driver.switch_to.window(original_window)
            print(
                f"          원래 상세 페이지로 돌아왔습니다. URL: {driver.current_url}"
            )

        else:
            print("          오류: 새 탭을 찾을 수 없습니다.")
            summary["에러"] = "새 탭 찾기 실패"

    except Exception as e:
        print(f"          JSON 추출 전체 과정 중 오류 발생: {e}")
        summary["에러"] = f"JSON 추출 오류: {e}"

        # 에러 발생 시 현재 열려 있는 다른 탭이 있다면 닫고 원래 탭으로 돌아오는 로직
        current_handles = driver.window_handles
        if original_window in current_handles:  # 원래 탭이 살아있으면
            for handle in current_handles:
                if handle != original_window:  # 다른 모든 탭 닫기
                    try:
                        driver.switch_to.window(handle)
                        driver.close()
                    except Exception as close_err:
                        print(f"          열려있던 탭 닫는 중 오류 발생: {close_err}")
            driver.switch_to.window(original_window)  # 원래 탭으로 복귀
        else:
            print(
                "          원래 탭을 찾을 수 없어 복구할 수 없습니다. 수동으로 드라이버 확인이 필요합니다."
            )
            # 드라이버 재시작 또는 추가적인 에러 처리 로직 고려

    return summary


def crawl_page_items(driver, data_type, current_page):
    """현재 페이지의 10개 아이템을 순회하며 메타데이터를 수집하고 파일을 다운로드하는 함수"""
    print(f"  > 페이지 {current_page} - 아이템 10개 크롤링 시작...")

    try:
        item_links = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(LOCATORS["데이터_리스트_아이템"])
        )

    except TimeoutException:
        print("    ! 데이터 목록 아이템을 찾을 수 없습니다. (타임아웃)")
        return

    # 10개 아이템을 순회합니다.
    for i in range(len(item_links)):
        try:
            # StaleElementReferenceException 방지를 위해 목록 전체를 다시 찾습니다.
            item_links_current = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    LOCATORS["데이터_리스트_아이템_실제_클릭_링크"]
                )
            )

            # 인덱스 초과 방지
            if i >= len(item_links_current):
                break

            link_to_click = item_links_current[i]
            item_title = link_to_click.text.strip()

            # # --- 여기부터 디버깅 정보 추가 ---
            # print(f"\n--- [{i+1:02d}/10] 요소 디버깅 정보 ---")
            # print(f"    - 요소의 태그 이름: {link_to_click.tag_name}")
            # print(f"    - 요소의 텍스트: '{link_to_click.text[:50]}...'")
            # print(f"    - 요소의 'href' 속성: {link_to_click.get_attribute('href')}")
            # print(f"    - 요소의 'id' 속성: {link_to_click.get_attribute('id')}")
            # print(f"    - 요소의 'class' 속성: {link_to_click.get_attribute('class')}")
            # print(f"    - 요소가 화면에 보이는가?: {link_to_click.is_displayed()}")
            # print(f"    - 요소가 활성화되어 있는가?: {link_to_click.is_enabled()}")
            # # print(f"    - 요소의 전체 HTML (outerHTML): {link_to_click_element.get_attribute('outerHTML')}") # 너무 길면 주석 처리
            # print("------------------------------")
            # # --- 디버깅 정보 끝 ---

            print(f"    - [{i+1:02d}/10] '{item_title[:30]}...' 클릭 및 처리...")

            # 상세 페이지로 이동
            # link_to_click.click()
            # time.sleep(3)  # 클릭 후 반응 대기

            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(link_to_click)
            ).click()
            # time.sleep(10)
            # **여기서 상세 페이지의 특정 요소가 나타날 때까지 기다립니다.**
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(LOCATORS["메타데이터_제목"])
            )
            print(f"        -> '{item_title[:30]}...' 상세 페이지 로드 완료!")

            # 상세 페이지 처리 (메타데이터 추출 및 파일 다운로드)
            summary_data = process_detail_page(driver, data_type, item_title)
            crawled_data_summary.append(summary_data)

            # # 목록 페이지로 복귀
            driver.back()

            # 목록 페이지 복귀 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((LOCATORS["데이터_리스트_아이템"]))
            )

        except Exception as e:
            print(
                f"    ! 크롤링 중 예상치 못한 오류 발생 (페이지 {current_page}, 아이템 {i+1}): {e}"
            )
            driver.back()  # 오류가 나더라도 다음 아이템을 위해 복귀 시도
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(LOCATORS["데이터_리스트_아이템"])
            )
            # time.sleep(2)

    output_directory = "data"  # 데이터를 저장할 폴더 이름
    if not os.path.exists(output_directory):  # 폴더가 없으면 생성
        os.makedirs(output_directory)

    output_filepath = os.path.join(output_directory, "all_crawled_data_summary.json")

    try:
        with open(output_filepath, "w", encoding="utf-8") as f:
            # indent=4는 JSON 파일을 들여쓰기해서 보기 좋게 만들어 줘요. (선택 사항)
            # ensure_ascii=False는 한글이 깨지지 않도록 해줍니다. (필수)
            json.dump(crawled_data_summary, f, indent=4, ensure_ascii=False)
        print(
            f"\n✅ 모든 수집 데이터가 '{output_filepath}' 에 성공적으로 저장되었습니다."
        )
    except Exception as e:
        print(f"\n❌ 데이터 저장 중 오류 발생: {e}")


def crawl_data_portal():
    """메인 크롤링 로직"""
    driver = None
    try:
        driver = webdriver.Chrome(options=setup_chrome_options())
        driver.get(BASE_URL)
        time.sleep(2)  # 2초간 대기
        print(f"1. 웹사이트 접속: {BASE_URL}")

        # 1. 초기 검색 버튼 클릭

        search_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(LOCATORS["검색_버튼"])
        )
        search_button.click()
        print("   > '검색하기' 버튼 클릭 완료.")

        # 카테고리별 순회
        for data_type, css_selector in DATA_TYPES.items():
            print(f"\n==============================================")
            print(f"2. [데이터 유형: {data_type}] 크롤링 시작")
            print(f"==============================================")

            # 2-1. 카테고리 탭 클릭
            category_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(css_selector)
            )
            category_tab.click()
            print(f"> '{data_type}' 탭 클릭 완료. 목록 로딩 대기...")
            time.sleep(2)

            # 2-2. 페이지네이션 순회 (이전 코드의 페이지네이션 로직을 여기에 삽입)
            # ... (페이지네이션 순회 로직을 구현하여 crawl_page_items 호출)

            # 예시를 위해 1페이지만 크롤링
            crawl_page_items(driver, data_type, 1)

    except Exception as e:
        print(f"\n! 치명적인 메인 오류 발생: {e}")
    finally:
        # if driver:
        #     driver.quit()
        pass


# 크롤링 실행
crawl_data_portal()

# 3. 결과 정리
# df = pd.DataFrame(crawled_data_summary)
# print("\n[ 최종 수집된 다운로드 요약 ]")
# print(df)
# print(
#     f"\n총 {len(df)}건의 데이터를 처리했으며, 파일은 '{DOWNLOAD_DIR}'에 저장되었습니다."
# )
