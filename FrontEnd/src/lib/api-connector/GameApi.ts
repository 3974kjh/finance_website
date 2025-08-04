import { localAxiosInstance } from "../axios-provider/AxiosProvider";
import { stockDataCache, stockListCache, analysisCache, cachedApiCall, generateTimeBasedKey, generateDateBasedKey } from "../utils/CacheManager";

/**
 * 게임 스코어 저장
 */
export const saveGameScore = async (requestData: {
	gameType: string, 
	userId: string, 
	mode: string, 
	score: number
}, cancelController?: AbortController) => {
	try {
		const newAxiosInstance = localAxiosInstance();

		if (!!cancelController) {
			newAxiosInstance.defaults.signal = cancelController.signal;
		}

		const response = await newAxiosInstance.post(
			'/save_game_score/',
			requestData
		);

		// 저장 후 관련 캐시 무효화
		analysisCache.invalidatePattern(`game_scores_${requestData.gameType}`);

		return response.data;
	} catch (error) {
		if (error) {
			console.error('게임 스코어 저장 에러 발생 : ' + error);
			return { success: false, message: 'fail-network' };
		}
	}
}

/**
 * 게임 스코어 목록 조회 (캐시 적용)
 */
export const getGameScores = async (requestData: {gameType?: string}, cancelController?: AbortController) => {
	// 게임 스코어는 시간 기반 캐시 (5분 간격)
	const cacheKey = generateTimeBasedKey(`game_scores_${requestData.gameType || 'all'}`, 5);
	
	return cachedApiCall(
		cacheKey,
		async () => {
			try {
				const newAxiosInstance = localAxiosInstance();

				if (!!cancelController) {
					newAxiosInstance.defaults.signal = cancelController.signal;
				}

				const response = await newAxiosInstance.post(
					'/get_game_scores/',
					requestData
				);

				return response.data;
			} catch (error) {
				if (error) {
					console.error('게임 스코어 조회 에러 발생 : ' + error);
					return { success: false, data: 'fail-network' };
				}
			}
		},
		analysisCache,
		30 // 게임 스코어는 30분 캐시
	);
}

/**
 * 특정 게임의 랭킹 조회 (캐시 적용)
 */
export const getGameRanking = async (requestData: {
	gameType: string, 
	mode?: string, 
	limit?: number
}, cancelController?: AbortController) => {
	// 랭킹은 시간 기반 캐시 (10분 간격)
	const cacheKey = generateTimeBasedKey(`game_ranking_${requestData.gameType}_${requestData.mode || 'all'}_${requestData.limit || 10}`, 10);
	
	return cachedApiCall(
		cacheKey,
		async () => {
			try {
				const newAxiosInstance = localAxiosInstance();

				if (!!cancelController) {
					newAxiosInstance.defaults.signal = cancelController.signal;
				}

				const response = await newAxiosInstance.post(
					'/get_game_ranking/',
					requestData
				);

				return response.data;
			} catch (error) {
				if (error) {
					console.error('게임 랭킹 조회 에러 발생 : ' + error);
					return { success: false, data: 'fail-network' };
				}
			}
		},
		analysisCache,
		15 // 게임 랭킹은 15분 캐시
	);
}