<script lang="ts">
	import '../app.css';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { page } from "$app/stores";
	import { auth } from '$lib/stores/auth';
	import { Toaster } from 'svelte-french-toast';
	import { toast } from 'svelte-french-toast';
	import { onMount, onDestroy } from 'svelte';

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
			icon: 'M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z',
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
			label: 'RESEARCH', 
			icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
			gradient: 'from-orange-500 to-red-600',
			description: '투자 리서치'
		},
		{ 
			path: '/news', 
			label: 'NEWS', 
			icon: 'M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z',
			gradient: 'from-cyan-500 to-blue-600',
			description: '실시간 뉴스'
		},
		{ 
			path: '/calendar', 
			label: 'F_CALENDAR', 
			icon: 'M8 7V3m8 4V3M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
			gradient: 'from-indigo-500 to-blue-600',
			description: '경제 달력'
		},
		{ 
			path: '/stockCalendar', 
			label: 'S_CALENDAR', 
			icon: 'M8 7V3m8 4V3M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
			gradient: 'from-orange-500 to-red-600',
			description: '주식 달력'
		},
		{ 
			path: '/invest', 
			label: 'INVEST', 
			icon: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1',
			gradient: 'from-green-500 to-emerald-600',
			description: '모의 투자'
		},
		{ 
			path: '/timeLine', 
			label: 'PORTFOLIO', 
			icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10',
			gradient: 'from-violet-500 to-purple-600',
			description: '포트폴리오 관리'
		}
	];

	// 로그인 상태 관리
	let isAuthenticated = false;
	let currentUser: any = null;

	// 사이드바 확장 상태
	let isExpanded = false;
	let expandTimeout: NodeJS.Timeout | null = null;
	let collapseTimeout: NodeJS.Timeout | null = null;
	let isHovering = false; // 실제 마우스 호버 상태 추적
	let forceCloseTimeout: NodeJS.Timeout | null = null; // 강제 닫기 타이머

	// 마우스 위치 추적을 위한 변수
	let mouseX = 0;
	let mouseY = 0;
	let sidebarElement: HTMLDivElement;

	// 로그아웃 처리 함수
	const handleLogout = () => {
		auth.logout();
		toast.success('로그아웃되었습니다.');
		goto(`${base}/login`);
	};

	// 마우스 위치 업데이트 함수
	const updateMousePosition = (event: MouseEvent) => {
		mouseX = event.clientX;
		mouseY = event.clientY;
		
		// 사이드바 영역 밖에 있으면 강제로 닫기
		if (sidebarElement && isExpanded) {
			try {
				const rect = sidebarElement.getBoundingClientRect();
				// 확장된 상태일 때는 280px 너비를 고려
				const expandedWidth = 280;
				const isOutside = mouseX < rect.left || mouseX > rect.left + expandedWidth || mouseY < rect.top || mouseY > rect.bottom;
				
				if (isOutside) {
					// 마우스가 확장된 사이드바 영역을 완전히 벗어났으면 즉시 닫기
					clearAllTimeouts();
					isHovering = false;
					isExpanded = false;
				}
			} catch (error) {
				// DOM 요소에 접근할 수 없는 경우 안전하게 처리
				console.warn('Sidebar element access error:', error);
			}
		}
	};

	// 모든 타이머 정리 함수
	const clearAllTimeouts = () => {
		try {
			if (expandTimeout) {
				clearTimeout(expandTimeout);
				expandTimeout = null;
			}
			if (collapseTimeout) {
				clearTimeout(collapseTimeout);
				collapseTimeout = null;
			}
			if (forceCloseTimeout) {
				clearTimeout(forceCloseTimeout);
				forceCloseTimeout = null;
			}
		} catch (error) {
			console.warn('Timer cleanup error:', error);
		}
	};

	// 사이드바 확장 함수 (지연 시간 포함)
	const handleMouseEnter = () => {
		if (!isAuthenticated) return; // 로그인되지 않으면 확장하지 않음
		
		try {
			isHovering = true;
			
			// 모든 타이머 정리
			clearAllTimeouts();
			
			// 이미 확장된 상태라면 즉시 반환
			if (isExpanded) {
				return;
			}
			
			// 짧은 지연 후 확장
			expandTimeout = setTimeout(() => {
				if (isHovering) {
					isExpanded = true;
					
					// 안전장치: 3초 후 강제로 닫기 (비정상적인 상황 방지)
					forceCloseTimeout = setTimeout(() => {
						if (isExpanded && !isHovering) {
							isExpanded = false;
						}
					}, 3000);
				}
				expandTimeout = null;
			}, 100);
		} catch (error) {
			console.warn('Mouse enter handler error:', error);
		}
	};

	// 사이드바 축소 함수 (지연 시간 포함)
	const handleMouseLeave = () => {
		try {
			isHovering = false;
			
			// 확장 타이머 즉시 취소
			if (expandTimeout) {
				clearTimeout(expandTimeout);
				expandTimeout = null;
			}
			
			// 강제 닫기 타이머 취소
			if (forceCloseTimeout) {
				clearTimeout(forceCloseTimeout);
				forceCloseTimeout = null;
			}
			
			// 축소 타이머 설정
			if (collapseTimeout) {
				clearTimeout(collapseTimeout);
			}
			
			collapseTimeout = setTimeout(() => {
				if (!isHovering) {
					isExpanded = false;
				}
				collapseTimeout = null;
			}, 150);
		} catch (error) {
			console.warn('Mouse leave handler error:', error);
		}
	};

	// 이벤트 리스너 추가 여부 추적
	let listenersAdded = false;

	// 컴포넌트 마운트 시 전역 마우스 이벤트 리스너 추가
	onMount(() => {
		try {
			// auth store 초기화
			auth.initialize();

			// 로그인 상태 구독
			const unsubscribe = auth.subscribe((authState) => {
				isAuthenticated = authState.isAuthenticated;
				currentUser = authState.user;
			});

			if (!listenersAdded) {
				document.addEventListener('mousemove', updateMousePosition);
				
				// 페이지를 벗어날 때 사이드바 닫기
				document.addEventListener('mouseleave', () => {
					clearAllTimeouts();
					isHovering = false;
					isExpanded = false;
				});
				
				listenersAdded = true;
			}

			return unsubscribe;
		} catch (error) {
			console.error('Event listener setup error:', error);
		}
	});

	onDestroy(() => {
		try {
			if (listenersAdded) {
				document.removeEventListener('mousemove', updateMousePosition);
				listenersAdded = false;
			}
			clearAllTimeouts();
		} catch (error) {
			console.warn('Cleanup error:', error);
		}
	});
