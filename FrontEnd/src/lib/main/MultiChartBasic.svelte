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

    keys.forEach(key => localStorage.removeItem(key));
    localStorage.setItem(`${todayDate}chartModeObject`, JSON.stringify(chartModeObject));
  }

</script>

<div class="flex flex-col space-y-2 p-2 w-full h-full scrollbar-thin-custom">
  <div class="flex flex-col w-full space-y-2 {isProgress ? 'disabledComponent' : ''}">
    <!-- 그래프로 표시할 종목들 -->
    <div class="flex flex-wrap h-[75px] border border-white/20 rounded-xl overflow-auto px-2 py-1 bg-white/10 backdrop-blur-md scrollbar-thin-custom shadow-lg">
      {#each Object.keys(chartModeObject) as chartMode}
        {#if !!chartModeObject[chartMode]?.detailInfo}
          <!-- 기업 종목 (삭제 가능) -->
          <button class="border-0 h-[30px] rounded-lg px-3 mr-2 my-0.5 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white relative transition-all duration-200 shadow-md hover:shadow-lg font-medium text-sm border border-purple-300/30" on:click={async () => {
            chartModeObject[chartMode].dataList = await getFinanceDataListByChartMode(chartModeObject[chartMode].key, searchDuration.month, true);
            chartModeObject[chartMode].newsInfoList = await getNewInfoList(chartMode+'지수', 20, 1);

            const todayDate = new Date().toISOString().slice(0, 10);
            const keys = Object.keys(window.localStorage).filter((key) => key.includes('chartModeObject'));

            keys.forEach(key => localStorage.removeItem(key));
            localStorage.setItem(`${todayDate}chartModeObject`, JSON.stringify(chartModeObject));
          }}>{chartModeObject[chartMode].name}
            <button class="absolute -top-1 -right-1 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 border-0 rounded-full w-[16px] h-[16px] flex items-center justify-center text-white text-xs transition-all duration-200 shadow-md hover:shadow-lg"
              on:click|capture|preventDefault|stopPropagation={() => {
                delete chartModeObject[chartMode];

                chartModeObject = chartModeObject;
              }}
            >
              <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </button>
        {:else}
          <!-- 지수 종목 (기본 종목) -->
          <button class="border-0 h-[30px] rounded-lg px-3 mr-2 my-0.5 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white relative transition-all duration-200 shadow-md hover:shadow-lg font-medium text-sm" on:click={async () => {
            chartModeObject[chartMode].dataList = await getFinanceDataListByChartMode(chartModeObject[chartMode].key, searchDuration.month, true);
            chartModeObject[chartMode].newsInfoList = await getNewInfoList(chartMode+'지수', 20, 1);

            const todayDate = new Date().toISOString().slice(0, 10);
            const keys = Object.keys(window.localStorage).filter((key) => key.includes('chartModeObject'));

            keys.forEach(key => localStorage.removeItem(key));
            localStorage.setItem(`${todayDate}chartModeObject`, JSON.stringify(chartModeObject));
          }}>{chartModeObject[chartMode].name}
          </button>
        {/if}
      {/each}
      <button class="flex border-0 h-[30px] bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 rounded-lg items-center px-3 mr-2 my-0.5 text-white font-medium text-sm transition-all duration-200 shadow-md hover:shadow-lg" on:click={async() => {
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
        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
        </svg>
        추가
      </button>
    </div>
    <div class="flex flex-row space-x-2">
      <!-- 분할모드 -->
      <div class="flex w-auto space-x-1 items-center">
        <p class="font-bold mr-2 text-white flex items-center">
          <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z"></path>
          </svg>
          보기 모드
        </p>
        {#each Object.keys(displayModeObject) as displayMode}
          <button class="border-0 h-[30px] rounded-lg px-3 transition-all duration-200 font-medium text-sm {nowDisplayMode === displayModeObject[displayMode] ? 'bg-white text-gray-800 shadow-lg' : 'bg-white/20 backdrop-blur-sm text-white hover:bg-white/30 shadow-md'}" on:click={() => {
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
        <p class="font-bold mr-2 text-white flex items-center">
          <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
          </svg>
          조회 기간
        </p>
        {#each Object.keys(durationObject) as duration}
          <button disabled={isProgress} class="border-0 h-[30px] rounded-lg px-3 transition-all duration-200 font-medium text-sm disabled:opacity-50 {searchDuration === durationObject[duration] ? 'bg-white text-gray-800 shadow-lg' : 'bg-white/20 backdrop-blur-sm text-white hover:bg-white/30 shadow-md'}" on:click={async () => {
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
        <div class="flex flex-row p-2 mr-2 mb-2 rounded-2xl bg-white/95 backdrop-blur-lg relative shadow-xl hover:shadow-2xl transition-all duration-300 border border-gray-200/50 hover:border-gray-300/70 group">
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
            <button class="flex absolute top-2 right-2 w-7 h-7 justify-center items-center bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 rounded-full shadow-lg hover:shadow-xl transition-all duration-200 group-hover:scale-110 border border-red-300/50"
              on:click|capture|preventDefault|stopPropagation={() => {
                delete chartModeObject[chartMode];

                chartModeObject = chartModeObject;
              }}
            >
              <svg class="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
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