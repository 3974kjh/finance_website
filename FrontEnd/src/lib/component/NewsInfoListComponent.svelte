<script lang="ts">
  export let newInfoList: any = [];

</script>

<div class="flex flex-col h-full overflow-auto w-full border rounded-md bg-gray-50 p-2 space-y-2 scrollbar-thin-custom">
  {#if newInfoList.length > 0}
    {#each newInfoList as newInfo}
      <div class="flex flex-col w-full bg-gray-200 rounded-md relative">
        <p class="font-bold p-2 {newInfo?.isOpen ? 'rounded-md border-2 border-gray-600' : 'truncate'}">{@html `🔍 ${newInfo?.title?.replace(/<b\s*\/?>/gi, '')}`}</p>
        <div class="flex absolute" style="top: 5px; right: 5px">
          <button class="bg-white px-1 border rounded-md" style="opacity: 0.7" on:click={() => {
            newInfo.isOpen = newInfo?.isOpen === undefined ? true : !newInfo?.isOpen;
          }}>{newInfo?.isOpen ? '▲' : '▼'}</button>
        </div>
        {#if newInfo?.isOpen}
          <div class="p-3 w-full">
            {@html newInfo?.description}
            <a href="{newInfo?.link}" title="{newInfo?.link}" target="_blank">{@html '<br/>[go to link]'}</a>
          </div>
        {/if}
      </div>
    {/each}
  {:else}
    <div class="flex w-full h-full justify-center items-center font-bold text-gray-400">
      {'해당 종목 관련 뉴스 정보가 없습니다.'}
    </div>
  {/if}
</div>

<style>
  /* Firefox용 */
  .scrollbar-thin-custom {
    scrollbar-width: thin;           /* 얇은 스크롤바 */
    scrollbar-color: #000000 transparent; /* 썸 색상, 트랙은 투명 */
  }
  /* Webkit(크롬, 사파리 등)용 */
  .scrollbar-thin-custom::-webkit-scrollbar {
    height: 6px;                     /* 가로 스크롤바 두께 */
    background: transparent;         /* 트랙(배경) 투명 */
  }
  .scrollbar-thin-custom::-webkit-scrollbar-thumb {
    background: #000000;                /* 썸(움직이는 부분) 색상 */
    border-radius: 4px;              /* 둥근 모서리 */
  }
  .scrollbar-thin-custom::-webkit-scrollbar-thumb:hover {
    background: #555;                /* 썸 호버 시 색상 */
  }
</style>