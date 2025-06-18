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
        totalScore: stockInfo?.Marcap <= 0 ? scoreResult : scoreResult + parseFloat((selfNormalize(rank, 1, totalStockInfoList) * 50).toFixed(2))
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

    return result.data.map((item: any) => {
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
<div class="flex w-full h-full relative bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-900 overflow-hidden">
  <!-- 배경 데코레이션 -->
  <div class="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,_rgba(59,130,246,0.1)_1px,_transparent_0)] bg-[size:32px_32px] pointer-events-none"></div>
  <div class="absolute top-0 left-0 w-96 h-96 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2 animate-pulse"></div>
  <div class="absolute bottom-0 right-0 w-96 h-96 bg-gradient-to-r from-cyan-500/20 to-teal-500/20 rounded-full blur-3xl translate-x-1/2 translate-y-1/2 animate-pulse"></div>
  
  <div class="flex flex-col w-full h-full p-4 space-y-4 relative z-10">
    <!-- 조회 조건 -->
    <div class="flex flex-wrap gap-4 items-center bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/20 shadow-xl">
      <!-- 지수 항목 -->
      <div class="flex items-center space-x-3">
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center shadow-lg">
            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
            </svg>
          </div>
          <span class="font-bold text-white">지수 항목</span>
        </div>
        <div class="flex flex-wrap gap-2">
          {#each stockModeList as stockMode}
            <button
              class="h-10 px-3 rounded-lg font-medium text-sm transition-all duration-200 shadow-md hover:shadow-lg {stockMode.isSelected ? 'bg-white text-gray-800 shadow-lg' : 'bg-white/20 backdrop-blur-sm text-white hover:bg-white/30'}"
              on:click={() => {
                nowStateText = null;
                stockModeList = setSelectStockModeList(stockModeList, stockMode.value);
              }}
            >
              {stockMode.name}
            </button>
          {/each}
        </div>
      </div>   
      <!-- 조회 기간 설정 -->
      <div class="flex items-center space-x-3">
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
            </svg>
          </div>
          <span class="font-bold text-white">조회 기간</span>
        </div>
        <div class="flex flex-wrap gap-2">
          {#each Object.keys(durationObject) as duration}
            <button 
              class="h-10 px-3 rounded-lg font-medium text-sm transition-all duration-200 shadow-md hover:shadow-lg {searchDuration === durationObject[duration] ? 'bg-white text-gray-800 shadow-lg' : 'bg-white/20 backdrop-blur-sm text-white hover:bg-white/30'}"
              on:click={() => {
                nowStateText = null;
                selectedDurationKey = duration;
                searchDuration = durationObject[duration];
              }}
            >
              {duration}
            </button>
          {/each}
        </div>
      </div>
      <!-- 검색란 -->
      <div class="flex items-center space-x-3">
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-600 rounded-xl flex items-center justify-center shadow-lg">
            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
          </div>
          <span class="font-bold text-white">종목 검색</span>
        </div>
        <input
          bind:this={searchInputDocument}
          type="text"
          autocomplete="off"
          id="name"
          name="name"
          class="h-10 px-3 rounded-lg bg-white/90 backdrop-blur-sm border border-white/30 focus:border-purple-400 focus:ring-2 focus:ring-purple-400/50 outline-none transition-all duration-200 text-gray-800 placeholder-gray-500 shadow-md hover:shadow-lg w-48"
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
              const filteredList = calcSignalScoreResultList.filter((item) => 
                item?.code?.includes(searchStockText) || item?.name?.includes(searchStockText)
              );
              filteredCalcSignalScoreResultList = sortBySimilarity(searchStockText, filteredList, ['code', 'name']);
              loadProgress = false;

              await tick();
              searchInputDocument?.focus();
            }
          }}
        />
      </div>    
      <!-- 액션 버튼들 -->
      <div class="flex items-center space-x-2 ml-auto">
        <button 
          disabled={loadProgress} 
          class="h-10 flex items-center space-x-2 px-4 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 disabled:from-gray-400 disabled:to-gray-500 text-white rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl disabled:cursor-not-allowed"
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
            });


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
        }}>
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
          </svg>
          <span>분석시작</span>
        </button>
        <button 
          disabled={loadProgress} 
          class="h-10 flex items-center space-x-2 px-4 bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-500 text-white rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl disabled:cursor-not-allowed"
          on:click={onSaveFinanceRankList}
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path>
          </svg>
          <span>저장</span>
        </button>
        <div class="ml-4">
          <KakaoLoginAndSend
            bind:kakaoAccessCode
            isTextDark={false}
            on:onSendFinanceResultByKakaoApiCallback={sendFinanceResultByKakaoApi}
            on:onUpdateKakaoAccessCodeCallback={onUpdateKakaoAccessCode}
          />
        </div>
      </div>
    </div>
    <!-- 데이터 테이블 -->
    <div class="flex-1 bg-white/95 backdrop-blur-lg rounded-2xl shadow-2xl overflow-hidden">
      <div class="tableWrap h-full">
        <table class="w-full h-full">
          <thead class="bg-gradient-to-r from-gray-100 to-gray-200 border-b border-gray-300/50">
            <tr>
              <th class="text-gray-700 font-semibold py-2 px-3 text-center" style="width: 5%;">Rank</th>
              <th class="text-gray-700 font-semibold py-2 px-3 text-center" style="width: 10%;">코드</th>
              <th class="text-gray-700 font-semibold py-2 px-3 text-left" style="width: 20%;">주식명</th>
              <th class="text-gray-700 font-semibold py-2 px-3 text-right" style="width: 10%;">총점수</th>
              <th class="text-gray-700 font-semibold py-2 px-3 text-right" style="width: 10%;">추세점수</th>
              <th class="text-gray-700 font-semibold py-2 px-3 text-right" style="width: 10%;">규모점수</th>
              <th class="text-gray-700 font-semibold py-2 px-3 text-right" style="width: 10%;">현재가</th>
              <th class="text-gray-700 font-semibold py-2 px-3 text-right" style="width: 25%;">시가총액</th>
            </tr>
          </thead>
          <tbody style="height: {innerHeight - 180}px" class="divide-y divide-gray-200/30">
            {#if filteredCalcSignalScoreResultList.length > 0 && loadProgress === false}
              {#each filteredCalcSignalScoreResultList as calcSignalScoreResultInfo, index}
                <tr
                  class="hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 transition-all duration-200 cursor-pointer group {index % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}"
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
                  <td class="py-2 px-3 text-center text-gray-700 font-medium" style="width: 5%;">{calcSignalScoreResultInfo.rank}</td>
                  <td class="py-2 px-3 text-center text-gray-700 font-mono text-sm" style="width: 10%;">{calcSignalScoreResultInfo.code}</td>
                  <td class="py-2 px-3 text-left text-gray-800 font-semibold" style="width: 20%;">{calcSignalScoreResultInfo.name}</td>
                  <td class="py-2 px-3 text-right text-gray-700 font-medium" style="width: 10%;">{calcSignalScoreResultInfo?.totalScore ?? '-'}</td>
                  <td class="py-2 px-3 text-right text-gray-700 font-medium" style="width: 10%;">{calcSignalScoreResultInfo?.trendScore ?? '-'}</td>
                  <td class="py-2 px-3 text-right text-gray-700 font-medium" style="width: 10%;">{calcSignalScoreResultInfo?.marcapScore ?? '-'}</td>
                  <td class="py-2 px-3 text-right text-gray-700 font-medium" style="width: 10%;">{`${formatIncludeComma(calcSignalScoreResultInfo?.close) ?? '-'} ₩`}</td>
                  <td class="py-2 px-3 text-right text-gray-700 font-medium" style="width: 25%;">{`${formatIncludeComma(calcSignalScoreResultInfo?.marcap) ?? '-'} ₩`}</td>
                </tr>
              {/each}
            {:else if loadProgress}
              <tr>
                <td colspan="8" class="relative" style="height: {innerHeight - 180}px;">
                  <div class="absolute inset-0 flex justify-center items-center">
                    {#if count < 0}
                      <ProgressCircle
                        size={100}
                        thickness={10}
                        isLarge={true}
                        text={loadingText}
                      />
                    {:else}
                      <div class="flex flex-col items-center space-y-4">
                        <p class="text-gray-700 font-semibold text-lg">{totalStockInfoList}개의 주식 분석중입니다.</p>
                        <DownLoadProgressBar
                          min={0}
                          max={totalStockInfoList}
                          nowCount={count}
                        />
                      </div>
                    {/if}
                  </div>
                </td>
              </tr>
            {:else}
              <tr class="relative">
                <td colspan="8" class="relative" style="height: {innerHeight - 180}px;">
                  <div class="absolute inset-0 flex flex-col justify-center items-center space-y-4">
                    <div class="w-16 h-16 bg-gray-300 rounded-2xl flex items-center justify-center">
                      <svg class="w-8 h-8 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                      </svg>
                    </div>
                    <p class="text-gray-600 font-semibold text-lg">목록이 없습니다.</p>
                  </div>
                </td>
              </tr>
            {/if}
          </tbody>
        </table>
      </div>
    </div>
  </div>
  
  {#if isSingleMode && singleChartInfo}
    <div class="absolute inset-0 z-50 bg-black/50 backdrop-blur-sm">
      <SingleChartBasic
        {singleChartInfo}
        on:closeSingleChartModeCallback={() => {
          isSingleMode = false;
        }}
      />
    </div>
  {/if}
</div>

<style>
	.tableWrap {
		width: 100%;
		height: 100%;
		overflow: hidden;
	}
	
	table {
		width: 100%;
		height: 100%;
		table-layout: fixed;
	}
	
	thead {
		display: table;
		table-layout: fixed;
		width: 100%;
	}
	
	tbody {
		width: 100%;
		display: block;
		overflow-y: auto;
		overflow-x: hidden;
	}
	
	tr {
		display: table;
		width: 100%;
		table-layout: fixed;
	}

  /* 현대적인 스크롤바 */
  tbody::-webkit-scrollbar {
    width: 8px;
  }

  tbody::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.1);
    border-radius: 10px;
  }

  tbody::-webkit-scrollbar-thumb {
    background: linear-gradient(45deg, rgba(59, 130, 246, 0.6), rgba(99, 102, 241, 0.6));
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  tbody::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(45deg, rgba(59, 130, 246, 0.8), rgba(99, 102, 241, 0.8));
  }

  /* Firefox용 스크롤바 */
  tbody {
    scrollbar-width: thin;
    scrollbar-color: rgba(59, 130, 246, 0.6) rgba(0, 0, 0, 0.1);
  }

  /* 애니메이션 */
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .animate-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }
</style> 