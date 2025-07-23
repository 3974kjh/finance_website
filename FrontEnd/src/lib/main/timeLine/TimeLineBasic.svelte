<script lang="ts">
  import { onMount } from 'svelte';
  import { getFinanceDataListByChartMode, setUpDownColor, setUpDownRatioTag, SingleChartBasic } from '$lib/main';
  import { CalenderContent } from '$lib/main/timeLine';
  import { AddTimeLinePopup } from '$lib/main/timeLine';
  import { createComponent, formatIncludeComma } from '$lib/utils/CommonHelper';
  import { saveHistoryInfo, getHistoryInfo } from "$lib/api-connector/FinanceApi";
  import toast from 'svelte-french-toast';
  import type { SplitLayoutSizeType } from '$lib/types';
  import { Pane, Splitpanes } from 'svelte-splitpanes';

	let componentWidth: number = 0;

  const searchDuration: {month: number, week: number} = {month: 12, week: 52};

  let isSingleMode: boolean = false;
  let singleChartInfo: {
		title: string,
		searchDuration: {month: number, week: number},
		chartMode: string,
		chartKey: string,
		detailInfo: any
	} | null = null;

  /**
   * example format
   * '005930': {
        name: '삼성전자',
        code: '005930',
        todayAmount: 55000,
        totalShares: 2,
        haveAmount: 109000,
        data: [
                {
                  name: '삼성전자',
                  code: '005930', 
                  date: '2025.05.09 14:22',
                  todayAmount: 55000,
                  todayShares: 1,
                  totalShares: 2,
                  buyYn: 'Y',
                  buyAmount: 55000,
                  buyReason: '테스트용1'
                },
                {
                  name: '삼성전자',
                  code: '005930', 
                  date: '2025.05.08 12:22',
                  todayAmount: 54000,
                  todayShares: 1,
                  totalShares: 1,
                  buyYn: 'Y',
                  buyAmount: 54000,
                  buyReason: '테스트용2'
                }
        ]
      }
  */
  let virtualInvestItemObject: {[key: string]: any} = {} as {[key: string]: any};
  let realInvestItemObject: {[key: string]: any} = {} as {[key: string]: any};

  let virtualTotalInvestInfo: {
    totalAmount: number,
    totalProfitLossAmount: number
  } = {
    totalAmount: 0,
    totalProfitLossAmount: 0
  }

  let realTotalInvestInfo: {
    totalAmount: number,
    totalProfitLossAmount: number
  } = {
    totalAmount: 0,
    totalProfitLossAmount: 0
  }

  /**
   * 행 레이아웃 사이즈 초기화
   */
  const initialRowSplitLayoutSize = () => {
    return [
      {
        size: 50,
        min: 10,
        max: 100
      },
      {
        size: 50,
        min: 10,
        max: 100
      }
    ]
  }

  /**
   * 행 레이아웃 사이즈
   */
  let splitRowLayoutSize: SplitLayoutSizeType[] = initialRowSplitLayoutSize();

  const setInvestItemTodayInfo = async (stockList: Array<string>, investItemObject: any) => {
    for (let stock of stockList) {
      const financeDataResult = await getFinanceDataListByChartMode(stock, 1, false);
      investItemObject[stock].todayAmount = parseInt(financeDataResult[financeDataResult.length - 1]?.Close ?? 0);
    }

    return investItemObject;
  }

  const refreshAllInvestBindingItems = async () => {
    const getInvestHistoryObject = await getHistoryInfo();

    virtualInvestItemObject = getInvestHistoryObject?.data?.virtualInvestItemObject ?? {};
    realInvestItemObject = getInvestHistoryObject?.data?.realInvestItemObject ?? {};

    virtualInvestItemObject = await setInvestItemTodayInfo(Object.keys(virtualInvestItemObject), virtualInvestItemObject)
    realInvestItemObject = await setInvestItemTodayInfo(Object.keys(realInvestItemObject), realInvestItemObject);

    virtualTotalInvestInfo = setTotalInvestInfo(virtualInvestItemObject);
    realTotalInvestInfo = setTotalInvestInfo(realInvestItemObject);
  }

  onMount(async () => {
    // 행 레이아웃 사이즈 초기화
    const localStorageTimeLineRowLayoutSize = localStorage.getItem('timeLineSplitRowLayoutSize');
    splitRowLayoutSize = !!localStorageTimeLineRowLayoutSize ? JSON.parse(localStorageTimeLineRowLayoutSize) : initialRowSplitLayoutSize();

    await refreshAllInvestBindingItems();
  })

  const onOpenAddTimeLinePopup = async (isReal: boolean) => {
    const popupResult = await createComponent(AddTimeLinePopup, {
      titleName: isReal ? 'Real Investment 항목 추가' : 'Virtual Investment 항목 추가'
    });

    if (!!!popupResult) {
      return;
    }

    let investItemObject = isReal ? realInvestItemObject : virtualInvestItemObject;

    if (Object.keys(investItemObject).includes(popupResult.code)) {
      investItemObject[popupResult.code].todayAmount = popupResult.todayAmount;
      investItemObject[popupResult.code].totalShares = popupResult.buyYn === 'Y' ? 
        (parseInt(investItemObject[popupResult.code].totalShares) + parseInt(popupResult.todayShares)) : (parseInt(investItemObject[popupResult.code].totalShares) - parseInt(popupResult.todayShares));
      investItemObject[popupResult.code].haveAmount = popupResult.buyYn === 'Y' ? 
        (parseInt(investItemObject[popupResult.code].haveAmount) + parseInt(popupResult.buyAmount)) : (parseInt(investItemObject[popupResult.code].haveAmount) - parseInt(popupResult.buyAmount));
      investItemObject[popupResult.code].data = [
        {
          ...popupResult,
          totalShares: investItemObject[popupResult.code].totalShares
        },
        ...investItemObject[popupResult.code].data
      ]
    } else {
      investItemObject[popupResult.code] = {
        name: popupResult.name,
        code: popupResult.code,
        todayAmount: popupResult.todayAmount,
        totalShares: popupResult.todayShares,
        haveAmount: popupResult.buyAmount,
        data: [
          {
            ...popupResult,
            totalShares: popupResult.todayShares
          }
        ]
      }
    }

    if (isReal) {
      realInvestItemObject = investItemObject;
      realTotalInvestInfo = setTotalInvestInfo(realInvestItemObject);
    } else {
      virtualInvestItemObject = investItemObject;
      virtualTotalInvestInfo = setTotalInvestInfo(virtualInvestItemObject);
    };

    const saveResult = await saveHistoryInfo({data: {
      virtualInvestItemObject: virtualInvestItemObject,
      realInvestItemObject: realInvestItemObject
    }});

    if (saveResult.isSuccess) {
      toast.success(`${popupResult.name}[${popupResult.code}] 매매 정보가 등록되었습니다.`);
    } else {
      toast.error(`${popupResult.name}[${popupResult.code}] 매매 정보 등록에 실패하였습니다.`);
    }
  }

  const setTotalInvestInfo = (investItemObject: any) => {
    const investItemList = Object.keys(investItemObject);

    let totalInvestAmount: number = 0;
    let totalInvestProfitLossAmount: number = 0;

    if (investItemList.length < 0) {
      return {
        totalAmount: 0,
        totalProfitLossAmount: 0
      };
    }

    for (let investItem of investItemList) {
      totalInvestAmount += investItemObject[investItem].haveAmount;

      if (investItemObject[investItem].totalShares > 0) {
        totalInvestProfitLossAmount += (investItemObject[investItem].todayAmount - (investItemObject[investItem].haveAmount / investItemObject[investItem].totalShares)) * investItemObject[investItem].totalShares;
      } else {
        totalInvestProfitLossAmount += -investItemObject[investItem].haveAmount;
      }
    }

    return {
      totalAmount: totalInvestAmount,
      totalProfitLossAmount: totalInvestProfitLossAmount
    };
  }

  const setProfitLossTitleText = (profitLossAmount: number | string) => {
    if (!!!profitLossAmount || profitLossAmount === '0') {
      return '이득액 :';
    }

    const numericValue = typeof profitLossAmount === 'string' ? parseFloat(profitLossAmount) : profitLossAmount;
    return numericValue > 0 ? '📈 이득액 :' : '📉 손실액 :';
  }
  
  const onDeleteStockInfoCallback = async (stockInfo: any, isReal: boolean) => {
    if (!!!stockInfo?.code) {
      return;
    }

    if (confirm(`${stockInfo.name}[${stockInfo.code}] 매매 정보를 삭제하시겠습니까?`) === false) {
      return; 
    }

    if (isReal) {
      delete realInvestItemObject[stockInfo.code];
    } else {
      delete virtualInvestItemObject[stockInfo.code];
    }

    const deleteResult = await saveHistoryInfo({data: {
      virtualInvestItemObject: virtualInvestItemObject,
      realInvestItemObject: realInvestItemObject
    }});

    if (deleteResult.isSuccess) {
      toast.success(`${stockInfo.name}[${stockInfo.code}] 매매 정보가 삭제되었습니다.`);
    } else {
      toast.error(`${stockInfo.name}[${stockInfo.code}] 매매 정보 삭제에 실패하였습니다.`);
    }

    await refreshAllInvestBindingItems();
  }

  const onShowDetailStockInfoCallback = (e: any) => {
    if (!!!e?.detail?.code) {
      return;
    }

    singleChartInfo = {
      title: e.detail.name,
      searchDuration: searchDuration,
      chartMode: e.detail.code,
      chartKey: e.detail.code,
      detailInfo: null
    }

    isSingleMode = true;
  }

  /**
   * 행 레이아웃 사이즈 변경 이벤트 처리
   * @param event
   */
  const onLayoutRowResized = (event: CustomEvent) => {
    if (!!!event || !!!event.detail || event.detail?.length < 1) {
      return;
    }

    splitRowLayoutSize = event.detail as SplitLayoutSizeType[];

    // 행 레이아웃 사이즈 저장
    localStorage.setItem('timeLineSplitRowLayoutSize', JSON.stringify(splitRowLayoutSize));
  };
