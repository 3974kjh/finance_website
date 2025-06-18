<script lang="ts">
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';
  import type { TradeInfoType } from '$lib/types';
  import { setUpDownRatioTag, setUpDownIcon, setUpDownColor } from '$lib/main';
  import { calculateRatio, formatCostValue, formatIncludeComma } from '$lib/utils/CommonHelper';
  import { NaverFinanceImg, CompanyGuideImg } from '$lib/images/logo';

  const dispatch = createEventDispatcher();

  let contentComponent: HTMLDivElement;

  export let componentWidth: number;
  export let investItemInfo: {
    name: string,
    code: string,
    totalShares: number,
    todayAmount: number,
    haveAmount: number,
    data: Array<TradeInfoType>
  };
  export let uniqueId: number;

  onMount(() => {
    if (typeof document !== 'undefined') {
      // document.addEventListener('onOpenAddTimeLinePopupCallback', onOpenAddTimeLinePopupCallback);
    }
  })

  onDestroy(() => {
    if (typeof document !== 'undefined') {
      // document.removeEventListener('onOpenAddTimeLinePopupCallback', onOpenAddTimeLinePopupCallback);
    }
  })

  /**
	 * 스크롤 이동 왼쪽
	 */
	const scrollMoveLeft = () => {
    // 스크롤 위치가 시작인 경우 리턴
		if (contentComponent?.scrollLeft === 0) {
      return;
		}
    
		contentComponent.scrollTo({ left: contentComponent.scrollLeft - 10, behavior: 'auto' });
	};

	/**
	 * 스크롤 이동 오른쪽
	 */
	const scrollMoveRight = () => {
    // 스크롤 위치가 끝인 경우 리턴
		if (contentComponent?.scrollLeft >= contentComponent?.scrollWidth - contentComponent?.offsetWidth) {
      return;
		}

		contentComponent.scrollTo({ left: contentComponent?.scrollLeft + 10, behavior: 'auto' });
	};

  /**
	 * 페이지 자동 스크롤 이동
	 * @param buttonDom
	 * @param duration
	 * @param callback
	 */
	const onLongMouseOver = (buttonDom: HTMLButtonElement | null, duration: number, callback: any) => {
		if (!!!buttonDom) {
			return;
		}

		// duration 마다 callback함수 실행
		const intervalTimer = setInterval(callback, duration);
		// 마우스 out이벤트 시, 종료
		buttonDom.onmouseout = () => {
			clearInterval(intervalTimer);
		};
	};

  const setProfitLossTitleText = (profitLossAmount: number | string) => {
    if (!!!profitLossAmount || profitLossAmount === '0') {
      return '📊';
    }

    const numericValue = typeof profitLossAmount === 'string' ? parseFloat(profitLossAmount) : profitLossAmount;
    return numericValue > 0 ? '📈' : '📉';
  }
</script>

