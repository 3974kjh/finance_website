<script lang='ts'>
	import type { SplitLayoutSizeType } from '$lib/types';
  import { onMount, onDestroy } from 'svelte';
  import { Pane, Splitpanes } from 'svelte-splitpanes';

  const investingUrl = "https://comp.fnguide.com/SVO2/ASP/SVD_Report_Trend.asp";
  const krxUrl = 'https://ecos.bok.or.kr';
  const mkStockurl = 'https://stock.mk.co.kr';

  /**
   * 컬럼 레이아웃 사이즈 초기화
   */
  const initialColSplitLayoutSize = () => {
    return [
      {
        size: 50,
        min: 10,
        max: 100
      },
      {
        size: 50,
        min: 10,
        max: 100
      }
    ]
  }

  /**
   * 행 레이아웃 사이즈 초기화
   */
  const initialRowSplitLayoutSize = () => {
    return [
      {
        size: 50,
        min: 10,
        max: 100
      },
      {
        size: 50,
        min: 10,
        max: 100
      }
    ]
  }

  /**
   * 컬럼 레이아웃 사이즈
   */
  let splitColLayoutSize: SplitLayoutSizeType[] = initialColSplitLayoutSize();

  /** 
   * 행 레이아웃 사이즈
   */
  let splitRowLayoutSize: SplitLayoutSizeType[] = initialRowSplitLayoutSize();

  /**
   * URL을 새창으로 열기
   */
  const openUrlInNewWindow = (url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  onMount(() => {
    if (!sessionStorage.getItem('hasReloaded')) {
      sessionStorage.setItem('hasReloaded', 'true');
      // 강력 새로고침
      window.location.reload();
    }

    // 행 레이아웃 사이즈 초기화
    const localStorageSplitRowLayoutSize = localStorage.getItem('webSearchSplitRowLayoutSize');
    splitRowLayoutSize = !!localStorageSplitRowLayoutSize ? JSON.parse(localStorageSplitRowLayoutSize) : initialRowSplitLayoutSize();

    // 컬럼 레이아웃 사이즈 초기화
    const localStorageSplitColLayoutSize = localStorage.getItem('webSearchSplitColLayoutSize');
    splitColLayoutSize = !!localStorageSplitColLayoutSize ? JSON.parse(localStorageSplitColLayoutSize) : initialColSplitLayoutSize();
  });

  onDestroy(() => {
    if (typeof document !== 'undefined') {
      sessionStorage.removeItem('hasReloaded');
    };
  })

  /**
   * 행 레이아웃 사이즈 변경 이벤트 처리
   * @param event
   */
  const onLayoutRowResized = (event: CustomEvent) => {
    if (!!!event || !!!event.detail || event.detail?.length < 1) {
      return;
    }

    splitRowLayoutSize = event.detail as SplitLayoutSizeType[];

    // 행 레이아웃 사이즈 저장
    localStorage.setItem('webSearchSplitRowLayoutSize', JSON.stringify(splitRowLayoutSize));
  };

  /**
   * 컬럼 레이아웃 사이즈 변경 이벤트 처리
   * @param event
   */
  const onLayoutColResized = (event: CustomEvent) => {
    if (!!!event || !!!event.detail || event.detail?.length < 1) {
      return;
    }

    splitColLayoutSize = event.detail as SplitLayoutSizeType[];

    // 컬럼 레이아웃 사이즈 저장
    localStorage.setItem('webSearchSplitColLayoutSize', JSON.stringify(splitColLayoutSize));
  };
</script>

<svelte:head>
	<title>투자 리서치 - FinanceChart</title>
</svelte:head>
<!-- 메인 컨텐츠 -->
<div class="flex flex-row w-full h-[calc(100%)] p-2 space-x-2">
  <Splitpanes on:resized={onLayoutRowResized}>
    <!-- 좌측 패널 -->
    <Pane size={splitRowLayoutSize[0].size} minSize={splitRowLayoutSize[0].min} maxSize={splitRowLayoutSize[0].max}>
      <div class="flex flex-col h-full space-y-2">
        <Splitpanes horizontal="{true}" on:resized={onLayoutColResized}>
          <!-- FnGuide 섹션 -->
          <Pane size={splitColLayoutSize[0].size} minSize={splitColLayoutSize[0].min} maxSize={splitColLayoutSize[0].max}>
            <div class="flex flex-col h-full bg-white/95 backdrop-blur-xl rounded-2xl border border-blue-200/50 shadow-2xl shadow-blue-500/20 overflow-hidden">
              <button class="flex items-center justify-between p-4 border-b border-blue-200/40 bg-gradient-to-r from-blue-50 to-indigo-100 cursor-pointer hover:from-blue-100 hover:to-indigo-200 transition-colors" 
                  on:click={() => openUrlInNewWindow(investingUrl)}>
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/30">
                    <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                  </div>
                  <h2 class="text-lg font-bold text-slate-800">FnGuide 분석</h2>
                </div>
                <div class="flex items-center space-x-2">
                  <div class="text-xs text-blue-700 bg-blue-100 px-2 py-1 rounded-lg font-medium">실시간</div>
                  <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                  </svg>
                </div>
              </button>
              <div class="flex-1 p-4 bg-gray-50/80">
                <!-- svelte-ignore a11y-missing-attribute -->
                <object data={investingUrl} type="text/html" class="research-frame">
                  <div class="flex items-center justify-center h-full bg-white/90 rounded-xl border-2 border-dashed border-blue-300/50 shadow-inner">
                    <div class="text-center">
                      <svg class="w-12 h-12 text-blue-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                      </svg>
                      <p class="text-slate-700 font-medium">페이지를 로드하는 중...</p>
                      <p class="text-sm text-slate-500 mt-1">브라우저가 지원하지 않거나 페이지를 로드할 수 없습니다.</p>
                    </div>
                  </div>
                </object>
              </div>
            </div>
          </Pane>
          <!-- 한국은행 ECOS 섹션 -->
          <Pane size={splitColLayoutSize[1].size} minSize={splitColLayoutSize[1].min} maxSize={splitColLayoutSize[1].max}>
            <div class="flex flex-col h-full bg-white/95 backdrop-blur-xl rounded-2xl border border-emerald-200/50 shadow-2xl shadow-emerald-500/20 overflow-hidden">
              <button class="flex items-center justify-between p-4 border-b border-emerald-200/40 bg-gradient-to-r from-emerald-50 to-teal-100 cursor-pointer hover:from-emerald-100 hover:to-teal-200 transition-colors"
                  on:click={() => openUrlInNewWindow(krxUrl)}>
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center shadow-lg shadow-emerald-500/30">
                    <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                    </svg>
                  </div>
                  <h2 class="text-lg font-bold text-slate-800">한국은행 ECOS</h2>
                </div>
                <div class="flex items-center space-x-2">
                  <div class="text-xs text-emerald-700 bg-emerald-100 px-2 py-1 rounded-lg font-medium">경제통계</div>
                  <svg class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                  </svg>
                </div>
              </button>
              <div class="flex-1 p-4 bg-gray-50/80">
                <!-- svelte-ignore a11y-missing-attribute -->
                <object data={krxUrl} type="text/html" class="research-frame">
                  <div class="flex items-center justify-center h-full bg-white/90 rounded-xl border-2 border-dashed border-emerald-300/50 shadow-inner">
                    <div class="text-center">
                      <svg class="w-12 h-12 text-emerald-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                      </svg>
                      <p class="text-slate-700 font-medium">페이지를 로드하는 중...</p>
                      <p class="text-sm text-slate-500 mt-1">브라우저가 지원하지 않거나 페이지를 로드할 수 없습니다.</p>
                    </div>
                  </div>
                </object>
              </div>
            </div>
          </Pane>
        </Splitpanes>
      </div>
    </Pane>
    <!-- 우측 패널 -->
    <Pane size={splitRowLayoutSize[1].size} minSize={splitRowLayoutSize[1].min} maxSize={splitRowLayoutSize[1].max}>
      <div class="flex flex-col h-full bg-white/95 backdrop-blur-xl rounded-2xl border border-purple-200/50 shadow-2xl shadow-purple-500/20 overflow-hidden">
        <button class="flex items-center justify-between p-4 border-b border-purple-200/40 bg-gradient-to-r from-purple-50 to-pink-100 cursor-pointer hover:from-purple-100 hover:to-pink-200 transition-colors"
            on:click={() => openUrlInNewWindow(mkStockurl)}>
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg flex items-center justify-center shadow-lg shadow-purple-500/30">
              <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path>
              </svg>
            </div>
            <h2 class="text-lg font-bold text-slate-800">매일경제 증권</h2>
          </div>
          <div class="flex items-center space-x-2">
            <div class="text-xs text-purple-700 bg-purple-100 px-2 py-1 rounded-lg font-medium">증권정보</div>
            <svg class="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
            </svg>
          </div>
        </button>
        <div class="flex-1 p-4 bg-gray-50/80">
          <!-- svelte-ignore a11y-missing-attribute -->
          <object data={mkStockurl} type="text/html" class="research-frame">
            <div class="flex items-center justify-center h-full bg-white/90 rounded-xl border-2 border-dashed border-purple-300/50 shadow-inner">
              <div class="text-center">
                <svg class="w-12 h-12 text-purple-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <p class="text-slate-700 font-medium">페이지를 로드하는 중...</p>
                <p class="text-sm text-slate-500 mt-1">브라우저가 지원하지 않거나 페이지를 로드할 수 없습니다.</p>
              </div>
            </div>
          </object>
        </div>
      </div>
    </Pane>
  </Splitpanes>
</div>

<style>
  .research-frame {
    width: 100%;
    height: 100%;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(148, 163, 184, 0.3);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }

  /* Splitpanes 투명 배경 스타일 */
  :global(.splitpanes) {
    background: transparent !important;
  }

  :global(.splitpanes__pane) {
    background: transparent !important;
  }

  :global(.splitpanes__splitter) {
    background: transparent !important;
    border: none !important;
    position: relative;
    cursor: col-resize;
  }

  :global(.splitpanes--horizontal .splitpanes__splitter) {
    cursor: row-resize;
  }

  /* 스플릿 바 ::before, ::after 가상 요소 아이콘 스타일 */
  :global(.splitpanes__splitter::before),
  :global(.splitpanes__splitter::after) {
    background-color: white !important;
    border-color: white !important;
    color: white !important;
    fill: white !important;
    stroke: white !important;
  }

  /* 호버 시 아이콘 강조 */
  :global(.splitpanes__splitter:hover *) {
    color: white !important;
    fill: white !important;
    stroke: white !important;
  }

  /* 호버 시 ::before, ::after 가상 요소 강조 */
  :global(.splitpanes__splitter:hover::before),
  :global(.splitpanes__splitter:hover::after) {
    background-color: rgba(255, 255, 255, 0.9) !important;
  }

  /* 글래스모피즘 효과 강화 */
  :global(.backdrop-blur-xl) {
    backdrop-filter: blur(24px) saturate(180%);
    -webkit-backdrop-filter: blur(24px) saturate(180%);
  }

  /* 애니메이션 */
  :global(.animate-pulse) {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }

  /* 스크롤바 스타일링 - 밝은 테마 */
  :global(::-webkit-scrollbar) {
    width: 8px;
  }

  :global(::-webkit-scrollbar-track) {
    background: rgba(241, 245, 249, 0.8);
    border-radius: 10px;
  }

  :global(::-webkit-scrollbar-thumb) {
    background: linear-gradient(45deg, rgba(148, 163, 184, 0.6), rgba(203, 213, 225, 0.8));
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  :global(::-webkit-scrollbar-thumb:hover) {
    background: linear-gradient(45deg, rgba(100, 116, 139, 0.8), rgba(148, 163, 184, 0.9));
  }

  /* 추가 시각적 효과 */
  .research-frame object {
    border-radius: 8px;
    overflow: hidden;
  }

  /* 반응형 디자인 */
  @media (max-width: 1024px) {
    .flex-row {
      flex-direction: column;
    }
    
    .w-\[50\%\] {
      width: 100%;
    }
    
    .space-x-2 > :not([hidden]) ~ :not([hidden]) {
      margin-left: 0;
      margin-top: 0.5rem;
    }
  }

  @media (max-width: 768px) {
    .space-y-2 > :not([hidden]) ~ :not([hidden]) {
      margin-top: 0.5rem;
    }
    
    .p-4 {
      padding: 0.75rem;
    }
    
    .text-lg {
      font-size: 1rem;
    }

    .w-8.h-8 {
      width: 1.5rem;
      height: 1.5rem;
    }
  }

  /* 로딩 상태 개선 */
  .border-dashed {
    animation: dash 1.5s ease-in-out infinite;
  }

  @keyframes dash {
    0%, 100% { border-opacity: 0.3; }
    50% { border-opacity: 0.6; }
  }

  /* 텍스트 가독성 개선 */
  .text-slate-800 {
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  }

  /* 그림자 효과 개선 */
  .shadow-2xl {
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(255, 255, 255, 0.05);
  }
</style>