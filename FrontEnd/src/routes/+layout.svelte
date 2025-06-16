<script lang="ts">
	import '../app.css';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { page } from "$app/stores";
	import { Toaster } from 'svelte-french-toast';

	// toast 간격 설정
	const toastGutter: number = 10;

	// toast 간격 설정
	const toastReverseOrder: boolean = true;

	const toastPosition:
		| 'top-center'
		| 'top-left'
		| 'top-right'
		| 'top-start'
		| 'top-end'
		| 'bottom-center'
		| 'bottom-left'
		| 'bottom-right'
		| 'bottom-start'
		| 'bottom-end'
		| undefined = 'top-center';

	/**
	 * toast option - 다크 선명 테마로 개선
	 */
	const toastOptions = {
		id: 'toast',
		position: undefined,
		style: 'padding: 16px 20px; color: #f8fafc; background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(16px); border-radius: 16px; border: 1px solid rgba(59, 130, 246, 0.3); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 0 20px rgba(59, 130, 246, 0.1); font-weight: 500;',
		className: 'toast-info',
		error: {
			className: 'toast-error',
			style: 'padding: 16px 20px; color: #fecaca; background: rgba(127, 29, 29, 0.95); backdrop-filter: blur(16px); border-radius: 16px; border: 1px solid rgba(239, 68, 68, 0.4); box-shadow: 0 20px 25px -5px rgba(220, 38, 38, 0.3), 0 0 20px rgba(239, 68, 68, 0.2); font-weight: 500;'
		},
		success: {
			className: 'toast-success',
			style: 'padding: 16px 20px; color: #bbf7d0; background: rgba(20, 83, 45, 0.95); backdrop-filter: blur(16px); border-radius: 16px; border: 1px solid rgba(34, 197, 94, 0.4); box-shadow: 0 20px 25px -5px rgba(5, 150, 105, 0.3), 0 0 20px rgba(34, 197, 94, 0.2); font-weight: 500;'
		}
	};

	// 네비게이션 메뉴 데이터
	const navigationItems = [
		{ 
			path: '/', 
			label: 'HOME', 
			icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
			gradient: 'from-blue-500 to-indigo-600',
			description: '대시보드 홈'
		},
		{ 
			path: '/analyze', 
			label: 'ANALYZE', 
			icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
			gradient: 'from-emerald-500 to-teal-600',
			description: '데이터 분석'
		},
		{ 
			path: '/statistic', 
			label: 'STATISTIC', 
			icon: 'M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z',
			gradient: 'from-purple-500 to-pink-600',
			description: '통계 정보'
		},
		{ 
			path: '/webSearch', 
			label: 'SEARCH', 
			icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
			gradient: 'from-orange-500 to-red-600',
			description: '웹 검색'
		},
		{ 
			path: '/news', 
			label: 'NEWS', 
			icon: 'M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z',
			gradient: 'from-cyan-500 to-blue-600',
			description: '실시간 뉴스'
		},
		{ 
			path: '/invest', 
			label: 'INVEST', 
			icon: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1',
			gradient: 'from-green-500 to-emerald-600',
			description: '투자 정보'
		},
		{ 
			path: '/timeLine', 
			label: 'TIMELINE', 
			icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
			gradient: 'from-violet-500 to-purple-600',
			description: '시간별 추이'
		}
	];

	// 사이드바 확장 상태
	let isExpanded = false;
	let expandTimeout: NodeJS.Timeout | null = null;
	let collapseTimeout: NodeJS.Timeout | null = null;
	let isHovering = false; // 실제 마우스 호버 상태 추적

	// 사이드바 확장 함수 (지연 시간 포함)
	const handleMouseEnter = () => {
		isHovering = true;
		
		// 축소 타이머가 있다면 즉시 취소
		if (collapseTimeout) {
			clearTimeout(collapseTimeout);
			collapseTimeout = null;
		}
		
		// 이미 확장된 상태라면 즉시 반환
		if (isExpanded) {
			return;
		}
		
		// 확장 타이머가 있다면 취소하고 새로 시작
		if (expandTimeout) {
			clearTimeout(expandTimeout);
		}
		
		// 짧은 지연 후 확장 (너무 빠른 마우스 이동 필터링)
		expandTimeout = setTimeout(() => {
			if (isHovering) { // 여전히 호버 중인지 확인
				isExpanded = true;
			}
			expandTimeout = null;
		}, 100); // 150ms에서 100ms로 단축
	};

	// 사이드바 축소 함수 (지연 시간 포함)
	const handleMouseLeave = () => {
		isHovering = false;
		
		// 확장 타이머가 있다면 즉시 취소
		if (expandTimeout) {
			clearTimeout(expandTimeout);
			expandTimeout = null;
		}
		
		// 축소 타이머가 있다면 취소하고 새로 시작
		if (collapseTimeout) {
			clearTimeout(collapseTimeout);
		}
		
		// 짧은 지연 후 축소
		collapseTimeout = setTimeout(() => {
			if (!isHovering) { // 여전히 호버 중이 아닌지 확인
				isExpanded = false;
			}
			collapseTimeout = null;
		}, 150); // 200ms에서 150ms로 단축
	};
