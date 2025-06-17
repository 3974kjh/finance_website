<script lang="ts">
  import { LineChart } from '$lib/component';
  import { getExpectStockValue } from '$lib/api-connector/FinanceApi';
  import type { ExpectResultType } from '$lib/types';
  import { createEventDispatcher, tick } from 'svelte';
  import { setUpDownRatioTag } from '$lib/main';

  export let searchDuration: {month: number, week: number};
  export let title: string = '';
  export let chartMode: string;
  export let chartKey: string | null = null;
  export let dataList: any = [];
  export let height: number = 0;
  export let width: number = 0;
  export let detailInfo: any = null;
  export let widthRangeValue: number = 0;
  export let heightRangeValue: number = 0;

  const dispatch = createEventDispatcher();

  let isMultiLine: boolean = false;

  let expectValue: string = '';
  let afterMonthExpectValue: string = '';
  let nowValue: string = '';

  const addExpectStockValueToChart = async (weekTerm: number) => {
    if (!!!chartKey) {
      return;
    }

    const result = await getExpectStockValue({symbol: chartKey, term: weekTerm});

    if (!!!result || !!!result?.data || dataList.length < 1) {
      return;
    }

    nowValue = result.data?.nowValue;
    expectValue = result.data?.expectValue;
    afterMonthExpectValue = result.data?.afterMonthExpectValue;

    dataList = dataList.map((data: any) => {
      return {
        ...data,
        afterMonthExpectValue: result.data?.afterMonthExpectValue,
        bottomValue: result.data?.bottomValue,
        expectValue: result.data?.expectValue,
        nowValue: result.data?.nowValue,
        topValue: result.data?.topValue
      }
    });

    isMultiLine = true;
    
    await tick();
    
    dispatch('updateDataListCallback', {chartMode: chartMode, dataList: dataList});
  }
</script>

<div class="flex flex-col mr-1 mb-1">
  <div class="flex flex-row h-[30px] w-full items-center relative bg-gradient-to-r from-slate-50 to-gray-50 border-b border-gray-200/50 px-3 rounded-t-xl">
    <p class="font-bold overflow-hidden whitespace-nowrap text-gray-800" 
      style="width: calc(100% - 120px); text-overflow: ellipsis;" 
      title={title}>{title}</p>
    <div class="absolute right-0 flex flex-row">
      {#if isMultiLine}
        <div class="absolute flex flex-col space-y-2 border-0 rounded-xl bg-white/95 backdrop-blur-md p-4 cursor-pointer shadow-2xl shadow-gray-900/20 border border-gray-200/50 z-[9999]" style="top: 35px; right: 0px; min-width: 300px; max-width: 400px;"
          aria-hidden="true"
          on:click={(e) => {
            e.preventDefault();
			      e.stopPropagation(); // 이벤트 전파 중단하기

            isMultiLine = false;
          }}
        >
          <p class="font-bold text-gray-800 border-b border-gray-200 pb-2 text-sm">{`[${title}] (최근 ${searchDuration.month}개월)`}</p>
          <div class="space-y-2 text-sm">
            <div class="flex items-center text-gray-700 flex-wrap">
              <span class="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs mr-2 flex-shrink-0">💲</span>
              <span class="flex-shrink-0 mr-1">현재 가:</span>
              <span class="font-semibold text-gray-900 break-all">{nowValue}</span>
            </div>
            <div class="flex items-center text-gray-700 flex-wrap">
              <span class="w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center text-white text-xs mr-2 flex-shrink-0">🎯</span>
              <span class="flex-shrink-0 mr-1">현재 예측가:</span>
              <span class="font-semibold text-gray-900 break-all mr-1">{expectValue}</span>
              <span class="break-all">{@html setUpDownRatioTag(nowValue, expectValue)}</span>
            </div>
            <div class="flex items-center text-gray-700 flex-wrap">
              <span class="w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center text-white text-xs mr-2 flex-shrink-0">🔮</span>
              <span class="flex-shrink-0 mr-1">한달뒤 예측가:</span>
              <span class="font-semibold text-gray-900 break-all mr-1">{afterMonthExpectValue}</span>
              <span class="break-all">{@html setUpDownRatioTag(nowValue, afterMonthExpectValue)}</span>
            </div>
          </div>
        </div>
      {/if}
      <button class="border-0 bg-transparent hover:bg-gray-100/80 text-gray-600 hover:text-gray-900 px-2 py-1 text-sm rounded-md transition-all duration-200 font-medium" on:click={async () => {
        await addExpectStockValueToChart(searchDuration.week);
      }}>
        <svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
        </svg>
        분석
      </button>
      <button class="border-0 bg-transparent hover:bg-gray-100/80 text-gray-600 hover:text-gray-900 px-2 py-1 text-sm rounded-md transition-all duration-200 font-medium" on:click={() => {
        dispatch('showDetailChartViewerCallback', {
          title: title,
          searchDuration: searchDuration,
          chartMode: chartMode,
          chartKey: chartKey,
          detailInfo: detailInfo
        });
      }}>
        <svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
        </svg>
        상세
      </button>
    </div>
  </div>
  <div class="border-0 overflow-auto p-3 rounded-b-xl bg-white/90 backdrop-blur-sm shadow-xl shadow-gray-900/10 border border-gray-200/50"
    style="width: {widthRangeValue > width ? width : widthRangeValue}px; height: {heightRangeValue > height - 40 ? height - 40 : heightRangeValue}px">
    {#if dataList.length > 0 && widthRangeValue && heightRangeValue}
      {#key isMultiLine}
        <LineChart
          lineDataList={dataList}
          {isMultiLine}
        />
      {/key}
    {:else}
      <div class="flex h-full items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg border border-gray-200/50">
        <div class="text-center space-y-2">
          <div class="w-12 h-12 bg-gray-300 rounded-2xl flex items-center justify-center mx-auto">
            <svg class="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
            </svg>
          </div>
          <p class="text-gray-600 font-medium">표시할 {title}차트가 없습니다.</p>
        </div>
      </div>
    {/if}
  </div>
</div>