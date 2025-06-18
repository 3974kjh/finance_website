<script lang="ts">
  import { onMount, tick, createEventDispatcher } from 'svelte';
  import { LineChart, ProgressCircle, NewsInfoListComponent } from '$lib/component';
  import { getExpectStockValue } from '$lib/api-connector/FinanceApi';
  import { getSearchResultByNaverApi } from '$lib/api-connector/NaverApi';
  import { 
    getFinanceDataListByChartMode, 
    setUpDownRatioTag, setUpDownIcon, setUpDownColor, 
    calculateExpectFinanceScore,
    getNewInfoList
  } from '$lib/main';
  import { calculateRatio, formatCostValue, formatIncludeComma } from '$lib/utils/CommonHelper';
  import { NaverFinanceImg, CompanyGuideImg } from '$lib/images/logo';

  export let singleChartInfo: {
		title: string,
		searchDuration: {month: number, week: number},
		chartMode: string,
		chartKey: string,
    detailInfo: any
	};

  const dispatch = createEventDispatcher();

  let dataList: any = [];

  let durationModeList: Array<{name: string, value: {month: number, week: number}, isSelected: boolean}> = [
    { name: '10 YEAR', value: {month: 120, week: 520}, isSelected: false },
    { name: '5 YEAR', value: {month: 60, week: 260}, isSelected: false },
    { name: '2 YEAR', value: {month: 24, week: 104}, isSelected: false },
    { name: '1 YEAR', value: {month: 12, week: 52}, isSelected: true },
    { name: '6 MONTH', value: {month: 6, week: 26}, isSelected: false }
  ]

  let expectValue: string = '';
  let afterMonthExpectValue: string = '';
  let nowValue: string = '';
  let bottomValue: string = '';
  let topValue: string = '';
  let expectRatioValue: string = '';

  let calcSignalScoreResult = {
    crossNormalizeValue: null as number | null,
    volumeNormalizeValue: null as number | null,
    lineNormalizeValue: null as number | null,
    expectNormalizeValue: null as number | null
  }

  let signalScoreWeight = {
    crossWeight: 35,
    volumeWeight: 25,
    lineWeight: 15,
    expectWeight: 25
  }

  let isProgress: boolean = false;

  let newInfoList: any = [];

  // 각 섹션의 펼침/접힘 상태 관리
  let sectionStates = {
    duration: false,     // 조회 기간 - 닫힌 상태
    prediction: true,    // 예측 정보
    movingAverage: true, // 이동평균선
    stockInfo: false,    // 종목 정보 - 닫힌 상태
    signalScore: false,  // 투자 신호 점수 - 닫힌 상태
    news: true          // 관련 뉴스
  };

  onMount(async () => {
    if (!!!singleChartInfo) {
      return;
    }

    isProgress = true;

    durationModeList = setSelectDurationModeList(durationModeList, singleChartInfo?.searchDuration);
    dataList = await setSingleChartDataList(singleChartInfo?.searchDuration);
    newInfoList = await getNewInfoList(singleChartInfo.title, 20, 1);

    isProgress = false;
  })

  const getSelectedDurationModeValue = (list: any) => {
    const selectedDurationMode = list.find((item: any) => item.isSelected);

    return selectedDurationMode?.value;
  }

  const setSelectDurationModeList = (list: any, durationValue: any) => {
    if (list.length < 1) {
      return [];
    }

    return list.map((item: any) => {
      if (item.value?.month === durationValue?.month) {
        return {
          ...item,
          isSelected: true
        }
      } else {
        return {
          ...item,
          isSelected: false
        }
      }
    })
  }

  /**
   * 해당 주식의 상세 그래프 표시를 위한 데이터 값 조회
  */
  const setSingleChartDataList = async (duration: {month: number, week: number}) => {
    const financeDataResult = await getFinanceDataListByChartMode(singleChartInfo.chartKey, duration.month, true);

    if (financeDataResult.length < 1) {
      return [];
    }
    
    const expectResult = await getExpectStockValue({symbol: singleChartInfo.chartKey, term: duration.week});

    if (!!!expectResult || !!!expectResult?.data || expectResult.length < 1) {
      return [];
    }

    nowValue = expectResult.data?.nowValue;
    expectValue = expectResult.data?.expectValue;
    afterMonthExpectValue = expectResult.data?.afterMonthExpectValue;
    bottomValue = expectResult.data?.bottomValue;
    topValue = expectResult.data?.topValue;
    expectRatioValue = expectResult.data?.expectRatioValue;

    // 이동평균 계산 함수
    const calculateMA = (data: any, moveSize: number): (number | string | null)[] => {
      const movingAverages: (number | string | null)[] = [];
      for (let index = 0; index < data.length; index++) {
        if (index < moveSize - 1) {
          // 데이터가 부족한 경우 null로 표시
          movingAverages.push(null);
        } else {
          const moveList = data.slice(index - moveSize + 1, index + 1);
          const sum = moveList.reduce((acc: any, cur: any) => acc + cur.Open, 0);
          movingAverages.push(formatCostValue(sum / moveSize));
        }
      }
      return movingAverages;
    };

    // 각 이동평균 계산
    const ma5 = calculateMA(financeDataResult, 5);
    const ma20 = calculateMA(financeDataResult, 20);
    const ma60 = calculateMA(financeDataResult, 60);

    // 해당 주가의 여러 요인들을 종합하여 각 요인별 점수를 계산하여 일반화한 값 가져오기
    calcSignalScoreResult = calculateExpectFinanceScore(
      financeDataResult,
      parseFloat(singleChartInfo.detailInfo?.marcap),
      parseFloat(singleChartInfo.detailInfo?.amount),
      parseFloat(topValue),
      parseFloat(bottomValue),
      parseFloat(expectValue),
      parseFloat(expectRatioValue)
    )

    return financeDataResult.map((data: any, index: number) => {
      return {
        ...data,
        afterMonthExpectValue: expectResult.data?.afterMonthExpectValue,
        bottomValue: expectResult.data?.bottomValue,
        expectValue: expectResult.data?.expectValue,
        nowValue: expectResult.data?.nowValue,
        topValue: expectResult.data?.topValue,
        ma5: ma5[index] ?? undefined,
        ma20: ma20[index] ?? undefined,
        ma60: ma60[index] ?? undefined,
      }
    });
  }

  /**
   * 가중치 총 합 리턴
  */
  const sumWeight = (scoreWeight: any) => {
    return scoreWeight.crossWeight + scoreWeight.volumeWeight + scoreWeight.lineWeight + scoreWeight.expectWeight;
  }

  /**
   * score와 가중치를 곱한 최종 결과 값 리턴
  */
  const calculateSignalScore = (score: any, scoreWeight: any) => {
    return scoreWeight.crossWeight * score.crossNormalizeValue + scoreWeight.volumeWeight * score.volumeNormalizeValue + scoreWeight.lineWeight * score.lineNormalizeValue + scoreWeight.expectWeight * score.expectNormalizeValue;
  }

  /**
   * 버튼 기간 명 표시 문구
  */
  const showDurationButtonText = (durationName: string) => {
    if (durationName.includes(' YEAR')) {
      return durationName.replace(' YEAR', '년');
    } else {
      return durationName.replace(' MONTH', '달');
    }
  }

  /**
   * 현재 선택된 기간 반환
  */
  const getSelectedDurationText = () => {
    const selectedDuration = durationModeList.find(item => item.isSelected);
    return selectedDuration ? showDurationButtonText(selectedDuration.name) : '1년';
  }

  let clientHeight: number = 0;

  $: console.log(clientHeight);

