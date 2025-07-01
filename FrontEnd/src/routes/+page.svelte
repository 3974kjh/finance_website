<script lang="ts">
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { auth } from '$lib/stores/auth';
	import { onMount } from 'svelte';
	import { MultiChartBasic, SingleChartBasic } from '$lib/main';

	let innerHeight: number = 0;
	let innerWidth: number = 0;

	let isSingleMode: boolean = false;
	let isAuthenticated: boolean = false;
	let isLoading: boolean = true;

	let singleChartInfo: {
		title: string,
		searchDuration: {month: number, week: number},
		chartMode: string,
		chartKey: string,
		detailInfo: any
	} | null = null;

	// 컴포넌트 마운트 시 로그인 상태 확인
	onMount(() => {
		// auth store 초기화
		auth.initialize();

		// 로그인 상태 구독
		const unsubscribe = auth.subscribe((authState) => {
			isAuthenticated = authState.isAuthenticated;
			isLoading = false;

			// 로그인되지 않은 경우 로그인 페이지로 리다이렉트
			if (!authState.isAuthenticated) {
				goto(`${base}/login`);
			}
		});

		return unsubscribe;
	});
</script>

<svelte:head>
	<title>대시보드 홈 - FinanceChart</title>
</svelte:head>
<svelte:window bind:innerHeight bind:innerWidth/>
{#if isLoading}
	<!-- 로딩 화면 -->
	<div class="w-full h-full flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-900">
		<div class="text-center">
			<div class="w-16 h-16 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
			<p class="text-slate-200 text-lg font-medium">로딩 중...</p>
		</div>
	</div>
{:else if isAuthenticated}
	<!-- 로그인된 사용자만 차트 기능 표시 -->
	<div class="w-full h-full relative">
		<MultiChartBasic
			fullChartViewerWidth={innerWidth - 100}
			fullChartViewerHeight={innerHeight}
			on:showDetailChartViewerCallback={(e) => {
				singleChartInfo = e.detail;
				isSingleMode = true;
			}}
		/>
		{#if isSingleMode && singleChartInfo}
			<div class="absolute inset-0 z-20 bg-black/50 backdrop-blur-sm">
				<SingleChartBasic
					{singleChartInfo}
					on:closeSingleChartModeCallback={() => {
						isSingleMode = false;
						singleChartInfo = null;
					}}
				/>
			</div>
		{/if}
	</div>
{/if}

<style>
  :global(body) {
    overflow: hidden;
  }
  :global(html) {
    overflow: hidden;
  }

  /* 로딩 스피너 애니메이션 */
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .animate-spin {
    animation: spin 1s linear infinite;
  }
</style>