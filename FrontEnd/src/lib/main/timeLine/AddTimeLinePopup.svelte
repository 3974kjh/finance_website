<script lang="ts">
  import { CommonPopup, ProgressCircle } from '$lib/component';
  import type { TradeInfoType } from '$lib/types';
  import { createComponent, getTodayDateDotFormatted } from '$lib/utils/CommonHelper';
  import { StockListPopup } from '$lib/popup';
  import { formatIncludeComma } from '$lib/utils/CommonHelper';
  import toast from 'svelte-french-toast'

  export let titleName: string = '';
  export let close: (value: any) => void;

  const initTradeInfo = (): TradeInfoType => {
    return {
      name: '',
      code: '',
      buyYn: 'Y',
      date: getTodayDateDotFormatted(true),
      todayAmount: 0,
      todayShares: 0,
      totalShares: 0,
      buyAmount: 0,
      buyReason: '',
    }
  }

  let tradeInfo: TradeInfoType = initTradeInfo();

  /**
	 * 팝업 창 종료
	 *
	 *  - 팝업 창 종료 시점에 resolve함수를 실행 시켜 fulfilled 상태로 전환
	 * 	- 이 때, true값을 resolve함수의 인자 값으로 보낸다.
	 *
	 */
	const closePopup = (requestData: any): void => {
		close(requestData);
	};

	/**
	 * dialog 닫기 버튼 클릭 시, 팝업 창 종료
	 */
	const closedDialogCallback = (): void => {
		closePopup(null);
	};

  const applyInfoToTimeLine = () => {
    if (!!!tradeInfo?.name || !!!tradeInfo?.code) {
      toast.error('등록버튼을 눌러 추가할 주식을 선택해주세요.');
      return;
    }
    
    if (tradeInfo?.todayShares < 1) {
      toast.error('주식 수 입력해주세요.');
      return;
    }

    closePopup(tradeInfo);
  }

  const getStockInfo = async () => {
    const popupResult = await createComponent(StockListPopup, {
      titleName: '주식 목록 조회',
      isSingleMode: true
    });

    if (popupResult.isSave === false) {
      return;
    }

    if (popupResult.choiceStockInfoList.length < 1) {
      return;
    }

    tradeInfo = initTradeInfo();

    tradeInfo.name = popupResult.choiceStockInfoList[0].name;
    tradeInfo.code = popupResult.choiceStockInfoList[0].code;
    tradeInfo.todayAmount = parseInt(popupResult.choiceStockInfoList[0].close);
  }
</script>