</script>

<div class="flex flex-row w-full h-full bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-900 relative overflow-hidden p-4">
  <!-- 배경 데코레이션 -->
  <div class="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,_rgba(59,130,246,0.1)_1px,_transparent_0)] bg-[size:32px_32px] pointer-events-none"></div>
  <div class="absolute top-0 left-0 w-96 h-96 bg-gradient-to-r from-violet-500/20 to-purple-500/20 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2 animate-pulse"></div>
  <div class="absolute bottom-0 right-0 w-96 h-96 bg-gradient-to-r from-cyan-500/20 to-teal-500/20 rounded-full blur-3xl translate-x-1/2 translate-y-1/2 animate-pulse"></div>

  <Splitpanes on:resized={onLayoutRowResized}>
    <!-- Virtual Investment Section -->
    <Pane size={splitRowLayoutSize[0].size} minSize={splitRowLayoutSize[0].min} maxSize={splitRowLayoutSize[0].max}>
      <div class="flex flex-col h-full relative z-10 mr-2">
        <div class="flex flex-row w-full items-center justify-between mb-4 bg-slate-800/60 backdrop-blur-xl rounded-2xl border border-slate-600/40 shadow-2xl shadow-black/20 p-6">
          <div class="flex items-center space-x-4">
            <div class="w-12 h-12 bg-gradient-to-r from-violet-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg shadow-violet-500/30">
              <span class="text-white text-xl">📝</span>
            </div>
            <h2 class="text-2xl font-black bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">Virtual Investment</h2>
          </div>
          
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-6">
              <div class="flex items-center space-x-3 bg-slate-700/80 backdrop-blur-sm rounded-xl px-4 py-2 border border-slate-500/30">
                <div class="w-6 h-6 bg-gradient-to-r from-emerald-400 to-teal-400 rounded-lg flex items-center justify-center">
                  <span class="text-white text-sm">💰</span>
                </div>
                <span class="text-slate-200 font-medium text-sm">전체 투자액 :</span>
                <span class="text-white font-bold text-lg">{`${formatIncludeComma(virtualTotalInvestInfo?.totalAmount) ?? '-'} ₩`}</span>
              </div>
              
              <div class="flex items-center space-x-3 bg-slate-200/90 backdrop-blur-sm rounded-xl px-4 py-2 border border-slate-300/50 shadow-sm">
                <span class="text-slate-700 font-medium text-sm">{setProfitLossTitleText(virtualTotalInvestInfo?.totalProfitLossAmount)}</span>
                <span class="font-bold text-lg drop-shadow-lg" style="color: {setUpDownColor(virtualTotalInvestInfo?.totalProfitLossAmount)};">
                  {`${formatIncludeComma(virtualTotalInvestInfo?.totalProfitLossAmount) ?? '-'} ₩`}
                </span>
                <span class="text-slate-600 font-medium">
                  <span>{'('}</span>
                  {@html setUpDownRatioTag(virtualTotalInvestInfo?.totalAmount, virtualTotalInvestInfo?.totalAmount + virtualTotalInvestInfo?.totalProfitLossAmount)}
                  <span>{')'}</span>
                </span>
              </div>
            </div>
            
            <button class="w-12 h-12 bg-gradient-to-r from-violet-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-violet-500/30 transition-all duration-200 hover:scale-110 hover:shadow-xl hover:shadow-violet-500/40 border border-violet-400/50" 
              on:click={() => onOpenAddTimeLinePopup(false)}>
              <span class="text-white text-xl">➕</span>
            </button>
          </div>
        </div>
        
        {#if Object.keys(virtualInvestItemObject).length > 0}
          <div 
            class="flex flex-col w-full h-full bg-slate-800/40 backdrop-blur-xl rounded-2xl border border-slate-600/40 shadow-inner p-4 space-y-4 overflow-auto modern-scrollbar"
            bind:clientWidth={componentWidth}
          >
            {#each Object.keys(virtualInvestItemObject) as virtualInvestItem, index}
              <CalenderContent
                bind:componentWidth
                investItemInfo={virtualInvestItemObject[virtualInvestItem]}
                uniqueId={index}
                on:onDeleteStockInfoCallback={(e) => onDeleteStockInfoCallback(e?.detail, false)}
                on:onShowDetailStockInfoCallback={onShowDetailStockInfoCallback}
              />
            {/each}
          </div>
        {:else}
          <div class="flex w-full h-full justify-center items-center bg-slate-800/40 backdrop-blur-xl rounded-2xl border border-slate-600/40 shadow-inner">
            <div class="text-center space-y-3">
              <div class="w-16 h-16 bg-gradient-to-r from-slate-600 to-slate-500 rounded-2xl flex items-center justify-center mx-auto shadow-lg">
                <span class="text-white text-2xl">➕</span>
              </div>
              <p class="text-slate-300 font-medium text-lg">➕ 버튼을 눌러 종목을 추가해주세요</p>
            </div>
          </div>
        {/if}
      </div>
    </Pane>
    <!-- Real Investment Section -->
    <Pane size={splitRowLayoutSize[1].size} minSize={splitRowLayoutSize[1].min} maxSize={splitRowLayoutSize[1].max}>
      <div class="flex flex-col h-full relative z-10 ml-2">
        <div class="flex flex-row w-full items-center justify-between mb-4 bg-slate-800/60 backdrop-blur-xl rounded-2xl border border-slate-600/40 shadow-2xl shadow-black/20 p-6">
          <div class="flex items-center space-x-4">
            <div class="w-12 h-12 bg-gradient-to-r from-emerald-500 to-green-600 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-500/30">
              <span class="text-white text-xl">💵</span>
            </div>
            <h2 class="text-2xl font-black bg-gradient-to-r from-emerald-400 to-green-400 bg-clip-text text-transparent">Real Investment</h2>
          </div>
          
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-6">
              <div class="flex items-center space-x-3 bg-slate-700/80 backdrop-blur-sm rounded-xl px-4 py-2 border border-slate-500/30">
                <div class="w-6 h-6 bg-gradient-to-r from-emerald-400 to-teal-400 rounded-lg flex items-center justify-center">
                  <span class="text-white text-sm">💰</span>
                </div>
                <span class="text-slate-200 font-medium text-sm">전체 투자액 :</span>
                <span class="text-white font-bold text-lg">{`${formatIncludeComma(realTotalInvestInfo?.totalAmount) ?? '-'} ₩`}</span>
              </div>
              
              <div class="flex items-center space-x-3 bg-slate-200/90 backdrop-blur-sm rounded-xl px-4 py-2 border border-slate-300/50 shadow-sm">
                <span class="text-slate-700 font-medium text-sm">{setProfitLossTitleText(realTotalInvestInfo?.totalProfitLossAmount)}</span>
                <span class="font-bold text-lg drop-shadow-lg" style="color: {setUpDownColor(realTotalInvestInfo?.totalProfitLossAmount)};">
                  {`${formatIncludeComma(realTotalInvestInfo?.totalProfitLossAmount) ?? '-'} ₩`}
                </span>
                <span class="text-slate-600 font-medium">
                  <span>{'('}</span>
                  {@html setUpDownRatioTag(realTotalInvestInfo?.totalAmount, realTotalInvestInfo?.totalAmount + realTotalInvestInfo?.totalProfitLossAmount)}
                  <span>{')'}</span>
                </span>
              </div>
            </div>
            
            <button class="w-12 h-12 bg-gradient-to-r from-emerald-500 to-green-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/30 transition-all duration-200 hover:scale-110 hover:shadow-xl hover:shadow-emerald-500/40 border border-emerald-400/50"
              on:click={() => onOpenAddTimeLinePopup(true)}>
              <span class="text-white text-xl">➕</span>
            </button>
          </div>
        </div>
        
        {#if Object.keys(realInvestItemObject).length > 0}
          <div 
            class="flex flex-col w-full h-full bg-slate-800/40 backdrop-blur-xl rounded-2xl border border-slate-600/40 shadow-inner p-4 space-y-4 overflow-auto modern-scrollbar"
            bind:clientWidth={componentWidth}
          >
            {#each Object.keys(realInvestItemObject) as realInvestItem, index}
              <CalenderContent
                bind:componentWidth
                investItemInfo={realInvestItemObject[realInvestItem]}
                uniqueId={index + 100}
                on:onDeleteStockInfoCallback={(e) => onDeleteStockInfoCallback(e?.detail, true)}
                on:onShowDetailStockInfoCallback={onShowDetailStockInfoCallback}
              />
            {/each}
          </div>
        {:else}
          <div class="flex w-full h-full justify-center items-center bg-slate-800/40 backdrop-blur-xl rounded-2xl border border-slate-600/40 shadow-inner">
            <div class="text-center space-y-3">
              <div class="w-16 h-16 bg-gradient-to-r from-slate-600 to-slate-500 rounded-2xl flex items-center justify-center mx-auto shadow-lg">
                <span class="text-white text-2xl">➕</span>
              </div>
              <p class="text-slate-300 font-medium text-lg">➕ 버튼을 눌러 종목을 추가해주세요</p>
            </div>
          </div>
        {/if}
      </div>
    </Pane>
  </Splitpanes>

  {#if isSingleMode && singleChartInfo}
    <div class="absolute inset-0 z-20 bg-black/50 backdrop-blur-sm">
      <SingleChartBasic
        singleChartInfo={singleChartInfo}
        on:closeSingleChartModeCallback={() => {
          isSingleMode = false;
        }}
      />
    </div>
  {/if}
</div>

<style>
  /* Splitpanes 투명 배경 스타일 */
  :global(.splitpanes) {
    background: transparent !important;
  }

  :global(.splitpanes__pane) {
    background: transparent !important;
  }

  :global(.splitpanes__splitter) {
    background: transparent !important;
    border: none !important;
    position: relative;
    cursor: col-resize;
  }

  :global(.splitpanes--horizontal .splitpanes__splitter) {
    cursor: row-resize;
  }

  /* :global(.splitpanes__splitter:hover) {
    background: rgba(255, 255, 255, 0.1) !important;
  } */

  /* 스플릿 바 ::before, ::after 가상 요소 아이콘 스타일 */
  :global(.splitpanes__splitter::before),
  :global(.splitpanes__splitter::after) {
    background-color: white !important;
    border-color: white !important;
    color: white !important;
    fill: white !important;
    stroke: white !important;
  }

  /* 호버 시 아이콘 강조 */
  :global(.splitpanes__splitter:hover *) {
    color: white !important;
    fill: white !important;
    stroke: white !important;
  }

  /* 호버 시 ::before, ::after 가상 요소 강조 */
  :global(.splitpanes__splitter:hover::before),
  :global(.splitpanes__splitter:hover::after) {
    background-color: rgba(255, 255, 255, 0.9) !important;
  }

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

  /* 현대적인 스크롤바 */
  .modern-scrollbar {
    scrollbar-width: thin;
    scrollbar-color: rgba(148, 163, 184, 0.6) rgba(0, 0, 0, 0.1);
  }

  .modern-scrollbar::-webkit-scrollbar {
    width: 8px;
  }

  .modern-scrollbar::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.1);
    border-radius: 10px;
  }

  .modern-scrollbar::-webkit-scrollbar-thumb {
    background: linear-gradient(45deg, rgba(148, 163, 184, 0.6), rgba(203, 213, 225, 0.8));
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .modern-scrollbar::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(45deg, rgba(100, 116, 139, 0.8), rgba(148, 163, 184, 0.9));
  }

  /* 버튼 효과 */
  button {
    outline: none;
  }

  button:focus {
    outline: none;
    box-shadow: none;
  }

  /* 텍스트 그라데이션 */
  .bg-clip-text {
    -webkit-background-clip: text;
    background-clip: text;
  }

  /* 드롭 섀도우 효과 */
  .drop-shadow-lg {
    filter: drop-shadow(0 10px 8px rgb(0 0 0 / 0.04)) drop-shadow(0 4px 3px rgb(0 0 0 / 0.1));
  }

  /* 반응형 디자인 */
  @media (max-width: 768px) {
    .modern-scrollbar::-webkit-scrollbar {
      width: 6px;
    }
  }
</style>