<script lang="ts">
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { auth } from '$lib/stores/auth';
	import { toast } from 'svelte-french-toast';
	import { onMount, onDestroy } from 'svelte';
	import { loginUser } from '$lib/api-connector/FinanceApi';

	let username = '';
	let password = '';
	let isLoading = false;
	let isRedirecting = false;
	let showPassword = false;
	let cancelController: AbortController;

	// 컴포넌트 마운트 시 이미 로그인되어 있으면 홈으로 이동
	onMount(() => {
		const unsubscribe = auth.subscribe((authState) => {
			if (authState.isAuthenticated) {
				goto(`${base}/`);
			}
		});

		// auth store 초기화
		auth.initialize();

		// AbortController 초기화
		cancelController = new AbortController();

		return unsubscribe;
	});

	// 컴포넌트 언마운트 시 진행 중인 요청 취소
	onDestroy(() => {
		if (cancelController) {
			cancelController.abort();
		}
	});

	// 로그인 처리 함수
	const handleLogin = async (e: Event) => {
		e.preventDefault();
		
		if (!username || !password) {
			toast.error('아이디와 비밀번호를 입력해주세요.');
			return;
		}

		isLoading = true;

		try {
			// FinanceApi의 loginUser 함수 사용
			const response = await loginUser({
				username: username,
				password: password
			}, cancelController);
			
			if (response.success) {
				// 로그인 성공
				const user = {
					id: response.user.id,
					email: response.user.email,
					name: response.user.name,
					username: response.user.username
				};

				// 간단한 토큰 생성 (실제로는 서버에서 받아야 하지만 여기서는 간단히)
				const token = 'simple-token-' + Date.now();
				auth.login(user, token);
				
				// 화면 전환 상태로 변경
				isLoading = false;
				isRedirecting = true;
				
				// 홈으로 이동 (더 빠른 전환으로 깜빡임 방지)
				setTimeout(() => {
          toast.success(response.message);
          
					goto(`${base}/`);
				}, 300); // 1초에서 300ms로 단축
			} else {
				// 로그인 실패
				if (response.message === 'fail-network') {
					toast.error('서버에 연결할 수 없습니다. 서버가 실행되어 있는지 확인해주세요.');
				} else {
					toast.error(response.message);
				}
				isLoading = false;
			}
			
		} catch (error: any) {
			console.error('Login error:', error);
			if (error.name === 'AbortError') {
				// 요청이 취소된 경우 에러 메시지 표시하지 않음
				return;
			}
			toast.error('로그인에 실패했습니다. 네트워크 연결을 확인해주세요.');
			isLoading = false;
		}
	};

	// 데모 계정으로 로그인
	const loginWithDemo = () => {
		username = 'jukim';
		password = 'jukim123$';
		setTimeout(() => {
			const form = document.querySelector('form');
			if (form) {
				form.dispatchEvent(new Event('submit', { cancelable: true }));
			}
		}, 100);
	};
</script>

<svelte:head>
	<title>로그인 - FinanceChart</title>
</svelte:head>

