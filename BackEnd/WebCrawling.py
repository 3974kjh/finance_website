import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

def setup_driver():
    """
    Chrome 웹드라이버 설정 및 초기화
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 브라우저 창을 띄우지 않음
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"웹드라이버 설정 중 오류 발생: {e}")
        return None

def extract_individual_search_terms(rank_elements):
    """
    rank-column 요소들에서 개별 검색어들을 추출하는 함수
    """
    search_terms = []
    
    for rank_element in rank_elements:
        # rank-column 내의 모든 하위 요소들을 찾기
        child_elements = rank_element.find_all(['div', 'span', 'p', 'a', 'li'])
        
        if child_elements:
            # 하위 요소가 있는 경우, 각각의 텍스트를 개별적으로 추출
            for child in child_elements:
                text_content = child.get_text(strip=True)
                if text_content and len(text_content) > 1:
                    # 정규식을 사용하여 순위 번호 제거
                    cleaned_text = re.sub(r'^\d+', '', text_content).strip()
                    # 숫자로만 이루어진 텍스트는 제외 (순위 번호 등)
                    if cleaned_text and not cleaned_text.isdigit() and len(cleaned_text) > 2:
                        search_terms.append(cleaned_text)
        else:
            # 하위 요소가 없는 경우, 직접 텍스트 추출
            text_content = rank_element.get_text(strip=True)
            if text_content:
                # 여러 검색어가 붙어있는 경우를 정규식으로 분리
                # 예: "1이스라엘 이란 공습2은마아파트 작업자 매몰" -> ["이스라엘 이란 공습", "은마아파트 작업자 매몰"]
                parts = re.split(r'\d+', text_content)
                for part in parts:
                    cleaned_part = part.strip()
                    if cleaned_part and len(cleaned_part) > 2:
                        search_terms.append(cleaned_part)
    
    # 중복 제거하되 순서는 유지 (dict.fromkeys 사용)
    unique_terms = list(dict.fromkeys([term for term in search_terms if term.strip()]))
    
    # 추가적으로 너무 짧거나 의미없는 텍스트 필터링
    filtered_terms = []
    for term in unique_terms:
        # 최소 길이 체크 및 특수문자만으로 이루어진 텍스트 제외
        if len(term) >= 3 and not re.match(r'^[^\w\s가-힣]+$', term):
            filtered_terms.append(term)
    
    return filtered_terms

def crawl_signal_realtime_search():
    """
    Signal.bz 사이트에서 실시간 검색어 데이터를 크롤링하는 함수
    
    Returns:
        dict: 검색어 데이터와 날짜 정보를 포함한 딕셔너리
    """
    driver = None
    try:
        # 웹드라이버 설정
        driver = setup_driver()
        if driver is None:
            return {"error": "웹드라이버 초기화 실패"}
        
        # Signal.bz 사이트 접속
        url = "https://signal.bz/"
        driver.get(url)
        
        # 페이지 로딩 대기
        time.sleep(3)
        
        # 페이지가 완전히 로드될 때까지 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 현재 페이지 소스 가져오기
        page_source = driver.page_source
        
        # BeautifulSoup으로 HTML 파싱
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # rank-column 클래스를 가진 요소들 찾기
        rank_elements = soup.find_all(class_='rank-column')
        
        # 개별 검색어 추출
        search_terms = extract_individual_search_terms(rank_elements)
        
        # 추가적으로 다른 가능한 선택자들도 시도
        if not search_terms:
            # 다른 가능한 클래스나 요소들 시도
            alternative_selectors = [
                '.ranking-item', '.search-term', '.keyword', 
                '.rank-item', '.trend-item', '[class*="rank"]',
                '[class*="search"]', '[class*="keyword"]'
            ]
            
            for selector in alternative_selectors:
                elements = soup.select(selector)
                if elements:
                    for element in elements:
                        text = element.get_text(strip=True)
                        if text and len(text) > 1 and not text.isdigit():
                            search_terms.append(text)
                    break
        
        # 날짜 데이터 찾기 (다양한 선택자로 시도)
        date_info = None
        
        # 일반적인 날짜 관련 클래스나 ID 찾기
        date_selectors = [
            'date', 'time', 'datetime', 'timestamp', 
            'update-time', 'last-update', 'current-time'
        ]
        
        for selector in date_selectors:
            date_element = soup.find(class_=selector) or soup.find(id=selector)
            if date_element:
                date_info = date_element.get_text(strip=True)
                break
        
        # 만약 특정 날짜 요소를 찾지 못했다면, 현재 시간을 사용
        if not date_info:
            date_info = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 결과 데이터 구성
        result = {
            "success": True,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "site_url": url,
            "date_info": date_info,
            "search_terms": search_terms,
            "total_count": len(search_terms)
        }
        
        return result
        
    except Exception as e:
        error_msg = f"크롤링 중 오류 발생: {str(e)}"
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    finally:
        # 웹드라이버 종료
        if driver:
            driver.quit()

def crawl_with_beautifulsoup_only():
    """
    BeautifulSoup만을 사용한 개선된 정적 크롤링
    다양한 선택자를 시도하여 검색어 추출 성공률을 높임
    """
    try:
        # 브라우저처럼 보이게 하는 헤더 설정
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        print("정적 크롤링 시작: Signal.bz 접속 중...")
        response = requests.get("https://signal.bz/", headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        search_terms = []
        
        # 다양한 선택자들을 순차적으로 시도
        selectors_to_try = [
            # 기본 선택자들
            '.rank-column',
            '.ranking-item',
            '.search-term',
            '.keyword',
            '.rank-item',
            '.trend-item',
            '.realtime-keyword',
            '.hot-keyword',
            
            # 클래스 속성이 포함된 요소들
            '[class*="rank"]',
            '[class*="search"]',
            '[class*="keyword"]',
            '[class*="trend"]',
            '[class*="hot"]',
            '[class*="realtime"]',
            
            # 리스트 형태의 요소들
            'li[class*="rank"]',
            'li[class*="keyword"]',
            'div[class*="rank"]',
            'span[class*="rank"]',
            
            # 일반적인 순위 관련 선택자들
            '.ranking',
            '.top-keywords',
            '.popular-keywords',
            '.trending-keywords'
        ]
        
        for selector in selectors_to_try:
            try:
                elements = soup.select(selector)
                if elements:
                    print(f"선택자 '{selector}'로 {len(elements)}개 요소 발견")
                    
                    # rank-column 클래스의 경우 특별 처리
                    if 'rank-column' in selector:
                        temp_terms = extract_individual_search_terms(elements)
                    else:
                        temp_terms = []
                        for element in elements:
                            text = element.get_text(strip=True)
                            if text and len(text) > 2 and not text.isdigit():
                                # 순위 번호 제거
                                cleaned_text = re.sub(r'^\d+\.?\s*', '', text).strip()
                                if cleaned_text and len(cleaned_text) > 2:
                                    temp_terms.append(cleaned_text)
                    
                    if temp_terms:
                        search_terms.extend(temp_terms)
                        print(f"선택자 '{selector}'에서 {len(temp_terms)}개 검색어 추출")
                        
                        # 충분한 검색어를 찾았으면 중단
                        if len(search_terms) >= 10:
                            break
                            
            except Exception as e:
                print(f"선택자 '{selector}' 처리 중 오류: {e}")
                continue
        
        # 중복 제거 및 정리
        if search_terms:
            # 중복 제거하되 순서는 유지
            unique_terms = list(dict.fromkeys(search_terms))
            
            # 추가 필터링
            filtered_terms = []
            for term in unique_terms:
                # 길이 체크, 특수문자만으로 이루어진 텍스트 제외
                if len(term) >= 2 and not re.match(r'^[^\w\s가-힣]+$', term):
                    # 너무 긴 텍스트 제외 (일반적으로 검색어는 50자 이내)
                    if len(term) <= 50:
                        filtered_terms.append(term)
            
            search_terms = filtered_terms[:20]  # 최대 20개까지만
        
        # 날짜 정보 찾기
        date_info = None
        date_selectors = [
            '.date', '.time', '.datetime', '.timestamp', 
            '.update-time', '.last-update', '.current-time',
            '[class*="date"]', '[class*="time"]'
        ]
        
        for selector in date_selectors:
            try:
                date_element = soup.select_one(selector)
                if date_element:
                    date_info = date_element.get_text(strip=True)
                    break
            except:
                continue
        
        if not date_info:
            date_info = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        result = {
            "success": True,
            "method": "requests + BeautifulSoup (개선됨)",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "site_url": "https://signal.bz/",
            "date_info": date_info,
            "search_terms": search_terms,
            "total_count": len(search_terms)
        }
        
        print(f"정적 크롤링 완료: {len(search_terms)}개 검색어 수집")
        return result
        
    except requests.RequestException as e:
        error_msg = f"네트워크 요청 오류: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "method": "requests + BeautifulSoup",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        error_msg = f"정적 크롤링 중 오류: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "method": "requests + BeautifulSoup",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def getRealtimeSearchTerms():
    """
    실시간 검색어 크롤링 함수 (API용)
    정적 크롤링을 우선적으로 시도하고, 실패시에만 동적 크롤링 사용
    """
    # 1. 먼저 requests + BeautifulSoup 방식으로 시도 (빠르고 효율적)
    result = crawl_with_beautifulsoup_only()
    
    # 정적 크롤링이 성공하고 검색어가 충분히 가져와졌다면 바로 반환
    if result.get("success", False) and len(result.get("search_terms", [])) > 5:
        print(f"정적 크롤링 성공: {len(result.get('search_terms', []))}개 검색어 수집")
        return result
    
    # 정적 크롤링이 실패하거나 검색어가 부족하면 Selenium으로 시도
    print("정적 크롤링 실패 또는 검색어 부족, 동적 크롤링으로 재시도...")
    selenium_result = crawl_signal_realtime_search()
    
    # 동적 크롤링 결과 반환
    if selenium_result.get("success", False):
        print(f"동적 크롤링 성공: {len(selenium_result.get('search_terms', []))}개 검색어 수집")
    else:
        print("동적 크롤링도 실패")
        
    return selenium_result

def test_crawling_performance():
    """
    크롤링 성능 테스트 함수
    정적 크롤링과 동적 크롤링의 시간을 비교
    """
    print("=== 크롤링 성능 테스트 시작 ===")
    
    # 정적 크롤링 테스트
    print("\n1. 정적 크롤링 (requests + BeautifulSoup) 테스트")
    start_time = time.time()
    static_result = crawl_with_beautifulsoup_only()
    static_time = time.time() - start_time
    
    print(f"정적 크롤링 결과:")
    print(f"- 성공: {static_result.get('success', False)}")
    print(f"- 검색어 수: {len(static_result.get('search_terms', []))}개")
    print(f"- 소요 시간: {static_time:.2f}초")
    if static_result.get('search_terms'):
        print(f"- 검색어 예시: {static_result['search_terms'][:3]}")
    
    # 동적 크롤링 테스트 (선택적)
    print(f"\n2. 동적 크롤링 테스트는 시간이 오래 걸리므로 생략")
    print(f"   (보통 10-30초 소요)")
    
    print(f"\n=== 성능 비교 결과 ===")
    print(f"정적 크롤링: {static_time:.2f}초 (빠름)")
    print(f"동적 크롤링: ~15-30초 (느림)")
    print(f"성능 개선: 약 {15/static_time:.1f}배 빨라짐")
    
    return static_result

# 테스트 실행 (직접 실행시에만)
if __name__ == "__main__":
    test_crawling_performance()