# Selenium 크롤링 완벽 가이드

> 📄 **실전 코드 예시**: [archive/crawling.py](file:///c:/Users/3571/Desktop/projects/DatasetExplorerAI/archive/crawling.py)

---

## 목차

1. [WebDriver 초기화](#1-webdriver-초기화)
2. [대기 전략](#2-대기-전략)
3. [요소 찾기](#3-요소-찾기)
4. [핵심 패턴](#4-핵심-패턴)
5. [디버깅](#5-디버깅)
6. [자주 발생하는 에러](#6-자주-발생하는-에러)

---

## 1. WebDriver 초기화

### 기본 설정

```python
from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('window-size=1920x1080')

driver = webdriver.Chrome(options=options)
```

### 다운로드 경로 설정

> 📄 [crawling.py:L30-L49](file:///c:/Users/3571/Desktop/projects/DatasetExplorerAI/archive/crawling.py#L30-L49)

```python
import os

DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

prefs = {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
}
options.add_experimental_option("prefs", prefs)
```

---

## 2. 대기 전략

### 핵심 Expected Conditions

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# 단일 요소 대기
element = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "myElement"))
)

# 복수 요소 대기 ⭐ 가장 자주 사용
elements = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CLASS_NAME, "item"))
)

# 클릭 가능할 때까지 대기 ⭐ 클릭 전 필수
button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "submitBtn"))
)
button.click()
```

### 주요 EC 비교

| Expected Condition | 조건 | 사용 시점 |
|-------------------|------|-----------|
| `presence_of_element_located` | DOM에 존재 | 요소 존재 확인 |
| `presence_of_all_elements_located` | 여러 요소 DOM에 존재 | **리스트 가져올 때** ⭐ |
| `visibility_of_element_located` | 화면에 보임 | 화면 표시 필요 시 |
| `element_to_be_clickable` | 클릭 가능 | **클릭하기 전** ⭐ |
| `invisibility_of_element_located` | 사라짐 | 로딩 스피너 대기 |

---

## 3. 요소 찾기

### Locator 우선순위

1. **`By.ID`** ⭐⭐⭐ 가장 빠르고 안정적
2. **`By.CSS_SELECTOR`** ⭐⭐ 유연하고 빠름
3. **`By.XPATH`** ⭐ 복잡한 구조에 유용

### CSS Selector 핵심 패턴

```python
# ID
By.CSS_SELECTOR, "#myId"

# 클래스
By.CSS_SELECTOR, ".myClass"

# 자식 요소
By.CSS_SELECTOR, "div.parent > ul > li"

# 속성
By.CSS_SELECTOR, "a[href*='.json']"  # href에 .json 포함

# n번째 자식
By.CSS_SELECTOR, "ul > li:nth-child(2)"
```

### XPath 핵심 패턴

```python
# 텍스트로 찾기 ⭐ 가장 강력
By.XPATH, "//button[text()='로그인']"
By.XPATH, "//a[contains(text(), '다운로드')]"

# 속성
By.XPATH, "//input[@placeholder='이메일']"
```

### 개발자 도구에서 선택자 테스트

```javascript
// Console에서 테스트
$$("button.submit-btn")  // CSS Selector
$x("//button[text()='로그인']")  // XPath
```

---

## 4. 핵심 패턴

### 4-1. 리스트 순회 (StaleElement 방지) ⭐⭐⭐

**가장 중요한 패턴!** 페이지 이동 후 요소가 "stale" 상태가 되는 것을 방지합니다.

> 📄 [crawling.py:L215-L254](file:///c:/Users/3571/Desktop/projects/DatasetExplorerAI/archive/crawling.py#L215-L254)

```python
# 초기 목록 개수 확인
items = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul > li > a"))
)

for i in range(len(items)):
    # ⭐ 매번 요소를 다시 찾습니다!
    current_items = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul > li > a"))
    )
    
    if i >= len(current_items):
        break
    
    link = current_items[i]
    
    # 클릭
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(link)).click()
    
    # 상세 페이지 로드 대기
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#detail"))
    )
    
    # ... 작업 ...
    
    # 뒤로 가기
    driver.back()
    
    # ⭐⭐⭐ 목록 로드 대기 (매우 중요!)
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul > li"))
    )
```

**핵심**:
- 루프 안에서 **매번** 요소 다시 찾기
- `driver.back()` 후 **반드시** 목록 로드 대기
- 인덱스 방식 순회 (`for i in range(...)`)

### 4-2. 새 탭 처리 ⭐⭐

> 📄 [crawling.py:L157-L193](file:///c:/Users/3571/Desktop/projects/DatasetExplorerAI/archive/crawling.py#L157-L193)

```python
import time

# 1. 현재 탭 저장
original_window = driver.current_window_handle

# 2. 링크 클릭 (새 탭 열림)
link.click()
time.sleep(2)

# 3. 새 탭 찾기
new_window = None
for handle in driver.window_handles:
    if handle != original_window:
        new_window = handle
        break

if new_window:
    # 4. 새 탭 전환
    driver.switch_to.window(new_window)
    
    # 5. 작업 수행
    content = driver.find_element(By.TAG_NAME, "body").text
    
    # 6. 새 탭 닫기
    driver.close()
    
    # 7. 원래 탭 복귀
    driver.switch_to.window(original_window)