</script>

<Toaster gutter={toastGutter} reverseOrder={toastReverseOrder} position={toastPosition} {toastOptions} />

<div class="flex flex-row w-screen h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-900 relative overflow-hidden">
	<!-- 배경 데코레이션 -->
	<div class="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,_rgba(59,130,246,0.1)_1px,_transparent_0)] bg-[size:32px_32px] pointer-events-none"></div>
	<div class="absolute top-0 left-0 w-96 h-96 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2 animate-pulse"></div>
	<div class="absolute bottom-0 right-0 w-96 h-96 bg-gradient-to-r from-cyan-500/20 to-teal-500/20 rounded-full blur-3xl translate-x-1/2 translate-y-1/2 animate-pulse"></div>
	<div class="absolute top-1/2 left-1/2 w-64 h-64 bg-gradient-to-r from-violet-500/15 to-pink-500/15 rounded-full blur-2xl -translate-x-1/2 -translate-y-1/2"></div>
	
	<!-- 로그인된 사용자에게 사이드바 표시 (단, 로그인 페이지가 아닐 때만) -->
	{#if isAuthenticated && !$page.url.pathname.includes('/login')}
	<!-- 확장 가능한 사이드바 -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div 
		bind:this={sidebarElement}
		class="sidebar-container relative z-30"
		on:mouseenter={handleMouseEnter}
		on:mouseleave={handleMouseLeave}
	>
		<!-- 기본 사이드바 (항상 표시) -->
		<div class="flex flex-col w-[100px] h-full p-4 space-y-3 bg-slate-800/80 backdrop-blur-xl border-r border-slate-600/40 shadow-2xl shadow-black/30 transition-all duration-200 {isExpanded ? 'opacity-40 scale-95' : 'opacity-100 scale-100'}">
			<!-- 로고 영역 -->
			<div class="flex items-center justify-center mb-6 p-2">
				<div class="relative group">
					<div class="flex items-center justify-center w-12 h-12 bg-gradient-to-r from-blue-500 via-purple-500 to-teal-500 rounded-2xl shadow-2xl shadow-blue-500/40 transform rotate-3 transition-transform duration-200 group-hover:rotate-6 group-hover:scale-110">
						<!-- 금융 차트 로고 SVG -->
						<svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<!-- 상승 트렌드 라인 -->
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M3 17l4-4 4 4 6-6 4 4"></path>
							<!-- 데이터 포인트들 -->
							<circle cx="3" cy="17" r="1.5" fill="currentColor" opacity="0.8"></circle>
							<circle cx="7" cy="13" r="1.5" fill="currentColor" opacity="0.9"></circle>
							<circle cx="11" cy="17" r="1.5" fill="currentColor" opacity="0.8"></circle>
							<circle cx="17" cy="11" r="1.5" fill="currentColor"></circle>
							<circle cx="21" cy="15" r="1.5" fill="currentColor" opacity="0.9"></circle>
							<!-- 상승 화살표 -->
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 7l4 0 0 4" opacity="0.7"></path>
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 7l-4 4" opacity="0.7"></path>
						</svg>
					</div>
					<!-- 활성 상태 인디케이터 -->
					<div class="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full animate-pulse shadow-lg shadow-emerald-400/50"></div>
					<!-- 추가 데코레이션 -->
					<div class="absolute -bottom-1 -left-1 w-2 h-2 bg-blue-400 rounded-full opacity-60 animate-pulse" style="animation-delay: 0.5s;"></div>
				</div>
			</div>

			<!-- 네비게이션 메뉴 -->
			<nav class="flex-1 space-y-2 overflow-y-auto overflow-x-hidden max-h-[calc(100vh-280px)] scrollbar-thin">
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
							<!-- 달력 아이콘에 글자 추가 -->
							{#if item.path === '/calendar'}
								<div class="absolute inset-0 flex items-center justify-center">
									<span class="text-xs font-black {$page.url.pathname === item.path ? 'text-white drop-shadow-lg' : 'text-slate-200 hover:text-white'} transition-colors duration-200" style="margin-top: 2px;">F</span>
								</div>
							{:else if item.path === '/stockCalendar'}
								<div class="absolute inset-0 flex items-center justify-center">
									<span class="text-xs font-black {$page.url.pathname === item.path ? 'text-white drop-shadow-lg' : 'text-slate-200 hover:text-white'} transition-colors duration-200" style="margin-top: 2px;">S</span>
								</div>
							{/if}
						</div>
						
						<!-- 활성 상태 인디케이터 -->
						{#if $page.url.pathname === item.path}
							<div class="absolute -right-1 top-1/2 -translate-y-1/2 w-1 h-8 bg-white rounded-full shadow-lg shadow-white/50"></div>
						{/if}
					</button>
				{/each}
			</nav>

			<!-- 하단 로그아웃 버튼 -->
			<div class="mt-auto pt-4 border-t border-slate-600/40">
				<button 
					class="w-full flex items-center justify-center p-3 bg-gradient-to-r from-red-500/80 to-red-600/80 hover:from-red-500 hover:to-red-600 rounded-2xl border border-red-500/30 shadow-lg transition-all duration-200 hover:shadow-xl hover:shadow-red-500/20 hover:scale-105"
					on:click={handleLogout}
				>
					<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
					</svg>
				</button>
			</div>
		</div>

		<!-- 확장된 사이드바 (호버 시 표시) -->
		<div class="expanded-sidebar absolute top-0 left-0 h-full bg-slate-800/95 backdrop-blur-xl border-r border-slate-600/40 shadow-2xl shadow-black/40 transition-all duration-300 ease-in-out {isExpanded ? 'w-[280px] opacity-100 translate-x-0 pointer-events-auto' : 'w-[100px] opacity-0 -translate-x-4 pointer-events-none'}">
			<!-- 로고 영역 -->
			<div class="flex items-center space-x-4 mb-8 p-6">
				<div class="relative">
					<div class="flex items-center justify-center w-12 h-12 bg-gradient-to-r from-blue-500 via-purple-500 to-teal-500 rounded-2xl shadow-2xl shadow-blue-500/40 transform rotate-3">
						<!-- 금융 차트 로고 SVG -->
						<svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<!-- 상승 트렌드 라인 -->
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M3 17l4-4 4 4 6-6 4 4"></path>
							<!-- 데이터 포인트들 -->
							<circle cx="3" cy="17" r="1.5" fill="currentColor" opacity="0.8"></circle>
							<circle cx="7" cy="13" r="1.5" fill="currentColor" opacity="0.9"></circle>
							<circle cx="11" cy="17" r="1.5" fill="currentColor" opacity="0.8"></circle>
							<circle cx="17" cy="11" r="1.5" fill="currentColor"></circle>
							<circle cx="21" cy="15" r="1.5" fill="currentColor" opacity="0.9"></circle>
							<!-- 상승 화살표 -->
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 7l4 0 0 4" opacity="0.7"></path>
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 7l-4 4" opacity="0.7"></path>
						</svg>
					</div>
					<!-- 활성 상태 인디케이터 -->
					<div class="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full animate-pulse shadow-lg shadow-emerald-400/50"></div>
					<!-- 추가 데코레이션 -->
					<div class="absolute -bottom-1 -left-1 w-2 h-2 bg-blue-400 rounded-full opacity-60 animate-pulse" style="animation-delay: 0.5s;"></div>
				</div>
				<div class="transition-all duration-200 {isExpanded ? 'opacity-100 translate-x-0 delay-100' : 'opacity-0 translate-x-4'}">
					<h1 class="text-xl font-black bg-gradient-to-r from-white via-blue-200 to-purple-200 bg-clip-text text-transparent tracking-tight">
						FinanceChart
					</h1>
					<p class="text-sm text-slate-300 font-medium">Analytics Dashboard</p>
				</div>
			</div>

			<!-- 사용자 정보 -->
			{#if currentUser}
			<div class="px-6 mb-6">
				<div class="bg-gradient-to-r from-slate-700/80 to-slate-600/80 backdrop-blur-sm rounded-2xl p-4 border border-slate-500/30 shadow-lg transition-all duration-200 {isExpanded ? 'opacity-100 translate-x-0 delay-100' : 'opacity-0 translate-x-4'}">
					<div class="flex items-center space-x-3">
						<div class="w-10 h-10 bg-gradient-to-r from-blue-400 to-purple-500 rounded-xl flex items-center justify-center shadow-lg shadow-blue-400/30">
							<span class="text-white font-bold text-sm">{currentUser.name?.charAt(0).toUpperCase() || 'U'}</span>
						</div>
						<div class="flex-1 min-w-0">
							<p class="text-sm font-bold text-slate-100 truncate">{currentUser.name || '사용자'}</p>
							<p class="text-xs text-slate-300 truncate">{currentUser.username || ''}</p>
						</div>
					</div>
				</div>
			</div>
			{/if}

			<!-- 확장된 네비게이션 메뉴 -->
			<nav class="flex-1 space-y-2 px-4 overflow-y-auto overflow-x-hidden max-h-[calc(100vh-380px)] scrollbar-thin">
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
							<!-- 달력 아이콘에 글자 추가 -->
							{#if item.path === '/calendar'}
								<div class="absolute inset-0 flex items-center justify-center">
									<span class="text-sm font-black {$page.url.pathname === item.path ? 'text-white drop-shadow-lg' : 'text-slate-200 hover:text-white'} transition-colors duration-200" style="margin-top: 2px;">F</span>
								</div>
							{:else if item.path === '/stockCalendar'}
								<div class="absolute inset-0 flex items-center justify-center">
									<span class="text-sm font-black {$page.url.pathname === item.path ? 'text-white drop-shadow-lg' : 'text-slate-200 hover:text-white'} transition-colors duration-200" style="margin-top: 2px;">S</span>
								</div>
							{/if}
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

			<!-- 확장된 로그아웃 버튼 -->
			<div class="mt-auto pt-6 border-t border-slate-600/40 p-4">
				<button 
					class="w-full flex items-center space-x-3 px-4 py-3 bg-gradient-to-r from-red-500/80 to-red-600/80 hover:from-red-500 hover:to-red-600 rounded-2xl border border-red-500/30 shadow-lg transition-all duration-200 hover:shadow-xl hover:shadow-red-500/20 hover:scale-105 {isExpanded ? 'opacity-100 translate-x-0 delay-150' : 'opacity-0 translate-x-4'}"
					on:click={handleLogout}
				>
					<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
					</svg>
					<span class="text-white font-medium">로그아웃</span>
				</button>
			</div>
		</div>
	</div>
	{/if}

	<!-- 메인 컨텐츠 영역 -->
	<div class="flex {isAuthenticated && !$page.url.pathname.includes('/login') ? 'w-[calc(100%_-_100px)]' : 'w-full'} h-full">
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
		z-index: 40;
		transform-origin: left center;
	}

	/* 기본 사이드바가 비활성화될 때 시각적 피드백 */
	.sidebar-container > div:first-child.pointer-events-none {
		opacity: 0.3;
		transition: opacity 0.1s ease-out;
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
		transition: left 0.1s ease-out;
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

	/* 네비게이션 전용 얇은 스크롤바 */
	:global(.scrollbar-thin::-webkit-scrollbar) {
		width: 4px;
	}

	:global(.scrollbar-thin::-webkit-scrollbar-track) {
		background: rgba(0, 0, 0, 0.1);
		border-radius: 8px;
		margin: 4px 0;
	}

	:global(.scrollbar-thin::-webkit-scrollbar-thumb) {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.4), rgba(139, 92, 246, 0.4));
		border-radius: 8px;
		border: none;
		transition: all 0.2s ease;
	}

	:global(.scrollbar-thin::-webkit-scrollbar-thumb:hover) {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.6), rgba(139, 92, 246, 0.6));
		box-shadow: 0 0 8px rgba(59, 130, 246, 0.3);
	}

	/* Firefox 스크롤바 스타일링 */
	:global(.scrollbar-thin) {
		scrollbar-width: thin;
		scrollbar-color: rgba(59, 130, 246, 0.4) rgba(0, 0, 0, 0.1);
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