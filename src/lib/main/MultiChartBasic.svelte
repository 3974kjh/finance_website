<script lang="ts">
	import { ChartViewer, RangeBar, ProgressCircle, NewsInfoListComponent, DownLoadProgressBar } from '$lib/component';
	import { SortableList } from '$lib/sortableList';
	import { onMount, onDestroy, tick, createEventDispatcher } from 'svelte';
  import { getFinanceDataListByChartMode, getNewInfoList } from '$lib/main';
	import { createComponent } from '$lib/utils/CommonHelper';
	import { StockListPopup } from '$lib/popup';
  import { cancelRequest } from "$lib/axios-provider/AxiosProvider";

  export let fullChartViewerWidth: number = 0;
	export let fullChartViewerHeight: number = 0;

  const dispatch = createEventDispatcher();

  let widthRangeValue: number = 0;
	let heightRangeValue: number = 0;

  let durationObject: any = {
    '2 YEAR': {month: 24, week: 104},
    '1 YEAR': {month: 12, week: 52},
    '6 MONTH': {month: 6, week: 26}
  }

  /**
   * 검색 조회 기간
  */
  let searchDuration: any = durationObject['1 YEAR'];

  let refreshFlag: boolean = false;

  let displayModeObject: any = {
    '2×1': {row: 2, col: 2},
    '2×2': {row: 2, col: 4},
    '3×2': {row: 3, col: 4},
    '4×2': {row: 4, col: 4},
    '5×4': {row: 5, col: 8},
  }

  /**
   * 분할 초기 값
   */
  let nowDisplayMode: any = displayModeObject['5×4'];

	let chartModeObject: any = {
		'S&P500'			: {name: 'S&P500', key: 'US500', dataList: [], detailInfo: null, newsInfoList: []},
		'나스닥'			 : {name: '나스닥', key: 'IXIC', dataList: [], detailInfo: null, newsInfoList: []},
    '다우존스'		 : {name: '다우존스', key: 'DJI', dataList: [], detailInfo: null, newsInfoList: []},
		'코스피'			 : {name: '코스피', key: 'KS11', dataList: [], detailInfo: null, newsInfoList: []},
    '코스닥'			 : {name: '코스닥', key: 'KQ11', dataList: [], detailInfo: null, newsInfoList: []},
    '상해'			   : {name: '상해', key: 'SSEC', dataList: [], detailInfo: null, newsInfoList: []},
    '항셍'			   : {name: '항셍', key: 'HSI', dataList: [], detailInfo: null, newsInfoList: []},
    '닛케이'			 : {name: '닛케이', key: 'N225', dataList: [], detailInfo: null, newsInfoList: []},
    '영국'			   : {name: '영국', key: 'FTSE', dataList: [], detailInfo: null, newsInfoList: []},
    '프랑스'			 : {name: '프랑스', key: 'FCHI', dataList: [], detailInfo: null, newsInfoList: []},
    '독일'			   : {name: '독일', key: 'GDAXI', dataList: [], detailInfo: null, newsInfoList: []},
    '비트코인'		 : {name: '비트코인', key: 'BTC/USD', dataList: [], detailInfo: null, newsInfoList: []},
    'VIX'					: {name: 'VIX', key: 'VIX', dataList: [], detailInfo: null, newsInfoList: []},
		'달러'			   : {name: '달러', key: 'USD/KRW', dataList: [], detailInfo: null, newsInfoList: []},
		'달러인덱스' 	 : {name: '달러인덱스', key: '^NYICDX', dataList: [], detailInfo: null, newsInfoList: []},
		'미국5년채권'	 : {name: '미국5년채권', key: 'US5YT', dataList: [], detailInfo: null, newsInfoList: []},
		'미국10년채권' : {name: '미국10년채권', key: 'US10YT', dataList: [], detailInfo: null, newsInfoList: []},
		'미국30년채권' : {name: '미국30년채권', key: 'US30YT', dataList: [], detailInfo: null, newsInfoList: []},
		'금'				  : {name: '금', key: 'GC=F', dataList: [], detailInfo: null, newsInfoList: []},
		'WTI원유'		  : {name: 'WTI원유', key: 'CL=F', dataList: [], detailInfo: null, newsInfoList: []},
	}

  let isProgress: boolean = true;

  let count: number = -1;

  let axiosController: any = null;

	onMount(async() => {
    if (!!!localStorage) {
      return;
    }

    isProgress = true;

    const todayDate = new Date().toISOString().slice(0, 10);
    const keys = Object.keys(window.localStorage).filter((key) => key.includes('chartModeObject'));

    if (keys.filter((key) => key.includes(todayDate)).length > 0) {
      const getChartModeObject = localStorage.getItem(`${todayDate}chartModeObject`);
      chartModeObject = !!getChartModeObject ? JSON.parse(getChartModeObject) : chartModeObject;
    } else if (keys.length > 0) {
      const getChartModeObject = localStorage.getItem(keys[0]);
      chartModeObject = !!getChartModeObject ? JSON.parse(getChartModeObject) : chartModeObject;
      await refreshAllFinanceDataList(Object.keys(chartModeObject), searchDuration.month);
    } else {
      await refreshAllFinanceDataList(Object.keys(chartModeObject), searchDuration.month);
    }

    isProgress = false;

    await tick();

    heightRangeValue = Math.round((fullChartViewerHeight - 300) / nowDisplayMode.row) - (nowDisplayMode.row * 5);
    widthRangeValue = Math.round((fullChartViewerWidth - 50) / nowDisplayMode.col) - 15;
	});

  onDestroy(() => {
    if (typeof document !== 'undefined') {
      cancelRequest(axiosController);
    }
  })

  /**
   * 전체 주가 데이터 값 갱신
  */
  const refreshAllFinanceDataList = async (chartModeList: any, month: number) => {
    axiosController = new AbortController();

    count = 0;
    isProgress = true;

    for (let chartMode of chartModeList) {
      count += 1;
      chartModeObject[chartMode].dataList = await getFinanceDataListByChartMode(chartModeObject[chartMode].key, month, true, axiosController);
      chartModeObject[chartMode].newsInfoList = await getNewInfoList(chartMode+'지수', 20, 1);
    }

    refreshFlag = !refreshFlag;

    isProgress = false;

    const todayDate = new Date().toISOString().slice(0, 10);
    const keys = Object.keys(window.localStorage).filter((key) => key.includes('chartModeObject'));

    localStorage.removeItem(keys);
    localStorage.setItem(`${todayDate}chartModeObject`, JSON.stringify(chartModeObject));
  }

