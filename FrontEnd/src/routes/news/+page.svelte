<script lang="ts">
	import { onMount } from 'svelte';
	import { getRealtimeSearchTerms } from '$lib/api-connector/FinanceApi';
	import { getSearchResultByNaverApi } from '$lib/api-connector/NaverApi';
	import { browser } from '$app/environment';
	import { ProgressCircle, DownLoadProgressBar } from '$lib/component';

	// 타입 정의
	interface NewsItem {
		title: string;
		originallink: string;
		link: string;
		description: string;
		pubDate: string;
	}

	interface SearchTermData {
		term: string;
		news: NewsItem[];
		loading: boolean;
		expanded: boolean;
	}

	// 상태 변수들
	let searchTerms: string[] = [];
	let dateInfo: string = '';
	let searchTermsData: SearchTermData[] = [];
	let loading = false;
	let error = '';
	let selectedTermIndex: number = -1; // 선택된 검색어 인덱스
	
	// 진행률 관련 변수들 (MultiChartBasic 참고)
	let isProgress: boolean = false;
	let loadingCount: number = -1;
	let totalNewsToLoad: number = 0;

	// 실시간 검색어 가져오기
	const fetchRealtimeSearchTerms = async () => {
		try {
			loading = true;
			error = '';
			selectedTermIndex = -1; // 선택 초기화
			const response = await getRealtimeSearchTerms();
			
			if (response && response.search_terms) {
				searchTerms = response.search_terms;
				dateInfo = response.date_info || '';
				
				// 검색어별 데이터 초기화
				searchTermsData = searchTerms.map(term => ({
					term,
					news: [],
					loading: false,
					expanded: false
				}));
			} else {
				error = '실시간 검색어를 가져올 수 없습니다.';
			}
		} catch (err) {
			console.error('실시간 검색어 가져오기 실패:', err);
			error = '실시간 검색어를 가져오는 중 오류가 발생했습니다.';
		} finally {
			loading = false;
		}
	};

	// 모든 검색어의 뉴스를 한번에 가져오기
	const fetchAllNews = async () => {
		if (searchTermsData.length === 0) return;
		
		try {
			isProgress = true;
			loadingCount = 0;
			totalNewsToLoad = searchTermsData.length;
			selectedTermIndex = -1; // 선택 초기화
			
			// 모든 검색어에 대해 순차적으로 뉴스 로드
			for (let i = 0; i < searchTermsData.length; i++) {
				loadingCount = i + 1;
				
				try {
					const response = await getSearchResultByNaverApi('news', {
						query: searchTermsData[i].term,
						display: 10,
						start: 1,
						sort: 'date',
						filter: 'all'
					});
					
					if (response && response.items) {
						searchTermsData[i].news = response.items;
					}
				} catch (err) {
					console.error(`${searchTermsData[i].term} 뉴스 가져오기 실패:`, err);
				}
			}
			
		} catch (err) {
			console.error('전체 뉴스 가져오기 실패:', err);
		} finally {
			isProgress = false;
			loadingCount = -1;
		}
	};

	// 특정 검색어의 뉴스 가져오기 (개별 클릭용)
	const fetchNewsForTerm = async (index: number) => {
		selectedTermIndex = index; // 선택된 항목 설정
		
		const termData = searchTermsData[index];
		if (termData.news.length > 0) {
			// 이미 뉴스가 있으면 바로 표시
			return;
		}

		try {
			searchTermsData[index].loading = true;
			
			const response = await getSearchResultByNaverApi('news', {
				query: termData.term,
				display: 10,
				start: 1,
				sort: 'date',
				filter: 'all'
			});
			
			console.log('네이버 API 응답:', response); // 디버깅용 로그 추가
			
			// items만 체크하도록 조건 간소화
			if (response && response.items) {
				searchTermsData[index].news = response.items;
			} else {
				console.error('뉴스 데이터 가져오기 실패:', response);
			}
		} catch (err) {
			console.error('뉴스 가져오기 실패:', err);
		} finally {
			searchTermsData[index].loading = false;
		}
	};

	// HTML 태그 제거 함수
	const stripHtml = (html: string) => {
		return html.replace(/<[^>]*>/g, '');
	};

	// HTML을 안전하게 렌더링하기 위한 함수
	const sanitizeHtml = (html: string) => {
		// 기본적인 HTML 태그만 허용하고 나머지는 제거
		return html
			.replace(/<script[^>]*>.*?<\/script>/gi, '') // script 태그 제거
			.replace(/<style[^>]*>.*?<\/style>/gi, '') // style 태그 제거
			.replace(/on\w+="[^"]*"/gi, '') // 이벤트 핸들러 제거
			.replace(/javascript:/gi, '') // javascript: 프로토콜 제거
			.trim();
	};

	// 날짜 포맷팅 함수
	const formatDate = (dateString: string) => {
		try {
			const date = new Date(dateString);
			return date.toLocaleDateString('ko-KR') + ' ' + date.toLocaleTimeString('ko-KR', { 
				hour: '2-digit', 
				minute: '2-digit' 
			});
		} catch {
			return dateString;
		}
	};

	// 선택된 검색어의 뉴스 데이터 가져오기
	$: selectedNews = selectedTermIndex >= 0 ? searchTermsData[selectedTermIndex]?.news || [] : [];
	$: selectedTerm = selectedTermIndex >= 0 ? searchTermsData[selectedTermIndex]?.term || '' : '';
	$: selectedLoading = selectedTermIndex >= 0 ? searchTermsData[selectedTermIndex]?.loading || false : false;

	// 컴포넌트 마운트시 실시간 검색어 로드
	onMount(() => {
		if (browser) {
			fetchRealtimeSearchTerms();
		}
	});
