<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { getStockCalendar, getKoreanHolidays } from '$lib/api-connector/FinanceApi';

	// 현재 연도 (2025년으로 변경해서 테스트)
	let currentYear = 2025;

	// 월 이름 배열
	const monthNames = [
		'1월', '2월', '3월', '4월', '5월', '6월',
		'7월', '8월', '9월', '10월', '11월', '12월'
	];

	// 주식 이벤트 타입 목록 정의
	const availableEventTypes = [
		{ code: 'earnings', name: '실적발표', icon: '📊', color: 'from-green-500 to-emerald-500' },
		{ code: 'ir', name: 'IR 이벤트', icon: '🎤', color: 'from-blue-500 to-cyan-500' },
		{ code: 'listing', name: '신규상장', icon: '🚀', color: 'from-purple-500 to-violet-500' },
		{ code: 'capital', name: '자본변동', icon: '💰', color: 'from-yellow-500 to-amber-500' },
		{ code: 'dividend', name: '배당', icon: '💎', color: 'from-indigo-500 to-blue-500' },
		{ code: 'split', name: '액면분할', icon: '✂️', color: 'from-teal-500 to-cyan-500' },
		{ code: 'merger', name: '합병/분할', icon: '🔄', color: 'from-red-500 to-pink-500' },
		{ code: 'namechange', name: '상호변경', icon: '📝', color: 'from-gray-500 to-slate-500' }
	];

	// 선택된 이벤트 타입들 (기본값 확장 - 더 많은 이벤트 표시)
	let selectedEventTypes: string[] = ['earnings', 'ir', 'listing', 'capital', 'dividend', 'split', 'merger', 'namechange'];
	
	// 전체 선택 상태 (reactive)
	$: isAllSelected = selectedEventTypes.length === availableEventTypes.length;

	// 종목 검색 관련 변수
	let searchQuery = '';
	
	// 검색 결과 계산 (reactive)
	$: searchResultCount = searchQuery.trim() === '' ? stockEvents.length : 
		stockEvents.filter(event => {
			const query = searchQuery.toLowerCase().trim();
			return event.company_name.toLowerCase().includes(query) ||
            event.stock_code.toLowerCase().includes(query) ||
            event.event_name.toLowerCase().includes(query);
		}).length;

	// 한국 공휴일 데이터 (API에서 가져올 데이터)
	let koreanHolidays: Record<string, string> = {};

	// 주식 일정 데이터
	let stockEvents: StockEvent[] = [];
	let isLoadingEvents = false;
	let eventsError = '';

	// 검색어 디바운싱 변수
	let searchDebounceTimer: any = null;

	// 즉시 시각적 피드백을 위한 상태 관리 (호환성을 위해 유지, 실제로는 사용하지 않음)
	let clickedButton: string | null = null; // 클릭된 버튼 추적
	let isProcessing = false; // 전역 처리 상태
	let buttonLoadingStates: Record<string, boolean> = {}; // 버튼별 로딩 상태

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
			events: StockEvent[];
			isToday: boolean;
			isSelected: boolean;
		}>;
	} | null = null;

	// 선택된 이벤트 상세정보
	let selectedEventDetail: StockEvent | null = null;

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

	// 주식 일정 데이터 가져오기
	const fetchStockCalendar = async (year: number) => {
		isLoadingEvents = true;
		eventsError = '';

    await tick();
		
		try {
			const result = await getStockCalendar({
				year: year
			});

			if (result.success && result.data.stock_events) {
				stockEvents = result.data.stock_events;
			} else {
				throw new Error(result.error || '주식 일정 데이터를 가져올 수 없습니다.');
			}
		} catch (error) {
			eventsError = `주식 일정 데이터 로딩 실패: ${error instanceof Error ? error.message : String(error)}`;
			stockEvents = [];
		} finally {
			// 데이터 로딩 완료 후 달력 데이터 생성 (필터 상태에 관계없이 항상 생성)
			calendarData = generateCalendarData(year);
			isLoadingEvents = false;
		}
	};

	// 검색어 디바운싱 (300ms 지연으로 타이핑 성능 최적화)
	const debouncedSearch = (query: string) => {
		if (searchDebounceTimer) {
			clearTimeout(searchDebounceTimer);
		}
		
		// 검색 시작 시 페이지 로딩 표시
		isLoadingEvents = true;
		
    requestAnimationFrame(() => {
      searchDebounceTimer = setTimeout(() => {
        try {
          if (stockEvents.length > 0) {
            calendarData = generateCalendarData(currentYear);
          }
        } finally {
          // 로딩 상태 종료
          isLoadingEvents = false;
        }
      }, 500); // 500ms로 늘려서 로딩 스피너가 보이도록 함
    });
	};

	// 최적화된 날짜별 이벤트 조회 함수
	const getEventsForDate = (year: number, month: number, date: number): StockEvent[] => {
		// 두 가지 날짜 형식 지원
		const targetDateISO = `${year}-${month.toString().padStart(2, '0')}-${date.toString().padStart(2, '0')}`;  // YYYY-MM-DD (IR 이벤트용)
		const targetDateCompact = `${year}${month.toString().padStart(2, '0')}${date.toString().padStart(2, '0')}`;  // YYYYMMDD (나머지 이벤트용)
		
		const filteredEvents = stockEvents.filter(event => {
			// 날짜 매칭 확인 - 두 가지 형식 모두 지원
			const dateMatches = event.date_time && (
				event.date_time.includes(targetDateISO) ||     // YYYY-MM-DD HH:MM 형식 (IR1, IR2)
				event.date_time.includes(targetDateCompact)    // YYYYMMDD 형식 (나머지 이벤트)
			);
			
			if (dateMatches) {
				// 이벤트 타입 필터링
				const isTypeSelected = isEventTypeSelected(event.event_type, event.event_code);
				
				// 검색 필터링 (검색어가 있는 경우만)
				if (searchQuery.trim() !== '') {
					const query = searchQuery.toLowerCase().trim();
					const matchesSearch = event.company_name.toLowerCase().includes(query) ||
                                event.stock_code.toLowerCase().includes(query) ||
                                event.event_name.toLowerCase().includes(query);
					return isTypeSelected && matchesSearch;
				}
				
				return isTypeSelected;
			}
			
			return false;
		});
		
		return filteredEvents;
	};

	// 이벤트 타입이 선택되었는지 확인하는 함수 (신규상장 디버깅 포함)
	const isEventTypeSelected = (eventType: string, eventCode: string): boolean => {
		// 실적발표 - eventCode: 'IR1'
		if (selectedEventTypes.includes('earnings')) {
			if (eventCode === 'IR1') {
				return true;
			}
		}
		
		// IR 이벤트 - eventCode: 'IR2'
		if (selectedEventTypes.includes('ir')) {
			if (eventCode === 'IR2') {
				return true;
			}
		}
		
		// 신규상장 - eventCode: '17'
		if (selectedEventTypes.includes('listing')) {
			if (eventCode === '17') {
				return true;
			}
		}
		
		// 자본변동 - eventCode: '10', '20', '22', '23', '30', '31', '32', '33'
		if (selectedEventTypes.includes('capital')) {
			if (eventCode === '10' ||  // 유상증자(주주배정)
				eventCode === '20' ||  // 무상증자
				eventCode === '22' ||  // 유상증자(3자배정)
				eventCode === '23' ||  // 유상증자(일반공모)
				eventCode === '30' ||  // 무상소각
				eventCode === '31' ||  // 자본감소
				eventCode === '32' ||  // 주식소각
				eventCode === '33') {  // 기타자본변동
				return true;
			}
		}
		
		// 배당 - eventCode: '21', '40', '42', '43'
		if (selectedEventTypes.includes('dividend')) {
			if (eventCode === '21' ||  // 주식배당
				eventCode === '40' ||  // 액면병합
				eventCode === '42' ||  // 현금배당
				eventCode === '43') {  // 중간배당
				return true;
			}
		}
		
		// 액면분할/분할 - eventCode: '41', '54', '55', '56'
		if (selectedEventTypes.includes('split')) {
			if (eventCode === '41' ||  // 액면분할
				eventCode === '54' ||  // 기업물적분할
				eventCode === '55' ||  // 기업인적분할
				eventCode === '56') {  // 분할신주상장
				return true;
			}
		}
		
		// 합병 - eventCode: '52', '53'
		if (selectedEventTypes.includes('merger')) {
			if (eventCode === '52' ||  // 기업합병
				eventCode === '53') {  // 기업인수
				return true;
			}
		}
		
		// 상호변경 - eventCode: '50'
		if (selectedEventTypes.includes('namechange')) {
			if (eventCode === '50') {  // 상호변경
				return true;
			}
		}
		
		return false;
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
				
				// 필터가 선택되지 않은 경우 빈 이벤트 배열, 그렇지 않으면 실제 이벤트 가져오기
				const events = selectedEventTypes.length === 0 ? [] : getEventsForDate(year, month, date);
				
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
		const todayCheck = isToday(year, month, dateInfo.date);
		const selectedCheck = selectedDateInfo !== null && 
			selectedDateInfo.year === year && 
			selectedDateInfo.month === month && 
			selectedDateInfo.date === dateInfo.date;
		
		let baseClass = "flex flex-col items-center justify-start w-[100px] h-[100px] p-2 text-sm border rounded-xl transition-all duration-300 cursor-pointer relative backdrop-blur-sm shadow-lg overflow-visible";
		
		// 호버 시 효과
		baseClass += " hover:shadow-xl hover:scale-105";
		
		// 선택된 날짜 강조 (레이아웃에 영향 없는 방식)
		if (selectedCheck) {
			baseClass += " shadow-2xl shadow-orange-400/60";
			// 선택된 날짜는 배경을 오렌지/핑크 계열로
			if (dateInfo.isHoliday) {
				return baseClass + " bg-gradient-to-br from-orange-500/50 via-pink-500/40 to-red-500/50 text-orange-100 hover:from-orange-500/60 hover:via-pink-500/50 hover:to-red-500/60 border-orange-400/40";
			} else if (dateInfo.dayOfWeek === 6) { // 토요일
				return baseClass + " bg-gradient-to-br from-orange-500/50 via-pink-500/40 to-red-500/50 text-orange-100 hover:from-orange-500/60 hover:via-pink-500/50 hover:to-red-500/60 border-orange-400/40";
			} else {
				return baseClass + " bg-gradient-to-br from-orange-500/50 via-pink-500/40 to-red-500/50 text-orange-100 hover:from-orange-500/60 hover:via-pink-500/50 hover:to-red-500/60 border-orange-400/40";
			}
		}
		
		// 오늘 날짜 강조 - 부드러운 애니메이션으로 개선
		if (todayCheck) {
			baseClass += " ring-4 ring-green-400 ring-offset-4 ring-offset-slate-900 shadow-2xl shadow-green-400/50 gentle-glow border-green-400/60";
			// 오늘 날짜는 배경도 더 밝게
			if (dateInfo.isHoliday) {
				return baseClass + " bg-gradient-to-br from-green-500/40 via-emerald-500/30 to-teal-500/40 text-green-100 hover:from-green-500/50 hover:via-emerald-500/40 hover:to-teal-500/50";
			} else if (dateInfo.dayOfWeek === 6) { // 토요일
				return baseClass + " bg-gradient-to-br from-green-500/40 via-emerald-500/30 to-teal-500/40 text-green-100 hover:from-green-500/50 hover:via-emerald-500/40 hover:to-teal-500/50";
			} else {
				return baseClass + " bg-gradient-to-br from-green-500/40 via-emerald-500/30 to-teal-500/40 text-green-100 hover:from-green-500/50 hover:via-emerald-500/40 hover:to-teal-500/50";
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
			return baseClass + " bg-gradient-to-br from-green-600 via-emerald-600 to-teal-600 ring-4 ring-green-400 ring-offset-2 ring-offset-slate-900 shadow-2xl shadow-green-400/50 subtle-border border-green-400/60";
		} else {
			return baseClass + " bg-gradient-to-br from-orange-600 via-red-600 to-pink-600";
		}
	};

	// 이벤트 타입에 따른 색상 반환
	const getEventColor = (eventType: string, eventCode: string): string => {
		if (eventType.includes('실적발표') || eventCode === 'IR1') {
			return 'bg-green-500/70 text-green-100 border-green-400/30'; // 실적발표
		}
		if (eventType.includes('경영현황') || eventCode === 'IR2') {
			return 'bg-blue-500/70 text-blue-100 border-blue-400/30'; // IR 이벤트
		}
		if (eventType.includes('신규상장')) {
			return 'bg-purple-500/70 text-purple-100 border-purple-400/30'; // 신규상장
		}
		if (eventType.includes('증자') || eventType.includes('감자')) {
			return 'bg-yellow-500/70 text-yellow-100 border-yellow-400/30'; // 자본변동
		}
		if (eventType.includes('배당')) {
			return 'bg-indigo-500/70 text-indigo-100 border-indigo-400/30'; // 배당
		}
		if (eventType.includes('분할')) {
			return 'bg-teal-500/70 text-teal-100 border-teal-400/30'; // 분할
		}
		if (eventType.includes('합병')) {
			return 'bg-red-500/70 text-red-100 border-red-400/30'; // 합병
		}
		if (eventType.includes('상호변경')) {
			return 'bg-gray-500/70 text-gray-100 border-gray-400/30'; // 상호변경
		}
		return 'bg-slate-500/70 text-slate-100 border-slate-400/30'; // 기타
	};

	// 특정 날짜를 선택하는 함수 (재사용 가능)
	const selectDate = (year: number, month: number, date: number) => {
		selectedDateInfo = {
			year: year,
			month: month,
			date: date,
			weekEvents: generateWeekEvents(year, month, date)
		};
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
	};

	// 1월 1일로 스크롤 이동하는 함수
	const scrollToJanuary1st = () => {
		if (!scrollContainer) return;
		
		scrollContainer.scrollTo({
			left: 0,
			top: 0,
			behavior: 'smooth'
		});
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
	};

	// 이벤트 타입 토글 함수 (모든 이벤트 타입 디버깅 지원)
	const toggleEventType = async (eventTypeCode: string) => {
    isLoadingEvents = true;
		
		if (selectedEventTypes.includes(eventTypeCode)) {
			// 이벤트 타입 제거
			selectedEventTypes = selectedEventTypes.filter(code => code !== eventTypeCode);
		} else {
			// 이벤트 타입 추가
			selectedEventTypes = [...selectedEventTypes, eventTypeCode];
		}
		
		// 조회 조건 변경 시 모달 닫기
		selectedDateInfo = null;
		
		// 비동기 처리로 달력 업데이트
    requestAnimationFrame(() => {
      setTimeout(() => {
        try {
          if (stockEvents.length > 0) {
            calendarData = generateCalendarData(currentYear);
          }
        } finally {
          isLoadingEvents = false;
        }
      }, 500);
		});
	};

	// 전체 선택 토글 함수 (즉시 피드백 개선)
	const toggleAllEventTypes = async () => {
    isLoadingEvents = true;

		if (isAllSelected) {
			// 전체 선택 해제
			selectedEventTypes = [];
		} else {
			// 전체 선택
			selectedEventTypes = availableEventTypes.map(eventType => eventType.code);
		}
		
		// 조회 조건 변경 시 모달 닫기
		selectedDateInfo = null;
		
		// 비동기로 달력 업데이트 (UI 반응성 개선)
		requestAnimationFrame(() => {
      setTimeout(() => {
        try {
          if (stockEvents.length > 0) {
            calendarData = generateCalendarData(currentYear);
          }
        } finally {
          isLoadingEvents = false;
        }
      }, 500);
		});
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
		}
	};

	// 페이지 마운트 시 초기화
	onMount(async () => {
    await applyKoreanHolidays();

		// 초기 빈 달력 데이터 생성 (로딩 중에도 달력 구조는 보이도록)
		calendarData = generateCalendarData(currentYear);
		
		// 주식 일정 데이터 로드 완료를 기다림
		await fetchStockCalendar(currentYear);
		
		// 로딩 완료 후 스크롤 및 선택 로직 실행
		requestAnimationFrame(() => {
			const today = new Date();
			const todayYear = today.getFullYear();
			
			if (currentYear === todayYear) {
				// 현재 연도라면 먼저 오늘 날짜 선택 (모달 표시)
				autoSelectToday();
				// 모달이 뜬 후 스크롤 이동
				requestAnimationFrame(() => {
					scrollToToday();
				});
			} else {
				// 다른 연도면 1월 1일로 스크롤만
				scrollToJanuary1st();
			}
		});
	});

  /**
	 * 한국 공휴일 데이터 로드 및 적용
	 */
	const applyKoreanHolidays = async () => {
		// 새로운 연도의 한국 공휴일 데이터 로드 완료를 기다림
		isLoadingEvents = true;
		try {
			const result = await getKoreanHolidays({ year: currentYear });
			if (result.success && result.data.holidays) {
				// 공휴일 데이터를 월-일 형태의 키로 변환
				const holidaysMap: Record<string, string> = {};
				result.data.holidays.forEach((holiday: any) => {
					if (holiday.formatted_date) {
						const [year, month, day] = holiday.formatted_date.split('-');
						const key = `${parseInt(month)}-${parseInt(day)}`;
						holidaysMap[key] = holiday.date_name;
					}
				});
				koreanHolidays = holidaysMap;
			} else {
				throw new Error(result.error || '한국 공휴일 데이터를 가져올 수 없습니다.');
			}
		} catch (error) {
			koreanHolidays = {}; // 에러 발생 시 빈 객체로 설정
		} finally {
			isLoadingEvents = false;
		}
	}

	// 연도 변경 함수
	const changeYear = async (delta: number) => {
		// 조회 조건 변경 시 모달 닫기
		selectedDateInfo = null;
		
		currentYear += delta;

    await applyKoreanHolidays();

		calendarData = generateCalendarData(currentYear);
		
		// 새로운 연도의 주식 일정 데이터 로드 완료를 기다림
		await fetchStockCalendar(currentYear);
		
		// 로딩 완료 후 스크롤 위치 결정
		requestAnimationFrame(() => {
			scrollToAppropriateDate();
		});
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
			requestAnimationFrame(() => {
				scrollToToday();
			});
		} else {
			// 다른 연도면 1월 1일로 스크롤하고 선택 해제
			scrollToJanuary1st();
			selectedDateInfo = null;
		}
	};

	// 이벤트 타입에 따른 필드 라벨 매핑 함수
	const getFieldLabel = (fieldName: string, eventType: string, eventCode: string): string => {
		// 실적발표
		if (eventType.includes('실적발표') || eventCode === 'IR1') {
			switch(fieldName) {
				case 'issue_price': return '발표예정가';
				case 'allocation_ratio': return '실적수치';
				case 'payment_date': return '발표일';
				case 'new_stock_listing_date': return '정정공시일';
				case 'ex_rights_date': return '실적반영일';
				case 'allocation_base_date': return '기준일자';
				case 'capital_after_change': return '예상매출';
				case 'total_issued_stocks': return '발행주식수';
				case 'change_stocks': return '실적변동';
				case 'discount_ratio': return '변동률';
				default: return fieldName;
			}
		}
		
		// IR 이벤트
		if (eventType.includes('경영현황') || eventCode === 'IR2') {
			switch(fieldName) {
				case 'issue_price': return '참가비용';
				case 'allocation_ratio': return '참여방법';
				case 'payment_date': return '신청마감일';
				case 'new_stock_listing_date': return '개최일';
				case 'ex_rights_date': return '사전등록일';
				case 'allocation_base_date': return '대상주주';
				case 'capital_after_change': return '회사규모';
				case 'total_issued_stocks': return '발행주식수';
				case 'change_stocks': return '유통주식수';
				case 'discount_ratio': return '참여율';
				default: return fieldName;
			}
		}
		
		// 신규상장
		if (eventType.includes('신규상장') || eventCode === '17') {
			switch(fieldName) {
				case 'issue_price': return '공모가격';
				case 'allocation_ratio': return '공모비율';
				case 'payment_date': return '납입일';
				case 'new_stock_listing_date': return '상장예정일';
				case 'ex_rights_date': return '청약일';
				case 'allocation_base_date': return '배정일';
				case 'capital_after_change': return '상장후자본금';
				case 'total_issued_stocks': return '상장주식수';
				case 'change_stocks': return '공모주식수';
				case 'discount_ratio': return '할인율';
				default: return fieldName;
			}
		}
		
		// 증자/감자
		if (eventType.includes('증자') || eventType.includes('감자') ||
			eventCode === '10' || eventCode === '20' || eventCode === '22' || eventCode === '23' || 
			eventCode === '30' || eventCode === '31' || eventCode === '32' || eventCode === '33') {
			switch(fieldName) {
				case 'issue_price': return '발행가격';
				case 'allocation_ratio': return '배정비율';
				case 'payment_date': return '납입일';
				case 'new_stock_listing_date': return '신주상장일';
				case 'ex_rights_date': return '권리락일';
				case 'allocation_base_date': return '배정기준일';
				case 'capital_after_change': return '변경후자본금';
				case 'total_issued_stocks': return '총발행주식수';
				case 'change_stocks': return '신주발행수';
				case 'discount_ratio': return '할인율';
				default: return fieldName;
			}
		}
		
		// 배당
		if (eventType.includes('배당') || 
			eventCode === '21' || eventCode === '40' || eventCode === '42' || eventCode === '43') {
			switch(fieldName) {
				case 'issue_price': return '배당금액';
				case 'allocation_ratio': return '배당율';
				case 'payment_date': return '배당지급일';
				case 'new_stock_listing_date': return '배당확정일';
				case 'ex_rights_date': return '배당기준일';
				case 'allocation_base_date': return '주주확정일';
				case 'capital_after_change': return '배당총액';
				case 'total_issued_stocks': return '배당대상주식수';
				case 'change_stocks': return '배당주식수';
				case 'discount_ratio': return '배당수익률';
				default: return fieldName;
			}
		}
		
		// 분할
		if (eventType.includes('분할') || 
			eventCode === '41' || eventCode === '54' || eventCode === '55' || eventCode === '56') {
			switch(fieldName) {
				case 'issue_price': return '분할후가격';
				case 'allocation_ratio': return '분할비율';
				case 'payment_date': return '분할기준일';
				case 'new_stock_listing_date': return '분할상장일';
				case 'ex_rights_date': return '권리락일';
				case 'allocation_base_date': return '분할기준일';
				case 'capital_after_change': return '분할후자본금';
				case 'total_issued_stocks': return '분할후주식수';
				case 'change_stocks': return '분할증가수';
				case 'discount_ratio': return '분할비율';
				default: return fieldName;
			}
		}
		
		// 합병
		if (eventType.includes('합병') || eventCode === '52' || eventCode === '53') {
			switch(fieldName) {
				case 'issue_price': return '합병가격';
				case 'allocation_ratio': return '합병비율';
				case 'payment_date': return '합병승인일';
				case 'new_stock_listing_date': return '합병효력일';
				case 'ex_rights_date': return '합병기준일';
				case 'allocation_base_date': return '주주확정일';
				case 'capital_after_change': return '합병후자본금';
				case 'total_issued_stocks': return '합병후주식수';
				case 'change_stocks': return '합병주식수';
				case 'discount_ratio': return '합병프리미엄';
				default: return fieldName;
			}
		}
		
		// 상호변경
		if (eventType.includes('상호변경') || eventCode === '50') {
			switch(fieldName) {
				case 'issue_price': return '변경비용';
				case 'allocation_ratio': return '변경사유';
				case 'payment_date': return '변경신고일';
				case 'new_stock_listing_date': return '변경효력일';
				case 'ex_rights_date': return '변경기준일';
				case 'allocation_base_date': return '공고일';
				case 'capital_after_change': return '자본금';
				case 'total_issued_stocks': return '발행주식수';
				case 'change_stocks': return '변경없음';
				case 'discount_ratio': return '해당없음';
				default: return fieldName;
			}
		}
		
		// 기본 라벨
		switch(fieldName) {
			case 'issue_price': return '발행가격';
			case 'allocation_ratio': return '배정비율';
			case 'payment_date': return '납입일';
			case 'new_stock_listing_date': return '신주상장일';
			case 'ex_rights_date': return '권리락일';
			case 'allocation_base_date': return '배정기준일';
			case 'capital_after_change': return '변경후자본금';
			case 'total_issued_stocks': return '총발행주식수';
			case 'change_stocks': return '변동주식수';
			case 'discount_ratio': return '할인율';
			default: return fieldName;
		}
	};

	// 이벤트 타입에 따라 관련 있는 필드인지 확인하는 함수
	const isFieldRelevant = (fieldName: string, eventType: string, eventCode: string): boolean => {
		// 실적발표에 관련 있는 필드
		if (eventType.includes('실적발표') || eventCode === 'IR1') {
			return ['payment_date', 'ex_rights_date', 'allocation_base_date', 'total_issued_stocks'].includes(fieldName);
		}
		
		// IR 이벤트에 관련 있는 필드
		if (eventType.includes('경영현황') || eventCode === 'IR2') {
			return ['new_stock_listing_date', 'allocation_base_date', 'total_issued_stocks', 'change_stocks'].includes(fieldName);
		}
		
		// 신규상장에 관련 있는 필드
		if (eventType.includes('신규상장') || eventCode === '17') {
			return ['issue_price', 'allocation_ratio', 'payment_date', 'new_stock_listing_date', 'ex_rights_date', 'allocation_base_date', 'capital_after_change', 'total_issued_stocks', 'change_stocks'].includes(fieldName);
		}
		
		// 증자/감자에 관련 있는 필드 (자본변동)
		if (eventType.includes('증자') || eventType.includes('감자') ||
			eventCode === '10' || eventCode === '20' || eventCode === '22' || eventCode === '23' || 
			eventCode === '30' || eventCode === '31' || eventCode === '32' || eventCode === '33') {
			return ['issue_price', 'allocation_ratio', 'payment_date', 'new_stock_listing_date', 'ex_rights_date', 'allocation_base_date', 'capital_after_change', 'total_issued_stocks', 'change_stocks', 'discount_ratio'].includes(fieldName);
		}
		
		// 배당에 관련 있는 필드
		if (eventType.includes('배당') || 
			eventCode === '21' || eventCode === '40' || eventCode === '42' || eventCode === '43') {
			return ['issue_price', 'allocation_ratio', 'payment_date', 'ex_rights_date', 'allocation_base_date', 'capital_after_change', 'total_issued_stocks', 'discount_ratio'].includes(fieldName);
		}
		
		// 분할에 관련 있는 필드
		if (eventType.includes('분할') || 
			eventCode === '41' || eventCode === '54' || eventCode === '55' || eventCode === '56') {
			return ['allocation_ratio', 'payment_date', 'new_stock_listing_date', 'ex_rights_date', 'capital_after_change', 'total_issued_stocks', 'change_stocks'].includes(fieldName);
		}
		
		// 합병에 관련 있는 필드
		if (eventType.includes('합병') || eventCode === '52' || eventCode === '53') {
			return ['issue_price', 'allocation_ratio', 'payment_date', 'new_stock_listing_date', 'ex_rights_date', 'allocation_base_date', 'capital_after_change', 'total_issued_stocks', 'change_stocks'].includes(fieldName);
		}
		
		// 상호변경에 관련 있는 필드
		if (eventType.includes('상호변경') || eventCode === '50') {
			return ['payment_date', 'new_stock_listing_date', 'allocation_base_date', 'capital_after_change', 'total_issued_stocks'].includes(fieldName);
		}
		
		// 기본적으로 모든 필드 표시
		return true;
	};

	// 월별 날짜 데이터 타입
	interface DateInfo {
		date: number;
		dayOfWeek: number; // 0: 일요일, 1: 월요일, ..., 6: 토요일
		isWeekend: boolean;
		isHoliday: boolean;
		holidayName?: string;
		events?: StockEvent[]; // 해당 날짜의 주식 이벤트들
	}

	// 주식 이벤트 타입
	interface StockEvent {
		key: string;
		serial_number: string;
		base_date: string;
		company_name: string;
		activity_code: string;
		event_name: string;
		event_code: string;
		date_time: string;
		stock_code: string;
		stock_type: string;
		event_type: string;
		change_stocks: string;
		issue_price: string;
		capital_after_change: string;
		total_issued_stocks: string;
		new_stock_listing_date: string;
		ex_rights_date: string;
		payment_date: string;
		allocation_base_date: string;
		allocation_ratio: string;
		discount_ratio: string;
		note: string;
		year_month: string;
	}

	// 연도별 달력 데이터
	let calendarData: DateInfo[][] = [];
