import { getFinanceDataList } from "$lib/api-connector/FinanceApi";
import { getSearchResultByNaverApi } from '$lib/api-connector/NaverApi';
import { sendFinanceResultByKakaoApi } from '$lib/api-connector/KakaoApi';
import _ from 'lodash';

/**
  * 주가 데이터 가져오기
*/
export const getFinanceDataListByChartMode = async (symbol: string, duration: number = 36, isMonth: boolean = true, cancelController: any = null) => {
  let resultList: any = []; 

  let result = await getFinanceDataList({symbol: symbol, duration: duration, isMonth: isMonth}, cancelController);

  let dataObject = result?.data;

  if (!!!dataObject || Object.keys(dataObject).length < 1) {
    return resultList;
  }

  for (let item of Object.keys(dataObject)) {
    if (!!!dataObject[item]?.Open) {
      continue;
    }

    resultList.push({Date: item, ...dataObject[item]});
  }

  return resultList;
}

export const setUpDownRatioTag = (originValue: number | string, targetValue: number | string) => {
  let ratioValue: string = '0';
  let fontColor: string = '#000000';
  let upDownIcon: string = '';

  const originValueNumber = typeof originValue === 'string' ? parseFloat(originValue) : originValue;
  const targetValueNumber = typeof targetValue === 'string' ? parseFloat(targetValue) : targetValue;
  
  // 오늘대비 예측가가 up, down인지에 따라 아이콘 표시 적용
  if (originValueNumber !== targetValueNumber) {
    upDownIcon = originValueNumber > targetValueNumber ? '▼' : '▲';
    fontColor = originValueNumber > targetValueNumber ? 'blue' : 'red';
  }

  ratioValue = calculateChangeRate(originValueNumber, targetValueNumber);

  return `<span style="color: ${fontColor}">${upDownIcon}${ratioValue ?? '-'}%</span>`
}

/**
 * 현재가와 예측값을 받아 변동 비율(%)을 계산하는 함수
 * @param currentPrice - 현재가 (number)
 * @param predictedPrice - 예측값 (number)
 * @returns 변동 비율 (%) (소수점 둘째 자리까지)
 */
export const calculateChangeRate = (currentPrice: number, predictedPrice: number): string => {
  if (currentPrice === 0) {
    return '0';
  }

  // 변동 비율 계산
  const changeRate = ((predictedPrice - currentPrice) / currentPrice) * 100;

  // 소수점 둘째 자리까지 반올림
  return changeRate.toFixed(2);
}

export const setUpDownIcon = (changeRatio: any) => {
  if (!!!changeRatio || changeRatio === '0') {
    return '';
  }

  return changeRatio > 0 ? '▲' : '▼';
}

export const setUpDownColor = (changeRatio: any) => {
  if (!!!changeRatio || changeRatio === '0') {
    return 'black';
  }

  return changeRatio > 0 ? 'red' : 'blue';
}

/**
 * 주어진 값을 특정 범위 내로 제한하는 함수
 * @param value 
 * @param minValue 
 * @param maxValue 
 * @returns 
 */
export const clip = (value: number, minValue: number, maxValue: number) => {
  return Math.min(Math.max(value, minValue), maxValue);
}

/**
 * 안전하게 정규화하여 0에서 1 사이의 값으로 변환
 * @param value 
 * @param averageValue 
 * @returns 
 */
export const selfNormalize = (value: number, minValue: number, maxValue: number) => {
  const clippedValue = clip(value, minValue, maxValue);

  return parseFloat(((clippedValue - minValue) / (maxValue - minValue)).toFixed(2));
}

/**
 * 기간에 따른 vmma (거래량 가중 이동평균) 값 계산
 * @param dataList 
 * @param day 
 * @returns 
 */
const getVWMAValue = (dataList: any, day: number) => {
  let multiplyVolumeAndCloseValue: number = 0;
  let totalVolumeValue: number = 0;

  for (let lastIndex = dataList.length - 1; lastIndex >= dataList.length - day; lastIndex--) {
    multiplyVolumeAndCloseValue += (dataList[lastIndex]?.Volume ?? 0) * (dataList[lastIndex]?.Open ?? 0); 
    totalVolumeValue += (dataList[lastIndex]?.Volume ?? 0)
  }

  return parseFloat((multiplyVolumeAndCloseValue / totalVolumeValue).toFixed(2))
}

/**
 * 현재 거래량과 평균 거래량을 기반으로 비율 값을 계산
 */
const getCalcComputeVolumeRatio = (dataList: any, day: number) => {
  let avgVolumeValue: number = 0;
  const listLength: number = dataList.length;

  if (listLength < 1) {
    return avgVolumeValue;
  }

  avgVolumeValue = parseFloat((_.sumBy(dataList.slice(listLength - day, listLength), (data: any) => { 
    return parseFloat(data?.Volume); 
  }) / day).toFixed(2));

  return parseFloat(calculateChangeRate(dataList[listLength - 1]?.Volume, avgVolumeValue));
}

/**
 * 목록 평균값 계산
 * @param values 
 * @returns 
 */
const getAverageValue = (values: any) => {
  let sumValue: number = 0;

  if (values.length < 1) {
    return sumValue;
  }

  for (let value of values) {
    sumValue += parseFloat(value);
  }

  return parseFloat((sumValue / values.length).toFixed(2))
}

/**
 * 이평선 값 계산
 * @param dataList 
 * @param day 
 * @returns 
 */
const getCalcMoveAvgValue = (dataList: any, day: number) => {
  if (dataList.length < day) {
    return 0;
  }

  const listLength: number = dataList.length;

  return parseFloat((_.sumBy(dataList.slice(listLength - day, listLength), (data: any) => {
    return parseFloat(data?.Close);
  }) / day).toFixed(2));
}

