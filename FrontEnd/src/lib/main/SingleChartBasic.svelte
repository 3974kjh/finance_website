<script lang="ts">
  import { onMount, tick, createEventDispatcher } from 'svelte';
  import { LineChart, ProgressCircle, NewsInfoListComponent } from '$lib/component';
  import { getExpectStockValue } from '$lib/api-connector/FinanceApi';
  import { getSearchResultByNaverApi } from '$lib/api-connector/NaverApi';
  import { 
    getFinanceDataListByChartMode, 
    setUpDownRatioTag, setUpDownIcon, setUpDownColor, 
    calculateExpectFinanceScore,
    getNewInfoList
  } from '$lib/main';
  import { calculateRatio, formatCostValue, formatIncludeComma } from '$lib/utils/CommonHelper';
  import { NaverFinanceImg, CompanyGuideImg } from '$lib/images/logo';

  export let singleChartInfo: {
		title: string,
		searchDuration: {month: number, week: number},
		chartMode: string,
		chartKey: string,
    detailInfo: any
	};

  const dispatch = createEventDispatcher();

  let dataList: any = [];

  let durationModeList: Array<{name: string, value: {month: number, week: number}, isSelected: boolean}> = [
    { name: '10 YEAR', value: {month: 120, week: 520}, isSelected: false },
    { name: '5 YEAR', value: {month: 60, week: 260}, isSelected: false },
    { name: '2 YEAR', value: {month: 24, week: 104}, isSelected: false },
    { name: '1 YEAR', value: {month: 12, week: 52}, isSelected: true },
    { name: '6 MONTH', value: {month: 6, week: 26}, isSelected: false }
  ]

  let expectValue: string = '';
  let afterMonthExpectValue: string = '';
  let nowValue: string = '';
  let bottomValue: string = '';
  let topValue: string = '';
  let expectRatioValue: string = '';

  let calcSignalScoreResult = {
    crossNormalizeValue: null,
    volumeNormalizeValue: null,
    lineNormalizeValue: null,
    expectNormalizeValue: null
  }

  let signalScoreWeight = {
    crossWeight: 35,
    volumeWeight: 25,
    lineWeight: 15,
    expectWeight: 25
  }

  let isProgress: boolean = false;

  let newInfoList: any = [];

  onMount(async () => {
    if (!!!singleChartInfo) {
      return;
    }

    isProgress = true;

    durationModeList = setSelectDurationModeList(durationModeList, singleChartInfo?.searchDuration);
    dataList = await setSingleChartDataList(singleChartInfo?.searchDuration);
    newInfoList = await getNewInfoList(singleChartInfo.title, 20, 1);

    isProgress = false;
  })

  const getSelectedDurationModeValue = (list: any) => {
    const selectedDurationMode = list.find((item: any) => item.isSelected);

    return selectedDurationMode?.value;
  }

  const setSelectDurationModeList = (list: any, durationValue: any) => {
    if (list.length < 1) {
      return [];
    }

    return list.map((item: any) => {
      if (item.value?.month === durationValue?.month) {
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

  /**
   * 해당 주식의 상세 그래프 표시를 위한 데이터 값 조회
  */
  const setSingleChartDataList = async (duration: {month: number, week: number}) => {
    const financeDataResult = await getFinanceDataListByChartMode(singleChartInfo.chartKey, duration.month, true);

    if (financeDataResult.length < 1) {
      return [];
    }
    
    const expectResult = await getExpectStockValue({symbol: singleChartInfo.chartKey, term: duration.week});

    if (!!!expectResult || !!!expectResult?.data || expectResult.length < 1) {
      return [];
    }

    nowValue = expectResult.data?.nowValue;
    expectValue = expectResult.data?.expectValue;
    afterMonthExpectValue = expectResult.data?.afterMonthExpectValue;
    bottomValue = expectResult.data?.bottomValue;
    topValue = expectResult.data?.topValue;
    expectRatioValue = expectResult.data?.expectRatioValue;

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
    calcSignalScoreResult = calculateExpectFinanceScore(
      financeDataResult,
      parseFloat(singleChartInfo.detailInfo?.marcap),
      parseFloat(singleChartInfo.detailInfo?.amount),
      parseFloat(topValue),
      parseFloat(bottomValue),
      parseFloat(expectValue),
      parseFloat(expectRatioValue)
    )

    return financeDataResult.map((data: any, index: number) => {
      return {
        ...data,
        afterMonthExpectValue: expectResult.data?.afterMonthExpectValue,
        bottomValue: expectResult.data?.bottomValue,
        expectValue: expectResult.data?.expectValue,
        nowValue: expectResult.data?.nowValue,
        topValue: expectResult.data?.topValue,
        ma5: ma5[index] ?? undefined,
        ma20: ma20[index] ?? undefined,
        ma60: ma60[index] ?? undefined,
      }
    });
  }

  /**
   * 가중치 총 합 리턴
  */
  const sumWeight = (scoreWeight: any) => {
    return scoreWeight.crossWeight + scoreWeight.volumeWeight + scoreWeight.lineWeight + scoreWeight.expectWeight;
  }

  /**
   * score와 가중치를 곱한 최종 결과 값 리턴
  */
  const calculateSignalScore = (score: any, scoreWeight: any) => {
    return scoreWeight.crossWeight * score.crossNormalizeValue + scoreWeight.volumeWeight * score.volumeNormalizeValue + scoreWeight.lineWeight * score.lineNormalizeValue + scoreWeight.expectWeight * score.expectNormalizeValue;
  }

  /**
   * 버튼 기간 명 표시 문구
  */
  const showDurationButtonText = (durationName: string) => {
    if (durationName.includes(' YEAR')) {
      return durationName.replace(' YEAR', '년');
    } else {
      return durationName.replace(' MONTH', '달');
    }
  }

  let clientHeight: number = 0;

  $: console.log(clientHeight);

</script>

<div class="flex flex-col w-full h-full bg-white absolute p-2 space-y-2" style="top: 0px; left: 0px" bind:clientHeight={clientHeight}>
  {#if singleChartInfo}
    <div class="flex w-full h-auto">
      <button on:click={() => {
        dispatch('closeSingleChartModeCallback');
      }}>🔙</button>
      <div class="flex grow justify-center font-bold">
        {singleChartInfo?.title ?? '-'}
      </div>
      <div class="flex justify-end mr-2 space-x-1">
        <a 
          class="border rounded-md"
          href="{`https://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A${singleChartInfo?.chartKey ?? ''}`}"
          title="FnGuide_{singleChartInfo?.title}"
          target="_blank"
          style="
            background-image: url({CompanyGuideImg});
            background-size: cover;
            background-position: center;
            width: 28px;   /* 버튼 크기 지정 */
            height: 28px;
          "
        />
        <a
          class="border rounded-md"
          href="{`https://finance.naver.com/item/main.naver?code=${singleChartInfo?.chartKey ?? ''}`}"
          title="NAVER_{singleChartInfo?.title}"
          target="_blank"
          style="
            background-image: url({NaverFinanceImg});
            background-size: cover;
            background-position: center;
            width: 28px;   /* 버튼 크기 지정 */
            height: 28px;
          "
        />
      </div>
    </div>
    <div class="flex flex-row w-full grow space-x-2" style="height: {clientHeight - 50}px">
      <div class="flex w-[80%] h-full border rounded-md">
        {#if dataList.length > 0 && isProgress === false}
          {#key dataList}
            <LineChart
              lineDataList={dataList}
              isMultiLine={true}
              isDetailMode={true}
            />
          {/key}
        {:else if isProgress}
          <div class="flex w-full h-full justify-center items-center font-bold text-gray">
            <ProgressCircle
              size={100}
              thickness={10}
              isLarge={true}
              text={'해당 종목 분석 중...'}
            />
          </div>
        {:else}
          <div class="flex w-full h-full justify-center items-center font-bold text-gray">
            {'해당 종목의 조회 데이터가 없습니다.'}
          </div>
        {/if}
      </div>
      <div class="flex flex-col w-[20%] h-full border rounded-md p-2 space-y-2 overflow-auto scrollbar-thin-custom">
        <!-- 조회 기간 설정 -->
        <div class="flex flex-row w-full items-center border rounded-md bg-gray-50 p-2">
          <p class="w-[30%]">조회 기간</p>
          <div class="grow space-x-1">
            {#each durationModeList as durationMode}
              <button
                class="border rounded-md px-1 border-gray-400 {durationMode.isSelected ? 'bg-gray-200' : 'bg-white'}"
                on:click={async () => {
                  isProgress = true;

                  durationModeList = setSelectDurationModeList(durationModeList, durationMode.value);
                  dataList = await setSingleChartDataList(durationMode.value);

                  isProgress = false;
                }}
              >
                {showDurationButtonText(durationMode.name)}
              </button>
            {/each}
          </div>
        </div>
        <!-- 예측 데이터 값 표시 -->
        <div class="flex flex-col w-full border rounded-md bg-gray-50 p-2 space-y-2">
          <div class="flex flex-row h-auto w-full items-center">
            <p class="w-[30%]">현재 가</p>
            <div class="grow">
              {`${formatIncludeComma(formatCostValue(dataList[dataList.length - 1]?.Close)) ?? '-'} ₩`}
            </div>
          </div>
          <div class="flex flex-row h-auto w-full items-center">
            <p class="w-[30%]">현재 예측가</p>
            <div class="grow">
              <span>{`${formatIncludeComma(expectValue) ?? '-'} ₩`}</span>
              {@html setUpDownRatioTag(formatCostValue(dataList[dataList.length - 1]?.Close) ?? 0, expectValue ?? 0)}
            </div>
          </div>
          <div class="flex flex-row h-auto w-full items-center">
            <p class="w-[30%]">한달뒤 예측가</p>
            <div class="grow">
              <span>{`${formatIncludeComma(afterMonthExpectValue) ?? '-'} ₩`}</span>
              {@html setUpDownRatioTag(formatCostValue(dataList[dataList.length - 1]?.Close) ?? 0, afterMonthExpectValue ?? 0)}
            </div>
          </div>
          <div class="flex flex-row h-auto w-full items-center">
            <p class="w-[30%]">지지평균값</p>
            <div class="grow">
              <span>{`${formatIncludeComma(bottomValue) ?? '-'} ₩`}</span>
              {@html setUpDownRatioTag(formatCostValue(dataList[dataList.length - 1]?.Close) ?? 0, bottomValue ?? 0)}
            </div>
          </div>
          <div class="flex flex-row h-auto w-full items-center">
            <p class="w-[30%]">저항평균값</p>
            <div class="grow">
              <span>{`${formatIncludeComma(topValue) ?? '-'} ₩`}</span>
              {@html setUpDownRatioTag(formatCostValue(dataList[dataList.length - 1]?.Close) ?? 0, topValue ?? 0)}
            </div>
          </div>
        </div>
        <!-- 이평선 데이터 값 표시 -->
        <div class="flex flex-col w-full border rounded-md bg-gray-50 p-2 space-y-2">
          <div class="flex flex-row h-auto w-full items-center">
            <p class="w-[30%]">5일 이평선</p>
            <div class="grow">
              <span>{`${formatIncludeComma(dataList[dataList.length - 1]?.ma5) ?? '-'} ₩`}</span>
              {@html setUpDownRatioTag(dataList[dataList.length - 1]?.ma5 ?? 0, nowValue ?? 0)}
              <span>{'(단기 추세)'}</span>
            </div>
          </div>
          <div class="flex flex-row h-auto w-full items-center">
            <p class="w-[30%]">20일 이평선</p>
            <div class="grow">
              <span>{`${formatIncludeComma(dataList[dataList.length - 1]?.ma20) ?? '-'} ₩`}</span>
              {@html setUpDownRatioTag(dataList[dataList.length - 1]?.ma20 ?? 0, dataList[dataList.length - 1]?.ma5 ?? 0)}
              <span>{'(중기 추세)'}</span>
            </div>
          </div>
          <div class="flex flex-row h-auto w-full items-center">
            <p class="w-[30%]">60일 이평선</p>
            <div class="grow">
              <span>{`${formatIncludeComma(dataList[dataList.length - 1]?.ma60) ?? '-'} ₩`}</span>
              {@html setUpDownRatioTag(dataList[dataList.length - 1]?.ma60 ?? 0, dataList[dataList.length - 1]?.ma20 ?? 0)}
              <span>{'(장기 추세)'}</span>
            </div>
          </div>
        </div>
        <!-- 항목 데이터 값 표시 -->
        {#if dataList.length > 0}
          <div class="flex flex-col w-full border rounded-md bg-gray-50 p-2 space-y-2">
            <div class="flex flex-row h-auto w-full items-center">
              <p class="w-[30%]">종목 명</p>
              <div class="grow">
                {singleChartInfo.detailInfo?.name ?? '-'}
              </div>
            </div>
            <div class="flex flex-row h-auto w-full items-center">
              <p class="w-[30%]">종목 코드</p>
              <div class="grow">
                {singleChartInfo.detailInfo?.code ?? '-'}
              </div>
            </div>
            <div class="flex flex-row h-auto w-full items-center">
              <p class="w-[30%]">현재가</p>
              <div class="grow">
                {`${formatIncludeComma(formatCostValue(dataList[dataList.length - 1]?.Close)) ?? '-'} ₩`}
              </div>
            </div>
            <div class="flex flex-row h-auto w-full items-center">
              <p class="w-[30%]">전일대비</p>
              <div class="grow" style="color: {setUpDownColor(singleChartInfo.detailInfo?.chagesRatio)}">
                {`${setUpDownIcon(singleChartInfo.detailInfo?.chagesRatio)}${singleChartInfo.detailInfo?.chagesRatio ?? '-'}%`}
              </div>
            </div>
            <div class="flex flex-row h-auto w-full items-center">
              <p class="w-[30%]">시초가</p>
              <div class="grow">
                <span>{`${formatIncludeComma(formatCostValue(dataList[dataList.length - 1]?.Open)) ?? '-'} ₩`}</span>
                {@html setUpDownRatioTag(nowValue ?? 0, dataList[dataList.length - 1]?.Open ?? 0)}
              </div>
            </div>
            <div class="flex flex-row h-auto w-full items-center">
              <p class="w-[30%]">일일최고가</p>
              <div class="grow">
                <span>{`${formatIncludeComma(formatCostValue(dataList[dataList.length - 1]?.High)) ?? '-'} ₩`}</span>
                {@html setUpDownRatioTag(nowValue ?? 0, dataList[dataList.length - 1]?.High ?? 0)}
              </div>
            </div>
            <div class="flex flex-row h-auto w-full items-center">
              <p class="w-[30%]">일일최저가</p>
              <div class="grow">
                <span>{`${formatIncludeComma(formatCostValue(dataList[dataList.length - 1]?.Low)) ?? '-'} ₩`}</span>
                {@html setUpDownRatioTag(nowValue ?? 0, dataList[dataList.length - 1]?.Low ?? 0)}
              </div>
            </div>
            <div class="flex flex-row h-auto w-full items-center">
              <p class="w-[30%]">일일거래량</p>
              <div class="grow">
                {`${formatIncludeComma(dataList[dataList.length - 1]?.Volume) ?? '-'} (주)`}
              </div>
            </div>
            <div class="flex flex-row h-auto w-full items-center">
              <p class="w-[30%]">시가총액</p>
              <div class="grow">
                {`${formatIncludeComma(singleChartInfo.detailInfo?.marcap) ?? '-'} ₩`}
              </div>
            </div>
            <div class="flex flex-row h-auto w-full items-center">
              <p class="w-[30%]">일일거래대금</p>
              <div class="grow">
                {`${formatIncludeComma(singleChartInfo.detailInfo?.amount) ?? '-'} ₩`}
              </div>
            </div>
            <div class="flex flex-row h-auto w-full items-center">
              <p class="w-[30%]">거래 유동성</p>
              <div class="grow">
                {`${calculateRatio(singleChartInfo.detailInfo?.marcap, singleChartInfo.detailInfo?.amount) ?? '-'}% (1%이상 좋음, 5%이상 매우좋음)`}
              </div>
            </div>
          </div>
        {/if}
        <!-- 주가 점수 데이터 값 표시 -->
        <div class="flex flex-col w-full border rounded-md bg-gray-50 p-2 space-y-2">
          <div class="flex flex-row h-auto w-full items-center">
            <p class="w-[23%] bg-gray-200">추세 신호</p>
            <p class="w-[27%] bg-gray-200">(0 ~ 1)</p>
            <div class="flex flex-row grow">
              <p class="w-[30%]" style="text-align: right;">{calcSignalScoreResult?.crossNormalizeValue ?? '-'}</p>
              <div class="flex grow justify-end">
                <span class="mr-2">가중치</span>
                <input autocomplete="off" bind:value={signalScoreWeight.crossWeight} placeholder="입력" type="number" class="border w-[50px] px-1 mr-1" max={100} min={0}/>
                <span>%</span>
              </div>
            </div>
          </div>
          <div class="flex flex-row h-auto w-full items-center">
            <p class="w-[23%] bg-gray-200">거래량</p>
            <p class="w-[27%] bg-gray-200">(0 ~ 1)</p>
            <div class="flex flex-row grow">
              <p class="w-[30%]" style="text-align: right;">{calcSignalScoreResult?.volumeNormalizeValue ?? '-'}</p>
              <div class="flex grow justify-end">
                <span class="mr-2">가중치</span>
                <input autocomplete="off" bind:value={signalScoreWeight.volumeWeight} placeholder="입력" type="number" class="border w-[50px] px-1 mr-1" max={100} min={0}/>
                <span>%</span>
              </div>
            </div>
          </div>
          <div class="flex flex-row h-auto w-full items-center">
            <p class="w-[23%] bg-gray-200">지지/저항</p>
            <p class="w-[27%] bg-gray-200">(0 ~ 1)</p>
            <div class="flex flex-row grow">
              <p class="w-[30%]" style="text-align: right;">{calcSignalScoreResult?.lineNormalizeValue ?? '-'}</p>
              <div class="flex grow justify-end">
                <span class="mr-2">가중치</span>
                <input autocomplete="off" bind:value={signalScoreWeight.lineWeight} placeholder="입력" type="number" class="border w-[50px] px-1 mr-1" max={100} min={0}/>
                <span>%</span>
              </div>
            </div>
          </div>
          <div class="flex flex-row h-auto w-full items-center">
            <p class="w-[23%] bg-gray-200">예측 추세</p>
            <p class="w-[27%] bg-gray-200">(0 ~ 1)</p>
            <div class="flex flex-row grow">
              <p class="w-[30%]" style="text-align: right;">{calcSignalScoreResult?.expectNormalizeValue ?? '-'}</p>
              <div class="flex grow justify-end">
                <span class="mr-2">가중치</span>
                <input autocomplete="off" bind:value={signalScoreWeight.expectWeight} placeholder="입력" type="number" class="border w-[50px] px-1 mr-1" max={100} min={0}/>
                <span>%</span>
              </div>
            </div>
          </div>
          <div class="border w-full h-[1px]"/>
          <div class="flex flex-row h-auto w-full items-center">
            <p class="w-[23%] {calculateSignalScore(calcSignalScoreResult, signalScoreWeight) > 50 ? 'bg-red-100 text-red-500' : 'bg-blue-100 text-blue-500'} font-bold">Total Score</p>
            <p class="w-[27%] {calculateSignalScore(calcSignalScoreResult, signalScoreWeight) > 50 ? 'bg-red-100 text-red-500' : 'bg-blue-100 text-blue-500'} font-bold">(0 ~ 100)</p>
            <div class="flex flex-row grow">
              <p style="text-align: right;" class="{calculateSignalScore(calcSignalScoreResult, signalScoreWeight) > 50 ? 'text-red-500' : 'text-blue-500'} w-[30%] font-bold">{calculateSignalScore(calcSignalScoreResult, signalScoreWeight) ?? '-'}</p>
              <div class="flex grow justify-end">
                <span class="mr-2">총계 </span>
                <input autocomplete="off" disabled value={sumWeight(signalScoreWeight)} placeholder="전체" type="text" class="border w-[50px] px-1 mr-1" max={100} min={0}/>
                <span>%</span>
              </div>
            </div>
          </div>
        </div>
        <!-- 뉴스 정보 -->
        <div class="flex flex-col h-[345px]">
          <NewsInfoListComponent
            bind:newInfoList
          />
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  /* Firefox용 */
  .scrollbar-thin-custom {
    scrollbar-width: thin;           /* 얇은 스크롤바 */
    scrollbar-color: #000000 transparent; /* 썸 색상, 트랙은 투명 */
  }
  /* Webkit(크롬, 사파리 등)용 */
  .scrollbar-thin-custom::-webkit-scrollbar {
    height: 6px;                     /* 가로 스크롤바 두께 */
    background: transparent;         /* 트랙(배경) 투명 */
  }
  .scrollbar-thin-custom::-webkit-scrollbar-thumb {
    background: #000000;                /* 썸(움직이는 부분) 색상 */
    border-radius: 4px;              /* 둥근 모서리 */
  }
  .scrollbar-thin-custom::-webkit-scrollbar-thumb:hover {
    background: #555;                /* 썸 호버 시 색상 */
  }
</style>