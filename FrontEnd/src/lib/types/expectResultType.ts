export type ExpectResultType = {
  expectValue: number,
  afterMonthExpectValue: number,
  nowValue: number,
  bottomValue: number,
  topValue: number,
  expectRatioValue: number
}

export type OverallStockFinalObjectType = {
  isOverGoldenCross: boolean; // 골든크로스 초과 여부 (20일 이평선이 60일 이평선 돌파 여부)
  isNearGoldenCross: boolean; // 골든크로스 근접 여부 (오늘 기준 20일 이평선 값과 60일 이평선 값의 차이가 현재가 기준 5% 이내 여부)
  generalizedPricePosition: number | null; // 일반화된 가격 위치 (오늘 기준 볼린져 밴드 상한 = 100, 하한 값 = 0을 기준으로 현재가의 위치가 어디에 위치하는지 일반화된 값, 상한이나 하한을 초과한 경우 100을 넘어서거나 음수값이 될 수 있음)
  stockFinanceScore: number; // 종목 최종 결과 점수
}