<script lang="ts">
  import { getFinanceStockList, getExpectStockValue, saveFinanceRankList, getTodayAnalyze } from '$lib/api-connector/FinanceApi';
  import type { StockType } from '$lib/types';
  import { calculateRatio, formatCostValue, formatIncludeComma, sortBySimilarity, getTodayDateFormatted } from '$lib/utils/CommonHelper';
  import { getFinanceDataListByChartMode, calculateExpectFinanceScore, selfNormalize, SingleChartBasic, sendFinanceResult } from '$lib/main';
  import { onMount, onDestroy, tick } from 'svelte';
  import { DownLoadProgressBar, ProgressCircle, KakaoLoginAndSend } from '$lib/component';
  import { cancelRequest } from "$lib/axios-provider/AxiosProvider";
  import { page } from '$app/stores';
  import toast from 'svelte-french-toast';
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

  let signalScoreWeight = {
    crossWeight: 35,
    volumeWeight: 25,
    lineWeight: 15,
    expectWeight: 25
  }

  /**
   * 검색 조회 기간
  */
  let searchDuration: any = durationObject['1 YEAR'];
  let selectedDurationKey: string = '1 YEAR';

  // 주식 목록
	let stockInfoList: StockType[] = [];

  // 결과 목록
  let calcSignalScoreResultList: any = [];
  let filteredCalcSignalScoreResultList: any = [];

  // 로딩 상태
  let nowStateText: string | null = null;

  let isSingleMode: boolean = false;

  let singleChartInfo: {
		title: string,
		searchDuration: {month: number, week: number},
		chartMode: string,
		chartKey: string,
		detailInfo: any
	} | null = null;

  let count: number = 0;
  let totalStockInfoList: number = 0;
  let loadProgress: boolean = false;

  let searchInputDocument: any;
  let searchStockText: string = '';

  let loadingText: string = '';

  let multipleLength = 5;

  let innerHeight: number = 0;

  let axiosController: any = null;

  let kakaoAccessCode: string = '';
  let kakaoAccessToken: string = '';

  onMount(async () => {
    if (!!!sessionStorage) {
      return;
    }

    count = -1;
    loadingText = '오늘 분석 데이터 조회 중...';
    loadProgress = true;

    kakaoAccessCode = sessionStorage.getItem('kakaoAccessCode') ?? '';
    kakaoAccessToken = sessionStorage.getItem('kakaoAccessToken') ?? '';

    const getSelectedDurationKey = sessionStorage.getItem('selectedDurationKey');
    const getSelectedStockMode = sessionStorage.getItem('selectedStockMode');
    const getCalcResultList = await getTodayAnalyze();

    searchDuration = !!getSelectedDurationKey ? durationObject[getSelectedDurationKey] : durationObject['1 YEAR'];
    stockModeList = !!getSelectedStockMode ? setSelectStockModeList(stockModeList, JSON.parse(getSelectedStockMode)) : stockModeList;
    calcSignalScoreResultList = !!getCalcResultList?.data ? getCalcResultList.data : [];

    filteredCalcSignalScoreResultList = _.cloneDeep(calcSignalScoreResultList);

    sessionStorage.removeItem('selectedDurationKey');
    sessionStorage.removeItem('selectedStockMode');

    loadProgress = false;
    count = 0;
  })

  onDestroy(() => {
    if (typeof document !== 'undefined') {
      cancelRequest(axiosController);
      sessionStorage.setItem('kakaoAccessCode', kakaoAccessCode);
      sessionStorage.setItem('kakaoAccessToken', kakaoAccessToken);

      sessionStorage.setItem('selectedDurationKey', selectedDurationKey);
      sessionStorage.setItem('selectedStockMode', JSON.stringify(getSelectedStockModeValue(stockModeList)));
    }
  });

  /**
   * 증시 분석
  */
  const getCalcSignalScoreResultList = async (stockList: any, calcScoreResultList: any, rank: number) => {
    let promiseFinanceDataList: any = [];

    for (let stockInfo of stockList) {
      const symbol = stockInfo?.Code ?? stockInfo?.Symbol;
      const marcap = stockInfo?.Marcap ?? 0;
      const amount = stockInfo?.Amount ?? 0;

      if (!!!symbol) {
        continue;
      }

      // 해당 주식의 상세 값 조회 후 점수 계산
      const promiseData = getCalculateExpectFinanceScore(marcap, amount, symbol, searchDuration);
      promiseFinanceDataList.push(promiseData);
    }

    const multiAwaitResult = await Promise.all(promiseFinanceDataList);

    let index: number = 0;

    for (let stockInfo of stockList) {
      rank += 1;

      const symbol = stockInfo?.Code ?? stockInfo?.Symbol;
      const marcap = stockInfo?.Marcap ?? 0;
      const amount = stockInfo?.Amount ?? 0;

      if (!!!symbol) {
        continue;
      }

      // 해당 주식의 상세 값 조회 후 점수 계산
      const scoreResult = multiAwaitResult[index];
      index += 1;

      if (!!!scoreResult || scoreResult <= 0) {
        continue;
      }

      calcScoreResultList.push({
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
        amount: stockInfo?.Amount,
        trendScore: parseFloat(scoreResult.toFixed(2)),
        marcapScore: stockInfo?.Marcap <= 0 ? 0 : parseFloat((selfNormalize(rank, 1, totalStockInfoList) * 50).toFixed(2)),
        totalScore: stockInfo?.Marcap <= 0 ? scoreResult : scoreResult + parseFloat((selfNormalize(rank, 1, totalStockInfoList) * 50).toFixed(2)),
        marcap: stockInfo?.Marcap ?? 0
      })
    }

    return {
      rank: rank,
      resultList: calcScoreResultList
    };
  }

  /**
   * 주식 목록 가져오기
  */
  const setFinanceStockList = async (symbol: string) => {
    const result = await getFinanceStockList({symbol: symbol}, axiosController);

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

  const getSelectedStockModeValue = (list: any) => {
    const selectedStockMode = list.find((item: any) => item.isSelected);

    return selectedStockMode?.value;
  }

  /**
   * score와 가중치를 곱한 최종 결과 값 리턴
  */
  const calculateSignalScore = (score: any, scoreWeight: any) => {
    return scoreWeight.crossWeight * score.crossNormalizeValue + scoreWeight.volumeWeight * score.volumeNormalizeValue + scoreWeight.lineWeight * score.lineNormalizeValue + scoreWeight.expectWeight * score.expectNormalizeValue;
  }

  /**
   * 해당 주식의 상세 값 조회 후 점수 계산
  */
  const getCalculateExpectFinanceScore = async (marcap: any, amount: any, symbol: string, duration: {month: number, week: number}) => {
    const financeDataResult = await getFinanceDataListByChartMode(symbol, duration.month, true, axiosController);

    if (financeDataResult.length < 1) {
      return 0;
    }
    
    const expectResult = await getExpectStockValue({symbol: symbol, term: duration.week}, axiosController);

    if (!!!expectResult || !!!expectResult?.data || expectResult.length < 1) {
      return 0;
    }

    let nowValue = expectResult.data?.nowValue;
    let expectValue = expectResult.data?.expectValue;
    let afterMonthExpectValue = expectResult.data?.afterMonthExpectValue;
    let bottomValue = expectResult.data?.bottomValue;
    let topValue = expectResult.data?.topValue;
    let expectRatioValue = expectResult.data?.expectRatioValue;

    // 이동평균 계산 함수
    const calculateMA = (data: any, moveSize: number): (number | string | null)[] => {
      const movingAverages: (number | string | null)[] = [];
      for (let index = 0; index < data.length; index++) {
        if (index < moveSize - 1) {
          // 데이터가 부족한 경우 null로 표시
          movingAverages.push(null);
        } else {
          const moveList = data.slice(index - moveSize + 1, index + 1);
          const sum = moveList.reduce((acc: any, cur: any) => acc + cur.Open, 0);
          movingAverages.push(formatCostValue(sum / moveSize));
        }
      }
      return movingAverages;
    };

    // 각 이동평균 계산
    const ma5 = calculateMA(financeDataResult, 5);
    const ma20 = calculateMA(financeDataResult, 20);
    const ma60 = calculateMA(financeDataResult, 60);

    // 해당 주가의 여러 요인들을 종합하여 각 요인별 점수를 계산하여 일반화한 값 가져오기
    let calcSignalScoreResult = calculateExpectFinanceScore(
      financeDataResult,
      parseFloat(marcap),
      parseFloat(amount),
      parseFloat(topValue),
      parseFloat(bottomValue),
      parseFloat(expectValue),
      parseFloat(expectRatioValue)
    )

    return calculateSignalScore(calcSignalScoreResult, signalScoreWeight);
  }

  /**
   * 분석한 증시정보 데이터 저장
  */
  const onSaveFinanceRankList = async () => {
    if ($page.url.hostname !== 'localhost') {
      toast.error('수행 권환이 없습니다.');
      return;
    }

    if (calcSignalScoreResultList.length < 1) {
      toast.error('저장할 데이터가 없습니다.');
      return;
    }

    const saveResult = await saveFinanceRankList({stock: getSelectedStockModeValue(stockModeList), data: calcSignalScoreResultList}, axiosController);

    if (saveResult.isSuccess) {
      toast.success('저장되었습니다.');
    } else {
      toast.error('오늘 저장된 데이터가 이미 존재합니다.');
    }
  }

  /**
   * 카카오톡으로 보낼 금일 통계 메세지 생성
  */
  const getFinanceResultTodayMessageText = () => {
    const NaverFinanceUrl: string = 'https://finance.naver.com/item/main.naver?code=';
    let financeTodayResultMessageText: string = '';

    if (filteredCalcSignalScoreResultList.length < 1) {
      return financeTodayResultMessageText;
    }

    financeTodayResultMessageText += `[${getTodayDateFormatted()}] TOP 30종목(데이터)\n`;

    let rank: number = 1;
    for (let filteredCalcSignalScoreInfo of filteredCalcSignalScoreResultList.slice(0, 30)) {
      financeTodayResultMessageText += `${rank}등(${filteredCalcSignalScoreInfo?.totalScore}) ${filteredCalcSignalScoreInfo?.name} ${filteredCalcSignalScoreInfo?.close}원\n`;
      rank += 1;
    };

    return financeTodayResultMessageText;
  }

  /**
   * 카카오톡으로 보낼 금일 통계 항목 링크 메세지 생성
  */
  const getFinanceResultTodayLinkMessageText = (rank: number, startRank: number, endRank: number) => {
    const NaverFinanceUrl: string = 'https://finance.naver.com/item/main.naver?code=';
    let financeTodayResultMessageText: string = '';

    if (filteredCalcSignalScoreResultList.length < 1) {
      return financeTodayResultMessageText;
    }

    if (startRank === 0) financeTodayResultMessageText += `[${getTodayDateFormatted()}] TOP 30종목(링크)\n`;

    for (let filteredCalcSignalScoreInfo of filteredCalcSignalScoreResultList.slice(startRank, endRank)) {
      financeTodayResultMessageText += `${rank}등 ${NaverFinanceUrl}${filteredCalcSignalScoreInfo?.code}\n`;
      rank += 1;
    };

    return financeTodayResultMessageText;
  }

  /**
   * 통계 결과 종목 정보 (top 30) 카카오로 전송
  */
  const sendFinanceResultTodayStockInfo = async (accessToken: string) => {
    const result = await sendFinanceResult(kakaoAccessCode, accessToken, getFinanceResultTodayMessageText());

    if (result.isFail === true) {
      toast.error('카카오 Access Code를 재발급 받으세요.');
      return '';
    } else {
      toast.success('카카오 종목 정보 메세지 전달 성공.');
      return result.token;
    }
  }

  /**
   * 통계 결과 종목 링크 정보 (top 30) 카카오로 전송
  */
  const sendFinanceResultTodayStockLink = async (accessToken: string) => {
    let result: any;

    // (1 ~ 15)등
    result = await sendFinanceResult(kakaoAccessCode, accessToken, getFinanceResultTodayLinkMessageText(1, 0, 15));

    if (result.isFail === true) {
      toast.error('종목 링크 정보 (1 ~ 15)등 데이터 전송에 실패했습니다.');
      return '';
    }

    // (16 ~ 30)등
    result = await sendFinanceResult(kakaoAccessCode, accessToken, getFinanceResultTodayLinkMessageText(16, 15, 30));

    if (result.isFail === true) {
      toast.error('종목 링크 정보 (16 ~ 30)등 데이터 전송에 실패했습니다.');
      return '';
    } else {
      toast.success('카카오 링크 정보 메세지 전달 성공.');
      return result.token;
    }
  }

  /**
   * 통계 결과 값 카카오로 전송 (요청 1회 당 1000글자 전송가능)
  */
  const sendFinanceResultByKakaoApi = async () => {
    if (!!!kakaoAccessCode) {
      return;
    }

    await tick();
    // 통계 결과 종목 정보 (top 30) 카카오로 전송
    kakaoAccessToken = await sendFinanceResultTodayStockInfo(kakaoAccessToken);

    if (!!!kakaoAccessToken) {
      return;
    }

    // 통계 결과 종목 링크 정보 (top 30) 카카오로 전송
    kakaoAccessToken = await sendFinanceResultTodayStockLink(kakaoAccessToken);
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
<div class="flex w-full h-full relative bg-gray-600">
  <div class="flex flex-col w-full h-full p-2 space-y-2">
    <!-- 조회 조건 -->
    <div class="flex flex-row h-[30px] items-center w-full space-x-5">
      <div class="flex flex-row space-x-1">
        <p class="font-bold mr-2 text-white">{'📊 지수 항목'}</p>
        {#each stockModeList as stockMode}
          <button
            class="border rounded-md px-1 border-gray-400 {stockMode.isSelected ? 'bg-white' : 'bg-gray-500 text-white'}"
            on:click={() => {
              nowStateText = null;
              stockModeList = setSelectStockModeList(stockModeList, stockMode.value);
            }}
          >
            {stockMode.name}
          </button>
        {/each}
      </div>
      <!-- 조회 기간 설정 -->
      <div class="flex flex-row space-x-1">
        <p class="font-bold mr-2 text-white">{'📆 조회 기간'}</p>
        {#each Object.keys(durationObject) as duration}
          <button class="border rounded-md px-2 border-gray-400 {searchDuration === durationObject[duration] ? 'bg-white' : 'bg-gray-500 text-white'}"
            on:click={() => {
              nowStateText = null;
              selectedDurationKey = duration;
              searchDuration = durationObject[duration];
            }}>
              {duration}
          </button>
        {/each}
      </div>
      <!-- 검색란 -->
      <div class="flex flex-row space-x-1">
        <p class="font-bold mr-2 text-white">{'🔍 종목 검색'}</p>
        <input
          bind:this={searchInputDocument}
          autocomplete="off"
          type="text"
          id="name"
          name="name"
          class="border-gray-400 w-[200px] px-1 rounded-md"
          autofocus={true}
          disabled={loadProgress}
          minlength="4"
          maxlength="8"
          size="10"
          placeholder="종목명/종목코드 검색"
          bind:value={searchStockText}
          on:keypress={async (e) => {
            if (e.key === 'Enter') {
              loadProgress = true;
              filteredCalcSignalScoreResultList = sortBySimilarity(searchStockText, calcSignalScoreResultList.filter((item) => item?.code?.includes(searchStockText) || item?.name?.includes(searchStockText)), ['code', 'name']);
              loadProgress = false;

              await tick();
              searchInputDocument?.focus();
            }
          }}
        />
      </div>
      <div class="flex flex-row space-x-1">
        <button disabled={loadProgress} class="border rounded-md px-1 bg-gray-600 border-gray-400 text-white"
          on:click={async () => {
            if ($page.url.hostname !== 'localhost') {
              toast.error('수행 권환이 없습니다.');
              return;
            }

            axiosController = new AbortController();
            searchStockText = '';
            loadingText = '증시 목록을 가져오는 중입니다...';
            // 카운트 초기화
            count = -1;
            totalStockInfoList = 0;
            calcSignalScoreResultList = [];
            filteredCalcSignalScoreResultList = [];

            await tick();

            loadProgress = true;
            // 목록 조회
            stockInfoList = await setFinanceStockList(getSelectedStockModeValue(stockModeList));

            totalStockInfoList = stockInfoList.length;

            if (totalStockInfoList < 1) {
              loadProgress = false;
              count = -1;
              return;
            }

            stockInfoList = _.sortBy(stockInfoList, (stockInfo) => {
              return parseInt(stockInfo?.Marcap ?? 0);
            })


            // 카운트 시작
            count = 0;

            for (let range = 0; range < Math.ceil(totalStockInfoList / multipleLength); range++) {
              const calcResult = await getCalcSignalScoreResultList(
                stockInfoList.slice(range * multipleLength, (range + 1) * multipleLength),
                calcSignalScoreResultList,
                count
              );

              count = calcResult.rank;
              calcSignalScoreResultList = calcResult.resultList;
            }

            calcSignalScoreResultList = _.orderBy(calcSignalScoreResultList.map((calcSignalScoreResult) => {
                return {...calcSignalScoreResult, totalScore: parseFloat(calcSignalScoreResult.totalScore), trendScore: parseFloat(calcSignalScoreResult.trendScore)}
              }), ['totalScore', 'trendScore'], ['desc', 'desc']).map((item, index) => {
              return {
                ...item,
                rank: index + 1,
              }
            });

            filteredCalcSignalScoreResultList = _.cloneDeep(calcSignalScoreResultList);

            // 카운트 초기화
            count = -1;
            loadProgress = false;
        }}>📈 분석시작</button>
        <button disabled={loadProgress} class="border rounded-md px-1 bg-gray-600 border-gray-400 text-white"
          on:click={onSaveFinanceRankList}
        >💾 저장</button>
      </div>
      <div class="flex grow">
        <KakaoLoginAndSend
          bind:kakaoAccessCode
          isTextDark={false}
          on:onSendFinanceResultByKakaoApiCallback={sendFinanceResultByKakaoApi}
          on:onUpdateKakaoAccessCodeCallback={onUpdateKakaoAccessCode}
        />
      </div>
    </div>
    <div class="flex grow border bg-white">
      <div class="flex grow w-full">
        <div class="tableWrap">
          <table>
            <thead>
              <tr tabindex="0">
                <th style="width: 5%; text-align: center;">Rank</th>
                <th style="width: 10%; text-align: center;">코드</th>
                <th style="width: 20%; text-align: left;">주식명</th>
                <th style="width: 10%; text-align: right;">총점수</th>
                <th style="width: 10%; text-align: right;">추세점수</th>
                <th style="width: 10%; text-align: right;">규모점수</th>
                <th style="width: 10%; text-align: right;">현재가</th>
                <th style="width: 25%; text-align: center;">시가총액</th>
              </tr>
            </thead>
            <tbody style="height: {innerHeight - 90}px">
              {#if filteredCalcSignalScoreResultList.length > 0 && loadProgress === false}
                {#each filteredCalcSignalScoreResultList as calcSignalScoreResultInfo}
                  <tr
                    on:click={() => {
                      singleChartInfo = {
                        title: calcSignalScoreResultInfo.name,
                        searchDuration: searchDuration,
                        chartMode: calcSignalScoreResultInfo.code,
                        chartKey: calcSignalScoreResultInfo.code,
                        detailInfo: calcSignalScoreResultInfo
                      }

                      isSingleMode = true;
                    }}
                  >
                    <td style="width: 5%; text-align: center;">{calcSignalScoreResultInfo.rank}</td>
                    <td style="width: 10%; text-align: center;">{calcSignalScoreResultInfo.code}</td>
                    <td style="width: 20%; text-align: left;">{calcSignalScoreResultInfo.name}</td>
                    <td style="width: 10%; text-align: right;">{calcSignalScoreResultInfo?.totalScore ?? '-'}</td>
                    <td style="width: 10%; text-align: right;">{calcSignalScoreResultInfo?.trendScore ?? '-'}</td>
                    <td style="width: 10%; text-align: right;">{calcSignalScoreResultInfo?.marcapScore ?? '-'}</td>
                    <td style="width: 10%; text-align: right;">{`${formatIncludeComma(calcSignalScoreResultInfo?.close) ?? '-'} ₩`}</td>
                    <td style="width: 25%; text-align: right;">{`${formatIncludeComma(calcSignalScoreResultInfo?.marcap) ?? '-'} ₩`}</td>
                  </tr>
                {/each}
              {:else if loadProgress}
                {#if count < 0}
                  <div class="flex w-full h-full justify-center items-center font-bold text-gray">
                    <ProgressCircle
                      size={100}
                      thickness={10}
                      isLarge={true}
                      text={loadingText}
                    />
                  </div>
                {:else}
                  <div class="flex flex-col w-full h-full justify-center items-center font-bold text-gray">
                    <p>{totalStockInfoList}개의 주식 분석중입니다.</p>
                    <DownLoadProgressBar
                      min={0}
                      max={totalStockInfoList}
                      nowCount={count}
                    />
                  </div>
                {/if}
              {:else}
                <p class="flex w-full h-full justify-center items-center font-bold text-gray">
                  {'목록이 없습니다.'}
                </p>
              {/if}
            </tbody>
          </table>
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