</script>

<Toaster gutter={toastGutter} reverseOrder={toastReverseOrder} position={toastPosition} {toastOptions} />

<div class="flex flex-row w-screen h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-900 relative overflow-hidden">
	<!-- 배경 데코레이션 -->
	<div class="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,_rgba(59,130,246,0.1)_1px,_transparent_0)] bg-[size:32px_32px] pointer-events-none"></div>
	<div class="absolute top-0 left-0 w-96 h-96 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2 animate-pulse"></div>
	<div class="absolute bottom-0 right-0 w-96 h-96 bg-gradient-to-r from-cyan-500/20 to-teal-500/20 rounded-full blur-3xl translate-x-1/2 translate-y-1/2 animate-pulse"></div>
	<div class="absolute top-1/2 left-1/2 w-64 h-64 bg-gradient-to-r from-violet-500/15 to-pink-500/15 rounded-full blur-2xl -translate-x-1/2 -translate-y-1/2"></div>
	
	<!-- 확장 가능한 사이드바 -->
	<div 
		class="sidebar-container relative z-20"
		on:mouseenter={handleMouseEnter}
		on:mouseleave={handleMouseLeave}
	>
		<!-- 기본 사이드바 (항상 표시) -->
		<div class="flex flex-col w-[100px] h-full p-4 space-y-3 bg-slate-800/80 backdrop-blur-xl border-r border-slate-600/40 shadow-2xl shadow-black/30 transition-all duration-200 {isExpanded ? 'opacity-40 scale-95' : 'opacity-100 scale-100'}">
			<!-- 로고 영역 -->
			<div class="flex items-center justify-center mb-6 p-2">
				<div class="relative group">
					<div class="flex items-center justify-center w-12 h-12 bg-gradient-to-r from-blue-500 via-purple-500 to-teal-500 rounded-2xl shadow-2xl shadow-blue-500/40 transform rotate-3 transition-transform duration-200 group-hover:rotate-6 group-hover:scale-110">
						<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
						</svg>
					</div>
					<div class="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full animate-pulse shadow-lg shadow-emerald-400/50"></div>
				</div>
			</div>

			<!-- 네비게이션 메뉴 -->
			<nav class="flex-1 space-y-2">
				{#each navigationItems as item}
					<button 
						class="nav-button w-full flex items-center justify-center p-4 rounded-2xl transition-all duration-200 overflow-hidden {$page.url.pathname === item.path ? 'bg-gradient-to-r ' + item.gradient + ' text-white shadow-2xl shadow-' + item.gradient.split(' ')[1].replace('to-', '').replace('-600', '-500') + '/40 transform scale-105' : 'text-slate-200 hover:bg-slate-700/60 hover:shadow-lg hover:shadow-black/20'} {isExpanded ? 'pointer-events-none' : ''}"
						on:click={() => !isExpanded && goto(`${base}${item.path}`)}
					>
						<!-- 활성 상태 배경 효과 -->
						{#if $page.url.pathname !== item.path}
							<div class="absolute inset-0 bg-gradient-to-r {item.gradient} opacity-0 hover:opacity-15 transition-opacity duration-200 rounded-2xl"></div>
						{/if}
						
						<!-- 아이콘 -->
						<div class="relative z-10 flex items-center justify-center w-8 h-8 rounded-xl transition-all duration-200 hover:scale-110">
							<svg class="w-6 h-6 {$page.url.pathname === item.path ? 'text-white drop-shadow-lg' : 'text-slate-200 hover:text-white'} transition-colors duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="{item.icon}"></path>
							</svg>
						</div>
						
						<!-- 활성 상태 인디케이터 -->
						{#if $page.url.pathname === item.path}
							<div class="absolute -right-1 top-1/2 -translate-y-1/2 w-1 h-8 bg-white rounded-full shadow-lg shadow-white/50"></div>
						{/if}
					</button>
				{/each}
			</nav>

			<!-- 하단 시스템 상태 -->
			<div class="mt-auto pt-4 border-t border-slate-600/40">
				<div class="flex items-center justify-center p-3 bg-gradient-to-r from-slate-700/80 to-slate-600/80 backdrop-blur-sm rounded-2xl border border-slate-500/30 shadow-lg transition-all duration-200 hover:shadow-xl hover:shadow-emerald-500/20">
					<div class="w-6 h-6 bg-gradient-to-r from-emerald-400 to-teal-400 rounded-lg flex items-center justify-center shadow-lg shadow-emerald-400/30">
						<svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
						</svg>
					</div>
				</div>
			</div>
		</div>

		<!-- 확장된 사이드바 (호버 시 표시) -->
		<div class="expanded-sidebar absolute top-0 left-0 h-full bg-slate-800/95 backdrop-blur-xl border-r border-slate-600/40 shadow-2xl shadow-black/40 transition-all duration-300 ease-in-out {isExpanded ? 'w-[280px] opacity-100 translate-x-0 pointer-events-auto' : 'w-[100px] opacity-0 -translate-x-4 pointer-events-none'}">
			<!-- 로고 영역 -->
			<div class="flex items-center space-x-4 mb-8 p-6">
				<div class="relative">
					<div class="flex items-center justify-center w-12 h-12 bg-gradient-to-r from-blue-500 via-purple-500 to-teal-500 rounded-2xl shadow-2xl shadow-blue-500/40 transform rotate-3">
						<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
						</svg>
					</div>
					<div class="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full animate-pulse shadow-lg shadow-emerald-400/50"></div>
				</div>
				<div class="transition-all duration-200 {isExpanded ? 'opacity-100 translate-x-0 delay-100' : 'opacity-0 translate-x-4'}">
					<h1 class="text-xl font-black bg-gradient-to-r from-white via-blue-200 to-purple-200 bg-clip-text text-transparent tracking-tight">
						Finance
					</h1>
					<p class="text-sm text-slate-300 font-medium">Dashboard</p>
				</div>
			</div>

			<!-- 확장된 네비게이션 메뉴 -->
			<nav class="flex-1 space-y-2 px-4">
				{#each navigationItems as item, index}
					<button 
						class="w-full flex items-center space-x-4 px-4 py-4 rounded-2xl transition-all duration-200 overflow-hidden {$page.url.pathname === item.path ? 'bg-gradient-to-r ' + item.gradient + ' text-white shadow-2xl shadow-' + item.gradient.split(' ')[1].replace('to-', '').replace('-600', '-500') + '/40' : 'text-slate-200 hover:bg-slate-700/60 hover:shadow-lg hover:shadow-black/20'} {isExpanded ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-4'}"
						style="transition-delay: {isExpanded ? Math.min(index * 30 + 100, 250) : 0}ms"
						on:click={() => goto(`${base}${item.path}`)}
					>
						<!-- 활성 상태 배경 효과 -->
						{#if $page.url.pathname !== item.path}
							<div class="absolute inset-0 bg-gradient-to-r {item.gradient} opacity-0 hover:opacity-15 transition-opacity duration-200 rounded-2xl"></div>
						{/if}
						
						<!-- 아이콘 -->
						<div class="relative z-10 flex items-center justify-center w-10 h-10 rounded-xl {$page.url.pathname === item.path ? 'bg-white/20 shadow-lg shadow-white/20' : 'bg-slate-700/80 hover:bg-slate-600/80'} transition-all duration-200">
							<svg class="w-5 h-5 {$page.url.pathname === item.path ? 'text-white drop-shadow-lg' : 'text-slate-200 hover:text-white'} transition-colors duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="{item.icon}"></path>
							</svg>
						</div>
						
						<!-- 텍스트 -->
						<div class="relative z-10 transition-all duration-200 {isExpanded ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-4'}">
							<span class="font-bold text-sm tracking-wide {$page.url.pathname === item.path ? 'text-white drop-shadow-sm' : 'text-slate-200 hover:text-white'} transition-colors duration-200">
								{item.label}
							</span>
							<p class="text-xs {$page.url.pathname === item.path ? 'text-white/90' : 'text-slate-400 hover:text-slate-300'} mt-0.5 transition-colors duration-200">
								{item.description}
							</p>
						</div>
						
						<!-- 활성 상태 인디케이터 -->
						{#if $page.url.pathname === item.path}
							<div class="absolute right-4 w-2 h-2 bg-white rounded-full animate-pulse shadow-lg shadow-white/50"></div>
						{/if}
					</button>
				{/each}
			</nav>

			<!-- 확장된 하단 정보 -->
			<div class="mt-auto pt-6 border-t border-slate-600/40 p-4">
				<div class="bg-gradient-to-r from-slate-700/80 to-slate-600/80 backdrop-blur-sm rounded-2xl p-4 border border-slate-500/30 shadow-lg hover:shadow-emerald-500/20 transition-all duration-200 {isExpanded ? 'opacity-100 translate-x-0 delay-150' : 'opacity-0 translate-x-4'}">
					<div class="flex items-center space-x-3">
						<div class="w-8 h-8 bg-gradient-to-r from-emerald-400 to-teal-400 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-400/30">
							<svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
							</svg>
						</div>
						<div class="transition-all duration-200 {isExpanded ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-4'}">
							<p class="text-sm font-bold text-slate-100">System Status</p>
							<p class="text-xs text-emerald-300 font-medium flex items-center mt-1">
								<span class="w-2 h-2 bg-emerald-400 rounded-full mr-2 animate-pulse shadow-sm shadow-emerald-400/50"></span>
								All systems operational
							</p>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- 메인 컨텐츠 영역 -->
	<div class="flex w-[calc(100%_-_100px)] h-full">
		<slot />
	</div>
</div>

<style>
	/* 사이드바 컨테이너 */
	.sidebar-container {
		position: relative;
		width: 100px;
		flex-shrink: 0;
	}

	/* 확장된 사이드바 */
	.expanded-sidebar {
		z-index: 50;
		transform-origin: left center;
	}

	/* 기본 사이드바가 비활성화될 때 시각적 피드백 */
	.sidebar-container > div:first-child.pointer-events-none {
		opacity: 0.3;
		transition: opacity 0.3s ease-out;
	}

	/* 네비게이션 버튼 애니메이션 */
	.nav-button {
		position: relative;
		will-change: transform;
		backface-visibility: hidden;
		transform-origin: center;
		outline: none; /* 클릭 시 흰색 테두리 제거 */
	}
	
	.nav-button:focus {
		outline: none; /* focus 시에도 테두리 제거 */
		box-shadow: none; /* focus 시 박스 섀도우도 제거 */
	}
	
	.nav-button::before {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, 
			transparent, 
			rgba(255, 255, 255, 0.1), 
			transparent
		);
		transition: left 0.5s ease-out;
		border-radius: 16px;
	}
	
	.nav-button:hover:not(.pointer-events-none)::before {
		left: 100%;
	}

	/* 부드러운 전환을 위한 추가 스타일 */
	.sidebar-container * {
		transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
	}

	/* 확장된 사이드바 내부 요소들의 스태거 애니메이션 */
	.expanded-sidebar nav button {
		transform: translateX(0);
		opacity: 1;
		outline: none; /* 클릭 시 흰색 테두리 제거 */
	}

	.expanded-sidebar nav button:focus {
		outline: none; /* focus 시에도 테두리 제거 */
		box-shadow: none; /* focus 시 박스 섀도우도 제거 */
	}

	.expanded-sidebar:not(.opacity-100) nav button {
		transform: translateX(16px);
		opacity: 0;
	}

	/* 현대적인 애니메이션 */
	:global(.animate-pulse) {
		animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
	}
	
	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	/* 글래스모피즘 효과 강화 */
	:global(.backdrop-blur-xl) {
		backdrop-filter: blur(24px) saturate(180%);
		-webkit-backdrop-filter: blur(24px) saturate(180%);
	}

	/* 어두운 테마 스크롤바 */
	:global(::-webkit-scrollbar) {
		width: 6px;
	}

	:global(::-webkit-scrollbar-track) {
		background: rgba(0, 0, 0, 0.2);
		border-radius: 10px;
	}

	:global(::-webkit-scrollbar-thumb) {
		background: linear-gradient(45deg, rgba(75, 85, 99, 0.6), rgba(107, 114, 128, 0.6));
		border-radius: 10px;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	:global(::-webkit-scrollbar-thumb:hover) {
		background: linear-gradient(45deg, rgba(75, 85, 99, 0.8), rgba(107, 114, 128, 0.8));
	}

	/* 반응형 디자인 */
	@media (max-width: 768px) {
		.sidebar-container {
			width: 80px;
		}
		
		.expanded-sidebar {
			width: 240px !important;
		}
	}
</style>