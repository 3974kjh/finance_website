<script lang="ts">
  import Chart from 'devextreme/viz/chart';
  import { onMount, tick } from 'svelte'; 
  import { formatIncludeComma } from '$lib/utils/CommonHelper';
  import _ from 'lodash';

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

  /**
   * line Chart 영역
   */
  let lineChart: HTMLDivElement;

  onMount(async () => {
    startDate = lineDataList[0]?.Date;

    const lastData = getLastData(lineDataList);
    lastDate = lastData.date;
    upDownGradient = getUpDownGradient(lineDataList[0]?.Close, lastData?.value);

    await tick();

    createMonthLineChart();
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
        { valueField: 'Close', name: '종가', hoverMode: 'none', color: setMainLineColor(upDownGradient) }
      ];
    }

    if (!isDetailMode) {
      return [
        { valueField: 'Close', name: '종가', hoverMode: 'none', color: '#000000' },
        { valueField: 'topValue', name: '저항평균선', hoverMode: 'none', color: '#FF0000', dashStyle: 'dash' },
        { valueField: 'bottomValue', name: '지지평균선', hoverMode: 'none', color: '#0000FF', dashStyle: 'dash' }
      ];
    } else {
      return [
        { valueField: 'Close', name: '종가', hoverMode: 'none', color: '#000000', width: 3 },
        { valueField: 'topValue', name: '저항평균선', hoverMode: 'none', color: '#FF0000', dashStyle: 'dash' },
        { valueField: 'bottomValue', name: '지지평균선', hoverMode: 'none', color: '#0000FF', dashStyle: 'dash' },
        { valueField: 'ma5', name: '5일이평선', hoverMode: 'none', color: '#1E90FF', width: 3 },
        { valueField: 'ma20', name: '20일이평선', hoverMode: 'none', color: '#FFA500', width: 3 },
        { valueField: 'ma60', name: '60일이평선', hoverMode: 'none', color: '#32CD32', width: 3 }
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
          visible: false
        }
      },
      zoomAndPan: {
        argumentAxis: 'both'
      },
      scrollBar: {
        visible: true,
      },
      customizeLabel: (e: any) => {
        const setBackGroundColor = (seriesName: string) => {
          let color: string = '#000000';

          if (seriesName === '종가') {
            color = '#000000';
          } else if (seriesName === '저항평균선') {
            color = '#FF0000';
          } else if (seriesName === '지지평균선') {
            color = '#0000FF';
          } else if (seriesName === '5일이평선') {
            color = '#1E90FF';
          } else if (seriesName === '20일이평선') {
            color = '#FFA500';
          } else if (seriesName === '60일이평선') {
            color = '#32CD32';
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
          backgroundColor: setBackGroundColor(e?.seriesName),
          verticalOffset: setOffsetPadding(e?.seriesName),
          customizeText() {
            let title: string = e?.seriesName ?? '미정';
            let value: number = 0;

            if (isMultiLine) {
              if (e.seriesName === '종가') {
                value = typeof e.data.Close === 'string' ? Math.round(parseInt(e.data.Close) * 100) / 100 : Math.round(e.data.Close * 100) / 100;
              } else if (e.seriesName === '저항평균선') {
                value = typeof e.data.topValue === 'string' ? Math.round(parseFloat(e.data.topValue) * 100) / 100 : Math.round(e.data.topValue * 100) / 100;
              } else if (e.seriesName === '지지평균선') {
                value = typeof e.data.bottomValue === 'string' ? Math.round(parseFloat(e.data.bottomValue) * 100) / 100 : Math.round(e.data.bottomValue * 100) / 100;
              } else if (e.seriesName === '5일이평선') {
                value = typeof e.data?.ma5 === 'string' ? Math.round(parseFloat(e.data?.ma5) * 100) / 100 : Math.round(e.data?.ma5 * 100) / 100;
              } else if (e.seriesName === '20일이평선') {
                value = typeof e.data?.ma20 === 'string' ? Math.round(parseFloat(e.data?.ma20) * 100) / 100 : Math.round(e.data?.ma20 * 100) / 100;
              } else if (e.seriesName === '60일이평선') {
                value = typeof e.data?.ma60 === 'string' ? Math.round(parseFloat(e.data?.ma60) * 100) / 100 : Math.round(e.data?.ma60 * 100) / 100;
              }
            } else {
              value = typeof e.data.Close === 'string' ? Math.round(parseInt(e.data.Close) * 100) / 100 : Math.round(e.data.Close * 100) / 100;
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
				customizeTooltip: function (arg: { value: number, argument: string }) {
          const value: number = typeof arg.value === 'string' ? Math.round(parseInt(arg?.value) * 100) / 100 : Math.round(arg?.value * 100) / 100;

					return {
						text: `날짜: ${arg.argument} | 지수: ${formatIncludeComma(value)}`
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