<script lang="ts">
	import { onMount } from 'svelte';
	import { getRealtimeSearchTerms } from '$lib/api-connector/FinanceApi';
	import { getSearchResultByNaverApi } from '$lib/api-connector/NaverApi';
	import { browser } from '$app/environment';
	import { DownLoadProgressBar } from '$lib/component';

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

	// 키워드 검색 관련 변수들
	let searchKeyword: string = '';
	let isSearching: boolean = false;
	let customSearchData: SearchTermData | null = null;
	
	// 검색 기록 관리 변수들
	let searchHistory: string[] = [];
	let showSearchHistory: boolean = false;
	let maxHistoryItems: number = 10;

	// 검색 모드 관리 (실시간 검색어 vs 직접 검색)
	let searchMode: 'realtime' | 'custom' = 'realtime';

	// 검색 기록 전체 삭제
	const clearAllSearchHistory = () => {
		searchHistory = [];
		// localStorage에서도 삭제
		if (typeof localStorage !== 'undefined') {
			try {
				localStorage.removeItem('newsSearchHistory');
			} catch (error) {
				console.error('검색 기록 삭제 실패:', error);
			}
		}
	};

	// 실시간 검색어 데이터 로드 (localStorage에서)
	const loadRealtimeSearchData = () => {
		if (typeof localStorage !== 'undefined') {
			try {
				const savedData = localStorage.getItem('realtimeSearchData');
				if (savedData) {
					const parsedData = JSON.parse(savedData);
					// 데이터 유효성 검증
					if (parsedData && 
						Array.isArray(parsedData.searchTerms) && 
						typeof parsedData.dateInfo === 'string' &&
						parsedData.timestamp) {
						
						// 저장된 데이터가 24시간 이내인지 확인 (선택적)
						const savedTime = new Date(parsedData.timestamp);
						const now = new Date();
						const hoursDiff = (now.getTime() - savedTime.getTime()) / (1000 * 60 * 60);
						
						// 24시간 이내 데이터면 사용, 아니면 새로 조회
						if (hoursDiff < 24) {
							searchTerms = parsedData.searchTerms;
							dateInfo = parsedData.dateInfo;
							
							// 검색어별 데이터 초기화
							searchTermsData = searchTerms.map(term => ({
								term,
								news: [],
								loading: false,
								expanded: false
							}));
							
							return true; // 캐시된 데이터 사용
						}
					}
				}
			} catch (error) {
				console.error('실시간 검색어 데이터 로드 실패:', error);
			}
		}
		return false; // 캐시된 데이터 없음
	};

	// 실시간 검색어 데이터 저장 (localStorage에)
	const saveRealtimeSearchData = () => {
		if (typeof localStorage !== 'undefined' && searchTerms.length > 0) {
			try {
				const dataToSave = {
					searchTerms: searchTerms,
					dateInfo: dateInfo,
					timestamp: new Date().toISOString()
				};
				localStorage.setItem('realtimeSearchData', JSON.stringify(dataToSave));
			} catch (error) {
				console.error('실시간 검색어 데이터 저장 실패:', error);
			}
		}
	};

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
				
				// localStorage에 저장 (새로고침 시에만)
				saveRealtimeSearchData();
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

	// 초기 데이터 로드 (페이지 진입 시)
	const initializeData = async () => {
		// 먼저 localStorage에서 캐시된 데이터 시도
		const hasCachedData = loadRealtimeSearchData();
		
		if (!hasCachedData) {
			// 캐시된 데이터가 없으면 API 호출
			await fetchRealtimeSearchTerms();
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
		
		// 뉴스 결과 영역을 최상단으로 스크롤
		setTimeout(() => {
			const newsContainer = document.querySelector('#news-results-container');
			if (newsContainer) {
				newsContainer.scrollTop = 0;
			}
		}, 0);
		
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

	// 검색 기록 로드
	const loadSearchHistory = () => {
		if (typeof localStorage !== 'undefined') {
			try {
				const saved = localStorage.getItem('newsSearchHistory');
				if (saved) {
					const parsedHistory = JSON.parse(saved);
					// 배열인지 확인하고 유효한 데이터만 사용
					if (Array.isArray(parsedHistory)) {
						searchHistory = parsedHistory.filter(item => 
							typeof item === 'string' && item.trim().length > 0
						).slice(0, maxHistoryItems); // 최대 개수 제한
					} else {
						searchHistory = [];
					}
				} else {
					searchHistory = [];
				}
			} catch (error) {
				console.error('검색 기록 로드 실패:', error);
				searchHistory = [];
			}
		} else {
			searchHistory = [];
		}
	};

	// 검색 기록 저장
	const saveSearchHistory = () => {
		if (typeof localStorage !== 'undefined') {
			try {
				localStorage.setItem('newsSearchHistory', JSON.stringify(searchHistory));
			} catch (error) {
				console.error('검색 기록 저장 실패:', error);
			}
		}
	};

	// 검색 기록에 추가
	const addToSearchHistory = (keyword: string) => {
		const trimmedKeyword = keyword.trim();
		if (!trimmedKeyword) return;
		
		// 중복 제거 (대소문자 구분 없이)
		searchHistory = searchHistory.filter(item => 
			item.toLowerCase() !== trimmedKeyword.toLowerCase()
		);
		
		// 맨 앞에 추가
		searchHistory.unshift(trimmedKeyword);
		
		// 최대 개수 제한
		if (searchHistory.length > maxHistoryItems) {
			searchHistory = searchHistory.slice(0, maxHistoryItems);
		}
		
		// localStorage에 즉시 저장
		saveSearchHistory();
	};

	// 검색 기록에서 제거
	const removeFromSearchHistory = (keyword: string) => {
		searchHistory = searchHistory.filter(item => item !== keyword);
		// localStorage에 즉시 저장
		saveSearchHistory();
	};

	// 검색 기록 항목 클릭
	const selectFromHistory = (keyword: string) => {
		searchKeyword = keyword;
		showSearchHistory = false;
		searchKeywordNews();
	};

	// 검색 모드 전환
	const switchToCustomSearch = () => {
		searchMode = 'custom';
		selectedTermIndex = -1;
		customSearchData = null;
	};

	const switchToRealtimeSearch = () => {
		searchMode = 'realtime';
		customSearchData = null;
		searchKeyword = '';
	};

	// 키워드 검색 함수
	const searchKeywordNews = async () => {
		if (!searchKeyword.trim()) return;
		
		try {
			isSearching = true;
			selectedTermIndex = -1; // 실시간 검색어 선택 해제
			searchMode = 'custom'; // 직접 검색 모드로 전환
			
			// 검색 기록에 추가
			addToSearchHistory(searchKeyword.trim());
			
			const response = await getSearchResultByNaverApi('news', {
				query: searchKeyword.trim(),
				display: 20, // 키워드 검색은 더 많은 결과 표시
				start: 1,
				sort: 'date',
				filter: 'all'
			});
			
			if (response && response.items) {
				customSearchData = {
					term: searchKeyword.trim(),
					news: response.items,
					loading: false,
					expanded: false
				};
			} else {
				customSearchData = {
					term: searchKeyword.trim(),
					news: [],
					loading: false,
					expanded: false
				};
			}
		} catch (err) {
			console.error('키워드 검색 실패:', err);
			customSearchData = {
				term: searchKeyword.trim(),
				news: [],
				loading: false,
				expanded: false
			};
		} finally {
			isSearching = false;
		}
	};

	// 검색 초기화 함수
	const clearSearch = () => {
		searchKeyword = '';
		customSearchData = null;
		selectedTermIndex = -1;
	};

	// 선택된 검색어의 뉴스 데이터 가져오기 (키워드 검색 결과 우선)
	$: selectedNews = customSearchData ? customSearchData.news : (selectedTermIndex >= 0 ? searchTermsData[selectedTermIndex]?.news || [] : []);
	$: selectedTerm = customSearchData ? customSearchData.term : (selectedTermIndex >= 0 ? searchTermsData[selectedTermIndex]?.term || '' : '');
	$: selectedLoading = customSearchData ? false : (selectedTermIndex >= 0 ? searchTermsData[selectedTermIndex]?.loading || false : false);

	// 컴포넌트 마운트시 실시간 검색어 로드
	onMount(() => {
		if (browser) {
			loadSearchHistory(); // 검색 기록 로드
			initializeData();
		}
	});
</script>

<svelte:head>
	<title>실시간 뉴스 - Finance Website</title>
</svelte:head>

<div class="flex flex-col w-full h-full bg-gradient-to-br from-indigo-50 via-white to-cyan-50 relative overflow-hidden">
	<!-- 배경 데코레이션 -->
	<div class="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,_rgba(255,255,255,0.15)_1px,_transparent_0)] bg-[size:24px_24px] pointer-events-none"></div>
	<div class="absolute top-0 left-0 w-96 h-96 bg-gradient-to-r from-blue-400/20 to-purple-400/20 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2"></div>
	<div class="absolute bottom-0 right-0 w-96 h-96 bg-gradient-to-r from-cyan-400/20 to-teal-400/20 rounded-full blur-3xl translate-x-1/2 translate-y-1/2"></div>
	
	<!-- 현대적인 헤더 -->
	<div class="sticky top-0 z-10 backdrop-blur-xl bg-white/70 border-b border-white/20 shadow-lg shadow-gray-900/5">
		<div class="flex justify-between items-center p-8">
			<div class="flex items-center space-x-6">
				<div class="relative">
					<div class="flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-600 via-purple-600 to-teal-600 rounded-2xl shadow-2xl shadow-blue-500/25 transform rotate-3">
						<svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path>
						</svg>
					</div>
					<div class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full animate-pulse"></div>
				</div>
				<div>
					<h1 class="text-4xl font-black bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent tracking-tight">
						실시간 뉴스
					</h1>
					{#if dateInfo}
						<p class="text-sm text-gray-600 mt-2 flex items-center font-medium">
							<span class="w-2 h-2 bg-emerald-500 rounded-full mr-2 animate-pulse"></span>
							<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
							</svg>
							{dateInfo}
						</p>
					{/if}
				</div>
			</div>
			
			<!-- 현대적인 버튼들 -->
			<div class="flex items-center space-x-4">
				<!-- 키워드 검색 입력창 -->
				<div class="relative">
					<div class="flex items-center bg-white/90 backdrop-blur-sm border border-white/30 rounded-2xl shadow-xl shadow-gray-900/10 overflow-hidden" style="width: 400px;">
						<div class="flex items-center px-4 py-3 flex-1 min-w-0">
							<svg class="w-5 h-5 text-gray-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
							</svg>
							<input
								type="text"
								placeholder="키워드로 뉴스 검색..."
								class="bg-transparent outline-none text-gray-800 placeholder-gray-500 font-medium flex-1 min-w-0"
								bind:value={searchKeyword}
								disabled={loading || isProgress || isSearching}
								on:keypress={(e) => {
									if (e.key === 'Enter') {
										searchKeywordNews();
									}
								}}
							/>
						</div>
						<!-- 고정 너비 버튼 영역 -->
						<div class="flex items-center" style="width: 120px;">
							{#if searchKeyword}
								<button
									class="px-3 py-3 text-gray-500 hover:text-gray-700 transition-colors duration-200"
									on:click={clearSearch}
									title="검색 초기화"
								>
									<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
									</svg>
								</button>
							{/if}
							<!-- 검색 버튼을 항상 오른쪽 끝에 고정 -->
							<button
								class="px-5 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white font-bold hover:from-orange-600 hover:to-red-600 transition-all duration-300 disabled:opacity-50 rounded-r-2xl ml-auto"
								on:click={searchKeywordNews}
								disabled={!searchKeyword.trim() || loading || isProgress || isSearching}
							>
								{#if isSearching}
									<div class="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></div>
								{:else}
									<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
									</svg>
								{/if}
							</button>
						</div>
					</div>
				</div>
				
				<button 
					class="group relative px-8 py-4 bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 text-white font-bold rounded-2xl shadow-xl shadow-emerald-500/30 hover:shadow-2xl hover:shadow-emerald-500/40 transform hover:-translate-y-1 transition-all duration-300 disabled:opacity-50 disabled:transform-none disabled:shadow-lg overflow-hidden"
					on:click={fetchAllNews}
					disabled={loading || isProgress || searchTermsData.length === 0}
				>
					<div class="absolute inset-0 bg-gradient-to-r from-emerald-600 to-teal-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
					<div class="relative flex items-center space-x-3">
						{#if isProgress}
							<div class="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></div>
						{:else}
							<svg class="w-5 h-5 group-hover:rotate-180 transition-transform duration-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
							</svg>
						{/if}
						<span>{isProgress ? '뉴스 로딩 중...' : '모든 뉴스 로드'}</span>
					</div>
				</button>
				
				<button 
					class="group relative px-8 py-4 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 text-white font-bold rounded-2xl shadow-xl shadow-blue-500/30 hover:shadow-2xl hover:shadow-blue-500/40 transform hover:-translate-y-1 transition-all duration-300 disabled:opacity-50 disabled:transform-none disabled:shadow-lg overflow-hidden"
					on:click={fetchRealtimeSearchTerms}
					disabled={loading || isProgress}
				>
					<div class="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
					<div class="relative flex items-center space-x-3">
						{#if loading}
							<div class="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></div>
						{:else}
							<svg class="w-5 h-5 group-hover:rotate-180 transition-transform duration-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
	<div class="flex-1 overflow-hidden p-8">
		{#if error}
			<div class="bg-gradient-to-r from-red-50 to-pink-50 border border-red-200/50 text-red-800 px-8 py-6 rounded-3xl mb-8 flex items-center space-x-4 shadow-xl shadow-red-500/10">
				<div class="flex-shrink-0 w-12 h-12 bg-red-500 rounded-2xl flex items-center justify-center">
					<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
					</svg>
				</div>
				<div>
					<h3 class="font-bold text-lg mb-1">오류가 발생했습니다</h3>
					<span class="text-red-700">{error}</span>
				</div>
			</div>
		{/if}

		{#if loading}
			<div class="flex items-center justify-center h-full">
				<div class="text-center space-y-8">
					<div class="relative">
						<div class="w-32 h-32 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full opacity-20 animate-ping"></div>
					</div>
					<div class="space-y-3">
						<h3 class="text-2xl font-bold text-gray-800">데이터를 가져오고 있어요</h3>
						<p class="text-gray-600">잠시만 기다려주세요...</p>
					</div>
				</div>
			</div>
		{:else if isProgress}
			<div class="flex flex-col items-center justify-center h-full space-y-8">
				<div class="relative">
					<div class="w-40 h-40 bg-gradient-to-r from-emerald-400 to-teal-400 rounded-full opacity-20 animate-pulse"></div>
					<div class="absolute inset-0 flex items-center justify-center">
						<div class="text-center space-y-4">
							<div class="w-24 h-24 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-2xl flex items-center justify-center shadow-2xl shadow-emerald-500/30">
								<svg class="w-12 h-12 text-white animate-bounce" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"></path>
								</svg>
							</div>
						</div>
					</div>
				</div>
				<div class="text-center space-y-4">
					<h3 class="text-3xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">뉴스 데이터 수집 중</h3>
					<p class="text-xl text-gray-700 font-medium">{totalNewsToLoad}개 검색어의 뉴스를 가져오고 있습니다</p>
				</div>
				<div class="w-full max-w-lg">
					<DownLoadProgressBar
						min={0}
						max={totalNewsToLoad}
						nowCount={loadingCount}
					/>
				</div>
				<div class="bg-white/80 backdrop-blur-sm px-6 py-3 rounded-2xl shadow-lg">
					<p class="text-lg text-gray-700 font-bold">
						{loadingCount}/{totalNewsToLoad} 완료
					</p>
				</div>
			</div>
		{:else if searchTermsData.length === 0}
			<div class="flex flex-col items-center justify-center h-full space-y-8">
				<div class="relative">
					<div class="w-32 h-32 bg-gradient-to-r from-gray-200 to-gray-300 rounded-full opacity-50"></div>
					<div class="absolute inset-0 flex items-center justify-center">
						<div class="w-20 h-20 bg-gradient-to-r from-gray-400 to-gray-500 rounded-2xl flex items-center justify-center shadow-xl">
							<svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
							</svg>
						</div>
					</div>
				</div>
				<div class="text-center space-y-4">
					<h3 class="text-2xl font-bold text-gray-900">검색어가 없습니다</h3>
					<p class="text-gray-600 text-lg">새로고침 버튼을 눌러 실시간 검색어를 불러오세요</p>
				</div>
			</div>
		{:else}
			<!-- 좌우 분할 레이아웃 -->
			<div class="flex h-full space-x-8">
				<!-- 왼쪽: 실시간 검색어 목록 -->
				<div class="w-1/3 flex flex-col min-h-0">
					<div class="bg-white/60 backdrop-blur-xl border border-white/30 rounded-3xl shadow-2xl shadow-gray-900/10 h-full overflow-hidden flex flex-col">
						<div class="p-6 border-b border-white/20 flex-shrink-0 bg-gradient-to-r from-blue-50/50 to-purple-50/50">
							<div class="flex items-center justify-between">
								<div class="flex items-center space-x-3">
									<div class="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl flex items-center justify-center">
										<svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											{#if searchMode === 'realtime'}
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
											{:else}
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
											{/if}
										</svg>
									</div>
									<h2 class="text-xl font-bold bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent">
										{searchMode === 'realtime' ? '실시간 검색어' : '직접 검색'}
									</h2>
								</div>
								<!-- 모드 전환 버튼 -->
								<div class="flex space-x-2">
									<button
										class="px-3 py-1.5 text-sm font-medium rounded-xl transition-all duration-300 {searchMode === 'realtime' ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg shadow-blue-500/30' : 'bg-gray-200/80 text-gray-600 hover:bg-gray-300/80'}"
										on:click={switchToRealtimeSearch}
									>
										실시간
									</button>
									<button
										class="px-3 py-1.5 text-sm font-medium rounded-xl transition-all duration-300 {searchMode === 'custom' ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white shadow-lg shadow-orange-500/30' : 'bg-gray-200/80 text-gray-600 hover:bg-gray-300/80'}"
										on:click={switchToCustomSearch}
									>
										직접검색
									</button>
								</div>
							</div>
						</div>
						<div class="flex-1 overflow-y-auto min-h-0">
							{#if searchMode === 'custom'}
								<!-- 직접 검색 모드 -->
								<div class="p-4 space-y-4">
									{#if customSearchData}
										<!-- 현재 검색 결과 -->
										<div class="bg-gradient-to-r from-orange-50 to-red-50 border border-orange-200/50 rounded-2xl p-4">
											<div class="flex items-center space-x-3">
												<div class="w-8 h-8 bg-gradient-to-r from-orange-500 to-red-500 rounded-xl flex items-center justify-center">
													<svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
													</svg>
												</div>
												<div class="flex-1">
													<h3 class="font-bold text-orange-800">현재 검색</h3>
													<p class="text-sm text-orange-700">'{customSearchData.term}' 검색 결과 {customSearchData.news.length}개</p>
												</div>
											</div>
										</div>
									{/if}
									
									{#if searchHistory.length > 0}
										<!-- 검색 기록 -->
										<div class="space-y-2">
											<div class="flex items-center justify-between">
												<h3 class="text-sm font-bold text-gray-800 flex items-center">
													<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
													</svg>
													최근 검색어
												</h3>
												<button
													class="text-xs text-gray-500 hover:text-red-500 transition-colors duration-200"
													on:click={clearAllSearchHistory}
												>
													전체 삭제
												</button>
											</div>
											<div class="space-y-1 max-h-96 overflow-y-auto">
												{#each searchHistory as historyItem, index}
													<div class="flex items-center justify-between hover:bg-gray-50/80 px-3 py-2 rounded-xl group transition-colors duration-200">
														<button
															class="flex-1 text-left text-sm text-gray-700 hover:text-gray-900 font-medium"
															on:click={() => selectFromHistory(historyItem)}
														>
															<svg class="w-3 h-3 inline mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
															</svg>
															{historyItem}
														</button>
														<button
															class="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all duration-200"
															on:click={() => removeFromSearchHistory(historyItem)}
															title="삭제"
														>
															<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
															</svg>
														</button>
													</div>
												{/each}
											</div>
										</div>
									{:else}
										<!-- 검색 기록이 없을 때 -->
										<div class="text-center py-8">
											<div class="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
												<svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
												</svg>
											</div>
											<h3 class="text-lg font-bold text-gray-600 mb-2">검색 기록이 없습니다</h3>
											<p class="text-sm text-gray-500">상단 검색창에서 키워드를 검색해보세요</p>
										</div>
									{/if}
								</div>
							{:else}
								<!-- 기존 실시간 검색어 목록 -->
								{#each searchTermsData as termData, index}
									<button 
										class="search-term-button w-full p-5 text-left flex justify-between items-center transition-all duration-300 {index === searchTermsData.length - 1 ? '' : 'border-b border-white/10'} {selectedTermIndex === index ? 'bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-blue-200/30 shadow-lg shadow-blue-500/10' : 'hover:bg-white/40'} min-h-[72px] group focus:outline-none"
										on:click={(e) => {
											e.preventDefault();
											e.stopPropagation();
											customSearchData = null; // 키워드 검색 결과 초기화
											fetchNewsForTerm(index);
										}}
									>
										<div class="flex items-center space-x-4 flex-1 min-w-0">
											<div class="flex items-center justify-center w-10 h-10 {selectedTermIndex === index ? 'bg-gradient-to-r from-blue-500 to-purple-500 shadow-lg shadow-blue-500/30' : 'bg-gradient-to-r from-blue-400 to-purple-400 group-hover:shadow-lg group-hover:shadow-blue-400/20'} text-white text-sm font-bold rounded-2xl flex-shrink-0 transition-all duration-300 group-hover:scale-110">
												{index + 1}
											</div>
											<span class="search-term-text text-lg font-semibold {selectedTermIndex === index ? 'text-blue-700' : 'text-gray-800 group-hover:text-gray-900'} break-words flex-1 min-w-0 text-left transition-colors duration-300">
												{termData.term}
											</span>
											{#if termData.loading}
												<div class="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full flex-shrink-0"></div>
											{/if}
										</div>
										<div class="flex items-center space-x-3 flex-shrink-0 ml-3">
											{#if termData.news.length > 0}
												<span class="px-3 py-1.5 {selectedTermIndex === index ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30' : 'bg-gray-200/80 text-gray-700 group-hover:bg-gray-300/80'} text-sm font-bold rounded-full whitespace-nowrap transition-all duration-300">
													{termData.news.length}개
												</span>
											{/if}
											<svg 
												class="w-5 h-5 {selectedTermIndex === index ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-600'} flex-shrink-0 transition-all duration-300 group-hover:translate-x-1"
												fill="none" 
												stroke="currentColor" 
												viewBox="0 0 24 24"
											>
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
											</svg>
										</div>
									</button>
								{/each}
							{/if}
						</div>
					</div>
				</div>

				<!-- 오른쪽: 선택된 검색어의 뉴스 목록 -->
				<div class="flex-1 flex flex-col">
					<div class="bg-white/60 backdrop-blur-xl border border-white/30 rounded-3xl shadow-2xl shadow-gray-900/10 h-full overflow-hidden flex flex-col">
						{#if customSearchData || selectedTermIndex >= 0}
							<div class="p-6 border-b border-white/20 flex-shrink-0 bg-gradient-to-r from-emerald-50/50 to-teal-50/50">
								<div class="flex items-center justify-between">
									<div class="flex items-center space-x-3">
										<div class="w-8 h-8 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-xl flex items-center justify-center">
											<svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path>
											</svg>
										</div>
										<h2 class="text-xl font-bold bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent">
											'{selectedTerm}' 관련 뉴스
										</h2>
									</div>
									{#if selectedLoading || isSearching}
										<div class="animate-spin h-6 w-6 border-2 border-emerald-500 border-t-transparent rounded-full"></div>
									{/if}
								</div>
							</div>
							<div class="flex-1 overflow-y-auto min-h-0" id="news-results-container">
								{#if selectedLoading || isSearching}
									<div class="flex items-center justify-center h-full">
										<div class="text-center space-y-6">
											<div class="relative">
												<div class="w-24 h-24 bg-gradient-to-r from-emerald-400 to-teal-400 rounded-full opacity-20 animate-pulse"></div>
											</div>
											<div class="space-y-2">
												<h3 class="text-xl font-bold text-gray-800">뉴스를 가져오고 있어요</h3>
												<p class="text-gray-600">잠시만 기다려주세요...</p>
											</div>
										</div>
									</div>
								{:else if selectedNews.length > 0}
									<div class="divide-y divide-white/10">
										{#each selectedNews as news, newsIndex}
											<div class="p-8 hover:bg-white/20 transition-all duration-300 group/news">
												<div class="flex justify-between items-start space-x-6">
													<div class="flex-1 min-w-0 space-y-4">
														<a 
															href={news.originallink || news.link} 
															target="_blank" 
															rel="noopener noreferrer"
															class="block group-hover/news:text-emerald-600 transition-colors duration-300"
														>
															<h4 class="text-xl font-bold text-gray-900 leading-relaxed mb-3 line-clamp-2 group-hover/news:text-emerald-700 transition-colors duration-300">
																{@html sanitizeHtml(news.title)}
															</h4>
														</a>
														<p class="text-gray-700 text-base leading-relaxed mb-4 line-clamp-3">
															{@html sanitizeHtml(news.description)}
														</p>
														<div class="flex items-center justify-between">
															<div class="flex items-center space-x-4">
																<span class="text-sm text-gray-500 flex items-center bg-gray-100/60 px-3 py-1.5 rounded-full">
																	<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
																		<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
																	</svg>
																	{formatDate(news.pubDate)}
																</span>
																<span class="px-3 py-1.5 bg-gradient-to-r from-blue-500/10 to-purple-500/10 text-blue-700 text-sm rounded-full font-semibold border border-blue-200/30">
																	{newsIndex + 1}/{selectedNews.length}
																</span>
															</div>
														</div>
													</div>
													<div class="flex-shrink-0">
														<a 
															href={news.originallink || news.link} 
															target="_blank" 
															rel="noopener noreferrer"
															class="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white rounded-2xl shadow-xl shadow-emerald-500/30 hover:shadow-2xl hover:shadow-emerald-500/40 transition-all duration-300 hover:scale-110 group"
														>
															<svg class="w-6 h-6 group-hover:rotate-12 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
															</svg>
														</a>
													</div>
												</div>
											</div>
										{/each}
									</div>
								{:else}
									<div class="flex flex-col items-center justify-center h-full space-y-8">
										<div class="relative">
											<div class="w-32 h-32 bg-gradient-to-r from-gray-200 to-gray-300 rounded-full opacity-50"></div>
											<div class="absolute inset-0 flex items-center justify-center">
												<div class="w-20 h-20 bg-gradient-to-r from-gray-400 to-gray-500 rounded-2xl flex items-center justify-center shadow-xl">
													<svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
													</svg>
												</div>
											</div>
										</div>
										<div class="text-center space-y-4">
											<h3 class="text-2xl font-bold text-gray-900">뉴스를 찾을 수 없어요</h3>
											<p class="text-gray-600 text-lg">해당 검색어에 대한 뉴스가 없습니다</p>
										</div>
									</div>
								{/if}
							</div>
						{:else}
							<div class="flex flex-col items-center justify-center h-full space-y-8">
								<div class="relative">
									<div class="w-40 h-40 bg-gradient-to-r from-indigo-200 to-purple-200 rounded-full opacity-50 animate-pulse"></div>
									<div class="absolute inset-0 flex items-center justify-center">
										<div class="w-24 h-24 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-3xl flex items-center justify-center shadow-2xl shadow-indigo-500/30">
											<svg class="w-12 h-12 text-white animate-bounce" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"></path>
											</svg>
										</div>
									</div>
								</div>
								<div class="text-center space-y-4">
									<h3 class="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">검색어를 선택하세요</h3>
									<p class="text-gray-600 text-xl">왼쪽에서 실시간 검색어를 클릭하면<br/>관련 뉴스가 표시됩니다</p>
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
	
	:global(.animate-pulse) {
		animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
	}
	
	:global(.animate-bounce) {
		animation: bounce 1s infinite;
	}
	
	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	
	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}
	
	@keyframes bounce {
		0%, 100% {
			transform: translateY(-25%);
			animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
		}
		50% {
			transform: translateY(0);
			animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
		}
	}

	/* 현대적인 텍스트 말줄임 */
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
		line-height: 1.5;
	}

	.line-clamp-3 {
		display: -webkit-box;
		-webkit-line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
		line-height: 1.6;
	}

	/* 현대적인 스크롤바 스타일링 */
	:global(.overflow-y-auto::-webkit-scrollbar) {
		width: 6px;
	}

	:global(.overflow-y-auto::-webkit-scrollbar-track) {
		background: rgba(255, 255, 255, 0.1);
		border-radius: 10px;
	}

	:global(.overflow-y-auto::-webkit-scrollbar-thumb) {
		background: linear-gradient(45deg, rgba(59, 130, 246, 0.6), rgba(147, 51, 234, 0.6));
		border-radius: 10px;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	:global(.overflow-y-auto::-webkit-scrollbar-thumb:hover) {
		background: linear-gradient(45deg, rgba(59, 130, 246, 0.8), rgba(147, 51, 234, 0.8));
	}

	/* 검색어 버튼 개선된 스타일 */
	.search-term-button {
		backdrop-filter: blur(10px);
		border-radius: 16px;
		position: relative;
		overflow: hidden;
		will-change: transform;
		backface-visibility: hidden;
	}
	
	.search-term-button:focus {
		outline: none !important;
		box-shadow: none !important;
	}
	
	.search-term-button::before {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, 
			transparent, 
			rgba(255, 255, 255, 0.3), 
			transparent
		);
		transition: left 0.5s;
	}
	
	.search-term-button:hover::before {
		left: 100%;
	}
	
	.search-term-button:hover {
		background: rgba(255, 255, 255, 0.3) !important;
		border-color: rgba(255, 255, 255, 0.4) !important;
		transform: translateY(-2px);
		box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
	}
	
	.search-term-button:active {
		transform: translateY(0);
	}

	/* 검색어 텍스트 스타일 */
	.search-term-text {
		word-break: break-word;
		overflow-wrap: break-word;
		hyphens: auto;
		line-height: 1.5;
		font-weight: 600;
		letter-spacing: -0.025em;
	}

	/* 글래스모피즘 효과 강화 */
	:global(.backdrop-blur-xl) {
		backdrop-filter: blur(24px) saturate(180%);
		-webkit-backdrop-filter: blur(24px) saturate(180%);
	}

	/* 그라데이션 텍스트 애니메이션 */
	@keyframes gradient-flow {
		0%, 100% {
			background-position: 0% 50%;
		}
		50% {
			background-position: 100% 50%;
		}
	}

	.gradient-text-animated {
		background: linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #f5576c);
		background-size: 400% 400%;
		animation: gradient-flow 3s ease infinite;
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}

	/* 호버 시 아이콘 회전 애니메이션 */
	@keyframes icon-rotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	/* 현대적인 그림자 효과 */
	.modern-shadow {
		box-shadow: 
			0 4px 6px -1px rgba(0, 0, 0, 0.1),
			0 2px 4px -1px rgba(0, 0, 0, 0.06),
			0 0 0 1px rgba(255, 255, 255, 0.05);
	}

	.modern-shadow-lg {
		box-shadow: 
			0 10px 15px -3px rgba(0, 0, 0, 0.1),
			0 4px 6px -2px rgba(0, 0, 0, 0.05),
			0 0 0 1px rgba(255, 255, 255, 0.1);
	}

	/* 부드러운 전환 효과 */
	.smooth-transition {
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	}

	/* 반응형 폰트 크기 */
	@media (max-width: 768px) {
		.search-term-text {
			font-size: 0.9rem;
		}
		
		.line-clamp-2,
		.line-clamp-3 {
			line-height: 1.4;
		}
	}

	/* 검색 기록 드롭다운 스크롤바 */
	.max-h-60::-webkit-scrollbar {
		width: 4px;
	}

	.max-h-60::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.05);
	}

	.max-h-60::-webkit-scrollbar-thumb {
		background: rgba(0, 0, 0, 0.2);
		border-radius: 2px;
	}

	.max-h-60::-webkit-scrollbar-thumb:hover {
		background: rgba(0, 0, 0, 0.3);
	}

	/* 검색 기록 영역 스크롤바 */
	.max-h-96::-webkit-scrollbar {
		width: 4px;
	}

	.max-h-96::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.05);
	}

	.max-h-96::-webkit-scrollbar-thumb {
		background: rgba(0, 0, 0, 0.2);
		border-radius: 2px;
	}

	.max-h-96::-webkit-scrollbar-thumb:hover {
		background: rgba(0, 0, 0, 0.3);
	}
</style> 