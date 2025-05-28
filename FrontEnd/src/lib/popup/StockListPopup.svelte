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
    name: string,
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

  let stockModeList: Array<{name: string, value: string, isSelected: boolean}> = [
    { name: '국내상장', value: 'KRX', isSelected: true },
    { name: '나스닥상장', value: 'NASDAQ', isSelected: false },
    { name: 'S&P500상장', value: 'S&P500', isSelected: false },
    { name: '상하이상장', value: 'SSE', isSelected: false },
    { name: '도쿄상장', value: 'TSE', isSelected: false },
  ]
  
  let searchInputDocument;

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

    return result.data.map((item) => {
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

  const onFocusSearchText = (e) => {
    if (e.key === 'F4' && filteredStockInfoList.length > 0) {
			e.preventDefault(); // 기본 동작 막기
			e.stopPropagation(); // 이벤트 전파 중단하기
			
      searchInputDocument?.focus();
		}
  }
</script>

<svelte:window on:keydown={onFocusSearchText}/>
<CommonPopup {titleName} on:closedDialogCallback={closedDialogCallback}>
  <div class="flex flex-col w-[800px] h-[1000px] bg-white space-y-2 p-2">
    <div class="flex h-auto w-full mt-2">
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
    <div class="flex flex-row h-auto w-full space-x-1">
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
    <!-- 주식 목록 Grid -->
    <div class="flex h-[800px] w-full">
      <div class="tableWrap border">
        <table>
          <thead>
            <tr tabindex="0">
              <th style="width: 10%; text-align: left;">코드</th>
              <th style="width: 30%; text-align: left;">주식명</th>
              <th style="width: 15%; text-align: center;">현재가</th>
              <th on:click={() => {
                filteredStockInfoList = _.sortBy(filteredStockInfoList, (item) => { return item?.ChagesRatio; }).reverse();
              }} style="width: 15%; text-align: center;">{@html `전일대비<br/>상승&하락`}</th>
              <th style="width: 15%; text-align: center;">시초가</th>
              <th on:click={() => {
                filteredStockInfoList = _.sortBy(filteredStockInfoList, (item) => { return parseFloat(item?.VolumeRatio); }).reverse();
              }} style="width: 15%; text-align: center;">{@html `거래 유동성`}</th>
            </tr>
          </thead>
          <tbody>
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
                  <td style="width: 15%; text-align: right;">{`${stockInfo?.VolumeRatio ?? '-'}%`}</td>
                </tr>
              {/each}
            {:else if isProgress}
              <div class="flex w-full h-full justify-center items-center font-bold text-gray">
                <ProgressCircle
                  text={'해당 증시 목록을 가져오는 중입니다...'}
                />
              </div>
            {:else}
              <p class="flex w-full h-full justify-center items-center font-bold text-gray">
                {'목록이 없습니다.'}
              </p>
            {/if}
          </tbody>
        </table>
      </div>
    </div>
    <div class="flex w-full grow">
      <div class="flex flex-wrap w-full h-[100px] border overflow-auto p-1 space-x-1">
        {#each choiceStockInfoList as choiceStockInfo}
          <button
            class="border rounded-md px-1 border-gray-400 bg-white h-[30px]"
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
		height: calc(100%);
	}
	thead {
		display: table;
		table-layout: fixed;
		width: 100%;
	}
	tbody {
		width: 100%;
		display: block;
		height: calc(100%);
		overflow: auto;
	}
  th {
    color: white;
    background-color: #4B5563;
  }
	tr {
		display: table;
		width: 100%;
		table-layout: fixed;
    border-bottom: 1px solid black; /* 각 행 하단에 라인 추가 */
	}
  tr:last-child {
    border-bottom: none; /* 마지막 행에는 라인 제거 */
  }
	table {
		table-layout: fixed;
	}
	tbody {
		height: 740px;
		grid-auto-flow: row;
	}
	td {
		margin-top: -1px;
	}

  /* 기본 배경색 */
  table tr {
    background-color: white;
  }

  /* 포커스된 행의 배경색 */
  table tr:hover {
    background-color: #f0f8ff;
  }

  /* 키보드 네비게이션을 위한 outline 제거 */
  table tr:hover {
    outline: none;
  }
</style>