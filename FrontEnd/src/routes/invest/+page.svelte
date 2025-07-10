<script lang="ts">
  import { onMount } from 'svelte';
  import { InvestConfidence, ProgressCircle } from '$lib/component';
  import { calculateChangeRate, getFinanceDataListByChartMode, setUpDownColor, setUpDownRatioTag } from '$lib/main';
  import { getAllFinanceRankList } from '$lib/api-connector/FinanceApi';
  import { formatIncludeComma, createComponent } from '$lib/utils/CommonHelper';
  import { StockListPopup } from '$lib/popup';
  import _ from 'lodash';

  let financeMonthRankObject: any = null;

  let selectedFinanceMonthRankList: any = [];
  let choicedStockInfoList: any = [];

  let loadProgress: boolean = false;
  let loadingText: string = '';

  let allPeriodTextKey: string = '전체 기간 없음';
  let axiosController: any = null;

  let topNList = [
    {name: 'Top 10', value: 10},
    {name: 'Top 30', value: 30},
    {name: 'Top 50', value: 50},
    {name: 'Top 100', value: 100},
    {name: 'ALL', value: 0}
  ]

  let investModeList = [
    {name: 'FIX STOCK', value: 1},
    {name: 'CHOICE STOCK', value: 2}
  ]

  let selectedMonthRank: string = '';
  let selectedTopN: number = 10;
  let selectedInvestMode: number = 1;

  let calRankStockList: any = [];
  let searchDuration: any = null;

  let listProgress: boolean = false;

  let investResultInfo: {
    investMoney: number,
    equalExpectCost: number,
    weightExpectCost: number
  } | null = null;

  onMount(async () => {
    await getKoreaAllFinanceRankList();
  })

  const getKoreaAllFinanceRankList = async () => {
    axiosController = new AbortController();
    allPeriodTextKey = '전체 기간 없음';
    financeMonthRankObject = null;
    loadProgress = true;

    const resultList = await getAllFinanceRankList({stock: 'KRX'}, axiosController);

    loadProgress = false;

    if (!!resultList?.data?.perMonthDataList) {
      financeMonthRankObject = {...resultList?.data?.allPeriodDataList, ...resultList.data?.perMonthDataList}
      selectedMonthRank = Object.keys(financeMonthRankObject)[0];
      selectedFinanceMonthRankList = _.orderBy(financeMonthRankObject[selectedMonthRank].map((item: any) => {return {...item, rankAvg: Math.round(parseInt(item.rankSum) / parseInt(item.fullCount)), rankSum: parseInt(item.rankSum), count: parseInt(item.count)}}), ['rankAvg', 'count'], ['asc', 'desc']);
    };
  }

  /**
   * 가중 분산금 계산
   * @param investCost
   * @param stockLength
   * @param weightRank
   */
  const getAddWeightValue = (investCost: number, stockLength: number, weightRank: number) => {
    return (parseFloat((2 * (investCost / (stockLength * (stockLength + 1)))).toFixed(2)) - 1) * weightRank;
  }

  /**
   * 모의 투자 결과 값 계산
   * @param investMoney
   * @param rankStockList
   */
  const calculationInvestResultInfo = (investMoney: number, rankStockList: any) => {
    if (rankStockList.length < 1 || investMoney <= 0) {
      return null;
    }

    let equalExpectCost: number = 0;
    let weightExpectCost: number = 0;
    let stockLength: number = rankStockList.length;

    // 종목별 투자 금액
    const equalInvestMoney: number = Math.ceil(investMoney / stockLength);

    let weightRank: number = stockLength;

    for (let rankStockInfo of rankStockList) {
      const upDownRatio: number = parseFloat(calculateChangeRate(rankStockInfo.startCost, rankStockInfo.endCost)) / 100;
      rankStockInfo.equalCost = equalInvestMoney.toFixed(0);
      rankStockInfo.weightCost = getAddWeightValue(investMoney, stockLength, weightRank).toFixed(0);
      rankStockInfo.equalExpectCost = parseInt(((upDownRatio * equalInvestMoney) + equalInvestMoney).toFixed(0));
      rankStockInfo.weightExpectCost = parseInt(((upDownRatio * getAddWeightValue(investMoney, stockLength, weightRank)) + getAddWeightValue(investMoney, stockLength, weightRank)).toFixed(0));

      equalExpectCost += (upDownRatio * equalInvestMoney) + equalInvestMoney;
      weightExpectCost += (upDownRatio * getAddWeightValue(investMoney, stockLength, weightRank)) + getAddWeightValue(investMoney, stockLength, weightRank);

      weightRank -= 1;
    }

    return {
      investMoney: investMoney,
      equalExpectCost: Math.ceil(equalExpectCost),
      weightExpectCost: Math.ceil(weightExpectCost)
    }
  }

  /**
   * 모의 투자 시작
   * @param e
   */
  const onInvestCallback = async (e: any) => {
    if (!!!e?.detail) {
      return;
    }

    searchDuration = e.detail.duration;
    const investMoney = e.detail.investMoney;
    const rankStockList = selectedInvestMode === 1 ? selectedFinanceMonthRankList.slice(1, selectedTopN + 1) : choicedStockInfoList;

    listProgress = true;

    for (let rankStockInfo of rankStockList) {
      const financeDataResult = await getFinanceDataListByChartMode(rankStockInfo.code, searchDuration.week, false);
      rankStockInfo.startCost = financeDataResult[0]?.Close ?? 0;
      rankStockInfo.endCost = financeDataResult[financeDataResult.length - 1]?.Close ?? 0;
    }

    listProgress = false;

    calRankStockList = _.cloneDeep(rankStockList);

    investResultInfo = calculationInvestResultInfo(investMoney, calRankStockList);
  }

  const setTextColorByUpDown = (target: any, value: any) => {
    if (!!!target || !!!value) {
      return 'black';
    }

    if (target > value) {
      return 'red';
    } else {
      return 'blue';
    }
  }

  /**
   * 데이터 변환 및 정렬 최적화 함수
   */
  const processFinanceData = (dataArray: any[]): any[] => {
    if (!dataArray || dataArray.length === 0) {
      return [];
    }

    // 한 번의 순회로 변환과 정렬을 위한 데이터 준비
    const processedData = dataArray.map((item: any) => {
      const rankSum = parseInt(item.rankSum) || 0;
      const fullCount = parseInt(item.fullCount) || 1;
      const count = parseInt(item.count) || 0;
      
      return {
        ...item,
        rankAvg: Math.round(rankSum / fullCount),
        rankSum,
        count
      };
    });

    // 네이티브 sort 사용 (lodash orderBy보다 빠름)
    return processedData.sort((a, b) => {
      // 1차 정렬: rankAvg 오름차순
      if (a.rankAvg !== b.rankAvg) {
        return a.rankAvg - b.rankAvg;
      }
      // 2차 정렬: count 내림차순
      return b.count - a.count;
    });
  };
