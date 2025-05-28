<script lang="ts">
  import { onMount } from 'svelte';
  import type { TradeInfoType } from '$lib/types';
  import { getFinanceDataListByChartMode, setUpDownColor, setUpDownRatioTag, SingleChartBasic } from '$lib/main';
  import { CalenderContent } from '$lib/main/timeLine';
  import { AddTimeLinePopup } from '$lib/main/timeLine';
  import { createComponent, formatIncludeComma } from '$lib/utils/CommonHelper';
  import { saveHistoryInfo, getHistoryInfo } from "$lib/api-connector/FinanceApi";
  import toast from 'svelte-french-toast';

	let componentWidth: number = 0;
  let fullContentWidth: number = 0;

  let contentComponent: HTMLDivElement;

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
      investItemObject[popupResult.code].totalShares += (popupResult.buyYn === 'Y' ? popupResult.todayShares : -popupResult.todayShares);
      investItemObject[popupResult.code].haveAmount += (popupResult.buyYn === 'Y' ? popupResult.buyAmount : -popupResult.buyAmount);
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
      return '📊 이득액 :';
    }

    return profitLossAmount > 0 ? '📈 이득액 :' : '📉 손실액 :';
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
</script>

<div class="flex flex-col w-full h-full">
  <div class="flex flex-col w-full h-[50%] border-b p-2">
    <div class="flex flex-row w-full text-sky-50 italic space-x-10">
      <p class="text-3xl font-bold">{'📝 Virtual Investment'}</p>
      <div class="flex flex-row grow justify-end items-center space-x-5 text-xl font-bold">
        <div class="flex flex-row space-x-2">
          <p class="">{'💰 전체 투자액 :'}</p>
          <p class="">{`${formatIncludeComma(virtualTotalInvestInfo?.totalAmount) ?? '-'} ₩`}</p>
        </div>
        <div class="flex flex-row space-x-2">
          <p class="">{setProfitLossTitleText(virtualTotalInvestInfo?.totalProfitLossAmount)}</p>
          <p class="" style="color: {setUpDownColor(virtualTotalInvestInfo?.totalProfitLossAmount)}; text-shadow: 0 0 5px #fff, 0 0 10px #fff;">
            {`${formatIncludeComma(virtualTotalInvestInfo?.totalProfitLossAmount) ?? '-'} ₩`}
          </p>
          <p style="text-shadow: 0 0 5px #fff, 0 0 10px #fff;">
            <span>{'('}</span>
            {@html setUpDownRatioTag(virtualTotalInvestInfo?.totalAmount, virtualTotalInvestInfo?.totalAmount + virtualTotalInvestInfo?.totalProfitLossAmount)}
            <span>{')'}</span>
          </p>
        </div>
      </div>
      <div class="w-auto">
        <button class="w-[36px] h-[36px] border rounded-md bg-gray-50 z-10" 
          on:click={() => onOpenAddTimeLinePopup(false)}>{'💾'}</button>
      </div>
    </div>
    {#if Object.keys(virtualInvestItemObject).length > 0}
      <div 
        class="flex flex-col w-full hidden-scrollbar overflow-auto space-y-5 rounded-e-md"
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
      <div class="flex w-full h-full justify-center items-center font-bold text-gray-50 text-xl italic">{'💾 버튼을 눌러 종목을 추가해주세요.'}</div>
    {/if}
  </div>
  <div class="flex flex-col w-full h-[50%] border-t p-2">
    <div class="flex flex-row w-full text-sky-50 italic space-x-10">
      <p class="text-3xl font-bold">{'💵 Real Investment'}</p>
      <div class="flex flex-row grow justify-end items-center space-x-5 text-xl font-bold">
        <div class="flex flex-row space-x-2">
          <p class="">{'💰 전체 투자액 :'}</p>
          <p class="">{`${formatIncludeComma(realTotalInvestInfo?.totalAmount) ?? '-'} ₩`}</p>
        </div>
        <div class="flex flex-row space-x-2">
          <p class="">{setProfitLossTitleText(realTotalInvestInfo?.totalProfitLossAmount)}</p>
          <p class="" style="color: {setUpDownColor(realTotalInvestInfo?.totalProfitLossAmount)}; text-shadow: 0 0 5px #fff, 0 0 10px #fff;">
            {`${formatIncludeComma(realTotalInvestInfo?.totalProfitLossAmount) ?? '-'} ₩`}
          </p>
          <p style="text-shadow: 0 0 5px #fff, 0 0 10px #fff;">
            <span>{'('}</span>
            {@html setUpDownRatioTag(realTotalInvestInfo?.totalAmount, realTotalInvestInfo?.totalAmount + realTotalInvestInfo?.totalProfitLossAmount)}
            <span>{')'}</span>
          </p>
        </div>
      </div>
      <div class="w-auto">
        <button class="w-[36px] h-[36px] border rounded-md bg-gray-50 z-10"
          on:click={() => onOpenAddTimeLinePopup(true)}>{'💾'}</button>
      </div>
    </div>
    {#if Object.keys(realInvestItemObject).length > 0}
      <div 
        class="flex flex-col w-full hidden-scrollbar overflow-auto space-y-5 rounded-e-md"
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
      <div class="flex w-full h-full justify-center items-center font-bold text-gray-50 text-xl italic">{'💾 버튼을 눌러 종목을 추가해주세요.'}</div>
    {/if}
  </div>
  {#if isSingleMode}
    <SingleChartBasic
      {singleChartInfo}
      on:closeSingleChartModeCallback={() => {
        isSingleMode = false;
      }}
    />
  {/if}
</div>

<style>
  .hidden-scrollbar {
    scrollbar-width: none; /* Firefox */
  }
  .hidden-scrollbar::-webkit-scrollbar {
    display: none; /* Chrome, Safari */
  }
</style>