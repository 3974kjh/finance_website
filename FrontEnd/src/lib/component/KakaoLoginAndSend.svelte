<script lang="ts">
  import { onMount, onDestroy, tick, createEventDispatcher } from 'svelte';
  import { KaKaoLoginImg, KaKaoSendImg } from '$lib/images/kakao';
  import { KAKAO_REST_API_KEY, REDIRECT_URI } from "$lib/api-connector/AppKeys";
  import axios from 'axios';

  export let kakaoAccessCode: string;
  export let isTextDark: boolean = true;

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

<div class="flex grow justify-end space-x-1 items-center">
  <p class="flex h-auto justify-center font-bold mr-1" style="color: {isTextDark ? 'black' : 'white'}">{'・ 카카오 Access Code :'}</p>
  <input
    type="text"
    autocomplete="off"
    id="access-code"
    name="access-code"
    disabled
    class="border w-[200px] px-1 rounded-md"
    placeholder="카카오 access code 입력"
    bind:value={kakaoAccessCode}
  />
  <button
    class="border-white rounded-md px-2 bg-gray-600 text-white"
    style="
      background-image: url({KaKaoLoginImg});
      background-size: cover;
      background-position: center;
      width: 150px;   /* 버튼 크기 지정 */
      height: 28px;
    "
    on:click={getKakaoAccessCode}
  />
  <button
    class="border-white rounded-md px-2 bg-gray-600 text-white" disabled={!!!kakaoAccessCode}
    style="
      background-image: url({KaKaoSendImg});
      background-size: cover;
      background-position: center;
      width: 28px;   /* 버튼 크기 지정 */
      height: 28px;
    "
    on:click={() => {
      dispatch('onSendFinanceResultByKakaoApiCallback');
    }}
  />
</div>