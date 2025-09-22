import FinanceDataReader as fdr
from datetime import timedelta, datetime
import calendar

저항_반환수정문 = []
저항_반환추세 = []
저항_cnt = 0

지지_반환수정문 = []
지지_반환추세 = []
지지_cnt = 0

def get_valid_date(date):
    year, month, day = date.year, date.month, date.day
    
    # 해당 월의 마지막 날짜 확인
    _, last_day = calendar.monthrange(year, month)

    # 2월 마지막 날짜인 경우 financeDataReader가 2월 29일을 없는 날짜로 생각하여 28일로 의도적 변경
    if day == 29 and last_day == 29:
        day = 28
    # 날짜가 해당 월의 마지막 날짜를 초과하는 경우 조정
    elif day > last_day:
        day = last_day
    
    return datetime(year, month, day)

def subtract_weeks(n):
    current_date = datetime.now()
    result_date = current_date - timedelta(weeks=n)
    
    # 결과 날짜의 유효성 검사 및 조정
    valid_date = get_valid_date(result_date)
    
    return valid_date.strftime("%Y-%m-%d")

def 지지선찾습니다(원문, 추세):
    global 지지_cnt, 지지_반환수정문, 지지_반환추세
    수정문 = []
    
    if len(원문) <= 2:
        # print('원문 = ', 원문)
        # print('수정문 = ', 수정문)
        # print('추세 = ', 추세)
        return
    
    first_value = 원문[0][1]

    for i in range(1, len(원문)):
        if first_value > 원문[i][1]:
            추세.append('-')
        elif first_value == 원문[i][1]:
            추세.append('o')
        else:
            추세.append('+')

        first_value = 원문[i][1]

        if len(추세) >= 2:
            if 추세[i-2] == '-' and 추세[i-1] == '+':
                수정문.append(원문[i-1])

        if i == 0 or i == len(원문) - 1:
            if (추세[i-2] == '+' and 추세[i-1] == '+') or (추세[i-2] == '-' and 추세[i-1] == '-'):
                수정문.append(원문[i])

    # print('원문 = ', 원문)
    # print('수정문 = ', 수정문)
    # print('추세 = ', 추세)

    if 추세.count('-') == 1 or 추세.count('+') == 1:
        return 
    
    지지선찾습니다(수정문, [])
    
    if 지지_cnt == 0:
        if len(수정문) <= 1:
            지지_반환수정문 = 원문
        else:
            지지_반환수정문 = 수정문
        지지_반환추세 = 추세

    지지_cnt += 1
    
    return 지지_반환수정문

def 저항선찾습니다(원문, 추세):
    global 저항_cnt, 저항_반환수정문, 저항_반환추세
    수정문 = []

    if len(원문) <= 2:
        # print('원문 = ', 원문)
        # print('수정문 = ', 수정문)
        # print('추세 = ', 추세)
        return
    
    first_value = 원문[0][1]

    for i in range(1, len(원문)):
        if first_value > 원문[i][1]:
            추세.append('-')
        elif first_value == 원문[i][1]:
            추세.append('o')
        else:
            추세.append('+')

        first_value = 원문[i][1]

        if len(추세) >= 2:
            if 추세[i-2] == '+' and 추세[i-1] == '-':
                수정문.append(원문[i-1])

        if i == 0 or i == len(원문) - 1:
            if (추세[i-2] == '+' and 추세[i-1] == '+') or (추세[i-2] == '-' and 추세[i-1] == '-'):
                수정문.append(원문[i])

    # print('원문 = ', 원문)
    # print('수정문 = ', 수정문)
    # print('추세 = ', 추세)

    if 추세.count('-') == 1 or 추세.count('+') == 1:
        return 
    
    저항선찾습니다(수정문, [])
    
    if 저항_cnt == 0:
        if len(수정문) <= 1: 
            저항_반환수정문 = 원문
        else:
            저항_반환수정문 = 수정문
        저항_반환추세 = 추세

    저항_cnt += 1
    
    return 저항_반환수정문

