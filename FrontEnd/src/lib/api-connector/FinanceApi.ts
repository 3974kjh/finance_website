import { localAxiosInstance } from "../axios-provider/AxiosProvider";
import { stockDataCache, stockListCache, analysisCache, cachedApiCall, generateTimeBasedKey, generateDateBasedKey } from "../utils/CacheManager";

/**
 * 로그인 요청
 */
export const loginUser = async (requestData: {username: string, password: string}, cancelController?: AbortController) => {
	try {
		const newAxiosInstance = localAxiosInstance();

		if (!!cancelController) {
			newAxiosInstance.defaults.signal = cancelController.signal;
		}

		const response = await newAxiosInstance.post(
			'/login/',
			requestData
		);

		return response.data;
	} catch (error) {
		if (error) {
			console.error('로그인 에러 발생 : ' + error);
			return { success: false, message: 'fail-network' };
		}
	}
}

/**
 * 주가 데이터 가져오기 (캐시 적용)
 */
export const getFinanceDataList = async (requestData: {symbol: string, duration: number, isMonth: boolean}, cancelController?: AbortController) => {
	// 캐시 키 생성 (심볼, 기간, 월/주 단위를 조합)
	const cacheKey = generateTimeBasedKey(`stock_data_${requestData.symbol}_${requestData.duration}_${requestData.isMonth}`, 30);
	
	return cachedApiCall(
		cacheKey,
		async () => {
			try {
				const newAxiosInstance = localAxiosInstance();

				if (!!cancelController) {
					newAxiosInstance.defaults.signal = cancelController.signal;
				}

				const response = await newAxiosInstance.post(
					'/stock_data/',
					requestData
				);

				return response.data;
			} catch (error) {
				if (error) {
					console.error('에러 발생 : ' + error);
					return { isSuccess: false, data: 'fail-network' };
				}
			}
		},
		stockDataCache,
		60 // 주가 데이터는 1시간 캐시
	);
}

/**
 * 주가 목록 가져오기 (캐시 적용)
 */
export const getFinanceStockList = async (requestData: {symbol: string}, cancelController?: AbortController) => {
	// 주식 목록은 하루에 한 번만 갱신되므로 날짜 기반 캐시
	const cacheKey = generateDateBasedKey(`stock_list_${requestData.symbol}`);
	
	return cachedApiCall(
		cacheKey,
		async () => {
			try {
				const newAxiosInstance = localAxiosInstance();

				if (!!cancelController) {
					newAxiosInstance.defaults.signal = cancelController.signal;
				}

				const response = await newAxiosInstance.post(
					'/stock_list/',
					requestData
				);

				return response.data;
			} catch (error) {
				if (error) {
					console.error('에러 발생 : ' + error);
					return { isSuccess: false, data: 'fail-network' };
				}
			}
		},
		stockListCache,
		240 // 주식 목록은 4시간 캐시
	);
}

/**
 * 주가 예측 데이터 가져오기 (캐시 적용)
 */
export const getExpectStockValue = async (requestData: {symbol: string, term: number}, cancelController?: AbortController) => {
	// 예측 데이터는 시간 기반 캐시 (2시간 간격)
	const cacheKey = generateTimeBasedKey(`expect_stock_${requestData.symbol}_${requestData.term}`, 120);
	
	return cachedApiCall(
		cacheKey,
		async () => {
			try {
				const newAxiosInstance = localAxiosInstance();

				if (!!cancelController) {
					newAxiosInstance.defaults.signal = cancelController.signal;
				}

				const response = await newAxiosInstance.post(
					'/expect_stock/',
					requestData
				);

				return response.data;
			} catch (error) {
				if (error) {
					console.error('에러 발생 : ' + error);
					return { isSuccess: false, data: 'fail-network' };
				}
			}
		},
		analysisCache,
		120 // 예측 데이터는 2시간 캐시
	);
}

/**
 * 증시 별 예측 점수 기준으로 sort한 목록 저장
 * @param requestData 
 * @returns 
 */
