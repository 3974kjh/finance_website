<script lang="ts">
  import { getAllFinanceRankList } from '$lib/api-connector/FinanceApi';
  import { SingleChartBasic, sendFinanceResult } from '$lib/main';
  import { onMount, onDestroy, tick } from 'svelte';
  import { BarChart, ProgressCircle, KakaoLoginAndSend } from '$lib/component';
  import toast from 'svelte-french-toast';
  import { cancelRequest } from "$lib/axios-provider/AxiosProvider";

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

  // 월별 데이터 캐시
  let processedMonthlyDataCache: Map<string, any[]> = new Map();
  
  // 월별 버튼 클릭 디바운싱을 위한 변수
  let monthlyUpdateInProgress: boolean = false;

  let innerHeight: number = 0;

  let loadProgress: boolean = false;
  let monthlyLoadProgress: boolean = false;

  let allPeriodTextKey: string = '전체 기간 없음';
  let selectedMonthRank: string = '';

  let axiosController: any = null;
  
  let searchAllStockText: string = '';
  let searchMonthStockText: string = '';

  // 테이블 페이지네이션
  let allTableCurrentPage: number = 0;
  let monthTableCurrentPage: number = 0;
  const itemsPerPage: number = 100; // 페이지당 100개 항목

  let kakaoAccessCode: string = '';
  let kakaoAccessToken: string = '';

  // 검색 필터링된 데이터
  $: filteredAllRankList = searchAllStockText.trim() === '' 
    ? financeAllRankList.map((item: any, index: number) => ({ ...item, originalIndex: index }))
    : financeAllRankList
        .map((item: any, index: number) => ({ ...item, originalIndex: index }))
        .filter((item: any) => 
          item.name.toLowerCase().includes(searchAllStockText.toLowerCase()) || 
          item.code.toLowerCase().includes(searchAllStockText.toLowerCase())
        );

  $: filteredMonthRankList = searchMonthStockText.trim() === '' 
    ? selectedFinanceMonthRankList.map((item: any, index: number) => ({ ...item, originalIndex: index }))
    : selectedFinanceMonthRankList
        .map((item: any, index: number) => ({ ...item, originalIndex: index }))
        .filter((item: any) => 
          item.name.toLowerCase().includes(searchMonthStockText.toLowerCase()) || 
          item.code.toLowerCase().includes(searchMonthStockText.toLowerCase())
        );

  // 전체 테이블용 페이지네이션 데이터 (필터링된 데이터 기준)
  $: allTableData = filteredAllRankList.slice(
    allTableCurrentPage * itemsPerPage,
    (allTableCurrentPage + 1) * itemsPerPage
  );

  // 월별 테이블용 페이지네이션 데이터 (필터링된 데이터 기준)
  $: monthTableData = filteredMonthRankList.slice(
    monthTableCurrentPage * itemsPerPage,
    (monthTableCurrentPage + 1) * itemsPerPage
  );

  // 페이지 수 계산 (필터링된 데이터 기준)
  $: allTableMaxPage = Math.ceil(filteredAllRankList.length / itemsPerPage);
  $: monthTableMaxPage = Math.ceil(filteredMonthRankList.length / itemsPerPage);

  // 검색 시 첫 페이지로 이동
  $: if (searchAllStockText) {
    allTableCurrentPage = 0;
  }

  $: if (searchMonthStockText) {
    monthTableCurrentPage = 0;
  }

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

  /**
   * 데이터 변환 및 정렬 최적화 함수
   */
  const processFinanceData = (dataArray: any[]): any[] => {
    if (!dataArray || dataArray.length === 0) {
      return [];
    }

    // 한 번의 순회로 변환과 정렬을 위한 데이터 준비
    const processedData = dataArray.map((item: any) => {
      const rankSum = parseInt(item.rankSum) || 0;
      const fullCount = parseInt(item.fullCount) || 1;
      const count = parseInt(item.count) || 0;
      
      return {
        ...item,
        rankAvg: Math.round(rankSum / fullCount),
        rankSum,
        count
      };
    });

    // 네이티브 sort 사용 (lodash orderBy보다 빠름)
    return processedData.sort((a, b) => {
      // 1차 정렬: rankAvg 오름차순
      if (a.rankAvg !== b.rankAvg) {
        return a.rankAvg - b.rankAvg;
      }
      // 2차 정렬: count 내림차순
      return b.count - a.count;
    });
  };

  /**
   * 모든 월별 데이터를 미리 처리하여 캐시에 저장
   */
  const preprocessAllMonthlyData = (monthlyDataObject: any) => {
    if (!monthlyDataObject) return;
    
    // 캐시 초기화
    processedMonthlyDataCache.clear();
    
    // 각 월별 데이터를 미리 처리
    Object.keys(monthlyDataObject).forEach(month => {
      const processedData = processFinanceData(monthlyDataObject[month]);
      processedMonthlyDataCache.set(month, processedData);
    });
  };

  /**
   * 캐시에서 월별 데이터 가져오기 (즉시 반환)
   */
  const getProcessedMonthlyData = (month: string): any[] => {
    return processedMonthlyDataCache.get(month) || [];
  };

  const getKoreaAllFinanceRankList = async () => {
    axiosController = new AbortController();
    allPeriodTextKey = '전체 기간 없음';
    financeAllRankList = [];
    financeMonthRankObject = null;
    loadProgress = true;

    const resultList = await getAllFinanceRankList({stock: 'KRX'}, axiosController);

    loadProgress = false;

    if (!!resultList?.data?.allPeriodDataList) {
      const allPeriodKeys = Object.keys(resultList.data.allPeriodDataList);
      if (allPeriodKeys.length > 0) {
        allPeriodTextKey = allPeriodKeys[0];
        financeAllRankList = processFinanceData(resultList.data.allPeriodDataList[allPeriodTextKey]);
      }
    }

    if (!!resultList?.data?.perMonthDataList) {
      financeMonthRankObject = resultList.data.perMonthDataList;
      const monthKeys = Object.keys(financeMonthRankObject);
      if (monthKeys.length > 0) {
        // 모든 월별 데이터를 미리 처리하여 캐시에 저장
        preprocessAllMonthlyData(financeMonthRankObject);
        
        selectedMonthRank = monthKeys[monthKeys.length - 1];
        selectedFinanceMonthRankList = getProcessedMonthlyData(selectedMonthRank);
      }
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

  const setTopAverageRankSumAvg = (financeRankList: any) => {
    if (!!!financeRankList || financeRankList.length < 0) {
      return 0;
    }

    // rankAvg 기준으로 오름차순 정렬 (낮은 RankSum이 더 좋은 순위)
    const sortedList = financeRankList
      .filter((item: any) => item && typeof item.rankAvg === 'number')
      .sort((a: any, b: any) => a.rankAvg - b.rankAvg);

    if (sortedList.length === 0) {
      return 0;
    }

    // 상위 10% 계산 (최소 1개 이상)
    const topPercentCount = Math.max(1, Math.floor(sortedList.length * 0.1));
    
    // 상위 10% 항목들을 가져옴
    const topItems = sortedList.slice(0, topPercentCount);
    
    // 상위 10% 항목들의 rankAvg 평균값 계산
    return topItems.reduce((sum: number, item: any) => sum + item.rankAvg, 0) / topItems.length;
  }

  const setFinanceListByTopAverageRankSumAvg = (financeRankList: any) => {
    if (!!!financeRankList || financeRankList.length < 0) {
      return [];
    }

    // rankAvg 기준으로 오름차순 정렬 (낮은 RankSum이 더 좋은 순위)
    const sortedList = financeRankList
      .filter((item: any) => item && typeof item.rankAvg === 'number')
      .sort((a: any, b: any) => a.rankAvg - b.rankAvg);

    if (sortedList.length === 0) {
      return [];
    }

    // 상위 10% 계산 (최소 1개 이상)
    const topPercentCount = Math.max(1, Math.floor(sortedList.length * 0.1));
    
    // 상위 10% 항목들을 가져옴
    const topItems = sortedList.slice(0, topPercentCount);
    
    // 상위 10% 항목들의 rankAvg 평균값 계산
    const averageRankSum = topItems.reduce((sum: number, item: any) => sum + item.rankAvg, 0) / topItems.length;
    
    // 평균값보다 낮은(더 좋은) rankAvg을 가진 항목들을 반환
    const result = sortedList.filter((item: any) => item.rankAvg <= averageRankSum);
    
    // 성능을 위해 차트용은 상위 100개로 제한
    return result.slice(0, 100);
  }

  // BarChart 포인트 클릭 이벤트 핸들러
  const handleBarChartPointClick = (event: CustomEvent) => {
    const { item, seriesName } = event.detail;
    
    if (!item || item.name === '횟수') {
      return;
    }
    
    // SingleChart 모드로 전환
    singleChartInfo = {
      title: item.name,
      searchDuration: searchDuration,
      chartMode: item.code,
      chartKey: item.code,
      detailInfo: {
        ...item,
        seriesName: seriesName
      }
    };

    isSingleMode = true;
  }

  // BarChart 렌더링 완료 이벤트 핸들러
  const handleChartRendered = () => {
    monthlyLoadProgress = false;
    monthlyUpdateInProgress = false;
    
    // 월별 테이블 페이지 초기화
    monthTableCurrentPage = 0;
  }

  /**
   * 테이블 상단으로 즉시 스크롤
   */
  const scrollToTableTop = (tableType: 'all' | 'month') => {
    try {
      // tbody 내부 스크롤만 초기화 (페이지 전체 스크롤 방지)
      const allTbodies = document.querySelectorAll('tbody');
      if (tableType === 'all' && allTbodies[0]) {
        // 즉시 맨 위로 이동
        allTbodies[0].scrollTop = 0;
      } else if (tableType === 'month' && allTbodies[1]) {
        // 즉시 맨 위로 이동
        allTbodies[1].scrollTop = 0;
      }
      
    } catch (error) {
      console.error('스크롤 에러:', error);
    }
  }
</script>

<svelte:window bind:innerHeight/>
<div class="flex w-full h-full bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-900 relative overflow-hidden">
  <!-- 배경 데코레이션 -->
  <div class="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,_rgba(59,130,246,0.1)_1px,_transparent_0)] bg-[size:32px_32px] pointer-events-none"></div>
  <div class="absolute top-0 left-0 w-96 h-96 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2 animate-pulse"></div>
  <div class="absolute bottom-0 right-0 w-96 h-96 bg-gradient-to-r from-cyan-500/20 to-teal-500/20 rounded-full blur-3xl translate-x-1/2 translate-y-1/2 animate-pulse"></div>
  <div class="absolute top-1/2 left-1/2 w-64 h-64 bg-gradient-to-r from-violet-500/15 to-pink-500/15 rounded-full blur-2xl -translate-x-1/2 -translate-y-1/2"></div>
  
  <div class="flex flex-col w-full h-full p-2 space-y-2 relative z-10">
    <!-- 전체 -->
    <div class="flex flex-row h-[50%] bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 shadow-xl">
      <!-- bar chart -->
      <div class="flex flex-col h-full w-[50%] border-r border-white/20 p-2 space-y-2">
        <p class="flex h-auto w-full font-bold text-white">{allPeriodTextKey}</p>
        <div class="flex grow rounded-md overflow-auto relative z-20">
          {#if financeAllRankList.length > 0 && loadProgress === false}
            <div class="h-auto relative z-30">
              <BarChart
                barDataList={setFinanceListByTopAverageRankSumAvg(financeAllRankList)}
                on:pointClick={handleBarChartPointClick}
              />
            </div>
          {:else if loadProgress}
            <div class="flex w-full h-full justify-center items-center font-bold text-white">
              <ProgressCircle
                isTextBlack={false}
                size={100}
                thickness={10}
                isLarge={true}
                text={'저장된 전체 기간 상위도달횟수 데이터 조회 중...'}
              />
            </div>
          {:else}
            <p class="flex w-full h-full justify-center items-center font-bold text-white">
              {'저장된 전체 기간 상위도달횟수 데이터가 없습니다.'}
            </p>
          {/if}
        </div>
      </div>
      <div class="flex flex-col h-full w-[50%]">
        <div class="flex flex-row h-auto w-full pt-2 pb-1 px-2">
          <div class="flex flex-row grow items-center space-x-4">
            <div class="flex items-center space-x-2">
              <div class="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-600 rounded-xl flex items-center justify-center shadow-lg">
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
              </div>
              <span class="font-bold text-white">종목 검색</span>
            </div>
            <input
              autocomplete="off"
              id="name"
              name="name"
              class="h-10 px-3 rounded-lg bg-white/90 backdrop-blur-sm border border-white/30 focus:border-purple-400 focus:ring-2 focus:ring-purple-400/50 outline-none transition-all duration-200 text-gray-800 placeholder-gray-500 shadow-md hover:shadow-lg w-[280px]"
              autofocus={true}
              disabled={financeAllRankList.length < 1 ? true : false}
              minlength="0"
              maxlength="20"
              size="10"
              placeholder="종목명/종목코드 실시간 검색"
              bind:value={searchAllStockText}
            />
          </div>
          <div class="flex items-center">
            <KakaoLoginAndSend
              bind:kakaoAccessCode
              isTextDark={false}
              on:onSendFinanceResultByKakaoApiCallback={sendFinanceResultByKakaoApi}
              on:onUpdateKakaoAccessCodeCallback={onUpdateKakaoAccessCode}
            />
          </div>
        </div>
        <!-- 검색 상태 표시 -->
        {#if searchAllStockText.trim() !== ''}
          <div class="flex justify-center py-1">
            <div class="px-3 py-1 bg-blue-500/20 backdrop-blur-sm border border-blue-400/30 rounded-full text-sm text-blue-200 shadow-lg">
              🔍 '<span class="font-semibold text-white">{searchAllStockText}</span>' 검색 중 - {filteredAllRankList.length}개 결과
            </div>
          </div>
        {/if}
        <div class="flex grow w-full relative z-10">
          <div class="tableWrap px-2 py-1">
            <table>
              <thead class="all-table-header">
                <tr tabindex="0">
                  <th style="width: 5%; text-align: center;">Rank</th>
                  <th style="width: 10%; text-align: center;">RankAvg</th>
                  <th style="width: 10%; text-align: center;">CountSum</th>
                  <th style="width: 30%; text-align: center;">코드</th>
                  <th style="width: 45%; text-align: left;">주식명</th>
                </tr>
              </thead>
              <tbody style="height: {(innerHeight / 2) - 155}px">
                {#if financeAllRankList.length > 0 && loadProgress === false}
                  {#if allTableData.length > 0}
                    {#each allTableData as financeAllRankInfo, index}
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
                        <td style="width: 5%; text-align: center; color: {setTopAverageRankSumAvg(financeAllRankList) > financeAllRankInfo.rankAvg ? 'red' : 'blue'}">{financeAllRankInfo.originalIndex + 1}</td>
                        <td style="width: 10%; text-align: center;">{financeAllRankInfo?.rankAvg ?? '-'}</td>
                        <td style="width: 10%; text-align: center;">{financeAllRankInfo?.count ?? '-'}</td>
                        <td style="width: 30%; text-align: center;">{financeAllRankInfo?.code ?? '-'}</td>
                        <td style="width: 45%; text-align: left;">{financeAllRankInfo?.name ?? '-'}</td>
                      </tr>
                    {/each}
                  {:else}
                    <tr>
                      <td colspan="5" class="text-center py-4 text-gray-500">
                        '{searchAllStockText}' 검색 결과가 없습니다.
                      </td>
                    </tr>
                  {/if}
                {:else if loadProgress}
                  <div class="absolute inset-0 flex w-full h-full justify-center items-center font-bold text-white">
                    <ProgressCircle
                      size={100}
                      thickness={10}
                      isLarge={true}
                      text={'저장된 전체 기간 RankSum 데이터 조회 중...'}
                    />
                  </div>
                {:else}
                  <div class="absolute inset-0 flex w-full h-full justify-center items-center font-bold text-white">
                    {'저장된 전체 기간 RankSum 데이터가 없습니다.'}
                  </div>
                {/if}
              </tbody>
            </table>
          </div>
        </div>
        <!-- 전체 테이블 페이지네이션 -->
        {#if filteredAllRankList.length > itemsPerPage}
          <div class="flex justify-center items-center space-x-3 py-1 px-2">
            <button 
              class="group relative w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold transition-all duration-300 transform {allTableCurrentPage === 0 ? 'bg-white/20 border-white/30 text-white/50 cursor-not-allowed' : 'bg-gradient-to-r from-blue-500 to-blue-600 border-blue-500 text-white hover:from-blue-600 hover:to-blue-700 hover:scale-110 hover:shadow-lg active:scale-95'}"
              disabled={allTableCurrentPage === 0}
              on:click={() => {
                allTableCurrentPage = Math.max(0, allTableCurrentPage - 1);
                requestAnimationFrame(() => scrollToTableTop('all'));
              }}
              title="이전 페이지"
            >
              <svg class="w-3 h-3 transition-transform duration-200 group-hover:-translate-x-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </button>
            
            <div class="flex items-center space-x-2">
              <span class="px-2 py-1 text-xs font-semibold bg-white/20 backdrop-blur-sm rounded-full border border-white/30 shadow-sm text-white">
                <span class="text-blue-300">{allTableCurrentPage + 1}</span>
                <span class="text-white/60 mx-1">/</span>
                <span class="text-white">{allTableMaxPage}</span>
              </span>
              {#if searchAllStockText.trim() !== ''}
                <span class="text-xs px-2 py-0.5 bg-blue-500/20 text-blue-200 rounded-full border border-blue-400/30 backdrop-blur-sm">
                  검색: {filteredAllRankList.length}/{financeAllRankList.length}
                </span>
              {:else}
                <span class="text-xs px-2 py-0.5 bg-white/20 text-white rounded-full border border-white/30 backdrop-blur-sm">
                  총 {filteredAllRankList.length}개
                </span>
              {/if}
            </div>
            
            <button 
              class="group relative w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold transition-all duration-300 transform {allTableCurrentPage >= allTableMaxPage - 1 ? 'bg-white/20 border-white/30 text-white/50 cursor-not-allowed' : 'bg-gradient-to-r from-blue-500 to-blue-600 border-blue-500 text-white hover:from-blue-600 hover:to-blue-700 hover:scale-110 hover:shadow-lg active:scale-95'}"
              disabled={allTableCurrentPage >= allTableMaxPage - 1}
              on:click={() => {
                allTableCurrentPage = Math.min(allTableMaxPage - 1, allTableCurrentPage + 1);
                requestAnimationFrame(() => scrollToTableTop('all'));
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
    </div>
    <!-- 월별 -->
    <div class="flex flex-row h-[50%] bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 shadow-xl">
      <!-- bar chart -->
      <div class="flex flex-col h-full w-[50%] border-r border-white/20 p-2 space-y-2">
        <div class="flex flex-wrap h-[75px] w-full border border-white/30 rounded-md overflow-auto px-1 py-0.5 bg-white/5 backdrop-blur-sm">
          {#if !!financeMonthRankObject}
            {#each Object.keys(financeMonthRankObject) as financeMonth}
              <button 
                class="h-[30px] rounded-md px-2 mr-1 my-0.5 font-medium text-sm transition-all duration-200 shadow-md hover:shadow-lg {selectedMonthRank === financeMonth ? 'bg-white text-gray-800 shadow-lg' : 'bg-white/20 backdrop-blur-sm text-white hover:bg-white/30 border border-white/30'}" 
                disabled={monthlyLoadProgress}
                on:click={async () => {
                // 이미 업데이트 중이면 무시
                if (monthlyUpdateInProgress) return;
                
                // 즉시 UI 반응
                selectedMonthRank = financeMonth;
                monthlyLoadProgress = true;
                monthlyUpdateInProgress = true;
                
                // 브라우저의 다음 프레임에서 실행 (60fps에 맞춘 최적화)
                requestAnimationFrame(() => {
                  // 추가로 한 프레임 더 기다려서 UI 업데이트 완전 보장
                  requestAnimationFrame(async () => {
                    // 캐시에서 즉시 가져오기 (데이터 처리 없음)
                    selectedFinanceMonthRankList = getProcessedMonthlyData(selectedMonthRank);
                    
                    // 추가 렌더링 시간 확보
                    await tick();
                    
                    // ProgressCircle 종료는 차트 렌더링 완료 시점에서 처리
                  });
                });
              }}>{financeMonth}</button>
            {/each}
          {/if}
        </div>
        <div class="flex grow rounded-md overflow-auto relative z-20">
          {#if monthlyLoadProgress}
            <div class="flex w-full h-full justify-center items-center font-bold text-white">
              <ProgressCircle
                isTextBlack={false}
                size={100}
                thickness={10}
                isLarge={true}
                text={'차트 업데이트 중...'}
              />
            </div>
          {:else if selectedFinanceMonthRankList.length > 0 && loadProgress === false}
            <div class="h-auto relative z-30">
              <BarChart
                barDataList={setFinanceListByTopAverageRankSumAvg(selectedFinanceMonthRankList)}
                on:pointClick={handleBarChartPointClick}
                on:chartRendered={handleChartRendered}
              />
            </div>
          {:else if loadProgress}
            <div class="flex w-full h-full justify-center items-center font-bold text-white">
              <ProgressCircle
                isTextBlack={false}
                size={100}
                thickness={10}
                isLarge={true}
                text={'저장된 월별 상위도달횟수 데이터 조회 중...'}
              />
            </div>
          {:else}
            <p class="flex w-full h-full justify-center items-center font-bold text-white">
              {'저장된 월별 상위도달횟수 데이터가 없습니다.'}
            </p>
          {/if}
        </div>
      </div>
      <div class="flex flex-col h-full w-[50%]">
        <div class="flex flex-row h-auto w-full space-x-4 pt-2 pb-1 items-center px-2">
          <div class="flex items-center space-x-2">
            <div class="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-600 rounded-xl flex items-center justify-center shadow-lg">
              <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
            </div>
            <span class="font-bold text-white">종목 검색</span>
          </div>
          <input
            id="name"
            name="name"
            autocomplete="off"
            class="h-10 px-3 rounded-lg bg-white/90 backdrop-blur-sm border border-white/30 focus:border-purple-400 focus:ring-2 focus:ring-purple-400/50 outline-none transition-all duration-200 text-gray-800 placeholder-gray-500 shadow-md hover:shadow-lg w-[280px]"
            autofocus={true}
            disabled={selectedFinanceMonthRankList.length < 1 || monthlyLoadProgress ? true : false}
            minlength="0"
            maxlength="20"
            size="10"
            placeholder="종목명/종목코드 실시간 검색"
            bind:value={searchMonthStockText}
          />
        </div>
        <!-- 검색 상태 표시 -->
        {#if searchMonthStockText.trim() !== ''}
          <div class="flex justify-center py-1">
            <div class="px-3 py-1 bg-green-500/20 backdrop-blur-sm border border-green-400/30 rounded-full text-sm text-green-200 shadow-lg">
              🔍 '<span class="font-semibold text-white">{searchMonthStockText}</span>' 검색 중 - {filteredMonthRankList.length}개 결과
            </div>
          </div>
        {/if}
        <div class="flex h-full w-full relative z-10">
          <div class="tableWrap px-2 py-1">
            <table>
              <thead class="month-table-header">
                <tr tabindex="0">
                  <th style="width: 5%; text-align: center;">Rank</th>
                  <th style="width: 10%; text-align: center;">RankAvg</th>
                  <th style="width: 10%; text-align: center;">CountSum</th>
                  <th style="width: 30%; text-align: center;">코드</th>
                  <th style="width: 45%; text-align: left;">주식명</th>
                </tr>
              </thead>
              <tbody style="height: {(innerHeight / 2) - 155}px">
                {#if monthlyLoadProgress}
                  <div class="absolute inset-0 flex w-full h-full justify-center items-center font-bold text-white">
                    <ProgressCircle
                      size={100}
                      thickness={10}
                      isLarge={true}
                      text={'테이블 업데이트 중...'}
                    />
                  </div>
                {:else if selectedFinanceMonthRankList.length > 0 && loadProgress === false}
                  {#if monthTableData.length > 0}
                    {#each monthTableData as financeMonthRankInfo, index}
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
                        <td style="width: 5%; text-align: center; color: {setTopAverageRankSumAvg(selectedFinanceMonthRankList) > financeMonthRankInfo.rankAvg ? 'red' : 'blue'}">{financeMonthRankInfo.originalIndex + 1}</td>
                        <td style="width: 10%; text-align: center;">{financeMonthRankInfo?.rankAvg ?? '-'}</td>
                        <td style="width: 10%; text-align: center;">{financeMonthRankInfo?.count ?? '-'}</td>
                        <td style="width: 30%; text-align: center;">{financeMonthRankInfo?.code ?? '-'}</td>
                        <td style="width: 45%; text-align: left;">{financeMonthRankInfo?.name ?? '-'}</td>
                      </tr>
                    {/each}
                  {:else}
                    <tr>
                      <td colspan="5" class="text-center py-4 text-gray-500">
                        '{searchMonthStockText}' 검색 결과가 없습니다.
                      </td>
                    </tr>
                  {/if}
                {:else if loadProgress}
                  <div class="absolute inset-0 flex w-full h-full justify-center items-center font-bold text-white">
                    <ProgressCircle
                      size={100}
                      thickness={10}
                      isLarge={true}
                      text={'저장된 월별 RankSum 데이터 조회 중...'}
                    />
                  </div>
                {:else}
                  <div class="absolute inset-0 flex w-full h-full justify-center items-center font-bold text-white">
                    {'저장된 월별 RankSum 데이터가 없습니다.'}
                  </div>
                {/if}
              </tbody>
            </table>
          </div>
        </div>
        <!-- 월별 테이블 페이지네이션 -->
        {#if filteredMonthRankList.length > itemsPerPage}
          <div class="flex justify-center items-center space-x-3 py-1 px-2">
            <button 
              class="group relative w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold transition-all duration-300 transform {monthTableCurrentPage === 0 ? 'bg-white/20 border-white/30 text-white/50 cursor-not-allowed' : 'bg-gradient-to-r from-green-500 to-green-600 border-green-500 text-white hover:from-green-600 hover:to-green-700 hover:scale-110 hover:shadow-lg active:scale-95'}"
              disabled={monthTableCurrentPage === 0}
              on:click={() => {
                monthTableCurrentPage = Math.max(0, monthTableCurrentPage - 1);
                requestAnimationFrame(() => scrollToTableTop('month'));
              }}
              title="이전 페이지"
            >
              <svg class="w-3 h-3 transition-transform duration-200 group-hover:-translate-x-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </button>
            
            <div class="flex items-center space-x-2">
              <span class="px-2 py-1 text-xs font-semibold bg-white/20 backdrop-blur-sm rounded-full border border-white/30 shadow-sm text-white">
                <span class="text-green-300">{monthTableCurrentPage + 1}</span>
                <span class="text-white/60 mx-1">/</span>
                <span class="text-white">{monthTableMaxPage}</span>
              </span>
              {#if searchMonthStockText.trim() !== ''}
                <span class="text-xs px-2 py-0.5 bg-green-500/20 text-green-200 rounded-full border border-green-400/30 backdrop-blur-sm">
                  검색: {filteredMonthRankList.length}/{selectedFinanceMonthRankList.length}
                </span>
              {:else}
                <span class="text-xs px-2 py-0.5 bg-white/20 text-white rounded-full border border-white/30 backdrop-blur-sm">
                  총 {filteredMonthRankList.length}개
                </span>
              {/if}
            </div>
            
            <button 
              class="group relative w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold transition-all duration-300 transform {monthTableCurrentPage >= monthTableMaxPage - 1 ? 'bg-white/20 border-white/30 text-white/50 cursor-not-allowed' : 'bg-gradient-to-r from-green-500 to-green-600 border-green-500 text-white hover:from-green-600 hover:to-green-700 hover:scale-110 hover:shadow-lg active:scale-95'}"
              disabled={monthTableCurrentPage >= monthTableMaxPage - 1}
              on:click={() => {
                monthTableCurrentPage = Math.min(monthTableMaxPage - 1, monthTableCurrentPage + 1);
                requestAnimationFrame(() => scrollToTableTop('month'));
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
    </div>
  </div>
  {#if isSingleMode && singleChartInfo}
    <div class="absolute inset-0 z-20 bg-black/50 backdrop-blur-sm">
      <SingleChartBasic
        singleChartInfo={singleChartInfo}
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
		height: calc(100%);
		display: flex;
		flex-direction: column;
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
		position: relative;
	}
  th {
    color: #374151;
    background: #F8FAFC;
    font-weight: 600;
    padding: 8px 12px;
    border-bottom: 2px solid #E2E8F0;
  }
	tr {
		display: table;
		width: 100%;
		table-layout: fixed;
	}
	table {
		width: 100%;
		table-layout: fixed;
		background: rgba(255, 255, 255, 0.95);
		backdrop-filter: blur(16px);
		border-radius: 16px;
		overflow: hidden;
		box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
	}
	tbody {
		grid-auto-flow: row;
	}
	td {
		margin-top: -1px;
		padding: 8px 12px;
		color: #374151;
	}

  /* 기본 배경색 */
  table tr {
    background-color: rgba(255, 255, 255, 0.8);
    transition: all 0.2s ease;
  }

  /* 포커스된 행의 배경색 */
  table tr:hover {
    background: linear-gradient(to right, rgba(59, 130, 246, 0.1), rgba(99, 102, 241, 0.1));
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  /* 키보드 네비게이션을 위한 outline 제거 */
  table tr:hover {
    outline: none;
  }

  /* 페이지네이션 버튼 호버 효과 강화 */
  .group:hover svg {
    transition: transform 0.2s ease-in-out;
  }

  /* 현대적인 스크롤바 스타일링 */
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

  /* BarChart 영역 스크롤바 스타일링 - 얇은 스타일 */
  .overflow-auto::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }

  .overflow-auto::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
  }

  .overflow-auto::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.3);
    border-radius: 3px;
  }

  .overflow-auto::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.5);
  }

  .overflow-auto::-webkit-scrollbar-corner {
    background: transparent;
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

  /* 글래스모피즘 효과 강화 */
  :global(.backdrop-blur-md) {
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
  }

  :global(.backdrop-blur-lg) {
    backdrop-filter: blur(24px) saturate(180%);
    -webkit-backdrop-filter: blur(24px) saturate(180%);
  }

  :global(.backdrop-blur-sm) {
    backdrop-filter: blur(8px) saturate(180%);
    -webkit-backdrop-filter: blur(8px) saturate(180%);
  }

  /* 전체 테이블 헤더 - 파란색 그라데이션 */
  .all-table-header th {
    background: #3b82f6;
    color: white;
    border-bottom: 2px solid #1e40af;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  }

  /* 월별 테이블 헤더 - 초록색 그라데이션 */
  .month-table-header th {
    background: #10b981;
    color: white;
    border-bottom: 2px solid #065f46;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  }
</style>