</script>

<div class="flex flex-col w-full h-full bg-gradient-to-br from-slate-50 to-gray-100 absolute p-3 space-y-3" style="top: 0px; left: 0px" bind:clientHeight={clientHeight}>
  {#if singleChartInfo}
    <div class="flex w-full h-auto items-center bg-white/80 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/50 px-4 py-3">
      <button 
        class="flex items-center justify-center w-10 h-10 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white rounded-xl shadow-md hover:shadow-lg transition-all duration-200 mr-4"
        on:click={() => {
          dispatch('closeSingleChartModeCallback');
        }}
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
        </svg>
      </button>
      <div class="flex grow justify-center">
        <h1 class="text-xl font-bold text-gray-800 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          {singleChartInfo?.title ?? '-'}
        </h1>
      </div>
      <div class="flex justify-end space-x-2">
        <a 
          class="flex items-center justify-center w-10 h-10 bg-white hover:bg-gray-50 border border-gray-200 rounded-xl shadow-md hover:shadow-lg transition-all duration-200"
          href="{`https://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A${singleChartInfo?.chartKey ?? ''}`}"
          title="FnGuide_{singleChartInfo?.title}"
          target="_blank"
          style="
            background-image: url({CompanyGuideImg});
            background-size: 20px 20px;
            background-position: center;
            background-repeat: no-repeat;
          "
        />
        <a
          class="flex items-center justify-center w-10 h-10 bg-white hover:bg-gray-50 border border-gray-200 rounded-xl shadow-md hover:shadow-lg transition-all duration-200"
          href="{`https://finance.naver.com/item/main.naver?code=${singleChartInfo?.chartKey ?? ''}`}"
          title="NAVER_{singleChartInfo?.title}"
          target="_blank"
          style="
            background-image: url({NaverFinanceImg});
            background-size: 20px 20px;
            background-position: center;
            background-repeat: no-repeat;
          "
        />
      </div>
    </div>
    <div class="flex flex-row w-full grow space-x-3" style="height: {clientHeight - 150}px">
      <div class="flex w-[80%] h-full bg-white/80 backdrop-blur-sm border border-gray-200/50 rounded-xl shadow-lg overflow-hidden">
        {#if dataList.length > 0 && isProgress === false}
          {#key dataList}
            <LineChart
              lineDataList={dataList}
              isMultiLine={true}
              isDetailMode={true}
            />
          {/key}
        {:else if isProgress}
          <div class="flex w-full h-full justify-center items-center">
            <ProgressCircle
              size={100}
              thickness={10}
              isLarge={true}
              text={'해당 종목 분석 중...'}
            />
          </div>
        {:else}
          <div class="flex w-full h-full justify-center items-center">
            <div class="text-center space-y-3">
              <div class="w-16 h-16 bg-gray-300 rounded-2xl flex items-center justify-center mx-auto">
                <svg class="w-8 h-8 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
              </div>
              <p class="text-gray-600 font-medium">해당 종목의 조회 데이터가 없습니다.</p>
            </div>
          </div>
        {/if}
      </div>
      <div class="flex flex-col w-[20%] h-full bg-white/80 backdrop-blur-sm border border-gray-200/50 rounded-xl shadow-lg overflow-hidden">
        <div class="flex-1 p-3 space-y-3 overflow-y-auto scrollbar-thin-custom">
          <!-- 조회 기간 설정 -->
          <div class="flex flex-col w-full bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200/50 rounded-xl overflow-hidden flex-shrink-0">
            <button 
              class="flex items-center justify-between w-full p-3 hover:bg-blue-100/50 transition-colors duration-200"
              on:click={() => sectionStates.duration = !sectionStates.duration}
            >
              <div class="flex items-center space-x-2">
                <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                </svg>
                <p class="font-semibold text-blue-800">조회 기간</p>
                {#if !sectionStates.duration}
                  <span class="text-sm text-blue-600 bg-blue-100 px-2 py-0.5 rounded-full">{getSelectedDurationText()}</span>
                {/if}
              </div>
              <svg class="w-4 h-4 text-blue-600 transition-transform duration-200 {sectionStates.duration ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </button>
            {#if sectionStates.duration}
              <div class="px-3 pb-3 space-y-2">
                <div class="flex flex-wrap gap-1">
                  {#each durationModeList as durationMode}
                    <button
                      class="px-2 py-1 text-xs font-medium rounded-lg transition-all duration-200 {durationMode.isSelected 
                        ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-md' 
                        : 'bg-white/80 text-blue-700 border border-blue-200 hover:bg-blue-50 hover:border-blue-300'}"
                      on:click={async () => {
                        isProgress = true;

                        durationModeList = setSelectDurationModeList(durationModeList, durationMode.value);
                        dataList = await setSingleChartDataList(durationMode.value);

                        isProgress = false;
                      }}
                    >
                      {showDurationButtonText(durationMode.name)}
                    </button>
                  {/each}
                </div>
              </div>
            {/if}
          </div>
          
          <!-- 예측 데이터 값 표시 -->
          <div class="flex flex-col w-full bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200/50 rounded-xl overflow-hidden flex-shrink-0">
            <button 
              class="flex items-center justify-between w-full p-3 hover:bg-emerald-100/50 transition-colors duration-200"
              on:click={() => sectionStates.prediction = !sectionStates.prediction}
            >
              <div class="flex items-center space-x-2">
                <svg class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                </svg>
                <p class="font-semibold text-emerald-800">예측 정보</p>
              </div>
              <svg class="w-4 h-4 text-emerald-600 transition-transform duration-200 {sectionStates.prediction ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </button>
            {#if sectionStates.prediction}
              <div class="px-3 pb-3 space-y-2">
                <div class="flex flex-col h-auto w-full space-y-2">
                  <div class="flex items-center justify-between bg-white/60 rounded-lg p-2">
                    <span class="text-sm font-medium text-gray-700">현재 가</span>
                    <span class="text-sm font-semibold text-gray-900">{`${formatIncludeComma(formatCostValue(dataList[dataList.length - 1]?.Close)) ?? '-'} ₩`}</span>
                  </div>
                  <div class="flex items-center justify-between bg-white/60 rounded-lg p-2">
                    <span class="text-sm font-medium text-gray-700">현재 예측가</span>
                    <div class="flex items-center space-x-1">
                      <span class="text-sm font-semibold text-gray-900">{`${formatIncludeComma(expectValue) ?? '-'} ₩`}</span>
                      {@html setUpDownRatioTag(formatCostValue(dataList[dataList.length - 1]?.Close) ?? 0, expectValue ?? 0)}
                    </div>
                  </div>
                  <div class="flex items-center justify-between bg-white/60 rounded-lg p-2">
                    <span class="text-sm font-medium text-gray-700">한달뒤 예측가</span>
                    <div class="flex items-center space-x-1">
                      <span class="text-sm font-semibold text-gray-900">{`${formatIncludeComma(afterMonthExpectValue) ?? '-'} ₩`}</span>
                      {@html setUpDownRatioTag(formatCostValue(dataList[dataList.length - 1]?.Close) ?? 0, afterMonthExpectValue ?? 0)}
                    </div>
                  </div>
                  <div class="flex items-center justify-between bg-white/60 rounded-lg p-2">
                    <span class="text-sm font-medium text-gray-700">지지평균값</span>
                    <div class="flex items-center space-x-1">
                      <span class="text-sm font-semibold text-gray-900">{`${formatIncludeComma(bottomValue) ?? '-'} ₩`}</span>
                      {@html setUpDownRatioTag(formatCostValue(dataList[dataList.length - 1]?.Close) ?? 0, bottomValue ?? 0)}
                    </div>
                  </div>
                  <div class="flex items-center justify-between bg-white/60 rounded-lg p-2">
                    <span class="text-sm font-medium text-gray-700">저항평균값</span>
                    <div class="flex items-center space-x-1">
                      <span class="text-sm font-semibold text-gray-900">{`${formatIncludeComma(topValue) ?? '-'} ₩`}</span>
                      {@html setUpDownRatioTag(formatCostValue(dataList[dataList.length - 1]?.Close) ?? 0, topValue ?? 0)}
                    </div>
                  </div>
                </div>
              </div>
            {/if}
          </div>
          
          <!-- 이평선 데이터 값 표시 -->
          <div class="flex flex-col w-full bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200/50 rounded-xl overflow-hidden flex-shrink-0">
            <button 
              class="flex items-center justify-between w-full p-3 hover:bg-purple-100/50 transition-colors duration-200"
              on:click={() => sectionStates.movingAverage = !sectionStates.movingAverage}
            >
              <div class="flex items-center space-x-2">
                <svg class="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"></path>
                </svg>
                <p class="font-semibold text-purple-800">이동평균선</p>
              </div>
              <svg class="w-4 h-4 text-purple-600 transition-transform duration-200 {sectionStates.movingAverage ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </button>
            {#if sectionStates.movingAverage}
              <div class="px-3 pb-3 space-y-2">
                <div class="flex flex-col h-auto w-full space-y-2">
                  <div class="flex items-center justify-between bg-white/60 rounded-lg p-2">
                    <div class="flex items-center space-x-2">
                      <span class="text-sm font-medium text-gray-700">5일 이평선</span>
                      <span class="text-xs text-purple-600 bg-purple-100 px-1 rounded">단기</span>
                    </div>
                    <div class="flex items-center space-x-1">
                      <span class="text-sm font-semibold text-gray-900">{`${formatIncludeComma(dataList[dataList.length - 1]?.ma5) ?? '-'} ₩`}</span>
                      {@html setUpDownRatioTag(dataList[dataList.length - 1]?.ma5 ?? 0, nowValue ?? 0)}
                    </div>
                  </div>
                  <div class="flex items-center justify-between bg-white/60 rounded-lg p-2">
                    <div class="flex items-center space-x-2">
                      <span class="text-sm font-medium text-gray-700">20일 이평선</span>
                      <span class="text-xs text-blue-600 bg-blue-100 px-1 rounded">중기</span>
                    </div>
                    <div class="flex items-center space-x-1">
                      <span class="text-sm font-semibold text-gray-900">{`${formatIncludeComma(dataList[dataList.length - 1]?.ma20) ?? '-'} ₩`}</span>
                      {@html setUpDownRatioTag(dataList[dataList.length - 1]?.ma20 ?? 0, dataList[dataList.length - 1]?.ma5 ?? 0)}
                    </div>
                  </div>
                  <div class="flex items-center justify-between bg-white/60 rounded-lg p-2">
                    <div class="flex items-center space-x-2">
                      <span class="text-sm font-medium text-gray-700">60일 이평선</span>
                      <span class="text-xs text-emerald-600 bg-emerald-100 px-1 rounded">장기</span>
                    </div>
                    <div class="flex items-center space-x-1">
                      <span class="text-sm font-semibold text-gray-900">{`${formatIncludeComma(dataList[dataList.length - 1]?.ma60) ?? '-'} ₩`}</span>
                      {@html setUpDownRatioTag(dataList[dataList.length - 1]?.ma60 ?? 0, dataList[dataList.length - 1]?.ma20 ?? 0)}
                    </div>
                  </div>
                </div>
              </div>
            {/if}
          </div>
          
          <!-- 항목 데이터 값 표시 -->
          {#if dataList.length > 0}
            <div class="flex flex-col w-full bg-gradient-to-r from-orange-50 to-amber-50 border border-orange-200/50 rounded-xl overflow-hidden flex-shrink-0">
              <button 
                class="flex items-center justify-between w-full p-3 hover:bg-orange-100/50 transition-colors duration-200"
                on:click={() => sectionStates.stockInfo = !sectionStates.stockInfo}
              >
                <div class="flex items-center space-x-2">
                  <svg class="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                  </svg>
                  <p class="font-semibold text-orange-800">종목 정보</p>
                </div>
                <svg class="w-4 h-4 text-orange-600 transition-transform duration-200 {sectionStates.stockInfo ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
              </button>
              {#if sectionStates.stockInfo}
                <div class="px-3 pb-3 space-y-2">
                  <div class="grid grid-cols-1 gap-2">
                    <div class="flex items-center justify-between bg-white/60 rounded-lg p-2">
                      <span class="text-sm font-medium text-gray-700">종목명</span>
                      <span class="text-sm font-semibold text-gray-900">{singleChartInfo.detailInfo?.name ?? '-'}</span>
                    </div>
                    <div class="flex items-center justify-between bg-white/60 rounded-lg p-2">
                      <span class="text-sm font-medium text-gray-700">종목코드</span>
                      <span class="text-sm font-mono text-gray-900">{singleChartInfo.detailInfo?.code ?? '-'}</span>
                    </div>
                    <div class="flex items-center justify-between bg-white/60 rounded-lg p-2">
                      <span class="text-sm font-medium text-gray-700">현재가</span>
                      <span class="text-sm font-semibold text-gray-900">{`${formatIncludeComma(formatCostValue(dataList[dataList.length - 1]?.Close)) ?? '-'} ₩`}</span>
                    </div>
                    <div class="flex items-center justify-between bg-white/60 rounded-lg p-2">
                      <span class="text-sm font-medium text-gray-700">전일대비</span>
                      <span class="text-sm font-semibold" style="color: {setUpDownColor(singleChartInfo.detailInfo?.chagesRatio)}">
                        {`${setUpDownIcon(singleChartInfo.detailInfo?.chagesRatio)}${singleChartInfo.detailInfo?.chagesRatio ?? '-'}%`}
                      </span>
                    </div>
                    <div class="flex items-center justify-between bg-white/60 rounded-lg p-2">
                      <span class="text-sm font-medium text-gray-700">시초가</span>
                      <div class="flex items-center space-x-1">
                        <span class="text-sm font-semibold text-gray-900">{`${formatIncludeComma(formatCostValue(dataList[dataList.length - 1]?.Open)) ?? '-'} ₩`}</span>
                        {@html setUpDownRatioTag(nowValue ?? 0, dataList[dataList.length - 1]?.Open ?? 0)}
                      </div>
                    </div>
                    <div class="flex items-center justify-between bg-white/60 rounded-lg p-2">
                      <span class="text-sm font-medium text-gray-700">최고가</span>
                      <div class="flex items-center space-x-1">
                        <span class="text-sm font-semibold text-gray-900">{`${formatIncludeComma(formatCostValue(dataList[dataList.length - 1]?.High)) ?? '-'} ₩`}</span>
                        {@html setUpDownRatioTag(nowValue ?? 0, dataList[dataList.length - 1]?.High ?? 0)}
                      </div>
                    </div>
                    <div class="flex items-center justify-between bg-white/60 rounded-lg p-2">
                      <span class="text-sm font-medium text-gray-700">최저가</span>
                      <div class="flex items-center space-x-1">
                        <span class="text-sm font-semibold text-gray-900">{`${formatIncludeComma(formatCostValue(dataList[dataList.length - 1]?.Low)) ?? '-'} ₩`}</span>
                        {@html setUpDownRatioTag(nowValue ?? 0, dataList[dataList.length - 1]?.Low ?? 0)}
                      </div>
                    </div>
                    <div class="flex items-center justify-between bg-white/60 rounded-lg p-2">
                      <span class="text-sm font-medium text-gray-700">거래량</span>
                      <span class="text-sm font-semibold text-gray-900">{`${formatIncludeComma(dataList[dataList.length - 1]?.Volume) ?? '-'} 주`}</span>
                    </div>
                    <div class="flex items-center justify-between bg-white/60 rounded-lg p-2">
                      <span class="text-sm font-medium text-gray-700">시가총액</span>
                      <span class="text-sm font-semibold text-gray-900">{`${formatIncludeComma(singleChartInfo.detailInfo?.marcap) ?? '-'} ₩`}</span>
                    </div>
                    <div class="flex items-center justify-between bg-white/60 rounded-lg p-2">
                      <span class="text-sm font-medium text-gray-700">거래대금</span>
                      <span class="text-sm font-semibold text-gray-900">{`${formatIncludeComma(singleChartInfo.detailInfo?.amount) ?? '-'} ₩`}</span>
                    </div>
                    <div class="flex flex-col bg-white/60 rounded-lg p-2 space-y-1">
                      <span class="text-sm font-medium text-gray-700">거래 유동성</span>
                      <div class="flex items-center justify-between">
                        <span class="text-sm font-semibold text-gray-900">{`${calculateRatio(singleChartInfo.detailInfo?.marcap, singleChartInfo.detailInfo?.amount) ?? '-'}%`}</span>
                        <span class="text-xs text-gray-500">1%이상 좋음, 5%이상 매우좋음</span>
                      </div>
                    </div>
                  </div>
                </div>
              {/if}
            </div>
          {/if}
          
          <!-- 주가 점수 데이터 값 표시 -->
          <div class="flex flex-col w-full bg-gradient-to-r from-red-50 to-pink-50 border border-red-200/50 rounded-xl overflow-hidden flex-shrink-0">
            <button 
              class="flex items-center justify-between w-full p-3 hover:bg-red-100/50 transition-colors duration-200"
              on:click={() => sectionStates.signalScore = !sectionStates.signalScore}
            >
              <div class="flex items-center space-x-2">
                <svg class="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
                <p class="font-semibold text-red-800">투자 신호 점수</p>
                {#if !sectionStates.signalScore}
                  <span class="text-sm {calculateSignalScore(calcSignalScoreResult, signalScoreWeight) > 50 ? 'text-red-600 bg-red-100' : 'text-blue-600 bg-blue-100'} px-2 py-0.5 rounded-full font-semibold">
                    {calculateSignalScore(calcSignalScoreResult, signalScoreWeight) || 0}점
                  </span>
                {/if}
              </div>
              <svg class="w-4 h-4 text-red-600 transition-transform duration-200 {sectionStates.signalScore ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </button>
            
            {#if sectionStates.signalScore}
              <div class="px-3 pb-3 space-y-3">
                <div class="space-y-2">
                  <div class="bg-white/60 rounded-lg p-3">
                    <div class="flex items-center justify-between mb-2">
                      <div class="flex items-center space-x-2">
                        <span class="w-2 h-2 bg-blue-500 rounded-full"></span>
                        <span class="text-sm font-medium text-gray-700">추세 신호</span>
                        <span class="text-xs text-gray-500">(0~1)</span>
                      </div>
                      <span class="text-sm font-semibold text-gray-900">{calcSignalScoreResult?.crossNormalizeValue ?? '-'}</span>
                    </div>
                    <div class="flex items-center space-x-2">
                      <span class="text-xs text-gray-600">가중치:</span>
                      <input 
                        autocomplete="off" 
                        bind:value={signalScoreWeight.crossWeight} 
                        placeholder="35" 
                        class="w-12 px-1 py-0.5 text-xs border border-gray-300 rounded focus:border-blue-500 focus:outline-none" 
                        max={100} 
                        min={0}
                      />
                      <span class="text-xs text-gray-600">%</span>
                    </div>
                  </div>

                  <div class="bg-white/60 rounded-lg p-3">
                    <div class="flex items-center justify-between mb-2">
                      <div class="flex items-center space-x-2">
                        <span class="w-2 h-2 bg-emerald-500 rounded-full"></span>
                        <span class="text-sm font-medium text-gray-700">거래량</span>
                        <span class="text-xs text-gray-500">(0~1)</span>
                      </div>
                      <span class="text-sm font-semibold text-gray-900">{calcSignalScoreResult?.volumeNormalizeValue ?? '-'}</span>
                    </div>
                    <div class="flex items-center space-x-2">
                      <span class="text-xs text-gray-600">가중치:</span>
                      <input 
                        autocomplete="off" 
                        bind:value={signalScoreWeight.volumeWeight} 
                        placeholder="25" 
                        class="w-12 px-1 py-0.5 text-xs border border-gray-300 rounded focus:border-emerald-500 focus:outline-none" 
                        max={100} 
                        min={0}
                      />
                      <span class="text-xs text-gray-600">%</span>
                    </div>
                  </div>

                  <div class="bg-white/60 rounded-lg p-3">
                    <div class="flex items-center justify-between mb-2">
                      <div class="flex items-center space-x-2">
                        <span class="w-2 h-2 bg-purple-500 rounded-full"></span>
                        <span class="text-sm font-medium text-gray-700">지지/저항</span>
                        <span class="text-xs text-gray-500">(0~1)</span>
                      </div>
                      <span class="text-sm font-semibold text-gray-900">{calcSignalScoreResult?.lineNormalizeValue ?? '-'}</span>
                    </div>
                    <div class="flex items-center space-x-2">
                      <span class="text-xs text-gray-600">가중치:</span>
                      <input 
                        autocomplete="off" 
                        bind:value={signalScoreWeight.lineWeight} 
                        placeholder="15" 
                        class="w-12 px-1 py-0.5 text-xs border border-gray-300 rounded focus:border-purple-500 focus:outline-none" 
                        max={100} 
                        min={0}
                      />
                      <span class="text-xs text-gray-600">%</span>
                    </div>
                  </div>

                  <div class="bg-white/60 rounded-lg p-3">
                    <div class="flex items-center justify-between mb-2">
                      <div class="flex items-center space-x-2">
                        <span class="w-2 h-2 bg-orange-500 rounded-full"></span>
                        <span class="text-sm font-medium text-gray-700">예측 추세</span>
                        <span class="text-xs text-gray-500">(0~1)</span>
                      </div>
                      <span class="text-sm font-semibold text-gray-900">{calcSignalScoreResult?.expectNormalizeValue ?? '-'}</span>
                    </div>
                    <div class="flex items-center space-x-2">
                      <span class="text-xs text-gray-600">가중치:</span>
                      <input 
                        autocomplete="off" 
                        bind:value={signalScoreWeight.expectWeight} 
                        placeholder="25" 
                        class="w-12 px-1 py-0.5 text-xs border border-gray-300 rounded focus:border-orange-500 focus:outline-none" 
                        max={100} 
                        min={0}
                      />
                      <span class="text-xs text-gray-600">%</span>
                    </div>
                  </div>
                </div>

                <div class="border-t border-gray-200 pt-3">
                  <div class="bg-gradient-to-r {calculateSignalScore(calcSignalScoreResult, signalScoreWeight) > 50 ? 'from-red-100 to-red-50 border-red-200' : 'from-blue-100 to-blue-50 border-blue-200'} border rounded-lg p-3">
                    <div class="flex items-center justify-between mb-2">
                      <div class="flex items-center space-x-2">
                        <svg class="w-4 h-4 {calculateSignalScore(calcSignalScoreResult, signalScoreWeight) > 50 ? 'text-red-600' : 'text-blue-600'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"></path>
                        </svg>
                        <span class="font-semibold {calculateSignalScore(calcSignalScoreResult, signalScoreWeight) > 50 ? 'text-red-700' : 'text-blue-700'}">Total Score</span>
                        <span class="text-xs text-gray-500">(0~100)</span>
                      </div>
                      <span class="text-lg font-bold {calculateSignalScore(calcSignalScoreResult, signalScoreWeight) > 50 ? 'text-red-600' : 'text-blue-600'}">{calculateSignalScore(calcSignalScoreResult, signalScoreWeight) ?? '-'}</span>
                    </div>
                    <div class="flex items-center justify-between text-xs text-gray-600">
                      <span>총 가중치:</span>
                      <div class="flex items-center space-x-1">
                        <input 
                          autocomplete="off" 
                          disabled 
                          value={sumWeight(signalScoreWeight)} 
                          class="w-12 px-1 py-0.5 text-xs bg-gray-100 border border-gray-300 rounded text-center" 
                        />
                        <span>%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            {/if}
          </div>
          
          <!-- 뉴스 정보 -->
          <div class="flex flex-col bg-gradient-to-r from-gray-50 to-slate-50 border border-gray-200/50 rounded-xl overflow-hidden flex-shrink-0">
            <button 
              class="flex items-center justify-between w-full p-3 bg-white/60 border-b border-gray-200/50 hover:bg-gray-100/50 transition-colors duration-200"
              on:click={() => sectionStates.news = !sectionStates.news}
            >
              <div class="flex items-center space-x-2">
                <svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path>
                </svg>
                <p class="font-semibold text-gray-800">관련 뉴스</p>
              </div>
              <svg class="w-4 h-4 text-gray-600 transition-transform duration-200 {sectionStates.news ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </button>
            {#if sectionStates.news}
              <div class="p-2 max-h-80 overflow-y-auto scrollbar-thin-custom">
                <NewsInfoListComponent
                  bind:newInfoList
                />
              </div>
            {/if}
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  /* Firefox용 */
  .scrollbar-thin-custom {
    scrollbar-width: thin;           /* 얇은 스크롤바 */
    scrollbar-color: #000000 transparent; /* 썸 색상, 트랙은 투명 */
  }
  /* Webkit(크롬, 사파리 등)용 */
  .scrollbar-thin-custom::-webkit-scrollbar {
    height: 6px;                     /* 가로 스크롤바 두께 */
    background: transparent;         /* 트랙(배경) 투명 */
  }
  .scrollbar-thin-custom::-webkit-scrollbar-thumb {
    background: #000000;                /* 썸(움직이는 부분) 색상 */
    border-radius: 4px;              /* 둥근 모서리 */
  }
  .scrollbar-thin-custom::-webkit-scrollbar-thumb:hover {
    background: #555;                /* 썸 호버 시 색상 */
  }
</style>