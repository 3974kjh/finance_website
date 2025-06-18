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

  const setChoiceWeekMonthText = (durationModeInfo) => {
    if (durationModeInfo.name.includes('WEEK')){
      return durationModeInfo.value.week;
    } else {
      return durationModeInfo.value.month;
    }
  }

  const onCheckDownValue = (durationModeInfo) => {
    if (durationModeInfo.name.includes('WEEK')){
      return durationModeInfo.value.week > 1 ? true : false;
    } else {
      return durationModeInfo.value.month > 1 ? true : false;
    }
  }

  const onUpDownChoiceWeekMonthValue = (durationModeInfo, isUp) => {
    if (durationModeInfo.name.includes('WEEK')){
      durationModeInfo.value.week += (isUp ? 1 : -1);
      durationModeInfo.value.month = parseFloat((durationModeInfo.value.week / 4).toFixed(1));
    } else {
      durationModeInfo.value.month += (isUp ? 1 : -1);
      durationModeInfo.value.week = (durationModeInfo.value.month * 4) + Math.floor(durationModeInfo.value.month / 3);
    }

    durationModeList = durationModeList;
  }

  const refreshChoiceWeekMonthValue = (durationModeInfo) => {
    if (durationModeInfo.name.includes('WEEK')){
      durationModeInfo.value.week = 1;
    } else {
      durationModeInfo.value.month = 1;
      durationModeInfo.value.week = (durationModeInfo.value.month * 4) + Math.floor(durationModeInfo.value.month / 3);
    }

    durationModeList = durationModeList;
  }
</script>

<div class="flex flex-col w-full h-auto bg-slate-700/80 backdrop-blur-xl rounded-xl border border-slate-500/30 shadow-lg p-4 space-y-4">
  <!-- 기간 설정 -->
  <div class="flex flex-col lg:flex-row h-auto w-full space-y-3 lg:space-y-0 lg:space-x-4 text-white">
    <div class="flex items-center space-x-2 flex-shrink-0">
      <div class="w-6 h-6 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-lg">
        <span class="text-white text-sm">📆</span>
      </div>
      <p class="font-bold text-base text-white">기간 설정</p>
    </div>
    <div class="flex flex-col space-y-2 flex-1">
      <div class="flex flex-wrap gap-2">
        {#each durationModeList as durationModeInfo}
          <button class="flex flex-row items-center rounded-md px-2 py-1 text-xs font-medium transition-all duration-200 shadow-sm {selectedDuration.name === durationModeInfo.name ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-500/30' : 'bg-slate-600/80 text-slate-200 border border-slate-500/50 hover:bg-slate-500/80'}"
            on:click={() => {
              selectedDuration = durationModeInfo;
            }}
          >
            {durationModeInfo.name}
            {#if durationModeInfo.name.includes('CHOICE')}
              <div class="flex flex-row ml-2 bg-slate-800/90 rounded-md border border-slate-600/50 overflow-hidden">
                <div class="flex w-auto h-auto justify-center items-center text-white px-2 py-0.5 text-xs font-mono">{setChoiceWeekMonthText(durationModeInfo)}</div>
                <button class="w-5 h-5 bg-gradient-to-b from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white text-xs flex items-center justify-center transition-colors duration-200" on:click={() => {
                  onUpDownChoiceWeekMonthValue(durationModeInfo, true);
                }}>▲</button>
                <button class="w-5 h-5 bg-gradient-to-b from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white text-xs flex items-center justify-center transition-colors duration-200" on:click={() => {
                  if (onCheckDownValue(durationModeInfo) === false) {
                    return;
                  }

                  onUpDownChoiceWeekMonthValue(durationModeInfo, false);
                }}>▼</button>
                <button class="w-5 h-5 bg-gradient-to-b from-slate-500 to-slate-600 hover:from-slate-600 hover:to-slate-700 text-white text-xs flex items-center justify-center transition-colors duration-200" on:click={() => {
                  refreshChoiceWeekMonthValue(durationModeInfo);
                }}>↻</button>
              </div>
            {/if}
          </button>
        {/each}
      </div>
    </div>
  </div>
  
  <!-- 투자금액 입력 -->
  <div class="flex flex-col lg:flex-row h-auto w-full space-y-3 lg:space-y-0 lg:space-x-4 text-white">
    <div class="flex items-center space-x-2 flex-shrink-0">
      <div class="w-6 h-6 bg-gradient-to-r from-emerald-500 to-green-600 rounded-lg flex items-center justify-center shadow-lg">
        <span class="text-white text-sm">₩</span>
      </div>
      <p class="font-bold text-base text-white">투자 금액</p>
    </div>
    
    <div class="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3 flex-1 items-start">
      <!-- 입력 필드와 리셋 버튼 -->
      <div class="flex flex-row space-x-1 h-[4.25rem]">
        <input
          bind:this={inputElement}
          autocomplete="off"
          type="number"
          class="w-40 px-3 py-2 rounded-lg bg-white/95 backdrop-blur-sm border border-slate-200/50 text-slate-800 font-medium text-right placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 shadow-sm transition-all duration-200 text-sm h-full"
          placeholder="투자 금액 입력"
          bind:value={investMoney}
          on:focus={onInputFocusEvent}
        />
        <button class="w-10 h-full px-2 py-1 rounded-lg bg-gradient-to-r from-slate-500 to-slate-600 hover:from-slate-600 hover:to-slate-700 text-white font-medium shadow-sm transition-all duration-200 flex items-center justify-center"
          title="초기화"
          on:click={() => {
            investMoney = 0;
          }}
        >
          <span class="text-lg">↺</span>
        </button>
      </div>
      
      <!-- 금액 버튼들 -->
      <div class="flex flex-col space-y-1.5">
        <div class="flex flex-wrap gap-1">
          {#each moneyList as moneyInfo}
            <button class="w-12 h-8 rounded-md bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 text-white font-medium shadow-sm transition-all duration-200 hover:scale-105 flex items-center justify-center group relative"
              title="+{moneyInfo.name} ({moneyInfo.value.toLocaleString()}원)"
              on:click={() => {
                investMoney += moneyInfo.value;
              }}
            >
              <span class="text-xs font-bold">{moneyInfo.name}</span>
              <span class="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full flex items-center justify-center text-xs font-bold text-white">+</span>
            </button>
          {/each}
        </div>
        <div class="flex flex-wrap gap-1">
          {#each moneyList as moneyInfo}
            <button class="w-12 h-8 rounded-md bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-medium shadow-sm transition-all duration-200 hover:scale-105 flex items-center justify-center group relative"
              title="-{moneyInfo.name} ({moneyInfo.value.toLocaleString()}원)"
              on:click={() => {
                investMoney -= moneyInfo.value;
              }}
            >
              <span class="text-xs font-bold">{moneyInfo.name}</span>
              <span class="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full flex items-center justify-center text-xs font-bold text-white">-</span>
            </button>
          {/each}
        </div>
      </div>
      
      <!-- 모의투자 버튼 -->
      <button class="px-4 h-full rounded-lg bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold shadow-lg shadow-green-500/30 transition-all duration-200 hover:scale-105 flex flex-row items-center justify-center space-x-1"
        on:click={() => {
          dispatch('onInvestCallback', {
            duration: selectedDuration.value,
            investMoney: investMoney
          })
        }}
      >
        <span class="text-xl">💳</span>
        <span class="text-sm font-bold">모의투자</span>
        <span class="text-xs">시작</span>
      </button>
    </div>
  </div>
</div>