from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import FinanceDataReader as fdr
import pandas as pd
import CalculateLogic, XmlDataBase, JsonDataBase, WebCrawling

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 구체적인 origin을 지정하세요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로그인 요청/응답 모델
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    user: dict = None

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