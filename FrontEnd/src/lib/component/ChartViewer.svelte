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
  <div class="flex flex-row h-[30px] w-full items-center relative">
    <p class="font-bold overflow-hidden whitespace-nowrap" 
      style="width: calc(100% - 120px); text-overflow: ellipsis;" 
      title={title}>{title}</p>
    <div class="absolute right-0 flex flex-row space-x-1">
      {#if isMultiLine}
        <div class="absolute flex flex-col space-y-1 border rounded-md bg-white p-1 cursor-pointer" style="top: 0px; left: 0px"
          aria-hidden="true"
          on:click={(e) => {
            e.preventDefault();
			      e.stopPropagation(); // 이벤트 전파 중단하기

            isMultiLine = false;
          }}
        >
          <p class="font-bold">{`[${title}] (최근 ${searchDuration.month}개월)`}</p>
          <p>{@html `💲 현재 가: ${nowValue}`}</p>
          <p>{@html `🎯 현재 예측가: ${expectValue}(${setUpDownRatioTag(nowValue, expectValue)})`}</p>
          <p>{@html `🔮 한달뒤 예측가: ${afterMonthExpectValue}(${setUpDownRatioTag(nowValue, afterMonthExpectValue)})`}</p>
        </div>
      {/if}
      <button class="border-b-2 border-black px-1 text-sm" on:click={async () => {
        await addExpectStockValueToChart(searchDuration.week);
      }}>📊분석</button>
      <button class="border-b-2 border-black px-1 text-sm" on:click={() => {
        dispatch('showDetailChartViewerCallback', {
          title: title,
          searchDuration: searchDuration,
          chartMode: chartMode,
          chartKey: chartKey,
          detailInfo: detailInfo
        });
      }}>🔍상세</button>
    </div>
  </div>
  <div class="border overflow-auto p-1 rounded-lg"
    style="width: {widthRangeValue > width ? width : widthRangeValue}px; height: {heightRangeValue > height - 40 ? height - 40 : heightRangeValue}px">
    {#if dataList.length > 0 && widthRangeValue && heightRangeValue}
      {#key isMultiLine}
        <LineChart
          lineDataList={dataList}
          {isMultiLine}
        />
      {/key}
    {:else}
      <p class="flex h-full items-center justify-center">표시할 {title}차트가 없습니다.</p>
    {/if}
  </div>
</div>