export const saveFinanceRankList = async (requestData: {stock: string, data: any}, cancelController?: AbortController) => {
	try {
		const newAxiosInstance = localAxiosInstance();

		if (!!cancelController) {
			newAxiosInstance.defaults.signal = cancelController.signal;
		}

		const response = await newAxiosInstance.post(
			'/save_finance_rank/',
			requestData
		);

		// 저장 후 관련 캐시 무효화
		analysisCache.invalidatePattern(`finance_rank_${requestData.stock}`);

		return response.data;
	} catch (error) {
		if (error) {
			console.error('에러 발생 : ' + error);
			return { isSuccess: false, data: 'fail-network' };
		}
	}
}

/**
 * 증시 별 예측 점수 기준으로 저장한 항목 조회 (캐시 적용)
 * @param requestData 
 * @returns 
 */
export const getAllFinanceRankList = async (requestData: {stock: string}, cancelController?: AbortController) => {
	// 분석 결과는 날짜 기반 캐시
	const cacheKey = generateDateBasedKey(`finance_rank_${requestData.stock}`);
	
	return cachedApiCall(
		cacheKey,
		async () => {
			try {
				const newAxiosInstance = localAxiosInstance();

				if (!!cancelController) {
					newAxiosInstance.defaults.signal = cancelController.signal;
				}

				const response = await newAxiosInstance.post(
					'/get_finance_rank/',
					requestData
				);

				return response.data;
			} catch (error) {
				if (error) {
					console.error('에러 발생 : ' + error);
					return { isSuccess: false, data: 'fail-network' };
				}
			}
		},
		analysisCache,
		180 // 분석 결과는 3시간 캐시
	);
}

/**
 * 사고 판 주식 history 정보 저장
 * @param requestData 
 * @returns 
 */
export const saveHistoryInfo = async (requestData: {data: any}, cancelController?: AbortController) => {
	try {
		const newAxiosInstance = localAxiosInstance();

		if (!!cancelController) {
			newAxiosInstance.defaults.signal = cancelController.signal;
		}

		const response = await newAxiosInstance.post(
			'/save_buy_history/',
			requestData
		);

		// 저장 후 히스토리 캐시 무효화
		analysisCache.invalidatePattern('buy_history');

		return response.data;
	} catch (error) {
		if (error) {
			console.error('에러 발생 : ' + error);
			return { isSuccess: false, data: 'fail-network' };
		}
	}
}

/**
 * 사고 판 주식 history 정보 조회 (캐시 적용)
 * @param requestData 
 * @returns 
 */
export const getHistoryInfo = async (cancelController?: AbortController) => {
	// 히스토리는 시간 기반 캐시 (10분 간격)
	const cacheKey = generateTimeBasedKey('buy_history', 10);
	
	return cachedApiCall(
		cacheKey,
		async () => {
			try {
				const newAxiosInstance = localAxiosInstance();

				if (!!cancelController) {
					newAxiosInstance.defaults.signal = cancelController.signal;
				}

				const response = await newAxiosInstance.post(
					'/get_buy_history/',
					{}
				);

				return response.data;
			} catch (error) {
				if (error) {
					console.error('에러 발생 : ' + error);
					return { isSuccess: false, data: 'fail-network' };
				}
			}
		},
		analysisCache,
		30 // 히스토리는 30분 캐시
	);
}

/**
 * 오늘 전체 주식 분석 정보 조회 (캐시 적용)
 * @param requestData 
 * @returns 
 */
export const getTodayAnalyze = async (cancelController?: AbortController) => {
	// 오늘 분석은 날짜 기반 캐시
	const cacheKey = generateDateBasedKey('today_analyze');
	
	return cachedApiCall(
		cacheKey,
		async () => {
			try {
				const newAxiosInstance = localAxiosInstance();

				if (!!cancelController) {
					newAxiosInstance.defaults.signal = cancelController.signal;
				}

				const response = await newAxiosInstance.post(
					'/get_today_analyze/',
					{}
				);

				return response.data;
			} catch (error) {
				if (error) {
					console.error('에러 발생 : ' + error);
					return { isSuccess: false, data: 'fail-network' };
				}
			}
		},
		analysisCache,
		60 // 오늘 분석은 1시간 캐시
	);
}

/**
 * 실시간 검색어 가져오기 (캐시 적용)
 */
