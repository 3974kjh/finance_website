import { getFinanceDataList } from "$lib/api-connector/FinanceApi";
import { getSearchResultByNaverApi } from '$lib/api-connector/NaverApi';
import { sendFinanceResultByKakaoApi } from '$lib/api-connector/KakaoApi';
import _ from 'lodash';
import type { OverallStockFinalObjectType } from "$lib/types";
import { formatCostValue } from "$lib/utils/CommonHelper";

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
    expectNormalizeValue: 0,
    bandPosition: 0,
    isNearLowerBand: false,
    isOverGoldenCross: false,
    isNearGoldenCross: false
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

  // 오늘 기준 볼린저 밴드 값 조회
  const todayBollingerBands = getTodayBollingerBands(dataList, 20, 2);
  resultObject.isNearLowerBand = todayBollingerBands?.isNearLowerBand ?? false;
  resultObject.bandPosition = todayBollingerBands?.bandPosition ?? 0;

  /**
   * 골든크로스 여부 확인
   * @param ma20Value 
   * @param ma60Value 
   * @returns 
   */
  resultObject.isOverGoldenCross = isOverGoldenCross(ma20Value, ma60Value);

  /**
   * 골든크로스 임박 여부 확인
   * @param nowValue 
   * @param ma20Value 
   * @param ma60Value 
   * @returns 
   */
  resultObject.isNearGoldenCross = isNearGoldenCross(nowValue, ma20Value, ma60Value);

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

/**
 * 골든크로스 발생 여부 확인
 * 20일 이동평균선이 60일 이동평균선을 상향 돌파했는지 확인
 * @param ma20Value - 20일 이동평균 값
 * @param ma60Value - 60일 이동평균 값
 * @returns 골든크로스 발생 여부 (true: 발생, false: 미발생)
 */
export const isOverGoldenCross = (ma20Value: number | string | null, ma60Value: number | string | null): boolean => {
  if (!ma20Value || !ma60Value) {
    return false;
  }

  const ma20 = typeof ma20Value === 'string' ? parseFloat(ma20Value) : ma20Value;
  const ma60 = typeof ma60Value === 'string' ? parseFloat(ma60Value) : ma60Value;

  // 20일 이평선이 60일 이평선보다 위에 있으면 골든크로스
  return ma20 > ma60;
}

/**
 * 골든크로스 임박 여부 확인
 * 현재가와 이동평균선의 위치를 기반으로 골든크로스가 임박했는지 판단
 * @param nowValue - 현재가
 * @param ma20Value - 20일 이동평균 값
 * @param ma60Value - 60일 이동평균 값
 * @returns 골든크로스 임박 여부 (true: 임박, false: 아님)
 */
export const isNearGoldenCross = (
  nowValue: number | string,
  ma20Value: number | string | null,
  ma60Value: number | string | null
): boolean => {
  if (!ma20Value || !ma60Value) {
    return false;
  }

  const now = typeof nowValue === 'string' ? parseFloat(nowValue) : nowValue;
  const ma20 = typeof ma20Value === 'string' ? parseFloat(ma20Value) : ma20Value;
  const ma60 = typeof ma60Value === 'string' ? parseFloat(ma60Value) : ma60Value;

  // 20일 이평선과 60일 이평선의 차이가 2% 이내이고, 현재가가 둘 다보다 높으면 임박
  const diff = Math.abs(ma20 - ma60);
  const diffPercent = (diff / now) * 100;

  return diffPercent <= 2 && now > ma20 && now > ma60;
}

/**
 * 볼린저 밴드 내에서 현재가의 위치를 0~1 사이로 정규화
 * 0에 가까울수록 하한선 근처, 1에 가까울수록 상한선 근처
 * @param nowValue - 현재가
 * @param upBollingerBand - 볼린저 밴드 상한 값
 * @param downBollingerBand - 볼린저 밴드 하한 값
 * @returns 정규화된 위치 값 (0~1, 범위를 벗어나면 0 미만 또는 1 초과 가능)
 */
