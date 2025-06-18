<script lang="ts">
  export let newInfoList: any = [];

</script>

<div class="flex flex-col h-full overflow-auto w-full bg-transparent space-y-2 scrollbar-thin-custom">
  {#if newInfoList.length > 0}
    {#each newInfoList as newInfo}
      <div class="flex flex-col w-full bg-white/80 backdrop-blur-sm rounded-lg relative shadow-md hover:shadow-lg transition-all duration-200 border border-gray-200/50">
        <button class="font-semibold p-2.5 text-left transition-all duration-200 hover:bg-gray-50/50 rounded-lg {newInfo?.isOpen ? 'rounded-b-none border-b border-gray-200/50 bg-gradient-to-r from-blue-50 to-indigo-50' : 'truncate'}" on:click={() => {
          newInfo.isOpen = newInfo?.isOpen === undefined ? true : !newInfo?.isOpen;
        }}>
          <div class="flex items-start justify-between">
            <div class="flex items-start space-x-2 flex-1 min-w-0">
              <div class="flex-shrink-0 w-1.5 h-1.5 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full mt-1.5 shadow-sm"></div>
              <span class="text-gray-800 leading-snug text-sm {newInfo?.isOpen ? '' : 'line-clamp-2'}">{@html `${newInfo?.title?.replace(/<b\s*\/?>/gi, '')}`}</span>
            </div>
            <div class="flex-shrink-0 ml-2 flex items-center justify-center w-6 h-6 bg-white/80 backdrop-blur-sm border border-gray-200/50 rounded-md shadow-sm hover:shadow-md transition-all duration-200 hover:bg-gray-50">
              <svg class="w-3 h-3 text-gray-600 transition-transform duration-200 {newInfo?.isOpen ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </div>
          </div>
        </button>
        {#if newInfo?.isOpen}
          <div class="p-2.5 pt-0 w-full bg-gradient-to-br from-gray-50/50 to-slate-50/50 rounded-b-lg">
            <div class="prose prose-sm max-w-none text-gray-700 leading-relaxed mb-2 text-sm">
              {@html newInfo?.description}
            </div>
            <div class="flex justify-end">
              <a href="{newInfo?.link}" title="원문 보기" target="_blank" class="inline-flex items-center justify-center w-8 h-8 bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white rounded-lg shadow-md hover:shadow-lg transition-all duration-200 group">
                <svg class="w-4 h-4 transition-transform duration-200 group-hover:scale-110" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                </svg>
              </a>
            </div>
          </div>
        {/if}
      </div>
    {/each}
  {:else}
    <div class="flex flex-col w-full h-full justify-center items-center space-y-2">
      <div class="w-12 h-12 bg-gradient-to-r from-gray-200 to-gray-300 rounded-full flex items-center justify-center shadow-lg">
        <svg class="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path>
        </svg>
      </div>
      <p class="font-medium text-gray-500 text-center text-sm">해당 종목 관련 뉴스 정보가 없습니다.</p>
    </div>
  {/if}
</div>

<style>
  /* Firefox용 */
  .scrollbar-thin-custom {
    scrollbar-width: thin;           /* 얇은 스크롤바 */
    scrollbar-color: #94a3b8 #f1f5f9; /* 썸 색상, 트랙 색상 */
  }
  /* Webkit(크롬, 사파리 등)용 */
  .scrollbar-thin-custom::-webkit-scrollbar {
    width: 6px;                     /* 세로 스크롤바 두께 */
    background: #f1f5f9;           /* 트랙(배경) 색상 */
    border-radius: 4px;
  }
  .scrollbar-thin-custom::-webkit-scrollbar-thumb {
    background: linear-gradient(to bottom, #94a3b8, #64748b); /* 썸(움직이는 부분) 그라데이션 */
    border-radius: 4px;              /* 둥근 모서리 */
    border: 1px solid #e2e8f0;      /* 썸 테두리 */
  }
  .scrollbar-thin-custom::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(to bottom, #64748b, #475569); /* 썸 호버 시 색상 */
  }
  .scrollbar-thin-custom::-webkit-scrollbar-track {
    background: #f1f5f9;           /* 트랙 배경 */
    border-radius: 4px;
  }

  /* 텍스트 라인 클램프 유틸리티 */
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  /* 프로즈 스타일 개선 */
  .prose {
    color: #374151;
  }
  .prose p {
    margin-bottom: 0.5rem;
  }
  .prose strong {
    color: #1f2937;
    font-weight: 600;
  }
  .prose a {
    color: #3b82f6;
    text-decoration: none;
  }
  .prose a:hover {
    color: #1d4ed8;
    text-decoration: underline;
  }
</style>