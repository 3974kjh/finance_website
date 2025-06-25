<script lang="ts">
  import { getFinanceStockList } from '$lib/api-connector/FinanceApi';
  import { CommonPopup, ProgressCircle } from '$lib/component';
  import { onMount, tick } from 'svelte';
  import type { StockType } from '$lib/types';
  import { setUpDownIcon, setUpDownColor } from '$lib/main';
  import { calculateRatio, sortBySimilarity, formatCostValue, formatIncludeComma } from '$lib/utils/CommonHelper';

  export let titleName: string = '';
  export let close: (value: any) => void;
  export let isSingleMode: boolean = false;

  // 주식 목록
	let originalStockData: StockType[] = []; // 원본 데이터 (변경되지 않음)
	let originStockInfoList: StockType[] = []; // 표시용 데이터 (정렬/필터링 적용)

  // 표시할 주식 목록
	let filteredStockInfoList: StockType[] = [];

  // 검색한 주식 코드/명
  let searchStockText: string = '';

  // 선택한 주식 목록
  let choiceStockInfoList: Array<{
    name: string, 
    value: string,
    code: string,
    close: any,
    chagesRatio: any,
    open: any,
    high: any,
    low: any,
    volume: any,
    marcap: any,
    amount: any
  }> = [];

  // 로딩 유무
  let isProgress: boolean = false;

  // 동적 높이 관련 변수들
  let popupHeight: number = 600; // 기본값을 더 작게 설정
  let innerHeight: number = 0;

  // 테이블 페이지네이션
  let currentPage: number = 0;
  const itemsPerPage: number = 50; // 페이지당 50개 항목

  // 정렬 상태 관리
  let sortState = {
    chagesRatio: 'none', // 'none' | 'asc' | 'desc'
    volumeRatio: 'none'  // 'none' | 'asc' | 'desc'
  };

  let stockModeList: Array<{name: string, value: string, isSelected: boolean}> = [
    { name: '국내상장', value: 'KRX', isSelected: true },
    { name: '나스닥상장', value: 'NASDAQ', isSelected: false },
    { name: 'S&P500상장', value: 'S&P500', isSelected: false },
    { name: '상하이상장', value: 'SSE', isSelected: false },
    { name: '도쿄상장', value: 'TSE', isSelected: false },
  ]
  
  let searchInputDocument: HTMLInputElement;

  // 브라우저 높이에 따른 팝업 높이 계산
  $: {
    // innerHeight가 유효한 값일 때만 계산
    if (innerHeight > 200) {
      const calculatedHeight = Math.floor(innerHeight * 0.8); // 80%로 더 보수적으로 계산
      popupHeight = Math.min(Math.max(400, calculatedHeight), 800); // 최소 400px, 최대 800px로 더 작게 조정
    }
  }

  // 검색 필터링된 데이터 (실시간 검색)
  $: searchFilteredList = searchStockText.trim() === '' 
    ? originStockInfoList.map((item: any, index: number) => ({ ...item, originalIndex: index }))
    : originStockInfoList
        .map((item: any, index: number) => ({ ...item, originalIndex: index }))
        .filter((item: any) => 
          item.Name?.toLowerCase().includes(searchStockText.toLowerCase()) || 
          item.Code?.toLowerCase().includes(searchStockText.toLowerCase()) ||
          item.Symbol?.toLowerCase().includes(searchStockText.toLowerCase())
        );

  // 페이지네이션 데이터
  $: tableData = searchFilteredList.slice(
    currentPage * itemsPerPage,
    (currentPage + 1) * itemsPerPage
  );

  // 페이지 수 계산
  $: maxPage = Math.ceil(searchFilteredList.length / itemsPerPage);

  // 검색 시 첫 페이지로 이동
  $: if (searchStockText) {
    currentPage = 0;
  }

  onMount(async () => {
    isProgress = true;
    const stockData = await setFinanceStockList(getSelectedStockModeValue(stockModeList));
    originalStockData = [...stockData]; // 원본 데이터 저장
    originStockInfoList = [...stockData]; // 표시용 데이터 초기화
    isProgress = false;

    await tick();
    searchInputDocument?.focus();
  })

  /**
   * 주식 목록 가져오기
  */
  const setFinanceStockList = async (symbol: string) => {
    const result = await getFinanceStockList({symbol: symbol});

    if (!!!result?.data || result.data.length < 1) {
      return [];
    }

    return result.data.map((item: any) => {
      return {
        ...item,
        VolumeRatio: calculateRatio(item?.Marcap, item?.Amount)
      }
    });
  }

  /**
	 * 팝업 창 종료
	 *
	 *  - 팝업 창 종료 시점에 resolve함수를 실행 시켜 fulfilled 상태로 전환
	 * 	- 이 때, true값을 resolve함수의 인자 값으로 보낸다.
	 *
	 */
	const closePopup = (requestData: any): void => {
		close(requestData);
	};

	/**
	 * dialog 닫기 버튼 클릭 시, 팝업 창 종료
	 */
	const closedDialogCallback = (): void => {
		closePopup({
			isSave: false
		});
	};

  const getSelectedStockModeValue = (list: any) => {
    const selectedStockMode = list.find((item: any) => item.isSelected);

    return selectedStockMode?.value;
  }

  const setSelectStockModeList = (list: any, stockValue: string) => {
    if (list.length < 1) {
      return [];
    }

    return list.map((item: any) => {
      if (item.value === stockValue) {
        return {
          ...item,
          isSelected: true
        }
      } else {
        return {
          ...item,
          isSelected: false
        }
      }
    })
  }

  const applyStockInfoToGraph = () => {
    closePopup({
      isSave: true,
      choiceStockInfoList: [...choiceStockInfoList]
    })
  }

  const onFocusSearchText = (e: KeyboardEvent) => {
    if (e.key === 'F4' && searchFilteredList.length > 0) {
			e.preventDefault(); // 기본 동작 막기
			e.stopPropagation(); // 이벤트 전파 중단하기
			
      searchInputDocument?.focus();
		}
  }

  // 정렬 함수들
  const sortByChagesRatio = () => {
    // 현재 상태에 따라 다음 상태 결정
    let nextState: string;
    if (sortState.chagesRatio === 'none' || sortState.chagesRatio === 'asc') {
      nextState = 'desc';
    } else {
      nextState = 'asc';
    }

    // 다른 정렬 상태 초기화
    sortState.volumeRatio = 'none';
    sortState.chagesRatio = nextState;

    // 표시용 데이터만 정렬 (원본 데이터는 보존)
    const sorted = [...originStockInfoList].sort((a: any, b: any) => {
      const aRatio = parseFloat(a?.ChagesRatio) || 0;
      const bRatio = parseFloat(b?.ChagesRatio) || 0;
      
      if (nextState === 'desc') {
        return bRatio - aRatio; // 내림차순
      } else {
        return aRatio - bRatio; // 오름차순
      }
    });
    
    // 표시용 데이터만 업데이트
    originStockInfoList = sorted;
    currentPage = 0; // 첫 페이지로 이동
  }

  const sortByVolumeRatio = () => {
    // 현재 상태에 따라 다음 상태 결정
    let nextState: string;
    if (sortState.volumeRatio === 'none' || sortState.volumeRatio === 'asc') {
      nextState = 'desc';
    } else {
      nextState = 'asc';
    }

    // 다른 정렬 상태 초기화
    sortState.chagesRatio = 'none';
    sortState.volumeRatio = nextState;

    // 표시용 데이터만 정렬 (원본 데이터는 보존)
    const sorted = [...originStockInfoList].sort((a: any, b: any) => {
      const aRatio = parseFloat(a?.VolumeRatio) || 0;
      const bRatio = parseFloat(b?.VolumeRatio) || 0;
      
      if (nextState === 'desc') {
        return bRatio - aRatio; // 내림차순
      } else {
        return aRatio - bRatio; // 오름차순
      }
    });
    
    // 표시용 데이터만 업데이트
    originStockInfoList = sorted;
    currentPage = 0; // 첫 페이지로 이동
  }

  // 정렬 상태 아이콘 반환 함수
  const getSortIcon = (sortType: string) => {
    if (sortType === 'asc') return '↑';
    if (sortType === 'desc') return '↓';
    return '⇅';
  }

  // 테이블 상단으로 스크롤
  const scrollToTableTop = () => {
    try {
      const tbody = document.querySelector('.modern-tbody');
      if (tbody) {
        tbody.scrollTop = 0;
      }
    } catch (error) {
      console.error('스크롤 에러:', error);
    }
  }

  // 실시간 검색 처리
  const handleSearchInput = async () => {
    // 검색어가 비어있으면 전체 목록 표시
    if (searchStockText.trim() === '') {
      currentPage = 0;
      return;
    }

    // 검색 결과가 있으면 첫 페이지로 이동
    if (searchFilteredList.length > 0) {
      currentPage = 0;
    }
  }

  // Enter 키 처리 (기존 검색 로직 제거하고 실시간 검색만 사용)
  const handleKeyPress = async (e: KeyboardEvent) => {
    if (e.key === 'Enter') {
      await tick();
      searchInputDocument?.focus();
    }
  }

  // 초기 상태로 되돌리기
  const resetToInitialState = async () => {
    // 검색어 초기화
    searchStockText = '';
    
    // 정렬 상태 초기화
    sortState.chagesRatio = 'none';
    sortState.volumeRatio = 'none';
    
    // 페이지 초기화
    currentPage = 0;
    
    // 원본 데이터를 표시용 데이터로 복원 (API 호출 없음)
    originStockInfoList = [...originalStockData];
    
    // 검색 입력창에 포커스
    await tick();
    searchInputDocument?.focus();
  }