</script>

<svelte:head>
	<title>모의 투자 - FinanceChart</title>
</svelte:head>
<div class="flex w-full h-full bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-900 relative overflow-hidden">
  <!-- 배경 데코레이션 -->
  <div class="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,_rgba(59,130,246,0.1)_1px,_transparent_0)] bg-[size:32px_32px] pointer-events-none"></div>
  <div class="absolute top-0 left-0 w-96 h-96 bg-gradient-to-r from-green-500/20 to-emerald-500/20 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2 animate-pulse"></div>
  <div class="absolute bottom-0 right-0 w-96 h-96 bg-gradient-to-r from-blue-500/20 to-cyan-500/20 rounded-full blur-3xl translate-x-1/2 translate-y-1/2 animate-pulse"></div>
  
  <div class="flex flex-col w-full h-full p-3 sm:p-4 lg:p-6 space-y-3 sm:space-y-4 lg:space-y-6 relative z-10 min-h-0">
    <div class="flex flex-col xl:flex-row w-full flex-1 space-y-3 xl:space-y-0 xl:space-x-6 min-h-0">
      <!-- 모의 투자하기 -->
      <div class="flex flex-col w-full xl:w-[70%] h-full bg-slate-800/60 backdrop-blur-xl rounded-2xl border border-slate-600/40 shadow-2xl shadow-black/20 p-3 sm:p-4 lg:p-6 space-y-3 lg:space-y-4 min-h-0">
        <InvestConfidence
          on:onInvestCallback={onInvestCallback}
        />
        <div class="flex flex-col flex-1 overflow-hidden bg-white/95 backdrop-blur-xl rounded-xl border border-slate-200/50 shadow-lg min-h-0">
          <div class="flex w-full h-[40px] sm:h-[45px] lg:h-[50px] items-center space-x-1 sm:space-x-2 text-white rounded-t-xl px-2 sm:px-3 lg:px-4 bg-gradient-to-r from-slate-700 to-slate-600 border-b border-slate-500/30 flex-shrink-0">
            <p class="w-[8%] sm:w-[5%] text-center font-medium text-xs sm:text-sm">Rank</p>
            <p class="w-[15%] sm:w-[10%] text-center font-medium text-xs sm:text-sm">코드명</p>
            <p class="w-[20%] font-medium text-xs sm:text-sm">종목명</p>
            <p class="w-[15%] text-right font-medium text-xs sm:text-sm">{`${searchDuration?.month ?? 'N'}달전`}</p>
            <p class="w-[15%] text-right font-medium text-xs sm:text-sm">현재주가</p>
            <p class="w-[8%] sm:w-[5%] font-medium text-xs sm:text-sm">등락</p>
            <p class="w-[15%] text-right font-medium text-xs sm:text-sm hidden sm:block">균등투자금</p>
            <p class="w-[15%] text-right font-medium text-xs sm:text-sm hidden sm:block">균등결과</p>
            <p class="w-[15%] text-right font-medium text-xs sm:text-sm hidden lg:block">가중투자금</p>
            <p class="w-[15%] text-right font-medium text-xs sm:text-sm hidden lg:block">가중결과</p>
          </div>
          {#if calRankStockList.length > 0 && listProgress === false}
            <div class="flex flex-col flex-1 overflow-auto min-h-0">
              {#each calRankStockList as calRankStockInfo, index}
                <div class="flex w-full h-[35px] sm:h-[40px] lg:h-[45px] items-center space-x-1 sm:space-x-2 text-slate-700 border-b border-slate-200/50 px-2 sm:px-3 lg:px-4 hover:bg-slate-50/80 transition-colors duration-200 flex-shrink-0">
                  <p class="w-[8%] sm:w-[5%] text-center font-medium text-xs sm:text-sm">{index + 1}</p>
                  <p class="w-[15%] sm:w-[10%] text-center font-mono text-xs">{calRankStockInfo.code}</p>
                  <p class="w-[20%] font-medium text-xs sm:text-sm truncate">{calRankStockInfo.name}</p>
                  <p class="w-[15%] text-right font-medium text-xs sm:text-sm">{`${formatIncludeComma(calRankStockInfo.startCost)} ₩`}</p>
                  <p class="w-[15%] text-right font-medium text-xs sm:text-sm">{`${formatIncludeComma(calRankStockInfo.endCost)} ₩`}</p>
                  <p class="w-[8%] sm:w-[5%] text-xs">{@html setUpDownRatioTag(calRankStockInfo.startCost ?? 0, calRankStockInfo.endCost ?? 0)}</p>
                  <p class="w-[15%] text-right font-medium text-xs sm:text-sm hidden sm:block">{`${formatIncludeComma(calRankStockInfo?.equalCost)} ₩`}</p>
                  <p class="w-[15%] text-right font-bold text-xs sm:text-sm hidden sm:block" style="color: {setTextColorByUpDown(calRankStockInfo?.equalExpectCost, calRankStockInfo?.equalCost)}">{`${formatIncludeComma(calRankStockInfo?.equalExpectCost)} ₩`}</p>
                  <p class="w-[15%] text-right font-medium text-xs sm:text-sm hidden lg:block">{`${formatIncludeComma(calRankStockInfo?.weightCost)} ₩`}</p>
                  <p class="w-[15%] text-right font-bold text-xs sm:text-sm hidden lg:block" style="color: {setTextColorByUpDown(calRankStockInfo?.weightExpectCost, calRankStockInfo?.weightCost)}">{`${formatIncludeComma(calRankStockInfo?.weightExpectCost)} ₩`}</p>
                </div>
              {/each}
            </div>
          {:else if listProgress}
            <div class="flex w-full flex-1 justify-center items-center min-h-0">
              <ProgressCircle
                size={80}
                thickness={8}
                isLarge={true}
                isTextBlack={true}
                text={'투자 항목 데이터 조회 중...'}
              />
            </div>
          {:else}
            <div class="flex w-full flex-1 justify-center items-center text-slate-600 font-medium text-sm sm:text-base lg:text-lg min-h-0">
              투자 항목이 없습니다.
            </div>
          {/if}
        </div>
      </div>
      <!-- 월별 항목 불러오기 -->
      <div class="flex flex-col w-full xl:w-[30%] h-full min-h-0">
        <div class="flex flex-row space-x-1 px-2 mb-2 flex-shrink-0">
          {#each investModeList as investModeInfo}
            <button class="px-2 sm:px-3 lg:px-4 py-1 sm:py-2 rounded-t-xl font-bold text-xs sm:text-sm transition-all duration-200 border-t border-x border-slate-600/40 {selectedInvestMode === investModeInfo.value ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg shadow-green-500/30' : 'bg-slate-700/80 text-slate-300 hover:bg-slate-600/80'}"
              on:click={() => {
                selectedInvestMode = investModeInfo.value;
              }}
            >
              {investModeInfo.name}
            </button>
          {/each}
        </div>
        <div class="flex flex-col flex-1 bg-slate-800/60 backdrop-blur-xl rounded-2xl border border-slate-600/40 shadow-2xl shadow-black/20 p-3 sm:p-4 space-y-3 sm:space-y-4 min-h-0">
          <!-- 고정 항목 -->
          {#if selectedInvestMode === 1}
            <div class="flex flex-col sm:flex-row h-auto sm:h-[70px] lg:h-[80px] w-full space-y-2 sm:space-y-0 sm:space-x-3 flex-shrink-0">
              <!-- 월별 선택 -->
              <div class="flex flex-wrap h-[60px] sm:h-full w-full bg-slate-700/80 backdrop-blur-sm rounded-xl border border-slate-500/30 overflow-auto px-2 py-2">
                {#if !!financeMonthRankObject}
                  {#each Object.keys(financeMonthRankObject) as financeMonth}
                    <button class="h-[24px] sm:h-[28px] rounded-lg px-2 sm:px-3 mr-1 mb-1 text-xs font-medium transition-all duration-200 flex-shrink-0 {selectedMonthRank === financeMonth ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-500/30' : 'bg-slate-600/80 text-slate-200 border border-slate-500/50 hover:bg-slate-500/80'}" on:click={async () => {
                      selectedMonthRank = financeMonth;
                      selectedFinanceMonthRankList = financeMonthRankObject[selectedMonthRank];
                      selectedFinanceMonthRankList = processFinanceData(financeMonthRankObject[selectedMonthRank]);
                    }}>{`${financeMonth} (${financeMonthRankObject[financeMonth][0]?.count ?? 0}회)`}</button>
                  {/each}
                {/if}
              </div>
              <!-- topN 선택 -->
              <div class="flex flex-wrap h-[60px] sm:h-full w-full bg-slate-700/80 backdrop-blur-sm rounded-xl border border-slate-500/30 overflow-auto px-2 py-2">
                {#if !!topNList}
                  {#each topNList as topNInfo}
                    <button class="h-[24px] sm:h-[28px] rounded-lg px-2 sm:px-3 mr-1 mb-1 text-xs font-medium transition-all duration-200 flex-shrink-0 {(selectedTopN === topNInfo.value || (topNInfo.name === 'ALL' && selectedTopN > 100)) ? 'bg-gradient-to-r from-purple-500 to-pink-600 text-white shadow-lg shadow-purple-500/30' : 'bg-slate-600/80 text-slate-200 border border-slate-500/50 hover:bg-slate-500/80'}" on:click={async () => {
                      if (topNInfo.name === 'ALL') {
                        selectedTopN = selectedFinanceMonthRankList.length;
                      } else {
                        selectedTopN = topNInfo.value;
                      }
                    }}>{topNInfo.name}</button>
                  {/each}
                {/if}
              </div>
            </div>
            <!-- 월별 top10 -->
            <div class="flex flex-col flex-1 w-full bg-white/95 backdrop-blur-xl rounded-xl border border-slate-200/50 shadow-inner min-h-0 overflow-hidden">
              {#if selectedFinanceMonthRankList.length > 0}
                <div class="flex flex-col h-full w-full overflow-auto px-3 py-3 space-y-1">
                  {#each selectedFinanceMonthRankList.slice(1, selectedTopN + 1) as financeMonthRankInfo, index}
                    <div class="flex items-center h-[28px] sm:h-[32px] rounded-lg px-3 bg-gradient-to-r from-slate-100 to-slate-50 border border-slate-200/50 shadow-sm flex-shrink-0">
                      <span class="text-xs font-bold text-slate-600 mr-2 flex-shrink-0">{index+1}위</span>
                      <span class="text-xs sm:text-sm font-medium text-slate-800 truncate flex-1">{financeMonthRankInfo.name}</span>
                      <span class="text-xs text-slate-500 ml-2 flex-shrink-0">({financeMonthRankInfo.code})</span>
                    </div>
                  {/each}
                </div>
              {:else}
                <div class="flex items-center justify-center h-full text-slate-500 text-sm">
                  종목을 선택해주세요
                </div>
              {/if}
            </div>
          {:else}
            <!-- 선택 항목 -->
            <div class="flex flex-col flex-1 w-full bg-white/95 backdrop-blur-xl rounded-xl border border-slate-200/50 shadow-inner min-h-0 overflow-hidden">
              <div class="flex flex-col h-full w-full px-3 py-3 space-y-2">
                {#if choicedStockInfoList.length > 0}
                  <div class="flex flex-col overflow-auto space-y-2 flex-1">
                    {#each choicedStockInfoList as choicedStockInfo}
                      <div class="flex items-center h-[28px] sm:h-[32px] rounded-lg px-3 bg-gradient-to-r from-emerald-100 to-teal-50 border border-emerald-200/50 shadow-sm flex-shrink-0">
                        <span class="text-xs sm:text-sm font-medium text-slate-800 truncate flex-1">{choicedStockInfo.name}</span>
                        <span class="text-xs text-slate-500 ml-2 flex-shrink-0">({choicedStockInfo.code})</span>
                      </div>
                    {/each}
                  </div>
                  <button class="flex items-center justify-center h-[35px] sm:h-[40px] bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 rounded-xl border border-green-400/50 shadow-lg shadow-green-500/30 transition-all duration-200 group flex-shrink-0" on:click={async() => {
                    const popupResult = await createComponent(StockListPopup, {
                      titleName: '주식 목록 조회'
                    });
                
                    if (popupResult.isSave === false) {
                      return;
                    }
    
                    for (let choiceStockInfo of popupResult.choiceStockInfoList) {
                      choicedStockInfoList.push({
                        name: choiceStockInfo.name,
                        code: choiceStockInfo.code
                      })
                    }
    
                    choicedStockInfoList = _.uniqBy(choicedStockInfoList, "code");
                  }}>
                    <span class="text-white font-bold text-sm sm:text-lg group-hover:scale-110 transition-transform duration-200">➕</span>
                    <span class="text-white font-medium ml-2 text-xs sm:text-sm">종목 추가</span>
                  </button>
                {:else}
                  <div class="flex flex-col items-center justify-center h-full space-y-4">
                    <div class="text-center space-y-2">
                      <div class="w-12 h-12 bg-gradient-to-r from-slate-400 to-slate-500 rounded-xl flex items-center justify-center mx-auto">
                        <span class="text-white text-xl">📈</span>
                      </div>
                      <p class="text-slate-500 text-sm font-medium">선택된 종목이 없습니다</p>
                    </div>
                    <button class="flex items-center justify-center h-[40px] px-6 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 rounded-xl border border-green-400/50 shadow-lg shadow-green-500/30 transition-all duration-200 group" on:click={async() => {
                      const popupResult = await createComponent(StockListPopup, {
                        titleName: '주식 목록 조회'
                      });
                  
                      if (popupResult.isSave === false) {
                        return;
                      }
      
                      for (let choiceStockInfo of popupResult.choiceStockInfoList) {
                        choicedStockInfoList.push({
                          name: choiceStockInfo.name,
                          code: choiceStockInfo.code
                        })
                      }
      
                      choicedStockInfoList = _.uniqBy(choicedStockInfoList, "code");
                    }}>
                      <span class="text-white font-bold text-lg group-hover:scale-110 transition-transform duration-200">➕</span>
                      <span class="text-white font-medium ml-2 text-sm">종목 추가</span>
                    </button>
                  </div>
                {/if}
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>
    <div class="flex flex-col lg:flex-row w-full flex-1 bg-slate-800/60 backdrop-blur-xl rounded-2xl border border-slate-600/40 shadow-2xl shadow-black/20 p-4 sm:p-6 lg:p-8 space-y-4 lg:space-y-0 lg:space-x-8 min-h-0">
      {#if !!investResultInfo && listProgress === false}
        <div class="flex flex-col w-full lg:w-[50%] h-full bg-gradient-to-br from-white via-blue-50 to-indigo-50 backdrop-blur-xl rounded-2xl border border-blue-200/50 shadow-xl shadow-blue-500/20 p-4 sm:p-6 lg:p-8 min-h-0">
          <div class="flex items-center space-x-3 mb-4 lg:mb-6 flex-shrink-0">
            <div class="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/30">
              <span class="text-white text-lg sm:text-xl lg:text-2xl">⚌</span>
            </div>
            <h2 class="font-black text-lg sm:text-2xl lg:text-3xl bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">균등투자결과</h2>
          </div>
          <div class='flex flex-col flex-1 justify-center space-y-3 sm:space-y-4 lg:space-y-6 px-2 sm:px-4'>
            <div class="flex flex-row justify-between items-center p-3 sm:p-4 bg-white/80 rounded-xl border border-blue-200/30 shadow-sm">
              <p class="font-bold text-sm sm:text-lg lg:text-xl text-slate-700">투자시작금액</p>
              <p class="font-black text-sm sm:text-lg lg:text-xl text-blue-600">{`${formatIncludeComma(investResultInfo?.investMoney) ?? '-'} ₩`}</p>
            </div>
            <div class="flex flex-row justify-between items-center p-3 sm:p-4 bg-white/80 rounded-xl border border-blue-200/30 shadow-sm">
              <p class="font-bold text-sm sm:text-lg lg:text-xl text-slate-700">투자결과금액</p>
              <p class="font-black text-sm sm:text-lg lg:text-xl text-blue-600">{`${formatIncludeComma(investResultInfo?.equalExpectCost) ?? '-'} ₩`}</p>
            </div>
            <div class="flex flex-row justify-between items-center p-3 sm:p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200/50 shadow-md">
              <p class="font-bold text-sm sm:text-lg lg:text-xl text-slate-700">이득/손실금액</p>
              <div class="text-right">
                <p class="font-black text-sm sm:text-lg lg:text-xl" style="color: {setUpDownColor((investResultInfo?.equalExpectCost ?? 0) - (investResultInfo?.investMoney ?? 0))}">
                  {@html `(${setUpDownRatioTag(investResultInfo?.investMoney ?? 0, investResultInfo?.equalExpectCost ?? 0)})`}
                </p>
                <p class="font-black text-sm sm:text-lg lg:text-xl" style="color: {setUpDownColor((investResultInfo?.equalExpectCost ?? 0) - (investResultInfo?.investMoney ?? 0))}">
                  {`${formatIncludeComma((investResultInfo?.equalExpectCost ?? 0) - (investResultInfo?.investMoney ?? 0)) ?? '-'} ₩`}
                </p>
              </div>
            </div>
          </div>
        </div>
        <div class="flex flex-col w-full lg:w-[50%] h-full bg-gradient-to-br from-white via-emerald-50 to-green-50 backdrop-blur-xl rounded-2xl border border-emerald-200/50 shadow-xl shadow-emerald-500/20 p-4 sm:p-6 lg:p-8 min-h-0">
          <div class="flex items-center space-x-3 mb-4 lg:mb-6 flex-shrink-0">
            <div class="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 bg-gradient-to-r from-emerald-500 to-green-600 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-500/30">
              <span class="text-white text-lg sm:text-xl lg:text-2xl">⚖</span>
            </div>
            <h2 class="font-black text-lg sm:text-2xl lg:text-3xl bg-gradient-to-r from-emerald-600 to-green-600 bg-clip-text text-transparent">가중투자결과</h2>
          </div>
          <div class='flex flex-col flex-1 justify-center space-y-3 sm:space-y-4 lg:space-y-6 px-2 sm:px-4'>
            <div class="flex flex-row justify-between items-center p-3 sm:p-4 bg-white/80 rounded-xl border border-emerald-200/30 shadow-sm">
              <p class="font-bold text-sm sm:text-lg lg:text-xl text-slate-700">투자시작금액</p>
              <p class="font-black text-sm sm:text-lg lg:text-xl text-emerald-600">{`${formatIncludeComma(investResultInfo?.investMoney) ?? '-'} ₩`}</p>
            </div>
            <div class="flex flex-row justify-between items-center p-3 sm:p-4 bg-white/80 rounded-xl border border-emerald-200/30 shadow-sm">
              <p class="font-bold text-sm sm:text-lg lg:text-xl text-slate-700">투자결과금액</p>
              <p class="font-black text-sm sm:text-lg lg:text-xl text-emerald-600">{`${formatIncludeComma(investResultInfo?.weightExpectCost) ?? '-'} ₩`}</p>
            </div>
            <div class="flex flex-row justify-between items-center p-3 sm:p-4 bg-gradient-to-r from-emerald-50 to-green-50 rounded-xl border border-emerald-200/50 shadow-md">
              <p class="font-bold text-sm sm:text-lg lg:text-xl text-slate-700">이득/손실금액</p>
              <div class="text-right">
                <p class="font-black text-sm sm:text-lg lg:text-xl" style="color: {setUpDownColor((investResultInfo?.weightExpectCost ?? 0) - (investResultInfo?.investMoney ?? 0))}">
                  {@html `(${setUpDownRatioTag(investResultInfo?.investMoney ?? 0, investResultInfo?.weightExpectCost ?? 0)})`}
                </p>
                <p class="font-black text-sm sm:text-lg lg:text-xl" style="color: {setUpDownColor((investResultInfo?.weightExpectCost ?? 0) - (investResultInfo?.investMoney ?? 0))}">
                  {`${formatIncludeComma((investResultInfo?.weightExpectCost ?? 0) - (investResultInfo?.investMoney ?? 0)) ?? '-'} ₩`}
                </p>
              </div>
            </div>
          </div>
        </div>
      {:else if listProgress}
        <div class="flex w-full h-full justify-center items-center min-h-0">
          <ProgressCircle
            size={100}
            thickness={10}
            isLarge={true}
            isTextBlack={false}
            text={'모의투자 결과 계산 중...'}
          />
        </div>
      {:else}
        <div class="flex flex-col w-full h-full justify-center items-center min-h-0">
          <div class="text-center space-y-4">
            <div class="w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-r from-slate-600 to-slate-500 rounded-2xl flex items-center justify-center mx-auto shadow-lg">
              <span class="text-white text-2xl sm:text-3xl">📊</span>
            </div>
            <h3 class="font-bold text-lg sm:text-xl lg:text-2xl text-white">모의투자 결과화면</h3>
            <p class="text-slate-300 font-medium text-sm sm:text-base">투자 설정을 완료하고 시뮬레이션을 시작해보세요</p>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  /* 글래스모피즘 효과 강화 */
  :global(.backdrop-blur-xl) {
    backdrop-filter: blur(24px) saturate(180%);
    -webkit-backdrop-filter: blur(24px) saturate(180%);
  }

  /* 애니메이션 */
  :global(.animate-pulse) {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }

  /* 스크롤바 스타일링 */
  :global(::-webkit-scrollbar) {
    width: 6px;
  }

  :global(::-webkit-scrollbar-track) {
    background: rgba(241, 245, 249, 0.8);
    border-radius: 10px;
  }

  :global(::-webkit-scrollbar-thumb) {
    background: linear-gradient(45deg, rgba(148, 163, 184, 0.6), rgba(203, 213, 225, 0.8));
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  :global(::-webkit-scrollbar-thumb:hover) {
    background: linear-gradient(45deg, rgba(100, 116, 139, 0.8), rgba(148, 163, 184, 0.9));
  }

  /* 버튼 호버 효과 */
  button {
    outline: none;
  }

  button:focus {
    outline: none;
    box-shadow: none;
  }

  /* 모바일에서 작은 스크롤바 */
  @media (max-width: 768px) {
    :global(::-webkit-scrollbar) {
      width: 4px;
    }
  }

  /* 텍스트 줄임표 처리 */
  .truncate {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* 최소 높이 보장 */
  .min-h-0 {
    min-height: 0;
  }

  /* Flexbox 레이아웃 최적화 */
  .flex-1 {
    flex: 1 1 0%;
  }

  .flex-shrink-0 {
    flex-shrink: 0;
  }

  /* 컨테이너 높이 제한 */
  .container-height {
    height: calc(100vh - 2rem);
    max-height: calc(100vh - 2rem);
  }

  @media (min-width: 640px) {
    .container-height {
      height: calc(100vh - 2rem);
      max-height: calc(100vh - 2rem);
    }
  }

  @media (min-width: 1024px) {
    .container-height {
      height: calc(100vh - 3rem);
      max-height: calc(100vh - 3rem);
    }
  }
</style>