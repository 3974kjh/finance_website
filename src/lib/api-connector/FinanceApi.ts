import { localAxiosInstance } from "../axios-provider/AxiosProvider";

/**
 * 주가 데이터 가져오기
 */
export const getFinanceDataList = async (requestData: {symbol: string, duration: number, isMonth: boolean}, cancelController?: AbortController) => {
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
}

/**
 * 주가 목록 가져오기
 */
export const getFinanceStockList = async (requestData: {symbol: string}, cancelController?: AbortController) => {
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
}

/**
 * 주가 예측 데이터 가져오기
 */
export const getExpectStockValue = async (requestData: {symbol: string, term: number}, cancelController?: AbortController) => {
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

		return response.data;
	} catch (error) {
		if (error) {
			console.error('에러 발생 : ' + error);
			return { isSuccess: false, data: 'fail-network' };
		}
	}
}

/**
 * 증시 별 예측 점수 기준으로 저장한 항목 조회
 * @param requestData 
 * @returns 
 */
export const getAllFinanceRankList = async (requestData: {stock: string}, cancelController?: AbortController) => {
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

		return response.data;
	} catch (error) {
		if (error) {
			console.error('에러 발생 : ' + error);
			return { isSuccess: false, data: 'fail-network' };
		}
	}
}

/**
 * 사고 판 주식 history 정보 조회
 * @param requestData 
 * @returns 
 */
export const getHistoryInfo = async (cancelController?: AbortController) => {
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
}

/**
 * 오늘 전체 주식 분석 정보 조회
 * @param requestData 
 * @returns 
 */
export const getTodayAnalyze = async (cancelController?: AbortController) => {
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
}