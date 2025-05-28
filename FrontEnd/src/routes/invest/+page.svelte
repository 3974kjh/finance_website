<script lang="ts">
  import { onMount } from 'svelte';
  import { InvestConfidence, ProgressCircle } from '$lib/component';
  import { calculateChangeRate, getFinanceDataListByChartMode, setUpDownColor, setUpDownRatioTag } from '$lib/main';
  import { getFinanceStockList, getExpectStockValue, getAllFinanceRankList } from '$lib/api-connector/FinanceApi';
  import { calculateRatio, formatCostValue, formatIncludeComma, createComponent } from '$lib/utils/CommonHelper';
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
      selectedFinanceMonthRankList = _.orderBy(financeMonthRankObject[selectedMonthRank].map((item: any) => {return {...item, rankSum: parseInt(item.rankSum), count: parseInt(item.count)}}), ['count', 'rankSum'], ['desc', 'asc']);
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
      rankStockInfo.equalCost = parseInt(equalInvestMoney).toFixed(0);
      rankStockInfo.weightCost = parseInt(getAddWeightValue(investMoney, stockLength, weightRank).toFixed(0));
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
</script>

<div class="flex w-full h-full bg-gray-600 relative">
  <div class="flex flex-col w-full h-full p-2 space-y-2">
    <div class="flex flex-row w-full h-[50%] space-x-2">
      <!-- 모의 투자하기 -->
      <div class="flex flex-col w-[70%] h-full border border-gray-200 rounded p-2 space-y-2">
        <InvestConfidence
          on:onInvestCallback={onInvestCallback}
        />
        <div class="flex flex-col grow overflow-auto border rounded bg-gray-50">
          <div class="flex w-full h-[30px] items-center space-x-2 text-white rounded-t px-2 bg-gray-800">
            <p class="w-[5%] text-center">{'Rank'}</p>
            <p class="w-[10%] text-center">{'코드명'}</p>
            <p class="w-[20%]">{'종목명'}</p>
            <p class="w-[15%] text-right">{`${searchDuration?.month ?? 'N'}달전 주가`}</p>
            <p class="w-[15%] text-right">{'현재주가'}</p>
            <p class="w-[5%]">{'등락'}</p>
            <p class="w-[15%] text-right">{'균등투자금'}</p>
            <p class="w-[15%] text-right">{'균등투자결과'}</p>
            <p class="w-[15%] text-right">{'가중투자금'}</p>
            <p class="w-[15%] text-right">{'가중투자결과'}</p>
          </div>
          {#if calRankStockList.length > 0 && listProgress === false}
            <div class="flex flex-col h-full overflow-auto space-y-1">
              {#each calRankStockList as calRankStockInfo, index}
                <div class="flex w-full h-[30px] items-center space-x-2 text-black border-b px-2">
                  <p class="w-[5%] text-center">{index + 1}</p>
                  <p class="w-[10%] text-center">{calRankStockInfo.code}</p>
                  <p class="w-[20%]">{calRankStockInfo.name}</p>
                  <p class="w-[15%] text-right">{`${formatIncludeComma(calRankStockInfo.startCost)} ₩`}</p>
                  <p class="w-[15%] text-right">{`${formatIncludeComma(calRankStockInfo.endCost)} ₩`}</p>
                  <p class="w-[5%]">{@html setUpDownRatioTag(calRankStockInfo.startCost ?? 0, calRankStockInfo.endCost ?? 0)}</p>
                  <p class="w-[15%] text-right">{`${formatIncludeComma(calRankStockInfo?.equalCost)} ₩`}</p>
                  <p class="w-[15%] text-right" style="color: {setTextColorByUpDown(calRankStockInfo?.equalExpectCost, calRankStockInfo?.equalCost)}">{`${formatIncludeComma(calRankStockInfo?.equalExpectCost)} ₩`}</p>
                  <p class="w-[15%] text-right ">{`${formatIncludeComma(calRankStockInfo?.weightCost)} ₩`}</p>
                  <p class="w-[15%] text-right" style="color: {setTextColorByUpDown(calRankStockInfo?.weightExpectCost, calRankStockInfo?.weightCost)}">{`${formatIncludeComma(calRankStockInfo?.weightExpectCost)} ₩`}</p>
                </div>
              {/each}
            </div>
          {:else if listProgress}
            <div class="flex w-full h-full justify-center items-center font-bold text-gray">
              <ProgressCircle
                size={100}
                thickness={10}
                isLarge={true}
                isTextBlack={true}
                text={'투자 항목 데이터 조회 중...'}
              />
            </div>
          {:else}
            <div class="flex w-full h-full justify-center items-center text-black font-bold">
              {'투자 항목이 없습니다.'}
            </div>
          {/if}
        </div>
      </div>
      <!-- 월별 항목 불러오기 -->
      <div class="flex flex-col w-[30%] h-full">
        <div class="flex flex-row space-x-2 px-2">
          {#each investModeList as investModeInfo}
            <button class="border-t border-x px-2 rounded-t text-lg {selectedInvestMode === investModeInfo.value ? 'font-bold bg-gray-800' : ''} text-white"
              on:click={() => {
                selectedInvestMode = investModeInfo.value;
              }}
            >
              {investModeInfo.name}
            </button>
          {/each}
        </div>
        <div class="flex flex-col grow border border-gray-200 rounded p-2 space-y-2">
          <!-- 고정 항목 -->
          {#if selectedInvestMode === 1}
            <div class="flex flex-row h-[75px] w-full space-x-2">
              <!-- 월별 선택 -->
              <div class="flex flex-wrap h-full w-full border rounded-md overflow-auto px-1 py-0.5 bg-gray-800">
                {#if !!financeMonthRankObject}
                  {#each Object.keys(financeMonthRankObject) as financeMonth}
                    <button class="border border-gray-400 h-[30px] rounded-md px-2 mr-1 my-0.5 {selectedMonthRank === financeMonth ? 'bg-white' : 'bg-gray-500 text-white'}" on:click={async () => {
                      selectedMonthRank = financeMonth;
                      selectedFinanceMonthRankList = financeMonthRankObject[selectedMonthRank];
                      selectedFinanceMonthRankList = _.orderBy(financeMonthRankObject[selectedMonthRank].map((item) => {return {...item, rankSum: parseInt(item.rankSum), count: parseInt(item.count)}}), ['count', 'rankSum'], ['desc', 'asc']);
                    }}>{`${financeMonth} (총 ${financeMonthRankObject[financeMonth][0]?.count ?? 0}회)`}</button>
                  {/each}
                {/if}
              </div>
              <!-- topN 선택 -->
              <div class="flex flex-wrap h-full w-full border rounded-md overflow-auto px-1 py-0.5 bg-gray-800">
                {#if !!topNList}
                  {#each topNList as topNInfo}
                    <button class="border border-gray-400 h-[30px] rounded-md px-2 mr-1 my-0.5 {(selectedTopN === topNInfo.value || (topNInfo.name === 'ALL' && selectedTopN > 100)) ? 'bg-white' : 'bg-gray-500 text-white'}" on:click={async () => {
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
            <div class="flex flex-wrap grow w-full border rounded-md overflow-auto px-1 py-0.5 bg-gray-50">
              {#if selectedFinanceMonthRankList.length > 0}
                <div class="h-[300px] w-full">
                  {#each selectedFinanceMonthRankList.slice(1, selectedTopN + 1) as financeMonthRankInfo, index}
                    <button class="border-white h-[30px] rounded-md px-2 mr-1 my-0.5 bg-gray-600 text-white" on:click={async () => {
                    }}>{`${index+1}위 ${financeMonthRankInfo.name}(${financeMonthRankInfo.code})`}</button>
                  {/each}
                </div>
              {/if}
            </div>
          {:else}
            <!-- 선택 항목 -->
            <div class="flex flex-wrap grow border rounded-md overflow-auto px-1 py-0.5 bg-gray-50">
              <div class="flex flex-row h-[300px] w-full">
                {#if choicedStockInfoList.length > 0}
                  {#each choicedStockInfoList as choicedStockInfo}
                    <button class="border-white h-[30px] rounded-md px-2 mr-1 my-0.5 bg-gray-600 text-white">
                      {choicedStockInfo.name}
                    </button>
                  {/each}
                {/if}
                <button class="flex border h-[30px] bg-gray-600 border-black rounded-md items-center px-1 mr-1 my-0.5" on:click={async() => {
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
                  ➕
                </button>
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>
    <div class="flex flex-row w-full h-[50%] border border-gray-200 bg-gray-800 rounded p-10 space-x-10">
      {#if !!investResultInfo && listProgress === false}
        <div class="flex flex-col w-[50%] h-full border rounded-md bg-white p-10">
          <p class="font-bold text-5xl">{'⚌ 균등투자결과'}</p>
          <div class='flex flex-col grow justify-center space-y-5 px-20'>
            <div class="flex flex-row space-x-10 text-3xl">
              <p class="font-bold w-[300px]">{'✔ 투자시작금액'}</p>
              <p class="flex grow justify-end">{`${formatIncludeComma(investResultInfo?.investMoney) ?? '-'} ₩`}</p>
            </div>
            <div class="flex flex-row space-x-10 text-3xl">
              <p class="font-bold w-[300px]">{'✔ 투자결과금액'}</p>
              <p class="flex grow justify-end">{`${formatIncludeComma(investResultInfo?.equalExpectCost) ?? '-'} ₩`}</p>
            </div>
            <div class="flex flex-row space-x-10 text-3xl">
              <p class="font-bold w-[300px]">{'✔ 이득/손실금액'}</p>
              <p class="flex grow justify-end" style="color: {setUpDownColor((investResultInfo?.equalExpectCost ?? 0) - (investResultInfo?.investMoney ?? 0))}">
                {@html `(${setUpDownRatioTag(investResultInfo?.investMoney ?? 0, investResultInfo?.equalExpectCost ?? 0)})`}
                {`${formatIncludeComma((investResultInfo?.equalExpectCost ?? 0) - (investResultInfo?.investMoney ?? 0)) ?? '-'}`}
                {'₩'}
              </p>
            </div>
          </div>
        </div>
        <div class="flex flex-col w-[50%] h-full border rounded-md bg-white p-10">
          <p class="font-bold text-5xl">{'⚖ 가중투자결과'}</p>
          <div class='flex flex-col grow justify-center space-y-5 px-20'>
            <div class="flex flex-row space-x-10 text-3xl">
              <p class="font-bold w-[300px]">{'✔ 투자시작금액'}</p>
              <p class="flex grow justify-end">{`${formatIncludeComma(investResultInfo?.investMoney) ?? '-'} ₩`}</p>
            </div>
            <div class="flex flex-row space-x-10 text-3xl">
              <p class="font-bold w-[300px]">{'✔ 투자결과금액'}</p>
              <p class="flex grow justify-end">{`${formatIncludeComma(investResultInfo?.weightExpectCost) ?? '-'} ₩`}</p>
            </div>
            <div class="flex flex-row space-x-10 text-3xl">
              <p class="font-bold w-[300px]">{'✔ 이득/손실금액'}</p>
              <p class="flex grow justify-end" style="color: {setUpDownColor((investResultInfo?.weightExpectCost ?? 0) - (investResultInfo?.investMoney ?? 0))}">
                {@html `(${setUpDownRatioTag(investResultInfo?.investMoney ?? 0, investResultInfo?.weightExpectCost ?? 0)})`}
                {`${formatIncludeComma((investResultInfo?.weightExpectCost ?? 0) - (investResultInfo?.investMoney ?? 0)) ?? '-'}`}
                {'₩'}
              </p>
            </div>
          </div>
        </div>
      {:else if listProgress}
        <div class="flex w-full h-full justify-center items-center font-bold text-gray">
          <ProgressCircle
            size={100}
            thickness={10}
            isLarge={true}
            isTextBlack={false}
            text={'모의투자 결과 계산 중...'}
          />
        </div>
      {:else}
        <div class="flex flex-col w-full h-full justify-center items-center font-bold text-white">
          {'모의투자 결과화면입니다.'}
        </div>
      {/if}
    </div>
  </div>
</div>