</script>

<div class="flex flex-col space-y-2 p-2 w-full h-full scrollbar-thin-custom">
  <div class="flex flex-col w-full space-y-2 {isProgress ? 'disabledComponent' : ''}">
    <!-- 그래프로 표시할 종목들 -->
    <div class="flex flex-wrap h-[75px] border rounded-md overflow-auto px-1 py-0.5 bg-gray-50 scrollbar-thin-custom">
      {#each Object.keys(chartModeObject) as chartMode}
        <button class="border-white h-[30px] rounded-md px-2 mr-1 my-0.5 bg-gray-600 text-white relative" on:click={async () => {
          chartModeObject[chartMode].dataList = await getFinanceDataListByChartMode(chartModeObject[chartMode].key, searchDuration.month, true);
          chartModeObject[chartMode].newsInfoList = await getNewInfoList(chartMode+'지수', 20, 1);

          const todayDate = new Date().toISOString().slice(0, 10);
          const keys = Object.keys(window.localStorage).filter((key) => key.includes('chartModeObject'));

          localStorage.removeItem(keys);
          localStorage.setItem(`${todayDate}chartModeObject`, JSON.stringify(chartModeObject));
        }}>{chartModeObject[chartMode].name}
          {#if !!chartModeObject[chartMode]?.detailInfo}
            <button class="absolute top-[-5px] right-[-5px] bg-red-400 border rounded-full w-[15px] h-[15px]"
              on:click|capture|preventDefault|stopPropagation={() => {
                delete chartModeObject[chartMode];

                chartModeObject = chartModeObject;
              }}
            />
          {/if}
        </button>
      {/each}
      <button class="flex border h-[30px] bg-gray-600 border-black rounded-md items-center px-1 mr-1 my-0.5" on:click={async() => {
        const popupResult = await createComponent(StockListPopup, {
          titleName: '주식 목록 조회'
        });
    
        if (popupResult.isSave === false) {
          return;
        }
    
        for (let choiceStockInfo of popupResult.choiceStockInfoList) {
          if (choiceStockInfo.name in Object.keys(chartModeObject)) {
            continue;
          }
          
          chartModeObject[choiceStockInfo.name] = { 
            name: choiceStockInfo.name,
            key: choiceStockInfo.value,
            detailInfo: choiceStockInfo,
            dataList: [],
            newsInfoList: []
          }
        }
      }}>
        ➕
      </button>
    </div>
    <div class="flex flex-row space-x-2">
      <!-- 분할모드 -->
      <div class="flex w-auto space-x-1 items-center">
        <p class="font-bold mr-2 text-white">{'✖ 보기 모드'}</p>
        {#each Object.keys(displayModeObject) as displayMode}
          <button class="border h-[30px] rounded-md px-2 border-gray-400 {nowDisplayMode === displayModeObject[displayMode] ?  'bg-white' : 'bg-gray-500 text-white'}" on:click={() => {
            nowDisplayMode = displayModeObject[displayMode];

            heightRangeValue = Math.round((fullChartViewerHeight - 300) / displayModeObject[displayMode].row) - (displayModeObject[displayMode].row * 5);
            widthRangeValue = Math.round((fullChartViewerWidth - 50) / displayModeObject[displayMode].col) - 15;
          }}>{displayMode}</button>
        {/each}
      </div>
      <!-- 수동 선택 -->
      <div class="flex w-auto space-x-2 items-center text-white">
        <RangeBar
          bind:value={widthRangeValue}
        />
        <RangeBar
          min={200}
          max={1500}
          bind:value={heightRangeValue}
        />
      </div>
      <!-- 조회 기간 설정 -->
      <div class="flex grow space-x-1 items-center justify-end">
        <p class="font-bold mr-2 text-white">{'📆 조회 기간'}</p>
        {#each Object.keys(durationObject) as duration}
          <button disabled={isProgress} class="border h-[30px] rounded-md px-2 border-gray-400 {searchDuration === durationObject[duration] ?  'bg-white' : 'bg-gray-500 text-white'}" on:click={async () => {
            searchDuration = durationObject[duration];

            await refreshAllFinanceDataList(Object.keys(chartModeObject), searchDuration.month);
          }}>{duration}</button>
        {/each}
      </div>
    </div>
  </div>
  {#if isProgress}
    {#if count < 0}
      <div class="flex w-full h-full justify-center items-center">
        <ProgressCircle
          size={100}
          thickness={10}
          isLarge={true}
          isTextBlack={false}
          text={'오늘 증시 및 주식 데이터를 가져옵니다.'}
        />
      </div>
    {:else}
      <div class="flex flex-col w-full h-full justify-center items-center font-bold text-white">
        <p>{Object.keys(chartModeObject).length}개의 증시 및 주식 데이터 조회중입니다.</p>
        <DownLoadProgressBar
          min={0}
          max={Object.keys(chartModeObject).length}
          nowCount={count}
        />
      </div>
    {/if}
  {:else}
    <SortableList
      id="chart-viewer"
      class="list-group flex flex-wrap overflow-auto"
      animation={150}
      disabled={false}
    >
      {#each Object.keys(chartModeObject) as chartMode}
        <div class="flex flex-row p-2 border mr-1 mb-1 rounded-md bg-white relative">
          {#key refreshFlag}
            <ChartViewer
              {searchDuration}
              {chartMode}
              title={chartModeObject[chartMode].name}
              height={fullChartViewerHeight/2 - 20}
              width={fullChartViewerWidth/2 - 20}
              chartKey={chartModeObject[chartMode].key}
              dataList={chartModeObject[chartMode].dataList}
              detailInfo={chartModeObject[chartMode].detailInfo}
              {widthRangeValue}
              {heightRangeValue}
              on:updateDataListCallback={(e) => {
                chartModeObject[e.detail.chartMode].dataList = e.detail.dataList;
              }}
              on:showDetailChartViewerCallback={(e) => {
                dispatch('showDetailChartViewerCallback', e.detail);
              }}
            />
          {/key}
          <!-- 뉴스 정보 -->
          <div class="flex flex-col"
            style="width: {widthRangeValue}px; height: {heightRangeValue + 30}px">
            <NewsInfoListComponent
              bind:newInfoList={chartModeObject[chartMode].newsInfoList}
            />
          </div>
          {#if !!chartModeObject[chartMode]?.detailInfo}
            <button class="flex absolute top-[2px] right-[2px] w-[30px] h-[30px] justify-center items-center border border-red-400 rounded-full bg-white"
              on:click|capture|preventDefault|stopPropagation={() => {
                delete chartModeObject[chartMode];

                chartModeObject = chartModeObject;
              }}
            >{'❌'}</button>
          {/if}
        </div>
      {/each}
    </SortableList>
  {/if}
</div>

<style>
	.disabledComponent {
		pointer-events: none;
		opacity: 0.5;
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