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
    BeautifulSoup만을 사용한 크롤링 (JavaScript가 필요없는 경우)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get("https://signal.bz/", headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # rank-column 클래스를 가진 요소들 찾기
        rank_elements = soup.find_all(class_='rank-column')
        
        # 개별 검색어 추출
        search_terms = extract_individual_search_terms(rank_elements)
        
        # 날짜 정보 찾기
        date_info = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "success": True,
            "method": "requests + BeautifulSoup",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date_info": date_info,
            "search_terms": search_terms,
            "total_count": len(search_terms)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"requests 크롤링 중 오류: {str(e)}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def getRealtimeSearchTerms():
    """
    실시간 검색어 크롤링 함수 (API용)
    """
    # Selenium을 사용한 크롤링 시도
    result = crawl_signal_realtime_search()
    
    # 만약 Selenium이 실패하면 requests 방식으로 시도
    if not result.get("success", False):
        result = crawl_with_beautifulsoup_only()
    
    return result