export const calculateGeneralizedPricePosition = (
  nowValue: number | string,
  upBollingerBand: number | string | null,
  downBollingerBand: number | string | null
): number => {
  if (!upBollingerBand || !downBollingerBand) {
    return 0.5; // 기본값: 중간
  }

  const now = typeof nowValue === 'string' ? parseFloat(nowValue) : nowValue;
  const upper = typeof upBollingerBand === 'string' ? parseFloat(upBollingerBand) : upBollingerBand;
  const lower = typeof downBollingerBand === 'string' ? parseFloat(downBollingerBand) : downBollingerBand;

  // 밴드 폭이 0이면 중간값 반환
  if (upper === lower) {
    return 0.5;
  }

  // 현재가의 볼린저 밴드 내 위치를 0~1로 정규화
  // 하한 = 0, 상한 = 1, 중간 = 0.5
  const position = (now - lower) / (upper - lower);

  return parseFloat(position.toFixed(2));
}

/**
 * 종목 최종 결과 텍스트 생성
 * @param stockName - 종목명
 * @param overallStocFinalObject - 종목 최종 결과 객체
 * @returns 종목 최종 결과 텍스트
 */
export const makeStockFinalReportText = (
  stockName: string,
  overallStocFinalObject: OverallStockFinalObjectType
) => {
  /**
   * 현재가의 위치를 기반으로 텍스트 생성
   * @param max 최대값
   * @param position 현재가의 위치
   * @param isReversal 반전 여부
   * @returns 현재가의 위치를 기반으로 텍스트 생성
   */
  const pricePositionText = (
    max: number,
    position: number,
    isReversal: boolean = false
  ) => {
    let text: string = '';
    let scoreText: string = '';
    let riskLevel: string = '';
    let positionScore: number = 0;

    if (position >= max) {
      text = '볼린저밴드 상단을 돌파하여 과매수 구간에 진입했습니다.';
      riskLevel = '높음';
    } else if (position >= max * 0.7) {
      text = '볼린저밴드 상단 근처로 저항선에 근접한 상태입니다.';
      riskLevel = '중간';
    } else if (position >= max * 0.4) {
      text = '볼린저밴드 중심선 부근으로 균형잡힌 위치에 있습니다.';
      riskLevel = '낮음';
    } else if (position >= 0) {
      text = '볼린저밴드 하단 근처로 지지선에 근접한 상태입니다.';
      riskLevel = '낮음';
    } else {
      text = '볼린저밴드 하단을 이탈하여 과매도 구간에 진입했습니다.';
      riskLevel = '중간';
    }

    positionScore = max === 100 ? position : position * 100;

    if (positionScore >= 100) {
      scoreText = isReversal ? '심각한 과대평가 (투자 위험도: 매우높음)' : '매력적인 저평가 (기회도: 매우높음)';
    } else if (positionScore >= 70) {
      scoreText = isReversal ? '과대평가 구간 (투자 위험도: 높음)' : '저평가 구간 (기회도: 높음)';
    } else if (positionScore >= 40) {
      scoreText = '적정가치 평가 구간 (투자 위험도: 보통)';
    } else if (positionScore >= 20) {
      scoreText = isReversal ? '저평가 구간 (기회도: 높음)' : '과대평가 구간 (투자 위험도: 높음)';
    } else {
      scoreText = isReversal ? '심각한 저평가 (기회도: 매우높음)' : '심각한 과대평가 (투자 위험도: 매우높음)';
    }

    return {
      text: `${text} 현재 <b>${scoreText}</b> 상태로 평가됩니다.`,
      positionScore: isReversal ? 100 - positionScore : positionScore,
      riskLevel
    };
  }

  // 종목 최종 결과 텍스트
  let reportText: string = '';
  // 종목 살지말지 결정 텍스트
  let reportBuyOrSellText: string = '';
  // 점수 총합
  let priceTotalScore: number = 0;
  // 종목 구매 등급
  let stockBuyLevel: 'S+' | 'S' | 'A+' | 'A' | 'B' | 'C' = 'C';

  if (overallStocFinalObject.generalizedPricePosition === null) {
    return {
      reportText: reportText,
      stockBuyLevel: stockBuyLevel
    };
  }

  reportText += `<div class='bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border-l-4 border-blue-500 mb-4'><h3 class='text-lg font-bold text-gray-800 mb-2'><b>${stockName}</b> 기술적 분석 리포트</h3>`;

  // 골든크로스 상태 분석
  let trendStrength = 0; // 추세 강도
  if (overallStocFinalObject.isOverGoldenCross) {
    reportText += `<div class='mb-2'><span class='inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800'>상승 추세 확인</span> 20일 이동평균선이 60일 이동평균선을 <b>상향 돌파</b>하여 <b>상승 모멘텀</b>이 형성된 상태입니다.</div>`;
    trendStrength += 30;
  }

  if (overallStocFinalObject.isNearGoldenCross) {
    reportText += '<div class="mb-2"><span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800">골든크로스 임박</span> <b>매우 중요한 시점입니다.</b> 단기 이동평균선이 장기 이동평균선 돌파를 준비 중으로, <b>상승 전환점</b>에 위치해 있습니다.</div>';
    trendStrength += 25;
  } else if (!overallStocFinalObject.isOverGoldenCross) {
    reportText += '<div class="mb-2"><span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">추세 중립</span> 현재 골든크로스 신호가 감지되지 않아 <b>추세 전환의 명확한 신호가 부족</b>한 상황입니다.</div>';
  }
  
  if (overallStocFinalObject.generalizedPricePosition) {
    const pricePositionTextResult = pricePositionText(1, overallStocFinalObject.generalizedPricePosition, true);
    reportText += `<div class='mb-3'><b>📊 볼린저밴드 분석:</b> 현재가 위치 지수 <b>${(overallStocFinalObject.generalizedPricePosition * 100).toFixed(1)}%</b><br/>${pricePositionTextResult.text}</div>`;
    priceTotalScore += pricePositionTextResult.positionScore;
    trendStrength += pricePositionTextResult.riskLevel === '낮음' ? 20 : (pricePositionTextResult.riskLevel === '중간' ? 10 : 0);
  }

  if (overallStocFinalObject.stockFinanceScore) {
    const stockFinanceScoreTextResult = pricePositionText(100, overallStocFinalObject.stockFinanceScore, false);
    let fundamentalLevel = '';
    if (overallStocFinalObject.stockFinanceScore >= 80) {
      fundamentalLevel = '우수';
      trendStrength += 25;
    } else if (overallStocFinalObject.stockFinanceScore >= 60) {
      fundamentalLevel = '양호';
      trendStrength += 15;
    } else if (overallStocFinalObject.stockFinanceScore >= 40) {
      fundamentalLevel = '보통';
      trendStrength += 5;
    } else {
      fundamentalLevel = '미흡';
    }
    
    reportText += `<div class='mb-3'><b>📈 펀더멘털 분석:</b> 종목 지표 점수 <b>${overallStocFinalObject.stockFinanceScore}점</b> (${fundamentalLevel})<br/>${stockFinanceScoreTextResult.text}</div>`;
    priceTotalScore += stockFinanceScoreTextResult.positionScore;
  }

  reportText += '</div>'; // 분석 리포트 div 닫기

  // 종합 투자 등급 계산 (기술적 분석 + 추세 강도)
  const totalInvestmentScore = priceTotalScore + trendStrength;
  let investmentGrade = '';
  let riskAssessment = '';
  let investmentStrategy = '';
  let timeHorizon = '';

  // 조건별 가중치 계산
  const hasStrongTrend = overallStocFinalObject.isNearGoldenCross && overallStocFinalObject.isOverGoldenCross;
  const hasMomentum = overallStocFinalObject.isNearGoldenCross || overallStocFinalObject.isOverGoldenCross;
  const isHighQuality = overallStocFinalObject.stockFinanceScore >= 70;
  const isFairValued = priceTotalScore >= 120 && priceTotalScore <= 160;

  if (totalInvestmentScore >= 220 && hasStrongTrend && isHighQuality) {
    investmentGrade = 'S+ 등급 (최우선 투자 대상)';
    riskAssessment = isFairValued ? '리스크: 매우낮음 | 기대수익률: 매우높음' : '리스크: 낮음 | 기대수익률: 매우높음';
    investmentStrategy = isFairValued ? '즉시 적극매수 권장. 포트폴리오 비중 확대 검토 (적정가치 구간)' : '즉시 적극매수 권장. 포트폴리오 비중 확대 검토';
    timeHorizon = '단기~중기 (1-6개월)';
    reportBuyOrSellText = '🚀 <b>최우선 매수 대상</b>';
    stockBuyLevel = 'S+';
  } else if (totalInvestmentScore >= 190 && hasMomentum) {
    investmentGrade = 'S 등급 (우수한 투자 기회)';
    riskAssessment = isFairValued ? '리스크: 낮음 | 기대수익률: 높음' : (priceTotalScore >= 160 ? '리스크: 중간 | 기대수익률: 높음' : '리스크: 낮음 | 기대수익률: 높음');
    investmentStrategy = isFairValued ? '적극매수 권장. 분할 매수 전략 고려 (적정가치 구간)' : '적극매수 권장. 분할 매수 전략 고려';
    timeHorizon = '중기 (3-6개월)';
    reportBuyOrSellText = '⭐ <b>적극 매수 추천</b>';
    stockBuyLevel = 'S';
  } else if (totalInvestmentScore >= 160) {
    investmentGrade = 'A+ 등급 (양호한 투자 기회)';
    riskAssessment = isFairValued ? '리스크: 낮음 | 기대수익률: 중상' : '리스크: 중간 | 기대수익률: 중상';
    investmentStrategy = hasMomentum ? 
      (isFairValued ? '매수 권장. 시장 상황 고려하여 진입 (적정가치 구간)' : '매수 권장. 시장 상황 고려하여 진입') : 
      (isFairValued ? '신중한 매수. 기술적 신호 재확인 필요 (적정가치 구간)' : '신중한 매수. 기술적 신호 재확인 필요');
    timeHorizon = '중기 (2-4개월)';
    reportBuyOrSellText = '📈 <b>매수 권장</b>';
    stockBuyLevel = 'A+';
  } else if (totalInvestmentScore >= 120) {
    investmentGrade = 'A 등급 (보통 수준)';
    riskAssessment = isFairValued ? '리스크: 중간 | 기대수익률: 보통' : '리스크: 중간 | 기대수익률: 보통';
    investmentStrategy = isFairValued ? '관망 후 매수. 적정가치 구간으로 안정적' : '관망 후 매수. 추가 긍정 신호 대기';
    timeHorizon = '중장기 (3-6개월)';
    reportBuyOrSellText = hasMomentum ? '🔍 <b>관심종목 등록</b>' : '⏳ <b>관망 권장</b>';
    stockBuyLevel = 'A';
  } else if (totalInvestmentScore >= 80) {
    investmentGrade = 'B 등급 (투자 주의)';
    riskAssessment = '리스크: 높음 | 기대수익률: 낮음';
    investmentStrategy = '투자 보류. 기본적 변화 관찰 필요';
    timeHorizon = '장기 관찰 (6개월 이상)';
    reportBuyOrSellText = '⚠️ <b>투자 보류</b>';
    stockBuyLevel = 'B';
  } else {
    investmentGrade = 'C 등급 (투자 부적합)';
    riskAssessment = '리스크: 매우높음 | 기대손실 가능성';
    investmentStrategy = '투자 금지. 다른 대안 종목 검토';
    timeHorizon = '투자 대상 제외';
    reportBuyOrSellText = '🚫 <b>투자 비추천</b>';
    stockBuyLevel = 'C';
  }

  // 특별 보너스/패널티 적용
  let specialNote = '';
  if (overallStocFinalObject.isNearGoldenCross && !overallStocFinalObject.isOverGoldenCross && priceTotalScore >= 140) {
    specialNote = isFairValued ? 
      '<div class="mt-2 p-2 bg-green-50 rounded"><span class="text-green-700"><b>🎯 골든크로스 임박 + 적정가치:</b> 상승 전환 신호가 강하며 가치평가도 안정적입니다.</span></div>' :
      '<div class="mt-2 p-2 bg-green-50 rounded"><span class="text-green-700"><b>🎯 골든크로스 임박 보너스:</b> 상승 전환 신호가 강하게 감지됩니다.</span></div>';
  } else if (priceTotalScore >= 180 && !hasMomentum) {
    specialNote = '<div class="mt-2 p-2 bg-orange-50 rounded"><span class="text-orange-700"><b>⚡ 모멘텀 부족 주의:</b> 높은 점수에도 불구하고 추세 신호가 약합니다.</span></div>';
  } else if (isFairValued && isHighQuality) {
    specialNote = '<div class="mt-2 p-2 bg-blue-50 rounded"><span class="text-blue-700"><b>💎 안정성 우수:</b> 적정가치 구간과 우수한 펀더멘털을 동시에 만족합니다.</span></div>';
  }

  reportBuyOrSellText += `
    <div class='mt-4 p-4 bg-white rounded-lg shadow-sm'>
      <h4 class='text-base font-bold text-gray-800 mb-3 pb-2 border-b border-gray-200'>📋 투자 분석 요약</h4>
      <div class='space-y-2 text-sm text-gray-700'>
        <div class='flex items-start'>
          <span class='font-semibold text-gray-600 w-20 flex-shrink-0'>투자등급:</span>
          <span class='font-medium'>${investmentGrade}</span>
        </div>
        <div class='flex items-start'>
          <span class='font-semibold text-gray-600 w-20 flex-shrink-0'>종합점수:</span>
          <span class='font-medium'>${totalInvestmentScore.toFixed(0)}점</span>
        </div>
        <div class='flex items-start'>
          <span class='font-semibold text-gray-600 w-20 flex-shrink-0'>위험분석:</span>
          <span>${riskAssessment}</span>
        </div>
        <div class='flex items-start'>
          <span class='font-semibold text-gray-600 w-20 flex-shrink-0'>투자전략:</span>
          <span>${investmentStrategy}</span>
        </div>
        <div class='flex items-start'>
          <span class='font-semibold text-gray-600 w-20 flex-shrink-0'>권장기간:</span>
          <span>${timeHorizon}</span>
        </div>
      </div>
      ${specialNote}
    </div>`;

  return {
    reportText: `
      <div class='investment-analysis-report max-w-4xl mx-auto'>
        <div class='text-xl font-bold text-center mb-6 p-4 bg-gradient-to-r from-slate-700 to-slate-800 text-white rounded-lg shadow-md'>
          📊 ${stockName} 투자 분석 보고서
        </div>
        
        <div class='recommendation-summary mb-6 p-4 text-center text-lg font-semibold rounded-lg shadow-sm ${
          reportBuyOrSellText.includes('최우선') || reportBuyOrSellText.includes('적극') ? 'bg-green-50 text-green-800' :
          reportBuyOrSellText.includes('권장') || reportBuyOrSellText.includes('관심') ? 'bg-blue-50 text-blue-800' :
          reportBuyOrSellText.includes('보류') ? 'bg-yellow-50 text-yellow-800' :
          'bg-red-50 text-red-800'
        }'>
          ${reportBuyOrSellText}
        </div>

        <div class='technical-analysis mb-6'>
          ${reportText}
        </div>
        
        <div class='disclaimer mt-8 p-4 bg-gray-50 rounded-lg text-xs text-gray-600 border-l-4 border-gray-300'>
          <div class='font-semibold text-gray-700 mb-2'>⚠️ 투자 유의사항</div>
          <div class='space-y-1'>
            <div>• 본 분석은 기술적 지표를 바탕으로 한 참고자료이며, 투자 결정은 개인의 판단과 책임하에 이루어져야 합니다.</div>
            <div>• 과거 데이터 기반 분석으로 미래 수익을 보장하지 않으며, 투자 손실 가능성을 충분히 고려하시기 바랍니다.</div>
            <div>• 투자 전 반드시 추가적인 정보 수집과 전문가 상담을 권장합니다.</div>
          </div>
        </div>
      </div>
    `,
    stockBuyLevel: stockBuyLevel
};
}