</script>

<svelte:window bind:innerHeight on:keydown={onFocusSearchText}/>
<CommonPopup {titleName} modalPositionType="center" on:closedDialogCallback={closedDialogCallback}>
  <div class="flex flex-col w-[800px] bg-white overflow-hidden" style="height: {popupHeight}px;">
    <!-- 검색 영역 - 고정 높이 -->
    <div class="flex h-auto w-full mt-2 px-2 flex-shrink-0">
      <!-- 검색란 -->
      <div class="flex flex-row w-full items-center space-x-2">
        <label class="w-[100px] font-bold text-sm" for="name">🔍 종목 검색</label>
        <input
          bind:this={searchInputDocument}
          autocomplete="off"
          type="text"
          id="name"
          name="name"
          class="border flex-grow px-3 py-2 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          autofocus={true}
          disabled={isProgress}
          minlength="0"
          maxlength="20"
          size="10"
          placeholder="종목명/종목코드 실시간 검색"
          bind:value={searchStockText}
          on:input={handleSearchInput}
          on:keypress={handleKeyPress}
        />
        <button
          class="flex items-center justify-center px-3 py-2 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-md text-sm font-medium text-gray-700 transition-colors duration-200 min-w-[80px]"
          disabled={isProgress}
          on:click={resetToInitialState}
          title="검색, 정렬 상태를 초기화하고 원본 데이터를 다시 불러옵니다"
        >
          <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
          {isProgress ? '로딩중...' : '초기화'}
        </button>
      </div>
    </div>

    <!-- 검색 상태 표시 -->
    {#if searchStockText.trim() !== '' || sortState.chagesRatio !== 'none' || sortState.volumeRatio !== 'none'}
      <div class="flex justify-center py-1 px-2 flex-shrink-0">
        <div class="px-3 py-1 bg-blue-50 border border-blue-200 rounded-full text-sm text-blue-700 flex items-center space-x-2">
          {#if searchStockText.trim() !== ''}
            <span>🔍 '<span class="font-semibold">{searchStockText}</span>' 검색 중 - {searchFilteredList.length}개 결과</span>
          {/if}
          {#if sortState.chagesRatio !== 'none'}
            <span class="text-xs bg-blue-100 px-2 py-0.5 rounded">상승률 정렬</span>
          {/if}
          {#if sortState.volumeRatio !== 'none'}
            <span class="text-xs bg-blue-100 px-2 py-0.5 rounded">유동성 정렬</span>
          {/if}
          <button 
            class="text-blue-500 hover:text-blue-700 ml-2"
            on:click={resetToInitialState}
            title="초기화"
          >
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
      </div>
    {/if}

    <!-- 버튼 영역 - 고정 높이 -->
    <div class="flex flex-row h-auto w-full space-x-1 px-2 py-2 flex-shrink-0">
      {#each stockModeList as stockMode}
        <button
          class="border rounded-md px-3 py-1 border-gray-400 transition-colors duration-200 {stockMode.isSelected ? 'bg-blue-100 border-blue-400 text-blue-700 font-semibold' : 'bg-white hover:bg-gray-50'} {isProgress ? 'opacity-50 cursor-not-allowed' : ''} {isProgress && stockMode.isSelected ? 'loading-tab' : ''}"
          disabled={isProgress}
          on:click={async () => {
            // 이미 로딩 중이거나 같은 모드를 선택한 경우 무시
            if (isProgress || stockMode.isSelected) return;
            
            searchStockText = '';
            currentPage = 0;

            // 정렬 상태 초기화
            sortState.chagesRatio = 'none';
            sortState.volumeRatio = 'none';

            stockModeList = setSelectStockModeList(stockModeList, stockMode.value);

            isProgress = true;
            const stockData = await setFinanceStockList(getSelectedStockModeValue(stockModeList));
            originalStockData = [...stockData]; // 원본 데이터 저장
            originStockInfoList = [...stockData]; // 표시용 데이터 초기화
            isProgress = false;
          }}
        >
          {#if isProgress && stockMode.isSelected}
            <div class="flex items-center space-x-1 relative z-10">
              <svg class="animate-spin h-3 w-3 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>로딩중...</span>
            </div>
          {:else}
            {stockMode.name}
          {/if}
        </button>
      {/each}
    </div>

    <!-- 주식 목록 Grid - 남은 공간 모두 사용 -->
    <div class="flex w-full flex-grow px-2 min-h-0 mb-1 overflow-hidden">
      <div class="modern-table-wrap rounded-xl overflow-hidden shadow-lg bg-white/95 backdrop-blur-sm border border-gray-200/50">
        <table class="modern-table">
          <thead class="modern-thead">
            <tr>
              <th class="modern-th" style="width: 12%;">
                <div class="flex items-center justify-start">
                  <span class="text-sm font-semibold">📋 코드</span>
                </div>
              </th>
              <th class="modern-th" style="width: 28%;">
                <div class="flex items-center justify-start">
                  <span class="text-sm font-semibold">🏢 주식명</span>
                </div>
              </th>
              <th class="modern-th" style="width: 15%;">
                <div class="flex items-center justify-center">
                  <span class="text-sm font-semibold">💰 현재가</span>
                </div>
              </th>
              <th 
                class="modern-th cursor-pointer hover:bg-slate-600/90 transition-all duration-200 group" 
                on:click={sortByChagesRatio} 
                style="width: 15%;"
                title="클릭하여 정렬"
              >
                <div class="flex items-center justify-center">
                  <span class="text-sm font-semibold group-hover:scale-105 transition-transform duration-200">
                    📈 전일대비 {getSortIcon(sortState.chagesRatio)}
                  </span>
                </div>
              </th>
              <th class="modern-th" style="width: 15%;">
                <div class="flex items-center justify-center">
                  <span class="text-sm font-semibold">🌅 시초가</span>
                </div>
              </th>
              <th 
                class="modern-th cursor-pointer hover:bg-slate-600/90 transition-all duration-200 group" 
                on:click={sortByVolumeRatio} 
                style="width: 15%;"
                title="클릭하여 정렬"
              >
                <div class="flex items-center justify-center">
                  <span class="text-sm font-semibold group-hover:scale-105 transition-transform duration-200">
                    💧 유동성 {getSortIcon(sortState.volumeRatio)}
                  </span>
                </div>
              </th>
            </tr>
          </thead>
          <tbody class="modern-tbody" style="height: {Math.max(120, popupHeight - 420)}px">
            {#if searchFilteredList.length > 0 && isProgress === false}
              {#if tableData.length > 0}
                {#each tableData as stockInfo, index}
                  <tr
                    class="modern-tr group hover:bg-gradient-to-r hover:from-blue-50/80 hover:to-indigo-50/80 transition-all duration-200 cursor-pointer hover:shadow-sm"
                    on:click={() => {
                      let newStockInfo = {
                        name: stockInfo?.Name ?? '',
                        value: stockInfo?.Code ?? stockInfo?.Symbol,
                        code: stockInfo?.Code ?? stockInfo?.Symbol,
                        close: stockInfo?.Close,
                        chagesRatio: stockInfo?.ChagesRatio,
                        open: stockInfo?.Open,
                        high: stockInfo?.High,
                        low: stockInfo?.Low,
                        volume: stockInfo?.Volume,
                        marcap: stockInfo?.Marcap,
                        amount: stockInfo?.Amount
                      };

                      if (isSingleMode) {
                        choiceStockInfoList = [newStockInfo];
                      } else {
                        // 중복 제거 로직
                        const exists = choiceStockInfoList.find(item => item.code === newStockInfo.code);
                        if (!exists) {
                          choiceStockInfoList = [...choiceStockInfoList, newStockInfo];
                        }
                      }
                    }}
                  >
                    <td class="modern-td" style="width: 12%;">
                      <div class="flex items-center justify-start">
                        <span class="font-mono text-xs bg-gray-100 px-2 py-1 rounded-md group-hover:bg-blue-100 transition-colors duration-200">
                          {stockInfo?.Code ?? stockInfo?.Symbol}
                        </span>
                      </div>
                    </td>
                    <td class="modern-td" style="width: 28%;">
                      <div class="flex items-center justify-start">
                        <span class="font-medium text-gray-800 group-hover:text-blue-800 transition-colors duration-200">
                          {stockInfo?.Name}
                        </span>
                      </div>
                    </td>
                    <td class="modern-td" style="width: 15%;">
                      <div class="flex items-center justify-end">
                        <span class="font-semibold text-gray-900 group-hover:text-blue-900 transition-colors duration-200">
                          {formatIncludeComma(formatCostValue(stockInfo?.Close)) ?? '-'}<span class="text-xs text-gray-500 ml-1">₩</span>
                        </span>
                      </div>
                    </td>
                    <td class="modern-td" style="width: 15%;">
                      <div class="flex items-center justify-center">
                        <span class="font-bold text-sm px-2 py-1 rounded-md transition-all duration-200" style="color: {setUpDownColor(stockInfo?.ChagesRatio)};">
                          {setUpDownIcon(stockInfo?.ChagesRatio)} {stockInfo?.ChagesRatio ?? '-'}%
                        </span>
                      </div>
                    </td>
                    <td class="modern-td" style="width: 15%;">
                      <div class="flex items-center justify-end">
                        <span class="text-gray-700 group-hover:text-gray-900 transition-colors duration-200">
                          {formatIncludeComma(formatCostValue(stockInfo?.Open)) ?? '-'}<span class="text-xs text-gray-500 ml-1">₩</span>
                        </span>
                      </div>
                    </td>
                    <td class="modern-td" style="width: 15%;">
                      <div class="flex items-center justify-end">
                        <span class="text-gray-700 group-hover:text-indigo-700 transition-colors duration-200 font-medium">
                          {stockInfo.VolumeRatio ?? '-'}<span class="text-xs text-gray-500 ml-1">%</span>
                        </span>
                      </div>
                    </td>
                  </tr>
                {/each}
              {:else}
                <tr class="modern-tr empty-state-row">
                  <td colspan="6" class="modern-td empty-state-cell">
                    <div class="flex flex-col items-center space-y-2">
                      <svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
                      </svg>
                      <span class="font-medium text-gray-500">목록이 없습니다.</span>
                    </div>
                  </td>
                </tr>
              {/if}
            {:else if isProgress}
              <tr class="modern-tr h-full">
                <td colspan="6" class="modern-td">
                  <div class="flex items-center justify-center h-full">
                    <ProgressCircle
                      text={'해당 증시 목록을 가져오는 중입니다...'}
                    />
                  </div>
                </td>
              </tr>
            {:else}
              <tr class="modern-tr empty-state-row">
                <td colspan="6" class="modern-td empty-state-cell">
                  <div class="flex flex-col items-center space-y-2">
                    <svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6m2 5.291A7.962 7.962 0 0112 15c-2.34 0-4.291-1.004-5.824-2.412M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
                    </svg>
                    <span class="text-gray-500 font-medium">'{searchStockText}' 검색 결과가 없습니다.</span>
                  </div>
                </td>
              </tr>
            {/if}
          </tbody>
        </table>
      </div>
    </div>

    <!-- 페이지네이션 -->
    {#if searchFilteredList.length > itemsPerPage}
      <div class="flex justify-center items-center space-x-3 py-2 px-2 flex-shrink-0">
        <button 
          class="group relative w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold transition-all duration-300 transform {currentPage === 0 ? 'bg-gray-100 border-gray-300 text-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-blue-500 to-blue-600 border-blue-500 text-white hover:from-blue-600 hover:to-blue-700 hover:scale-110 hover:shadow-lg active:scale-95'}"
          disabled={currentPage === 0}
          on:click={() => {
            currentPage = Math.max(0, currentPage - 1);
            requestAnimationFrame(() => scrollToTableTop());
          }}
          title="이전 페이지"
        >
          <svg class="w-3 h-3 transition-transform duration-200 group-hover:-translate-x-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
          </svg>
        </button>
        
        <div class="flex items-center space-x-2">
          <span class="px-3 py-1 text-xs font-semibold bg-gradient-to-r from-gray-50 to-gray-100 rounded-full border-2 border-gray-200 shadow-sm">
            <span class="text-blue-600">{currentPage + 1}</span>
            <span class="text-gray-400 mx-1">/</span>
            <span class="text-gray-600">{maxPage}</span>
          </span>
          {#if searchStockText.trim() !== ''}
            <span class="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full border border-blue-200">
              검색: {searchFilteredList.length}/{originalStockData.length}
            </span>
          {:else}
            <span class="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full border border-gray-200">
              총 {searchFilteredList.length}개
            </span>
          {/if}
        </div>
        
        <button 
          class="group relative w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold transition-all duration-300 transform {currentPage >= maxPage - 1 ? 'bg-gray-100 border-gray-300 text-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-blue-500 to-blue-600 border-blue-500 text-white hover:from-blue-600 hover:to-blue-700 hover:scale-110 hover:shadow-lg active:scale-95'}"
          disabled={currentPage >= maxPage - 1}
          on:click={() => {
            currentPage = Math.min(maxPage - 1, currentPage + 1);
            requestAnimationFrame(() => scrollToTableTop());
          }}
          title="다음 페이지"
        >
          <svg class="w-3 h-3 transition-transform duration-200 group-hover:translate-x-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
    {/if}

    <!-- 선택된 항목 영역 - 최우선 보장 -->
    <div class="flex w-full min-h-[70px] flex-shrink-0 px-2 pb-2" style="height: {Math.max(70, Math.min(140, choiceStockInfoList.length * 18 + 40))}px;">
      <div class="flex flex-wrap w-full h-full border rounded-md overflow-auto p-1 bg-gray-50">
        {#if choiceStockInfoList.length === 0}
          <div class="flex items-center justify-center w-full h-full text-gray-500 text-sm">
            선택된 종목이 없습니다. 위 테이블에서 종목을 클릭하여 선택하세요.
          </div>
        {:else}
          {#each choiceStockInfoList as choiceStockInfo}
            <button
              class="border rounded-md px-3 py-1 border-blue-400 bg-blue-100 text-blue-700 h-[30px] flex-shrink-0 hover:bg-blue-200 transition-colors duration-200 flex items-center m-0.5"
              on:click={() => {
                choiceStockInfoList = choiceStockInfoList.filter((item) => item.value !== choiceStockInfo.value);
              }}
              title="클릭하여 제거"
            >
              <span>{choiceStockInfo.name}</span>
              <span class="text-blue-500 font-bold">×</span>
            </button>
          {/each}
        {/if}
      </div>
    </div>
  </div>
  <div slot="subInfo" class="flex w-full justify-end items-center space-x-2">
    <div class="text-sm text-white mr-auto">
      {choiceStockInfoList.length}개 종목 선택됨
    </div>
    <button
      class="flex items-center justify-center border-2 rounded-md px-4 py-2 border-emerald-500 bg-emerald-500 text-white hover:bg-emerald-600 hover:border-emerald-600 transition-colors duration-200 font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
      disabled={choiceStockInfoList.length === 0}
      on:click={applyStockInfoToGraph}
    >
      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
      </svg>
      적용
    </button>
    <button
      class="flex items-center justify-center border-2 rounded-md px-4 py-2 border-red-400/50 bg-red-500/20 text-white hover:bg-red-500/40 hover:border-red-400/70 backdrop-blur-sm transition-colors duration-200 font-medium"
      on:click={closedDialogCallback}
    >
      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
      </svg>
      닫기
    </button>
  </div>
</CommonPopup>

<style>
	/* 현대적인 테이블 컨테이너 */
	.modern-table-wrap {
		width: 100%;
		height: 100%;
		overflow: hidden;
		display: flex;
		flex-direction: column;
		min-height: 0;
		position: relative;
	}
	
	/* 현대적인 테이블 기본 스타일 */
	.modern-table {
		width: 100%;
		height: 100%;
		table-layout: fixed;
		border-collapse: separate;
		border-spacing: 0;
		display: flex;
		flex-direction: column;
		min-height: 0;
		background: transparent;
	}
	
	/* 현대적인 테이블 헤더 */
	.modern-thead {
		display: table;
		table-layout: fixed;
		width: 100%;
		background: linear-gradient(135deg, #475569 0%, #334155 100%);
		flex-shrink: 0;
		position: relative;
		z-index: 10;
	}
	
	/* 현대적인 테이블 헤더 셀 */
	.modern-th {
		color: white;
		background: transparent;
		padding: 16px 12px;
		font-weight: 600;
		border: none;
		height: 56px;
		box-sizing: border-box;
		position: relative;
		vertical-align: middle;
	}
	
	.modern-th:not(:last-child)::after {
		content: '';
		position: absolute;
		right: 0;
		top: 50%;
		transform: translateY(-50%);
		width: 1px;
		height: 24px;
		background: rgba(255, 255, 255, 0.2);
	}
	
	/* 현대적인 테이블 바디 */
	.modern-tbody {
		display: block;
		width: 100%;
		flex-grow: 1;
		min-height: 0;
		max-height: 100%;
		overflow-y: auto;
		overflow-x: hidden;
		background: white;
	}
	
	/* 현대적인 테이블 행 */
	.modern-tr {
		display: table;
		width: 100%;
		table-layout: fixed;
		border-bottom: 1px solid #f1f5f9;
		background: white;
		min-height: 52px;
		position: relative;
	}
	
	.modern-tr:hover {
		transform: translateY(-1px);
		box-shadow: 0 4px 12px -2px rgba(0, 0, 0, 0.1);
		border-bottom-color: transparent;
		z-index: 5;
	}
	
	.modern-tr:last-child {
		border-bottom: none;
	}
	
	/* 현대적인 테이블 데이터 셀 */
	.modern-td {
		padding: 16px 12px;
		border: none;
		box-sizing: border-box;
		vertical-align: middle;
		height: 52px;
		position: relative;
		background: inherit;
	}
	
	/* 빈 상태 메시지를 위한 특별한 스타일 */
	.modern-tr:has(.text-center) {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.modern-tr:has(.text-center) .modern-td {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0;
	}
	
	/* 로딩 상태 스타일 */
	.modern-tbody:has(.loading-state) {
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
	}
	
	.modern-tr.loading-state {
		display: flex;
		width: 100%;
		height: 100%;
		align-items: center;
		justify-content: center;
		border: none;
	}
	
	.modern-tr.loading-state .modern-td {
		display: flex;
		width: 100%;
		height: 100%;
		align-items: center;
		justify-content: center;
		border: none;
		padding: 0;
	}

	/* 스크롤바 현대적 스타일링 */
	.modern-tbody::-webkit-scrollbar {
		width: 8px;
		background: transparent;
	}

	.modern-tbody::-webkit-scrollbar-track {
		background: #f8fafc;
		border-radius: 4px;
		margin: 4px;
	}

	.modern-tbody::-webkit-scrollbar-thumb {
		background: linear-gradient(135deg, #cbd5e1 0%, #94a3b8 100%);
		border-radius: 4px;
		border: 1px solid #e2e8f0;
	}

	.modern-tbody::-webkit-scrollbar-thumb:hover {
		background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
		border-color: #cbd5e1;
	}

	/* Firefox 스크롤바 */
	.modern-tbody {
		scrollbar-width: thin;
		scrollbar-color: #cbd5e1 #f8fafc;
	}

	/* 페이지네이션 버튼 호버 효과 강화 */
	.group:hover svg {
		transition: transform 0.2s ease-in-out;
	}

	/* 선택된 항목 영역 스크롤바 */
	.bg-gray-50::-webkit-scrollbar {
		width: 6px;
		height: 6px;
	}

	.bg-gray-50::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.05);
		border-radius: 3px;
	}

	.bg-gray-50::-webkit-scrollbar-thumb {
		background: rgba(0, 0, 0, 0.2);
		border-radius: 3px;
	}

	.bg-gray-50::-webkit-scrollbar-thumb:hover {
		background: rgba(0, 0, 0, 0.4);
	}

	/* 반응형 텍스트 크기 */
	@media (max-width: 768px) {
		.modern-th {
			padding: 12px 8px;
			height: 48px;
		}
		
		.modern-td {
			padding: 12px 8px;
			height: 48px;
		}
		
		.modern-th .text-sm {
			font-size: 0.75rem;
		}
	}

	/* 애니메이션 효과 */
	@keyframes fadeInUp {
		from {
			opacity: 0;
			transform: translateY(10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.modern-tr {
		animation: fadeInUp 0.3s ease-out;
	}

	/* 정렬 아이콘 애니메이션 */
	.modern-th.cursor-pointer:hover .text-sm {
		text-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
	}

	/* 탭 버튼 비활성화 스타일 */
	button:disabled {
		pointer-events: none;
		user-select: none;
	}

	button:disabled:hover {
		background-color: inherit !important;
		border-color: inherit !important;
		transform: none !important;
		box-shadow: none !important;
	}

	/* 로딩 중 탭 버튼 스타일 */
	.loading-tab {
		position: relative;
		overflow: hidden;
	}

	.loading-tab::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
		animation: shimmer 1.5s infinite;
		z-index: 1;
	}

	@keyframes shimmer {
		0% {
			transform: translateX(-100%);
		}
		100% {
			transform: translateX(100%);
		}
	}

	/* 스피너 애니메이션 */
	@keyframes spin {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}

	.animate-spin {
		animation: spin 1s linear infinite;
	}
	
	/* 빈 상태 행을 위한 특별한 스타일 */
	.empty-state-row {
		height: 100% !important;
		display: flex !important;
		align-items: center !important;
		justify-content: center !important;
		border: none !important;
		animation: none !important;
	}
	
	.empty-state-cell {
		height: 100% !important;
		display: flex !important;
		align-items: center !important;
		justify-content: center !important;
		padding: 32px !important;
		text-align: center !important;
		vertical-align: middle !important;
	}
	
	/* 빈 상태가 있는 tbody의 높이 조정 */
	.modern-tbody:has(.empty-state-row) {
		display: flex;
		align-items: center;
		justify-content: center;
	}
</style>