/**
 * 해당 주가의 여러 요인들을 종합하여 각 요인별 점수를 계산하여 일반화하는 함수 (0 ~ 1 사이의 소숫점으로 일반화)
 * [사용하는 요인들]
 * 1. 5, 20, 60일 이동평균선 현재 가 대비 현재가
 * 3. 60일 VWMA(거래량 가중 이동평균가)
 * 4. 유동성 비율
 * 5. 60일 평균 거래량 대비 현재가
 * 6. 지지, 저항선 현재 가
 * 7. 예측 추세선 기울기
 * 
 * @param dataList 
 * @param companyMarcap 
 * @param todayAmount 
 * @param topValue 
 * @param bottomValue 
 * @param expectValue 
 * @param expectRatioValue 
 * @returns 
 */
export const calculateExpectFinanceScore = (
  dataList: any,
  companyMarcap: any,
  todayAmount: any,
  topValue: any,
  bottomValue: any,
  expectValue: any,
  expectRatioValue: any
) => {
  const resultObject = {
    crossNormalizeValue: 0,
    volumeNormalizeValue: 0,
    lineNormalizeValue: 0,
    expectNormalizeValue: 0
  }

  let nowValue = dataList[dataList.length - 1]?.Close;
  // 5일 이평선 값
  let ma5Value = getCalcMoveAvgValue(dataList, 5);
  // 20일 이평선 값
  let ma20Value = getCalcMoveAvgValue(dataList, 20);
  // 60일 이평선 값
  let ma60Value = getCalcMoveAvgValue(dataList, 60);

  // 60일 VWMA(거래량 가중 이동평균)
  let vwma60Value = getVWMAValue(dataList, 60);

  /**
   * 추세신호 (가중치 35% - 초기 값)
   */
  let goldenShortCross = nowValue > ma5Value ? 15 : -15;
  let goldenMiddleCross = ma5Value > ma20Value ? 15 : -15;
  let goldenLargeCross = ma20Value > ma60Value ? 15 : -15;
  let upDownCross = expectRatioValue > 0 ? 15 : -15;
  // 추세신호
  let totalSumCross = goldenShortCross + goldenMiddleCross + goldenLargeCross + upDownCross;
  resultObject.crossNormalizeValue = selfNormalize(totalSumCross, -60, 60);

  /**
   * 거래동력 VWMA & 거래량 평균 대비 현재가 비율 & 유동성비율 (가중치 25% - 초기 값)
   */
  let calcVWMAValue = parseFloat(calculateChangeRate(ma60Value, vwma60Value)) > 0 ? 15 : -15;
  let calcBonusValue = (totalSumCross > 0 && calcVWMAValue > 0) ? 15 : 0;
  let calcMinusValue = (totalSumCross < 0 && calcVWMAValue < 0) ? -15 : 0;
  // 거래동력 VWMA
  let totalSumVWMA = calcVWMAValue + calcBonusValue + calcMinusValue;
  // 거래량 평균 대비 현재가 비율
  let calcComputeVolumeRatio = getCalcComputeVolumeRatio(dataList, 60);
  // 유동성비율
  let calcTodayVolumeRatioValue = Number.isNaN(todayAmount / companyMarcap) ? 0 : (todayAmount / companyMarcap) * 100;
  resultObject.volumeNormalizeValue = calcTodayVolumeRatioValue === 0 ? getAverageValue([selfNormalize(totalSumVWMA, -30, 30), selfNormalize(calcComputeVolumeRatio, -100, 100)]) : getAverageValue([selfNormalize(totalSumVWMA, -30, 30), selfNormalize(calcComputeVolumeRatio, -100, 100), selfNormalize(calcTodayVolumeRatioValue, 0, 2)]);

  /**
   * 지지/저항 (가중치 15% - 초기 값)
   */
  let lineValue: number = 0;
  if (nowValue > topValue) {
    lineValue = 15;
  } else if (nowValue < bottomValue) {
    lineValue = -15;
  } else {
    lineValue = 0;
  }
  resultObject.lineNormalizeValue = selfNormalize(lineValue, -15, 15);

  /**
   * 예측 추세값과 비교 (가중치 25% - 초기 값)
   */
  let calcExpectValue = parseFloat(calculateChangeRate(nowValue, expectValue));
  resultObject.expectNormalizeValue = selfNormalize(calcExpectValue, -30, 30);

  return resultObject;
}

/**
 * 뉴스정보 조회
 * @param searchQuery 
 * @returns 
 */
export const getNewInfoList = async (
  searchQuery: string, 
  displayCount: number,
  startCount: number,
  sortType: 'sim' | 'date' = 'sim',
  filter: 'all' = 'all'
) => {
  const result = await getSearchResultByNaverApi('news', {
    query: searchQuery,
    display: displayCount,
    start: startCount,
    sort: sortType,
    filter: filter
  })

  if (!!!result?.items || result?.items.length < 1) {
    return [];
  }

  return result.items;
}

/**
 * 카카오로 주가 통계 결과 값 전송
 * @param searchQuery 
 * @returns 
 */
export const sendFinanceResult = async (
  accessCode: string,
  accessToken: string,
  text: string = '',
  link: {
    'web_url': string,
    'mobile_web_url': string
  } | Object = {},
  buttonTitle?: string,
  objectType: string = 'text'
) => {
  const result = await sendFinanceResultByKakaoApi(accessCode, accessToken, link, {
    object_type: objectType,
    text: text,
    button_title: buttonTitle
  })

  return result;
}