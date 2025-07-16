<script lang="ts">
	import { onMount } from 'svelte';
	import { getEconomicCalendar } from '$lib/api-connector/FinanceApi';

	// 현재 연도
	let currentYear = new Date().getFullYear();

	// 월 이름 배열
	const monthNames = [
		'1월', '2월', '3월', '4월', '5월', '6월',
		'7월', '8월', '9월', '10월', '11월', '12월'
	];

	// 국가 목록 정의
	const availableCountries = [
		{ code: 'kr', name: '한국', flag: '🇰🇷' },
		{ code: 'us', name: '미국', flag: '🇺🇸' },
		{ code: 'cn', name: '중국', flag: '🇨🇳' },
		{ code: 'gb', name: '영국', flag: '🇬🇧' },
		{ code: 'eu', name: '유럽', flag: '🇪🇺' },
		{ code: 'jp', name: '일본', flag: '🇯🇵' },
		{ code: 'ca', name: '캐나다', flag: '🇨🇦' },
		{ code: 'au', name: '호주', flag: '🇦🇺' }
	];

	// 선택된 국가들
	let selectedCountries: string[] = ['kr', 'us', 'cn', 'gb', 'eu'];
	
	// 전체 선택 상태 (reactive)
	$: isAllSelected = selectedCountries.length === availableCountries.length;

	// 한국 공휴일 데이터 (기본적인 공휴일들)
	const koreanHolidays: Record<string, string> = {
		'1-1': '신정',
		'3-1': '삼일절',
		'5-5': '어린이날',
		'6-6': '현충일',
		'8-15': '광복절',
		'10-3': '개천절',
		'10-9': '한글날',
		'12-25': '크리스마스'
	};

	// 월별 날짜 데이터 타입
	interface DateInfo {
		date: number;
		dayOfWeek: number; // 0: 일요일, 1: 월요일, ..., 6: 토요일
		isWeekend: boolean;
		isHoliday: boolean;
		holidayName?: string;
		events?: EconomicEvent[]; // 해당 날짜의 경제 이벤트들
	}

	// 경제 이벤트 타입
	interface EconomicEvent {
		date: string;
		date_full: string;
		day: string;
		time: string;
		event_name: string;
		importance: string;
		importance_level: number;
		importance_class: string;
		actual: string;
		forecast: string;
		previous: string;
		country_name: string;
		country_code: string;
		index: string;
	}

	// 연도별 달력 데이터
	let calendarData: DateInfo[][] = [];
	
	// 경제 캘린더 데이터
	let economicEvents: EconomicEvent[] = [];
	let isLoadingEvents = false;
	let eventsError = '';

	// 스크롤 컨테이너 참조
	let scrollContainer: HTMLElement;

	// 선택된 날짜와 7일간 이벤트 데이터
	let selectedDateInfo: {
		year: number;
		month: number;
		date: number;
		weekEvents: Array<{
			date: string;
			year: number;
			month: number;
			day: number;
			events: EconomicEvent[];
			isToday: boolean;
			isSelected: boolean;
		}>;
	} | null = null;

	// 주어진 월의 일수를 반환하는 함수
	const getDaysInMonth = (year: number, month: number): number => {
		return new Date(year, month, 0).getDate();
	};

	// 특정 날짜의 요일을 반환하는 함수
	const getDayOfWeek = (year: number, month: number, date: number): number => {
		return new Date(year, month - 1, date).getDay();
	};

	// 공휴일 여부 확인 함수
	const isHoliday = (month: number, date: number): { isHoliday: boolean; name?: string } => {
		const key = `${month}-${date}`;
		if (koreanHolidays[key]) {
			return { isHoliday: true, name: koreanHolidays[key] };
		}
		return { isHoliday: false };
	};

	// 오늘 날짜인지 확인하는 함수
	const isToday = (year: number, month: number, date: number): boolean => {
		const today = new Date();
		return year === today.getFullYear() && 
			   month === (today.getMonth() + 1) && 
			   date === today.getDate();
	};

	// 경제 캘린더 데이터 가져오기
	const fetchEconomicCalendar = async (year: number) => {
		isLoadingEvents = true;
		eventsError = '';
		
		// 국가가 하나도 선택되지 않은 경우 빈 달력 표시
		if (selectedCountries.length === 0) {
			console.log('선택된 국가가 없어 빈 달력을 표시합니다.');
			economicEvents = [];
			calendarData = generateCalendarData(year);
			isLoadingEvents = false;
			return;
		}
		
		try {
			console.log(`경제 캘린더 데이터 요청: ${year}년, 국가: ${selectedCountries.join(', ')}`);
			
			const result = await getEconomicCalendar({
				year: year,
				countries: selectedCountries, // 선택된 국가들
				importance_levels: [2, 3] // 중요도 중급, 고급만
			});

			if (result.success && result.data.economic_data) {
				economicEvents = result.data.economic_data;
				console.log(`경제 이벤트 ${economicEvents.length}개 로드됨`);
				
				// 달력 데이터 재생성 (이벤트 포함)
				calendarData = generateCalendarData(year);
			} else {
				throw new Error(result.error || '경제 캘린더 데이터를 가져올 수 없습니다.');
			}
		} catch (error) {
			console.error('경제 캘린더 데이터 요청 실패:', error);
			eventsError = `경제 캘린더 데이터 로딩 실패: ${error instanceof Error ? error.message : String(error)}`;
			economicEvents = [];
			// 에러가 발생해도 달력은 표시 (이벤트 없이)
			calendarData = generateCalendarData(year);
		} finally {
			isLoadingEvents = false;
		}
	};

	// 날짜별 경제 이벤트 찾기
	const getEventsForDate = (year: number, month: number, date: number): EconomicEvent[] => {
		const targetDate = `${year}-${month.toString().padStart(2, '0')}-${date.toString().padStart(2, '0')}`;
		
		return economicEvents.filter(event => {
			// 날짜 형식이 'YYYY-MM-DD'인 경우
			if (event.date_full && event.date_full.includes(targetDate)) {
				return true;
			}
			// 다른 날짜 형식 처리
			if (event.date && event.date === targetDate) {
				return true;
			}
			return false;
		});
	};

	// 선택된 날짜 기준 7일간(이전 3일, 당일, 이후 3일) 이벤트 생성
	const generateWeekEvents = (year: number, month: number, date: number) => {
		const weekEvents = [];
		const today = new Date();
		
		// 연도 경계 처리를 위한 로직
		let startOffset = -3;
		let endOffset = 3;
		
		// 1월 초인 경우 (1일, 2일, 3일)
		if (month === 1) {
			if (date === 1) {
				startOffset = 0;  // 이전 0일
				endOffset = 6;    // 이후 6일
			} else if (date === 2) {
				startOffset = -1; // 이전 1일
				endOffset = 5;    // 이후 5일
			} else if (date === 3) {
				startOffset = -2; // 이전 2일
				endOffset = 4;    // 이후 4일
			}
		}
		
		// 12월 말인 경우 (29일, 30일, 31일)
		if (month === 12) {
			const daysInDecember = new Date(year, 12, 0).getDate(); // 12월의 마지막 날
			if (date === daysInDecember) { // 31일
				startOffset = -6; // 이전 6일
				endOffset = 0;    // 이후 0일
			} else if (date === daysInDecember - 1) { // 30일
				startOffset = -5; // 이전 5일
				endOffset = 1;    // 이후 1일
			} else if (date === daysInDecember - 2) { // 29일
				startOffset = -4; // 이전 4일
				endOffset = 2;    // 이후 2일
			}
		}
		
		// 지정된 범위로 7일간 데이터 생성
		for (let i = startOffset; i <= endOffset; i++) {
			const targetDate = new Date(year, month - 1, date + i);
			const targetYear = targetDate.getFullYear();
			const targetMonth = targetDate.getMonth() + 1;
			const targetDay = targetDate.getDate();
			
			const events = getEventsForDate(targetYear, targetMonth, targetDay);
			const dateString = `${targetYear}-${targetMonth.toString().padStart(2, '0')}-${targetDay.toString().padStart(2, '0')}`;
			
			weekEvents.push({
				date: dateString,
				year: targetYear,
				month: targetMonth,
				day: targetDay,
				events: events,
				isToday: targetYear === today.getFullYear() && targetMonth === (today.getMonth() + 1) && targetDay === today.getDate(),
				isSelected: i === 0 // 선택된 날짜는 i가 0일 때
			});
		}
		
		return weekEvents;
	};

	// 달력 데이터 생성 함수
	const generateCalendarData = (year: number): DateInfo[][] => {
		const data: DateInfo[][] = [];
		
		for (let month = 1; month <= 12; month++) {
			const monthData: DateInfo[] = [];
			const daysInMonth = getDaysInMonth(year, month);
			
			for (let date = 1; date <= daysInMonth; date++) {
				const dayOfWeek = getDayOfWeek(year, month, date);
				const holiday = isHoliday(month, date);
				const events = getEventsForDate(year, month, date);
				
				const dateInfo: DateInfo = {
					date,
					dayOfWeek,
					isWeekend: dayOfWeek === 0 || dayOfWeek === 6,
					isHoliday: holiday.isHoliday || dayOfWeek === 0, // 일요일도 공휴일로 처리
					holidayName: holiday.name,
					events: events
				};
				
				monthData.push(dateInfo);
			}
			
			data.push(monthData);
		}
		
		return data;
	};

	// 날짜 셀의 색상 클래스를 반환하는 함수
	const getDateCellClass = (dateInfo: DateInfo, year: number, month: number): string => {
		const hasEvents = dateInfo.events && dateInfo.events.length > 0;
		const todayCheck = isToday(year, month, dateInfo.date);
		
		let baseClass = "flex flex-col items-center justify-start w-[100px] h-[100px] p-2 text-sm border rounded-xl transition-all duration-300 cursor-pointer relative backdrop-blur-sm shadow-lg overflow-visible";
		
		// 호버 시 효과
		baseClass += " hover:shadow-xl hover:scale-105";
		
		// 오늘 날짜 강조 - 부드러운 애니메이션으로 개선
		if (todayCheck) {
			baseClass += " ring-4 ring-yellow-400 ring-offset-4 ring-offset-slate-900 shadow-2xl shadow-yellow-400/50 gentle-glow border-yellow-400/60";
			// 오늘 날짜는 배경도 더 밝게
			if (dateInfo.isHoliday) {
				return baseClass + " bg-gradient-to-br from-yellow-500/40 via-orange-500/30 to-red-500/40 text-yellow-100 hover:from-yellow-500/50 hover:via-orange-500/40 hover:to-red-500/50";
			} else if (dateInfo.dayOfWeek === 6) { // 토요일
				return baseClass + " bg-gradient-to-br from-yellow-500/40 via-amber-500/30 to-orange-500/40 text-yellow-100 hover:from-yellow-500/50 hover:via-amber-500/40 hover:to-orange-500/50";
			} else {
				return baseClass + " bg-gradient-to-br from-yellow-500/40 via-amber-500/30 to-orange-500/40 text-yellow-100 hover:from-yellow-500/50 hover:via-amber-500/40 hover:to-orange-500/50";
			}
		} else {
			baseClass += " border-white/5";
		}
		
		if (dateInfo.isHoliday) {
			return baseClass + " bg-gradient-to-br from-red-500/30 via-red-400/20 to-pink-500/30 text-red-100 hover:from-red-500/40 hover:via-red-400/30 hover:to-pink-500/40 border-red-400/20 hover:border-red-300/40";
		} else if (dateInfo.dayOfWeek === 6) { // 토요일
			return baseClass + " bg-gradient-to-br from-blue-500/30 via-blue-400/20 to-cyan-500/30 text-blue-100 hover:from-blue-500/40 hover:via-blue-400/30 hover:to-cyan-500/40 border-blue-400/20 hover:border-blue-300/40";
		} else {
			return baseClass + " bg-gradient-to-br from-slate-700/40 via-slate-600/30 to-slate-700/40 text-slate-100 hover:from-slate-600/50 hover:via-slate-500/40 hover:to-slate-600/50 border-slate-500/20 hover:border-slate-400/40";
		}
	};

	// 월 헤더 셀 클래스
	const getMonthHeaderClass = (month: number, year: number): string => {
		const today = new Date();
		const currentMonth = today.getMonth() + 1; // 1-12
		const todayYear = today.getFullYear();
		
		const isCurrentMonth = year === todayYear && month === currentMonth;
		
		let baseClass = "sticky left-0 z-10 text-white font-bold text-base border border-white/10 rounded-xl w-[100px] h-[100px] flex items-center justify-center shadow-xl backdrop-blur-sm transition-all duration-300";
		
		if (isCurrentMonth) {
			return baseClass + " bg-gradient-to-br from-yellow-600 via-orange-600 to-red-600 ring-4 ring-yellow-400 ring-offset-2 ring-offset-slate-900 shadow-2xl shadow-yellow-400/50 subtle-border border-yellow-400/60";
		} else {
			return baseClass + " bg-gradient-to-br from-indigo-600 via-purple-600 to-blue-600";
		}
	};

	// 중요도에 따른 이벤트 색상 반환
	const getEventColor = (importance_level: number): string => {
		switch (importance_level) {
			case 3: return 'bg-red-500/70 text-red-100'; // 고중요도
			case 2: return 'bg-yellow-500/70 text-yellow-100'; // 중중요도
			case 1: return 'bg-blue-500/70 text-blue-100'; // 저중요도
			default: return 'bg-gray-500/70 text-gray-100';
		}
	};

	// 특정 날짜를 선택하는 함수 (재사용 가능)
	const selectDate = (year: number, month: number, date: number) => {
		selectedDateInfo = {
			year: year,
			month: month,
			date: date,
			weekEvents: generateWeekEvents(year, month, date)
		};
		console.log(`날짜 선택: ${year}년 ${month}월 ${date}일`);
	};

	// 오늘 날짜로 스크롤 이동하는 함수 (선택 로직 제거)
	const scrollToToday = () => {
		if (!scrollContainer) return;
		
		const today = new Date();
		const currentMonth = today.getMonth() + 1; // 1-12
		const currentDate = today.getDate(); // 1-31
		
		// 각 셀의 크기: 100px + gap 2px = 102px
		const cellWidth = 102;
		const cellHeight = 102;
		
		// 월 헤더를 고려한 x 좌표 (월 헤더 100px + gap 8px + 날짜 인덱스 * cellWidth)
		const targetX = 108 + (currentDate - 1) * cellWidth;
		// 날짜 헤더를 고려한 y 좌표 (날짜 헤더 60px + padding + 월 인덱스 * cellHeight)
		const targetY = 70 + (currentMonth - 1) * cellHeight;
		
		// 화면 중앙에 오도록 조정
		const containerRect = scrollContainer.getBoundingClientRect();
		const scrollX = Math.max(0, targetX - containerRect.width / 2);
		const scrollY = Math.max(0, targetY - containerRect.height / 2);
		
		scrollContainer.scrollTo({
			left: scrollX,
			top: scrollY,
			behavior: 'smooth'
		});
		
		console.log(`오늘 날짜로 스크롤: ${currentMonth}월 ${currentDate}일 (${scrollX}, ${scrollY})`);
	};

	// 1월 1일로 스크롤 이동하는 함수
	const scrollToJanuary1st = () => {
		if (!scrollContainer) return;
		
		scrollContainer.scrollTo({
			left: 0,
			top: 0,
			behavior: 'smooth'
		});
		
		console.log('1월 1일로 스크롤 이동');
	};

	// 특정 날짜로 스크롤 이동하는 함수
	const scrollToDate = (year: number, month: number, date: number) => {
		if (!scrollContainer) return;
		
		// 각 셀의 크기: 100px + gap 2px = 102px
		const cellWidth = 102;
		const cellHeight = 102;
		
		// 월 헤더를 고려한 x 좌표 (월 헤더 100px + gap 8px + 날짜 인덱스 * cellWidth)
		const targetX = 108 + (date - 1) * cellWidth;
		// 날짜 헤더를 고려한 y 좌표 (날짜 헤더 60px + padding + 월 인덱스 * cellHeight)
		const targetY = 70 + (month - 1) * cellHeight;
		
		// 화면 중앙에 오도록 조정
		const containerRect = scrollContainer.getBoundingClientRect();
		const scrollX = Math.max(0, targetX - containerRect.width / 2);
		const scrollY = Math.max(0, targetY - containerRect.height / 2);
		
		scrollContainer.scrollTo({
			left: scrollX,
			top: scrollY,
			behavior: 'smooth'
		});
		
		console.log(`${month}월 ${date}일로 스크롤: (${scrollX}, ${scrollY})`);
	};

	// 국가 토글 함수
	const toggleCountry = (countryCode: string) => {
		if (selectedCountries.includes(countryCode)) {
			// 국가 제거
			selectedCountries = selectedCountries.filter(code => code !== countryCode);
		} else {
			// 국가 추가
			selectedCountries = [...selectedCountries, countryCode];
		}
		
		// 조회 조건 변경 시 모달 닫기
		selectedDateInfo = null;
		
		// 국가 선택이 변경되면 새로운 데이터 로드
		fetchEconomicCalendar(currentYear);
	};

	// 전체 선택 토글 함수
	const toggleAllCountries = () => {
		if (isAllSelected) {
			// 전체 선택 해제
			selectedCountries = [];
		} else {
			// 전체 선택
			selectedCountries = availableCountries.map(country => country.code);
		}
		
		// 조회 조건 변경 시 모달 닫기
		selectedDateInfo = null;
		
		// 국가 선택이 변경되면 새로운 데이터 로드
		fetchEconomicCalendar(currentYear);
	};

	// 오늘 날짜를 자동으로 선택하는 함수
	const autoSelectToday = () => {
		const today = new Date();
		const todayYear = today.getFullYear();
		const todayMonth = today.getMonth() + 1; // 1-12
		const todayDate = today.getDate(); // 1-31
		
		// 현재 보고 있는 연도가 오늘 날짜와 같은 연도인지 확인
		if (currentYear === todayYear) {
			// 오늘 날짜를 자동으로 선택
			selectDate(todayYear, todayMonth, todayDate);
			console.log(`오늘 날짜 자동 선택: ${todayYear}년 ${todayMonth}월 ${todayDate}일`);
		}
	};

	// 페이지 마운트 시 초기화
	onMount(() => {
		console.log('연간 달력 페이지 로드됨');
		calendarData = generateCalendarData(currentYear);
		// 경제 캘린더 데이터 로드
		fetchEconomicCalendar(currentYear);
		
		// 데이터 로딩 후 먼저 선택하고, 모달이 뜬 후 스크롤
		setTimeout(() => {
			const today = new Date();
			const todayYear = today.getFullYear();
			
			if (currentYear === todayYear) {
				// 현재 연도라면 먼저 오늘 날짜 선택 (모달 표시)
				autoSelectToday();
				// 모달이 뜬 후 스크롤 이동
				setTimeout(() => {
					scrollToToday();
				}, 200);
			} else {
				// 다른 연도라면 1월 1일로 스크롤만
				scrollToJanuary1st();
			}
		}, 100);
	});

	// 연도 변경 함수
	const changeYear = (delta: number) => {
		// 조회 조건 변경 시 모달 닫기
		selectedDateInfo = null;
		
		currentYear += delta;
		calendarData = generateCalendarData(currentYear);
		// 새로운 연도의 경제 캘린더 데이터 로드
		fetchEconomicCalendar(currentYear);
		
		// 연도 변경 시 스크롤 위치 결정
		setTimeout(() => {
			scrollToAppropriateDate();
		}, 100);
	};

	// 적절한 날짜로 스크롤하는 함수 (연도 변경 시 사용)
	const scrollToAppropriateDate = () => {
		if (!scrollContainer) return;
		
		const today = new Date();
		const todayYear = today.getFullYear();
		
		// 현재 보고 있는 연도가 오늘 날짜와 같은 연도인지 확인
		if (currentYear === todayYear) {
			// 같은 연도면 먼저 오늘 날짜 선택 (모달 표시)
			autoSelectToday();
			// 모달이 뜬 후 스크롤 이동
			setTimeout(() => {
				scrollToToday();
			}, 200);
		} else {
			// 다른 연도면 1월 1일로 스크롤하고 선택 해제
			scrollToJanuary1st();
			selectedDateInfo = null;
		}
		
		console.log(`연도 변경: ${currentYear}년 ${currentYear === todayYear ? '(오늘 날짜 선택 후 스크롤 이동)' : '(1월 1일로 이동, 선택 해제)'}`);
	};