def 고점저점예측(code, term):
    global 지지_cnt, 지지_반환수정문, 지지_반환추세, 저항_cnt, 저항_반환수정문, 저항_반환추세

    저항_반환수정문 = []
    저항_반환추세 = []
    저항_cnt = 0
    지지_반환수정문 = []
    지지_반환추세 = []
    지지_cnt = 0

    전체날짜 = subtract_weeks(term)
    증시정보 = fdr.DataReader(code, 전체날짜).dropna(axis=0)
    종가데이터 = 증시정보['Close'].values

    종가데이터순번넣기 = []
    index = 0
    for data in 종가데이터:
        종가데이터순번넣기.append([index, data])
        index += 1

    현재값 = 종가데이터순번넣기[-1][1]

    # print("=================저항선=====================")
    그래프저항점 = []
    그래프저항점 = 저항선찾습니다(종가데이터순번넣기, [])
    저항선변화율 = round((그래프저항점[-1][1] - 그래프저항점[0][1]) / (그래프저항점[-1][0] - 그래프저항점[0][0]), 2)
    저항선변화량 = 저항선변화율 * (종가데이터순번넣기[-1][0] - 그래프저항점[-1][0])
    고가예측값 = 그래프저항점[-1][1] + 저항선변화량
    
    # print(종가데이터순번넣기[-1], 저항선변화율)
    # print(그래프저항점)
    # print(고가예측값)

    # print("=================지지선=====================")
    그래프지지점 = []
    그래프지지점 = 지지선찾습니다(종가데이터순번넣기, [])
    지지선변화율 = round((그래프지지점[-1][1] - 그래프지지점[0][1]) / (그래프지지점[-1][0] - 그래프지지점[0][0]), 2)
    지지선변화량 = 지지선변화율 * (종가데이터순번넣기[-1][0] - 그래프지지점[-1][0])
    저가예측값 = 그래프지지점[-1][1] + 지지선변화량

    # print(종가데이터순번넣기[-1], 지지선변화율)
    # print(그래프지지점)
    # print(저가예측값)

    저항평균변화율 = round((저항선변화율 + 지지선변화율) / 2, 2)
    저항평균변화량 = 저항평균변화율 * (종가데이터순번넣기[-1][0] - 그래프저항점[-1][0])
    저항평균예측값 = 그래프저항점[-1][1] + 저항평균변화량
    한달뒤저항평균예측값 = round(저항평균예측값 + (저항평균변화율 * 19), 2)

    지지평균변화율 = round((저항선변화율 + 지지선변화율) / 2, 2)
    지지평균변화량 = 지지평균변화율 * (종가데이터순번넣기[-1][0] - 그래프지지점[-1][0])
    지지평균예측값 = 그래프지지점[-1][1] + 지지평균변화량
    한달뒤지지평균예측값 = round(지지평균예측값 + (지지평균변화율 * 19), 2)

    # print("========================[결과]======================")
    # print(저항평균예측값, 한달뒤저항평균예측값, 저항평균변화율)
    # print(지지평균예측값, 한달뒤지지평균예측값, 지지평균변화율)
    # print("==================================================")

    지지저항변화율평균값 = round((저항평균변화율 + 지지평균변화율) / 2, 2)

    return 한달뒤저항평균예측값, 한달뒤지지평균예측값, 저항평균예측값, 지지평균예측값, 현재값, 고가예측값, 저가예측값, 지지저항변화율평균값

def findStockPeaksAndTroughs(code, term):
    if (term == 99999): 
        return {
            'expectValue': 0,
            'afterMonthExpectValue': 0,
            'nowValue': 0,
            'bottomValue': 0,
            'topValue': 0,
            'expectRatioValue': 0
        }

    after_month_top_value, after_month_bottom_value, top_value, bottom_value, now_value, max_value, min_value, expect_ratio_value = 고점저점예측(code, term)

    return {
        'expectValue': float(round((top_value + bottom_value + max_value + min_value) / 4, 2)),
        'afterMonthExpectValue': float(round((after_month_top_value + after_month_bottom_value) / 2, 2)),
        'nowValue': int(now_value),
        'bottomValue': float(round((bottom_value + min_value) / 2, 2)),
        'topValue': float(round((top_value + max_value) / 2, 2)),
        'expectRatioValue': float(expect_ratio_value)
    }

# print(findStockPeaksAndTroughs('005930', 29))