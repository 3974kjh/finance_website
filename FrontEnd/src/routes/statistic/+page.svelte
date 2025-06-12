<script lang="ts">
  import { getAllFinanceRankList } from '$lib/api-connector/FinanceApi';
  import { SingleChartBasic, sendFinanceResult } from '$lib/main';
  import { onMount, onDestroy, tick } from 'svelte';
  import { BarChart, ProgressCircle, KakaoLoginAndSend } from '$lib/component';
  import toast from 'svelte-french-toast';
  import { cancelRequest } from "$lib/axios-provider/AxiosProvider";
  import _ from 'lodash';

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
      // 더 간단한 방법: 검색 입력 필드를 기준으로 스크롤
      if (tableType === 'all') {
        // 전체 테이블의 검색 영역으로 즉시 스크롤
        const searchElement = document.querySelector('input[placeholder*="종목명/종목코드 실시간 검색"]');
        if (searchElement) {
          searchElement.scrollIntoView({ 
            behavior: 'auto', 
            block: 'start',
            inline: 'nearest'
          });
        }
      } else {
        // 월별 테이블 영역으로 즉시 스크롤 - 월별 버튼 영역을 기준으로
        const monthButtonArea = document.querySelector('.flex.flex-wrap.h-\\[75px\\]');
        if (monthButtonArea) {
          monthButtonArea.scrollIntoView({ 
            behavior: 'auto', 
            block: 'start',
            inline: 'nearest'
          });
        }
      }
      
      // tbody 내부 스크롤도 즉시 초기화
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
                barDataList={setFinanceListByTopAverageRankSumAvg(financeAllRankList)}
                on:pointClick={handleBarChartPointClick}
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
              class="border w-[280px] px-2 py-1 rounded-md text-sm"
              autofocus={true}
              disabled={financeAllRankList.length < 1 ? true : false}
              minlength="0"
              maxlength="20"
              size="10"
              placeholder="종목명/종목코드 실시간 검색"
              bind:value={searchAllStockText}
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
        <!-- 검색 상태 표시 -->
        {#if searchAllStockText.trim() !== ''}
          <div class="flex justify-center py-1">
            <div class="px-3 py-1 bg-blue-50 border border-blue-200 rounded-full text-sm text-blue-700">
              🔍 '<span class="font-semibold">{searchAllStockText}</span>' 검색 중 - {filteredAllRankList.length}개 결과
            </div>
          </div>
        {/if}
        <div class="flex grow w-full">
          <div class="tableWrap p-1">
            <table>
              <thead>
                <tr tabindex="0">
                  <th style="width: 5%; text-align: center;">Rank</th>
                  <th style="width: 10%; text-align: center;">RankAvg</th>
                  <th style="width: 10%; text-align: center;">CountSum</th>
                  <th style="width: 30%; text-align: center;">코드</th>
                  <th style="width: 45%; text-align: left;">주식명</th>
                </tr>
              </thead>
              <tbody style="height: {(innerHeight / 2) - 135}px">
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
        <!-- 전체 테이블 페이지네이션 -->
        {#if filteredAllRankList.length > itemsPerPage}
          <div class="flex justify-center items-center space-x-3 py-1">
            <button 
              class="group relative w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold transition-all duration-300 transform {allTableCurrentPage === 0 ? 'bg-gray-100 border-gray-300 text-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-blue-500 to-blue-600 border-blue-500 text-white hover:from-blue-600 hover:to-blue-700 hover:scale-110 hover:shadow-lg active:scale-95'}"
              disabled={allTableCurrentPage === 0}
              on:click={() => {
                allTableCurrentPage = Math.max(0, allTableCurrentPage - 1);
                // requestAnimationFrame으로 즉시 스크롤 실행
                requestAnimationFrame(() => scrollToTableTop('all'));
              }}
              title="이전 페이지"
            >
              <svg class="w-3 h-3 transition-transform duration-200 group-hover:-translate-x-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </button>
            
            <div class="flex items-center space-x-2">
              <span class="px-3 py-1 text-xs font-semibold bg-gradient-to-r from-gray-50 to-gray-100 rounded-full border-2 border-gray-200 shadow-sm">
                <span class="text-blue-600">{allTableCurrentPage + 1}</span>
                <span class="text-gray-400 mx-1">/</span>
                <span class="text-gray-600">{allTableMaxPage}</span>
              </span>
              {#if searchAllStockText.trim() !== ''}
                <span class="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full border border-blue-200">
                  검색: {filteredAllRankList.length}/{financeAllRankList.length}
                </span>
              {:else}
                <span class="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full border border-gray-200">
                  총 {filteredAllRankList.length}개
                </span>
              {/if}
            </div>
            
            <button 
              class="group relative w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold transition-all duration-300 transform {allTableCurrentPage >= allTableMaxPage - 1 ? 'bg-gray-100 border-gray-300 text-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-blue-500 to-blue-600 border-blue-500 text-white hover:from-blue-600 hover:to-blue-700 hover:scale-110 hover:shadow-lg active:scale-95'}"
              disabled={allTableCurrentPage >= allTableMaxPage - 1}
              on:click={() => {
                allTableCurrentPage = Math.min(allTableMaxPage - 1, allTableCurrentPage + 1);
                // requestAnimationFrame으로 즉시 스크롤 실행
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
    <div class="flex flex-row h-[50%] space-x-2 border bg-white rounded-e-md">
      <!-- bar chart -->
      <div class="flex flex-col h-full w-[50%] border-r p-2 space-y-2">
        <div class="flex flex-wrap h-[75px] w-full border rounded-md overflow-auto px-1 py-0.5">
          {#if !!financeMonthRankObject}
            {#each Object.keys(financeMonthRankObject) as financeMonth}
              <button 
                class="border border-gray-400 h-[30px] rounded-md px-2 mr-1 my-0.5 {selectedMonthRank === financeMonth ? 'bg-gray-200' : 'bg-white'}" 
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
        <div class="flex grow rounded-md overflow-auto">
          {#if monthlyLoadProgress}
            <div class="flex w-full h-full justify-center items-center font-bold text-gray">
              <ProgressCircle
                size={60}
                thickness={8}
                isLarge={false}
                text={'차트 업데이트 중...'}
              />
            </div>
          {:else if selectedFinanceMonthRankList.length > 0 && loadProgress === false}
            <div class="h-auto">
              <BarChart
                barDataList={setFinanceListByTopAverageRankSumAvg(selectedFinanceMonthRankList)}
                on:pointClick={handleBarChartPointClick}
                on:chartRendered={handleChartRendered}
              />
            </div>
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
            class="border w-[280px] px-2 py-1 rounded-md text-sm"
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
            <div class="px-3 py-1 bg-green-50 border border-green-200 rounded-full text-sm text-green-700">
              🔍 '<span class="font-semibold">{searchMonthStockText}</span>' 검색 중 - {filteredMonthRankList.length}개 결과
            </div>
          </div>
        {/if}
        <div class="flex h-full w-full">
          <div class="tableWrap p-1">
            <table>
              <thead>
                <tr tabindex="0">
                  <th style="width: 5%; text-align: center;">Rank</th>
                  <th style="width: 10%; text-align: center;">RankAvg</th>
                  <th style="width: 10%; text-align: center;">CountSum</th>
                  <th style="width: 30%; text-align: center;">코드</th>
                  <th style="width: 45%; text-align: left;">주식명</th>
                </tr>
              </thead>
              <tbody style="height: {(innerHeight / 2) - 135}px">
                {#if monthlyLoadProgress}
                  <div class="flex w-full h-full justify-center items-center font-bold text-gray">
                    <ProgressCircle
                      size={60}
                      thickness={8}
                      isLarge={false}
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
        <!-- 월별 테이블 페이지네이션 -->
        {#if filteredMonthRankList.length > itemsPerPage}
          <div class="flex justify-center items-center space-x-3 py-1">
            <button 
              class="group relative w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold transition-all duration-300 transform {monthTableCurrentPage === 0 ? 'bg-gray-100 border-gray-300 text-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-green-500 to-green-600 border-green-500 text-white hover:from-green-600 hover:to-green-700 hover:scale-110 hover:shadow-lg active:scale-95'}"
              disabled={monthTableCurrentPage === 0}
              on:click={() => {
                monthTableCurrentPage = Math.max(0, monthTableCurrentPage - 1);
                // requestAnimationFrame으로 즉시 스크롤 실행
                requestAnimationFrame(() => scrollToTableTop('month'));
              }}
              title="이전 페이지"
            >
              <svg class="w-3 h-3 transition-transform duration-200 group-hover:-translate-x-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </button>
            
            <div class="flex items-center space-x-2">
              <span class="px-3 py-1 text-xs font-semibold bg-gradient-to-r from-gray-50 to-gray-100 rounded-full border-2 border-gray-200 shadow-sm">
                <span class="text-green-600">{monthTableCurrentPage + 1}</span>
                <span class="text-gray-400 mx-1">/</span>
                <span class="text-gray-600">{monthTableMaxPage}</span>
              </span>
              {#if searchMonthStockText.trim() !== ''}
                <span class="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full border border-green-200">
                  검색: {filteredMonthRankList.length}/{selectedFinanceMonthRankList.length}
                </span>
              {:else}
                <span class="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full border border-gray-200">
                  총 {filteredMonthRankList.length}개
                </span>
              {/if}
            </div>
            
            <button 
              class="group relative w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold transition-all duration-300 transform {monthTableCurrentPage >= monthTableMaxPage - 1 ? 'bg-gray-100 border-gray-300 text-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-green-500 to-green-600 border-green-500 text-white hover:from-green-600 hover:to-green-700 hover:scale-110 hover:shadow-lg active:scale-95'}"
              disabled={monthTableCurrentPage >= monthTableMaxPage - 1}
              on:click={() => {
                monthTableCurrentPage = Math.min(monthTableMaxPage - 1, monthTableCurrentPage + 1);
                // requestAnimationFrame으로 즉시 스크롤 실행
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

  /* 페이지네이션 버튼 호버 효과 강화 */
  .group:hover svg {
    transition: transform 0.2s ease-in-out;
  }

  /* 스크롤바 스타일링 (선택사항) */
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