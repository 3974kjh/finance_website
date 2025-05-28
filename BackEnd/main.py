from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import FinanceDataReader as fdr
import pandas as pd
import CalculateLogic, XmlDataBase, JsonDataBase

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 구체적인 origin을 지정하세요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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