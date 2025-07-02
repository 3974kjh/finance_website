<script lang="ts">
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';
  import { KaKaoLoginImg, KaKaoSendImg } from '$lib/images/kakao';
  import { EnvConfig } from "$lib/utils/EnvConfig";

  export let kakaoAccessCode: string;
  export let isTextDark: boolean = true;

  const KAKAO_REST_API_KEY = EnvConfig.kakao.apiKey;
  const REDIRECT_URI = EnvConfig.kakao.redirectUri;

  const dispatch = createEventDispatcher();

  onMount(() => {
    if (typeof window !== 'undefined') {
      window.addEventListener('message', eventsFromNewWindow);
    }
  })

  onDestroy(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('message', eventsFromNewWindow);
    }
  })

  const eventsFromNewWindow = (event: MessageEvent) => {
    if (!!!event?.data?.eventType) {
      return;
    }

    switch (event.data.eventType) {
      case 'getKakaoAccessCode':
        dispatch('onUpdateKakaoAccessCodeCallback', event.data?.detail ?? '');
        break;
    }
  }

  const getKakaoAccessCode = async () => {
    window.open(`https://kauth.kakao.com/oauth/authorize?client_id=${KAKAO_REST_API_KEY}&redirect_uri=${REDIRECT_URI}&response_type=code`, '_blank');
  }
</script>

<div class="kakao-container">
  <div class="label-container space-x-1">
    <svg class="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"></path>
    </svg>
    <p class="label-text" class:dark={isTextDark} class:light={!isTextDark}>카카오 Access Code</p>
  </div>
  
  <div class="input-container">
    <input
      type="text"
      autocomplete="off"
      id="access-code"
      name="access-code"
      disabled
      class="access-input"
      placeholder="카카오 access code 입력"
      bind:value={kakaoAccessCode}
    />
  </div>
  
  <div class="button-container">
    <button
      class="kakao-login-btn"
      style="background-image: url({KaKaoLoginImg});"
      on:click={getKakaoAccessCode}
    >
    </button>
    
    <button
      class="kakao-send-btn"
      class:disabled={!!!kakaoAccessCode}
      disabled={!!!kakaoAccessCode}
      style="background-image: url({KaKaoSendImg});"
      on:click={() => {
        dispatch('onSendFinanceResultByKakaoApiCallback');
      }}
    >
    </button>
  </div>
</div>

<style>
  .kakao-container {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.25rem 0.5rem;
    height: 40px; /* 종목검색 input과 동일한 높이 */
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 
      0 2px 8px rgba(0, 0, 0, 0.1),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
  }

  .kakao-container:hover {
    background: rgba(255, 255, 255, 0.15);
    border-color: rgba(255, 255, 255, 0.3);
    box-shadow: 
      0 4px 12px rgba(0, 0, 0, 0.15),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }

  .label-container {
    display: flex;
    align-items: center;
    gap: 0.2rem;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .label-icon {
    width: 0.75rem;
    height: 0.75rem;
    opacity: 0.8;
  }

  .label-text {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.025em;
    margin: 0;
  }

  .label-text.dark {
    color: #1e293b;
    text-shadow: 0 1px 2px rgba(30, 41, 59, 0.2);
  }

  .label-text.light {
    color: #f8fafc;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  }

  .input-container {
    flex: 1;
    min-width: 140px;
  }

  .access-input {
    width: 100%;
    height: 32px; /* 컨테이너 높이에 맞춘 input 높이 */
    padding: 0 0.5rem;
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(203, 213, 225, 0.5);
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 500;
    color: #334155;
    outline: none;
    transition: all 0.3s ease;
    box-shadow: 
      0 1px 4px rgba(0, 0, 0, 0.05),
      inset 0 1px 0 rgba(255, 255, 255, 0.8);
  }

  .access-input:focus {
    background: rgba(255, 255, 255, 0.95);
    border-color: rgba(59, 130, 246, 0.5);
    box-shadow: 
      0 0 0 2px rgba(59, 130, 246, 0.1),
      0 2px 8px rgba(0, 0, 0, 0.1),
      inset 0 1px 0 rgba(255, 255, 255, 0.9);
  }

  .access-input::placeholder {
    color: #94a3b8;
    font-weight: 400;
    font-size: 0.65rem;
  }

  .button-container {
    display: flex;
    gap: 0.2rem;
    flex-shrink: 0;
  }

  .kakao-login-btn,
  .kakao-send-btn {
    border: none;
    border-radius: 5px;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  }

  .kakao-login-btn {
    width: 120px;
    height: 32px;
  }

  .kakao-send-btn {
    width: 32px;
    height: 32px;
  }

  .kakao-login-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }

  .kakao-send-btn:hover:not(.disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }

  .kakao-login-btn:active {
    transform: translateY(0);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  }

  .kakao-send-btn:active:not(.disabled) {
    transform: translateY(0);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  }

  .kakao-send-btn.disabled {
    cursor: not-allowed;
    opacity: 0.5;
    filter: grayscale(50%);
  }

  /* 반응형 디자인 */
  @media (max-width: 768px) {
    .kakao-container {
      gap: 0.25rem;
      padding: 0.2rem 0.4rem;
      height: 36px;
    }

    .label-container {
      gap: 0.15rem;
    }

    .input-container {
      min-width: 120px;
    }

    .access-input {
      height: 28px;
      padding: 0 0.4rem;
      font-size: 0.65rem;
    }

    .kakao-login-btn {
      width: 100px;
      height: 28px;
    }

    .kakao-send-btn {
      width: 28px;
      height: 28px;
    }

    .label-icon {
      width: 0.7rem;
      height: 0.7rem;
    }

    .label-text {
      font-size: 0.65rem;
    }
  }
</style>