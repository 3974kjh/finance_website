from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import FinanceDataReader as fdr
import pandas as pd
import CalculateLogic, XmlDataBase, JsonDataBase, WebCrawling
import requests
import os
import json

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 구체적인 origin을 지정하세요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 네이버 API 설정
NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID', 'dqMtE_iRIgA_8e9aB_dV')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET', 'bg7d_nO_xJ')
NAVER_API_BASE_URL = "https://openapi.naver.com/v1/search"

# 카카오 API 설정
KAKAO_REST_API_KEY = os.getenv('KAKAO_REST_API_KEY', os.getenv('PUBLIC_API_KEY', '3efc0a804d4103ba9fd00387adc2f8ca'))
KAKAO_REDIRECT_URI = os.getenv('KAKAO_REDIRECT_URI', os.getenv('PUBLIC_REDIRECT_URI', 'http://localhost:7150/oauth'))
KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_API_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

# 로그인 요청/응답 모델
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    user: dict = None

# 네이버 API 요청/응답 모델
class NaverSearchRequest(BaseModel):
    query: str
    display: int = 10
    start: int = 1
    sort: str = 'sim'
    filter: str = 'all'

class NaverSearchResponse(BaseModel):
    lastBuildDate: str = ""
    total: int = 0
    start: int = 0
    display: int = 0
    items: List[dict] = []

# 요청 / 응답
class StockRequest(BaseModel):
    symbol: str = "US500",  # S&P500의 기본 심볼
    duration: int = 0,
    isMonth: bool = True
class StockResponse(BaseModel):
    symbol: str
    data: dict

# 요청 / 응답
class StockListRequest(BaseModel):
    symbol: str = "S&P500",  # S&P500의 기본 심볼
class StockListResponse(BaseModel):
    symbol: str
    data: list

# 요청 / 응답
class ExpectStockRequest(BaseModel):
    symbol: str = "S&P500",  # S&P500의 기본 심볼
    term: int = 0
class ExpectStockListResponse(BaseModel):
    symbol: str
    data: dict

# 요청 / 응답
class SaveListRequest(BaseModel):
    stock: str = '',
    data: list = []
class SaveListResponse(BaseModel):
    isSuccess: bool

# 요청 / 응답
class GetXmlListRequest(BaseModel):
    stock: str = ''
class GetXmlListResponse(BaseModel):
    data: dict

# 요청 / 응답
class SaveJsonHistoryRequest(BaseModel):
    data: dict = {}
class SaveJsonHistoryResponse(BaseModel):
    isSuccess: bool

# 요청 / 응답
class GetJsonHistoryRequest(BaseModel):
    stock: str = ''
class GetJsonHistoryResponse(BaseModel):
    data: dict

# 요청 / 응답
class GetJsonAnalyzeRequest(BaseModel):
    stock: str = ''
class GetJsonAnalyzeResponse(BaseModel):
    data: list

# 실시간 검색어 요청 / 응답
class RealtimeSearchRequest(BaseModel):
    pass  # 추가 파라미터가 필요한 경우 여기에 정의
class RealtimeSearchResponse(BaseModel):
    search_terms: List[str]
    date_info: str
    total_count: int

# 카카오 API 요청/응답 모델
class KakaoTokenRequest(BaseModel):
    accessCode: str
    redirectUri: str = None

class KakaoMessageRequest(BaseModel):
    accessCode: str = ""
    accessToken: str = ""
    redirectUri: str = None
    link: dict = {}
    data: dict = {}

class KakaoResponse(BaseModel):
    isFail: bool = False
    token: str = ""
    message: str = ""

@app.post("/login/", response_model=LoginResponse)
async def login(request: LoginRequest):
    try:
        # 정해진 아이디와 비밀번호
        CORRECT_USERNAME = "jukim"
        CORRECT_PASSWORD = "jukim123$"
        
        # 입력받은 값과 비교
        if request.username == CORRECT_USERNAME and request.password == CORRECT_PASSWORD:
            # 로그인 성공
            user_info = {
                "id": "1",
                "username": "jukim",
                "name": "김준형",
                "email": "jukim@example.com"
            }
            return LoginResponse(
                success=True,
                message="로그인 성공",
                user=user_info
            )
        else:
            # 로그인 실패
            return LoginResponse(
                success=False,
                message="아이디 또는 비밀번호가 일치하지 않습니다."
            )
            
    except Exception as e:
        return LoginResponse(
            success=False,
            message=f"로그인 처리 중 오류가 발생했습니다: {str(e)}"
        )

@app.post("/stock_data/", response_model=StockResponse)
async def get_stock_data(request: StockRequest):
    try:
        end_date = datetime.now()
        durationDay = request.duration * (30 if request.isMonth else 7)
        start_date = end_date - timedelta(days=durationDay)

        df = fdr.DataReader(request.symbol, start_date, end_date)

        if df.empty:
            raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다.")

        # 날짜를 문자열로 변환
        df.index = df.index.strftime('%Y-%m-%d')

        # DataFrame을 딕셔너리로 변환
        data_dict = df.to_dict(orient='index')

        return StockResponse(symbol=request.symbol, data=data_dict)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/stock_list/", response_model=StockListResponse)