</script>

<svelte:head>
	<title>연간 주식 달력 - FinanceChart</title>
	<meta name="description" content="연간 주식 이벤트 캘린더" />
</svelte:head>

<div class="w-screen h-screen bg-gradient-to-br from-slate-950 via-orange-950 to-red-950 relative overflow-hidden">
	<!-- 고급 배경 데코레이션 -->
	<div class="absolute inset-0 bg-[radial-gradient(circle_at_20%_80%,_rgba(255,119,95,0.3),_transparent_50%),radial-gradient(circle_at_80%_20%,_rgba(255,159,0,0.15),_transparent_50%),radial-gradient(circle_at_40%_40%,_rgba(255,200,119,0.2),_transparent_50%)] pointer-events-none"></div>
	<div class="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,_rgba(245,101,101,0.1)_1px,_transparent_0)] bg-[size:40px_40px] pointer-events-none"></div>
	
	<!-- 움직이는 배경 오브 -->
	<div class="absolute top-0 right-0 w-96 h-96 bg-gradient-to-r from-orange-400/30 to-red-400/30 rounded-full blur-3xl translate-x-1/3 -translate-y-1/3 animate-pulse"></div>
	<div class="absolute bottom-0 left-0 w-96 h-96 bg-gradient-to-r from-yellow-400/20 to-orange-400/20 rounded-full blur-3xl -translate-x-1/3 translate-y-1/3 animate-pulse"></div>
	<div class="absolute top-1/2 left-1/2 w-64 h-64 bg-gradient-to-r from-red-400/15 to-pink-400/15 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2 animate-pulse"></div>

	<div class="relative z-10 h-full flex flex-col">
		<!-- 헤더 영역 -->
		<div class="p-8 border-b border-white/10 backdrop-blur-xl bg-white/5 flex-shrink-0 shadow-2xl">
			<div class="flex items-center justify-between">
				<!-- 제목 영역 -->
				<div class="flex items-center space-x-6">
					<div class="relative">
						<div class="absolute inset-0 bg-gradient-to-r from-orange-500 to-red-600 rounded-3xl blur-lg opacity-70 animate-pulse"></div>
						<div class="relative flex items-center justify-center w-16 h-16 bg-gradient-to-br from-orange-500 via-red-500 to-pink-500 rounded-3xl shadow-2xl">
							<svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
							</svg>
						</div>
					</div>
					<div>
						<h1 class="text-4xl font-black bg-gradient-to-r from-white via-orange-200 to-red-200 bg-clip-text text-transparent tracking-tight">
							{`${currentYear}년 주식 달력`}
						</h1>
						<p class="text-slate-300 text-base font-medium mt-1 tracking-wide">Annual Stock Calendar</p>
					</div>
				</div>

				<!-- 연도 선택 영역 -->
				<div class="flex items-center space-x-6">
					<!-- 검색 영역 추가 -->
					<div class="relative">
						<div class="absolute inset-0 bg-gradient-to-r from-orange-500/20 to-red-500/20 rounded-2xl blur-xl"></div>
						<div class="relative flex items-center bg-gradient-to-r from-slate-800/90 to-slate-700/90 backdrop-blur-xl rounded-2xl px-4 py-3 border border-white/20 shadow-xl">
							{#if isProcessing && clickedButton === 'search-input'}
								<span class="w-5 h-5 text-orange-400 mr-3 loading-pulse">⚡</span>
							{:else if isLoadingEvents}
								<svg class="animate-spin w-5 h-5 text-orange-400 mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
									<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
									<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
								</svg>
							{:else}
								<svg class="w-5 h-5 text-slate-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
								</svg>
							{/if}
							<input
								type="text"
								placeholder="종목명, 코드 검색..."
								bind:value={searchQuery}
								on:input={() => {
									// 디바운싱된 검색으로 성능 최적화
									debouncedSearch(searchQuery);
									selectedDateInfo = null;
								}}
								class="bg-transparent text-white placeholder-slate-400 outline-none text-sm font-medium w-48"
							/>
							{#if searchQuery}
								<button
									class="ml-2 text-slate-400 hover:text-white transition-colors duration-200"
									on:click={() => {
                    searchQuery = '';
                    // 디바운싱된 검색으로 성능 최적화
                    debouncedSearch(searchQuery);
                    selectedDateInfo = null;
                  }}
								>
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
									</svg>
								</button>
							{/if}
						</div>
					</div>

					<button 
						class="group relative flex items-center justify-center w-12 h-12 bg-gradient-to-r from-slate-700/80 to-slate-600/80 hover:from-slate-600/90 hover:to-slate-500/90 rounded-2xl transition-all duration-300 hover:scale-110 shadow-lg hover:shadow-xl backdrop-blur-sm border border-white/10"
						on:click={() => changeYear(-1)}
					>
						<div class="absolute inset-0 bg-gradient-to-r from-orange-500/20 to-red-500/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
						<svg class="relative z-10 w-6 h-6 text-slate-200 group-hover:text-white transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"></path>
						</svg>
					</button>
					
					<div class="relative">
						<div class="absolute inset-0 bg-gradient-to-r from-orange-500/20 to-red-500/20 rounded-3xl blur-xl"></div>
						<div class="relative bg-gradient-to-r from-slate-800/90 to-slate-700/90 backdrop-blur-xl rounded-3xl px-8 py-4 border border-white/20 shadow-2xl">
							<span class="text-3xl font-black bg-gradient-to-r from-white to-orange-200 bg-clip-text text-transparent">{currentYear}</span>
						</div>
					</div>
					
					<button 
						class="group relative flex items-center justify-center w-12 h-12 bg-gradient-to-r from-slate-700/80 to-slate-600/80 hover:from-slate-600/90 hover:to-slate-500/90 rounded-2xl transition-all duration-300 hover:scale-110 shadow-lg hover:shadow-xl backdrop-blur-sm border border-white/10"
						on:click={() => changeYear(1)}
					>
						<div class="absolute inset-0 bg-gradient-to-r from-orange-500/20 to-red-500/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
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
				<!-- 이벤트 타입 선택 섹션 -->
				<div>
					<h3 class="text-sm font-bold text-slate-200 mb-2 flex items-center">
						이벤트 타입 선택
						{#if isProcessing}
							<span class="ml-2 text-xs text-orange-400 font-medium loading-pulse">⚡ 처리 중...</span>
						{:else if isLoadingEvents}
							<svg class="animate-spin ml-2 h-4 w-4 text-orange-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
							</svg>
						{/if}
					</h3>
					
					<div class="flex flex-wrap gap-2">
						<!-- 전체 선택 버튼 -->
						<button
							class="group relative flex items-center space-x-1.5 px-3 py-1.5 bg-gradient-to-r from-slate-700/80 to-slate-600/80 hover:from-slate-600/90 hover:to-slate-500/90 rounded-lg transition-all duration-300 hover:scale-105 shadow-md backdrop-blur-sm border border-white/10 
							{isAllSelected ? 'from-orange-600/80 to-red-600/80 hover:from-orange-500/90 hover:to-red-500/90' : ''}
							{buttonLoadingStates['all-events'] ? 'scale-95 opacity-80 cursor-wait' : 'hover:scale-105'}
							{isProcessing ? 'pointer-events-none' : ''}"
							on:click={toggleAllEventTypes}
							disabled={isProcessing}
						>
							<div class="w-3 h-3 rounded border-2 border-slate-300 flex items-center justify-center transition-all duration-200 {isAllSelected ? 'bg-white border-white' : 'bg-transparent'}">
								{#if isAllSelected}
									<svg class="w-2 h-2 text-orange-600" fill="currentColor" viewBox="0 0 20 20">
										<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
									</svg>
								{/if}
							</div>
							<span class="text-slate-200 font-medium text-xs">전체</span>
						</button>

						<!-- 이벤트 타입별 선택 버튼들 -->
						{#each availableEventTypes as eventType}
							<button
								class="group relative flex items-center space-x-1.5 px-2.5 py-1.5 bg-gradient-to-r from-slate-700/60 to-slate-600/60 hover:from-slate-600/70 hover:to-slate-500/70 rounded-lg transition-all duration-300 hover:scale-105 shadow-md backdrop-blur-sm border border-white/10 
								{selectedEventTypes.includes(eventType.code) ? `${eventType.color.replace('from-', 'from-').replace('to-', 'to-')}/70 hover:${eventType.color.replace('from-', 'from-').replace('to-', 'to-')}/80 border-orange-400/30` : 'hover:border-slate-400/30'}
								{buttonLoadingStates[`event-${eventType.code}`] ? 'scale-95 opacity-80 cursor-wait' : 'hover:scale-105'}
								{isProcessing ? 'pointer-events-none' : ''}"
								on:click={() => toggleEventType(eventType.code)}
								disabled={isProcessing}
							>
								<span class="text-sm">{eventType.icon}</span>
								<span class="text-xs font-medium text-slate-200">{eventType.name}</span>
								{#if selectedEventTypes.includes(eventType.code)}
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
						
						<!-- 이벤트 색상 범례 -->
						<div class="flex items-center space-x-4 border-l border-white/20 pl-4">
							<div class="flex items-center space-x-1">
								<span class="text-sm">📊</span>
								<span class="text-green-200 text-xs">실적발표</span>
 							</div>
							<div class="flex items-center space-x-1">
								<span class="text-sm">🎤</span>
								<span class="text-blue-200 text-xs">IR이벤트</span>
 							</div>
							<div class="flex items-center space-x-1">
								<span class="text-sm">🚀</span>
								<span class="text-purple-200 text-xs">신규상장</span>
 							</div>
							<div class="flex items-center space-x-1">
								<span class="text-sm">💰</span>
								<span class="text-yellow-200 text-xs">자본변동</span>
 							</div>
							<div class="flex items-center space-x-1">
								<span class="text-sm">💎</span>
								<span class="text-indigo-200 text-xs">배당</span>
 							</div>
						</div>
					</div>
					
					<!-- 주식 일정 상태 -->
					<div class="flex items-center space-x-3">
						{#if isLoadingEvents}
							<div class="flex items-center space-x-2">
								<div class="animate-spin rounded-full h-3 w-3 border-b-2 border-orange-400"></div>
								<span class="text-slate-300 text-xs">로딩 중...</span>
							</div>
						{:else if selectedEventTypes.length === 0}
							<div class="flex items-center space-x-2">
								<div class="w-3 h-3 bg-orange-500 rounded-full animate-pulse"></div>
								<span class="text-orange-300 text-xs">이벤트 타입을 선택해주세요</span>
							</div>
						{:else if eventsError}
							<div class="flex items-center space-x-2">
								<div class="w-3 h-3 bg-red-500 rounded-full"></div>
								<span class="text-red-300 text-xs">로딩 실패</span>
							</div>
						{:else}
							<div class="flex items-center space-x-4">
								<span class="text-slate-300 text-xs">
									전체: {stockEvents.length}개 이벤트 ({selectedEventTypes.length}개 타입)
								</span>
								{#if searchQuery}
									<span class="text-orange-300 text-xs border-l border-white/20 pl-4">
										🔍 검색결과: {searchResultCount}개
									</span>
								{/if}
							</div>
						{/if}
					</div>
				</div>
			</div>
		</div>

		<!-- Year Glance 스타일 메인 달력 -->
		<div class="flex-1 {isLoadingEvents ? '' : 'overflow-auto'} bg-black/20 backdrop-blur-sm px-2 relative
			{isProcessing ? 'btn-processing' : ''}" 
			bind:this={scrollContainer}>
			<!-- 로딩 오버레이 - 보이는 화면 영역 기준 중앙 정렬 -->
			{#if isLoadingEvents}
				<div class="absolute inset-0 z-50 bg-slate-900/80 backdrop-blur-md">
					<div class="fixed top-1/3 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-[60] bg-gradient-to-br from-slate-800/90 to-slate-700/90 backdrop-blur-xl rounded-2xl border border-white/20 shadow-2xl p-8 text-center max-w-md mx-4">
						<!-- 로딩 스피너 -->
						<div class="relative mb-6">
							<div class="w-16 h-16 mx-auto">
								<!-- 외부 링 -->
								<div class="absolute inset-0 border-4 border-orange-500/30 rounded-full"></div>
								<!-- 회전하는 링 -->
								<div class="absolute inset-0 border-4 border-transparent border-t-orange-500 border-r-red-500 rounded-full animate-spin"></div>
								<!-- 내부 펄스 -->
								<div class="absolute inset-2 bg-gradient-to-br from-orange-500/20 to-red-500/20 rounded-full animate-pulse"></div>
							</div>
						</div>
						
						<!-- 로딩 텍스트 -->
						<h3 class="text-xl font-bold text-white mb-2">
							주식 일정 로딩 중
						</h3>
						<p class="text-slate-300 text-sm mb-4">
							{currentYear}년 주식 이벤트를 가져오고 있습니다...
						</p>
						
						<!-- 진행 상태 바 -->
						<div class="w-full bg-slate-700/50 rounded-full h-2 overflow-hidden">
							<div class="h-full bg-gradient-to-r from-orange-500 to-red-500 rounded-full animate-pulse"></div>
						</div>
						
						<!-- 로딩 도트 애니메이션 -->
						<div class="flex justify-center items-center space-x-1 mt-4">
							<div class="w-2 h-2 bg-orange-400 rounded-full animate-bounce"></div>
							<div class="w-2 h-2 bg-red-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
							<div class="w-2 h-2 bg-pink-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
						</div>
					</div>
				</div>
			{/if}
			<div class="min-w-max"
				class:pointer-events-none={isLoadingEvents}
				class:opacity-50={isLoadingEvents}
			>
				<!-- 날짜 헤더 (1-31) -->
				<div class="sticky top-0 z-20 bg-gradient-to-r from-slate-900/95 via-orange-900/95 to-slate-900/95 backdrop-blur-xl border-b border-white/20 shadow-2xl">
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
										<div class="text-xs font-black text-green-200 mt-1 bg-green-500/20 px-2 py-0.5 rounded-full border border-green-400/40">
											THIS MONTH
										</div>
									{:else}
										<div class="text-sm text-orange-200 mt-1 font-medium">{monthData.length}일</div>
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
										}}
										title={monthData[dayIndex].holidayName || `${monthIndex + 1}월 ${monthData[dayIndex].date}일`}
									>
										<!-- 날짜 번호 -->
										<div class="font-black text-lg text-center mb-1 tracking-wide relative z-10 flex-shrink-0">
											{monthData[dayIndex].date}
											<!-- 오늘 날짜 표시 - 더 눈에 띄게 -->
											{#if isToday(currentYear, monthIndex + 1, monthData[dayIndex].date)}
												<div class="absolute -top-2 -right-2 bg-gradient-to-r from-green-400 to-emerald-400 text-slate-900 text-xs font-black px-1.5 py-0.5 rounded-full shadow-lg animate-bounce border-2 border-white">
													TODAY
												</div>
											{/if}
											<!-- 선택된 날짜 표시 - 오늘 날짜가 아닌 경우만 -->
											{#if selectedDateInfo && selectedDateInfo.year === currentYear && selectedDateInfo.month === (monthIndex + 1) && selectedDateInfo.date === monthData[dayIndex].date && !isToday(currentYear, monthIndex + 1, monthData[dayIndex].date)}
												<div class="absolute -top-2 -left-2 bg-gradient-to-r from-orange-400 to-red-400 text-white text-xs font-black px-1.5 py-0.5 rounded-full shadow-lg border-2 border-white animate-pulse">
													SELECTED
												</div>
											{/if}
											<!-- 오늘 날짜이면서 선택된 날짜인 경우 - 추가 표시 -->
											{#if selectedDateInfo && selectedDateInfo.year === currentYear && selectedDateInfo.month === (monthIndex + 1) && selectedDateInfo.date === monthData[dayIndex].date && isToday(currentYear, monthIndex + 1, monthData[dayIndex].date)}
												<div class="absolute -bottom-2 -left-2 bg-gradient-to-r from-orange-400 to-red-400 text-white text-xs font-black px-1.5 py-0.5 rounded-full shadow-lg border border-white animate-pulse">
													SELECTED
												</div>
											{/if}
										</div>
										
										<!-- 공휴일명 -->
										{#if monthData[dayIndex].holidayName}
											<div class="text-xs text-center font-bold bg-red-500/30 px-1 py-0.5 rounded border border-red-300/30 backdrop-blur-sm relative z-10 mb-1 flex-shrink-0">
												{monthData[dayIndex].holidayName}
											</div>
										{/if}
										
										<!-- 주식 이벤트들 -->
										{#if monthData[dayIndex].events && monthData[dayIndex].events.length > 0}
											<!-- 기본 이벤트 표시 (3개만) -->
											<div class="flex-1 w-full overflow-y-auto overflow-x-hidden space-y-1 scrollbar-thin">
												{#each monthData[dayIndex].events.slice(0, 3) as event, eventIndex}
													<!-- svelte-ignore a11y-click-events-have-key-events -->
													<!-- svelte-ignore a11y-no-static-element-interactions -->
													<div 
														class="text-xs px-1 py-0.5 rounded text-center font-medium border {getEventColor(event.event_type, event.event_code)} transition-all duration-200 cursor-pointer hover:shadow-lg"
														title="{event.company_name} - {event.event_type} ({event.date_time})"
														on:click|stopPropagation={() => selectedEventDetail = event}
													>
														<!-- 이벤트 이모지 표시 -->
														<div class="flex items-center justify-center space-x-1">
															<span class="text-xs">
																{#if event.event_type.includes('실적발표') || event.event_code === 'IR1'}
																	📊
																{:else if event.event_type.includes('경영현황') || event.event_code === 'IR2'}
																	🎤
																{:else if event.event_type.includes('신규상장')}
																	🚀
																{:else if event.event_type.includes('증자') || event.event_type.includes('감자')}
																	💰
																{:else if event.event_type.includes('배당')}
																	💎
																{:else if event.event_type.includes('분할')}
																	✂️
																{:else if event.event_type.includes('합병')}
																	🔄
																{:else if event.event_type.includes('상호변경')}
																	📝
																{:else}
																	📈
																{/if}
															</span>
														</div>
														<!-- 회사명 (축약) -->
														<div class="truncate font-bold text-xs">
															{event.company_name.length > 6 ? event.company_name.substring(0, 6) + '...' : event.company_name}
														</div>
														<!-- 이벤트 타입 -->
														<div class="text-xs opacity-90 truncate">
															{event.event_type.length > 4 ? event.event_type.substring(0, 4) + '...' : event.event_type}
														</div>
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
			<div class="border-t p-4 border-white/10 bg-gradient-to-r from-slate-900/95 via-orange-900/95 to-slate-900/95 backdrop-blur-xl flex-shrink-0 shadow-2xl max-h-80">
				<div class="">
					<!-- 헤더 -->
					<div class="flex items-center justify-between mb-4">
						<div class="flex items-center space-x-3">
							<div class="w-6 h-6 bg-gradient-to-r from-orange-500 to-red-600 rounded-lg flex items-center justify-center">
								<svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
								</svg>
							</div>
							<h3 class="text-xl font-bold text-white">
								{selectedDateInfo.year}년 {selectedDateInfo.month}월 {selectedDateInfo.date}일 주간 주식 이벤트
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
								<div class="text-center mb-1 py-1 border-b-4 {dayInfo.isSelected ? 'border-b-orange-300' : 'border-transparent'}">
									<div class="text-sm text-slate-400 font-medium">
										{dayInfo.month}월 {dayInfo.day}일
									</div>
									<div class="text-xs text-slate-500 mt-1">
										{['일', '월', '화', '수', '목', '금', '토'][new Date(dayInfo.year, dayInfo.month - 1, dayInfo.day).getDay()]}
									</div>
									{#if dayInfo.isToday}
										<div class="absolute top-0 left-1 bg-gradient-to-r from-green-400 to-emerald-400 text-slate-900 text-xs font-black px-1.5 py-0.5 rounded-full shadow-lg animate-bounce border-2 border-white">
											TODAY
										</div>
									{/if}
									{#if dayInfo.isSelected && !dayInfo.isToday}
										<div class="absolute top-0 left-1 bg-gradient-to-r from-orange-400 to-red-400 text-white text-xs font-black px-1.5 py-0.5 rounded-full shadow-lg animate-pulse border-2 border-white">
											SELECTED
										</div>
									{/if}
									{#if dayInfo.isSelected && dayInfo.isToday}
										<div class="absolute top-6 left-1 bg-gradient-to-r from-orange-400 to-red-400 text-white text-xs font-black px-1.5 py-0.5 rounded-full shadow-lg animate-pulse border-2 border-white">
											SELECTED
										</div>
									{/if}
								</div>
								
								<!-- 이벤트 목록 -->
								<div class="space-y-2 max-h-48 overflow-y-auto scrollbar-thin">
									{#if dayInfo.events.length === 0}
										<div class="flex h-48 justify-center items-center text-center text-slate-500 text-xs py-6 border border-slate-700/30 rounded-lg bg-slate-800/20 space-x-2">
											<div>📊</div>
											<div>이벤트 없음</div>
										</div>
									{:else}
										{#each dayInfo.events as event}
											<!-- svelte-ignore a11y-click-events-have-key-events -->
											<!-- svelte-ignore a11y-no-static-element-interactions -->
											<div 
												class="p-2 rounded-lg border {getEventColor(event.event_type, event.event_code)} transition-all duration-200 hover:bg-white/5 hover:border-opacity-80 cursor-pointer"
												on:click={() => selectedEventDetail = event}
											>
												<!-- 이벤트 아이콘과 회사명 -->
												<div class="flex items-center space-x-2 mb-1">
													<span class="text-sm">
														{#if event.event_type.includes('실적발표') || event.event_code === 'IR1'}
															📊
														{:else if event.event_type.includes('경영현황') || event.event_code === 'IR2'}
															🎤
														{:else if event.event_type.includes('신규상장')}
															🚀
														{:else if event.event_type.includes('증자') || event.event_type.includes('감자')}
															💰
														{:else if event.event_type.includes('배당')}
															💎
														{:else if event.event_type.includes('분할')}
															✂️
														{:else if event.event_type.includes('합병')}
															🔄
														{:else if event.event_type.includes('상호변경')}
															📝
														{:else}
															📈
														{/if}
													</span>
													<div class="text-xs font-bold leading-tight flex-1 truncate">
														{event.company_name}
													</div>
												</div>
												
												<!-- 이벤트 타입과 시간 -->
												<div class="flex items-center justify-between text-xs opacity-90 mb-1">
													<span class="font-medium">{event.event_type}</span>
													{#if event.date_time && event.date_time.includes(':')}
														<span class="text-xs">{event.date_time.split(' ')[1] || ''}</span>
													{/if}
												</div>
												
												<!-- 종목 코드와 추가 정보 -->
												<div class="flex items-center justify-between mt-1">
													<div class="text-xs font-medium text-white/80">
														{event.stock_code}
													</div>
													{#if event.event_name}
														<div class="text-xs font-medium text-white/60 truncate ml-2" title={event.event_name}>
															{event.event_name.length > 10 ? event.event_name.substring(0, 10) + '...' : event.event_name}
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

<!-- 이벤트 상세정보 모달 -->
{#if selectedEventDetail}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div 
		class="fixed inset-0 z-[100] bg-black/80 backdrop-blur-md flex items-center justify-center p-4"
		on:click={() => selectedEventDetail = null}
	>
		<!-- svelte-ignore a11y-click-events-have-key-events -->
		<!-- svelte-ignore a11y-no-static-element-interactions -->
		<div 
			class="relative bg-gradient-to-br from-slate-800/95 to-slate-700/95 backdrop-blur-xl rounded-3xl border border-white/20 shadow-2xl max-w-3xl w-full max-h-[80vh] overflow-y-auto"
			on:click|stopPropagation
		>
			<!-- 모달 헤더 -->
			<div class="sticky top-0 bg-gradient-to-r from-orange-600/90 to-red-600/90 backdrop-blur-xl p-6 rounded-t-3xl border-b border-white/20">
				<div class="flex items-center justify-between">
					<div class="flex items-center space-x-3">
						<span class="text-2xl">
							{#if selectedEventDetail.event_type.includes('실적발표') || selectedEventDetail.event_code === 'IR1'}
								📊
							{:else if selectedEventDetail.event_type.includes('경영현황') || selectedEventDetail.event_code === 'IR2'}
								🎤
							{:else if selectedEventDetail.event_type.includes('신규상장')}
								🚀
							{:else if selectedEventDetail.event_type.includes('증자') || selectedEventDetail.event_type.includes('감자')}
								💰
							{:else if selectedEventDetail.event_type.includes('배당')}
								💎
							{:else if selectedEventDetail.event_type.includes('분할')}
								✂️
							{:else if selectedEventDetail.event_type.includes('합병')}
								🔄
							{:else if selectedEventDetail.event_type.includes('상호변경')}
								📝
							{:else}
								📈
							{/if}
						</span>
						<div>
							<h2 class="text-xl font-bold text-white">{selectedEventDetail.company_name}</h2>
							<p class="text-orange-200 text-sm font-medium">{selectedEventDetail.event_type}</p>
						</div>
					</div>
					<button 
						class="text-white/70 hover:text-white transition-colors duration-200 p-2 rounded-full hover:bg-white/10"
						on:click={() => selectedEventDetail = null}
					>
						<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
						</svg>
					</button>
				</div>
			</div>

			<!-- 모달 내용 -->
			<div class="p-6 space-y-6">
				<!-- 기본 정보 -->
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div class="bg-slate-700/50 rounded-2xl p-4 border border-white/10">
						<h3 class="text-sm font-bold text-slate-300 mb-2 flex items-center space-x-2">
							<span>🏢</span>
							<span>기업 정보</span>
						</h3>
						<div class="space-y-2">
							<div class="flex justify-between items-center">
								<span class="text-slate-400 text-sm">회사명</span>
								<span class="text-white font-medium text-sm">{selectedEventDetail.company_name}</span>
							</div>
							<div class="flex justify-between items-center">
								<span class="text-slate-400 text-sm">종목코드</span>
								<span class="text-orange-300 font-bold text-sm">{selectedEventDetail.stock_code}</span>
							</div>
							<div class="flex justify-between items-center">
								<span class="text-slate-400 text-sm">종목유형</span>
								<span class="text-white text-sm">{selectedEventDetail.stock_type || '일반주식'}</span>
							</div>
						</div>
					</div>

					<div class="bg-slate-700/50 rounded-2xl p-4 border border-white/10">
						<h3 class="text-sm font-bold text-slate-300 mb-2 flex items-center space-x-2">
							<span>📅</span>
							<span>일정 정보</span>
						</h3>
						<div class="space-y-2">
							<div class="flex justify-between items-center">
								<span class="text-slate-400 text-sm">이벤트명</span>
								<span class="text-white font-medium text-sm">{selectedEventDetail.event_name || selectedEventDetail.event_type}</span>
							</div>
							<div class="flex justify-between items-center">
								<span class="text-slate-400 text-sm">일시</span>
								<span class="text-green-300 font-bold text-sm">{selectedEventDetail.date_time}</span>
							</div>
							<div class="flex justify-between items-center">
								<span class="text-slate-400 text-sm">이벤트코드</span>
								<span class="text-slate-300 text-sm">{selectedEventDetail.event_code}</span>
							</div>
						</div>
					</div>
				</div>

				<!-- 상세 정보 -->
				{#if selectedEventDetail.issue_price || selectedEventDetail.allocation_ratio || selectedEventDetail.payment_date || selectedEventDetail.new_stock_listing_date || selectedEventDetail.ex_rights_date || selectedEventDetail.allocation_base_date}
					<div class="bg-slate-700/50 rounded-2xl p-4 border border-white/10">
						<h3 class="text-sm font-bold text-slate-300 mb-3 flex items-center space-x-2">
							<span>📋</span>
							<span>상세 정보</span>
						</h3>
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
							{#if selectedEventDetail.issue_price && isFieldRelevant('issue_price', selectedEventDetail.event_type, selectedEventDetail.event_code)}
								<div class="flex justify-between items-center">
									<span class="text-slate-400 text-sm">{getFieldLabel('issue_price', selectedEventDetail.event_type, selectedEventDetail.event_code)}</span>
									<span class="text-yellow-300 font-bold text-sm">{selectedEventDetail.issue_price}</span>
								</div>
							{/if}
							{#if selectedEventDetail.allocation_ratio && isFieldRelevant('allocation_ratio', selectedEventDetail.event_type, selectedEventDetail.event_code)}
								<div class="flex justify-between items-center">
									<span class="text-slate-400 text-sm">{getFieldLabel('allocation_ratio', selectedEventDetail.event_type, selectedEventDetail.event_code)}</span>
									<span class="text-blue-300 font-medium text-sm">{selectedEventDetail.allocation_ratio}</span>
								</div>
							{/if}
							{#if selectedEventDetail.payment_date && isFieldRelevant('payment_date', selectedEventDetail.event_type, selectedEventDetail.event_code)}
								<div class="flex justify-between items-center">
									<span class="text-slate-400 text-sm">{getFieldLabel('payment_date', selectedEventDetail.event_type, selectedEventDetail.event_code)}</span>
									<span class="text-green-300 font-medium text-sm">{selectedEventDetail.payment_date}</span>
								</div>
							{/if}
							{#if selectedEventDetail.new_stock_listing_date && isFieldRelevant('new_stock_listing_date', selectedEventDetail.event_type, selectedEventDetail.event_code)}
								<div class="flex justify-between items-center">
									<span class="text-slate-400 text-sm">{getFieldLabel('new_stock_listing_date', selectedEventDetail.event_type, selectedEventDetail.event_code)}</span>
									<span class="text-purple-300 font-medium text-sm">{selectedEventDetail.new_stock_listing_date}</span>
								</div>
							{/if}
							{#if selectedEventDetail.ex_rights_date && isFieldRelevant('ex_rights_date', selectedEventDetail.event_type, selectedEventDetail.event_code)}
								<div class="flex justify-between items-center">
									<span class="text-slate-400 text-sm">{getFieldLabel('ex_rights_date', selectedEventDetail.event_type, selectedEventDetail.event_code)}</span>
									<span class="text-red-300 font-medium text-sm">{selectedEventDetail.ex_rights_date}</span>
								</div>
							{/if}
							{#if selectedEventDetail.allocation_base_date && isFieldRelevant('allocation_base_date', selectedEventDetail.event_type, selectedEventDetail.event_code)}
								<div class="flex justify-between items-center">
									<span class="text-slate-400 text-sm">{getFieldLabel('allocation_base_date', selectedEventDetail.event_type, selectedEventDetail.event_code)}</span>
									<span class="text-indigo-300 font-medium text-sm">{selectedEventDetail.allocation_base_date}</span>
								</div>
							{/if}
						</div>
					</div>
				{/if}

				<!-- 자본 정보 -->
				{#if selectedEventDetail.capital_after_change || selectedEventDetail.total_issued_stocks || selectedEventDetail.change_stocks || selectedEventDetail.discount_ratio}
					<div class="bg-slate-700/50 rounded-2xl p-4 border border-white/10">
						<h3 class="text-sm font-bold text-slate-300 mb-3 flex items-center space-x-2">
							<span>💰</span>
							<span>
								{#if selectedEventDetail.event_type.includes('실적발표')}
									실적 정보
								{:else if selectedEventDetail.event_type.includes('경영현황')}
									IR 정보
								{:else if selectedEventDetail.event_type.includes('신규상장')}
									상장 정보
								{:else if selectedEventDetail.event_type.includes('배당')}
									배당 정보
								{:else if selectedEventDetail.event_type.includes('분할')}
									분할 정보
								{:else if selectedEventDetail.event_type.includes('합병')}
									합병 정보
								{:else}
									자본 정보
								{/if}
							</span>
						</h3>
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
							{#if selectedEventDetail.capital_after_change && isFieldRelevant('capital_after_change', selectedEventDetail.event_type, selectedEventDetail.event_code)}
								<div class="flex justify-between items-center">
									<span class="text-slate-400 text-sm">{getFieldLabel('capital_after_change', selectedEventDetail.event_type, selectedEventDetail.event_code)}</span>
									<span class="text-yellow-300 font-bold text-sm">{selectedEventDetail.capital_after_change}</span>
								</div>
							{/if}
							{#if selectedEventDetail.total_issued_stocks && isFieldRelevant('total_issued_stocks', selectedEventDetail.event_type, selectedEventDetail.event_code)}
								<div class="flex justify-between items-center">
									<span class="text-slate-400 text-sm">{getFieldLabel('total_issued_stocks', selectedEventDetail.event_type, selectedEventDetail.event_code)}</span>
									<span class="text-blue-300 font-medium text-sm">{selectedEventDetail.total_issued_stocks}</span>
								</div>
							{/if}
							{#if selectedEventDetail.change_stocks && isFieldRelevant('change_stocks', selectedEventDetail.event_type, selectedEventDetail.event_code)}
								<div class="flex justify-between items-center">
									<span class="text-slate-400 text-sm">{getFieldLabel('change_stocks', selectedEventDetail.event_type, selectedEventDetail.event_code)}</span>
									<span class="text-green-300 font-medium text-sm">{selectedEventDetail.change_stocks}</span>
								</div>
							{/if}
							{#if selectedEventDetail.discount_ratio && isFieldRelevant('discount_ratio', selectedEventDetail.event_type, selectedEventDetail.event_code)}
								<div class="flex justify-between items-center">
									<span class="text-slate-400 text-sm">{getFieldLabel('discount_ratio', selectedEventDetail.event_type, selectedEventDetail.event_code)}</span>
									<span class="text-red-300 font-medium text-sm">{selectedEventDetail.discount_ratio}</span>
								</div>
							{/if}
						</div>
					</div>
				{/if}

				<!-- 비고 -->
				{#if selectedEventDetail.note}
					<div class="bg-slate-700/50 rounded-2xl p-4 border border-white/10">
						<h3 class="text-sm font-bold text-slate-300 mb-2 flex items-center space-x-2">
							<span>📝</span>
							<span>비고</span>
						</h3>
						<p class="text-slate-200 text-sm leading-relaxed">{selectedEventDetail.note}</p>
					</div>
				{/if}

				<!-- 액션 버튼 -->
				<div class="flex justify-end space-x-3 pt-4 border-t border-white/10">
					<button
						class="px-6 py-3 bg-gradient-to-r from-slate-600/80 to-slate-500/80 hover:from-slate-500/90 hover:to-slate-400/90 text-white rounded-xl font-medium transition-all duration-200 hover:scale-105 shadow-lg"
						on:click={() => selectedEventDetail = null}
					>
						닫기
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}

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
		background: linear-gradient(135deg, rgba(245, 101, 101, 0.8), rgba(239, 68, 68, 0.8));
		border-radius: 6px;
		border: 1px solid rgba(255, 255, 255, 0.1);
		box-shadow: 0 4px 16px rgba(245, 101, 101, 0.3);
	}

	:global(::-webkit-scrollbar-thumb:hover) {
		background: linear-gradient(135deg, rgba(245, 101, 101, 1), rgba(239, 68, 68, 1));
		box-shadow: 0 6px 20px rgba(245, 101, 101, 0.5);
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
		background: linear-gradient(135deg, rgba(245, 101, 101, 0.6), rgba(239, 68, 68, 0.6));
		border-radius: 4px;
		border: none;
		box-shadow: 0 2px 8px rgba(245, 101, 101, 0.2);
	}

	.scrollbar-thin::-webkit-scrollbar-thumb:hover {
		background: linear-gradient(135deg, rgba(245, 101, 101, 0.8), rgba(239, 68, 68, 0.8));
		box-shadow: 0 3px 12px rgba(245, 101, 101, 0.4);
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
			box-shadow: 0 0 20px rgba(34, 197, 94, 0.3), 0 0 40px rgba(34, 197, 94, 0.1);
		}
		50% { 
			box-shadow: 0 0 25px rgba(34, 197, 94, 0.4), 0 0 50px rgba(34, 197, 94, 0.15);
		}
	}

	.gentle-glow {
		animation: gentle-glow 3s ease-in-out infinite;
	}

	/* 부드러운 보더 애니메이션 (이번 달용) */
	@keyframes subtle-border {
		0%, 100% { 
			border-color: rgba(34, 197, 94, 0.6);
			box-shadow: 0 0 15px rgba(34, 197, 94, 0.2);
		}
		50% { 
			border-color: rgba(34, 197, 94, 0.8);
			box-shadow: 0 0 20px rgba(34, 197, 94, 0.3);
		}
	}

	.subtle-border {
		animation: subtle-border 4s ease-in-out infinite;
	}

	/* 스크롤바 스타일링 */
	.scrollbar-thin::-webkit-scrollbar {
		width: 6px;
	}
	
	.scrollbar-thin::-webkit-scrollbar-track {
		background: rgba(148, 163, 184, 0.1);
		border-radius: 3px;
	}
	
	.scrollbar-thin::-webkit-scrollbar-thumb {
		background: rgba(203, 213, 225, 0.3);
		border-radius: 3px;
		transition: background 0.2s ease;
	}
	
	.scrollbar-thin::-webkit-scrollbar-thumb:hover {
		background: rgba(203, 213, 225, 0.5);
	}

	/* 즉시 시각적 피드백 CSS */
	:global(body.processing) {
		cursor: wait !important;
		user-select: none;
	}

	:global(body.processing *) {
		cursor: wait !important;
	}

	/* 버튼 클릭 즉시 효과 */
	.btn-immediate-feedback {
		transform: scale(0.95);
		opacity: 0.8;
		transition: all 0.1s ease-out;
	}

	/* 처리 중 버튼 비활성화 효과 */
	.btn-processing {
		pointer-events: none;
		filter: saturate(0.7);
	}

	/* 로딩 펄스 효과 */
	.loading-pulse {
		animation: pulse 1.5s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% {
			opacity: 1;
		}
		50% {
			opacity: 0.5;
		}
	}
</style>