<div class="min-h-screen w-full bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-900 relative overflow-hidden flex items-center justify-center">
	<!-- 기본 배경 데코레이션 -->
	<div class="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,_rgba(59,130,246,0.1)_1px,_transparent_0)] bg-[size:32px_32px] pointer-events-none"></div>
	<div class="absolute top-0 left-0 w-96 h-96 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2 animate-pulse"></div>
	<div class="absolute bottom-0 right-0 w-96 h-96 bg-gradient-to-r from-cyan-500/20 to-teal-500/20 rounded-full blur-3xl translate-x-1/2 translate-y-1/2 animate-pulse"></div>
	<div class="absolute top-1/2 left-1/2 w-64 h-64 bg-gradient-to-r from-violet-500/15 to-pink-500/15 rounded-full blur-2xl -translate-x-1/2 -translate-y-1/2"></div>

	<!-- 움직이는 주식 차트 라인들 -->
	<svg class="absolute inset-0 w-full h-full pointer-events-none opacity-20" xmlns="http://www.w3.org/2000/svg">
		<!-- 주요 상승 트렌드 라인 1 -->
		<path class="chart-line-1" stroke="url(#gradient1)" stroke-width="2" fill="none" opacity="0.8"
			d="M-100,400 Q200,350 400,300 T800,250 L1200,200 L1600,150">
			<animate attributeName="d" 
				values="M-100,400 Q200,350 400,300 T800,250 L1200,200 L1600,150;
						M-100,420 Q200,360 400,290 T800,240 L1200,190 L1600,140;
						M-100,400 Q200,350 400,300 T800,250 L1200,200 L1600,150"
				dur="8s" repeatCount="indefinite"/>
		</path>
		
		<!-- 주요 상승 트렌드 라인 2 -->
		<path class="chart-line-2" stroke="url(#gradient2)" stroke-width="2" fill="none" opacity="0.6"
			d="M-100,500 Q300,450 500,400 T900,350 L1300,300 L1700,250">
			<animate attributeName="d" 
				values="M-100,500 Q300,450 500,400 T900,350 L1300,300 L1700,250;
						M-100,520 Q300,460 500,390 T900,340 L1300,290 L1700,240;
						M-100,500 Q300,450 500,400 T900,350 L1300,300 L1700,250"
				dur="12s" repeatCount="indefinite"/>
		</path>

		<!-- 보조 트렌드 라인들 -->
		<path class="chart-line-3" stroke="url(#gradient3)" stroke-width="1.5" fill="none" opacity="0.4"
			d="M-100,600 L200,580 L400,560 L600,540 L800,520 L1000,500 L1200,480 L1400,460 L1600,440">
			<animate attributeName="d" 
				values="M-100,600 L200,580 L400,560 L600,540 L800,520 L1000,500 L1200,480 L1400,460 L1600,440;
						M-100,610 L200,585 L400,550 L600,535 L800,515 L1000,495 L1200,475 L1400,455 L1600,435;
						M-100,600 L200,580 L400,560 L600,540 L800,520 L1000,500 L1200,480 L1400,460 L1600,440"
				dur="10s" repeatCount="indefinite"/>
		</path>

		<!-- 그라디언트 정의 -->
		<defs>
			<linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="0%">
				<stop offset="0%" style="stop-color:#3b82f6;stop-opacity:1" />
				<stop offset="50%" style="stop-color:#8b5cf6;stop-opacity:1" />
				<stop offset="100%" style="stop-color:#06b6d4;stop-opacity:1" />
			</linearGradient>
			<linearGradient id="gradient2" x1="0%" y1="0%" x2="100%" y2="0%">
				<stop offset="0%" style="stop-color:#10b981;stop-opacity:1" />
				<stop offset="50%" style="stop-color:#3b82f6;stop-opacity:1" />
				<stop offset="100%" style="stop-color:#8b5cf6;stop-opacity:1" />
			</linearGradient>
			<linearGradient id="gradient3" x1="0%" y1="0%" x2="100%" y2="0%">
				<stop offset="0%" style="stop-color:#f59e0b;stop-opacity:1" />
				<stop offset="100%" style="stop-color:#ef4444;stop-opacity:1" />
			</linearGradient>
		</defs>
	</svg>

	<!-- 떠다니는 금융 종목/지표들 -->
	<div class="absolute inset-0 pointer-events-none overflow-hidden">
		{#each [
			{name: 'Apple', iconColor: '#000000', color: 'text-blue-400'},
			{name: 'Tesla', iconColor: '#CC0000', color: 'text-emerald-400'},
			{name: 'Bitcoin', iconColor: '#F7931E', color: 'text-orange-400'},
			{name: 'S&P 500', iconColor: '#8B5CF6', color: 'text-purple-400'},
			{name: 'Gold', iconColor: '#FFD700', color: 'text-yellow-400'},
			{name: 'Microsoft', iconColor: '#5C2D91', color: 'text-indigo-400'},
			{name: 'NVIDIA', iconColor: '#76B900', color: 'text-cyan-400'},
			{name: 'Google', iconColor: '#4285F4', color: 'text-green-400'},
			{name: 'Samsung', iconColor: '#1428A0', color: 'text-indigo-400'},
			{name: 'AMD', iconColor: '#ED1C24', color: 'text-pink-400'},
			{name: 'Netflix', iconColor: '#E50914', color: 'text-red-400'},
			{name: 'Meta', iconColor: '#1877F2', color: 'text-blue-400'},
			{name: 'PayPal', iconColor: '#00457C', color: 'text-cyan-400'},
			{name: 'Shopify', iconColor: '#7AB55C', color: 'text-green-400'},
			{name: 'Intel', iconColor: '#0071C5', color: 'text-blue-400'},
			{name: 'Oracle', iconColor: '#F80000', color: 'text-red-400'},
			{name: 'Salesforce', iconColor: '#00A1E0', color: 'text-sky-400'},
			{name: 'Ethereum', iconColor: '#627EEA', color: 'text-indigo-400'},
			{name: 'Zoom', iconColor: '#2D8CFF', color: 'text-blue-400'},
			{name: 'Twitter', iconColor: '#1DA1F2', color: 'text-sky-400'}
		] as item, i}
			<div class="floating-financial-item absolute text-lg font-bold opacity-30 {item.color} flex items-center gap-2"
				style="left: {(i * 8 + 5) % 95}%; top: {(i * 12 + 15) % 75}%; animation-delay: {i * 0.6}s;">
				<div class="w-5 h-5 flex items-center justify-center">
					{#if item.name === 'Apple'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701"/>
						</svg>
					{:else if item.name === 'Tesla'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="m12 5.362-2.475-.308c-.738-.092-1.344-.145-1.344-.145s.737 3.476 3.819 3.476c3.083 0 3.819-3.476 3.819-3.476s-.606.053-1.344.145zm7.415.323c-.738-.074-1.605-.11-2.493-.11-1.374 0-2.878.11-4.922.11-2.045 0-3.548-.11-4.922-.11-.888 0-1.755.036-2.493.11C2.48 6.019.75 8.962.75 8.962s.951 1.83 2.585 1.83c1.634 0 3.819-.184 3.819-.184s-.328 5.895-.328 8.027c0 .737.184 1.105.184 1.105h1.474s.184-.368.184-1.105c0-2.132-.328-8.027-.328-8.027s2.185.184 3.819.184c1.634 0 3.819-.184 3.819-.184s-.328 5.895-.328 8.027c0 .737.184 1.105.184 1.105h1.474s.184-.368.184-1.105c0-2.132-.328-8.027-.328-8.027s2.185.184 3.819.184c1.634 0 2.585-1.83 2.585-1.83s-1.73-2.943-4.835-3.277"/>
						</svg>
					{:else if item.name === 'Bitcoin'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M23.638 14.904c-1.602 6.43-8.113 10.34-14.542 8.736C2.67 22.05-1.244 15.525.362 9.105 1.962 2.67 8.475-1.243 14.9.358c6.43 1.605 10.342 8.115 8.738 14.546M16.28 11.592c.21-1.41-.863-2.17-2.333-2.677l.477-1.913-1.164-.29-.464 1.86c-.306-.076-.62-.148-.934-.22l.468-1.87-1.165-.29-.477 1.912c-.253-.058-.502-.115-.744-.175l.001-.007-1.607-.4-.31 1.243s.863.198.845.21c.471.117.556.43.542.677l-.542 2.173c.032.008.074.02.12.038l-.12-.03-.76 3.045c-.058.143-.204.36-.533.278.012.017-.845-.21-.845-.21l-.578 1.332 1.517.378c.282.07.558.143.829.212l-.482 1.935 1.164.29.477-1.914c.314.085.618.162.915.235l-.475 1.902 1.165.29.482-1.932c1.99.377 3.485.225 4.117-1.574.51-1.45-.025-2.285-1.075-2.83.765-.176 1.34-.68 1.495-1.715M13.663 16.01c-.36 1.453-2.8.667-3.59.47l.64-2.57c.79.196 3.33.586 2.95 2.1m.36-3.612c-.33 1.32-2.37.65-3.03.485l.58-2.33c.66.165 2.79.473 2.45 1.845"/>
						</svg>
					{:else if item.name === 'Microsoft'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M11.4 24H0V12.6h11.4V24zM24 24H12.6V12.6H24V24zM11.4 11.4H0V0h11.4v11.4zM24 11.4H12.6V0H24v11.4z"/>
						</svg>
					{:else if item.name === 'NVIDIA'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M9.93 12.011c-.42 3.34 1.253 6.605 4.294 8.17.05.025.101.05.151.075 2.103 1.083 4.645 1.162 6.842.187 3.894-1.727 5.964-6.128 4.894-10.405-.065-.26-.14-.516-.224-.769C24.587 4.681 20.507.932 15.82.088c-.298-.054-.6-.082-.903-.084-4.997-.034-9.44 3.281-10.664 7.958-.213.814-.31 1.652-.323 2.497v1.552zm1.513-4.292c.41-.916 1.224-1.417 2.414-1.453 1.103-.033 2.206-.004 3.308-.014.266-.002.397.075.529.302 1.06 1.834 2.14 3.654 3.211 5.48l.058.099c-.013-.068-.013-.136-.042-.199-.658-1.46-1.332-2.911-1.994-4.369-.102-.224-.206-.33-.472-.33-1.076.009-2.153-.004-3.23.006-.172.002-.345.066-.47.174-.277.239-.483.548-.62.887-.405.99-.676 2.04-.725 3.115-.05 1.068.064 2.14.334 3.178.24.918.636 1.787 1.179 2.555.102.144.214.282.329.418l.016-.021c.122-.165.24-.335.349-.51.47-.755.797-1.593.956-2.473.16-.886.161-1.79-.002-2.676-.112-.612-.345-1.19-.688-1.701-.41-.615-.977-1.103-1.655-1.427-.678-.325-1.443-.475-2.201-.434-1.179.064-2.247.628-2.94 1.553-.692.925-1.018 2.106-.898 3.269.098.947.39 1.864.85 2.693.737 1.327 1.89 2.369 3.268 2.956.688.293 1.43.444 2.179.442.749-.002 1.49-.159 2.178-.46.459-.2.886-.473 1.264-.808.189-.167.361-.352.51-.556.075-.102.135-.212.18-.327.225-.576.225-1.211 0-1.787-.152-.387-.406-.728-.733-.982-.654-.507-1.49-.7-2.287-.527-.398.087-.77.263-1.077.51-.154.124-.285.277-.382.452-.194.35-.24.757-.131 1.14.109.382.365.71.7.896.335.186.73.222 1.098.099.184-.061.35-.167.481-.308.066-.07.12-.149.161-.235.082-.172.082-.371 0-.543-.164-.343-.533-.549-.914-.509-.191.02-.375.083-.534.181-.079.049-.148.11-.205.181-.114.142-.177.32-.177.505 0 .184.063.363.177.505.057.071.126.132.205.181.159.098.343.161.534.181.381-.04.75.166.914.509.082.172.082.371 0 .543-.041.086-.095.165-.161.235-.131.141-.297.247-.481.308-.368.123-.763.087-1.098-.099-.335-.186-.591-.514-.7-.896-.109-.383-.063-.79.131-1.14.097-.175.228-.328.382-.452.307-.247.679-.423 1.077-.51.797-.173 1.633.02 2.287.527.327.254.581.595.733.982.225.576.225 1.211 0 1.787-.045.115-.105.225-.18.327-.149.204-.321.389-.51.556-.378.335-.805.608-1.264.808-.688.301-1.429.458-2.178.46-.749.002-1.491-.149-2.179-.442-1.378-.587-2.531-1.629-3.268-2.956-.46-.829-.752-1.746-.85-2.693-.12-1.163.206-2.344.898-3.269.693-.925 1.761-1.489 2.94-1.553.758-.041 1.523.109 2.201.434.678.324 1.245.812 1.655 1.427.343.511.576 1.089.688 1.701.163.886.162 1.79.002 2.676-.159.88-.486 1.718-.956 2.473-.109.175-.227.345-.349.51l-.016.021c-.115-.136-.227-.274-.329-.418-.543-.768-.939-1.637-1.179-2.555-.27-1.038-.384-2.11-.334-3.178.049-1.075.32-2.125.725-3.115.137-.339.343-.648.62-.887.125-.108.298-.172.47-.174 1.077-.01 2.154.003 3.23-.006.266 0 .37.106.472.33.662 1.458 1.336 2.909 1.994 4.369.029.063.029.131.042.199l-.058-.099c-1.071-1.826-2.151-3.646-3.211-5.48-.132-.227-.263-.304-.529-.302-1.102.01-2.205-.019-3.308.014-1.19.036-2.004.537-2.414 1.453z"/>
						</svg>
					{:else if item.name === 'Google'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
							<path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
							<path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
							<path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
						</svg>
					{:else if item.name === 'Samsung'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M2 17.28c0 .76.61 1.37 1.37 1.37h17.26c.76 0 1.37-.61 1.37-1.37V6.72c0-.76-.61-1.37-1.37-1.37H3.37C2.61 5.35 2 5.96 2 6.72v10.56zm10.5-7.56c.96 0 1.74.79 1.74 1.74s-.79 1.74-1.74 1.74S10.76 12.42 10.76 11.46s.79-1.74 1.74-1.74zm-2.85 0c.96 0 1.74.79 1.74 1.74s-.79 1.74-1.74 1.74S8.91 12.42 8.91 11.46s.79-1.74 1.74-1.74zm5.7 0c.96 0 1.74.79 1.74 1.74s-.79 1.74-1.74 1.74S13.61 12.42 13.61 11.46s.79-1.74 1.74-1.74zm-8.55 0c.96 0 1.74.79 1.74 1.74s-.79 1.74-1.74 1.74S5.06 12.42 5.06 11.46s.79-1.74 1.74-1.74zm11.4 0c.96 0 1.74.79 1.74 1.74s-.79 1.74-1.74 1.74S16.46 12.42 16.46 11.46s.79-1.74 1.74-1.74zm-8.55 0c.96 0 1.74.79 1.74 1.74s-.79 1.74-1.74 1.74S5.06 12.42 5.06 11.46s.79-1.74 1.74-1.74zm11.4 0c.96 0 1.74.79 1.74 1.74s-.79 1.74-1.74 1.74S16.46 12.42 16.46 11.46s.79-1.74 1.74-1.74z"/>
						</svg>
					{:else if item.name === 'AMD'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M18.335 0L24 0v24h-5.665zM.001 24L0 0h5.665l12.671 18.667V24z"/>
						</svg>
					{:else if item.name === 'Netflix'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M5.398 0v.006c3.028 8.556 5.37 15.175 8.348 23.596 2.344.058 4.85.398 4.854.398-2.8-7.924-5.923-16.747-8.487-24zm8.489 0v9.63L18.6 22.951c-.043-7.86-.004-15.71.002-22.95zM5.398 1.05V24c2.182-.262 4.41-.398 5.404-.398V1.05z"/>
						</svg>
					{:else if item.name === 'Meta'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
						</svg>
					{:else if item.name === 'PayPal'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M7.076 21.337H2.47a.641.641 0 0 1-.633-.74L4.944.901C5.026.382 5.474 0 5.998 0h7.46c2.57 0 4.578.543 5.69 1.81 1.01 1.15 1.304 2.42 1.012 4.287-.023.143-.047.288-.077.437-.983 5.05-4.349 6.797-8.647 6.797h-2.19c-.524 0-.968.382-1.05.9l-1.12 7.106zm14.146-14.42a3.35 3.35 0 0 0-.607-.225c-.3-.1-.619-.18-.948-.24a15.963 15.963 0 0 0-1.759-.18h-2.852a.641.641 0 0 0-.633.531l-.713 4.51-.296 1.88c-.05.317.18.604.5.604h2.925c4.298 0 7.664-1.747 8.647-6.797.03-.149.054-.294.077-.437.201-1.28.082-2.15-.341-2.646z"/>
						</svg>
					{:else if item.name === 'Shopify'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M15.337 2.343c-.372-.045-.648.06-.781.21-.121.135-.242.405-.242.405s-2.176-1.545-3.074-1.47c-.898.075-1.35.405-1.59.63-.18.18-.36.39-.45.6-.09.195-.135.39-.135.39l-2.416.495s-.105-.255-.27-.525c-.165-.27-.375-.585-.735-.81-.36-.225-.795-.45-1.56-.225-.765.225-1.35.855-1.59 1.665-.24.81-.15 1.8.36 3.15.51 1.35 1.395 3.045 2.94 5.145l4.995 6.885s.045.06.09.105h.045l.045-.015c.045-.015.09-.045.135-.075l7.41-10.86c.45-.66.6-1.14.6-1.515 0-.375-.09-.705-.315-.96-.225-.255-.54-.42-.9-.48z"/>
						</svg>
					{:else if item.name === 'Intel'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M7.5 7.5h1.5v9h-1.5zm4.5 0h1.5v9H12zm-6 0h1.5v9H6zm12 0h1.5v9H18z"/>
						</svg>
					{:else if item.name === 'Oracle'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M16.412 4.412h-8.824a7.588 7.588 0 000 15.176h8.824a7.588 7.588 0 000-15.176zm0 12.176h-8.824a4.588 4.588 0 010-9.176h8.824a4.588 4.588 0 010 9.176z"/>
						</svg>
					{:else if item.name === 'Salesforce'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 6.621 5.367 11.988 11.988 11.988s11.987-5.367 11.987-11.988C24.004 5.367 18.637.001 12.017.001zM8.948 4.615c.129 0 .234.105.234.234v4.615c0 .129-.105.234-.234.234H4.333c-.129 0-.234-.105-.234-.234V4.849c0-.129.105-.234.234-.234h4.615zm10.719 4.849c0 .129-.105.234-.234.234h-4.615c-.129 0-.234-.105-.234-.234V4.849c0-.129.105-.234.234-.234h4.615c.129 0 .234.105.234.234v4.615zm0 10.719c0 .129-.105.234-.234.234h-4.615c-.129 0-.234-.105-.234-.234v-4.615c0-.129.105-.234.234-.234h4.615c.129 0 .234.105.234.234v4.615zm-10.719 0c0 .129-.105.234-.234.234H4.099c-.129 0-.234-.105-.234-.234v-4.615c0-.129.105-.234.234-.234h4.615c.129 0 .234.105.234.234v4.615z"/>
						</svg>
					{:else if item.name === 'Ethereum'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M11.944 17.97L4.58 13.62 11.943 24l7.37-10.38-7.372 4.35h.003zM12.056 0L4.69 12.223l7.365 4.354 7.365-4.35L12.056 0z"/>
						</svg>
					{:else if item.name === 'Zoom'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M21.542 6.11C20.555 3.556 18.204 2 15.5 2H8.5C3.806 2 0 5.806 0 10.5S3.806 19 8.5 19h7c2.704 0 5.055-1.556 6.042-4.11A1.5 1.5 0 0023 13.5v-3a1.5 1.5 0 00-1.458-1.39zM8.5 16a5.5 5.5 0 110-11 5.5 5.5 0 010 11z"/>
						</svg>
					{:else if item.name === 'Twitter'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
						</svg>
					{:else if item.name === 'S&P 500'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M3 17l6-6 4 4 8-8M3 21h18V3"/>
						</svg>
					{:else if item.name === 'Gold'}
						<svg class="w-full h-full" fill={item.iconColor} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
							<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
						</svg>
					{/if}
				</div>
				<span class="font-semibold">{item.name}</span>
			</div>
		{/each}
	</div>

	<!-- 떠다니는 금융 아이콘들 -->
	<div class="absolute inset-0 pointer-events-none overflow-hidden">
		{#each Array(8) as _, i}
			<div class="floating-icon absolute opacity-20"
				style="left: {(i * 12.5) % 100}%; top: {(i * 17 + 15) % 80}%; animation-delay: {i * 1.2}s;">
				{#if i % 4 === 0}
					<!-- 달러 아이콘 -->
					<svg class="w-8 h-8 text-green-400" fill="currentColor" viewBox="0 0 24 24">
						<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1.41 16.09V20h-2.67v-1.93c-1.71-.36-3.16-1.46-3.27-3.4h1.96c.1 1.05.82 1.87 2.65 1.87 1.96 0 2.4-.98 2.4-1.59 0-.83-.44-1.61-2.67-2.14-2.48-.6-4.18-1.62-4.18-3.67 0-1.72 1.39-2.84 3.11-3.21V4h2.67v1.95c1.86.45 2.79 1.86 2.85 3.39H14.3c-.05-1.11-.64-1.87-2.22-1.87-1.5 0-2.4.68-2.4 1.64 0 .84.65 1.39 2.67 1.91s4.18 1.39 4.18 3.91c-.01 1.83-1.38 2.83-3.12 3.16z"/>
					</svg>
				{:else if i % 4 === 1}
					<!-- 트렌드 아이콘 -->
					<svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
					</svg>
				{:else if i % 4 === 2}
					<!-- 파이 차트 아이콘 -->
					<svg class="w-8 h-8 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
					</svg>
				{:else}
					<!-- 지구본 아이콘 -->
					<svg class="w-8 h-8 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
					</svg>
				{/if}
			</div>
		{/each}
	</div>

	<!-- 미니 캔들스틱 차트들 -->
	<div class="absolute inset-0 pointer-events-none overflow-hidden opacity-15">
		{#each Array(12) as _, i}
			<div class="mini-candlestick absolute"
				style="left: {(i * 8 + 5) % 95}%; top: {(i * 11 + 25) % 65}%; animation-delay: {i * 0.5}s;">
				<div class="w-1 bg-emerald-400 mx-auto" style="height: {Math.random() * 20 + 10}px;"></div>
				<div class="w-3 {Math.random() > 0.5 ? 'bg-emerald-400' : 'bg-red-400'} mx-auto mt-1" style="height: {Math.random() * 15 + 8}px;"></div>
				<div class="w-1 bg-emerald-400 mx-auto" style="height: {Math.random() * 20 + 10}px;"></div>
			</div>
		{/each}
	</div>

	<!-- 흘러가는 금융 종목 티커 (상단) -->
	<div class="absolute top-0 w-full h-12 bg-gradient-to-r from-slate-800/80 to-slate-700/80 backdrop-blur-sm border-b border-slate-600/40 overflow-hidden">
		<div class="ticker-content flex items-center h-full text-sm font-mono text-slate-300 whitespace-nowrap">
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#000000" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701"/>
				</svg>
				<span>Apple</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#4285F4" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
					<path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
					<path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
					<path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
				</svg>
				<span>Google</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#5C2D91" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M11.4 24H0V12.6h11.4V24zM24 24H12.6V12.6H24V24zM11.4 11.4H0V0h11.4v11.4zM24 11.4H12.6V0H24v11.4z"/>
				</svg>
				<span>Microsoft</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#CC0000" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="m12 5.362-2.475-.308c-.738-.092-1.344-.145-1.344-.145s.737 3.476 3.819 3.476c3.083 0 3.819-3.476 3.819-3.476s-.606.053-1.344.145zm7.415.323c-.738-.074-1.605-.11-2.493-.11-1.374 0-2.878.11-4.922.11-2.045 0-3.548-.11-4.922-.11-.888 0-1.755.036-2.493.11C2.48 6.019.75 8.962.75 8.962s.951 1.83 2.585 1.83c1.634 0 3.819-.184 3.819-.184s-.328 5.895-.328 8.027c0 .737.184 1.105.184 1.105h1.474s.184-.368.184-1.105c0-2.132-.328-8.027-.328-8.027s2.185.184 3.819.184c1.634 0 3.819-.184 3.819-.184s-.328 5.895-.328 8.027c0 .737.184 1.105.184 1.105h1.474s.184-.368.184-1.105c0-2.132-.328-8.027-.328-8.027s2.185.184 3.819.184c1.634 0 2.585-1.83 2.585-1.83s-1.73-2.943-4.835-3.277"/>
				</svg>
				<span>Tesla</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#76B900" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M9.93 12.011c-.42 3.34 1.253 6.605 4.294 8.17.05.025.101.05.151.075 2.103 1.083 4.645 1.162 6.842.187 3.894-1.727 5.964-6.128 4.894-10.405-.065-.26-.14-.516-.224-.769C24.587 4.681 20.507.932 15.82.088c-.298-.054-.6-.082-.903-.084-4.997-.034-9.44 3.281-10.664 7.958-.213.814-.31 1.652-.323 2.497v1.552zm1.513-4.292c.41-.916 1.224-1.417 2.414-1.453 1.103-.033 2.206-.004 3.308-.014.266-.002.397.075.529.302 1.06 1.834 2.14 3.654 3.211 5.48l.058.099c-.013-.068-.013-.136-.042-.199-.658-1.46-1.332-2.911-1.994-4.369-.102-.224-.206-.33-.472-.33-1.076.009-2.153-.004-3.23.006-.172.002-.345.066-.47.174-.277.239-.483.548-.62.887-.405.99-.676 2.04-.725 3.115-.05 1.068.064 2.14.334 3.178.24.918.636 1.787 1.179 2.555.102.144.214.282.329.418l.016-.021c.122-.165.24-.335.349-.51.47-.755.797-1.593.956-2.473.16-.886.161-1.79-.002-2.676-.112-.612-.345-1.19-.688-1.701-.41-.615-.977-1.103-1.655-1.427-.678-.325-1.443-.475-2.201-.434-1.179.064-2.247.628-2.94 1.553-.692.925-1.018 2.106-.898 3.269.098.947.39 1.864.85 2.693.737 1.327 1.89 2.369 3.268 2.956.688.293 1.43.444 2.179.442.749-.002 1.49-.159 2.178-.46.459-.2.886-.473 1.264-.808.189-.167.361-.352.51-.556.075-.102.135-.212.18-.327.225-.576.225-1.211 0-1.787-.152-.387-.406-.728-.733-.982-.654-.507-1.49-.7-2.287-.527-.398.087-.77.263-1.077.51-.154.124-.285.277-.382.452-.194.35-.24.757-.131 1.14.109.382.365.71.7.896.335.186.73.222 1.098.099.184-.061.35-.167.481-.308.066-.07.12-.149.161-.235.082-.172.082-.371 0-.543-.164-.343-.533-.549-.914-.509-.191.02-.375.083-.534.181-.079.049-.148.11-.205.181-.114.142-.177.32-.177.505 0 .184.063.363.177.505.057.071.126.132.205.181.159.098.343.161.534.181.381-.04.75.166.914.509.082.172.082.371 0 .543-.041.086-.095.165-.161.235-.131.141-.297.247-.481.308-.368.123-.763.087-1.098-.099-.335-.186-.591-.514-.7-.896-.109-.383-.063-.79.131-1.14.097-.175.228-.328.382-.452.307-.247.679-.423 1.077-.51.797-.173 1.633.02 2.287.527.327.254.581.595.733.982.225.576.225 1.211 0 1.787-.045.115-.105.225-.18.327-.149.204-.321.389-.51.556-.378.335-.805.608-1.264.808-.688.301-1.429.458-2.178.46-.749.002-1.491-.149-2.179-.442-1.378-.587-2.531-1.629-3.268-2.956-.46-.829-.752-1.746-.85-2.693-.12-1.163.206-2.344.898-3.269.693-.925 1.761-1.489 2.94-1.553.758-.041 1.523.109 2.201.434.678.324 1.245.812 1.655 1.427.343.511.576 1.089.688 1.701.163.886.162 1.79.002 2.676-.159.88-.486 1.718-.956 2.473-.109.175-.227.345-.349.51l-.016.021c-.115-.136-.227-.274-.329-.418-.543-.768-.939-1.637-1.179-2.555-.27-1.038-.384-2.11-.334-3.178.049-1.075.32-2.125.725-3.115.137-.339.343-.648.62-.887.125-.108.298-.172.47-.174 1.077-.01 2.154.003 3.23-.006.266 0 .37.106.472.33.662 1.458 1.336 2.909 1.994 4.369.029.063.029.131.042.199l-.058-.099c-1.071-1.826-2.151-3.646-3.211-5.48-.132-.227-.263-.304-.529-.302-1.102.01-2.205-.019-3.308.014-1.19.036-2.004.537-2.414 1.453z"/>
				</svg>
				<span>NVIDIA</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#ED1C24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M18.335 0L24 0v24h-5.665zM.001 24L0 0h5.665l12.671 18.667V24z"/>
				</svg>
				<span>AMD</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#1877F2" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
				</svg>
				<span>Meta</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#E50914" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M5.398 0v.006c3.028 8.556 5.37 15.175 8.348 23.596 2.344.058 4.85.398 4.854.398-2.8-7.924-5.923-16.747-8.487-24zm8.489 0v9.63L18.6 22.951c-.043-7.86-.004-15.71.002-22.95zM5.398 1.05V24c2.182-.262 4.41-.398 5.404-.398V1.05z"/>
				</svg>
				<span>Netflix</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#00457C" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M7.076 21.337H2.47a.641.641 0 0 1-.633-.74L4.944.901C5.026.382 5.474 0 5.998 0h7.46c2.57 0 4.578.543 5.69 1.81 1.01 1.15 1.304 2.42 1.012 4.287-.023.143-.047.288-.077.437-.983 5.05-4.349 6.797-8.647 6.797h-2.19c-.524 0-.968.382-1.05.9l-1.12 7.106zm14.146-14.42a3.35 3.35 0 0 0-.607-.225c-.3-.1-.619-.18-.948-.24a15.963 15.963 0 0 0-1.759-.18h-2.852a.641.641 0 0 0-.633.531l-.713 4.51-.296 1.88c-.05.317.18.604.5.604h2.925c4.298 0 7.664-1.747 8.647-6.797.03-.149.054-.294.077-.437.201-1.28.082-2.15-.341-2.646z"/>
				</svg>
				<span>PayPal</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#8B5CF6" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M3 17l6-6 4 4 8-8M3 21h18V3"/>
				</svg>
				<span>S&P 500</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#0052CC" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M3 17l6-6 4 4 8-8M3 21h18V3"/>
				</svg>
				<span>NASDAQ</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#FFD700" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
				</svg>
				<span>Gold</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#F7931E" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M23.638 14.904c-1.602 6.43-8.113 10.34-14.542 8.736C2.67 22.05-1.244 15.525.362 9.105 1.962 2.67 8.475-1.243 14.9.358c6.43 1.605 10.342 8.115 8.738 14.546M16.28 11.592c.21-1.41-.863-2.17-2.333-2.677l.477-1.913-1.164-.29-.464 1.86c-.306-.076-.62-.148-.934-.22l.468-1.87-1.165-.29-.477 1.912c-.253-.058-.502-.115-.744-.175l.001-.007-1.607-.4-.31 1.243s.863.198.845.21c.471.117.556.43.542.677l-.542 2.173c.032.008.074.02.12.038l-.12-.03-.76 3.045c-.058.143-.204.36-.533.278.012.017-.845-.21-.845-.21l-.578 1.332 1.517.378c.282.07.558.143.829.212l-.482 1.935 1.164.29.477-1.914c.314.085.618.162.915.235l-.475 1.902 1.165.29.482-1.932c1.99.377 3.485.225 4.117-1.574.51-1.45-.025-2.285-1.075-2.83.765-.176 1.34-.68 1.495-1.715M13.663 16.01c-.36 1.453-2.8.667-3.59.47l.64-2.57c.79.196 3.33.586 2.95 2.1m.36-3.612c-.33 1.32-2.37.65-3.03.485l.58-2.33c.66.165 2.79.473 2.45 1.845"/>
				</svg>
				<span>Bitcoin</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#627EEA" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M11.944 17.97L4.58 13.62 11.943 24l7.37-10.38-7.372 4.35h.003zM12.056 0L4.69 12.223l7.365 4.354 7.365-4.35L12.056 0z"/>
				</svg>
				<span>Ethereum</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#0071C5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M7.5 7.5h1.5v9h-1.5zm4.5 0h1.5v9H12zm-6 0h1.5v9H6zm12 0h1.5v9H18z"/>
				</svg>
				<span>Intel</span>
			</div>
		</div>
	</div>

	<!-- 흘러가는 금융 종목 티커 (하단) -->
	<div class="absolute bottom-0 w-full h-12 bg-gradient-to-r from-slate-800/80 to-slate-700/80 backdrop-blur-sm border-t border-slate-600/40 overflow-hidden">
		<div class="ticker-content-reverse flex items-center h-full text-sm font-mono text-slate-300 whitespace-nowrap">
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#0052CC" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M3 17l6-6 4 4 8-8M3 21h18V3"/>
				</svg>
				<span>KOSPI</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#8B5CF6" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M3 17l6-6 4 4 8-8M3 21h18V3"/>
				</svg>
				<span>KOSDAQ</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#1428A0" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M2 17.28c0 .76.61 1.37 1.37 1.37h17.26c.76 0 1.37-.61 1.37-1.37V6.72c0-.76-.61-1.37-1.37-1.37H3.37C2.61 5.35 2 5.96 2 6.72v10.56zm10.5-7.56c.96 0 1.74.79 1.74 1.74s-.79 1.74-1.74 1.74S10.76 12.42 10.76 11.46s.79-1.74 1.74-1.74zm-2.85 0c.96 0 1.74.79 1.74 1.74s-.79 1.74-1.74 1.74S8.91 12.42 8.91 11.46s.79-1.74 1.74-1.74zm5.7 0c.96 0 1.74.79 1.74 1.74s-.79 1.74-1.74 1.74S13.61 12.42 13.61 11.46s.79-1.74 1.74-1.74zm-8.55 0c.96 0 1.74.79 1.74 1.74s-.79 1.74-1.74 1.74S5.06 12.42 5.06 11.46s.79-1.74 1.74-1.74zm11.4 0c.96 0 1.74.79 1.74 1.74s-.79 1.74-1.74 1.74S16.46 12.42 16.46 11.46s.79-1.74 1.74-1.74zm-8.55 0c.96 0 1.74.79 1.74 1.74s-.79 1.74-1.74 1.74S5.06 12.42 5.06 11.46s.79-1.74 1.74-1.74zm11.4 0c.96 0 1.74.79 1.74 1.74s-.79 1.74-1.74 1.74S16.46 12.42 16.46 11.46s.79-1.74 1.74-1.74z"/>
				</svg>
				<span>Samsung</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#1B263B" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M2 4v16h20V4H2zm18 14H4V6h16v12zM6 8h12v2H6V8zm0 4h12v2H6v-2zm0 4h12v2H6v-2z"/>
				</svg>
				<span>SK Hynix</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#A50034" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M7.5 5.25v1.5h1.5v-1.5h6v1.5h1.5v-1.5h0.75c0.414 0 0.75 0.336 0.75 0.75v12c0 0.414-0.336 0.75-0.75 0.75h-15c-0.414 0-0.75-0.336-0.75-0.75v-12c0-0.414 0.336-0.75 0.75-0.75h0.75zm1.5-1.5v-0.75c0-0.414 0.336-0.75 0.75-0.75h4.5c0.414 0 0.75 0.336 0.75 0.75v0.75h0.75c1.243 0 2.25 1.007 2.25 2.25v12c0 1.243-1.007 2.25-2.25 2.25h-15c-1.243 0-2.25-1.007-2.25-2.25v-12c0-1.243 1.007-2.25 2.25-2.25h0.75z"/>
				</svg>
				<span>LG Energy</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#03C75A" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M16.273 12.845 7.376 0H0v24h7.726V11.156L16.624 24H24V0h-7.727v12.845z"/>
				</svg>
				<span>NAVER</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#FFCD00" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M12 3c5.799 0 10.5 3.664 10.5 8.185 0 4.52-4.701 8.184-10.5 8.184a13.5 13.5 0 0 1-1.727-.11l-4.408 2.883c-.501.265-.678.236-.472-.413l.892-3.678c-2.88-1.46-4.785-3.99-4.785-6.866C1.5 6.665 6.201 3 12 3z"/>
				</svg>
				<span>Kakao</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#AA1428" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M2 4v16h20V4H2zm18 14H4V6h16v12zM6 8h12v2H6V8zm0 4h12v2H6v-2zm0 4h8v2H6v-2z"/>
				</svg>
				<span>Hyundai</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#FF6B00" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
				</svg>
				<span>Posco</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#0066CC" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
				</svg>
				<span>GDP</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#FF6B6B" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M3 13h2v8H3zM7 9h2v12H7zM11 5h2v16h-2zM15 8h2v13h-2zM19 2h2v19h-2z"/>
				</svg>
				<span>CPI</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#2ECC71" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
				</svg>
				<span>Interest Rate</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#E74C3C" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M3 17l6-6 4 4 8-8M3 21h18V3"/>
				</svg>
				<span>VIX</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#0052CC" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M3 17l6-6 4 4 8-8M3 21h18V3"/>
				</svg>
				<span>FTSE 100</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#00A651" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<circle cx="12" cy="12" r="10"/>
					<text x="12" y="17" text-anchor="middle" fill="white" font-size="8" font-weight="bold">₩</text>
				</svg>
				<span>USD/KRW</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#7AB55C" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M15.337 2.343c-.372-.045-.648.06-.781.21-.121.135-.242.405-.242.405s-2.176-1.545-3.074-1.47c-.898.075-1.35.405-1.59.63-.18.18-.36.39-.45.6-.09.195-.135.39-.135.39l-2.416.495s-.105-.255-.27-.525c-.165-.27-.375-.585-.735-.81-.36-.225-.795-.45-1.56-.225-.765.225-1.35.855-1.59 1.665-.24.81-.15 1.8.36 3.15.51 1.35 1.395 3.045 2.94 5.145l4.995 6.885s.045.06.09.105h.045l.045-.015c.045-.015.09-.045.135-.075l7.41-10.86c.45-.66.6-1.14.6-1.515 0-.375-.09-.705-.315-.96-.225-.255-.54-.42-.9-.48z"/>
				</svg>
				<span>Coupang</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#F80000" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M16.412 4.412h-8.824a7.588 7.588 0 000 15.176h8.824a7.588 7.588 0 000-15.176zm0 12.176h-8.824a4.588 4.588 0 010-9.176h8.824a4.588 4.588 0 010 9.176z"/>
				</svg>
				<span>Doosan</span>
			</div>
			<span class="ticker-separator">•</span>
			<div class="ticker-item flex items-center gap-1.5">
				<svg class="w-4 h-4" fill="#E91E63" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
				</svg>
				<span>Bank of Korea</span>
			</div>
		</div>
	</div>

	<!-- 로그인 폼 컨테이너 -->
	<div class="relative z-10 w-full max-w-md mx-4">
		<!-- 로고 및 헤더 -->
		<div class="text-center mb-8">
			<div class="flex items-center justify-center mb-4">
				<div class="relative group">
					<div class="flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-500 via-purple-500 to-teal-500 rounded-3xl shadow-2xl shadow-blue-500/40 transform rotate-3 transition-transform duration-200 group-hover:rotate-6 group-hover:scale-110">
						<!-- 금융 차트 로고 SVG -->
						<svg class="w-9 h-9 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
					<div class="absolute -top-1 -right-1 w-4 h-4 bg-emerald-400 rounded-full animate-pulse shadow-lg shadow-emerald-400/50"></div>
					<!-- 추가 데코레이션 -->
					<div class="absolute -bottom-1 -left-1 w-3 h-3 bg-blue-400 rounded-full opacity-60 animate-pulse" style="animation-delay: 0.5s;"></div>
				</div>
			</div>
			<h1 class="text-4xl font-black bg-gradient-to-r from-white via-blue-200 to-purple-200 bg-clip-text text-transparent tracking-tight mb-2">
				FinanceChart
			</h1>
			<p class="text-lg text-slate-300 font-medium">Analytics Dashboard</p>
			<p class="text-sm text-slate-400 mt-2">금융 데이터 분석의 새로운 경험</p>
		</div>

		<!-- 로그인 폼 -->
		<div class="bg-slate-800/80 backdrop-blur-xl border border-slate-600/40 rounded-3xl shadow-2xl shadow-black/40 p-8">
			<form on:submit={handleLogin} class="space-y-6">
				<div class="space-y-4">
					<h2 class="text-2xl font-bold text-white text-center mb-6">로그인</h2>
					
					<!-- 아이디 입력 -->
					<div class="space-y-2">
						<label for="username" class="block text-sm font-semibold text-slate-200">
							아이디
						</label>
						<div class="relative">
							<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
								<svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
								</svg>
							</div>
							<input
								id="username"
								type="text"
								bind:value={username}
								placeholder="아이디를 입력하세요"
								class="w-full pl-10 pr-4 py-3 bg-slate-700/80 border border-slate-600/60 rounded-2xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200"
								disabled={isLoading || isRedirecting}
								required
							/>
						</div>
					</div>

					<!-- 비밀번호 입력 -->
					<div class="space-y-2">
						<label for="password" class="block text-sm font-semibold text-slate-200">
							비밀번호
						</label>
						<div class="relative">
							<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
								<svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
								</svg>
							</div>
							<input
								id="password"
								type={showPassword ? 'text' : 'password'}
								value={password}
								on:input={(e) => password = e.currentTarget.value}
								placeholder="••••••••"
								class="w-full pl-10 pr-12 py-3 bg-slate-700/80 border border-slate-600/60 rounded-2xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200"
								disabled={isLoading || isRedirecting}
								required
							/>
							<button
								type="button"
								class="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-white transition-colors duration-200"
								on:click={() => showPassword = !showPassword}
								disabled={isLoading || isRedirecting}
							>
								{#if showPassword}
									<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21"></path>
									</svg>
								{:else}
									<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
									</svg>
								{/if}
							</button>
						</div>
					</div>
				</div>

				<!-- 로그인 버튼 -->
				<button
					type="submit"
					class="w-full bg-gradient-to-r from-blue-500 via-purple-500 to-teal-500 text-white font-bold py-3 px-6 rounded-2xl shadow-2xl shadow-blue-500/40 hover:shadow-blue-500/60 transform hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
					disabled={isLoading || isRedirecting}
				>
					{#if isLoading}
						<div class="flex items-center justify-center space-x-2">
							<div class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
							<span>로그인 중...</span>
						</div>
					{:else if isRedirecting}
						<div class="flex items-center justify-center space-x-2">
							<div class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
							<span>대시보드로 이동 중...</span>
						</div>
					{:else}
						로그인
					{/if}
				</button>
			</form>

			<!-- 데모 계정 안내 -->
			<div class="mt-6 pt-6 border-t border-slate-600/40">
				<div class="text-center space-y-3">
					<p class="text-sm text-slate-400">데모 계정으로 체험해보세요</p>
					<button
						type="button"
						on:click={loginWithDemo}
						class="w-full bg-slate-700/80 hover:bg-slate-600/80 text-slate-200 font-medium py-2.5 px-4 rounded-xl border border-slate-600/60 hover:border-slate-500/60 transition-all duration-200 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
						disabled={isLoading || isRedirecting}
					>
						데모 계정으로 로그인 (jukim)
					</button>
					<p class="text-xs text-slate-500">
						아이디: jukim, 비밀번호: jukim123$
					</p>
				</div>
			</div>
		</div>

		<!-- 추가 정보 -->
		<div class="text-center mt-6">
			<p class="text-sm text-slate-400">
				© 2025 FinanceChart. 모든 권리 보유.
			</p>
		</div>
	</div>
</div>

<style>
	/* 애니메이션 효과 */
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

	/* 입력 필드 포커스 효과 */
	input:focus {
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
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

	/* === 새로운 금융 배경 애니메이션 === */
	
	/* 떠다니는 금융 종목/지표 애니메이션 */
	.floating-financial-item {
		animation: floatFinancialItem 15s linear infinite;
	}

	@keyframes floatFinancialItem {
		0% {
			transform: translateY(100vh) translateX(0);
			opacity: 0;
		}
		10% {
			opacity: 0.3;
		}
		90% {
			opacity: 0.3;
		}
		100% {
			transform: translateY(-100px) translateX(20px);
			opacity: 0;
		}
	}

	/* 떠다니는 아이콘 애니메이션 */
	.floating-icon {
		animation: floatIcon 20s ease-in-out infinite;
	}

	@keyframes floatIcon {
		0%, 100% {
			transform: translateY(0) rotate(0deg) scale(1);
		}
		25% {
			transform: translateY(-20px) rotate(90deg) scale(1.1);
		}
		50% {
			transform: translateY(-10px) rotate(180deg) scale(0.9);
		}
		75% {
			transform: translateY(-25px) rotate(270deg) scale(1.05);
		}
	}

	/* 미니 캔들스틱 애니메이션 */
	.mini-candlestick {
		animation: candlestickPulse 3s ease-in-out infinite;
	}

	@keyframes candlestickPulse {
		0%, 100% {
			transform: scaleY(1);
			opacity: 0.15;
		}
		50% {
			transform: scaleY(1.2);
			opacity: 0.25;
		}
	}

	/* 상단 티커 테이프 애니메이션 */
	.ticker-content {
		animation: tickerScroll 30s linear infinite;
		display: flex;
		gap: 2rem;
	}

	@keyframes tickerScroll {
		0% {
			transform: translateX(100%);
		}
		100% {
			transform: translateX(-100%);
		}
	}

	/* 하단 티커 테이프 애니메이션 (역방향) */
	.ticker-content-reverse {
		animation: tickerScrollReverse 25s linear infinite;
		display: flex;
		gap: 2rem;
	}

	@keyframes tickerScrollReverse {
		0% {
			transform: translateX(-100%);
		}
		100% {
			transform: translateX(100%);
		}
	}

	/* 티커 아이템 스타일 */
	.ticker-item {
		color: #10b981; /* 기본 상승 색상 */
		font-weight: 600;
		text-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
	}

	.ticker-separator {
		color: #64748b;
		margin: 0 1rem;
	}

	/* 주식 차트 라인 글로우 효과 */
	.chart-line-1 {
		filter: drop-shadow(0 0 8px rgba(59, 130, 246, 0.6));
	}

	.chart-line-2 {
		filter: drop-shadow(0 0 6px rgba(16, 185, 129, 0.5));
	}

	.chart-line-3 {
		filter: drop-shadow(0 0 4px rgba(245, 158, 11, 0.4));
	}

	/* 반응형 애니메이션 성능 최적화 */
	@media (prefers-reduced-motion: reduce) {
		.floating-financial-item,
		.floating-icon,
		.mini-candlestick,
		.ticker-content,
		.ticker-content-reverse {
			animation-duration: 0.01ms !important;
			animation-iteration-count: 1 !important;
		}
		
		.chart-line-1,
		.chart-line-2,
		.chart-line-3 {
			filter: none;
		}
	}

	/* 모바일 최적화 */
	@media (max-width: 768px) {
		.floating-financial-item {
			font-size: 0.875rem;
		}
		
		.floating-financial-item .w-5 {
			width: 1.125rem;
			height: 1.125rem;
		}
		
		.floating-icon svg {
			width: 1.5rem;
			height: 1.5rem;
		}
		
		.ticker-content,
		.ticker-content-reverse {
			font-size: 0.75rem;
		}
		
		.ticker-content .w-4,
		.ticker-content-reverse .w-4 {
			width: 0.875rem;
			height: 0.875rem;
		}
		
		.mini-candlestick {
			transform: scale(0.8);
		}
	}

	/* 성능 최적화를 위한 GPU 가속 */
	.floating-financial-item,
	.floating-icon,
	.mini-candlestick,
	.ticker-content,
	.ticker-content-reverse {
		will-change: transform;
		backface-visibility: hidden;
		perspective: 1000px;
	}
</style> 