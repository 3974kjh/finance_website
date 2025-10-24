<script lang="ts">
  import { onMount, tick, onDestroy } from 'svelte'; 
  import { formatCostValue, formatIncludeComma } from '$lib/utils/CommonHelper';
  import _ from 'lodash';
  import { browser } from '$app/environment';
	import { setUpDownRatioTag } from '$lib/main';

  export let lineDataList: any = [];

  const getCurrentDate = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}-${month}-${day}`;
  }

  let startDate: string;
  let lastDate: string;
  let upDownGradient: boolean | null = null;
  let Chart: any;
  let chartInstance: any = null; // 성능 최적화: 차트 인스턴스 관리

  /**
   * line Chart 영역
   */
  let lineChart: HTMLDivElement;

  // 대용량 데이터 최적화를 위한 변수들
  let isLargeDataset: boolean = false;
  let optimizedDataSource: any[] = [];
  let lastUpdateTime: number = 0;

  // 대용량 데이터 감지 및 최적화 함수
  const optimizeForLargeDataset = (data: any[]): any[] => {
    if (!data || data.length === 0) return data;

    // 대용량 데이터 임계값 설정 (2년 이상의 데이터)
    isLargeDataset = data.length > 500; // 250 → 500으로 변경

    if (!isLargeDataset) {
      return data; // 소량 데이터는 최적화하지 않음
    }

    // 대용량 데이터 최적화 로직
    const getOptimizedData = (sourceData: any[]): any[] => {
      const dataLength = sourceData.length;
      
      // 데이터 크기에 따른 샘플링 비율 결정
      let samplingRatio = 1;
      if (dataLength > 2000) samplingRatio = 4;      // 5년 이상: 4분의 1
      else if (dataLength > 1000) samplingRatio = 3;  // 3년 이상: 3분의 1
      else if (dataLength > 500) samplingRatio = 2;   // 2년 이상: 2분의 1
      
      if (samplingRatio === 1) return sourceData;

      const optimized: any[] = [];
      
      // 첫 번째 데이터는 항상 포함
      optimized.push(sourceData[0]);
      
      // 샘플링된 데이터 추가
      for (let i = samplingRatio; i < dataLength - samplingRatio; i += samplingRatio) {
        optimized.push(sourceData[i]);
      }
      
      // 마지막 데이터는 항상 포함
      if (dataLength > 1) {
        optimized.push(sourceData[dataLength - 1]);
      }
      
      return optimized;
    };

    return getOptimizedData(data);
  };

  // 스로틀링된 차트 업데이트 함수
  const throttledUpdateChart = _.throttle(() => {
    if (chartInstance && lineDataList.length > 0) {
      const currentTime = Date.now();
      // 너무 빈번한 업데이트 방지
      if (currentTime - lastUpdateTime > 100) {
        lastUpdateTime = currentTime;
        optimizedDataSource = optimizeForLargeDataset(lineDataList);
      }
    }
  }, 150); // 150ms 스로틀링

  onMount(async () => {
    if (!browser) return;

    startDate = lineDataList[0]?.Date;

    const lastData = getLastData(lineDataList);
    lastDate = lastData.date;
    upDownGradient = getUpDownGradient(lineDataList[0]?.Close, lastData?.value);

    // 초기 데이터 최적화
    optimizedDataSource = optimizeForLargeDataset(lineDataList);

    // 동적으로 devextreme import
    try {
      const module = await import('devextreme/viz/chart');
      Chart = module.default;
      
      await tick();
      createMonthLineChart();
    } catch (error) {
      console.error('Failed to load chart library:', error);
    }
  });

  // 성능 최적화: 메모리 정리
  onDestroy(() => {
    if (chartInstance) {
      try {
        chartInstance.dispose();
      } catch (error) {
        console.error('Error disposing chart:', error);
      }
      chartInstance = null;
    }
    
    // 스로틀링 함수 정리
    throttledUpdateChart.cancel();
  });

  const getUpDownGradient = (startValue: any, lastValue: any) => {
    if (!!!startValue || !!!lastValue) {
      return null;
    }

    if (parseFloat(startValue) >= parseFloat(lastValue)) {
      return false;
    } else {
      return true;
    }
  }

  // linter 에러 수정: 리턴 타입 수정
  const getLastData = (list: any): { value: number; date: string } => {
    if (list.length < 1) {
      return {
        value: 0,
        date: getCurrentDate(new Date())
      };
    }

    for (let index = list.length - 1; index > 0; index--) {
      if (list[index].Close !== 0) {
        return {
          value: list[index].Close,
          date: _.cloneDeep(list[index].Date)
        }
      }
    }

    return {
      value: 0,
      date: getCurrentDate(new Date())
    }
  }

  const getSeriesList = () => {
    return [
      { 
        valueField: 'volume',
        name: '거래대금', 
        hoverMode: 'allArgumentPoints', 
        color: '#000000', 
        width: isLargeDataset ? 2 : 3,
        point: { visible: false }
      },
      { 
        valueField: 'vwma5',
        name: '5일VWMA',
        hoverMode: 'allArgumentPoints', 
        color: '#1E90FF', 
        width: isLargeDataset ? 2 : 3,
        point: { visible: false }
      },
      { 
        valueField: 'vwma20', 
        name: '20일VWMA', 
        hoverMode: 'allArgumentPoints', 
        color: '#FFA500', 
        width: isLargeDataset ? 2 : 3,
        point: { visible: false }
      },
      { 
        valueField: 'vwma60', 
        name: '60일VWMA', 
        hoverMode: 'allArgumentPoints', 
        color: '#32CD32', 
        width: isLargeDataset ? 2 : 3,
        point: { visible: false }
      },
      { 
        valueField: 'vwmaAvg', 
        name: 'VWMA평균', 
        hoverMode: 'allArgumentPoints', 
        color: '#000000',
        dashStyle: 'dash',
        width: isLargeDataset ? 2 : 3,
        point: { visible: false }
      }
    ];
  }

  /**
   * 라인 그래프 - 대용량 데이터 최적화 적용
   */
  const createMonthLineChart = () => {
    if (!!!optimizedDataSource || optimizedDataSource.length < 1) {
      return;
    }
    
    // linter 에러 수정: 매개변수 타입 지정
    let maxValue: number = (_.maxBy(optimizedDataSource.filter((item: any) => !!item?.volume && item?.volume > 0), 'volume')?.volume ?? 0) * 1.1;
    let minValue: number = (_.minBy(optimizedDataSource.filter((item: any) => !!item?.volume && item?.volume > 0), 'volume')?.volume ?? 0) * 0.9;

    const topValue: number = optimizedDataSource[0]?.volume ?? 0;
    const bottomValue: number = optimizedDataSource[0]?.volume ?? 0;

    maxValue = maxValue > topValue ? maxValue : topValue;
    minValue = minValue < bottomValue ? minValue : bottomValue;

    chartInstance = new Chart(lineChart, {
      dataSource: optimizedDataSource,
      
      // 대용량 데이터 성능 최적화 설정
      rtlEnabled: false,
      animation: false, // 애니메이션 비활성화로 성능 향상
      redrawOnResize: true,
      
      // Canvas 렌더링 활성화 (SVG보다 성능이 좋음)
      useCanvas: true,
      
      // 대용량 데이터 최적화를 위한 추가 설정
      seriesSelectionMode: 'single',
      pointSelectionMode: 'single',
      
      commonSeriesSettings: {
        argumentField: 'Date',
        point: {
          visible: false, // 포인트 숨김으로 성능 향상
          hoverMode: isLargeDataset ? 'none' : 'allArgumentPoints' // 대용량 데이터는 호버 비활성화
        }
      },
      zoomAndPan: {
        argumentAxis: 'both',
        // 대용량 데이터 최적화: 제스처 및 스크롤 최적화
        allowTouchGestures: true,
        allowMouseWheel: true,
        panKey: 'shift',
        dragToZoom: true
      },
      scrollBar: {
        visible: true,
        position: 'bottom', // 성능 최적화: 스크롤바 위치 최적화
        offset: 5
      },
      customizeLabel: (e: any) => {
        const setTextColor = (seriesName: string) => {
          let color: string = '#1e293b'; // slate-800

          if (seriesName === '거래대금') {
            color = '#1e293b'; // slate-800
          } else if (seriesName === '5일VWMA') {
            color = '#0284c7'; // sky-600
          } else if (seriesName === '20일VWMA') {
            color = '#ea580c'; // orange-600
          } else if (seriesName === '60일VWMA') {
            color = '#16a34a'; // green-600
          } else if (seriesName === 'VWMA평균') {
            color = '#000000'; // gray-600
          }

          return color;
        }

        const setOffsetPadding = (seriesName: string) => {
          let offsetPadding: number = 0;

          if (seriesName === '거래대금') {
            offsetPadding = -100;
          }

          return offsetPadding;
        }

        const setVisible = (seriesName: string, dateString: string) => {
          if (seriesName === '거래대금') {
            return dateString === lastDate;
          }

          return false;
        }

				if (e.data.Date !== startDate && e.data.Date !== lastDate) {
					return {
						visible: false
					};
				}

        return {
          visible: setVisible(e?.seriesName, e.data.Date),
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          border: {
            color: setTextColor(e?.seriesName),
            width: 1
          },
          cornerRadius: 6,
          horizontalOffset: 0,
          verticalOffset: setOffsetPadding(e?.seriesName),
          font: {
            size: 13,
            weight: 600,
            color: setTextColor(e?.seriesName)
          },
          customizeText() {
            let title: string = e?.seriesName ?? '미정';
            let value: number = 0;

            if (e.seriesName === '거래대금') {
              value = typeof e.data.volume === 'string' ? Math.round(parseFloat(e.data.volume) * 10) / 10 : Math.round(e.data.volume * 10) / 10;
            } else if (e.seriesName === '5일VWMA') {
              value = typeof e.data?.vwma5 === 'string' ? Math.round(parseFloat(e.data?.vwma5) * 10) / 10 : Math.round(e.data?.vwma5 * 10) / 10;
            } else if (e.seriesName === '20일VWMA') {
              value = typeof e.data?.vwma20 === 'string' ? Math.round(parseFloat(e.data?.vwma20) * 10) / 10 : Math.round(e.data?.vwma20 * 10) / 10;
            } else if (e.seriesName === '60일VWMA') {
              value = typeof e.data?.vwma60 === 'string' ? Math.round(parseFloat(e.data?.vwma60) * 10) / 10 : Math.round(e.data?.vwma60 * 10) / 10;
            } else if (e.seriesName === 'VWMA평균') {
              value = typeof e.data?.vwmaAvg === 'string' ? Math.round(parseFloat(e.data?.vwmaAvg) * 10) / 10 : Math.round(e.data?.vwmaAvg * 10) / 10;
            }

            return `평균대비 오늘 ${title}: ${setUpDownRatioTag(lineDataList[0]?.vwmaAvg ?? 0, value ?? 0)}`;
          }
        }
      },
      argumentAxis: {
        visible: true,
        label: {
          customizeText: function (arg: { value? : any; }) {
            return arg.value;
          },
        },
        grid: {
          visible: false,
        },
        tick: { 
          visible: true
        },
        // 대용량 데이터 최적화: 축 설정
        tickInterval: isLargeDataset ? 'year' : undefined,
        minorTickInterval: isLargeDataset ? 'month' : undefined,
      },
      valueAxis: [{
        title: {
          text: '거래대금',
          font: {
            size: 13
          }
        },
        visible: true,
        label: {
          customizeText: function (arg: { value? : any; }) {
            let value = typeof arg?.value === 'number' ? arg?.value.toString() : arg?.value;
            return formatIncludeComma(value);
          },
        },
        grid: {
          visible: true,
        },
        tick: { 
          visible: true
        },
        visualRange: {
          startValue: minValue, // valueAxis의 최소값 지정
          endValue: maxValue // valueAxis의 최대값 지정
        }
      }],
      legend: {
        verticalAlignment: "bottom",
        horizontalAlignment: "center",
        visible: true,
      },
      series: getSeriesList() as any,
      export: {
        enabled: false,
      },
      tooltip: {
				enabled: true, // 툴팁 항상 활성화
				location: 'edge',
				shared: true,
				zIndex: 99999,
				customizeTooltip: function (arg: { valueText: string, argument: string, point?: any }) {
          if (!arg.argument) {
            return { text: '' };
          }

          let toolTipText: string = '';
          
          // 멀티라인 모드인 경우 모든 시리즈 정보 표시
          if (arg.point) {
            const data = arg.point.data;
            if (data) {
              let parts: string[] = [];
              parts.push(`날짜: ${arg.argument}`);
              
              if (data.volume !== undefined && data.volume !== null && data.volume !== 0) {
                const volumeValue = typeof data.volume === 'string' ? parseFloat(data.volume) : data.volume;
                parts.push(`거래대금: ${formatIncludeComma(Math.round(volumeValue * 10) / 10)}`);
              }

              if (data.vwma5 !== undefined && data.vwma5 !== null && data.vwma5 !== 0) {
                const vwma5Value = typeof data.vwma5 === 'string' ? parseFloat(data.vwma5) : data.vwma5;
                parts.push(`5일VWMA: ${formatIncludeComma(Math.round(vwma5Value * 10) / 10)}`);
              }
              
              if (data.vwma20 !== undefined && data.vwma20 !== null && data.vwma20 !== 0) {
                const vwma20Value = typeof data.vwma20 === 'string' ? parseFloat(data.vwma20) : data.vwma20;
                parts.push(`20일VWMA: ${formatIncludeComma(Math.round(vwma20Value * 10) / 10)}`);
              }
              
              if (data.vwma60 !== undefined && data.vwma60 !== null && data.vwma60 !== 0) {
                const vwma60Value = typeof data.vwma60 === 'string' ? parseFloat(data.vwma60) : data.vwma60;
                parts.push(`60일VWMA: ${formatIncludeComma(Math.round(vwma60Value * 10) / 10)}`);
              }

              if (data.vwmaAvg !== undefined && data.vwmaAvg !== null && data.vwmaAvg !== 0) {
                const vwmaAvgValue = typeof data.vwmaAvg === 'string' ? parseFloat(data.vwmaAvg) : data.vwmaAvg;
                parts.push(`VWMA평균: ${formatIncludeComma(Math.round(vwmaAvgValue * 10) / 10)}`);
              }
              
              toolTipText = parts.join(' | ');
            }
          }

					return {
						text: toolTipText
					};
				}
			},
      // linter 에러 수정: 매개변수 타입 지정
      onLegendClick(e: any) {
        const series = e.target;
        if (series.isVisible()) {
          series.hide();
        } else {
          series.show();
        }
      },
    });
  }

  // 데이터 변경 감지 및 최적화된 업데이트
  $: if (lineDataList && lineDataList.length > 0) {
    throttledUpdateChart();
  }
</script>

<div bind:this={lineChart} class="h-[calc(100%)] w-[calc(100%)]"/>