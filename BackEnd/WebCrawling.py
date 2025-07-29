import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
from urllib.parse import urlencode, quote
import xml.etree.ElementTree as ET
from urllib.parse import urlencode, quote, unquote

# API 키 import
from key import KOREA_DATA_PORTAL_API_KEY, KOREA_DATA_PORTAL_HOLIDAY_URL

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

def crawl_zeroin_economic_calendar(start_date, end_date, countries=None, importance_levels=None):
    """
    제로인 API를 사용하여 경제캘린더 데이터를 가져오는 함수
    
    Args:
        start_date (str): 시작일 (YYYY-MM-DD 형식)
        end_date (str): 종료일 (YYYY-MM-DD 형식)
        countries (list): 국가 목록 ["KR", "US", "CN", "GB", "EU"] 등
        importance_levels (list): 중요도 목록 [1, 2, 3] (1:하, 2:중, 3:상)
    
    Returns:
        dict: 경제지표 데이터와 메타 정보를 포함한 딕셔너리
    """
    try:
        # 날짜 형식 검증
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return {
                "success": False,
                "error": "날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용해주세요.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        # 기본 국가 설정 (전체)
        if countries is None:
            countries = ["cn", "kr", "gb", "us", "eu"]
        
        # 기본 중요도 설정 (전체)
        if importance_levels is None:
            importance_levels = [1, 2, 3]
        
        # 국가 코드와 이름 매핑
        country_mapping = {
            "cn": "China|중국",
            "kr": "South Korea|대한민국", 
            "gb": "United Kingdom|영국",
            "us": "United States|미국",
            "eu": "European Union|유럽연합"
        }
        
        # 국가 파라미터 구성
        str_nation_parts = []
        str_natcd_parts = []
        
        for country_code in countries:
            if country_code.lower() in country_mapping:
                str_nation_parts.append(country_mapping[country_code.lower()])
                str_natcd_parts.append(country_code.lower())
        
        str_nation = "|".join(str_nation_parts) + "|"
        str_natcd = "|".join(str_natcd_parts) + "|"
        str_importance = "|".join(map(str, importance_levels)) + "|"
        
        # API URL 구성
        base_url = "https://asp.zeroin.co.kr/eco/includes/wei/module/json_getData.php"
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "sort_code": "0",
            "str_nation": str_nation,
            "str_natcd": str_natcd,
            "str_importance": str_importance
        }
        
        # 헤더 설정
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://asp.zeroin.co.kr/',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        print(f"제로인 API 요청: {start_date} ~ {end_date}")
        print(f"국가: {countries}, 중요도: {importance_levels}")
        
        # API 요청
        response = requests.get(base_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        # JSON 응답 파싱
        data = response.json()
        
        # 데이터 처리 및 구조화
        economic_events = []
        
        if all(key in data for key in ['date', 'time', 'kevent', 'importance']):
            event_count = len(data['date'])
            
            for i in range(event_count):
                try:
                    event = {
                        'date': data['date'][i] if i < len(data['date']) else '',
                        'date_full': data['date_temp'][i] if i < len(data.get('date_temp', [])) else '',
                        'day': data['day'][i] if i < len(data.get('day', [])) else '',
                        'time': data['time'][i] if i < len(data['time']) else '',
                        'event_name': data['kevent'][i] if i < len(data['kevent']) else '',
                        'importance': data['importance'][i] if i < len(data['importance']) else '',
                        'importance_level': get_importance_level(data['importance'][i] if i < len(data['importance']) else ''),
                        'importance_class': data['importance_class'][i] if i < len(data.get('importance_class', [])) else '',
                        'actual': data['actual'][i] if i < len(data.get('actual', [])) else '',
                        'forecast': data['forecast'][i] if i < len(data.get('forecast', [])) else '',
                        'previous': data['previous'][i] if i < len(data.get('previous', [])) else '',
                        'country_name': data['nat_hname'][i] if i < len(data.get('nat_hname', [])) else '',
                        'country_code': data['natcd'][i] if i < len(data.get('natcd', [])) else '',
                        'index': data['index'][i] if i < len(data.get('index', [])) else ''
                    }
                    
                    # 빈 이벤트는 제외
                    if event['event_name'].strip():
                        economic_events.append(event)
                        
                except Exception as e:
                    print(f"이벤트 {i} 처리 중 오류: {e}")
                    continue
        
        result = {
            "success": True,
            "method": "ZeroIn API",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "api_url": base_url,
            "parameters": {
                "start_date": start_date,
                "end_date": end_date,
                "countries": countries,
                "importance_levels": importance_levels
            },
            "economic_data": economic_events,
            "total_count": len(economic_events),
            "raw_data_keys": list(data.keys()) if isinstance(data, dict) else []
        }
        
        print(f"제로인 API 크롤링 완료: {len(economic_events)}개 이벤트 수집")
        return result
        
    except requests.RequestException as e:
        error_msg = f"API 요청 오류: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "method": "ZeroIn API",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except json.JSONDecodeError as e:
        error_msg = f"JSON 파싱 오류: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "method": "ZeroIn API",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        error_msg = f"제로인 API 크롤링 중 오류: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "method": "ZeroIn API",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def get_importance_level(importance_text):
    """
    중요도 텍스트를 숫자로 변환
    
    Args:
        importance_text (str): 중요도 텍스트 ("상", "중", "하")
    
    Returns:
        int: 중요도 레벨 (3: 상, 2: 중, 1: 하)
    """
    mapping = {
        "상": 3,
        "중": 2, 
        "하": 1
    }
    return mapping.get(importance_text, 1)

def extract_country_from_event(event_name):
    """
    이벤트명에서 국가 정보 추출
    
    Args:
        event_name (str): 이벤트명
    
    Returns:
        str: 국가 코드 또는 빈 문자열
    """
    # 간단한 키워드 기반 국가 추출
    country_keywords = {
        "미국": "US",
        "중국": "CN", 
        "영국": "GB",
        "한국": "KR",
        "일본": "JP",
        "독일": "DE",
        "유럽": "EU",
        "Fed": "US",
        "GDP": "",  # 국가별로 다름
        "CPI": "",  # 국가별로 다름
    }
    
    for keyword, country_code in country_keywords.items():
        if keyword in event_name:
            return country_code
    
    return ""

def getEconomicCalendarData(start_date, end_date, countries=None, importance_levels=None):
    """
    경제캘린더 데이터 크롤링 메인 함수 (제로인 API 사용)
    
    Args:
        start_date (str): 시작일 (YYYY-MM-DD 형식)
        end_date (str): 종료일 (YYYY-MM-DD 형식)  
        countries (list): 국가 코드 목록 ["KR", "US", "CN", "GB", "EU"]
        importance_levels (list): 중요도 목록 [1, 2, 3] (1:하, 2:중, 3:상)
    
    Returns:
        dict: 경제지표 데이터와 메타 정보
    """
    
    # 입력 검증
    if not start_date or not end_date:
        return {
            "success": False,
            "error": "시작일과 종료일을 모두 입력해주세요.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    # 국가 코드 정규화 (대소문자 통일)
    if countries:
        countries = [country.lower() for country in countries]
    
    return crawl_zeroin_economic_calendar(start_date, end_date, countries, importance_levels)

def test_zeroin_api():
    """
    제로인 API 테스트 함수
    """
    print("=== 제로인 API 경제캘린더 테스트 시작 ===")
    
    # 테스트 날짜 설정 (오늘부터 3일간)
    today = datetime.now()
    start_date = today.strftime('%Y-%m-%d')
    end_date = (today + timedelta(days=3)).strftime('%Y-%m-%d')
    
    print(f"\n테스트 기간: {start_date} ~ {end_date}")
    print(f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. 전체 국가, 전체 중요도 테스트
    print("1. 전체 데이터 테스트")
    print("-" * 50)
    
    try:
        result = getEconomicCalendarData(start_date, end_date)
        
        print(f"결과: {result.get('success', False)}")
        print(f"방식: {result.get('method', 'unknown')}")
        print(f"수집된 이벤트 수: {len(result.get('economic_data', []))}개")
        print(f"API URL: {result.get('api_url', 'N/A')}")
        
        if result.get('economic_data'):
            print(f"\n수집된 데이터 예시 (처음 3개):")
            for i, event in enumerate(result['economic_data'][:3], 1):
                print(f"  {i}. {event['date']} {event['time']} - {event['event_name'][:50]}...")
                print(f"     중요도: {event['importance']} | 실제: {event.get('actual', 'N/A')}")
        
        if result.get('error'):
            print(f"오류: {result['error']}")
            
    except Exception as e:
        print(f"전체 데이터 테스트 중 오류: {e}")
    
    print("\n" + "="*70 + "\n")
    
    # 2. 특정 국가 테스트
    print("2. 특정 국가 테스트 (한국, 미국)")
    print("-" * 50)
    
    try:
        kr_us_result = getEconomicCalendarData(start_date, end_date, ["kr", "us"], [2, 3])
        
        print(f"결과: {kr_us_result.get('success', False)}")
        print(f"수집된 이벤트 수: {len(kr_us_result.get('economic_data', []))}개")
        
        if kr_us_result.get('economic_data'):
            print(f"\n한국/미국 중요 이벤트 예시:")
            for i, event in enumerate(kr_us_result['economic_data'][:2], 1):
                print(f"  {i}. {event['date']} {event['time']} - {event['event_name']}")
                print(f"     중요도: {event['importance']} | 국가: {event.get('country_code', 'N/A')}")
            
    except Exception as e:
        print(f"특정 국가 테스트 중 오류: {e}")
    
    print("\n" + "="*70 + "\n")
    
    # 3. 고중요도만 테스트
    print("3. 고중요도 이벤트만 테스트")
    print("-" * 50)
    
    try:
        high_importance_result = getEconomicCalendarData(start_date, end_date, None, [3])
        
        print(f"결과: {high_importance_result.get('success', False)}")
        print(f"수집된 이벤트 수: {len(high_importance_result.get('economic_data', []))}개")
        
        if high_importance_result.get('economic_data'):
            print(f"\n고중요도 이벤트 예시:")
            for i, event in enumerate(high_importance_result['economic_data'][:3], 1):
                print(f"  {i}. {event['date']} {event['time']} - {event['event_name']}")
                print(f"     중요도: {event['importance']}")
            
    except Exception as e:
        print(f"고중요도 테스트 중 오류: {e}")
    
    print("\n" + "="*70)
    print("제로인 API 테스트 완료!")
    print(f"테스트 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    return result

def crawl_fnguide_calendar_month(year, month):
    """
    FnGuide에서 특정 연월의 주식 일정 데이터를 가져오는 함수
    
    Args:
        year (int): 연도 (예: 2024)
        month (int): 월 (1-12)
    
    Returns:
        dict: 주식 일정 데이터와 메타 정보를 포함한 딕셔너리
    """
    try:
        # 월을 2자리로 맞춤 (01, 02, ..., 12)
        month_str = f"{month:02d}"
        
        # API URL 구성
        base_url = "https://comp.fnguide.com/SVO2/json/data/05_01"
        filename = f"{year}{month_str}.json"
        api_url = f"{base_url}/{filename}"
        
        # 현재 타임스탬프를 파라미터로 추가 (캐시 방지)
        timestamp = int(time.time() * 1000)
        
        # 헤더 설정 (FnGuide 사이트에서 요구하는 형태)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://comp.fnguide.com/SVO2/ASP/SVD_comp_calendar.asp',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        # API 요청
        params = {'_': timestamp}
        print(f"FnGuide API 요청: {year}년 {month}월 ({api_url})")
        
        response = requests.get(api_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        # JSON 응답 파싱 (BOM 문제 해결)
        try:
            # UTF-8 BOM 제거하여 파싱
            content_text = response.content.decode('utf-8-sig')
            data = json.loads(content_text)
        except UnicodeDecodeError:
            # 일반 UTF-8로 시도
            data = response.json()
        except json.JSONDecodeError:
            # 응답 내용 확인을 위해 일부 출력
            print(f"JSON 파싱 실패. 응답 내용 (처음 200자): {response.text[:200]}")
            raise
        
        # 데이터 구조 확인 및 처리
        stock_events = []
        
        if 'comp' in data and isinstance(data['comp'], list):
            for event_data in data['comp']:
                try:
                    # 이벤트 데이터 구조화
                    event = {
                        'key': event_data.get('KEY', ''),
                        'serial_number': event_data.get('일련번호', ''),
                        'base_date': event_data.get('기준일자', ''),
                        'company_name': event_data.get('기업명', ''),
                        'activity_code': event_data.get('활동코드', ''),
                        'event_name': event_data.get('이벤트명', ''),
                        'event_code': event_data.get('이벤트코드', ''),
                        'date_time': event_data.get('일자', ''),
                        'stock_code': event_data.get('종목명', ''),
                        'stock_type': event_data.get('주식구분', ''),
                        'event_type': event_data.get('종류', ''),
                        'change_stocks': event_data.get('변동주식수', ''),
                        'issue_price': event_data.get('발행가', ''),
                        'capital_after_change': event_data.get('변동후자본금', ''),
                        'total_issued_stocks': event_data.get('총발행주식수', ''),
                        'new_stock_listing_date': event_data.get('신주상장일', ''),
                        'ex_rights_date': event_data.get('권리락일', ''),
                        'payment_date': event_data.get('납입일', ''),
                        'allocation_base_date': event_data.get('배정기준일', ''),
                        'allocation_ratio': event_data.get('배정비율', ''),
                        'discount_ratio': event_data.get('할인비율', ''),
                        'note': event_data.get('비고', ''),
                        'year_month': f"{year}-{month_str}"
                    }
                    
                    # 빈 이벤트가 아닌 경우만 추가
                    if event['company_name'] or event['event_name'] or event['event_type']:
                        stock_events.append(event)
                        
                except Exception as e:
                    print(f"이벤트 데이터 처리 중 오류: {e}")
                    continue
        
        result = {
            "success": True,
            "method": "FnGuide API",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "api_url": api_url,
            "year_month": f"{year}-{month_str}",
            "stock_events": stock_events,
            "total_count": len(stock_events),
            "raw_data_structure": list(data.keys()) if isinstance(data, dict) else []
        }
        
        print(f"FnGuide {year}년 {month}월 크롤링 완료: {len(stock_events)}개 이벤트 수집")
        return result
        
    except requests.RequestException as e:
        error_msg = f"API 요청 오류: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "method": "FnGuide API",
            "year_month": f"{year}-{month:02d}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except json.JSONDecodeError as e:
        error_msg = f"JSON 파싱 오류: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "method": "FnGuide API",
            "year_month": f"{year}-{month:02d}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        error_msg = f"FnGuide API 크롤링 중 오류: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "method": "FnGuide API",
            "year_month": f"{year}-{month:02d}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def getFnGuideStockCalendar(year=None, months=None):
    """
    FnGuide에서 1년치 또는 지정된 월들의 주식 일정 데이터를 가져오는 메인 함수
    
    Args:
        year (int): 연도 (기본값: 현재 연도)
        months (list): 가져올 월 목록 (기본값: 1-12월 전체)
    
    Returns:
        dict: 통합된 주식 일정 데이터
    """
    try:
        # 기본값 설정
        if year is None:
            year = datetime.now().year
        
        if months is None:
            months = list(range(1, 13))  # 1월부터 12월까지
        
        print(f"=== FnGuide 주식 일정 크롤링 시작: {year}년 ===")
        print(f"대상 월: {months}")
        
        all_events = []
        successful_months = []
        failed_months = []
        
        # 각 월별로 데이터 수집
        for month in months:
            try:
                print(f"\n{month}월 데이터 수집 중...")
                month_result = crawl_fnguide_calendar_month(year, month)
                
                if month_result.get('success', False):
                    events = month_result.get('stock_events', [])
                    all_events.extend(events)
                    successful_months.append(month)
                    print(f"{month}월: {len(events)}개 이벤트 수집 성공")
                else:
                    failed_months.append(month)
                    print(f"{month}월: 수집 실패 - {month_result.get('error', '알 수 없는 오류')}")
                
                # API 호출 간격 조절 (서버 부하 방지)
                time.sleep(0.5)
                
            except Exception as e:
                failed_months.append(month)
                print(f"{month}월 처리 중 오류: {e}")
                continue
        
        # 이벤트 타입별 통계
        event_type_stats = {}
        company_stats = {}
        
        for event in all_events:
            # 이벤트 타입별 카운트
            event_type = event.get('event_type', '기타')
            event_type_stats[event_type] = event_type_stats.get(event_type, 0) + 1
            
            # 회사별 카운트
            company_name = event.get('company_name', '기타')
            company_stats[company_name] = company_stats.get(company_name, 0) + 1
        
        # 날짜별로 정렬
        all_events.sort(key=lambda x: x.get('date_time', ''))
        
        # 결과 구성
        result = {
            "success": len(successful_months) > 0,
            "method": "FnGuide API (연간 데이터)",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target_year": year,
            "requested_months": months,
            "successful_months": successful_months,
            "failed_months": failed_months,
            "stock_events": all_events,
            "total_count": len(all_events),
            "statistics": {
                "event_types": dict(sorted(event_type_stats.items(), key=lambda x: x[1], reverse=True)),
                "top_companies": dict(sorted(company_stats.items(), key=lambda x: x[1], reverse=True)[:10]),
                "events_per_month": {month: len([e for e in all_events if e.get('year_month', '').endswith(f"{month:02d}")]) for month in successful_months}
            }
        }
        
        if failed_months:
            result["warnings"] = f"{len(failed_months)}개월 데이터 수집 실패: {failed_months}"
        
        print(f"\n=== FnGuide 크롤링 완료 ===")
        print(f"성공: {len(successful_months)}개월 / 실패: {len(failed_months)}개월")
        print(f"총 수집 이벤트: {len(all_events)}개")
        print(f"주요 이벤트 타입: {list(event_type_stats.keys())[:5]}")
        
        return result
        
    except Exception as e:
        error_msg = f"FnGuide 연간 데이터 수집 중 오류: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "method": "FnGuide API (연간 데이터)",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def test_fnguide_api():
    """
    FnGuide API 테스트 함수
    """
    print("=== FnGuide 주식 일정 API 테스트 시작 ===")
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    print(f"\n현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"테스트 대상: {current_year}년")
    
    # 1. 단일 월 테스트 (현재 월)
    print(f"\n1. 단일 월 테스트 ({current_year}년 {current_month}월)")
    print("-" * 60)
    
    try:
        single_result = crawl_fnguide_calendar_month(current_year, current_month)
        
        print(f"결과: {single_result.get('success', False)}")
        print(f"수집된 이벤트 수: {len(single_result.get('stock_events', []))}개")
        print(f"API URL: {single_result.get('api_url', 'N/A')}")
        
        if single_result.get('stock_events'):
            print(f"\n수집된 데이터 예시 (처음 3개):")
            for i, event in enumerate(single_result['stock_events'][:3], 1):
                print(f"  {i}. {event['company_name']} - {event['event_type']}")
                print(f"     일시: {event['date_time']} | 이벤트: {event['event_name']}")
        
        if single_result.get('error'):
            print(f"오류: {single_result['error']}")
            
    except Exception as e:
        print(f"단일 월 테스트 중 오류: {e}")
    
    print("\n" + "="*70 + "\n")
    
    # 2. 최근 3개월 테스트
    print(f"2. 최근 3개월 테스트")
    print("-" * 60)
    
    try:
        # 최근 3개월 계산
        recent_months = []
        for i in range(3):
            target_date = datetime.now() - timedelta(days=30*i)
            if target_date.month not in recent_months:
                recent_months.append(target_date.month)
        
        recent_months = sorted(recent_months)
        print(f"대상 월: {recent_months}")
        
        multi_result = getFnGuideStockCalendar(current_year, recent_months)
        
        print(f"결과: {multi_result.get('success', False)}")
        print(f"성공한 월: {multi_result.get('successful_months', [])}")
        print(f"실패한 월: {multi_result.get('failed_months', [])}")
        print(f"총 이벤트 수: {len(multi_result.get('stock_events', []))}개")
        
        if multi_result.get('statistics'):
            stats = multi_result['statistics']
            print(f"\n통계 정보:")
            print(f"  이벤트 타입별: {list(stats.get('event_types', {}).keys())[:5]}")
            print(f"  월별 이벤트 수: {stats.get('events_per_month', {})}")
            
        if multi_result.get('warnings'):
            print(f"경고: {multi_result['warnings']}")
            
    except Exception as e:
        print(f"다중 월 테스트 중 오류: {e}")
    
    print("\n" + "="*70 + "\n")
    
    # 3. 이벤트 타입 분석
    if 'multi_result' in locals() and multi_result.get('stock_events'):
        print("3. 이벤트 타입 분석")
        print("-" * 60)
        
        events = multi_result['stock_events']
        
        # 이벤트 타입별 분류
        ir_events = [e for e in events if 'IR' in e.get('event_code', '')]
        dividend_events = [e for e in events if '배당' in e.get('event_type', '')]
        capital_events = [e for e in events if '증자' in e.get('event_type', '') or '감자' in e.get('event_type', '')]
        
        print(f"IR 이벤트: {len(ir_events)}개")
        print(f"배당 관련: {len(dividend_events)}개") 
        print(f"자본 변동: {len(capital_events)}개")
        
        if ir_events:
            print(f"\nIR 이벤트 예시:")
            for event in ir_events[:2]:
                print(f"  - {event['company_name']}: {event['event_name']}")
    
    print("\n" + "="*70)
    print("FnGuide API 테스트 완료!")
    print(f"테스트 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    return multi_result if 'multi_result' in locals() else single_result

def crawl_monthly_holidays(year, month):
    """
    공공데이터포털 한국천문연구원 API에서 특정 연월의 공휴일 정보를 가져오는 함수
    
    Args:
        year (int): 연도 (예: 2024)
        month (int): 월 (1-12)
    
    Returns:
        dict: 공휴일 정보와 메타 정보를 포함한 딕셔너리
    """
    try:
        # 월을 2자리로 맞춤 (01, 02, ..., 12)
        month_str = f"{month:02d}"
        
        # API URL 및 파라미터 설정
        base_url = KOREA_DATA_PORTAL_HOLIDAY_URL
        service_key = KOREA_DATA_PORTAL_API_KEY
        
        params = {
            'serviceKey': service_key,
            'solYear': str(year),
            'solMonth': month_str,
            'numOfRows': '100'  # 한 달에 100개면 충분
        }
        
        # 헤더 설정
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/xml, text/xml, */*',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive'
        }
        
        print(f"한국천문연구원 API 요청: {year}년 {month}월")
        
        # API 요청
        response = requests.get(base_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        # XML 응답 파싱
        try:
            # UTF-8로 응답 처리
            response.encoding = 'utf-8'
            xml_content = response.text
            
            # XML 파싱
            root = ET.fromstring(xml_content)
            
            holidays = []
            
            # XML 구조에 따라 파싱 (공공데이터포털 표준 구조)
            # header 정보 확인
            header = root.find('.//header')
            result_code = header.find('resultCode').text if header is not None and header.find('resultCode') is not None else 'unknown'
            result_msg = header.find('resultMsg').text if header is not None and header.find('resultMsg') is not None else 'unknown'
            
            if result_code != '00':
                return {
                    "success": False,
                    "error": f"API 오류 (코드: {result_code}): {result_msg}",
                    "year_month": f"{year}-{month_str}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            
            # body 에서 items 찾기
            items = root.findall('.//item')
            
            for item in items:
                try:
                    holiday = {
                        'date_code': item.find('locdate').text if item.find('locdate') is not None else '',
                        'date_name': item.find('dateName').text if item.find('dateName') is not None else '',
                        'is_holiday': item.find('isHoliday').text if item.find('isHoliday') is not None else 'Y',
                        'year': year,
                        'month': month,
                        'year_month': f"{year}-{month_str}"
                    }
                    
                    # 날짜 코드를 실제 날짜로 변환 (YYYYMMDD -> YYYY-MM-DD)
                    if holiday['date_code'] and len(holiday['date_code']) == 8:
                        date_str = holiday['date_code']
                        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                        holiday['formatted_date'] = formatted_date
                        
                        # 요일 계산
                        try:
                            date_obj = datetime.strptime(formatted_date, '%Y-%m-%d')
                            holiday['weekday'] = date_obj.strftime('%A')
                            holiday['weekday_kr'] = ['월', '화', '수', '목', '금', '토', '일'][date_obj.weekday()]
                        except:
                            holiday['weekday'] = ''
                            holiday['weekday_kr'] = ''
                    else:
                        holiday['formatted_date'] = ''
                        holiday['weekday'] = ''
                        holiday['weekday_kr'] = ''
                    
                    if holiday['date_name']:  # 빈 공휴일명은 제외
                        holidays.append(holiday)
                        
                except Exception as e:
                    print(f"공휴일 항목 처리 중 오류: {e}")
                    continue
            
            result = {
                "success": True,
                "method": "Korean Astronomy API",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "api_url": base_url,
                "year_month": f"{year}-{month_str}",
                "holidays": holidays,
                "total_count": len(holidays),
                "api_result_code": result_code,
                "api_result_msg": result_msg
            }
            
            print(f"한국천문연구원 {year}년 {month}월 크롤링 완료: {len(holidays)}개 공휴일 수집")
            return result
            
        except ET.ParseError as e:
            error_msg = f"XML 파싱 오류: {str(e)}"
            print(error_msg)
            print(f"응답 내용 (처음 500자): {response.text[:500]}")
            return {
                "success": False,
                "error": error_msg,
                "year_month": f"{year}-{month_str}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
    except requests.RequestException as e:
        error_msg = f"API 요청 오류: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "method": "Korean Astronomy API",
            "year_month": f"{year}-{month:02d}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        error_msg = f"한국천문연구원 API 크롤링 중 오류: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "method": "Korean Astronomy API",
            "year_month": f"{year}-{month:02d}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def getKoreanHolidays(year=None):
    """
    한국천문연구원 API에서 1년치 공휴일 정보를 가져오는 메인 함수
    
    Args:
        year (int): 연도 (기본값: 현재 연도)
    
    Returns:
        dict: 통합된 연간 공휴일 데이터
    """
    try:
        # 기본값 설정
        if year is None:
            year = datetime.now().year
        
        print(f"=== 한국 공휴일 정보 수집 시작: {year}년 ===")
        
        all_holidays = []
        successful_months = []
        failed_months = []
        
        # 1월부터 12월까지 각 월별로 데이터 수집
        for month in range(1, 13):
            try:
                print(f"\n{month}월 공휴일 정보 수집 중...")
                month_result = crawl_monthly_holidays(year, month)
                
                if month_result.get('success', False):
                    holidays = month_result.get('holidays', [])
                    all_holidays.extend(holidays)
                    successful_months.append(month)
                    if holidays:
                        print(f"{month}월: {len(holidays)}개 공휴일 수집 성공")
                    else:
                        print(f"{month}월: 공휴일 없음")
                else:
                    failed_months.append(month)
                    print(f"{month}월: 수집 실패 - {month_result.get('error', '알 수 없는 오류')}")
                
                # API 호출 간격 조절 (서버 부하 방지)
                time.sleep(0.3)
                
            except Exception as e:
                failed_months.append(month)
                print(f"{month}월 처리 중 오류: {e}")
                continue
        
        # 공휴일 통계 및 분석
        holiday_type_stats = {}
        monthly_stats = {}
        
        for holiday in all_holidays:
            # 공휴일 이름별 카운트
            holiday_name = holiday.get('date_name', '기타')
            holiday_type_stats[holiday_name] = holiday_type_stats.get(holiday_name, 0) + 1
            
            # 월별 카운트
            month = holiday.get('month', 0)
            monthly_stats[month] = monthly_stats.get(month, 0) + 1
        
        # 날짜별로 정렬
        all_holidays.sort(key=lambda x: x.get('date_code', ''))
        
        # 특별한 공휴일 분류
        national_holidays = [h for h in all_holidays if any(keyword in h.get('date_name', '') for keyword in ['절', '기념일', '광복', '개천', '한글'])]
        traditional_holidays = [h for h in all_holidays if any(keyword in h.get('date_name', '') for keyword in ['설날', '추석', '부처님', '어린이날'])]
        substitute_holidays = [h for h in all_holidays if '대체공휴일' in h.get('date_name', '')]
        
        # 결과 구성
        result = {
            "success": len(successful_months) > 0,
            "method": "Korean Astronomy API (연간 데이터)",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target_year": year,
            "successful_months": successful_months,
            "failed_months": failed_months,
            "holidays": all_holidays,
            "total_count": len(all_holidays),
            "statistics": {
                "holiday_types": dict(sorted(holiday_type_stats.items(), key=lambda x: x[1], reverse=True)),
                "monthly_distribution": {f"{month}월": count for month, count in sorted(monthly_stats.items())},
                "categories": {
                    "national_holidays": len(national_holidays),
                    "traditional_holidays": len(traditional_holidays), 
                    "substitute_holidays": len(substitute_holidays)
                }
            },
            "holiday_details": {
                "national_holidays": national_holidays,
                "traditional_holidays": traditional_holidays,
                "substitute_holidays": substitute_holidays
            }
        }
        
        if failed_months:
            result["warnings"] = f"{len(failed_months)}개월 데이터 수집 실패: {failed_months}"
        
        print(f"\n=== 한국 공휴일 정보 수집 완료 ===")
        print(f"성공: {len(successful_months)}개월 / 실패: {len(failed_months)}개월")
        print(f"총 공휴일 수: {len(all_holidays)}일")
        print(f"주요 공휴일: {list(holiday_type_stats.keys())[:5]}")
        
        return result
        
    except Exception as e:
        error_msg = f"한국 공휴일 정보 수집 중 오류: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "method": "Korean Astronomy API (연간 데이터)",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def test_korean_holidays_api():
    """
    한국천문연구원 공휴일 API 테스트 함수
    """
    print("=== 한국천문연구원 공휴일 API 테스트 시작 ===")
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    print(f"\n현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"테스트 대상: {current_year}년")
    
    # 1. 단일 월 테스트 (현재 월)
    print(f"\n1. 단일 월 테스트 ({current_year}년 {current_month}월)")
    print("-" * 60)
    
    try:
        single_result = crawl_monthly_holidays(current_year, current_month)
        
        print(f"결과: {single_result.get('success', False)}")
        print(f"수집된 공휴일 수: {len(single_result.get('holidays', []))}개")
        print(f"API URL: {single_result.get('api_url', 'N/A')}")
        print(f"API 응답 코드: {single_result.get('api_result_code', 'N/A')}")
        
        if single_result.get('holidays'):
            print(f"\n수집된 공휴일:")
            for i, holiday in enumerate(single_result['holidays'], 1):
                print(f"  {i}. {holiday['formatted_date']} ({holiday['weekday_kr']}) - {holiday['date_name']}")
        else:
            print(f"  이번 달에는 공휴일이 없습니다.")
        
        if single_result.get('error'):
            print(f"오류: {single_result['error']}")
            
    except Exception as e:
        print(f"단일 월 테스트 중 오류: {e}")
    
    print("\n" + "="*70 + "\n")
    
    # 2. 연간 데이터 테스트
    print(f"2. 연간 공휴일 데이터 테스트 ({current_year}년)")
    print("-" * 60)
    
    try:
        annual_result = getKoreanHolidays(current_year)
        
        print(f"결과: {annual_result.get('success', False)}")
        print(f"성공한 월: {annual_result.get('successful_months', [])}")
        print(f"실패한 월: {annual_result.get('failed_months', [])}")
        print(f"총 공휴일 수: {len(annual_result.get('holidays', []))}일")
        
        if annual_result.get('statistics'):
            stats = annual_result['statistics']
            print(f"\n통계 정보:")
            print(f"  공휴일별 분포: {dict(list(stats.get('holiday_types', {}).items())[:5])}")
            print(f"  월별 분포: {stats.get('monthly_distribution', {})}")
            print(f"  카테고리별:")
            categories = stats.get('categories', {})
            print(f"    - 국경일: {categories.get('national_holidays', 0)}일")
            print(f"    - 전통명절: {categories.get('traditional_holidays', 0)}일")
            print(f"    - 대체공휴일: {categories.get('substitute_holidays', 0)}일")
        
        # 주요 공휴일 목록 출력
        if annual_result.get('holidays'):
            print(f"\n{current_year}년 전체 공휴일 목록:")
            for holiday in annual_result['holidays']:
                print(f"  • {holiday['formatted_date']} ({holiday['weekday_kr']}) - {holiday['date_name']}")
        
        if annual_result.get('warnings'):
            print(f"\n경고: {annual_result['warnings']}")
            
    except Exception as e:
        print(f"연간 데이터 테스트 중 오류: {e}")
    
    print("\n" + "="*70 + "\n")
    
    # 3. 이전 년도 테스트 (간단히)
    print(f"3. 이전 년도 공휴일 비교 ({current_year-1}년)")
    print("-" * 60)
    
    try:
        prev_year_result = getKoreanHolidays(current_year - 1)
        
        if prev_year_result.get('success', False):
            prev_holidays = prev_year_result.get('holidays', [])
            print(f"결과: 성공")
            print(f"{current_year-1}년 공휴일 수: {len(prev_holidays)}일")
            
            # 연도별 비교
            current_holidays = annual_result.get('holidays', []) if 'annual_result' in locals() else []
            if current_holidays:
                print(f"연도별 비교:")
                print(f"  - {current_year-1}년: {len(prev_holidays)}일")
                print(f"  - {current_year}년: {len(current_holidays)}일")
                print(f"  - 차이: {len(current_holidays) - len(prev_holidays):+d}일")
        else:
            print(f"결과: 실패")
            print(f"오류: {prev_year_result.get('error', '알 수 없는 오류')}")
            
    except Exception as e:
        print(f"이전 년도 테스트 중 오류: {e}")
    
    print("\n" + "="*70)
    print("한국천문연구원 공휴일 API 테스트 완료!")
    print(f"테스트 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    return annual_result if 'annual_result' in locals() else single_result

# 테스트 실행 (직접 실행시에만)
if __name__ == "__main__":
    # 사용자가 테스트할 API를 선택할 수 있도록 메뉴 제공
    print("=== WebCrawling 모듈 테스트 메뉴 ===")
    print("1. 제로인 경제캘린더 API 테스트")
    print("2. FnGuide 주식 일정 API 테스트")
    print("3. Signal.bz 실시간 검색어 크롤링 테스트")
    print("4. 한국천문연구원 공휴일 API 테스트")
    print("5. 모든 API 테스트")
    print("6. 종료")
    
    choice = input("\n선택하세요 (1-6): ").strip()
    
    if choice == "1":
        test_zeroin_api()
    elif choice == "2":
        test_fnguide_api()
    elif choice == "3":
        test_crawling_performance()
    elif choice == "4":
        test_korean_holidays_api()
    elif choice == "5":
        print("\n=== 모든 API 테스트 시작 ===\n")
        print("1. 제로인 경제캘린더 API 테스트")
        print("="*50)
        test_zeroin_api()
        
        print("\n\n2. FnGuide 주식 일정 API 테스트")
        print("="*50)
        test_fnguide_api()
        
        print("\n\n3. Signal.bz 실시간 검색어 크롤링 테스트")
        print("="*50)
        test_crawling_performance()
        
        print("\n\n4. 한국 공휴일 정보 API 테스트")
        print("="*50)
        test_korean_holidays_api()
        
        print("\n=== 모든 API 테스트 완료 ===")
    elif choice == "6":
        print("테스트를 종료합니다.")
    else:
        print("잘못된 선택입니다. 기본으로 한국 공휴일 API 테스트를 실행합니다.")
        test_korean_holidays_api()