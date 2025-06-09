<script lang="ts">
  import Chart from 'devextreme/viz/chart';
  import { onMount, tick, createEventDispatcher } from 'svelte';
  import { selfNormalize } from '$lib/main/MainCore';
  import _ from 'lodash';

  export let barDataList: any = [];

  let maxRankSum: number = 0;
  let minRankSum: number = 0;

  // 이벤트 디스패처 생성
  const dispatch = createEventDispatcher();

/**
 * bar Chart 영역
 */
  let barChart: HTMLDivElement;

  onMount(async () => {
    maxRankSum = _.maxBy(barDataList, 'rankSum')?.rankSum ?? 0;
    minRankSum = _.minBy(barDataList, 'rankSum')?.rankSum ?? 0;

    await tick();

    createCountBarChart();
  })

  const getSeriesList = () => {
    return [
      { valueField: 'count', name: '상위도달횟수', type: 'bar', axis: 'first', barWidth: 20, color: '#475569' },
      { valueField: 'rankNormalize', name: '랭크일반화', type: 'line', axis: 'second', width: 3, color: '#FFA500' }
    ];
  }

  /**
   * 바 차트
   */
  const createCountBarChart = () => {
    if (!!!barDataList || barDataList.length < 1) {
      return;
    }

    barDataList = _.orderBy(barDataList.map((item) => {
      return {
        ...item,
        count: parseInt(item.count),
        rankNormalize: 100 - (selfNormalize(item.rankSum, minRankSum, maxRankSum) * 100)
      };
    }), 'rankNormalize', 'desc');

    let maxValue: number = (_.maxBy(barDataList, 'count')?.count ?? 0);

    new Chart(barChart, {
      dataSource: barDataList,
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
            color: e.seriesName === '랭크일반화' ? '#FFF7ED' : '#E5E7EB',
            hoverStyle: {
              color: e.seriesName === '랭크일반화' ? '#FFA500' : '#475569'
            }
          };
        }

        return null;
      },
      customizeLabel: (e: any) => {
        if (e.data.name === '횟수') {
          return {
            visible: true,
            backgroundColor: e.seriesName === '랭크일반화' ? '#FFA500' : '#475569',
            customizeText() {
              return `전체 ${e.data.count}회`;
            },
          };
        }

        return null;
      },
      valueAxis: [
        {
          title: {
            text: '상위도달횟수',
            font: {
              size: 13,
              color: '#475569'
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
				customizeTooltip: function (arg: { value: number, argument: string, point: {data:{code: string, name: string, rankSum: string, count: number}}, seriesName: string }) {
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
      }
    });
  }
</script>

<div bind:this={barChart} class="h-[calc(100%)] w-[3500px]"/>