<CommonPopup {titleName} on:closedDialogCallback={closedDialogCallback}>
  <div class="flex flex-col w-[650px] h-[400px] bg-white p-3 space-y-3">
    <!-- 등록 -->
    <div class="flex w-full items-center justify-center h-[50px] border rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg flex-shrink-0">
      <button 
        class="text-lg font-bold w-full h-full hover:from-blue-600 hover:to-blue-700 transition-all duration-200 rounded-lg flex items-center justify-center space-x-2" 
        on:click={getStockInfo}
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H3m2 0h3M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
        </svg>
        <span>주식 종목 등록</span>
      </button>
    </div>

    <!-- 입력 필드들 -->
    <div class="flex flex-col space-y-3 flex-grow overflow-auto px-1">
      <!-- 날짜 -->
      <div class="flex flex-row items-center space-x-3 min-h-[32px]">
        <label class="w-[22%] font-semibold text-gray-700 text-sm">📅 거래일자</label>
        <div class="flex grow border border-gray-300 px-2 py-1.5 bg-gray-50 rounded-md text-sm">
          <span class="text-gray-600">{tradeInfo.date}</span>
        </div>
      </div>

      <!-- 회사이름 -->
      <div class="flex flex-row items-center space-x-3 min-h-[32px]">
        <label class="w-[22%] font-semibold text-gray-700 text-sm">🏢 회사명</label>
        <div class="grow">
          <input 
            bind:value={tradeInfo.name} 
            autocomplete="off" 
            placeholder="회사이름(자동입력)"
            disabled
            class="border border-gray-300 w-full px-2 py-1.5 rounded-md bg-gray-50 text-gray-600 focus:outline-none text-sm"
          />
        </div>
      </div>

      <!-- 주가코드 -->
      <div class="flex flex-row items-center space-x-3 min-h-[32px]">
        <label class="w-[22%] font-semibold text-gray-700 text-sm">🔢 종목코드</label>
        <div class="grow">
          <input 
            bind:value={tradeInfo.code} 
            autocomplete="off" 
            placeholder="주가코드(자동입력)"
            disabled
            class="border border-gray-300 w-full px-2 py-1.5 rounded-md bg-gray-50 text-gray-600 focus:outline-none text-sm"
          />
        </div>
      </div>

      <!-- 현재금액 입력 -->
      <div class="flex flex-row items-center space-x-3 min-h-[32px] relative">
        <label class="w-[22%] font-semibold text-gray-700 text-sm">💰 현재가격</label>
        <div class="flex grow items-center border border-gray-300 bg-white px-2 py-1.5 rounded-md focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent focus-within:relative focus-within:z-10">
          <input 
            bind:value={tradeInfo.todayAmount} 
            autocomplete="off"
            placeholder="현재금액 입력"
            class="grow px-1 focus:outline-none text-right text-sm"
            max={10000000000}
            min={0}
            on:keyup={() => {
              if (tradeInfo.todayAmount === null) {
                tradeInfo.buyAmount = 0;
              } else {
                tradeInfo.buyAmount = tradeInfo.todayShares * tradeInfo.todayAmount;
              }
            }}
          />
          <span class="text-gray-500 ml-2 font-medium text-sm">₩</span>
        </div>
      </div>

      <!-- 투자금액 입력 -->
      <div class="flex flex-row items-center space-x-3 min-h-[32px] relative">
        <label class="w-[22%] font-semibold text-gray-700 text-sm">
          {tradeInfo.buyYn === 'Y' ? '📈 매수금액' : '📉 매도금액'}
        </label>
        <div class="flex flex-row grow space-x-2 items-center">
          <button 
            class="border border-gray-300 w-8 h-8 rounded-md bg-gradient-to-r from-gray-50 to-gray-100 hover:from-gray-100 hover:to-gray-200 transition-all duration-200 flex items-center justify-center text-sm font-bold shadow-sm flex-shrink-0"
            on:click={() => {
              tradeInfo.buyYn = tradeInfo.buyYn === 'Y' ? 'N' : 'Y'; 
            }}
            title={tradeInfo.buyYn === 'Y' ? '매수 모드' : '매도 모드'}
          >
            {tradeInfo.buyYn === 'Y' ? '🟢' : '🔴'}
          </button>
          <div class="flex items-center border border-gray-300 bg-white px-2 py-1.5 rounded-md focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent focus-within:relative focus-within:z-10 flex-shrink-0 w-24">
            <input 
              bind:value={tradeInfo.todayShares} 
              autocomplete="off" 
              placeholder="주식 수"
              class="w-full px-1 focus:outline-none text-right text-sm"
              max={10000000000}
              min={0}
              on:keyup={() => {
                if (tradeInfo.todayShares === null) {
                  tradeInfo.buyAmount = 0;
                } else {
                  tradeInfo.buyAmount = tradeInfo.todayShares * tradeInfo.todayAmount;
                }
              }}
            />
          </div>
          <span class="text-gray-600 font-medium text-sm flex-shrink-0">주</span>
          <div class="flex grow justify-end border border-gray-300 px-2 py-1.5 bg-blue-50 rounded-md">
            <span class="font-semibold text-blue-700 text-sm">{formatIncludeComma(tradeInfo.buyAmount) ?? '-'} ₩</span>
          </div>
        </div>
      </div>

      <!-- 투자사유 입력 -->
      <div class="flex flex-row items-start space-x-3 flex-grow min-h-[60px] relative">
        <label class="flex w-[22%] items-start pt-2 font-semibold text-gray-700 text-sm flex-shrink-0">
          {tradeInfo.buyYn === 'Y' ? '📝 매수사유' : '📝 매도사유'}
        </label>
        <div class="grow min-h-0">
          <textarea
            bind:value={tradeInfo.buyReason} 
            autocomplete="off" 
            placeholder="거래 사유를 입력해주세요..."
            class="border border-gray-300 w-full h-full min-h-[60px] px-2 py-1.5 rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent focus:relative focus:z-10 text-sm"
          ></textarea>
        </div>
      </div>
    </div>
  </div>
  
  <div slot="subInfo" class="flex w-full justify-end items-center space-x-2">
    <button
      class="flex items-center justify-center border-2 rounded-md px-4 py-2 border-emerald-500 bg-emerald-500 text-white hover:bg-emerald-600 hover:border-emerald-600 transition-colors duration-200 font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
      disabled={!tradeInfo.name || !tradeInfo.code || tradeInfo.todayShares < 1}
      on:click={applyInfoToTimeLine}
    >
      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
      </svg>
      적용
    </button>
    <button
      class="flex items-center justify-center border-2 rounded-md px-4 py-2 border-red-400/50 bg-red-500/20 text-white hover:bg-red-500/40 hover:border-red-400/70 backdrop-blur-sm transition-colors duration-200 font-medium"
      on:click={closedDialogCallback}
    >
      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
      </svg>
      닫기
    </button>
  </div>
</CommonPopup>

<style>
  /* Chrome, Safari, Edge, Opera */
  input::-webkit-outer-spin-button,
  input::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
  }

  /* Firefox */
  input[type="number"] {
    -moz-appearance: textfield;
  }
</style>