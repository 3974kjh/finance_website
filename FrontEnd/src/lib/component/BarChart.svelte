<script lang="ts">
  import { onMount, tick, createEventDispatcher } from 'svelte';
  import { selfNormalize } from '$lib/main/MainCore';
  import { browser } from '$app/environment';

  export let barDataList: any = [];

  let maxRankSum: number = 0;
  let minRankSum: number = 0;
  let chartInstance: any = null;

  // 이벤트 디스패처 생성
  const dispatch = createEventDispatcher();

  /**
   * bar Chart 영역
   */
  let barChart: HTMLDivElement;

  // 이전 데이터 해시값으로 변경 감지 최적화
  let previousDataHash: string = '';

  // barDataList가 변경될 때만 차트 업데이트
  $: if (barDataList && barDataList.length > 0) {
    const currentHash = `${barDataList.length}_${barDataList[0]?.code || ''}_${barDataList[barDataList.length - 1]?.code || ''}`;
    if (currentHash !== previousDataHash) {
      previousDataHash = currentHash;
      handleDataChange();
    }
  }

  // 데이터 변경 처리 함수 (더 직접적인 제어)
  const handleDataChange = () => {
    if (chartInstance) {
      // 기존 차트가 있으면 즉시 데이터만 업데이트
      const processedData = prepareChartData();
      chartInstance.option('dataSource', processedData);
      
      // 업데이트 완료 이벤트 발생
      setTimeout(() => {
        dispatch('chartRendered');
      }, 50); // 더 짧은 대기 시간
    } else if (barChart) {
      // 차트가 없으면 새로 생성
      createCountBarChart();
    }
  };

  let Chart: any;

  onMount(async () => {
    if (!browser) return;

    // 동적으로 devextreme import
    try {
      const module = await import('devextreme/viz/chart');
      Chart = module.default;
      
      await tick();
      if (barDataList && barDataList.length > 0) {
        createCountBarChart();
      }
    } catch (error) {
      console.error('Failed to load chart library:', error);
    }
  })

  const prepareChartData = () => {
    if (!barDataList || barDataList.length < 1) {
      return [];
    }

    // 이미 처리된 데이터라고 가정하고 최소한의 처리만 수행
    maxRankSum = Math.max(...barDataList.map(item => item.rankAvg || 0));
    minRankSum = Math.min(...barDataList.map(item => item.rankAvg || 0));

    return barDataList.map(item => ({
      ...item,
      count: typeof item.count === 'number' ? item.count : parseInt(item.count) || 0,
      rankNormalize: Math.round(100 - (selfNormalize(item.rankAvg, minRankSum, maxRankSum) * 100))
    })).sort((a, b) => b.rankNormalize - a.rankNormalize);
  }

  const getSeriesList = () => {
    return [
      { valueField: 'count', name: '상위도달횟수', type: 'bar', axis: 'first', barWidth: 20, color: '#E5E7EB' },
      { valueField: 'rankNormalize', name: '랭크일반화', type: 'line', axis: 'second', width: 3, color: '#FFA500' }
    ];
  }

  /**
   * 바 차트
   */
  const createCountBarChart = () => {
    if (!barDataList || barDataList.length < 1) {
      return;
    }

    const processedData = prepareChartData();
    const maxValue = Math.max(...processedData.map(item => item.count));

    chartInstance = new Chart(barChart, {
      dataSource: processedData,
      commonSeriesSettings: {
        argumentField: 'code'
      },
      argumentAxis: {
        visible: true,
        label: {
          wordWrap: 'none',
          overlappingBehavior: 'stagger',
          customizeText: function (arg: { value? : any; }) {
            return arg.value;
          },
        },
        grid: {
          visible: false,
        }
      },
      customizePoint: (e: any) => {
        if (e.data.name === '횟수') {
          return { 
            color: e.seriesName === '랭크일반화' ? '#FFF7ED' : '#EC4899',
            hoverStyle: {
              color: e.seriesName === '랭크일반화' ? '#FFA500' : '#BE185D'
            }
          };
        }

        return {};
      },
      customizeLabel: (e: any) => {
        if (e.data.name === '횟수') {
          return {
            visible: true,
            backgroundColor: e.seriesName === '랭크일반화' ? '#FFA500' : '#EC4899',
            customizeText() {
              return `전체 ${e.data.count}회`;
            },
          };
        }

        return {};
      },
      valueAxis: [
        {
          title: {
            text: '상위도달횟수',
            font: {
              size: 13,
              color: '#E5E7EB'
            }
          },
          name: 'first',
          visible: true,
          label: {
            customizeText: function (arg: { value? : any; }) {
              let value = typeof arg?.value === 'number' ? arg?.value.toString() : arg?.value;
              return value;
            },
          },
          grid: {
            visible: true,
          },
          tick: { 
            visible: true
          },
          visualRange: {
            startValue: 0, // valueAxis의 최소값 지정
            endValue: maxValue + 1 // valueAxis의 최대값 지정
          }
        },
        {
          title: {
            text: '랭크일반화',
            font: {
              size: 13,
              color: '#FFA500'
            }
          },
          name: 'second',
          visible: true,
          position: 'left',
          label: {
            customizeText: function (arg: { value? : any; }) {
              let value = typeof arg?.value === 'number' ? Math.round(arg?.value).toString() : arg?.value;
              return value;
            },
          },
          grid: {
            visible: true,
          },
          tick: { 
            visible: true
          },
          visualRange: {
            startValue: 0, // valueAxis의 최소값 지정
            endValue: 100 // valueAxis의 최대값 지정
          }
        }
      ],
      legend: {
        verticalAlignment: "bottom",
        horizontalAlignment: "left",
        visible: true,
        position: "inside"
      },
      series: getSeriesList() as any,
      export: {
        enabled: false,
      },
      tooltip: {
				enabled: true,
				location: 'edge',
				zIndex: 99999,
				customizeTooltip: function (arg: { value: number, argument: string, point: {data: any}, seriesName: string }) {
          let toolTipText: string = '';

          const focusFinanceInfo = arg.point?.data;

          if (arg?.seriesName === "랭크일반화") {
            toolTipText = `코드: ${focusFinanceInfo?.code ?? '-'} | 주식명: ${focusFinanceInfo?.name ?? '-'} | 랭크일반화: ${focusFinanceInfo?.rankNormalize ?? '-'} (순위총합: ${focusFinanceInfo?.rankSum ?? '-'})`;
          } else {
            toolTipText = `코드: ${focusFinanceInfo?.code ?? '-'} | 주식명: ${focusFinanceInfo?.name ?? '-'} | 상위도달횟수: ${focusFinanceInfo?.count ?? '-'}`;
          }

					return {
						text: toolTipText
					};
				}
			},
      onLegendClick(e) {
        const series = e.target;
        if (series.isVisible()) {
          series.hide();
        } else {
          series.show();
        }
      },
      // 포인트 클릭 이벤트 추가
      onPointClick(e) {
        const clickedItem = e.target.data;
        
        // '횟수' 항목은 클릭 이벤트를 발생시키지 않음
        if (clickedItem?.name === '횟수') {
          return;
        }

        // 클릭된 항목 데이터를 상위 컴포넌트로 dispatch
        dispatch('pointClick', {
          item: clickedItem,
          seriesName: e.target.series.name
        });
      },
      // 차트 렌더링 완료 이벤트 추가
      onDrawn() {
        dispatch('chartRendered');
      }
    });
  }
</script>

<div bind:this={barChart} class="h-[calc(100%)] w-[3500px]"/>

<style>
  /* DevExtreme 차트 툴팁을 최상단에 표시 */
  :global(.dx-tooltip) {
    z-index: 999999 !important;
    position: fixed !important;
  }

  :global(.dx-tooltip-wrapper) {
    z-index: 999999 !important;
    position: fixed !important;
  }

  :global(.dx-overlay-wrapper) {
    z-index: 999999 !important;
  }

  :global(.dx-overlay-content) {
    z-index: 999999 !important;
  }

  /* 차트 컨테이너 자체도 적절한 z-index 설정 */
  :global(.dx-chart) {
    position: relative;
    z-index: 100;
  }
</style>