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
	let originStockInfoList: StockType[] = [];

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
      const calculatedHeight = Math.floor(innerHeight * 0.85); // 85%
      popupHeight = Math.min(Math.max(600, calculatedHeight), 1000); // 최소 600px, 최대 1000px
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
    originStockInfoList = await setFinanceStockList(getSelectedStockModeValue(stockModeList));
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

    const sorted = [...searchFilteredList].sort((a: any, b: any) => {
      const aRatio = parseFloat(a?.ChagesRatio) || 0;
      const bRatio = parseFloat(b?.ChagesRatio) || 0;
      
      if (nextState === 'desc') {
        return bRatio - aRatio; // 내림차순
      } else {
        return aRatio - bRatio; // 오름차순
      }
    });
    
    // 원본 데이터 업데이트
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

    const sorted = [...searchFilteredList].sort((a: any, b: any) => {
      const aRatio = parseFloat(a?.VolumeRatio) || 0;
      const bRatio = parseFloat(b?.VolumeRatio) || 0;
      
      if (nextState === 'desc') {
        return bRatio - aRatio; // 내림차순
      } else {
        return aRatio - bRatio; // 오름차순
      }
    });
    
    // 원본 데이터 업데이트
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
      const tbody = document.querySelector('.tableWrap tbody');
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
    
    // 원본 데이터를 다시 불러오기
    isProgress = true;
    originStockInfoList = await setFinanceStockList(getSelectedStockModeValue(stockModeList));
    isProgress = false;
    
    // 검색 입력창에 포커스
    await tick();
    searchInputDocument?.focus();
  }
</script>