</script>

<svelte:head>
	<title>실시간 뉴스 - Finance Website</title>
</svelte:head>

<div class="flex flex-col w-full h-full bg-gradient-to-br from-slate-50 to-gray-100">
	<!-- 현대적인 헤더 -->
	<div class="sticky top-0 z-10 backdrop-blur-md bg-white/80 border-b border-gray-200/50 shadow-sm">
		<div class="flex justify-between items-center p-6">
			<div class="flex items-center space-x-4">
				<div class="flex items-center justify-center w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl shadow-lg">
					<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path>
					</svg>
				</div>
				<div>
					<h1 class="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
						실시간 뉴스
					</h1>
					{#if dateInfo}
						<p class="text-sm text-gray-500 mt-1 flex items-center">
							<svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
							</svg>
							{dateInfo}
						</p>
					{/if}
				</div>
			</div>
			
			<!-- 현대적인 버튼들 -->
			<div class="flex items-center space-x-3">
				<button 
					class="group relative px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-50 disabled:transform-none disabled:shadow-lg"
					on:click={fetchAllNews}
					disabled={loading || isProgress || searchTermsData.length === 0}
				>
					<div class="flex items-center space-x-2">
						{#if isProgress}
							<div class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
						{:else}
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
							</svg>
						{/if}
						<span>{isProgress ? '뉴스 로딩 중...' : '모든 뉴스 로드'}</span>
					</div>
				</button>
				
				<button 
					class="group relative px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-50 disabled:transform-none disabled:shadow-lg"
					on:click={fetchRealtimeSearchTerms}
					disabled={loading || isProgress}
				>
					<div class="flex items-center space-x-2">
						{#if loading}
							<div class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
						{:else}
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
							</svg>
						{/if}
						<span>{loading ? '새로고침 중...' : '새로고침'}</span>
					</div>
				</button>
			</div>
		</div>
	</div>

	<!-- 메인 컨텐츠 -->
	<div class="flex-1 overflow-hidden p-6">
		{#if error}
			<div class="bg-red-50 border border-red-200 text-red-800 px-6 py-4 rounded-xl mb-6 flex items-center space-x-3">
				<svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
				</svg>
				<span>{error}</span>
			</div>
		{/if}

		{#if loading}
			<div class="flex items-center justify-center h-full">
				<ProgressCircle
					size={100}
					thickness={10}
					isLarge={true}
					isTextBlack={true}
					text={'실시간 검색어를 불러오는 중...'}
				/>
			</div>
		{:else if isProgress}
			<div class="flex flex-col items-center justify-center h-full space-y-6">
				<div class="text-center">
					<h3 class="text-xl font-semibold text-gray-800 mb-2">뉴스 데이터 수집 중</h3>
					<p class="text-gray-600">{totalNewsToLoad}개 검색어의 뉴스를 가져오고 있습니다</p>
				</div>
				<div class="w-full max-w-md">
					<DownLoadProgressBar
						min={0}
						max={totalNewsToLoad}
						nowCount={loadingCount}
					/>
				</div>
				<p class="text-sm text-gray-500 font-medium">
					{loadingCount}/{totalNewsToLoad} 완료
				</p>
			</div>
		{:else if searchTermsData.length === 0}
			<div class="flex flex-col items-center justify-center h-full space-y-4">
				<div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center">
					<svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
					</svg>
				</div>
				<div class="text-center">
					<h3 class="text-lg font-medium text-gray-900">검색어가 없습니다</h3>
					<p class="text-gray-500 mt-1">새로고침 버튼을 눌러 실시간 검색어를 불러오세요</p>
				</div>
			</div>
		{:else}
			<!-- 좌우 분할 레이아웃 -->
			<div class="flex h-full space-x-6">
				<!-- 왼쪽: 실시간 검색어 목록 -->
				<div class="w-1/3 flex flex-col min-h-0">
					<div class="bg-white/70 backdrop-blur-sm border border-gray-200/50 rounded-2xl shadow-sm h-full overflow-hidden flex flex-col">
						<div class="p-4 border-b border-gray-100 flex-shrink-0">
							<h2 class="text-lg font-semibold text-gray-800">실시간 검색어</h2>
						</div>
						<div class="flex-1 overflow-y-auto min-h-0">
							{#each searchTermsData as termData, index}
								<button 
									class="search-term-button w-full p-4 text-left hover:bg-blue-50/50 flex justify-between items-center transition-all duration-200 border-b border-gray-50 last:border-b-0 {selectedTermIndex === index ? 'bg-blue-100/70 border-blue-200' : ''} min-h-[60px]"
									on:click={() => fetchNewsForTerm(index)}
								>
									<div class="flex items-center space-x-3 flex-1 min-w-0">
										<div class="flex items-center justify-center w-7 h-7 {selectedTermIndex === index ? 'bg-blue-500' : 'bg-gradient-to-r from-blue-500 to-purple-600'} text-white text-sm font-bold rounded-lg shadow-sm flex-shrink-0">
											{index + 1}
										</div>
										<span class="search-term-text text-base font-medium {selectedTermIndex === index ? 'text-blue-700' : 'text-gray-800'} break-words flex-1 min-w-0 text-left">
											{termData.term}
										</span>
										{#if termData.loading}
											<div class="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full flex-shrink-0"></div>
										{/if}
									</div>
									<div class="flex items-center space-x-2 flex-shrink-0 ml-2">
										{#if termData.news.length > 0}
											<span class="px-2 py-1 {selectedTermIndex === index ? 'bg-blue-200 text-blue-800' : 'bg-gray-100 text-gray-600'} text-xs font-medium rounded-full whitespace-nowrap">
												{termData.news.length}개
											</span>
										{/if}
										<svg 
											class="w-4 h-4 {selectedTermIndex === index ? 'text-blue-500' : 'text-gray-400'} flex-shrink-0"
											fill="none" 
											stroke="currentColor" 
											viewBox="0 0 24 24"
										>
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
										</svg>
									</div>
								</button>
							{/each}
						</div>
					</div>
				</div>

				<!-- 오른쪽: 선택된 검색어의 뉴스 목록 -->
				<div class="flex-1 flex flex-col">
					<div class="bg-white/70 backdrop-blur-sm border border-gray-200/50 rounded-2xl shadow-sm h-full overflow-hidden flex flex-col">
						{#if selectedTermIndex >= 0}
							<div class="p-4 border-b border-gray-100 flex-shrink-0">
								<h2 class="text-lg font-semibold text-gray-800 flex items-center space-x-2">
									<span>'{selectedTerm}' 관련 뉴스</span>
									{#if selectedLoading}
										<div class="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
									{/if}
								</h2>
							</div>
							<div class="flex-1 overflow-y-auto min-h-0">
								{#if selectedLoading}
									<div class="flex items-center justify-center h-full">
										<ProgressCircle
											size={60}
											thickness={5}
											isLarge={false}
											isTextBlack={true}
											text={'뉴스를 불러오는 중...'}
										/>
									</div>
								{:else if selectedNews.length > 0}
									<div class="divide-y divide-gray-50">
										{#each selectedNews as news, newsIndex}
											<div class="p-6 hover:bg-blue-50/30 transition-colors duration-200 group/news">
												<div class="flex justify-between items-start space-x-4">
													<div class="flex-1 min-w-0">
														<a 
															href={news.originallink || news.link} 
															target="_blank" 
															rel="noopener noreferrer"
															class="block group-hover/news:text-blue-600 transition-colors duration-200"
														>
															<h4 class="text-lg font-medium text-gray-900 leading-snug mb-2 line-clamp-2">
																{@html sanitizeHtml(news.title)}
															</h4>
														</a>
														<p class="text-gray-600 text-sm leading-relaxed mb-3 line-clamp-3">
															{@html sanitizeHtml(news.description)}
														</p>
														<div class="flex items-center justify-between">
															<span class="text-xs text-gray-500 flex items-center">
																<svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
																	<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
																</svg>
																{formatDate(news.pubDate)}
															</span>
															<span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full font-medium">
																{newsIndex + 1}/{selectedNews.length}
															</span>
														</div>
													</div>
													<div class="flex-shrink-0">
														<a 
															href={news.originallink || news.link} 
															target="_blank" 
															rel="noopener noreferrer"
															class="inline-flex items-center justify-center w-10 h-10 bg-blue-100 hover:bg-blue-200 text-blue-600 rounded-full transition-colors duration-200"
														>
															<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
															</svg>
														</a>
													</div>
												</div>
											</div>
										{/each}
									</div>
								{:else}
									<div class="flex flex-col items-center justify-center h-full space-y-4">
										<div class="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center">
											<svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
											</svg>
										</div>
										<p class="text-gray-500 text-center">해당 검색어에 대한 뉴스를 찾을 수 없습니다</p>
									</div>
								{/if}
							</div>
						{:else}
							<div class="flex flex-col items-center justify-center h-full space-y-4">
								<div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center">
									<svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"></path>
									</svg>
								</div>
								<div class="text-center">
									<h3 class="text-lg font-medium text-gray-900">검색어를 선택하세요</h3>
									<p class="text-gray-500 mt-1">왼쪽에서 실시간 검색어를 클릭하면 관련 뉴스가 표시됩니다</p>
								</div>
							</div>
						{/if}
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	/* 현대적인 애니메이션 */
	:global(.animate-spin) {
		animation: spin 1s linear infinite;
	}
	
	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	/* 텍스트 말줄임 */
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.line-clamp-3 {
		display: -webkit-box;
		-webkit-line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	/* 스크롤바 스타일링 */
	:global(.overflow-y-auto::-webkit-scrollbar) {
		width: 8px;
	}

	:global(.overflow-y-auto::-webkit-scrollbar-track) {
		background: rgba(243, 244, 246, 0.5);
		border-radius: 4px;
	}

	:global(.overflow-y-auto::-webkit-scrollbar-thumb) {
		background: rgba(156, 163, 175, 0.7);
		border-radius: 4px;
		border: 1px solid rgba(243, 244, 246, 0.5);
	}

	:global(.overflow-y-auto::-webkit-scrollbar-thumb:hover) {
		background: rgba(107, 114, 128, 0.8);
	}

	/* 검색어 텍스트 줄바꿈 및 표시 개선 */
	.search-term-text {
		word-break: break-word;
		overflow-wrap: break-word;
		hyphens: auto;
		line-height: 1.4;
	}

	/* 검색어 버튼 호버 효과 개선 */
	.search-term-button:hover {
		transform: translateX(2px);
	}
</style> 