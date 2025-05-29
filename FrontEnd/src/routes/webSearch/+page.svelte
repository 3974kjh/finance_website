<script lang='ts'>
  import { onMount, onDestroy } from 'svelte';

  const investingUrl = "https://comp.fnguide.com/SVO2/ASP/SVD_Report_Trend.asp";
  const krxUrl = 'https://ecos.bok.or.kr';
  const mkStockurl = 'https://stock.mk.co.kr';

  onMount(() => {
    if (!sessionStorage.getItem('hasReloaded')) {
      sessionStorage.setItem('hasReloaded', 'true');
      // 강력 새로고침
      window.location.reload();
    }
  });

  onDestroy(() => {
    if (typeof document !== 'undefined') {
      sessionStorage.removeItem('hasReloaded');
    };
  })
</script>

<div class="flex flex-row w-full h-full bg-gray-600 p-2 space-x-2">
  <div class="flex flex-col w-[50%] h-full space-y-2">
    <div class="flex w-full h-full border bg-white rounded-md p-2">
      <object data={investingUrl} type="text/html">
        브라우저가 object 태그를 지원하지 않거나 네이버 페이지를 로드할 수 없습니다.
      </object>
    </div>
    <div class="flex w-full h-full border bg-white rounded-md p-2">
      <object data={krxUrl} type="text/html">
        브라우저가 object 태그를 지원하지 않거나 네이버 페이지를 로드할 수 없습니다.
      </object>
    </div>
  </div>
  <div class="flex w-[50%] h-full border bg-white rounded-md p-2">
    <object data={mkStockurl} type="text/html">
        브라우저가 object 태그를 지원하지 않거나 네이버 페이지를 로드할 수 없습니다.
      </object>
  </div>
</div>

<style>
  object {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
</style>