<svelte:window bind:innerHeight on:keydown={onFocusSearchText}/>
<CommonPopup {titleName} modalPositionType="center" on:closedDialogCallback={closedDialogCallback}>
  <div class="flex flex-col w-[800px] bg-white" style="height: {popupHeight}px;">
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
      <div class="flex justify-center py-1 px-2">
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
          class="border rounded-md px-3 py-1 border-gray-400 transition-colors duration-200 {stockMode.isSelected ? 'bg-blue-100 border-blue-400 text-blue-700 font-semibold' : 'bg-white hover:bg-gray-50'}"
          on:click={async () => {
            searchStockText = '';
            currentPage = 0;

            // 정렬 상태 초기화
            sortState.chagesRatio = 'none';
            sortState.volumeRatio = 'none';

            stockModeList = setSelectStockModeList(stockModeList, stockMode.value);

            isProgress = true;
            originStockInfoList = await setFinanceStockList(getSelectedStockModeValue(stockModeList));
            isProgress = false;
          }}
        >
          {stockMode.name}
        </button>
      {/each}
    </div>

    <!-- 주식 목록 Grid - 남은 공간 모두 사용 -->
    <div class="flex w-full flex-grow px-2 min-h-0 mb-1">
      <div class="tableWrap">
        <table>
          <thead>
            <tr tabindex="0">
              <th style="width: 10%; text-align: left;">코드</th>
              <th style="width: 30%; text-align: left;">주식명</th>
              <th style="width: 15%; text-align: center;">현재가</th>
              <th 
                class="cursor-pointer hover:bg-gray-600 transition-colors duration-200" 
                on:click={sortByChagesRatio} 
                style="width: 15%; text-align: center;"
                title="클릭하여 정렬"
              >{@html `전일대비<br/>상승&하락 ${getSortIcon(sortState.chagesRatio)}`}</th>
              <th style="width: 15%; text-align: center;">시초가</th>
              <th 
                class="cursor-pointer hover:bg-gray-600 transition-colors duration-200" 
                on:click={sortByVolumeRatio} 
                style="width: 15%; text-align: center;"
                title="클릭하여 정렬"
              >{@html `거래 유동성 ${getSortIcon(sortState.volumeRatio)}`}</th>
            </tr>
          </thead>
          <tbody style="height: {popupHeight - 280}px" class="{(isProgress || searchFilteredList.length === 0) ? 'loading-state' : ''}">
            {#if searchFilteredList.length > 0 && isProgress === false}
              {#if tableData.length > 0}
                {#each tableData as stockInfo}
                  <tr
                    class="hover:bg-blue-50 transition-colors duration-150 cursor-pointer"
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
                    <td style="width: 10%">{stockInfo?.Code ?? stockInfo?.Symbol}</td>
                    <td style="width: 30%">{stockInfo?.Name}</td>
                    <td style="width: 15%; text-align: right;">{`${formatIncludeComma(formatCostValue(stockInfo?.Close)) ?? '-'} ₩`}</td>
                    <td style="width: 15%; text-align: center; color: {setUpDownColor(stockInfo?.ChagesRatio)}">{`${setUpDownIcon(stockInfo?.ChagesRatio)} ${stockInfo?.ChagesRatio ?? '-'}%`}</td>
                    <td style="width: 15%; text-align: right;">{`${formatIncludeComma(formatCostValue(stockInfo?.Open)) ?? '-'} ₩`}</td>
                    <td style="width: 15%; text-align: right;">{`${stockInfo.VolumeRatio ?? '-'}%`}</td>
                  </tr>
                {/each}
              {:else}
                <tr>
                  <td colspan="6" class="text-center py-4 text-gray-500">
                    '{searchStockText}' 검색 결과가 없습니다.
                  </td>
                </tr>
              {/if}
            {:else if isProgress}
              <tr>
                <td colspan="6">
                  <ProgressCircle
                    text={'해당 증시 목록을 가져오는 중입니다...'}
                  />
                </td>
              </tr>
            {:else}
              <tr>
                <td colspan="6">
                  <p class="font-bold text-gray-500">
                    {'목록이 없습니다.'}
                  </p>
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
              검색: {searchFilteredList.length}/{originStockInfoList.length}
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

    <!-- 선택된 항목 영역 - 고정 높이 -->
    <div class="flex w-full h-[80px] flex-shrink-0 px-2 pb-2">
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
  <div slot="subInfo" class="flex w-full justify-end items-end space-x-2">
    <div class="text-sm text-gray-600 mr-auto">
      {choiceStockInfoList.length}개 종목 선택됨
    </div>
    <button
      class="flex items-center justify-center border-2 rounded-md px-4 py-2 border-blue-500 bg-blue-500 text-white hover:bg-blue-600 transition-colors duration-200 font-semibold"
      disabled={choiceStockInfoList.length === 0}
      on:click={applyStockInfoToGraph}
    >
      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
      </svg>
      적용
    </button>
    <button
      class="flex items-center justify-center border-2 rounded-md px-4 py-2 border-gray-400 bg-white hover:bg-gray-50 transition-colors duration-200"
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
	.tableWrap {
		width: 100%;
		height: 100%;
		overflow: hidden;
		border: 1px solid #ccc;
		display: flex;
		flex-direction: column;
		min-height: 0; /* flexbox에서 축소 가능하도록 */
	}
	
	table {
		width: 100%;
		height: 100%;
		table-layout: fixed;
		border-collapse: collapse;
		display: flex;
		flex-direction: column;
		min-height: 0; /* flexbox에서 축소 가능하도록 */
	}
	
	thead {
		display: table;
		table-layout: fixed;
		width: 100%;
		background-color: #4B5563;
		flex-shrink: 0;
	}
	
	tbody {
		display: block;
		width: 100%;
		flex-grow: 1;
		min-height: 0; /* flexbox에서 축소 가능하도록 */
		max-height: 100%; /* 부모 컨테이너 높이를 넘지 않도록 */
		overflow-y: auto;
		overflow-x: hidden;
	}
	
	/* 로딩 상태일 때 tbody가 전체 높이를 사용하도록 */
	tbody.loading-state {
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
	}
	
	/* 로딩 상태의 tr이 전체 높이를 사용하도록 */
	tbody.loading-state tr {
		display: flex;
		width: 100%;
		height: 100%;
		align-items: center;
		justify-content: center;
	}
	
	/* 로딩 상태의 td가 전체 공간을 사용하도록 */
	tbody.loading-state td {
		display: flex;
		width: 100%;
		height: 100%;
		align-items: center;
		justify-content: center;
		border: none;
	}
	
	thead tr, tbody tr {
		display: table;
		width: 100%;
		table-layout: fixed;
	}
	
	/* 일반 tbody tr에 최소 높이 설정 */
	tbody:not(.loading-state) tr {
		min-height: 35px; /* 각 행의 최소 높이 보장 */
	}
	
	th {
		color: white;
		background-color: #4B5563;
		padding: 8px 4px;
		font-weight: bold;
		border-right: 1px solid #6B7280;
		height: 40px;
		box-sizing: border-box;
	}
	
	th:last-child {
		border-right: none;
	}
	
	td {
		padding: 6px 4px;
		border-bottom: 1px solid #e5e7eb;
		border-right: 1px solid #e5e7eb;
		box-sizing: border-box;
		vertical-align: middle;
		height: 35px; /* 고정 높이로 일관성 유지 */
	}
	
	td:last-child {
		border-right: none;
	}
	
	tbody tr:last-child td {
		border-bottom: none;
	}

	/* 기본 배경색 */
	tbody tr {
		background-color: white;
	}

	/* 호버 효과 */
	tbody tr:hover {
		background-color: #f0f8ff;
		cursor: pointer;
	}

	/* 스크롤바 스타일링 - +page.svelte와 동일하게 */
	tbody::-webkit-scrollbar {
		width: 8px;
	}

	tbody::-webkit-scrollbar-track {
		background: #f1f1f1;
		border-radius: 4px;
	}

	tbody::-webkit-scrollbar-thumb {
		background: #c1c1c1;
		border-radius: 4px;
	}

	tbody::-webkit-scrollbar-thumb:hover {
		background: #a8a8a8;
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
</style>