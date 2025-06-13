<script lang="ts">
  import { getFinanceStockList } from '$lib/api-connector/FinanceApi';
  import { CommonPopup, ProgressCircle } from '$lib/component';
  import { onMount, tick } from 'svelte';
  import type { StockType } from '$lib/types';
  import { setUpDownIcon, setUpDownColor } from '$lib/main';
  import { calculateRatio, sortBySimilarity, formatCostValue, formatIncludeComma } from '$lib/utils/CommonHelper';
  import _ from 'lodash';

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

  onMount(async () => {
    isProgress = true;
    originStockInfoList = await setFinanceStockList(getSelectedStockModeValue(stockModeList));
    isProgress = false;
    filteredStockInfoList = _.cloneDeep(originStockInfoList);

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
      choiceStockInfoList: _.cloneDeep(choiceStockInfoList)
    })
  }

  const onFocusSearchText = (e: KeyboardEvent) => {
    if (e.key === 'F4' && filteredStockInfoList.length > 0) {
			e.preventDefault(); // 기본 동작 막기
			e.stopPropagation(); // 이벤트 전파 중단하기
			
      searchInputDocument?.focus();
		}
  }
</script>

<svelte:window bind:innerHeight on:keydown={onFocusSearchText}/>
<CommonPopup {titleName} modalPositionType="center" on:closedDialogCallback={closedDialogCallback}>
  <div class="flex flex-col w-[800px] bg-white" style="height: {popupHeight}px;">
    <!-- 검색 영역 - 고정 높이 -->
    <div class="flex h-auto w-full mt-2 px-2 flex-shrink-0">
      <!-- 검색란 -->
      <div class="flex flex-row w-full">
        <label class="w-[80px] font-bold" for="name">{'종목 검색'}</label>
        <input
          bind:this={searchInputDocument}
          autocomplete="off"
          type="text"
          id="name"
          name="name"
          class="border grow px-1 rounded-md"
          autofocus={true}
          disabled={isProgress}
          minlength="4"
          maxlength="8"
          size="10"
          placeholder="종목명/종목코드 검색"
          bind:value={searchStockText}
          on:keypress={async (e) => {
            if (e.key === 'Enter') {
              isProgress = true;
              filteredStockInfoList = sortBySimilarity(searchStockText, originStockInfoList.filter((item) => item?.Symbol?.includes(searchStockText) || item?.Code?.includes(searchStockText) || item?.Name?.includes(searchStockText)), ['Code', 'Name', 'Symbol']);
              isProgress = false;

              await tick();
              searchInputDocument?.focus();
            }
          }}
        />
      </div>
    </div>
    <!-- 버튼 영역 - 고정 높이 -->
    <div class="flex flex-row h-auto w-full space-x-1 px-2 py-2 flex-shrink-0">
      {#each stockModeList as stockMode}
        <button
          class="border rounded-md px-1 border-gray-400 {stockMode.isSelected ? 'bg-gray-200' : 'bg-white'}"
          on:click={async () => {
            searchStockText = '';

            stockModeList = setSelectStockModeList(stockModeList, stockMode.value);

            filteredStockInfoList = [];
            originStockInfoList = await setFinanceStockList(getSelectedStockModeValue(stockModeList));
            filteredStockInfoList = _.cloneDeep(originStockInfoList);
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
              <th on:click={() => {
                filteredStockInfoList = _.sortBy(filteredStockInfoList, (item) => { return item?.ChagesRatio; }).reverse();
              }} style="width: 15%; text-align: center;">{@html "전일대비<br/>상승&하락"}</th>
              <th style="width: 15%; text-align: center;">시초가</th>
              <th on:click={() => {
                filteredStockInfoList = _.sortBy(filteredStockInfoList, (item) => { return parseFloat(item?.VolumeRatio); }).reverse();
              }} style="width: 15%; text-align: center;">{@html "거래 유동성"}</th>
            </tr>
          </thead>
          <tbody class="{(isProgress || filteredStockInfoList.length === 0) ? 'loading-state' : ''}">
            {#if filteredStockInfoList.length > 0 && isProgress === false}
              {#each filteredStockInfoList as stockInfo}
                <tr
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
                      choiceStockInfoList.push(newStockInfo);
                      choiceStockInfoList = _.uniqBy(choiceStockInfoList, "code");
                    }
                  }}
                >
                  <td style="width: 10%">{stockInfo?.Code ?? stockInfo?.Symbol}</td>
                  <td style="width: 30%">{stockInfo?.Name}</td>
                  <td style="width: 15%; text-align: right;">{`${formatIncludeComma(formatCostValue(stockInfo?.Close)) ?? '-'} ₩`}</td>
                  <td style="width: 15%; text-align: center; color: {setUpDownColor(stockInfo?.ChagesRatio)}">{`${setUpDownIcon(stockInfo?.ChagesRatio)} ${stockInfo?.ChagesRatio ?? '-'}%`}</td>
                  <td style="width: 15%; text-align: right;">{`${formatIncludeComma(formatCostValue(stockInfo?.Open)) ?? '-'} ₩`}</td>
                  <td style="width: 15%; text-align: right;">{`${stockInfo['VolumeRatio'] ?? '-'}%`}</td>
                </tr>
              {/each}
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
    <!-- 선택된 항목 영역 - 고정 높이 -->
    <div class="flex w-full h-[80px] flex-shrink-0 px-2 pb-2">
      <div class="flex flex-wrap w-full h-full border overflow-auto p-1 space-x-1">
        {#each choiceStockInfoList as choiceStockInfo}
          <button
            class="border rounded-md px-1 border-gray-400 bg-white h-[30px] flex-shrink-0"
            on:click={() => {
              choiceStockInfoList = choiceStockInfoList.filter((item) => item.value !== choiceStockInfo.value);
            }}
          >
            {choiceStockInfo.name}
          </button>
        {/each}
      </div>
    </div>
  </div>
  <div slot="subInfo" class="flex w-full justify-end items-end space-x-1">
    <button
      class="flex items-center justify-center border-2 rounded-md px-1 border-gray-400 bg-white"
      on:click={applyStockInfoToGraph}>적용</button
    >
    <button
      class="flex items-center justify-center border-2 rounded-md px-1 border-gray-400 bg-white"
      on:click={closedDialogCallback}>닫기</button
    >
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

	/* 스크롤바 스타일링 */
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
</style>