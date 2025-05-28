<script lang="ts">
  import { onMount } from 'svelte';

  onMount(() => {
    // 리다이렉트 페이지에서 카카오 인증 코드 추출
    const url = new URL(window.location.href);
    const code = url.searchParams.get('code');

    window.opener.postMessage({ eventType: 'getKakaoAccessCode', detail: code });
    window.close();
  })
</script>

<div>카카오인증코드페이지</div>