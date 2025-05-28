<script lang="ts">
  import { CommonPopup, ProgressCircle } from '$lib/component';
  import type { TradeInfoType } from '$lib/types';
  import { createComponent, getTodayDateDotFormatted } from '$lib/utils/CommonHelper';
  import { StockListPopup } from '$lib/popup';
  import { formatIncludeComma } from '$lib/utils/CommonHelper';
  import toast from 'svelte-french-toast'
  import _ from 'lodash';

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
  <div class="flex flex-col w-[600px] h-[350px] bg-white p-2 space-y-2">
    <!-- 등록 -->
    <div class="flex w-full items-center justify-center h-[70px] border rounded-md bg-gray-500 text-white">
      <button class="text-3xl w-full h-full hover:bg-gray-800" on:click={getStockInfo}>{'㈜ 🏢 등록'}</button>
    </div>
    <!-- 날짜 -->
    <div class="flex flex-row h-auto w-full items-center space-x-2">
      <p class="w-[20%]">날짜 :</p>
      <p class="flex grow border px-1 bg-gray-50">
        {tradeInfo.date}
      </p>
    </div>
    <!-- 회사이름 -->
    <div class="flex flex-row h-auto w-full items-center space-x-2">
      <p class="w-[20%]">회사이름 :</p>
      <div class="grow">
        <input 
          bind:value={tradeInfo.name} 
          autocomplete="off" 
          placeholder="회사이름(자동입력)"
          disabled
          type="text"
          class="border w-full px-2"
        />
      </div>
    </div>
    <!-- 주가코드 -->
    <div class="flex flex-row h-auto w-full items-center space-x-2">
      <p class="w-[20%]">주가코드 :</p>
      <div class="grow">
        <input 
          bind:value={tradeInfo.code} 
          autocomplete="off" 
          placeholder="주가코드(자동입력)"
          disabled
          type="text"
          class="border w-full px-2"
        />
      </div>
    </div>
    <!-- 현재금액 입력 -->
    <div class="flex flex-row h-auto w-full items-center space-x-2">
      <p class="w-[20%]">현재금액 :</p>
      <div class="flex grow justify-end border bg-white px-1">
        <input 
          bind:value={tradeInfo.todayAmount} 
          autocomplete="off"
          placeholder="현재금액 입력"
          type="number"
          class="grow px-1"
          style="text-align: right"
          max={10000000000}
          min={0}
          on:keyup={(e) => {
            if (tradeInfo.todayAmount === null) {
              tradeInfo.buyAmount = 0;
            } else {
              tradeInfo.buyAmount = tradeInfo.todayShares * tradeInfo.todayAmount;
            }
          }}
        />
        <p>{'₩'}</p>
      </div>
    </div>
    <!-- 투자금액 입력 -->
    <div class="flex flex-row h-auto w-full items-center space-x-2">
      <p class="w-[20%]">{`${tradeInfo.buyYn === 'Y' ? '투자' : '판매'}금액 :`}</p>
      <div class="flex flex-row grow space-x-2">
        <button class="border w-[26px] rounded-md bg-gray-50 hover:bg-gray-200"
          on:click={() => {
            tradeInfo.buyYn = tradeInfo.buyYn === 'Y' ? 'N' : 'Y'; 
          }}
        >
          {tradeInfo.buyYn === 'Y' ? '➕' : '➖'}
        </button>
        <input 
          bind:value={tradeInfo.todayShares} 
          autocomplete="off" 
          placeholder="주식 수"
          type="number"
          class="border w-[20%] px-2"
          style="text-align: right"
          max={10000000000}
          min={0}
          on:keyup={(e) => {
            if (tradeInfo.todayShares === null) {
              tradeInfo.buyAmount = 0;
            } else {
              tradeInfo.buyAmount = tradeInfo.todayShares * tradeInfo.todayAmount;
            }
          }}
        />
        <span>주</span>
        <p class="flex grow justify-end border px-1 bg-gray-50">
          {`${formatIncludeComma(tradeInfo.buyAmount) ?? '-'} ₩`}
        </p>
      </div>
    </div>
    <!-- 투자사유 입력 -->
    <div class="flex flex-row h-auto w-full items-center space-x-2">
      <p class="flex w-[20%] h-full items-start">{`${tradeInfo.buyYn === 'Y' ? '투자' : '판매'}사유 :`}</p>
      <div class="grow">
        <textarea
          bind:value={tradeInfo.buyReason} 
          autocomplete="off" 
          placeholder="사유 입력"
          type="textarea"
          class="border w-full h-[100px] px-2"
        />
      </div>
    </div>
  </div>
  <div slot="subInfo" class="flex w-full justify-end items-end space-x-1">
    <button
      class="flex items-center justify-center border-2 rounded-md px-1 border-gray-400 bg-white"
      on:click={applyInfoToTimeLine}>적용</button
    >
    <button
      class="flex items-center justify-center border-2 rounded-md px-1 border-gray-400 bg-white"
      on:click={closedDialogCallback}>닫기</button
    >
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