async def get_stock_list(request: StockListRequest):
    try:
        df = fdr.StockListing(request.symbol)

        if df.empty:
            raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다.")
        
        # DataFrame을 딕셔너리로 변환
        data_dict = df.to_dict(orient='index')

        return StockListResponse(symbol=request.symbol, data=list(data_dict.values()))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/expect_stock/", response_model=ExpectStockListResponse)
async def get_stock_list(request: ExpectStockRequest):
    try:
        calculateStockInfo = CalculateLogic.findStockPeaksAndTroughs(request.symbol, request.term)

        return ExpectStockListResponse(symbol=request.symbol, data=calculateStockInfo)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_finance_rank/", response_model=SaveListResponse)
async def saveFinanceRank(request: SaveListRequest):
    try:
        isSuccess = XmlDataBase.saveXmlDataList(request.stock, request.data)

        return SaveListResponse(isSuccess=isSuccess)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/get_finance_rank/", response_model=GetXmlListResponse)
async def getFinanceRank(request: GetXmlListRequest):
    try:
        financeRankList = XmlDataBase.getXmlDataList(request.stock)

        return GetXmlListResponse(data=financeRankList)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_buy_history/", response_model=SaveJsonHistoryResponse)
async def saveFinanceRank(request: SaveJsonHistoryRequest):
    try:
        isSuccess = JsonDataBase.SaveHistoryJsonFile(request.data)

        return SaveJsonHistoryResponse(isSuccess=isSuccess)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/get_buy_history/", response_model=GetJsonHistoryResponse)
async def getFinanceRank(request: GetJsonHistoryRequest):
    try:
        buyHistory = JsonDataBase.ReadHistoryJsonFile()

        return GetJsonHistoryResponse(data=buyHistory)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/get_today_analyze/", response_model=GetJsonAnalyzeResponse)
async def getTodayAnalyze(request: GetJsonAnalyzeRequest):
    try:
        todayAnalyze = JsonDataBase.ReadAnalyzeJsonFile()

        return GetJsonAnalyzeResponse(data=todayAnalyze)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_realtime_search/", response_model=RealtimeSearchResponse)
async def getRealtimeSearch(request: RealtimeSearchRequest):
    try:
        # WebCrawling 모듈의 getRealtimeSearchTerms 함수 호출
        crawl_result = WebCrawling.getRealtimeSearchTerms()
        
        # 크롤링 실패 시 에러 처리
        if not crawl_result.get("success", False):
            raise HTTPException(status_code=500, detail=f"크롤링 실패: {crawl_result.get('error', '알 수 없는 오류')}")
        
        # 결과 데이터 추출
        search_terms = crawl_result.get("search_terms", [])
        date_info = crawl_result.get("date_info", "")
        total_count = crawl_result.get("total_count", 0)
        
        return RealtimeSearchResponse(
            search_terms=search_terms,
            date_info=date_info,
            total_count=total_count
        )

    except HTTPException:
        raise  # HTTPException은 그대로 다시 발생
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

# 네이버 API 프록시 엔드포인트들
@app.post("/api/naver/{service_id}")
async def naver_search_proxy(service_id: str, request: NaverSearchRequest):
    """
    네이버 검색 API 프록시 엔드포인트
    service_id: blog, news, book, encyc, cafearticle, kin, webkr, image, shop, doc
    """
    try:
        # 지원하는 서비스 목록
        valid_services = ['blog', 'news', 'book', 'encyc', 'cafearticle', 'kin', 'webkr', 'image', 'shop', 'doc']
        
        if service_id not in valid_services:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 서비스입니다. 사용 가능한 서비스: {', '.join(valid_services)}")
        
        # 네이버 API 요청 헤더
        headers = {
            'X-Naver-Client-Id': NAVER_CLIENT_ID,
            'X-Naver-Client-Secret': NAVER_CLIENT_SECRET,
            'Content-Type': 'application/json'
        }
        
        # 네이버 API 요청 파라미터
        params = {
            'query': request.query,
            'display': min(request.display, 100),  # 최대 100개로 제한
            'start': max(request.start, 1),        # 최소 1로 제한
            'sort': request.sort
        }
        
        # 이미지 서비스인 경우 filter 파라미터 추가
        if service_id == 'image':
            params['filter'] = request.filter
        
        # 네이버 API 호출
        naver_url = f"{NAVER_API_BASE_URL}/{service_id}"
        response = requests.get(naver_url, headers=headers, params=params, timeout=10)
        
        # 응답 처리
        if response.status_code == 200:
            result_data = response.json()
            return {
                "isSuccess": True,
                "data": result_data
            }
        else:
            raise HTTPException(status_code=response.status_code, detail=f"네이버 API 오류: {response.text}")
            
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="네이버 API 요청 시간 초과")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"네이버 API 요청 실패: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