/**
 * 오늘 기준 볼린저 밴드 값 조회 (최적화된 단일 계산)
 * @param data - 차트 데이터 배열 (시간순 정렬, 최신 데이터가 마지막)
 * @param period - 기간 (기본값: 20일)
 * @param multiplier - 표준편차 배수 (기본값: 2)
 * @returns {{ upperBand: number, middleBand: number, lowerBand: number, currentPrice: number } | null}
 */
export const getTodayBollingerBands = (data: any, period: number = 20, multiplier: number = 2) => {
  // 데이터가 충분하지 않으면 null 반환
  if (!data || data.length < period) {
    return null;
  }

  // 최근 period개의 데이터만 추출 (오늘 포함)
  const recentData = data.slice(-period);
  
  // 한 번의 루프로 합계와 제곱합을 동시에 계산
  let sum = 0;
  let sumOfSquares = 0;
  
  for (let i = 0; i < period; i++) {
    const closePrice = recentData[i].Close || 0;
    sum += closePrice;
    sumOfSquares += closePrice * closePrice;
  }
  
  // 평균 계산 (중간선)
  const middleBand = sum / period;
  
  // 분산 계산: Var(X) = E(X²) - [E(X)]²
  const variance = (sumOfSquares / period) - (middleBand * middleBand);
  
  // 표준편차 계산
  const standardDeviation = Math.sqrt(variance);
  
  // 상한선과 하한선 계산
  const upperBand = middleBand + (multiplier * standardDeviation);
  const lowerBand = middleBand - (multiplier * standardDeviation);
  
  // 현재가(오늘 종가)
  const currentPrice = data[data.length - 1].Close || 0;

  const bandPosition = calculateGeneralizedPricePosition(currentPrice, upperBand, lowerBand);
  
  return {
    upperBand: parseFloat(upperBand.toFixed(2)),
    middleBand: parseFloat(middleBand.toFixed(2)),
    lowerBand: parseFloat(lowerBand.toFixed(2)),
    currentPrice: parseFloat(currentPrice.toFixed(2)),
    // 추가 정보
    standardDeviation: parseFloat(standardDeviation.toFixed(2)),
    // 현재가가 밴드의 어느 위치에 있는지 (0~1, 0.5가 중간)
    bandPosition: bandPosition,
    // 볼린저 밴드의 하단 부분에 위치하고 있는지 여부
    isNearLowerBand: bandPosition < 0.6, // 0.6 이하면 하단 부분에 위치하고 있는 것으로 판단
  };
}