<div class="flex flex-col w-full min-h-[420px] max-h-[600px] h-auto bg-slate-800/40 backdrop-blur-xl rounded-2xl border border-slate-600/40 shadow-lg shadow-black/10 p-4 overflow-hidden">
  <!-- 헤더 섹션 -->
  <div class="flex flex-row w-full h-[60px] items-center justify-between mb-4 bg-slate-700/60 backdrop-blur-sm rounded-xl border border-slate-500/30 px-4 py-3 shadow-inner flex-shrink-0">
    <!-- 좌측: 삭제 버튼과 종목 정보 -->
    <div class="flex items-center space-x-4">
      <button class="w-10 h-10 bg-gradient-to-r from-red-500 to-red-600 rounded-xl flex items-center justify-center shadow-lg shadow-red-500/30 transition-all duration-200 hover:scale-110 hover:shadow-xl hover:shadow-red-500/40 border border-red-400/50 group"
        on:click={() => dispatch('onDeleteStockInfoCallback', investItemInfo)}
      >
        <svg class="w-4 h-4 text-white group-hover:scale-110 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
      
      <div class="flex items-center space-x-3 cursor-pointer bg-slate-600/60 backdrop-blur-sm rounded-lg px-4 py-2 border border-slate-500/30 transition-all duration-200 hover:bg-slate-500/60 hover:shadow-lg"
        on:click={() => dispatch('onShowDetailStockInfoCallback', investItemInfo)}
      >
        <div class="w-14 h-8 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-sm">
          <span class="text-white text-xs font-bold">{investItemInfo.code}</span>
        </div>
        <span class="text-white font-bold text-lg">{investItemInfo.name}</span>
      </div>
      
      <!-- 외부 링크 버튼들 -->
      <div class="flex space-x-2">
        <a 
          class="w-8 h-8 rounded-lg border border-slate-400/50 shadow-sm transition-all duration-200 hover:scale-110 hover:shadow-md"
          href="{`https://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A${investItemInfo.code ?? ''}`}"
          title="FnGuide_{investItemInfo?.name}"
          target="_blank"
          style="
            background-image: url({CompanyGuideImg});
            background-size: cover;
            background-position: center;
          "
        />
        <a
          class="w-8 h-8 rounded-lg border border-slate-400/50 shadow-sm transition-all duration-200 hover:scale-110 hover:shadow-md"
          href="{`https://finance.naver.com/item/main.naver?code=${investItemInfo.code ?? ''}`}"
          title="NAVER_{investItemInfo?.name}"
          target="_blank"
          style="
            background-image: url({NaverFinanceImg});
            background-size: cover;
            background-position: center;
          "
        />
      </div>
    </div>

    <!-- 우측: 투자 정보 카드들 -->
    <div class="flex items-center space-x-4">
      <div class="flex items-center space-x-2 bg-slate-600/80 backdrop-blur-sm rounded-lg px-3 py-2 border border-slate-500/30">
        <span class="text-slate-300 font-medium text-sm">현재가:</span>
        <span class="text-white font-bold text-sm">{`${formatIncludeComma(investItemInfo.todayAmount) ?? '-'} ₩`}</span>
      </div>
      
      <div class="flex items-center space-x-2 bg-slate-600/80 backdrop-blur-sm rounded-lg px-3 py-2 border border-slate-500/30">
        <span class="text-slate-300 font-medium text-sm">평단가:</span>
        <span class="text-white font-bold text-sm">{`${formatIncludeComma(investItemInfo.haveAmount / investItemInfo.totalShares) ?? '-'} ₩`}</span>
      </div>
      
      <div class="flex items-center space-x-2 bg-slate-600/80 backdrop-blur-sm rounded-lg px-3 py-2 border border-slate-500/30">
        <span class="text-slate-300 font-medium text-sm">투자액:</span>
        {#if investItemInfo.totalShares > 0}
          <span class="text-white font-bold text-sm">{`${formatIncludeComma(investItemInfo.haveAmount) ?? '-'} ₩`}</span>
        {:else}
          <span class="text-white font-bold text-sm">- ₩</span>
        {/if}
      </div>
      
      <div class="flex items-center space-x-2 bg-slate-200/90 backdrop-blur-sm rounded-lg px-3 py-2 border border-slate-300/50 shadow-sm">
        {#if investItemInfo.totalShares > 0}
          {@const totalProfitLossAmount = (investItemInfo.todayAmount - (investItemInfo.haveAmount / investItemInfo.totalShares)) * investItemInfo.totalShares}
          <span class="text-slate-700 font-medium text-sm">{setProfitLossTitleText(totalProfitLossAmount)}:</span>
          <span class="font-bold text-sm drop-shadow-sm" style="color: {setUpDownColor(totalProfitLossAmount)};">
            {`${formatIncludeComma(totalProfitLossAmount) ?? '-'} ₩`}
          </span>
          <span class="text-slate-600 font-medium text-xs">
            <span>{'('}</span>
            {@html setUpDownRatioTag(investItemInfo?.haveAmount, investItemInfo?.haveAmount + totalProfitLossAmount)}
            <span>{')'}</span>
          </span>
        {:else}
          {@const totalProfitLossAmount = -investItemInfo.haveAmount}
          <span class="text-slate-700 font-medium text-sm">{setProfitLossTitleText(totalProfitLossAmount)}:</span>
          <span class="font-bold text-sm drop-shadow-sm" style="color: {setUpDownColor(totalProfitLossAmount)};">
            {`${formatIncludeComma(totalProfitLossAmount) ?? '-'} ₩`}
          </span>
          <span class="text-slate-600 font-medium text-xs">
            <span>{'('}</span>
            {@html setUpDownRatioTag(investItemInfo?.haveAmount, investItemInfo?.haveAmount + totalProfitLossAmount)}
            <span>{')'}</span>
          </span>
        {/if}
      </div>
    </div>
  </div>

  <!-- 타임라인 섹션 -->
  <div class="flex w-full flex-1 relative bg-white/95 backdrop-blur-xl rounded-xl border border-slate-200/50 shadow-inner overflow-hidden">
    {#if contentComponent?.scrollWidth > componentWidth}
      <!-- 스크롤 화살표 -->
      <button class="left_arrow_{uniqueId} rounded-s-xl absolute h-full w-[30px] bg-gradient-to-r from-slate-800/80 to-transparent backdrop-blur-sm top-0 left-0 hover:from-slate-700/90 z-20 flex items-center justify-center transition-all duration-200"
        on:mouseover={(e) => {
          onLongMouseOver(document.querySelector(`.left_arrow_${uniqueId}`), 10, scrollMoveLeft);
        }}
      >
        <span class="text-white text-lg">◀</span>
      </button>
      <button class="right_arrow_{uniqueId} rounded-e-xl absolute h-full w-[30px] bg-gradient-to-l from-slate-800/80 to-transparent backdrop-blur-sm top-0 right-0 hover:from-slate-700/90 z-20 flex items-center justify-center transition-all duration-200"
        on:mouseover={(e) => {
          onLongMouseOver(document.querySelector(`.right_arrow_${uniqueId}`), 10, scrollMoveRight);
        }}
      >
        <span class="text-white text-lg">▶</span>
      </button>
    {/if}
    
    <div
      bind:this={contentComponent}
      class="flex flex-row modern-scrollbar overflow-x-auto overflow-y-hidden relative space-x-6 p-4 w-full h-full"
      style="width: {componentWidth}px;"
    >
      <!-- 타임라인 -->
      <div 
        class="absolute border-2 border-gradient-to-r from-blue-500 to-indigo-600 top-[65px] rounded-full shadow-sm"
        style="width: {(contentComponent?.scrollWidth ?? 0) - 32}px; height: 3px; background: linear-gradient(90deg, #3b82f6, #6366f1);"
      />
      
      {#if !!investItemInfo?.data && investItemInfo?.data.length > 0}
        {#each investItemInfo.data as detailInvestItemInfo, index}
          {@const profitLossAmount = (investItemInfo.todayAmount - detailInvestItemInfo.todayAmount) * detailInvestItemInfo.todayShares}
          {@const isProfit = profitLossAmount >= 0}
          {@const isBuy = detailInvestItemInfo.buyYn === 'Y'}
          <div class="flex flex-col h-full relative flex-shrink-0">
            <!-- 날짜 카드 (타임라인 위쪽에 간격을 두고 위치) -->
            <div class="flex h-[35px] items-center justify-center flex-shrink-0 mb-3">
              <div class="bg-gradient-to-r {isBuy ? 'from-emerald-500 to-green-600' : 'from-red-500 to-red-600'} text-white px-3 py-1.5 rounded-lg text-xs font-bold shadow-lg">
                {detailInvestItemInfo.date.split(' ')[0]}
              </div>
            </div>
            
            <!-- 날짜에서 타임라인으로 연결하는 선 (매달린 느낌) -->
            <div class="absolute w-0.5 h-[27px] bg-gradient-to-b from-slate-400 to-slate-500 top-[35px] left-[50%] transform -translate-x-1/2 z-5"/>
            
            <!-- 타임라인 노드 (라인 높이의 정중앙에 위치) -->
            <div class="absolute w-6 h-6 rounded-full border-3 border-white shadow-lg top-[56px] left-[50%] transform -translate-x-1/2 z-10 {isBuy ? 'bg-gradient-to-r from-emerald-500 to-green-600' : 'bg-gradient-to-r from-red-500 to-red-600'}"/>
            
            <!-- 타임라인에서 카드로 연결하는 선 -->
            <div class="absolute w-0.5 h-[20px] bg-gradient-to-b from-slate-500 to-slate-400 top-[68px] left-[50%] transform -translate-x-1/2 z-5"/>
            
            <!-- 투자 정보 카드 -->
            <div class="flex flex-col w-[300px] flex-1 mt-5 bg-white/95 backdrop-blur-xl rounded-xl border border-slate-200/50 shadow-lg overflow-hidden flex-shrink-0" style="height: calc(100% - 88px); max-height: calc(100% - 88px);">
              <!-- 카드 헤더 -->
              <div class="flex items-center justify-between h-[32px] px-3 py-2 bg-gradient-to-r {isBuy ? 'from-emerald-50 to-green-50' : 'from-red-50 to-red-50'} border-b border-slate-200/50 flex-shrink-0">
                <div class="flex items-center space-x-2">
                  <div class="w-4 h-4 rounded-full {isBuy ? 'bg-emerald-500' : 'bg-red-500'} flex items-center justify-center">
                    <span class="text-white text-xs">{isBuy ? '△' : '▽'}</span>
                  </div>
                  <span class="font-bold text-slate-700 text-xs">{detailInvestItemInfo.date.split(' ')[1]}</span>
                </div>
                <span class="font-bold text-slate-600 text-xs">{`${formatIncludeComma(detailInvestItemInfo.todayAmount) ?? '-'} ₩`}</span>
              </div>
              
              <!-- 카드 내용 -->
              <div class="flex flex-col flex-1 p-3 space-y-1.5 min-h-0 overflow-hidden">
                <div class="flex items-center justify-between flex-shrink-0">
                  <span class="text-slate-600 font-medium text-xs">총주식수:</span>
                  <span class="font-bold text-xs" style="color: {isBuy ? '#059669' : '#dc2626'}">{`${detailInvestItemInfo.totalShares}주 (${isBuy ? '△' : '▽'}${detailInvestItemInfo.todayShares}주)`}</span>
                </div>
                
                <div class="flex items-center justify-between flex-shrink-0">
                  <span class="text-slate-600 font-medium text-xs">투자금액:</span>
                  <span class="text-slate-800 font-bold text-xs">{`${formatIncludeComma(detailInvestItemInfo.buyAmount) ?? '-'} ₩`}</span>
                </div>
                
                <div class="flex items-center justify-between flex-shrink-0">
                  <span class="text-slate-600 font-medium text-xs">이득금액:</span>
                  <div class="flex items-center space-x-1">
                    <span class="font-bold text-xs" style="color: {setUpDownColor(profitLossAmount)}">{`${formatIncludeComma(profitLossAmount) ?? '-'} ₩`}</span>
                    <span class="text-slate-500 text-xs">
                      <span>{'('}</span>
                      {@html setUpDownRatioTag(detailInvestItemInfo.todayAmount, investItemInfo.todayAmount)}
                      <span>{')'}</span>
                    </span>
                  </div>
                </div>
                
                <div class="flex flex-col space-y-1 flex-1 min-h-0 overflow-hidden">
                  <span class="text-slate-600 font-medium text-xs flex-shrink-0">투자사유:</span>
                  <div class="bg-slate-50/80 backdrop-blur-sm border border-slate-200/50 rounded-lg p-3 text-slate-700 text-xs leading-relaxed flex-1 overflow-y-auto modern-scrollbar-small max-h-full">
                    {#if detailInvestItemInfo.buyReason && detailInvestItemInfo.buyReason.trim()}
                      {@html detailInvestItemInfo.buyReason.replaceAll('\n', '<br/>')}
                    {:else}
                      <span class="text-slate-400 italic">투자사유가 입력되지 않았습니다.</span>
                    {/if}
                  </div>
                </div>
              </div>
            </div>
          </div>
        {/each}
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

  /* 현대적인 스크롤바 */
  .modern-scrollbar {
    scrollbar-width: thin;
    scrollbar-color: rgba(148, 163, 184, 0.6) rgba(0, 0, 0, 0.1);
  }

  .modern-scrollbar::-webkit-scrollbar {
    width: 8px;
    height: 8px;
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

  /* 작은 스크롤바 */
  .modern-scrollbar-small {
    scrollbar-width: thin;
    scrollbar-color: rgba(148, 163, 184, 0.4) transparent;
  }

  .modern-scrollbar-small::-webkit-scrollbar {
    width: 4px;
  }

  .modern-scrollbar-small::-webkit-scrollbar-track {
    background: transparent;
  }

  .modern-scrollbar-small::-webkit-scrollbar-thumb {
    background: rgba(148, 163, 184, 0.4);
    border-radius: 6px;
  }

  .modern-scrollbar-small::-webkit-scrollbar-thumb:hover {
    background: rgba(100, 116, 139, 0.6);
  }

  /* 버튼 효과 */
  button {
    outline: none;
  }

  button:focus {
    outline: none;
    box-shadow: none;
  }

  /* 드롭 섀도우 효과 */
  .drop-shadow-sm {
    filter: drop-shadow(0 1px 2px rgb(0 0 0 / 0.05));
  }

  /* 테두리 효과 */
  .border-3 {
    border-width: 3px;
  }

  /* 반응형 디자인 */
  @media (max-width: 768px) {
    .modern-scrollbar::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
  }
</style>