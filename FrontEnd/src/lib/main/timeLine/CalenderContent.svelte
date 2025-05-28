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
			clearTimeout(intervalTimer);
		};
	};

  const setProfitLossTitleText = (profitLossAmount: number | string) => {
    if (!!!profitLossAmount || profitLossAmount === '0') {
      return '📊';
    }

    return profitLossAmount > 0 ? '📈' : '📉';
  }
</script>

<div class="flex flex-col w-full h-[350px]">
  <div class="flex flex-row w-full h-[50px] text-white space-x-2 text-xl">
    <button class="font-bold cursor-pointer"
      on:click={() => dispatch('onDeleteStockInfoCallback', investItemInfo)}
    >{`🗑️`}</button>
    <p class="flex w-auto font-bold items-center cursor-pointer"
      on:click={() => dispatch('onShowDetailStockInfoCallback', investItemInfo)}
    >{`${investItemInfo.name} [${investItemInfo.code}]`}</p>
    <div class="flex w-auto space-x-1 pr-8 items-center">
      <a 
        class="border rounded-md"
        href="{`https://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A${investItemInfo.code ?? ''}`}"
        title="FnGuide_{investItemInfo?.name}"
        target="_blank"
        style="
          background-image: url({CompanyGuideImg});
          background-size: cover;
          background-position: center;
          width: 28px;   /* 버튼 크기 지정 */
          height: 28px;
        "
      />
      <a
        class="border rounded-md"
        href="{`https://finance.naver.com/item/main.naver?code=${investItemInfo.code ?? ''}`}"
        title="NAVER_{investItemInfo?.name}"
        target="_blank"
        style="
          background-image: url({NaverFinanceImg});
          background-size: cover;
          background-position: center;
          width: 28px;   /* 버튼 크기 지정 */
          height: 28px;
        "
      />
    </div>
    <div class="flex flex-row grow justify-start items-center space-x-5">
      <div class="flex flex-row w-[250px] space-x-2">
        <p class="flex w-[80px]">{'현재가 :'}</p>
        <p class="flex grow justify-end">
          {`${formatIncludeComma(investItemInfo.todayAmount) ?? '-'} ₩`}
        </p>
      </div>
      <div class="flex flex-row w-[250px] space-x-2">
        <p class="flex w-[80px]">{'평단가 :'}</p>
        <p class="flex grow justify-end">
          {`${formatIncludeComma(investItemInfo.haveAmount / investItemInfo.totalShares) ?? '-'} ₩`}
        </p>
      </div>
      <div class="flex flex-row w-[250px] space-x-2">
        <p class="flex w-[80px]">{'투자액 :'}</p>
        {#if investItemInfo.totalShares > 0}
          <p class="flex grow justify-end">
            {`${formatIncludeComma(investItemInfo.haveAmount) ?? '-'} ₩`}
          </p>
        {:else}
          <p class="flex grow justify-end">
            {`- ₩`}
          </p>
        {/if}
      </div>
      <div class="flex flex-row grow space-x-2 font-bold">
        {#if investItemInfo.totalShares > 0}
          {@const totalProfitLossAmount = (investItemInfo.todayAmount - (investItemInfo.haveAmount / investItemInfo.totalShares)) * investItemInfo.totalShares}
          <p class="flex grow justify-end" style="color: {setUpDownColor(totalProfitLossAmount)}; text-shadow: 0 0 5px #fff, 0 0 10px #fff;">
            {setProfitLossTitleText(totalProfitLossAmount)}
            {`${formatIncludeComma(totalProfitLossAmount) ?? '-'} ₩`}
          </p>
          <p style="text-shadow: 0 0 5px #fff, 0 0 10px #fff;">
            <span>{'('}</span>
            {@html setUpDownRatioTag(investItemInfo?.haveAmount, investItemInfo?.haveAmount + totalProfitLossAmount)}
            <span>{')'}</span>
          </p>
        {:else}
          {@const totalProfitLossAmount = -investItemInfo.haveAmount}
          <p class="flex grow justify-end" style="color: {setUpDownColor(totalProfitLossAmount)}; text-shadow: 0 0 5px #fff, 0 0 10px #fff;">
            {setProfitLossTitleText(totalProfitLossAmount)}
            {`${formatIncludeComma(totalProfitLossAmount) ?? '-'} ₩`}
          </p>
          <p style="text-shadow: 0 0 5px #fff, 0 0 10px #fff;">
            <span>{'('}</span>
            {@html setUpDownRatioTag(investItemInfo?.haveAmount, investItemInfo?.haveAmount + totalProfitLossAmount)}
            <span>{')'}</span>
          </p>
        {/if}
      </div>
    </div>
  </div>
  <div class="flex w-full h-[300px] relative border rounded-md bg-white">
    {#if contentComponent?.scrollWidth > componentWidth}
      <!-- Hover Scroll -->
      <button class="left_arrow_{uniqueId} rounded-s-md absolute h-full w-[20px] bg-gray-500/20 top-[0px] left-[0px] hover:bg-gray-800/50 z-10"
        on:mouseover={(e) => {
          onLongMouseOver(document.querySelector(`.left_arrow_${uniqueId}`), 10, scrollMoveLeft);
        }}
      />
      <button class="right_arrow_{uniqueId} rounded-e-md absolute h-full w-[20px] bg-gray-500/20 top-[0px] right-[0px] hover:bg-gray-800/50 z-10"
        on:mouseover={(e) => {
          onLongMouseOver(document.querySelector(`.right_arrow_${uniqueId}`), 10, scrollMoveRight);
        }}
      />
    {/if}
    <div
      bind:this={contentComponent}
      class="flex flex-row hidden-scrollbar overflow-auto relative space-x-5"
      style="width: {componentWidth}px;"
    >
      <!-- Line -->
      <div 
        class="absolute border-2 border-black top-[25px]"
        style="width: {(contentComponent?.scrollWidth ?? 0)}px"
      />
      {#if !!investItemInfo?.data && investItemInfo?.data.length > 0}
        {#each investItemInfo.data as detailInvestItemInfo}
          {@const profitLossAmount = (investItemInfo.todayAmount - detailInvestItemInfo.todayAmount) * detailInvestItemInfo.todayShares}
          <div class="flex flex-col h-[300px] relative">
            <!-- Left Pin -->
            <div class="absolute border-2 border-black rounded-full h-[20px] w-[20px] bg-sky-50 top-[15px] left-[50px]"/>
            <div class="absolute h-[25px] border border-black top-[35px] left-[59px]"/>
            <!-- Right Pin -->
            <div class="absolute border-2 border-black rounded-full h-[20px] w-[20px] bg-sky-50 top-[15px] left-[250px]"/>
            <div class="absolute h-[25px] border border-black top-[35px] left-[259px]"/>
            <!-- Content -->
            <div class="flex h-[40px]"/>
            <div class="flex flex-col w-[320px] h-[230px] justify-top mt-5 space-y-1 bg-white border border-black">
              <p class="flex border-b h-[30px] px-2 font-bold items-center bg-sky-50">{`${detailInvestItemInfo.date} (${formatIncludeComma(detailInvestItemInfo.todayAmount) ?? '-'} ₩)`}</p>
              <!-- △ / ▽ -->
              <div class="flex flex-row w-full space-x-2 px-2">
                <p class="flex w-[80px]">{'총주식수 :'}</p>
                <p class="flex grow justify-start" style="color: {setUpDownColor(detailInvestItemInfo.buyYn === 'Y' ? 1 : -1)}">{`${detailInvestItemInfo.totalShares}주 (${detailInvestItemInfo.buyYn === 'Y' ? '△' : '▽'}${detailInvestItemInfo.todayShares}주)`}</p>
              </div>
              <div class="flex flex-row w-full space-x-2 px-2">
                <p class="flex w-[80px]">{'투자금액 :'}</p>
                <p class="flex grow justify-start">{`${formatIncludeComma(detailInvestItemInfo.buyAmount) ?? '-'} ₩`}</p>
              </div>
              <div class="flex flex-row w-full space-x-2 px-2">
                <p class="flex w-[80px]">{'이득금액 :'}</p>
                <div class="flex flex-row grow justify-start space-x-1" style="color: {setUpDownColor(profitLossAmount)}">
                  <p>{`${formatIncludeComma(profitLossAmount) ?? '-'} ₩`}</p>
                  <p>
                    <span>{'('}</span>
                    {@html setUpDownRatioTag(detailInvestItemInfo.todayAmount, investItemInfo.todayAmount)}
                    <span>{')'}</span>
                  </p>
                </div>
              </div>
              <div class="flex flex-row w-full space-x-2 px-2">
                <p class="flex w-[80px]">{'투자사유 :'}</p>
                <div class="border p-1 w-[220px] h-[100px] overflow-y-auto overflow-x-hidden scrollbar-thin-custom text-wrap break-words">
                  {@html detailInvestItemInfo.buyReason.replaceAll('\n', '<br/>')}
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
  .hidden-scrollbar {
    scrollbar-width: none; /* Firefox */
  }
  .hidden-scrollbar::-webkit-scrollbar {
    display: none; /* Chrome, Safari */
  }

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