/**
 * 볼린저 밴드 계산 함수
 * @param data - 데이터 리스트
 * @param period - 기간
 * @param multiplier - 곱수
 * @returns {upBollingerBandList: Array<number | null>, middleBollingerBandList: Array<number | null>, downBollingerBandList: Array<number | null>}
*/
export const calculateBollingerBands = (data: any, period: number = 20, multiplier: number = 2) => {
  const upBollingerBandList: (number | null)[] = [];
  const middleBollingerBandList: (number | null)[] = [];
  const downBollingerBandList: (number | null)[] = [];

  for (let index = 0; index < data.length; index++) {
    if (index < period - 1) {
      // 데이터가 부족한 경우 null로 표시
      upBollingerBandList.push(null);
      middleBollingerBandList.push(null);
      downBollingerBandList.push(null);
    } else {
      // 현재 기간의 데이터 추출
      const periodData = data.slice(index - period + 1, index + 1);
      
      // 중심선 (20일 이동평균) 계산
      const sum = periodData.reduce((acc: any, cur: any) => acc + cur.Open, 0);
      const middleBand = sum / period;
      
      // 표준편차 계산
      const squaredDifferences = periodData.map((item: any) => {
        const diff = item.Open - middleBand;
        return diff * diff;
      });

      const variance = squaredDifferences.reduce((acc: number, val: number) => acc + val, 0) / period;
      const standardDeviation = Math.sqrt(variance);
      
      // 상단 밴드와 하단 밴드 계산
      const upperBand = middleBand + (multiplier * standardDeviation);
      const lowerBand = middleBand - (multiplier * standardDeviation);
      
      // 값을 formatCostValue로 포맷팅
      const formattedMiddle = formatCostValue(middleBand);
      const formattedUpper = formatCostValue(upperBand);
      const formattedLower = formatCostValue(lowerBand);
      
      middleBollingerBandList.push(formattedMiddle ? parseFloat(formattedMiddle) : null);
      upBollingerBandList.push(formattedUpper ? parseFloat(formattedUpper) : null);
      downBollingerBandList.push(formattedLower ? parseFloat(formattedLower) : null);
    }
  }

  return {
    upBollingerBandList,
    middleBollingerBandList,
    downBollingerBandList
  };
}