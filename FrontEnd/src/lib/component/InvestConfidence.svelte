<script lang='ts'>
  import { createEventDispatcher, onMount, tick } from 'svelte';

  const dispatch = createEventDispatcher();

  let moneyList = [
    {name: '억', value: 100000000},
    {name: '천만', value: 10000000},
    {name: '백만', value: 1000000},
    {name: '십만', value: 100000},
    {name: '만', value: 10000},
  ]

  let durationModeList: Array<{name: string, value: {month: number, week: number}}> = [
    {name: '1 MONTH', value: {month: 1, week: 4}},
    {name: '3 MONTH', value: {month: 3, week: 13}},
    {name: '6 MONTH', value: {month: 6, week: 26}},
    {name: '1 YEAR', value: {month: 12, week: 52}},
    {name: '2 YEAR', value: {month: 24, week: 104}},
    {name: 'CHOICE WEEK', value: {month: 0, week: 1}},
    {name: 'CHOICE MONTH', value: {month: 1, week: 4}},
  ]

  let selectedDuration: any = durationModeList[0];
  let investMoney: number = 0;
  let inputElement: HTMLInputElement;

  onMount(async () => {
    await tick();

    onInputFocusEvent();
  })

  const onInputFocusEvent = () => {
    if (!!!inputElement) {
      return;
    }

		inputElement.select();
	}

  const setChoiceWeekMonthText = (
    durationModeInfo: {name: string, value: {month: number, week: number}}
  ): number => {
    if (durationModeInfo.name.includes('WEEK')){
      return durationModeInfo.value.week;
    } else {
      return durationModeInfo.value.month;
    }
  }

  const onCheckDownValue = (
    durationModeInfo: {name: string, value: {month: number, week: number}}
  ): boolean => {
    if (durationModeInfo.name.includes('WEEK')){
      return durationModeInfo.value.week > 1 ? true : false;
    } else {
      return durationModeInfo.value.month > 1 ? true : false;
    }
  }

  const onUpDownChoiceWeekMonthValue = (
    durationModeInfo: {name: string, value: {month: number, week: number}},
    isUp: boolean
  ): void => {
    if (durationModeInfo.name.includes('WEEK')){
      durationModeInfo.value.week += (isUp ? 1 : -1);
      durationModeInfo.value.month = parseFloat((durationModeInfo.value.week / 4).toFixed(1));
    } else {
      durationModeInfo.value.month += (isUp ? 1 : -1);
      durationModeInfo.value.week = (durationModeInfo.value.month * 4) + Math.floor(durationModeInfo.value.month / 3);
    }

    durationModeList = durationModeList;
  }

  const refreshChoiceWeekMonthValue = (
    durationModeInfo: {name: string, value: {month: number, week: number}}
  ): void => {
    if (durationModeInfo.name.includes('WEEK')){
      durationModeInfo.value.week = 1;
    } else {
      durationModeInfo.value.month = 1;
      durationModeInfo.value.week = (durationModeInfo.value.month * 4) + Math.floor(durationModeInfo.value.month / 3);
    }

    durationModeList = durationModeList;
  }
</script>

<div class="flex flex-col w-full h-auto border p-2 space-y-2 rounded bg-gray-800">
  <!-- 기간 설정 -->
  <div class="flex flex-row h-auto w-full space-x-1 text-white">
    <p class="flex w-[150px] items-center font-bold mr-2">{'📆 기간 설정'}</p>
    <div class="flex flex-col space-y-1">
      <div class="flex flex-row space-x-1">
        {#each durationModeList as durationModeInfo}
          <button class="flex flex-row border border-gray-400 rounded-md px-2 {selectedDuration.name === durationModeInfo.name ? 'bg-white text-black' : 'bg-gray-500 text-white'}"
            on:click={() => {
              selectedDuration = durationModeInfo;
            }}
          >
            {durationModeInfo.name}
            {#if durationModeInfo.name.includes('CHOICE')}
              <div class="flex flex-row ml-2 bg-black border">
                <div class="flex w-auto h-auto justify-center items-center text-white px-2">{setChoiceWeekMonthText(durationModeInfo)}</div>
                <button class="border-l w-[28px] bg-red-400" on:click={() => {
                  onUpDownChoiceWeekMonthValue(durationModeInfo, true);
                }}>△</button>
                <button class="border-x w-[28px] bg-blue-400" on:click={() => {
                  if (onCheckDownValue(durationModeInfo) === false) {
                    return;
                  }

                  onUpDownChoiceWeekMonthValue(durationModeInfo, false);
                }}>▽</button>
                <button class="w-[28px] bg-gray-400" on:click={() => {
                  refreshChoiceWeekMonthValue(durationModeInfo, false);
                }}>↻</button>
              </div>
            {/if}
          </button>
        {/each}
      </div>
    </div>
  </div>
  <!-- 투자금액 입력 -->
  <div class="flex flex-row h-auto w-full space-x-1 text-white">
    <p class="flex w-[150px] items-center font-bold mr-2">{'₩ 투자 금액'}</p>
    <input
      bind:this={inputElement}
      autocomplete="off"
      type="number"
      class="border w-[200px] px-1 rounded-md text-black"
      style="text-align: right"
      placeholder="투자 금액"
      bind:value={investMoney}
      on:focus={onInputFocusEvent}
    />
    <button class="border border-gray-400 rounded-md px-2 bg-white text-black"
      on:click={() => {
        investMoney = 0;
      }}
    >
      {'↺'}
    </button>
    <div class="flex flex-col space-y-1">
      <div class="space-x-1">
        {#each moneyList as moneyInfo}
          <button class="border border-gray-400 rounded-md px-2 bg-red-500"
            on:click={() => {
              investMoney += moneyInfo.value;
            }}
          >
            {moneyInfo.name}
          </button>
        {/each}
      </div>
      <div class="space-x-1">
        {#each moneyList as moneyInfo}
          <button class="border border-gray-400 rounded-md px-2 bg-blue-500"
            on:click={() => {
              investMoney -= moneyInfo.value;
            }}
          >
            {moneyInfo.name}
          </button>
        {/each}
      </div>
    </div>
    <button class="border border-gray-400 rounded-md px-2 bg-white text-black"
      on:click={() => {
        dispatch('onInvestCallback', {
          duration: selectedDuration.value,
          investMoney: investMoney
        })
      }}
    >
      {'💳 모의투자'}
    </button>
  </div>
</div>