</script>

<svelte:head>
	<title>연간 경제 달력 - FinanceChart</title>
	<meta name="description" content="연간 경제 이벤트 캘린더" />
</svelte:head>

<div class="w-screen h-screen bg-gradient-to-br from-slate-950 via-indigo-950 to-purple-950 relative overflow-hidden">
	<!-- 고급 배경 데코레이션 -->
	<div class="absolute inset-0 bg-[radial-gradient(circle_at_20%_80%,_rgba(120,119,198,0.3),_transparent_50%),radial-gradient(circle_at_80%_20%,_rgba(255,119,198,0.15),_transparent_50%),radial-gradient(circle_at_40%_40%,_rgba(120,200,255,0.2),_transparent_50%)] pointer-events-none"></div>
	<div class="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,_rgba(99,102,241,0.1)_1px,_transparent_0)] bg-[size:40px_40px] pointer-events-none"></div>
	
	<!-- 움직이는 배경 오브 -->
	<div class="absolute top-0 right-0 w-96 h-96 bg-gradient-to-r from-indigo-400/30 to-purple-400/30 rounded-full blur-3xl translate-x-1/3 -translate-y-1/3 animate-pulse"></div>
	<div class="absolute bottom-0 left-0 w-96 h-96 bg-gradient-to-r from-blue-400/20 to-cyan-400/20 rounded-full blur-3xl -translate-x-1/3 translate-y-1/3 animate-pulse"></div>
	<div class="absolute top-1/2 left-1/2 w-64 h-64 bg-gradient-to-r from-pink-400/15 to-violet-400/15 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2 animate-pulse"></div>

	<div class="relative z-10 h-full flex flex-col">
		<!-- 헤더 영역 -->
		<div class="p-8 border-b border-white/10 backdrop-blur-xl bg-white/5 flex-shrink-0 shadow-2xl">
			<div class="flex items-center justify-between">
				<!-- 제목 영역 -->
				<div class="flex items-center space-x-6">
					<div class="relative">
						<div class="absolute inset-0 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-3xl blur-lg opacity-70 animate-pulse"></div>
						<div class="relative flex items-center justify-center w-16 h-16 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-3xl shadow-2xl">
							<svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
							</svg>
						</div>
					</div>
					<div>
						<h1 class="text-4xl font-black bg-gradient-to-r from-white via-indigo-200 to-purple-200 bg-clip-text text-transparent tracking-tight">
							{`${currentYear}년 경제 달력`}
						</h1>
						<p class="text-slate-300 text-base font-medium mt-1 tracking-wide">Annual Economic Calendar</p>
					</div>
				</div>

				<!-- 연도 선택 영역 -->
				<div class="flex items-center space-x-6">
					<button 
						class="group relative flex items-center justify-center w-12 h-12 bg-gradient-to-r from-slate-700/80 to-slate-600/80 hover:from-slate-600/90 hover:to-slate-500/90 rounded-2xl transition-all duration-300 hover:scale-110 shadow-lg hover:shadow-xl backdrop-blur-sm border border-white/10"
						on:click={() => changeYear(-1)}
					>
						<div class="absolute inset-0 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
						<svg class="relative z-10 w-6 h-6 text-slate-200 group-hover:text-white transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"></path>
						</svg>
					</button>
					
					<div class="relative">
						<div class="absolute inset-0 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded-3xl blur-xl"></div>
						<div class="relative bg-gradient-to-r from-slate-800/90 to-slate-700/90 backdrop-blur-xl rounded-3xl px-8 py-4 border border-white/20 shadow-2xl">
							<span class="text-3xl font-black bg-gradient-to-r from-white to-indigo-200 bg-clip-text text-transparent">{currentYear}</span>
						</div>
					</div>
					
					<button 
						class="group relative flex items-center justify-center w-12 h-12 bg-gradient-to-r from-slate-700/80 to-slate-600/80 hover:from-slate-600/90 hover:to-slate-500/90 rounded-2xl transition-all duration-300 hover:scale-110 shadow-lg hover:shadow-xl backdrop-blur-sm border border-white/10"
						on:click={() => changeYear(1)}
					>
						<div class="absolute inset-0 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
						<svg class="relative z-10 w-6 h-6 text-slate-200 group-hover:text-white transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"></path>
						</svg>
					</button>
				</div>
			</div>
		</div>

		<!-- 범례 -->
		<div class="px-6 py-4 border-b border-white/10 backdrop-blur-xl bg-white/5 flex-shrink-0 shadow-lg">
			<div class="space-y-3">
				<!-- 국가 선택 섹션 -->
				<div>
					<h3 class="text-sm font-bold text-slate-200 mb-2">국가 선택</h3>
					
					<div class="flex flex-wrap gap-2">
						<!-- 전체 선택 버튼 -->
						<button
							class="group relative flex items-center space-x-1.5 px-3 py-1.5 bg-gradient-to-r from-slate-700/80 to-slate-600/80 hover:from-slate-600/90 hover:to-slate-500/90 rounded-lg transition-all duration-300 hover:scale-105 shadow-md backdrop-blur-sm border border-white/10 {isAllSelected ? 'from-indigo-600/80 to-purple-600/80 hover:from-indigo-500/90 hover:to-purple-500/90' : ''}"
							on:click={toggleAllCountries}
						>
							<div class="w-3 h-3 rounded border-2 border-slate-300 flex items-center justify-center transition-all duration-200 {isAllSelected ? 'bg-white border-white' : 'bg-transparent'}">
								{#if isAllSelected}
									<svg class="w-2 h-2 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
										<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
									</svg>
								{/if}
							</div>
							<span class="text-slate-200 font-medium text-xs">전체</span>
						</button>

						<!-- 국가별 선택 버튼들 -->
						{#each availableCountries as country}
							<button
								class="group relative flex items-center space-x-1.5 px-2.5 py-1.5 bg-gradient-to-r from-slate-700/60 to-slate-600/60 hover:from-slate-600/70 hover:to-slate-500/70 rounded-lg transition-all duration-300 hover:scale-105 shadow-md backdrop-blur-sm border border-white/10 {selectedCountries.includes(country.code) ? 'from-indigo-600/70 to-purple-600/70 hover:from-indigo-500/80 hover:to-purple-500/80 border-indigo-400/30' : 'hover:border-slate-400/30'}"
								on:click={() => toggleCountry(country.code)}
							>
								<span class="text-sm">{country.flag}</span>
								<span class="text-xs font-medium text-slate-200">{country.name}</span>
								{#if selectedCountries.includes(country.code)}
									<div class="w-1.5 h-1.5 bg-green-400 rounded-full shadow-sm"></div>
								{/if}
							</button>
						{/each}
					</div>
				</div>

				<!-- 기존 범례와 상태 -->
				<div class="flex items-center justify-between">
					<!-- 기존 범례 -->
					<div class="flex items-center space-x-6 text-sm">
						<div class="flex items-center space-x-2 group">
							<div class="w-4 h-4 bg-gradient-to-br from-slate-700/40 via-slate-600/30 to-slate-700/40 border border-slate-500/30 rounded shadow-sm group-hover:scale-110 transition-transform duration-200"></div>
							<span class="text-slate-200 font-medium text-xs">평일</span>
						</div>
						<div class="flex items-center space-x-2 group">
							<div class="w-4 h-4 bg-gradient-to-br from-blue-500/30 via-blue-400/20 to-cyan-500/30 border border-blue-400/30 rounded shadow-sm group-hover:scale-110 transition-transform duration-200"></div>
							<span class="text-blue-200 font-medium text-xs">토요일</span>
						</div>
						<div class="flex items-center space-x-2 group">
							<div class="w-4 h-4 bg-gradient-to-br from-red-500/30 via-red-400/20 to-pink-500/30 border border-red-400/30 rounded shadow-sm group-hover:scale-110 transition-transform duration-200"></div>
							<span class="text-red-200 font-medium text-xs">공휴일</span>
						</div>
						
						<!-- 중요도 범례도 같이 표시 -->
						<div class="flex items-center space-x-4 border-l border-white/20 pl-4">
							<div class="flex items-center space-x-1">
								<div class="w-3 h-3 bg-red-500/70 rounded border border-red-400/30"></div>
								<span class="text-red-200 text-xs">고중요도</span>
 							</div>
							<div class="flex items-center space-x-1">
								<div class="w-3 h-3 bg-yellow-500/70 rounded border border-yellow-400/30"></div>
								<span class="text-yellow-200 text-xs">중중요도</span>
 							</div>
						</div>
					</div>
					
					<!-- 경제 캘린더 상태 -->
					<div class="flex items-center space-x-3">
						{#if isLoadingEvents}
							<div class="flex items-center space-x-2">
								<div class="animate-spin rounded-full h-3 w-3 border-b-2 border-indigo-400"></div>
								<span class="text-slate-300 text-xs">로딩 중...</span>
							</div>
						{:else if selectedCountries.length === 0}
							<div class="flex items-center space-x-2">
								<div class="w-3 h-3 bg-orange-500 rounded-full animate-pulse"></div>
								<span class="text-orange-300 text-xs">국가를 선택해주세요</span>
							</div>
						{:else if eventsError}
							<div class="flex items-center space-x-2">
								<div class="w-3 h-3 bg-red-500 rounded-full"></div>
								<span class="text-red-300 text-xs">로딩 실패</span>
							</div>
						{:else}
							<span class="text-slate-300 text-xs">{economicEvents.length}개 이벤트 ({selectedCountries.length}개 국가)</span>
						{/if}
					</div>
				</div>
			</div>
		</div>

		<!-- Year Glance 스타일 메인 달력 -->
		<div class="flex-1 {isLoadingEvents ? '' : 'overflow-auto'} bg-black/20 backdrop-blur-sm px-2 relative" bind:this={scrollContainer}>
			<!-- 로딩 오버레이 - 보이는 화면 영역 기준 중앙 정렬 -->
			{#if isLoadingEvents}
				<div class="absolute inset-0 z-50 bg-slate-900/80 backdrop-blur-md">
					<div class="fixed top-1/3 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-[60] bg-gradient-to-br from-slate-800/90 to-slate-700/90 backdrop-blur-xl rounded-2xl border border-white/20 shadow-2xl p-8 text-center max-w-md mx-4">
						<!-- 로딩 스피너 -->
						<div class="relative mb-6">
							<div class="w-16 h-16 mx-auto">
								<!-- 외부 링 -->
								<div class="absolute inset-0 border-4 border-indigo-500/30 rounded-full"></div>
								<!-- 회전하는 링 -->
								<div class="absolute inset-0 border-4 border-transparent border-t-indigo-500 border-r-purple-500 rounded-full animate-spin"></div>
								<!-- 내부 펄스 -->
								<div class="absolute inset-2 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-full animate-pulse"></div>
							</div>
						</div>
						
						<!-- 로딩 텍스트 -->
						<h3 class="text-xl font-bold text-white mb-2">
							경제 캘린더 로딩 중
						</h3>
						<p class="text-slate-300 text-sm mb-4">
							{selectedCountries.length}개 국가의 {currentYear}년 경제 이벤트를 가져오고 있습니다...
						</p>
						
						<!-- 진행 상태 바 -->
						<div class="w-full bg-slate-700/50 rounded-full h-2 overflow-hidden">
							<div class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full animate-pulse"></div>
						</div>
						
						<!-- 로딩 도트 애니메이션 -->
						<div class="flex justify-center items-center space-x-1 mt-4">
							<div class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></div>
							<div class="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
							<div class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
						</div>
					</div>
				</div>
			{/if}

			<div class="min-w-max"
				class:pointer-events-none={isLoadingEvents}
				class:opacity-50={isLoadingEvents}
			>
				<!-- 날짜 헤더 (1-31) -->
				<div class="sticky top-0 z-20 bg-gradient-to-r from-slate-900/95 via-indigo-900/95 to-slate-900/95 backdrop-blur-xl border-b border-white/20 shadow-2xl">
					<div class="flex py-2 gap-2">
						<!-- 월 헤더 칸 (빈 공간) -->
						<div class="w-[100px] h-[60px] bg-gradient-to-br from-slate-800/90 to-slate-700/90 border border-white/20 rounded-xl p-3 flex items-center justify-center shadow-xl backdrop-blur-sm">
							<span class="text-slate-300 text-sm font-bold tracking-wider">MONTH</span>
						</div>
						
						<!-- 1-31 날짜 헤더 -->
						{#each Array(31) as _, index}
							<div class="w-[100px] h-[60px] p-2 text-center border border-white/10 bg-gradient-to-br from-slate-700/50 via-slate-600/40 to-slate-700/50 rounded-xl flex items-center justify-center shadow-lg backdrop-blur-sm hover:bg-slate-600/60 transition-all duration-300 hover:scale-105">
								<span class="text-slate-100 text-base font-bold">{index + 1}</span>
							</div>
						{/each}
					</div>
				</div>

				<!-- 12개월 행 -->
				<div class="space-y-2 pt-2">
					{#each calendarData as monthData, monthIndex}
						<div class="flex gap-2 hover:bg-white/5 rounded-2xl transition-all duration-300">
							<!-- 월 이름 헤더 -->
							<div class={getMonthHeaderClass(monthIndex + 1, currentYear)}>
								<div class="text-center">
									<div class="font-black text-xl tracking-wide">{monthNames[monthIndex]}</div>
									<!-- 현재 월 표시 - 더 자연스럽게 -->
									{#if currentYear === new Date().getFullYear() && (monthIndex + 1) === (new Date().getMonth() + 1)}
										<div class="text-xs font-black text-yellow-200 mt-1 bg-yellow-500/20 px-2 py-0.5 rounded-full border border-yellow-400/40">
											THIS MONTH
										</div>
									{:else}
										<div class="text-sm text-indigo-200 mt-1 font-medium">{monthData.length}일</div>
									{/if}
								</div>
							</div>
							
							<!-- 해당 월의 모든 날짜 -->
							{#each Array(31) as _, dayIndex}
								{#if dayIndex < monthData.length}
									<!-- 실제 날짜가 있는 경우 -->
									<!-- svelte-ignore a11y-click-events-have-key-events -->
									<!-- svelte-ignore a11y-no-static-element-interactions -->
									<div 
										class={getDateCellClass(monthData[dayIndex], currentYear, monthIndex + 1)}
										on:click={() => {
											// 선택된 날짜 설정
											selectDate(currentYear, monthIndex + 1, monthData[dayIndex].date);
											
											// 클릭한 날짜로 스크롤 이동
											setTimeout(() => {
												scrollToDate(currentYear, monthIndex + 1, monthData[dayIndex].date);
											}, 100);
											
											console.log(`클릭: ${monthIndex + 1}월 ${monthData[dayIndex].date}일`);
										}}
										title={monthData[dayIndex].holidayName || `${monthIndex + 1}월 ${monthData[dayIndex].date}일`}
									>
										<!-- 날짜 번호 -->
										<div class="font-black text-lg text-center mb-1 tracking-wide relative z-10 flex-shrink-0">
											{monthData[dayIndex].date}
											<!-- 오늘 날짜 표시 - 더 눈에 띄게 -->
											{#if isToday(currentYear, monthIndex + 1, monthData[dayIndex].date)}
												<div class="absolute -top-2 -right-2 bg-gradient-to-r from-yellow-400 to-orange-400 text-slate-900 text-xs font-black px-1.5 py-0.5 rounded-full shadow-lg animate-bounce border-2 border-white">
													TODAY
												</div>
											{/if}
										</div>
										
										<!-- 공휴일명 -->
										{#if monthData[dayIndex].holidayName}
											<div class="text-xs text-center font-bold bg-red-500/30 px-1 py-0.5 rounded border border-red-300/30 backdrop-blur-sm relative z-10 mb-1 flex-shrink-0">
												{monthData[dayIndex].holidayName}
											</div>
										{/if}
										
										<!-- 경제 이벤트들 -->
										{#if monthData[dayIndex].events && monthData[dayIndex].events.length > 0}
											<!-- 기본 이벤트 표시 (3개만) -->
											<div class="flex-1 w-full overflow-y-auto overflow-x-hidden space-y-1 scrollbar-thin">
												{#each monthData[dayIndex].events.slice(0, 3) as event, eventIndex}
													<div 
														class="text-xs px-1 py-0.5 rounded text-center font-medium border {getEventColor(event.importance_level)} transition-all duration-200"
														title="{event.event_name} ({event.time}) - {event.country_name}"
													>
														<!-- 이벤트명 (축약) -->
														<div class="truncate">
															{event.event_name.length > 10 ? event.event_name.substring(0, 10) + '...' : event.event_name}
														</div>
														<!-- 시간 -->
														{#if event.time}
															<div class="text-xs opacity-80">
																{event.time}
															</div>
														{/if}
													</div>
												{/each}
												
												<!-- 더 많은 이벤트가 있는 경우 -->
												{#if monthData[dayIndex].events.length > 3}
													<div class="text-xs text-center text-slate-400 font-medium">
														+{monthData[dayIndex].events.length - 3}개 더
													</div>
												{/if}
											</div>
											
										{/if}
										
										<!-- 글로우 효과 -->
										<div class="absolute inset-0 bg-gradient-to-r from-white/5 via-transparent to-white/5 opacity-0 hover:opacity-100 transition-opacity duration-300 rounded-xl pointer-events-none"></div>
									</div>
								{:else}
									<!-- 빈 날짜 칸 -->
									<div class="w-[100px] h-[100px] border border-white/5 bg-gradient-to-br from-slate-900/20 to-slate-800/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
										<span class="text-slate-600 text-lg font-light">—</span>
									</div>
								{/if}
							{/each}
						</div>
					{/each}
				</div>
			</div>
		</div>
		<!-- 선택된 날짜 기준 7일간 이벤트 표시 (하단 영역) -->
		{#if selectedDateInfo}
			<div class="border-t p-4 border-white/10 bg-gradient-to-r from-slate-900/95 via-indigo-900/95 to-slate-900/95 backdrop-blur-xl flex-shrink-0 shadow-2xl max-h-80">
				<div class="">
					<!-- 헤더 -->
					<div class="flex items-center justify-between mb-4">
						<div class="flex items-center space-x-3">
							<div class="w-6 h-6 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
								<svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
								</svg>
							</div>
							<h3 class="text-xl font-bold text-white">
								{selectedDateInfo.year}년 {selectedDateInfo.month}월 {selectedDateInfo.date}일 주간 이벤트
							</h3>
						</div>
						<button 
							class="text-slate-400 hover:text-white transition-colors duration-200"
							on:click={() => selectedDateInfo = null}
						>
							<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
							</svg>
						</button>
					</div>
					
					<!-- 7일간 이벤트 그리드 -->
					<div class="grid grid-cols-7 gap-4">
						{#each selectedDateInfo.weekEvents as dayInfo}
							<div class="relative">
								<!-- 날짜 헤더 -->
								<div class="text-center mb-3">
									<div class="text-sm text-slate-400 font-medium">
										{dayInfo.month}월 {dayInfo.day}일
									</div>
									<div class="text-xs text-slate-500 mt-1">
										{['일', '월', '화', '수', '목', '금', '토'][new Date(dayInfo.year, dayInfo.month - 1, dayInfo.day).getDay()]}
									</div>
									{#if dayInfo.isToday}
										<div class="w-2 h-2 bg-yellow-400 rounded-full mx-auto mt-1 animate-pulse"></div>
									{/if}
									{#if dayInfo.isSelected}
										<div class="w-full h-1 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full mt-1"></div>
									{/if}
								</div>
								
								<!-- 이벤트 목록 -->
								<div class="space-y-2 max-h-48 overflow-y-auto scrollbar-thin">
									{#if dayInfo.events.length === 0}
										<div class="text-center text-slate-500 text-xs py-6 border border-slate-700/30 rounded-lg bg-slate-800/20">
											<div class="mb-1">📅</div>
											<div>이벤트 없음</div>
										</div>
									{:else}
										{#each dayInfo.events as event}
											<div class="p-2 rounded-lg border {getEventColor(event.importance_level)} transition-all duration-200 hover:bg-white/5 hover:border-opacity-80 cursor-pointer">
												<!-- 이벤트명 (전체 표시) -->
												<div class="text-xs font-bold mb-1 leading-tight">
													{event.event_name}
												</div>
												
												<!-- 시간과 국가 -->
												<div class="flex items-center justify-between text-xs opacity-90">
													{#if event.time}
														<span class="font-medium">{event.time}</span>
													{/if}
													<span class="text-xs">{event.country_name}</span>
												</div>
												
												<!-- 중요도 표시 -->
												<div class="flex items-center justify-between mt-1">
													<div class="flex space-x-1">
														{#each Array(event.importance_level) as _}
															<div class="w-1 h-1 bg-white rounded-full opacity-80"></div>
														{/each}
													</div>
													{#if event.actual || event.forecast}
														<div class="text-xs font-medium">
															{#if event.actual}
																<span class="text-green-300">{event.actual}</span>
															{:else if event.forecast}
																<span class="text-blue-300">{event.forecast}</span>
															{/if}
														</div>
													{/if}
												</div>
											</div>
										{/each}
									{/if}
								</div>
							</div>
						{/each}
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	/* 고급 스크롤바 스타일링 */
	:global(::-webkit-scrollbar) {
		width: 8px;
		height: 8px;
	}

	:global(::-webkit-scrollbar-track) {
		background: rgba(0, 0, 0, 0.4);
		border-radius: 6px;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	:global(::-webkit-scrollbar-thumb) {
		background: linear-gradient(135deg, rgba(99, 102, 241, 0.8), rgba(139, 92, 246, 0.8));
		border-radius: 6px;
		border: 1px solid rgba(255, 255, 255, 0.1);
		box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
	}

	:global(::-webkit-scrollbar-thumb:hover) {
		background: linear-gradient(135deg, rgba(99, 102, 241, 1), rgba(139, 92, 246, 1));
		box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
	}

	:global(::-webkit-scrollbar-corner) {
		background: rgba(0, 0, 0, 0.4);
		border-radius: 6px;
	}

	/* 날짜 셀 내부 이벤트 영역 전용 스크롤바 스타일 */
	.scrollbar-thin::-webkit-scrollbar {
		width: 6px;
		height: 6px;
	}

	.scrollbar-thin::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.2);
		border-radius: 4px;
		border: none;
	}

	.scrollbar-thin::-webkit-scrollbar-thumb {
		background: linear-gradient(135deg, rgba(99, 102, 241, 0.6), rgba(139, 92, 246, 0.6));
		border-radius: 4px;
		border: none;
		box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
	}

	.scrollbar-thin::-webkit-scrollbar-thumb:hover {
		background: linear-gradient(135deg, rgba(99, 102, 241, 0.8), rgba(139, 92, 246, 0.8));
		box-shadow: 0 3px 12px rgba(99, 102, 241, 0.4);
	}

	/* 글로벌 애니메이션 */
	:global(body) {
		font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
	}

	/* 커스텀 애니메이션 키프레임 */
	@keyframes float {
		0%, 100% { transform: translateY(0px) rotate(0deg); }
		33% { transform: translateY(-10px) rotate(1deg); }
		66% { transform: translateY(5px) rotate(-1deg); }
	}

	.float-animation {
		animation: float 6s ease-in-out infinite;
	}

	/* 부드러운 글로우 애니메이션 (오늘 날짜용) */
	@keyframes gentle-glow {
		0%, 100% { 
			box-shadow: 0 0 20px rgba(251, 191, 36, 0.3), 0 0 40px rgba(251, 191, 36, 0.1);
		}
		50% { 
			box-shadow: 0 0 25px rgba(251, 191, 36, 0.4), 0 0 50px rgba(251, 191, 36, 0.15);
		}
	}

	.gentle-glow {
		animation: gentle-glow 3s ease-in-out infinite;
	}

	/* 부드러운 보더 애니메이션 (이번 달용) */
	@keyframes subtle-border {
		0%, 100% { 
			border-color: rgba(251, 191, 36, 0.6);
			box-shadow: 0 0 15px rgba(251, 191, 36, 0.2);
		}
		50% { 
			border-color: rgba(251, 191, 36, 0.8);
			box-shadow: 0 0 20px rgba(251, 191, 36, 0.3);
		}
	}

	.subtle-border {
		animation: subtle-border 4s ease-in-out infinite;
	}
</style>