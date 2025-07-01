<script lang="ts">
  import { onMount, tick } from 'svelte'; 
  import { formatIncludeComma } from '$lib/utils/CommonHelper';
  import _ from 'lodash';
  import { browser } from '$app/environment';

  export let lineDataList: any = [];
  export let isMultiLine: boolean = false;
  export let isDetailMode: boolean = false;

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

  /**
   * line Chart 영역
   */
  let lineChart: HTMLDivElement;

  onMount(async () => {
    if (!browser) return;

    startDate = lineDataList[0]?.Date;

    const lastData = getLastData(lineDataList);
    lastDate = lastData.date;
    upDownGradient = getUpDownGradient(lineDataList[0]?.Close, lastData?.value);

    // 동적으로 devextreme import
    try {
      const module = await import('devextreme/viz/chart');
      Chart = module.default;
      
      await tick();
      createMonthLineChart();
    } catch (error) {
      console.error('Failed to load chart library:', error);
    }
  })

  const setMainLineColor = (upDown: boolean | null) => {
    if (upDown === null) {
      return '#000000';
    }

    if (upDown) {
      return '#FF0000';
    } else {
      return '#0000FF';
    }
  }

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

  const getLastData = (list: any): string => {
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
    if (!isMultiLine) {
      return [
        { valueField: 'Close', name: '종가', hoverMode: 'allArgumentPoints', color: setMainLineColor(upDownGradient) }
      ];
    }

    if (!isDetailMode) {
      return [
        { valueField: 'Close', name: '종가', hoverMode: 'allArgumentPoints', color: '#000000' },
        { valueField: 'topValue', name: '저항평균선', hoverMode: 'allArgumentPoints', color: '#FF0000', dashStyle: 'dash' },
        { valueField: 'bottomValue', name: '지지평균선', hoverMode: 'allArgumentPoints', color: '#0000FF', dashStyle: 'dash' }
      ];
    } else {
      return [
        { valueField: 'Close', name: '종가', hoverMode: 'allArgumentPoints', color: '#000000', width: 3 },
        { valueField: 'topValue', name: '저항평균선', hoverMode: 'allArgumentPoints', color: '#FF0000', dashStyle: 'dash' },
        { valueField: 'bottomValue', name: '지지평균선', hoverMode: 'allArgumentPoints', color: '#0000FF', dashStyle: 'dash' },
        { valueField: 'ma5', name: '5일이평선', hoverMode: 'allArgumentPoints', color: '#1E90FF', width: 3 },
        { valueField: 'ma20', name: '20일이평선', hoverMode: 'allArgumentPoints', color: '#FFA500', width: 3 },
        { valueField: 'ma60', name: '60일이평선', hoverMode: 'allArgumentPoints', color: '#32CD32', width: 3 }
      ];
    }
  }

  /**
   * 라인 그래프
   */
  const createMonthLineChart = () => {
    if (!!!lineDataList || lineDataList.length < 1) {
      return;
    }
    
    let maxValue: number = (_.maxBy(lineDataList.filter((item) => !!item?.Close && item?.Close > 0), 'Close')?.Close ?? 0) * 1.1;
    let minValue: number = (_.minBy(lineDataList.filter((item) => !!item?.Close && item?.Close > 0), 'Close')?.Close ?? 0) * 0.9;

    const topValue: number = lineDataList[0]?.topValue ?? 0;
    const bottomValue: number = lineDataList[0]?.bottomValue ?? 0;

    if (isMultiLine) {
      maxValue = maxValue > topValue ? maxValue : topValue;
      minValue = minValue < bottomValue ? minValue : bottomValue;
    }

    let nowYear: string | null = null;

    new Chart(lineChart, {
      dataSource: lineDataList,
      commonSeriesSettings: {
        argumentField: 'Date',
        point: {
          visible: false,
          hoverMode: 'allArgumentPoints'
        }
      },
      zoomAndPan: {
        argumentAxis: 'both'
      },
      scrollBar: {
        visible: true,
      },
      customizeLabel: (e: any) => {
        const setTextColor = (seriesName: string) => {
          let color: string = '#1e293b'; // slate-800

          if (seriesName === '종가') {
            color = '#1e293b'; // slate-800
          } else if (seriesName === '저항평균선') {
            color = '#dc2626'; // red-600
          } else if (seriesName === '지지평균선') {
            color = '#2563eb'; // blue-600
          } else if (seriesName === '5일이평선') {
            color = '#0284c7'; // sky-600
          } else if (seriesName === '20일이평선') {
            color = '#ea580c'; // orange-600
          } else if (seriesName === '60일이평선') {
            color = '#16a34a'; // green-600
          }

          return color;
        }

        const setOffsetPadding = (seriesName: string) => {
          let offsetPadding: number = 0;

          if (seriesName === '종가') {
            offsetPadding = 0;
          } else if (seriesName === '저항평균선') {
            offsetPadding = 0;
          } else if (seriesName === '지지평균선') {
            offsetPadding = 45;
          }

          return offsetPadding;
        }

        const setVisible = (seriesName: string, dateString: string) => {
          if (seriesName === '종가') {
            return (!isDetailMode || dateString === startDate);
          }

          if ((seriesName === '저항평균선' || seriesName === '지지평균선') && dateString === startDate) {
            return true;
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

            if (isMultiLine) {
              if (e.seriesName === '종가') {
                value = typeof e.data.Close === 'string' ? Math.round(parseInt(e.data.Close) * 10) / 10 : Math.round(e.data.Close * 10) / 10;
              } else if (e.seriesName === '저항평균선') {
                value = typeof e.data.topValue === 'string' ? Math.round(parseFloat(e.data.topValue) * 10) / 10 : Math.round(e.data.topValue * 10) / 10;
              } else if (e.seriesName === '지지평균선') {
                value = typeof e.data.bottomValue === 'string' ? Math.round(parseFloat(e.data.bottomValue) * 10) / 10 : Math.round(e.data.bottomValue * 10) / 10;
              } else if (e.seriesName === '5일이평선') {
                value = typeof e.data?.ma5 === 'string' ? Math.round(parseFloat(e.data?.ma5) * 10) / 10 : Math.round(e.data?.ma5 * 10) / 10;
              } else if (e.seriesName === '20일이평선') {
                value = typeof e.data?.ma20 === 'string' ? Math.round(parseFloat(e.data?.ma20) * 10) / 10 : Math.round(e.data?.ma20 * 10) / 10;
              } else if (e.seriesName === '60일이평선') {
                value = typeof e.data?.ma60 === 'string' ? Math.round(parseFloat(e.data?.ma60) * 10) / 10 : Math.round(e.data?.ma60 * 10) / 10;
              }
            } else {
              value = typeof e.data.Close === 'string' ? Math.round(parseInt(e.data.Close) * 10) / 10 : Math.round(e.data.Close * 10) / 10;
            }

            return `${title}: ${formatIncludeComma(value)}`;
          }
			  }
      },
      argumentAxis: {
        visible: true,
        label: {
          customizeText: function (arg: { value? : any; }) {
            if (isDetailMode) {
              return arg.value;
            }

            if (!!!nowYear || nowYear !== arg.value.slice(0, 4)) {
              nowYear = _.cloneDeep(arg.value.slice(0, 4));
              return nowYear;
            }

            if (nowYear === arg.value.slice(0, 4)) {
              return '';
            } else if (arg.value !== startDate && arg.value !== lastDate) {
              return '';
            }

            return arg.value;
          },
        },
        grid: {
          visible: false,
        },
        tick: { 
          visible: true
        },
      },
      valueAxis: [{
        title: {
          text: '지수',
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
        visible: isMultiLine,
      },
      series: getSeriesList() as any,
      export: {
        enabled: false,
      },
      tooltip: {
				enabled: true,
				location: 'edge',
				shared: true,
				zIndex: 99999,
				customizeTooltip: function (arg: { valueText: string, argument: string, point?: any }) {
          if (!arg.argument) {
            return { text: '' };
          }

          let toolTipText: string = '';
          
          // 멀티라인 모드인 경우 모든 시리즈 정보 표시
          if (isMultiLine && arg.point) {
            const data = arg.point.data;
            if (data) {
              let parts: string[] = [];
              parts.push(`날짜: ${arg.argument}`);
              
              if (data.Close !== undefined && data.Close !== null && data.Close !== 0) {
                const closeValue = typeof data.Close === 'string' ? parseFloat(data.Close) : data.Close;
                parts.push(`종가: ${formatIncludeComma(Math.round(closeValue * 10) / 10)}`);
              }
              
              if (data.topValue !== undefined && data.topValue !== null && data.topValue !== 0) {
                const topValue = typeof data.topValue === 'string' ? parseFloat(data.topValue) : data.topValue;
                parts.push(`저항평균: ${formatIncludeComma(Math.round(topValue * 10) / 10)}`);
              }
              
              if (data.bottomValue !== undefined && data.bottomValue !== null && data.bottomValue !== 0) {
                const bottomValue = typeof data.bottomValue === 'string' ? parseFloat(data.bottomValue) : data.bottomValue;
                parts.push(`지지평균: ${formatIncludeComma(Math.round(bottomValue * 10) / 10)}`);
              }

              if (isDetailMode) {
                if (data.ma5 !== undefined && data.ma5 !== null && data.ma5 !== 0) {
                  const ma5Value = typeof data.ma5 === 'string' ? parseFloat(data.ma5) : data.ma5;
                  parts.push(`5일이평: ${formatIncludeComma(Math.round(ma5Value * 10) / 10)}`);
                }
                
                if (data.ma20 !== undefined && data.ma20 !== null && data.ma20 !== 0) {
                  const ma20Value = typeof data.ma20 === 'string' ? parseFloat(data.ma20) : data.ma20;
                  parts.push(`20일이평: ${formatIncludeComma(Math.round(ma20Value * 10) / 10)}`);
                }
                
                if (data.ma60 !== undefined && data.ma60 !== null && data.ma60 !== 0) {
                  const ma60Value = typeof data.ma60 === 'string' ? parseFloat(data.ma60) : data.ma60;
                  parts.push(`60일이평: ${formatIncludeComma(Math.round(ma60Value * 10) / 10)}`);
                }
              }
              
              toolTipText = parts.join(' | ');
            }
          } else {
            // 단일 라인 모드인 경우
            if (arg.point && arg.point.data && arg.point.data.Close !== undefined) {
              const closeValue = typeof arg.point.data.Close === 'string' ? parseFloat(arg.point.data.Close) : arg.point.data.Close;
              toolTipText = `날짜: ${arg.argument} | 지수: ${formatIncludeComma(Math.round(closeValue * 10) / 10)}`;
            }
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
    });
  }
</script>

<div bind:this={lineChart} class="h-[calc(100%)] w-[calc(100%)]"/>