# 카카오 API 프록시 엔드포인트들
@app.post("/api/kakao/token", response_model=KakaoResponse)
async def get_kakao_access_token(request: KakaoTokenRequest):
    """
    카카오 OAuth 인증 코드로 액세스 토큰 받기
    """
    try:
        print(f"🎯 카카오 토큰 요청 시작:")
        print(f"   - accessCode: {request.accessCode[:10]}..." if request.accessCode else "   - accessCode: None")
        print(f"   - redirectUri: {request.redirectUri}")
        print(f"   - KAKAO_REST_API_KEY: {KAKAO_REST_API_KEY[:10]}..." if KAKAO_REST_API_KEY else "   - KAKAO_REST_API_KEY: None")
        print(f"   - KAKAO_REDIRECT_URI: {KAKAO_REDIRECT_URI}")
        
        # API 키 검증
        if not KAKAO_REST_API_KEY or KAKAO_REST_API_KEY == '':
            return KakaoResponse(
                isFail=True,
                token="",
                message="카카오 API 키가 설정되지 않았습니다. 환경 변수 KAKAO_REST_API_KEY 또는 PUBLIC_API_KEY를 확인해주세요."
            )
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'
        }
        
        redirect_uri = request.redirectUri or KAKAO_REDIRECT_URI
        
        data = {
            'grant_type': 'authorization_code',
            'client_id': KAKAO_REST_API_KEY,
            'redirect_uri': redirect_uri,
            'code': request.accessCode
        }
        
        print(f"🔄 카카오 토큰 API 호출: {KAKAO_AUTH_URL}")
        print(f"   - grant_type: {data['grant_type']}")
        print(f"   - client_id: {data['client_id'][:10]}...")
        print(f"   - redirect_uri: {data['redirect_uri']}")
        print(f"   - code: {data['code'][:10]}..." if data['code'] else "   - code: None")
        
        response = requests.post(KAKAO_AUTH_URL, headers=headers, data=data, timeout=10)
        
        print(f"📥 카카오 응답 수신:")
        print(f"   - status_code: {response.status_code}")
        print(f"   - response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            access_token = result.get('access_token', '')
            
            if access_token:
                print(f"✅ 토큰 발급 성공: {access_token[:10]}...")
                return KakaoResponse(
                    isFail=False,
                    token=access_token,
                    message="토큰 발급 성공"
                )
            else:
                print(f"❌ 토큰 없음: {result}")
                return KakaoResponse(
                    isFail=True,
                    token="",
                    message=f"액세스 토큰을 받지 못했습니다. 응답: {result}"
                )
        else:
            error_detail = response.text
            print(f"❌ 카카오 API 오류: {response.status_code} - {error_detail}")
            return KakaoResponse(
                isFail=True,
                token="",
                message=f"카카오 인증 실패 ({response.status_code}): {error_detail}"
            )
            
    except requests.exceptions.Timeout:
        print("❌ 카카오 API 요청 시간 초과")
        return KakaoResponse(
            isFail=True,
            token="",
            message="카카오 API 요청 시간 초과"
        )
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")
        return KakaoResponse(
            isFail=True,
            token="",
            message=f"서버 오류: {str(e)}"
        )

@app.post("/api/kakao/send", response_model=KakaoResponse)
async def send_kakao_message(request: KakaoMessageRequest):
    """
    카카오톡 메시지 전송
    """
    try:
        # 액세스 토큰이 없으면 인증 코드로 토큰 발급 시도
        access_token = request.accessToken
        
        if not access_token and request.accessCode:
            token_request = KakaoTokenRequest(
                accessCode=request.accessCode,
                redirectUri=request.redirectUri
            )
            token_result = await get_kakao_access_token(token_request)
            
            if token_result.isFail:
                return KakaoResponse(
                    isFail=True,
                    token="",
                    message="액세스 토큰 발급 실패"
                )
            
            access_token = token_result.token
        
        if not access_token:
            return KakaoResponse(
                isFail=True,
                token="",
                message="액세스 토큰이 필요합니다"
            )
        
        # 카카오톡 메시지 전송
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Bearer {access_token}'
        }
        
        # 메시지 템플릿 구성
        template_object = {
            'object_type': request.data.get('object_type', 'text'),
            'text': request.data.get('text', '전달 데이터 없음'),
            'link': request.link,
        }
        
        # 버튼 제목이 있으면 추가
        if request.data.get('button_title'):
            template_object['button_title'] = request.data.get('button_title')
        
        data = {
            'template_object': json.dumps(template_object, ensure_ascii=False)
        }
        
        response = requests.post(KAKAO_API_URL, headers=headers, data=data, timeout=10)
        
        if response.status_code == 200:
            return KakaoResponse(
                isFail=False,
                token=access_token,
                message="메시지 전송 성공"
            )
        else:
            return KakaoResponse(
                isFail=True,
                token=access_token,
                message=f"메시지 전송 실패: {response.text}"
            )
            
    except requests.exceptions.Timeout:
        return KakaoResponse(
            isFail=True,
            token="",
            message="카카오 API 요청 시간 초과"
        )
    except Exception as e:
        return KakaoResponse(
            isFail=True,
            token="",
            message=f"서버 오류: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8250)