```

### 4-3. 여러 요소 중 n번째 선택 ⭐

> 📄 [crawling.py:L110-L135](file:///c:/Users/3571/Desktop/projects/DatasetExplorerAI/archive/crawling.py#L110-L135)

```python
# 같은 클래스를 가진 여러 버튼 가져오기
buttons = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button.action"))
)

# 조건에 따라 선택
if len(buttons) == 1:
    target = buttons[0]
elif len(buttons) > 1:
    target = buttons[1]  # 두 번째 선택

target.click()
```

### 4-4. 요소 타입별 처리

```python
# 버튼 클릭
WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "btn"))
).click()

# 입력창
input_field = driver.find_element(By.NAME, "username")
input_field.clear()
input_field.send_keys("myname")

# 드롭다운
from selenium.webdriver.support.ui import Select
dropdown = Select(driver.find_element(By.ID, "country"))
dropdown.select_by_visible_text("대한민국")

# 체크박스
checkbox = driver.find_element(By.ID, "agree")
if not checkbox.is_selected():
    checkbox.click()
```

### 4-5. 동적 요소 처리

```python
# AJAX 로딩 대기
elements = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CLASS_NAME, "item"))
)

# 로딩 스피너 사라질 때까지 대기
WebDriverWait(driver, 10).until(
    EC.invisibility_of_element_located((By.ID, "loading"))
)

# 특정 텍스트가 나타날 때까지
WebDriverWait(driver, 10).until(
    EC.text_to_be_present_in_element((By.ID, "status"), "완료")
)

# 요소가 화면에 보일 때까지
element = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.ID, "hidden"))
)
```

---

## 5. 디버깅

### 5-1. 요소 정보 출력 ⭐⭐

> 📄 [crawling.py:L127-L141](file:///c:/Users/3571/Desktop/projects/DatasetExplorerAI/archive/crawling.py#L127-L141)

```python
def debug_element(element):
    print(f"태그: {element.tag_name}")
    print(f"텍스트: {element.text.strip()}")
    print(f"ID: {element.get_attribute('id')}")
    print(f"Class: {element.get_attribute('class')}")
    print(f"href: {element.get_attribute('href')}")
    print(f"화면에 보이는가?: {element.is_displayed()}")
    print(f"활성화되어 있는가?: {element.is_enabled()}")
    print(f"HTML: {element.get_attribute('outerHTML')}")

# 사용
button = driver.find_element(By.ID, "myBtn")
debug_element(button)
```

### 5-2. 스크린샷

```python
# 전체 화면
driver.save_screenshot("debug.png")

# 특정 요소만
element.screenshot("element.png")
```

### 5-3. 페이지 소스 저장

```python
with open("page.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)
```

---

## 6. 자주 발생하는 에러

### `TimeoutException`

```python
from selenium.common.exceptions import TimeoutException

try:
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "slow"))
    )
except TimeoutException:
    print("타임아웃!")
    driver.save_screenshot("timeout.png")
```

### `StaleElementReferenceException`

**해결**: [4-1. 리스트 순회](#4-1-리스트-순회-staleelement-방지-) 참고

### `ElementClickInterceptedException`

```python
# JavaScript로 강제 클릭
driver.execute_script("arguments[0].click();", button)
```

### 요소가 화면 밖에 있을 때

```python
# 요소까지 스크롤
driver.execute_script("arguments[0].scrollIntoView(true);", element)
time.sleep(1)
element.click()
```

---

## 7. 완전한 크롤링 템플릿

```python
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('window-size=1920x1080')
    return webdriver.Chrome(options=options)

def crawl():
    driver = setup_driver()
    
    try:
        driver.get("https://example.com")
        
        # 리스트 가져오기
        items = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul > li > a"))
        )
        
        # 순회
        for i in range(len(items)):
            # ⭐ 매번 다시 찾기
            current = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul > li > a"))
            )
            
            if i >= len(current):
                break
            
            link = current[i]
            print(f"[{i+1}/{len(items)}] {link.text} 처리 중")
            
            # 클릭
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(link)).click()
            
            # 상세 페이지 대기
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "detail"))
            )
            
            # 데이터 추출
            content = driver.find_element(By.ID, "detail").text
            print(content[:100])
            
            # 뒤로 가기
            driver.back()
            
            # ⭐ 목록 로드 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul > li"))
            )
            
            time.sleep(1)
        
        print("완료!")
        
    except Exception as e:
        print(f"에러: {e}")
        driver.save_screenshot("error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    crawl()
```

---

## 핵심 요약

| 항목 | 방법 |
|------|------|
| **요소 찾기** | `WebDriverWait` + `presence_of_all_elements_located` |
| **클릭 전** | `element_to_be_clickable` 확인 |
| **리스트 순회** | 루프 안에서 **매번 요소 다시 찾기** ⭐⭐⭐ |
| **페이지 이동** | `driver.back()` 후 **목록 로드 대기** ⭐⭐⭐ |
| **새 탭** | `window_handles` → 전환 → 작업 → 복귀 |
| **디버깅** | `debug_element()`, 스크린샷 |
| **선택자 테스트** | 개발자 도구 Console: `$$()`, `$x()` |

---

📄 **실전 프로젝트 코드**: [archive/crawling.py](file:///c:/Users/3571/Desktop/projects/DatasetExplorerAI/archive/crawling.py)