export const getRealtimeSearchTerms = async (cancelController?: AbortController) => {
	// 실시간 검색어는 30분 간격으로 캐시
	const cacheKey = generateTimeBasedKey('get_realtime_search', 30);
	
	return cachedApiCall(
		cacheKey,
		async () => {
			try {
				const newAxiosInstance = localAxiosInstance();

				if (!!cancelController) {
					newAxiosInstance.defaults.signal = cancelController.signal;
				}

				const response = await newAxiosInstance.post(
					'/get_realtime_search/',
					{}
				);

				return response.data;
			} catch (error) {
				if (error) {
					console.error('에러 발생 : ' + error);
					return { isSuccess: false, data: 'fail-network' };
				}
			}
		},
		analysisCache,
		30 // 실시간 검색어는 30분 캐시
	);
}

/**
 * 경제 캘린더 데이터 가져오기 (캐시 적용)
 */
export const getEconomicCalendar = async (requestData: {
	year: number, 
	countries?: string[], 
	importance_levels?: number[]
}, cancelController?: AbortController) => {
	// 경제 캘린더는 날짜 기반 캐시 (연도, 국가, 중요도 레벨 조합으로)
	const countriesStr = requestData.countries ? requestData.countries.sort().join(',') : 'all';
	const importanceStr = requestData.importance_levels ? requestData.importance_levels.sort().join(',') : 'all';
	const cacheKey = generateDateBasedKey(`economic_calendar_${requestData.year}_${countriesStr}_${importanceStr}`);
	
	return cachedApiCall(
		cacheKey,
		async () => {
			try {
				const newAxiosInstance = localAxiosInstance();

				if (!!cancelController) {
					newAxiosInstance.defaults.signal = cancelController.signal;
				}

				const response = await newAxiosInstance.post(
					'/get_economic_calendar/',
					requestData
				);

				return response.data;
			} catch (error) {
				if (error) {
					console.error('경제 캘린더 데이터 요청 실패 : ' + error);
					return { success: false, error: 'fail-network' };
				}
			}
		},
		analysisCache,
		360 // 경제 캘린더는 6시간 캐시 (하루에 몇 번만 업데이트)
	);
}

/**
 * 주식 일정 캘린더 데이터 가져오기 (캐시 적용)
 */
export const getStockCalendar = async (requestData: {
	year: number, 
	months?: number[]
}, cancelController?: AbortController) => {
	// 주식 일정은 날짜 기반 캐시 (연도, 월 조합으로)
	const monthsStr = requestData.months ? requestData.months.sort().join(',') : 'all';
	const cacheKey = generateDateBasedKey(`stock_calendar_${requestData.year}_${monthsStr}`);
	
	return cachedApiCall(
		cacheKey,
		async () => {
			try {
				const newAxiosInstance = localAxiosInstance();

				if (!!cancelController) {
					newAxiosInstance.defaults.signal = cancelController.signal;
				}

				const response = await newAxiosInstance.post(
					'/get_stock_calendar/',
					requestData
				);

				return response.data;
			} catch (error) {
				if (error) {
					console.error('주식 일정 캘린더 데이터 요청 실패 : ' + error);
					return { success: false, error: 'fail-network' };
				}
			}
		},
		analysisCache,
		240 // 주식 일정은 4시간 캐시
	);
}

/**
 * 한국 공휴일 데이터 가져오기 (캐시 적용)
 */
export const getKoreanHolidays = async (requestData: {
	year: number
}, cancelController?: AbortController) => {
	// 한국 공휴일은 연도별로 캐시 (공휴일은 거의 변경되지 않으므로 하루 단위 캐시)
	const cacheKey = generateDateBasedKey(`korean_holidays_${requestData.year}`);
	
	return cachedApiCall(
		cacheKey,
		async () => {
			try {
				const newAxiosInstance = localAxiosInstance();

				if (!!cancelController) {
					newAxiosInstance.defaults.signal = cancelController.signal;
				}

				const response = await newAxiosInstance.post(
					'/get_korean_holidays/',
					requestData
				);

				return response.data;
			} catch (error) {
				if (error) {
					console.error('한국 공휴일 데이터 요청 실패 : ' + error);
					return { success: false, error: 'fail-network' };
				}
			}
		},
		analysisCache,
		1440 // 한국 공휴일은 24시간 캐시 (하루에 한 번만 체크)
	);
}