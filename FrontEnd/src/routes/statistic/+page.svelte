<script lang="ts">
  import { getFinanceStockList, getExpectStockValue, getAllFinanceRankList } from '$lib/api-connector/FinanceApi';
  import type { StockType } from '$lib/types';
  import { calculateRatio, formatCostValue, formatIncludeComma, sortBySimilarity } from '$lib/utils/CommonHelper';
  import { getFinanceDataListByChartMode, calculateExpectFinanceScore, selfNormalize, SingleChartBasic, sendFinanceResult } from '$lib/main';
  import { onMount, onDestroy, tick } from 'svelte';
  import { BarChart, ProgressCircle, KakaoLoginAndSend } from '$lib/component';
  import toast from 'svelte-french-toast';
  import { cancelRequest } from "$lib/axios-provider/AxiosProvider";
  import _ from 'lodash';

  let stockModeList: Array<{name: string, value: string, isSelected: boolean}> = [
    { name: '국내상장', value: 'KRX', isSelected: true },
    { name: '나스닥상장', value: 'NASDAQ', isSelected: false },
    { name: 'S&P500상장', value: 'S&P500', isSelected: false },
    { name: '상하이상장', value: 'SSE', isSelected: false },
    { name: '도쿄상장', value: 'TSE', isSelected: false },
  ]

  let durationObject: any = {
    '2 YEAR': {month: 24, week: 104},
    '1 YEAR': {month: 12, week: 52},
    '6 MONTH': {month: 6, week: 26}
  }

  let searchDuration: any = durationObject['1 YEAR'];

  let isSingleMode: boolean = false;

  let singleChartInfo: {
		title: string,
		searchDuration: {month: number, week: number},
		chartMode: string,
		chartKey: string,
		detailInfo: any
	} | null = null;

  let financeMonthRankObject: any = null;

  let selectedFinanceMonthRankList: any = [];
  let financeAllRankList: any = [];

  let innerHeight: number = 0;

  let loadProgress: boolean = false;
  let loadingText: string = '';

  let allPeriodTextKey: string = '전체 기간 없음';
  let selectedMonthRank: string = '';

  let axiosController: any = null;
  
  let searchAllStockText: string = '';
  let searchMonthStockText: string = '';

  let kakaoAccessCode: string = '';
  let kakaoAccessToken: string = '';

  onMount(() => {
    kakaoAccessCode = sessionStorage.getItem('kakaoAccessCode') ?? '';
    kakaoAccessToken = sessionStorage.getItem('kakaoAccessToken') ?? '';

    getKoreaAllFinanceRankList();
  })

  onDestroy(() => {
    if (typeof document !== 'undefined') {
      cancelRequest(axiosController);
      sessionStorage.setItem('kakaoAccessCode', kakaoAccessCode);
      sessionStorage.setItem('kakaoAccessToken', kakaoAccessToken);
    }
  });

  const getKoreaAllFinanceRankList = async () => {
    axiosController = new AbortController();
    allPeriodTextKey = '전체 기간 없음';
    financeAllRankList = [];
    financeMonthRankObject = null;
    loadProgress = true;

    const resultList = await getAllFinanceRankList({stock: 'KRX'}, axiosController);

    loadProgress = false;

    if (!!resultList?.data?.allPeriodDataList) {
      allPeriodTextKey = Object.keys(resultList.data?.allPeriodDataList)[0];
      financeAllRankList = _.orderBy(resultList.data?.allPeriodDataList[allPeriodTextKey].map((item) => {return {...item, rankSum: parseInt(item.rankSum), count: parseInt(item.count)}}), ['count', 'rankSum'], ['desc', 'asc']);
    };

    if (!!resultList?.data?.perMonthDataList) {
      financeMonthRankObject = resultList.data?.perMonthDataList
      selectedMonthRank = Object.keys(financeMonthRankObject)[Object.keys(financeMonthRankObject).length - 1];
      selectedFinanceMonthRankList = _.orderBy(financeMonthRankObject[selectedMonthRank].map((item) => {return {...item, rankSum: parseInt(item.rankSum), count: parseInt(item.count)}}), ['count', 'rankSum'], ['desc', 'asc']);
    };
  }

  const scrollToCodeInfo = (tableMode: 'All' | 'Month', stockCode: string) => {
    const row = document.querySelector(`tr[data-row-id="${tableMode}_${stockCode}"]`);
    if (row) {
      row.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  /**
   * 카카오톡으로 보낼 통계 메세지 생성
  */
  const getFinanceResultMessageText = () => {
    const NaverFinanceUrl: string = 'https://finance.naver.com/item/main.naver?code=';
    let financeResultMessageText: string = '';

    if (financeAllRankList.length < 1) {
      return financeResultMessageText;
    }

    financeResultMessageText += `[${allPeriodTextKey}]기간 TOP 10종목\n`;

    let rank: number = 1;
    for (let financeAllRankInfo of financeAllRankList.slice(1, 11)) {
      financeResultMessageText += `${rank}등 ${financeAllRankInfo?.name} Link: ${NaverFinanceUrl}${financeAllRankInfo?.code}\n`;
      rank += 1;
    };

    return financeResultMessageText;
  }

  /**
   * 통계 결과 값 카카오로 전송 (요청 1회 당 1000글자 전송가능)
  */
  const sendFinanceResultByKakaoApi = async () => {
    if (!!!kakaoAccessCode) {
      return;
    }

    await tick();

    const result = await sendFinanceResult(kakaoAccessCode, kakaoAccessToken, getFinanceResultMessageText());

    if (result.isFail === true) {
      toast.error('카카오 Access Code를 재발급 받으세요.');
      kakaoAccessToken = '';
    } else {
      toast.success('카카오 메세지 전달 성공.');
      kakaoAccessToken = result.token;
    }
  }

  /**
   * 카카오 인증코드 갱신
  */
  const onUpdateKakaoAccessCode = (e: any) => {
    if (!!!e?.detail) {
      return;
    }

    toast.success('카카오 인증코드 갱신');

    kakaoAccessCode = e.detail;
    sessionStorage.setItem('kakaoAccessCode', e.detail);
  }
</script>

<svelte:window bind:innerHeight/>
<div class="flex w-full h-full bg-gray-600 relative">
  <div class="flex flex-col w-full h-full p-2 space-y-2">
    <!-- 전체 -->
    <div class="flex flex-row h-[50%] space-x-2 border bg-white rounded-e-md">
      <!-- bar chart -->
      <div class="flex flex-col h-full w-[50%] border-r p-2 space-y-2">
        <p class="flex h-auto w-full font-bold">{allPeriodTextKey}</p>
        <div class="flex grow rounded-md overflow-auto">
          {#if financeAllRankList.length > 0 && loadProgress === false}
            <div class="h-auto">
              <BarChart
                barDataList={financeAllRankList.filter((item) => item?.count > 0)}
              />
            </div>
          {:else if loadProgress}
            <div class="flex w-full h-full justify-center items-center font-bold text-gray">
              <ProgressCircle
                size={100}
                thickness={10}
                isLarge={true}
                text={'저장된 전체 기간 상위도달횟수 데이터 조회 중...'}
              />
            </div>
          {:else}
            <p class="flex w-full h-full justify-center items-center font-bold text-gray">
              {'저장된 전체 기간 상위도달횟수 데이터가 없습니다.'}
            </p>
          {/if}
        </div>
      </div>
      <div class="flex flex-col h-full w-[50%]">
        <div class="flex flex-row h-auto w-full pt-2 pb-1 px-2">
          <div class="flex flex-row grow space-x-1 items-center">
            <p class="font-bold mr-2">{'🔍 종목 검색'}</p>
            <input
              type="text"
              autocomplete="off"
              id="name"
              name="name"
              class="border w-[200px] px-1 rounded-md"
              autofocus={true}
              disabled={financeAllRankList.length < 1 ? true : false}
              minlength="4"
              maxlength="8"
              size="10"
              placeholder="종목명/종목코드 검색"
              bind:value={searchAllStockText}
              on:keypress={async (e) => {
                if (e.key === 'Enter') {
                  const searchAllStockList = financeAllRankList.filter((item) => item.name.includes(searchAllStockText) || item.code.includes(searchAllStockText));
  
                  if (searchAllStockList.length < 1) {
                    return;
                  }
  
                  scrollToCodeInfo('All', searchAllStockList[0]?.code ?? '');
                }
              }}
            />
          </div>
          <div class="flex grow">
            <KakaoLoginAndSend
              bind:kakaoAccessCode
              on:onSendFinanceResultByKakaoApiCallback={sendFinanceResultByKakaoApi}
              on:onUpdateKakaoAccessCodeCallback={onUpdateKakaoAccessCode}
            />
          </div>
        </div>
        <div class="flex grow w-full">
          <div class="tableWrap p-1">
            <table>
              <thead>
                <tr tabindex="0">
                  <th style="width: 5%; text-align: center;">Rank</th>
                  <th style="width: 10%; text-align: center;">RankSum</th>
                  <th style="width: 10%; text-align: center;">CountSum</th>
                  <th style="width: 30%; text-align: center;">코드</th>
                  <th style="width: 45%; text-align: left;">주식명</th>
                </tr>
              </thead>
              <tbody style="height: {(innerHeight / 2) - 90}px">
                {#if financeAllRankList.length > 0 && loadProgress === false}
                  {#each financeAllRankList as financeAllRankInfo, index}
                    <tr
                      data-row-id={`All_${financeAllRankInfo?.code}`}
                      on:click={() => {
                        if (financeAllRankInfo.name === '횟수') {
                          toast('해당 월 분석 횟수입니다.');
                          return;
                        }

                        singleChartInfo = {
                          title: financeAllRankInfo.name,
                          searchDuration: searchDuration,
                          chartMode: financeAllRankInfo.code,
                          chartKey: financeAllRankInfo.code,
                          detailInfo: null
                        }
    
                        isSingleMode = true;
                      }}
                    >
                      <td style="width: 5%; text-align: center;">{index}</td>
                      <td style="width: 10%; text-align: center;">{financeAllRankInfo?.rankSum ?? '-'}</td>
                      <td style="width: 10%; text-align: center;">{financeAllRankInfo?.count ?? '-'}</td>
                      <td style="width: 30%; text-align: center;">{financeAllRankInfo?.code ?? '-'}</td>
                      <td style="width: 45%; text-align: left;">{financeAllRankInfo?.name ?? '-'}</td>
                    </tr>
                  {/each}
                {:else if loadProgress}
                  <div class="flex w-full h-full justify-center items-center font-bold text-gray">
                    <ProgressCircle
                      size={100}
                      thickness={10}
                      isLarge={true}
                      text={'저장된 전체 기간 RankSum 데이터 조회 중...'}
                    />
                  </div>
                {:else}
                  <p class="flex w-full h-full justify-center items-center font-bold text-gray">
                    {'저장된 전체 기간 RankSum 데이터가 없습니다.'}
                  </p>
                {/if}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    <!-- 월별 -->
    <div class="flex flex-row h-[50%] space-x-2 border bg-white rounded-e-md">
      <!-- bar chart -->
      <div class="flex flex-col h-full w-[50%] border-r p-2 space-y-2">
        <div class="flex flex-wrap h-[75px] w-full border rounded-md overflow-auto px-1 py-0.5">
          {#if !!financeMonthRankObject}
            {#each Object.keys(financeMonthRankObject) as financeMonth}
              <button class="border border-gray-400 h-[30px] rounded-md px-2 mr-1 my-0.5 {selectedMonthRank === financeMonth ? 'bg-gray-200' : 'bg-white'}" on:click={async () => {
                selectedMonthRank = financeMonth;
                selectedFinanceMonthRankList = financeMonthRankObject[selectedMonthRank];
                selectedFinanceMonthRankList = _.orderBy(financeMonthRankObject[selectedMonthRank].map((item) => {return {...item, rankSum: parseInt(item.rankSum), count: parseInt(item.count)}}), ['count', 'rankSum'], ['desc', 'asc']);
              }}>{financeMonth}</button>
            {/each}
          {/if}
        </div>
        <div class="flex grow rounded-md overflow-auto">
          {#if selectedFinanceMonthRankList.length > 0 && loadProgress === false}
            {#key selectedFinanceMonthRankList}
              <div class="h-auto">
                <BarChart
                  barDataList={selectedFinanceMonthRankList.filter((item) => item?.count > 0)}
                />
              </div>
            {/key}
          {:else if loadProgress}
            <div class="flex w-full h-full justify-center items-center font-bold text-gray">
              <ProgressCircle
                size={100}
                thickness={10}
                isLarge={true}
                text={'저장된 월별 상위도달횟수 데이터 조회 중...'}
              />
            </div>
          {:else}
            <p class="flex w-full h-full justify-center items-center font-bold text-gray">
              {'저장된 월별 상위도달횟수 데이터가 없습니다.'}
            </p>
          {/if}
        </div>
      </div>
      <div class="flex flex-col h-full w-[50%]">
        <div class="flex flex-row h-auto w-full space-x-1 pt-2 pb-1 items-center">
          <p class="font-bold mr-2">{'🔍 종목 검색'}</p>
          <input
            type="text"
            id="name"
            name="name"
            autocomplete="off"
            class="border w-[200px] px-1 rounded-md"
            autofocus={true}
            disabled={selectedFinanceMonthRankList.length < 1 ? true : false}
            minlength="4"
            maxlength="8"
            size="10"
            placeholder="종목명/종목코드 검색"
            bind:value={searchMonthStockText}
            on:keypress={async (e) => {
              if (e.key === 'Enter') {
                const searchMonthStockList = selectedFinanceMonthRankList.filter((item) => item.name.includes(searchMonthStockText) || item.code.includes(searchMonthStockText));

                if (searchMonthStockList.length < 1) {
                  return;
                }

                scrollToCodeInfo('Month', searchMonthStockList[0]?.code ?? '');
              }
            }}
          />
        </div>
        <div class="flex h-full w-full">
          <div class="tableWrap p-1">
            <table>
              <thead>
                <tr tabindex="0">
                  <th style="width: 5%; text-align: center;">Rank</th>
                  <th style="width: 10%; text-align: center;">RankSum</th>
                  <th style="width: 10%; text-align: center;">CountSum</th>
                  <th style="width: 30%; text-align: center;">코드</th>
                  <th style="width: 45%; text-align: left;">주식명</th>
                </tr>
              </thead>
              <tbody style="height: {(innerHeight / 2) - 90}px">
                {#if selectedFinanceMonthRankList.length > 0 && loadProgress === false}
                  {#each selectedFinanceMonthRankList as financeMonthRankInfo, index}
                    <tr
                      data-row-id={`Month_${financeMonthRankInfo?.code}`}
                      on:click={() => {
                        if (financeMonthRankInfo.name === '횟수') {
                          toast('해당 월 분석 횟수입니다.');
                          return;
                        }

                        singleChartInfo = {
                          title: financeMonthRankInfo.name,
                          searchDuration: searchDuration,
                          chartMode: financeMonthRankInfo.code,
                          chartKey: financeMonthRankInfo.code,
                          detailInfo: null
                        }
    
                        isSingleMode = true;
                      }}
                    >
                      <td style="width: 5%; text-align: center;">{index}</td>
                      <td style="width: 10%; text-align: center;">{financeMonthRankInfo?.rankSum ?? '-'}</td>
                      <td style="width: 10%; text-align: center;">{financeMonthRankInfo?.count ?? '-'}</td>
                      <td style="width: 30%; text-align: center;">{financeMonthRankInfo?.code ?? '-'}</td>
                      <td style="width: 45%; text-align: left;">{financeMonthRankInfo?.name ?? '-'}</td>
                    </tr>
                  {/each}
                {:else if loadProgress}
                  <div class="flex w-full h-full justify-center items-center font-bold text-gray">
                    <ProgressCircle
                      size={100}
                      thickness={10}
                      isLarge={true}
                      text={'저장된 월별 RankSum 데이터 조회 중...'}
                    />
                  </div>
                {:else}
                  <p class="flex w-full h-full justify-center items-center font-bold text-gray">
                    {'저장된 월별 RankSum 데이터가 없습니다.'}
                  </p>
                {/if}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
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