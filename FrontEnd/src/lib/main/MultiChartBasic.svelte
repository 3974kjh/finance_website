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
		'S&P500'			: {name: 'S&P500', key: 'US500', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
		'나스닥'			 : {name: '나스닥', key: 'IXIC', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
    '다우존스'		 : {name: '다우존스', key: 'DJI', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
		'코스피'			 : {name: '코스피', key: 'KS11', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
    '코스닥'			 : {name: '코스닥', key: 'KQ11', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
    '상해'			   : {name: '상해', key: 'SSEC', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
    '항셍'			   : {name: '항셍', key: 'HSI', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
    '닛케이'			 : {name: '닛케이', key: 'N225', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
    '영국'			   : {name: '영국', key: 'FTSE', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
    '프랑스'			 : {name: '프랑스', key: 'FCHI', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
    '독일'			   : {name: '독일', key: 'GDAXI', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
    '비트코인'		 : {name: '비트코인', key: 'BTC/USD', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
    'VIX'					: {name: 'VIX', key: 'VIX', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
		'달러'			   : {name: '달러', key: 'USD/KRW', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
		'달러인덱스' 	 : {name: '달러인덱스', key: '^NYICDX', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
		'미국5년채권'	 : {name: '미국5년채권', key: 'US5YT', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
		'미국10년채권' : {name: '미국10년채권', key: 'US10YT', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
		'미국30년채권' : {name: '미국30년채권', key: 'US30YT', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
		'금'				  : {name: '금', key: 'GC=F', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
		'WTI원유'		  : {name: 'WTI원유', key: 'CL=F', dataList: [], detailInfo: null, newsInfoList: [], isLoading: false, lastUpdated: null, isMultiLine: false, analysisData: null},
	}

  let isProgress: boolean = true;

  let count: number = -1;

  let axiosController: any = null;

  // 각 종목별 독립적인 업데이트 카운터
  let updateCounters: { [key: string]: number } = {};

  // 개별 종목 업데이트 카운터 증가 함수
  const incrementUpdateCounter = (chartMode: string) => {
    if (!updateCounters[chartMode]) {
      updateCounters[chartMode] = 0;
    }
    updateCounters[chartMode]++;
    updateCounters = { ...updateCounters }; // 해당 차트만 리렌더링
  };

  // 개별 종목 업데이트 함수
  const updateSingleChartMode = async (chartMode: string) => {
    if (chartModeObject[chartMode].isLoading) {
      return; // 이미 로딩 중이면 중복 요청 방지
    }

    // 로딩 상태 시작 - 개별 속성만 업데이트
    chartModeObject[chartMode].isLoading = true;
    incrementUpdateCounter(chartMode); // 로딩 상태 변경을 위한 리렌더링

    try {
      // 병렬로 데이터 가져오기
      const [financeData, newsData] = await Promise.all([
        getFinanceDataListByChartMode(chartModeObject[chartMode].key, searchDuration.month, true),
        getNewInfoList(chartMode + '지수', 20, 1)
      ]);

      // 데이터 업데이트 - 개별 속성만 업데이트
      chartModeObject[chartMode].dataList = financeData;
      chartModeObject[chartMode].newsInfoList = newsData;
      chartModeObject[chartMode].lastUpdated = new Date();
      
      console.log(`✅ Updated data for: ${chartMode}`);
      
      // 로컬스토리지 업데이트 (개별 종목만)
      updateLocalStorage();
      
    } catch (error) {
      console.error(`❌ Failed to update data for ${chartMode}:`, error);
    } finally {
      // 로딩 상태 종료 - 개별 속성만 업데이트
      chartModeObject[chartMode].isLoading = false;
      incrementUpdateCounter(chartMode); // 데이터 변경을 위한 리렌더링
    }
  };

  // 로컬스토리지 업데이트 함수
  const updateLocalStorage = () => {
    const todayDate = new Date().toISOString().slice(0, 10);
    const keys = Object.keys(window.localStorage).filter((key) => key.includes('chartModeObject'));

    // 기존 캐시 정리 (오늘 날짜가 아닌 것만)
    keys.forEach(key => {
      if (!key.includes(todayDate)) {
        localStorage.removeItem(key);
      }
    });

    // 새 데이터 저장
    try {
      localStorage.setItem(`${todayDate}chartModeObject`, JSON.stringify(chartModeObject));
    } catch (error) {
      console.error('캐시 저장 실패:', error);
    }
  };

	onMount(async() => {
    if (!!!localStorage) {
      return;
    }

    isProgress = true;

    const todayDate = new Date().toISOString().slice(0, 10);
    const keys = Object.keys(window.localStorage).filter((key) => key.includes('chartModeObject'));

    if (keys.filter((key) => key.includes(todayDate)).length > 0) {
      const getChartModeObject = localStorage.getItem(`${todayDate}chartModeObject`);
      if (getChartModeObject) {
        const cachedData = JSON.parse(getChartModeObject);
        // 캐시된 데이터를 현재 구조에 맞게 마이그레이션
        Object.keys(cachedData).forEach(key => {
          if (chartModeObject[key]) {
            // 기존 종목 업데이트
            chartModeObject[key] = {
              ...chartModeObject[key],
              ...cachedData[key],
              isLoading: false,
              lastUpdated: cachedData[key].lastUpdated ? new Date(cachedData[key].lastUpdated) : null,
              isMultiLine: cachedData[key].isMultiLine || false,
              analysisData: cachedData[key].analysisData || null
            };
          } else {
            // 새로 추가된 종목 복원
            chartModeObject[key] = {
              ...cachedData[key],
              isLoading: false,
              lastUpdated: cachedData[key].lastUpdated ? new Date(cachedData[key].lastUpdated) : null,
              isMultiLine: cachedData[key].isMultiLine || false,
              analysisData: cachedData[key].analysisData || null
            };
          }
          // 업데이트 카운터 초기화
          updateCounters[key] = 0;
        });
      }
    } else if (keys.length > 0) {
      const getChartModeObject = localStorage.getItem(keys[0]);
      if (getChartModeObject) {
        const cachedData = JSON.parse(getChartModeObject);
        Object.keys(cachedData).forEach(key => {
          if (chartModeObject[key]) {
            // 기존 종목 업데이트
            chartModeObject[key] = {
              ...chartModeObject[key],
              ...cachedData[key],
              isLoading: false,
              lastUpdated: cachedData[key].lastUpdated ? new Date(cachedData[key].lastUpdated) : null,
              isMultiLine: cachedData[key].isMultiLine || false,
              analysisData: cachedData[key].analysisData || null
            };
          } else {
            // 새로 추가된 종목 복원
            chartModeObject[key] = {
              ...cachedData[key],
              isLoading: false,
              lastUpdated: cachedData[key].lastUpdated ? new Date(cachedData[key].lastUpdated) : null,
              isMultiLine: cachedData[key].isMultiLine || false,
              analysisData: cachedData[key].analysisData || null
            };
          }
          // 업데이트 카운터 초기화
          updateCounters[key] = 0;
        });
      }
      await refreshAllFinanceDataList(Object.keys(chartModeObject), searchDuration.month);
    } else {
      await refreshAllFinanceDataList(Object.keys(chartModeObject), searchDuration.month);
    }

    // 모든 종목의 업데이트 카운터 초기화
    Object.keys(chartModeObject).forEach(key => {
      updateCounters[key] = 0;
    });
    updateCounters = { ...updateCounters };

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

    // 🚀 배치 처리로 최적화 - 동시에 최대 4개씩만 요청
    const batchSize = 4;
    const batches = [];
    
    for (let i = 0; i < chartModeList.length; i += batchSize) {
      batches.push(chartModeList.slice(i, i + batchSize));
    }

    for (const batch of batches) {
      // 배치 내 요청들을 병렬로 처리
      const batchPromises = batch.map(async (chartMode: string) => {
        try {
          // 로딩 상태 설정
          chartModeObject[chartMode].isLoading = true;
          incrementUpdateCounter(chartMode); // 로딩 상태 변경을 위한 리렌더링
          
          // 주가 데이터와 뉴스 데이터를 병렬로 가져오기
          const [financeData, newsData] = await Promise.all([
            getFinanceDataListByChartMode(chartModeObject[chartMode].key, month, true, axiosController),
            getNewInfoList(chartMode+'지수', 20, 1)
          ]);
          
          chartModeObject[chartMode].dataList = financeData;
          chartModeObject[chartMode].newsInfoList = newsData;
          chartModeObject[chartMode].lastUpdated = new Date();
          chartModeObject[chartMode].isLoading = false;
          
          count += 1;
          console.log(`🎯 Loaded data for: ${chartMode}`);
          
          incrementUpdateCounter(chartMode); // 데이터 변경을 위한 리렌더링
        } catch (error) {
          console.error(`❌ Failed to load data for ${chartMode}:`, error);
          chartModeObject[chartMode].isLoading = false;
          incrementUpdateCounter(chartMode); // 에러 상태 변경을 위한 리렌더링
        }
      });
      
      // 배치 내 모든 요청 완료 대기
      await Promise.all(batchPromises);
      
      // 배치 간 간격 (ngrok 제한 고려)
      if (batches.indexOf(batch) < batches.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 300)); // 300ms 대기
      }
    }

    isProgress = false;

    // 캐시 저장 최적화
    const todayDate = new Date().toISOString().slice(0, 10);
    const keys = Object.keys(window.localStorage).filter((key) => key.includes('chartModeObject'));

    // 기존 캐시 정리 (메모리 절약)
    keys.forEach(key => {
      if (!key.includes(todayDate)) {
        localStorage.removeItem(key);
      }
    });
    
    // 새 데이터 저장
    try {
      localStorage.setItem(`${todayDate}chartModeObject`, JSON.stringify(chartModeObject));
      console.log(`💾 Chart data cached for: ${todayDate}`);
    } catch (error) {
      console.error('캐시 저장 실패:', error);
      // 용량 부족 시 가장 오래된 캐시 삭제 후 재시도
      if (keys.length > 0) {
        localStorage.removeItem(keys[0]);
        try {
          localStorage.setItem(`${todayDate}chartModeObject`, JSON.stringify(chartModeObject));
        } catch (retryError) {
          console.error('캐시 재시도 실패:', retryError);
        }
      }
    }
  }

</script>

<div class="flex flex-col space-y-2 p-2 w-full h-full scrollbar-thin-custom">
  <div class="flex flex-col w-full space-y-2 {isProgress ? 'disabledComponent' : ''}">
    <!-- 그래프로 표시할 종목들 -->
    <div class="flex flex-wrap h-[75px] border border-white/20 rounded-xl overflow-auto px-2 py-1 bg-white/10 backdrop-blur-md scrollbar-thin-custom shadow-lg">
      {#each Object.keys(chartModeObject) as chartMode}
        {#if !!chartModeObject[chartMode]?.detailInfo}
          <!-- 기업 종목 (삭제 가능) -->
          <button 
            class="border-0 h-[30px] rounded-lg px-3 mr-2 my-0.5 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white relative transition-all duration-200 shadow-md hover:shadow-lg font-medium text-sm border border-purple-300/30 disabled:opacity-50 disabled:cursor-not-allowed" 
            disabled={chartModeObject[chartMode].isLoading}
            on:click={() => updateSingleChartMode(chartMode)}
          >
            {#if chartModeObject[chartMode].isLoading}
              <div class="flex items-center">
                <div class="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                <span>갱신중...</span>
              </div>
            {:else}
              {chartModeObject[chartMode].name}
              {#if chartModeObject[chartMode].lastUpdated}
                <span class="text-xs opacity-75 ml-1">
                  {chartModeObject[chartMode].lastUpdated.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                </span>
              {/if}
            {/if}
            <button class="absolute -top-1 -right-1 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 border-0 rounded-full w-[16px] h-[16px] flex items-center justify-center text-white text-xs transition-all duration-200 shadow-md hover:shadow-lg"
              on:click|capture|preventDefault|stopPropagation={() => {
                delete chartModeObject[chartMode];
                delete updateCounters[chartMode];
                updateCounters = { ...updateCounters };
                updateLocalStorage();
              }}
            >
              <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </button>
        {:else}
          <!-- 지수 종목 (기본 종목) -->
          <button 
            class="border-0 h-[30px] rounded-lg px-3 mr-2 my-0.5 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white relative transition-all duration-200 shadow-md hover:shadow-lg font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed" 
            disabled={chartModeObject[chartMode].isLoading}
            on:click={() => updateSingleChartMode(chartMode)}
          >
            {#if chartModeObject[chartMode].isLoading}
              <div class="flex items-center">
                <div class="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                <span>갱신중...</span>
              </div>
            {:else}
              {chartModeObject[chartMode].name}
              {#if chartModeObject[chartMode].lastUpdated}
                <span class="text-xs opacity-75 ml-1">
                  {chartModeObject[chartMode].lastUpdated.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                </span>
              {/if}
            {/if}
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
            newsInfoList: [],
            isLoading: false,
            lastUpdated: null,
            isMultiLine: false,
            analysisData: null
          }
          
          // 새로운 종목의 업데이트 카운터 초기화
          updateCounters[choiceStockInfo.name] = 0;
        }
        
        // 새로 추가된 종목들의 데이터 로드
        updateCounters = { ...updateCounters };
        updateLocalStorage();
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
      disabled={true}
    >
      {#each Object.keys(chartModeObject) as chartMode}
        <div class="flex flex-row p-2 mr-2 mb-2 rounded-2xl bg-white/95 backdrop-blur-lg relative shadow-xl hover:shadow-2xl transition-all duration-300 border border-gray-200/50 hover:border-gray-300/70 group">
          {#key updateCounters[chartMode]}
            <ChartViewer
              {searchDuration}
              {chartMode}
              title={chartModeObject[chartMode].name}
              height={fullChartViewerHeight/2 - 20}
              width={fullChartViewerWidth/2 - 20}
              chartKey={chartModeObject[chartMode].key}
              dataList={chartModeObject[chartMode].dataList}
              detailInfo={chartModeObject[chartMode].detailInfo}
              isMultiLine={chartModeObject[chartMode].isMultiLine}
              analysisData={chartModeObject[chartMode].analysisData}
              {widthRangeValue}
              {heightRangeValue}
              on:updateDataListCallback={(e) => {
                chartModeObject[e.detail.chartMode].dataList = e.detail.dataList;
                // 분석 기능 시 isMultiLine 상태와 분석 데이터도 업데이트
                if (e.detail.isMultiLine !== undefined) {
                  chartModeObject[e.detail.chartMode].isMultiLine = e.detail.isMultiLine;
                }
                if (e.detail.analysisData !== undefined) {
                  chartModeObject[e.detail.chartMode].analysisData = e.detail.analysisData;
                }
                // 분석 데이터 업데이트 시에만 해당 차트만 리렌더링
                incrementUpdateCounter(e.detail.chartMode);
              }}
              on:updateMultiLineCallback={(e) => {
                chartModeObject[e.detail.chartMode].isMultiLine = e.detail.isMultiLine;
                incrementUpdateCounter(e.detail.chartMode);
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
                delete updateCounters[chartMode];
                updateCounters = { ...updateCounters };
                updateLocalStorage();
              }}
            >
              <svg class="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          {/if}
          
          <!-- 개별 종목 로딩 상태 표시 -->
          {#if chartModeObject[chartMode].isLoading}
            <div class="absolute inset-0 bg-black/20 backdrop-blur-sm rounded-2xl flex items-center justify-center">
              <div class="bg-white/90 rounded-lg p-3 shadow-lg">
                <div class="flex items-center space-x-2">
                  <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span class="text-sm font-medium text-gray-700">데이터 갱신 중...</span>
                </div>
              </div>
            </div>
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

  /* 현대적이고 세련된 스크롤바 스타일 */
  .scrollbar-thin-custom {
    scrollbar-width: thin;
    scrollbar-color: rgba(148, 163, 184, 0.6) transparent;
  }

  /* Webkit 브라우저용 스크롤바 */
  .scrollbar-thin-custom::-webkit-scrollbar {
    width: 8px;
    height: 8px;
    background: transparent;
  }

  .scrollbar-thin-custom::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    margin: 4px;
  }

  .scrollbar-thin-custom::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, 
      rgba(99, 102, 241, 0.8) 0%, 
      rgba(139, 92, 246, 0.8) 50%, 
      rgba(168, 85, 247, 0.8) 100%);
    border-radius: 10px;
    border: 2px solid transparent;
    background-clip: content-box;
    transition: all 0.3s ease;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }

  .scrollbar-thin-custom::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, 
      rgba(79, 70, 229, 0.9) 0%, 
      rgba(124, 58, 237, 0.9) 50%, 
      rgba(147, 51, 234, 0.9) 100%);
    transform: scale(1.1);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  }

  .scrollbar-thin-custom::-webkit-scrollbar-thumb:active {
    background: linear-gradient(135deg, 
      rgba(67, 56, 202, 1) 0%, 
      rgba(109, 40, 217, 1) 50%, 
      rgba(126, 34, 206, 1) 100%);
    transform: scale(0.95);
  }

  .scrollbar-thin-custom::-webkit-scrollbar-corner {
    background: transparent;
  }

  /* 호버 시 트랙 강조 효과 */
  .scrollbar-thin-custom:hover::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(4px);
  }

  /* 부드러운 페이드 인/아웃 효과 */
  .scrollbar-thin-custom::-webkit-scrollbar-thumb {
    opacity: 0.7;
  }

  .scrollbar-thin-custom:hover::-webkit-scrollbar-thumb {
    opacity: 1;
  }

  /* 다크모드 대응 */
  @media (prefers-color-scheme: dark) {
    .scrollbar-thin-custom::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.2);
    }
    
    .scrollbar-thin-custom:hover::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.3);
    }
  }

  /* 모바일 터치 디바이스용 최적화 */
  @media (pointer: coarse) {
    .scrollbar-thin-custom::-webkit-scrollbar {
      width: 12px;
      height: 12px;
    }
    
    .scrollbar-thin-custom::-webkit-scrollbar-thumb {
      border: 3px solid transparent;
    }
  }
</style>