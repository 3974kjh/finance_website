<script lang="ts">
  import { getFinanceStockList, getExpectStockValue, saveFinanceRankList, getTodayAnalyze } from '$lib/api-connector/FinanceApi';
  import type { StockType } from '$lib/types';
  import { calculateRatio, formatCostValue, formatIncludeComma, sortBySimilarity, getTodayDateFormatted } from '$lib/utils/CommonHelper';
  import { getFinanceDataListByChartMode, calculateExpectFinanceScore, selfNormalize, SingleChartBasic, sendFinanceResult, makeStockFinalReportText } from '$lib/main';
  import { onMount, onDestroy, tick } from 'svelte';
  import { browser } from '$app/environment';
  import { DownLoadProgressBar, ProgressCircle, KakaoLoginAndSend } from '$lib/component';
  import { cancelRequest } from "$lib/axios-provider/AxiosProvider";
  import { page } from '$app/stores';
  import toast from 'svelte-french-toast';
  import { slide, fade, fly } from 'svelte/transition';
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

  // 시작 시간
  let startAnalyzeTime: string | null = null;

  // 결과 목록
  let calcSignalScoreResultList: any = [];
  let filteredCalcSignalScoreResultList: any = [];
  let analyzeDate: string | null = null;

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

  // 골든크로스 필터 옵션 (토글 방식)
  let goldenCrossFilterList: Array<{name: string, value: string, isSelected: boolean}> = [
    { name: '골든크로스 돌파', value: 'OVER', isSelected: false },
    { name: '골든크로스 근접', value: 'NEAR', isSelected: false },
    { name: '볼린저밴드 하단', value: 'LOWER_BAND', isSelected: false },
    { name: '우수 종합점수', value: 'GOOD_SCORE', isSelected: false },
  ];

  // 매수등급 필터 옵션
  let stockBuyLevelOptions = [
    { 
      name: '전체', 
      value: 'ALL', 
      rank: 'ALL', 
      description: '모든 등급 종목 표시', 
      bgColor: 'bg-gradient-to-r from-gray-500/80 to-gray-600/80',
      borderColor: 'border-gray-400/30',
      textColor: 'text-white'
    },
    { 
      name: 'S+ 등급', 
      value: 'S+', 
      rank: 'S+', 
      description: '최우선 투자대상 · 강력한 상승신호', 
      bgColor: 'bg-gradient-to-r from-purple-500/80 to-pink-500/80',
      borderColor: 'border-purple-400/30',
      textColor: 'text-purple-200'
    },
    { 
      name: 'S 등급', 
      value: 'S', 
      rank: 'S', 
      description: '적극 매수권장 · 우수한 기술적 신호', 
      bgColor: 'bg-gradient-to-r from-blue-500/80 to-indigo-500/80',
      borderColor: 'border-blue-400/30',
      textColor: 'text-blue-200'
    },
    { 
      name: 'A+ 등급', 
      value: 'A+', 
      rank: 'A+', 
      description: '매수 권장 · 양호한 상승 추세', 
      bgColor: 'bg-gradient-to-r from-emerald-500/80 to-teal-500/80',
      borderColor: 'border-emerald-400/30',
      textColor: 'text-emerald-200'
    },
    { 
      name: 'A 등급', 
      value: 'A', 
      rank: 'A', 
      description: '관심 종목 · 매수 검토 권장', 
      bgColor: 'bg-gradient-to-r from-green-500/80 to-lime-500/80',
      borderColor: 'border-green-400/30',
      textColor: 'text-green-200'
    },
    { 
      name: 'B 등급', 
      value: 'B', 
      rank: 'B', 
      description: '투자 주의 · 추가 분석 필요', 
      bgColor: 'bg-gradient-to-r from-yellow-500/80 to-orange-500/80',
      borderColor: 'border-yellow-400/30',
      textColor: 'text-yellow-200'
    },
    { 
      name: 'C 등급', 
      value: 'C', 
      rank: 'C', 
      description: '투자 비권장 · 고위험 종목', 
      bgColor: 'bg-gradient-to-r from-red-500/80 to-rose-500/80',
      borderColor: 'border-red-400/30',
      textColor: 'text-red-200'
    }
  ];
  let selectedStockBuyLevel: string = 'ALL';
  let isDropdownOpen: boolean = false;
  let dropdownButton: HTMLButtonElement;
  let dropdownPosition = { top: 0, left: 0, width: 0 };

  // 드롭다운 위치 계산
  const updateDropdownPosition = () => {
    if (dropdownButton) {
      const rect = dropdownButton.getBoundingClientRect();
      dropdownPosition = {
        top: rect.bottom + 8,
        left: rect.left,
        width: rect.width
      };
    }
  };

  // 페이지네이션 관련 변수
  let currentPage: number = 0;
  const itemsPerPage: number = 50; // 페이지당 50개 항목

  // 페이지네이션 표시 여부에 따른 테이블 높이 계산
  $: showPagination = filteredCalcSignalScoreResultList.length > itemsPerPage;
  $: showSearchStatus = (searchStockText.trim() !== '' || hasGoldenCrossFilter || selectedStockBuyLevel !== 'ALL') && calcSignalScoreResultList.length > 0;
  $: tableHeight = (() => {
    // innerHeight가 0이거나 너무 작으면 기본값 사용
    const windowHeight = innerHeight > 0 ? innerHeight : 800;
    let baseHeight = windowHeight - 190; // 기본 높이 (헤더, 조건 영역 등)
    if (showPagination) baseHeight -= 45; // 페이지네이션 영역 높이
    if (showSearchStatus) baseHeight -= 45; // 검색 상태 표시 높이
    return Math.max(400, baseHeight); // 최소 높이를 400px로 증가
  })();

  // 골든크로스 필터 선택값 가져오기 (배열로 반환)
  $: selectedGoldenCrossFilters = goldenCrossFilterList.filter(item => item.isSelected).map(item => item.value);
  $: hasGoldenCrossFilter = selectedGoldenCrossFilters.length > 0;

  // 실시간 검색 및 필터링
  $: filteredCalcSignalScoreResultList = (() => {
    let filtered = calcSignalScoreResultList;
    
    // 골든크로스 필터 적용 (AND 조건: 선택된 모든 조건을 만족해야 표시)
    if (hasGoldenCrossFilter) {
      filtered = filtered.filter((item: any) => {
        const hasOver = selectedGoldenCrossFilters.includes('OVER');
        const hasNear = selectedGoldenCrossFilters.includes('NEAR');
        const hasLowerBand = selectedGoldenCrossFilters.includes('LOWER_BAND');
        const hasGoodScore = selectedGoldenCrossFilters.includes('GOOD_SCORE');
        
        // 선택된 조건들을 배열로 수집
        const conditions: boolean[] = [];
        
        if (hasOver) {
          conditions.push(item.isOverGoldenCross === true);
        }
        
        if (hasNear) {
          conditions.push(item.isNearGoldenCross === true);
        }
        
        if (hasLowerBand) {
          conditions.push(item.isNearLowerBand === true);
        }
        
        if (hasGoodScore) {
          conditions.push(item.isGoodTotalScore === true);
        }
        
        // 모든 선택된 조건이 true여야 함 (AND 조건)
        return conditions.length > 0 && conditions.every(condition => condition === true);
      });
    }
    
    // 매수등급 필터 적용
    if (selectedStockBuyLevel !== 'ALL') {
      filtered = filtered.filter((item: any) => 
        item.stockBuyLevel === selectedStockBuyLevel
      );
    }
    
    // 검색 필터 적용
    if (searchStockText.trim() !== '') {
      filtered = filtered.filter((item: any) => 
        item.name.toLowerCase().includes(searchStockText.toLowerCase()) || 
        item.code.toLowerCase().includes(searchStockText.toLowerCase())
      );
    }
    
    return filtered;
  })();

  // 페이지네이션 데이터
  $: paginatedData = filteredCalcSignalScoreResultList.slice(
    currentPage * itemsPerPage,
    (currentPage + 1) * itemsPerPage
  );

  // 페이지 수 계산
  $: maxPage = Math.ceil(filteredCalcSignalScoreResultList.length / itemsPerPage);

  // 검색 또는 필터 변경 시 첫 페이지로 이동
  $: if (searchStockText || selectedGoldenCrossFilters || selectedStockBuyLevel) {
    currentPage = 0;
  }

  // 선택된 매수등급 옵션
  $: selectedStockBuyLevelOption = stockBuyLevelOptions.find(opt => opt.value === selectedStockBuyLevel);

  // 테이블 상단으로 스크롤
  const scrollToTableTop = () => {
    try {
      const tbody = document.querySelector('.elegant-scrollbar');
      if (tbody) {
        tbody.scrollTop = 0;
      }
    } catch (error) {
      console.error('스크롤 에러:', error);
    }
  }

  onMount(async () => {
    if (!!!sessionStorage) {
      return;
    }

    // innerHeight가 설정될 때까지 잠시 기다림
    await tick();
    if (innerHeight === 0) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    count = -1;
    loadingText = '오늘 분석 데이터 조회 중...';
    loadProgress = true;

    kakaoAccessCode = sessionStorage.getItem('kakaoAccessCode') ?? '';
    kakaoAccessToken = sessionStorage.getItem('kakaoAccessToken') ?? '';

    startAnalyzeTime = sessionStorage.getItem('startAnalyzeTime') || null;

    const getSelectedDurationKey = sessionStorage.getItem('selectedDurationKey');
    const getSelectedStockMode = sessionStorage.getItem('selectedStockMode');
    const getCalcResultList = await getTodayAnalyze();

    searchDuration = !!getSelectedDurationKey ? durationObject[getSelectedDurationKey] : durationObject['1 YEAR'];
    stockModeList = !!getSelectedStockMode ? setSelectStockModeList(stockModeList, JSON.parse(getSelectedStockMode)) : stockModeList;
    calcSignalScoreResultList = !!getCalcResultList?.data ? getCalcResultList.data : [];
    analyzeDate = getCalcResultList?.date || null;

    filteredCalcSignalScoreResultList = _.cloneDeep(calcSignalScoreResultList);
    startAnalyzeTime = null;

    sessionStorage.removeItem('selectedDurationKey');
    sessionStorage.removeItem('selectedStockMode');

    loadProgress = false;
    count = 0;

    // 이벤트 리스너 추가
    if (browser) {
      document.addEventListener('click', handleClickOutside);
      window.addEventListener('scroll', handleScroll);
    }
  })

  onDestroy(() => {
    if (typeof document !== 'undefined') {
      cancelRequest(axiosController);
      sessionStorage.setItem('startAnalyzeTime', startAnalyzeTime ?? '');

      sessionStorage.setItem('kakaoAccessCode', kakaoAccessCode);
      sessionStorage.setItem('kakaoAccessToken', kakaoAccessToken);

      sessionStorage.setItem('selectedDurationKey', selectedDurationKey);
      sessionStorage.setItem('selectedStockMode', JSON.stringify(getSelectedStockModeValue(stockModeList)));
      
      // 이벤트 리스너 제거
      document.removeEventListener('click', handleClickOutside);
      window.removeEventListener('scroll', handleScroll);
    }
  });

  /**
   * 증시 분석
  */
  const getCalcSignalScoreResultList = async (stockList: any, calcScoreResultList: any, rank: number) => {
    let promiseFinanceDataList: any = [];

    for (let stockInfo of stockList) {
      const symbol = stockInfo?.Code ?? stockInfo?.Symbol;

      if (!!!symbol) {
        continue;
      }

      // 해당 주식의 상세 값 조회 후 점수 계산
      const promiseData = getCalculateExpectFinanceScore(stockList, symbol, searchDuration);
      promiseFinanceDataList.push(promiseData);
    }

    const multiAwaitResult = await Promise.all(promiseFinanceDataList);

    let index: number = 0;

    stockList = [...stockList]

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

      if (!!!scoreResult?.signalScore || scoreResult.signalScore <= 0) {
        continue;
      }

      // 추세신호 점수
      const trendScore = parseFloat(scoreResult.signalScore.toFixed(2));
      // 마켓 평가 점수
      const marcapScore = marcap <= 0 ? 0 : parseFloat((selfNormalize(rank, 1, totalStockInfoList) * 50).toFixed(2));

      // 종목 최종 결과 텍스트 생성
      const stockBuyLevel = makeStockFinalReportText(stockInfo.title, {
        isOverGoldenCross: scoreResult.isOverGoldenCross,
        isNearGoldenCross: scoreResult.isNearGoldenCross,
        generalizedPricePosition: scoreResult.bandPosition,
        stockFinanceScore: trendScore
      })?.stockBuyLevel ?? 'C';

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
        marcap: marcap,
        amount: amount,
        trendScore: trendScore,
        marcapScore: marcapScore,
        totalScore: trendScore + marcapScore,
        isOverGoldenCross: scoreResult.isOverGoldenCross,
        isNearGoldenCross: scoreResult.isNearGoldenCross,
        isNearLowerBand: scoreResult.isNearLowerBand,
        isGoodTotalScore: trendScore > 50 && marcapScore >= 40,
        stockBuyLevel: stockBuyLevel
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

  // 토글 방식으로 변경: 선택/해제를 토글
  const toggleGoldenCrossFilter = (list: any, filterValue: string) => {
    if (list.length < 1) {
      return [];
    }

    return list.map((item: any) => {
      if (item.value === filterValue) {
        return {
          ...item,
          isSelected: !item.isSelected // 토글
        }
      } else {
        return item;
      }
    })
  }

  // 모든 필터 초기화
  const resetGoldenCrossFilters = (list: any) => {
    return list.map((item: any) => ({
      ...item,
      isSelected: false
    }));
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
  const getCalculateExpectFinanceScore = async (stockList: any, symbol: string, duration: {month: number, week: number}) => {
    const financeDataResult = await getFinanceDataListByChartMode(symbol, duration.month, true, axiosController);

    if (financeDataResult.length < 1) {
      return {
        isOverGoldenCross: false,
        isNearGoldenCross: false,
        isNearLowerBand: false,
        bandPosition: 0,
        signalScore: 0
      };
    }

    const marketCap = parseFloat((financeDataResult[financeDataResult.length - 1]?.High * financeDataResult[financeDataResult.length - 1]?.Volume).toFixed(2));
    const amount = parseFloat((financeDataResult[financeDataResult.length - 1]?.Close * financeDataResult[financeDataResult.length - 1]?.Volume).toFixed(2));

    const findStockInfoIndex = stockList.findIndex((item: any) => item.Code === symbol || item.Symbol === symbol);

    stockList[findStockInfoIndex].Marcap = marketCap;
    stockList[findStockInfoIndex].Amount = amount;
    
    const expectResult = await getExpectStockValue({symbol: symbol, term: duration.week}, axiosController);

    if (!!!expectResult || !!!expectResult?.data || expectResult.length < 1) {
      return {
        isOverGoldenCross: false,
        isNearGoldenCross: false,
        isNearLowerBand: false,
        bandPosition: 0,
        signalScore: 0
      };
    }

    let expectValue = expectResult.data?.expectValue;
    let bottomValue = expectResult.data?.bottomValue;
    let topValue = expectResult.data?.topValue;
    let expectRatioValue = expectResult.data?.expectRatioValue;

    // 해당 주가의 여러 요인들을 종합하여 각 요인별 점수를 계산하여 일반화한 값 가져오기
    let calcSignalScoreResult = calculateExpectFinanceScore(
      financeDataResult,
      marketCap,
      amount,
      parseFloat(topValue),
      parseFloat(bottomValue),
      parseFloat(expectValue),
      parseFloat(expectRatioValue)
    )

    return {
      isOverGoldenCross: calcSignalScoreResult.isOverGoldenCross,
      isNearGoldenCross: calcSignalScoreResult.isNearGoldenCross,
      isNearLowerBand: calcSignalScoreResult.isNearLowerBand,
      bandPosition: calcSignalScoreResult.bandPosition,
      signalScore: calculateSignalScore(calcSignalScoreResult, signalScoreWeight)
    };
  }

  /**
   * 분석한 증시정보 데이터 저장
  */
  const onSaveFinanceRankList = async () => {
    if (calcSignalScoreResultList.length < 1) {
      toast.error('저장할 데이터가 없습니다.');
      return;
    }

    if (
      !!!startAnalyzeTime ||
      startAnalyzeTime === new Date().toISOString()
    ) {
      toast.error('분석 시작 시간이 존재하지 않습니다.');
      return;
    }

    // 분석 시작 시간이 오후 3시 30분 이전인지 확인
    const analyzeDate = new Date(startAnalyzeTime);
    const targetTime = new Date(analyzeDate);
    targetTime.setHours(15, 30, 0, 0); // 15:30:00.000

    if (analyzeDate < targetTime) {
      toast.error('오후 3시 30분 이후에만 저장할 수 있습니다.');
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

  let isShowConditionSetting: boolean = false;

  // 드롭다운 외부 클릭 감지
  const handleClickOutside = (event: MouseEvent) => {
    const target = event.target as Element;
    if (!target.closest('.custom-dropdown')) {
      isDropdownOpen = false;
    }
  };

  // 드롭다운 옵션 선택
  const selectBuyLevelOption = (value: string) => {
    selectedStockBuyLevel = value;
    isDropdownOpen = false;
  };

  // 드롭다운 토글
  const toggleDropdown = () => {
    if (!isDropdownOpen) {
      updateDropdownPosition();
    }
    isDropdownOpen = !isDropdownOpen;
  };

  // 스크롤 시 드롭다운 닫기
  const handleScroll = () => {
    if (isDropdownOpen) {
      isDropdownOpen = false;
    }
  };

  // 키보드 네비게이션
  const handleKeydown = (event: KeyboardEvent) => {
    if (event.key === 'Escape') {
      isDropdownOpen = false;
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      isDropdownOpen = !isDropdownOpen;
    }
  };
</script>

<svelte:head>
	<title>데이터 분석 - FinanceChart</title>
</svelte:head>
<svelte:window bind:innerHeight on:click={handleClickOutside}/>
<div class="flex w-full h-full relative bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-900 overflow-hidden">
  <!-- 배경 데코레이션 -->
  <div class="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,_rgba(59,130,246,0.1)_1px,_transparent_0)] bg-[size:32px_32px] pointer-events-none"></div>
  <div class="absolute top-0 left-0 w-96 h-96 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2 animate-pulse"></div>
  <div class="absolute bottom-0 right-0 w-96 h-96 bg-gradient-to-r from-cyan-500/20 to-teal-500/20 rounded-full blur-3xl translate-x-1/2 translate-y-1/2 animate-pulse"></div>
  
  {#if isShowConditionSetting}
    <div 
      class="flex flex-wrap absolute top-[80px] right-0 w-[100%] h-[80px] bg-white/10 backdrop-blur-md p-4 border border-white/20 shadow-xl gap-4"
      style="z-index: 100;"
      transition:slide
    >
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
      <!-- 액션 버튼들 -->
      <div class="flex items-center space-x-2 ml-auto">
        <button 
          disabled={loadProgress} 
          class="h-10 flex items-center space-x-2 px-4 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 disabled:from-gray-400 disabled:to-gray-500 text-white rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl disabled:cursor-not-allowed"
          on:click={async () => {
            const nowDate = new Date();

            // 분석일자 변경
            analyzeDate = `${nowDate.getFullYear()}-${nowDate.getMonth() + 1}-${nowDate.getDate()}`;

            axiosController = new AbortController();
            searchStockText = '';
            goldenCrossFilterList = resetGoldenCrossFilters(goldenCrossFilterList);
            selectedStockBuyLevel = 'ALL';
            loadingText = '증시 목록을 가져오는 중입니다...';
            // 카운트 초기화
            count = -1;
            totalStockInfoList = 0;
            calcSignalScoreResultList = [];
            startAnalyzeTime = null;

            // 페이지 초기화
            currentPage = 0;

            await tick();

            loadProgress = true;
            // 목록 조회
            stockInfoList = await setFinanceStockList(getSelectedStockModeValue(stockModeList));

            totalStockInfoList = stockInfoList.length;

            if (totalStockInfoList < 1) {
              loadProgress = false;
              count = -1;
              analyzeDate = '';
              return;
            }

            stockInfoList = _.sortBy(stockInfoList, (stockInfo) => {
              return parseInt(stockInfo?.Marcap ?? 0);
            });

            // 카운트 시작
            count = 0;

            startAnalyzeTime = new Date().toISOString();

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
      </div>
    </div>
  {/if}
  <div class="flex flex-col w-full h-full p-4 space-y-4 relative z-10">
    <!-- 조회 조건 -->
    <div class="flex flex-wrap gap-4 items-center bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/20 shadow-xl">
      <!-- 분석 날짜 표시 -->
      {#if analyzeDate}
        <div class="flex items-center space-x-3">
          <div class="flex items-center space-x-2">
            <div class="w-8 h-8 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center shadow-lg">
              <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
              </svg>
            </div>
            <span class="font-bold text-white">분석 기준일</span>
          </div>
          <div class="px-3 py-1 bg-emerald-500/20 border border-emerald-400/30 rounded-lg text-emerald-200 text-sm font-medium shadow-sm">
            {analyzeDate}
          </div>
        </div>
      {/if}
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
        <div class="relative">
          <input
            bind:this={searchInputDocument}
            type="text"
            autocomplete="off"
            id="name"
            name="name"
            class="h-10 px-3 pr-10 rounded-lg bg-white/90 backdrop-blur-sm border border-white/30 focus:border-purple-400 focus:ring-2 focus:ring-purple-400/50 outline-none transition-all duration-200 text-gray-800 placeholder-gray-500 shadow-md hover:shadow-lg w-60"
            autofocus={true}
            disabled={loadProgress}
            minlength="4"
            maxlength="8"
            size="10"
            placeholder="종목명/종목코드 검색"
            bind:value={searchStockText}
            on:keypress={async (e) => {
              if (e.key === 'Enter') {
                await tick();
                searchInputDocument?.focus();
              }
            }}
          />
          {#if searchStockText.trim() !== ''}
            <button
              class="absolute right-2 top-1/2 -translate-y-1/2 w-6 h-6 bg-gray-500/20 hover:bg-gray-500/40 rounded-full flex items-center justify-center transition-all duration-200 group"
              on:click={() => {
                searchStockText = '';
                searchInputDocument?.focus();
              }}
              title="검색어 지우기"
            >
              <svg class="w-3 h-3 text-gray-600 group-hover:text-gray-800 transition-colors duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          {/if}
        </div>
      </div>
      <!-- 골든크로스 필터 -->
      <div class="flex items-center space-x-3">
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 bg-gradient-to-r from-amber-500 to-orange-600 rounded-xl flex items-center justify-center shadow-lg">
            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12"></path>
            </svg>
          </div>
          <span class="font-bold text-white">골든크로스</span>
        </div>
        <div class="flex flex-wrap gap-2">
          {#each goldenCrossFilterList as filter}
            <button
              class="relative h-10 px-3 rounded-lg font-medium text-sm transition-all duration-200 shadow-md hover:shadow-lg {filter.isSelected ? 'bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-lg ring-2 ring-white/50' : 'bg-white/20 backdrop-blur-sm text-white hover:bg-white/30'}"
              on:click={() => {
                goldenCrossFilterList = toggleGoldenCrossFilter(goldenCrossFilterList, filter.value);
              }}
            >
              <span class="flex items-center space-x-1">
                {#if filter.isSelected}
                  <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                  </svg>
                {/if}
                <span>{filter.name}</span>
              </span>
            </button>
          {/each}
          {#if hasGoldenCrossFilter}
            <button
              class="h-10 w-10 rounded-lg transition-all duration-200 bg-white/10 hover:bg-white/20 border border-white/20 hover:border-white/30 text-white/70 hover:text-white shadow-sm hover:shadow-md backdrop-blur-sm group flex items-center justify-center"
              on:click={() => {
                goldenCrossFilterList = resetGoldenCrossFilters(goldenCrossFilterList);
              }}
              title="필터 초기화"
            >
              <svg class="w-4 h-4 transition-transform duration-200 group-hover:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
            </button>
          {/if}
        </div>
      </div>
      <!-- 매수등급 필터 -->
      <div class="flex items-center space-x-3">
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg">
            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"></path>
            </svg>
          </div>
          <span class="font-bold text-white">매수등급</span>
        </div>
        <div class="relative custom-dropdown">
          <!-- 선택된 항목 표시 버튼 -->
          <button
            bind:this={dropdownButton}
            type="button"
            class="h-10 px-4 pr-3 rounded-lg bg-white/10 backdrop-blur-md border border-white/20 focus:border-green-400/70 focus:ring-2 focus:ring-green-400/30 outline-none transition-all duration-200 text-white font-medium shadow-lg hover:shadow-xl hover:bg-white/15 cursor-pointer w-48 max-w-xs flex items-center justify-between"
            on:click={toggleDropdown}
            on:keydown={handleKeydown}
            aria-haspopup="listbox"
            aria-expanded={isDropdownOpen}
          >
            <div class="flex items-center space-x-3">
              <div class="w-8 h-6 rounded bg-gradient-to-r {selectedStockBuyLevelOption?.bgColor || 'from-gray-500/80 to-gray-600/80'} flex items-center justify-center text-xs font-bold text-white shadow-sm">
                {selectedStockBuyLevelOption?.rank || 'ALL'}
              </div>
              <span class="font-medium text-white">{selectedStockBuyLevelOption?.name || '전체'}</span>
            </div>
            <svg 
              class="w-4 h-4 text-white/70 transform transition-transform duration-200 {isDropdownOpen ? 'rotate-180' : 'rotate-0'}" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
          </button>
        </div>
      </div>
      <!-- 액션 버튼들 -->
      <div class="flex items-center space-x-2 ml-auto">
        <div class="ml-4">
          <KakaoLoginAndSend
            bind:kakaoAccessCode
            isTextDark={false}
            on:onSendFinanceResultByKakaoApiCallback={sendFinanceResultByKakaoApi}
            on:onUpdateKakaoAccessCodeCallback={onUpdateKakaoAccessCode}
          />
        </div>
        <button class="h-10 flex items-center space-x-2 px-3 {isShowConditionSetting ? 'bg-gray-400' : 'bg-gradient-to-r from-gray-500 to-gray-600 hover:from-gray-600 hover:to-gray-700'} disabled:from-gray-400 disabled:to-gray-500 text-white rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl disabled:cursor-not-allowed transform"
          on:click={() => {
            isShowConditionSetting = !isShowConditionSetting;
          }}
        >
          <svg class="w-4 h-4 {isShowConditionSetting ? 'animate-spin' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
          </svg>
        </button>
      </div>
    </div>
    <!-- 검색 상태 표시 -->
    {#if (searchStockText.trim() !== '' || hasGoldenCrossFilter || selectedStockBuyLevel !== 'ALL') && calcSignalScoreResultList.length > 0}
      {@const searchActive = searchStockText.trim() !== ''}
      {@const goldenActive = hasGoldenCrossFilter}
      {@const buyLevelActive = selectedStockBuyLevel !== 'ALL'}
      
      <div class="flex justify-center">
        <div class="px-4 py-2 bg-blue-500/20 backdrop-blur-sm border border-blue-400/30 rounded-full text-sm text-blue-200 shadow-lg">
          {#if searchActive || goldenActive || buyLevelActive}
            🔍 필터 적용중: 
            {#if searchActive}
              '<span class="font-semibold text-white">{searchStockText}</span>' 검색
            {/if}
            {#if goldenActive}
              {searchActive ? ' + ' : ''}<span class="font-semibold text-amber-300">{goldenCrossFilterList.filter(f => f.isSelected).map(f => f.name).join(' & ')}</span>
            {/if}
            {#if buyLevelActive}
              {(searchActive || goldenActive) ? ' + ' : ''}<span class="inline-flex items-center space-x-1"><span class="font-semibold text-green-300">{selectedStockBuyLevelOption?.rank}</span><span class="text-green-200">등급</span></span>
            {/if}
            - <span class="font-semibold text-white">{filteredCalcSignalScoreResultList.length}</span>개 결과 / 전체 <span class="font-semibold text-white">{calcSignalScoreResultList.length}</span>개
          {/if}
        </div>
      </div>
    {/if}
    <!-- 데이터 테이블 -->
    <div class="flex-1 bg-white/95 backdrop-blur-lg rounded-2xl shadow-2xl overflow-hidden flex flex-col">
      <div class="tableWrap flex-1 min-h-0">
        <table class="w-full h-full">
          <thead class="bg-gradient-to-r from-slate-500 to-slate-600 border-b border-slate-400 flex-shrink-0">
            <tr>
              <th class="text-white font-semibold py-3 px-3 text-center text-shadow-light" style="width: 5%;">Rank</th>
              <th class="text-white font-semibold py-3 px-3 text-center text-shadow-light" style="width: 5%;">Buy-Tier</th>
              <th class="text-white font-semibold py-3 px-3 text-center text-shadow-light" style="width: 10%;">코드</th>
              <th class="text-white font-semibold py-3 px-3 text-left text-shadow-light" style="width: 20%;">주식명</th>
              <th class="text-white font-semibold py-3 px-3 text-right text-shadow-light" style="width: 10%;">총점수</th>
              <th class="text-white font-semibold py-3 px-3 text-right text-shadow-light" style="width: 10%;">추세점수</th>
              <th class="text-white font-semibold py-3 px-3 text-right text-shadow-light" style="width: 10%;">규모점수</th>
              <th class="text-white font-semibold py-3 px-3 text-right text-shadow-light" style="width: 10%;">현재가</th>
              <th class="text-white font-semibold py-3 px-3 text-right text-shadow-light" style="width: 20%;">시가총액</th>
            </tr>
          </thead>
          <tbody class="bg-white/95 backdrop-blur-lg elegant-scrollbar flex-1 overflow-y-auto" style="height: {tableHeight}px; max-height: {tableHeight}px; min-height: {tableHeight}px;">
            {#if filteredCalcSignalScoreResultList.length > 0 && loadProgress === false}
              {#each paginatedData as calcSignalScoreResultInfo}
                <tr
                  class="hover:bg-blue-100/80 hover:shadow-md transition-all duration-200 cursor-pointer group border-b border-gray-300/60"
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
                  <td class="py-2 px-3 text-center text-gray-600 font-medium" style="width: 5%;">{calcSignalScoreResultInfo.rank}</td>
                  <td class="py-2 px-3 text-center text-gray-600 font-medium" style="width: 5%;">{calcSignalScoreResultInfo?.stockBuyLevel ?? '-'}</td>
                  <td class="py-2 px-3 text-center text-gray-600 font-mono text-sm" style="width: 10%;">{calcSignalScoreResultInfo.code}</td>
                  <td class="py-2 px-3 text-left text-gray-700 font-semibold" style="width: 20%;">{calcSignalScoreResultInfo.name}</td>
                  <td class="py-2 px-3 text-right text-gray-600 font-medium" style="width: 10%;">{calcSignalScoreResultInfo?.totalScore ?? '-'}</td>
                  <td class="py-2 px-3 text-right text-gray-600 font-medium" style="width: 10%;">{calcSignalScoreResultInfo?.trendScore ?? '-'}</td>
                  <td class="py-2 px-3 text-right text-gray-600 font-medium" style="width: 10%;">{calcSignalScoreResultInfo?.marcapScore ?? '-'}</td>
                  <td class="py-2 px-3 text-right text-gray-600 font-medium" style="width: 10%;">{`${formatIncludeComma(calcSignalScoreResultInfo?.close) ?? '-'} ₩`}</td>
                  <td class="py-2 px-3 text-right text-gray-600 font-medium" style="width: 20%;">{`${formatIncludeComma(calcSignalScoreResultInfo?.marcap) ?? '-'} ₩`}</td>
                </tr>
              {/each}
            {:else if loadProgress}
              <tr class="h-full">
                <td colspan="8" class="p-0 relative h-full align-top">
                  <div class="w-full h-full flex justify-center items-center" style="min-height: {tableHeight}px;">
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
            {:else if searchStockText.trim() !== '' && calcSignalScoreResultList.length > 0}
              <tr class="h-full">
                <td colspan="8" class="p-0 relative h-full align-top">
                  <div class="w-full h-full flex flex-col justify-center items-center space-y-4" style="min-height: {tableHeight}px;">
                    <div class="w-16 h-16 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg">
                      <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                      </svg>
                    </div>
                    <div class="text-center space-y-2">
                      <p class="text-gray-700 font-semibold text-lg">'{searchStockText}' 검색 결과가 없습니다.</p>
                      <p class="text-gray-500 text-sm">다른 검색어를 시도해보세요.</p>
                    </div>
                  </div>
                </td>
              </tr>
            {:else}
              <tr class="h-full">
                <td colspan="8" class="p-0 relative h-full align-top">
                  <div class="w-full h-full flex flex-col justify-center items-center space-y-4" style="min-height: {tableHeight}px;">
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
    
    <!-- 페이지네이션 -->
    {#if filteredCalcSignalScoreResultList.length > itemsPerPage}
      <div class="flex justify-center items-center space-x-3 px-4">
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
          <span class="px-3 py-1 text-xs font-semibold bg-white/90 backdrop-blur-sm rounded-full border-2 border-white/30 shadow-sm">
            <span class="text-blue-600">{currentPage + 1}</span>
            <span class="text-gray-400 mx-1">/</span>
            <span class="text-gray-800">{maxPage}</span>
          </span>
          {#if searchStockText.trim() !== '' || hasGoldenCrossFilter || selectedStockBuyLevel !== 'ALL'}
            <span class="text-xs px-2 py-0.5 bg-blue-500/20 text-blue-200 rounded-full border border-blue-400/30">
              필터: {filteredCalcSignalScoreResultList.length}/{calcSignalScoreResultList.length}
            </span>
          {:else}
            <span class="text-xs px-2 py-0.5 bg-gray-800/80 text-white rounded-full border border-gray-600/50 shadow-sm">
              총 {filteredCalcSignalScoreResultList.length}개
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
  </div>
  
  {#if isSingleMode && singleChartInfo}
    <div class="absolute inset-0 z-20 bg-black/50 backdrop-blur-sm">
      <SingleChartBasic
        {singleChartInfo}
        on:closeSingleChartModeCallback={() => {
          isSingleMode = false;
        }}
      />
    </div>
  {/if}
</div>

<!-- 드롭다운 포털 - body에 직접 렌더링 -->
{#if isDropdownOpen}
  <div 
    class="fixed bg-slate-800/95 backdrop-blur-md rounded-lg border border-white/20 shadow-2xl max-h-80 overflow-y-auto overflow-x-hidden w-80 max-w-sm"
    style="top: {dropdownPosition.top}px; left: {dropdownPosition.left}px; z-index: 99999;"
    in:fly={{ y: -10, duration: 250, delay: 50 }}
    out:fly={{ y: -10, duration: 200 }}
  >
    {#each stockBuyLevelOptions as option, index}
      <button
        type="button"
        class="w-full px-3 py-3 flex items-center space-x-3 hover:bg-white/10 hover:shadow-lg active:bg-white/20 transition-all duration-200 {selectedStockBuyLevel === option.value ? 'bg-white/15 border-l-4 border-green-400 shadow-inner' : ''} first:rounded-t-lg last:rounded-b-lg group"
        on:click={() => selectBuyLevelOption(option.value)}
        in:fly={{ x: -20, duration: 200, delay: index * 40 }}
        out:fade={{ duration: 150 }}
      >
        <!-- 랭크 배지 -->
        <div class="w-9 h-6 rounded-md bg-gradient-to-r {option.bgColor} flex items-center justify-center text-xs font-bold text-white shadow-lg border {option.borderColor} transition-all duration-200 group-hover:shadow-xl group-hover:brightness-110 flex-shrink-0">
          {option.rank}
        </div>
        
        <!-- 내용 -->
        <div class="flex-1 text-left min-w-0">
          <div class="font-semibold text-white text-sm transition-colors duration-200 group-hover:text-green-200 truncate">{option.name}</div>
          <div class="text-xs text-white/60 mt-1 transition-opacity duration-200 group-hover:text-white/80 leading-tight break-words">{option.description}</div>
        </div>
        
        <!-- 선택 표시 -->
        {#if selectedStockBuyLevel === option.value}
          <div class="flex items-center justify-center w-6 h-6 rounded-full bg-green-500/20 border border-green-400/50" in:fly={{ x: 10, duration: 200 }}>
            <svg class="w-3 h-3 text-green-400 transition-all duration-200" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
          </div>
        {/if}
      </button>
    {/each}
  </div>
{/if}

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
		box-sizing: border-box;
		padding-bottom: 0;
		margin-bottom: 0;
		flex: 1;
		min-height: 0;
	}
	
	tr {
		display: table;
		width: 100%;
		table-layout: fixed;
		box-sizing: border-box;
	}

	/* 데이터 행에만 고정 높이 적용 */
	tr:not(.h-full) {
		height: 50px;
		min-height: 50px;
	}

	/* 빈 상태 메시지 행은 전체 높이 사용 */
	tr.h-full {
		height: 100%;
		min-height: 100%;
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

  /* 세련된 스크롤바 디자인 */
  .elegant-scrollbar::-webkit-scrollbar {
    width: 6px;
  }

  .elegant-scrollbar::-webkit-scrollbar-track {
    background: rgba(148, 163, 184, 0.1);
    border-radius: 12px;
    margin: 4px 0;
  }

  .elegant-scrollbar::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, 
      rgba(100, 116, 139, 0.4) 0%,
      rgba(148, 163, 184, 0.6) 50%,
      rgba(100, 116, 139, 0.4) 100%
    );
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.3);
    transition: all 0.3s ease;
  }

  .elegant-scrollbar::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, 
      rgba(59, 130, 246, 0.5) 0%,
      rgba(99, 102, 241, 0.7) 50%,
      rgba(139, 92, 246, 0.5) 100%
    );
    border-color: rgba(255, 255, 255, 0.5);
    transform: scaleX(1.2);
  }

  .elegant-scrollbar::-webkit-scrollbar-thumb:active {
    background: linear-gradient(135deg, 
      rgba(59, 130, 246, 0.7) 0%,
      rgba(99, 102, 241, 0.9) 50%,
      rgba(139, 92, 246, 0.7) 100%
    );
  }

  /* Firefox용 세련된 스크롤바 */
  .elegant-scrollbar {
    scrollbar-width: thin;
    scrollbar-color: rgba(148, 163, 184, 0.6) rgba(148, 163, 184, 0.1);
  }

  /* 테이블 헤더 텍스트 그림자 */
  .text-shadow {
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  }

  .text-shadow-light {
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  }

  /* 애니메이션 */
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .animate-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }

  /* 커스텀 드롭다운 스크롤바 */
  .custom-dropdown .max-h-80::-webkit-scrollbar {
    width: 8px;
  }

  .custom-dropdown .max-h-80::-webkit-scrollbar-track {
    background: rgba(51, 65, 85, 0.3);
    border-radius: 8px;
    margin: 4px 0;
  }

  .custom-dropdown .max-h-80::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, 
      rgba(34, 197, 94, 0.4) 0%,
      rgba(16, 185, 129, 0.6) 50%,
      rgba(5, 150, 105, 0.4) 100%
    );
    border-radius: 8px;
    border: 2px solid rgba(51, 65, 85, 0.2);
    transition: all 0.3s ease;
  }

  .custom-dropdown .max-h-80::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, 
      rgba(34, 197, 94, 0.6) 0%,
      rgba(16, 185, 129, 0.8) 50%,
      rgba(5, 150, 105, 0.6) 100%
    );
    border-color: rgba(255, 255, 255, 0.2);
    transform: scaleX(1.2);
  }

  /* Firefox용 커스텀 드롭다운 스크롤바 */
  .custom-dropdown .max-h-80 {
    scrollbar-width: thin;
    scrollbar-color: rgba(34, 197, 94, 0.6) rgba(51, 65, 85, 0.3);
  }

  /* 드롭다운 애니메이션 최적화 */
  .custom-dropdown button {
    will-change: transform, background-color;
  }
  
  .custom-dropdown .group:hover .w-10 {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  }
</style> 