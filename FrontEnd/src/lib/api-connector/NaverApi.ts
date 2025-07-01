import axios from 'axios';
import { newsCache, cachedApiCall, generateTimeBasedKey } from "../utils/CacheManager";
import { browser } from '$app/environment';

// 환경 변수에서 백엔드 URL 가져오기
const getBackendUrl = () => {
  const backendUrl = browser 
    ? (import.meta.env.VITE_BACKEND_URL || 'http://localhost:8250')
    : (process.env.VITE_BACKEND_URL || 'http://localhost:8250');
  
  console.log('🔍 환경 정보:', {
    browser,
    viteBackendUrl: browser ? import.meta.env.VITE_BACKEND_URL : process.env.VITE_BACKEND_URL,
    finalBackendUrl: backendUrl,
    allEnvVars: browser ? import.meta.env : 'SSR환경'
  });
  
  return backendUrl;
};

/**
 * 네이버 api를 통해 검색 결과 가져오기 (캐시 적용)
 * 모든 환경에서 백엔드 우선, 실패시 SSR 폴백
 */
export const getSearchResultByNaverApi = async (
  serviceId: 'blog' | 'news' | 'book' | 'encyc' | 'cafearticle' | 'kin' | 'webkr' | 'image' | 'shop' | 'doc', // 블로그-> blog, 뉴스-> news, 책-> book, 백과사전->encyc, 카페글->cafearticle, 지식인->kin, 웹문서->webkr, 이미지->image, 쇼핑->shop, 전문자료->doc, 성인검색어 판별->adult, 오타변환->errata
  requestData: {
    query: any, 
    display: number,  // 검색결과 출력건수 (10 ~ 100)
    start: number,    // 검색시작위치 (1 ~ 1000)
    sort: 'sim' | 'date', 
    filter: 'all' | 'large' | 'medium' | 'small'
  }) => {
	
	console.log('🚀 네이버 API 함수 시작:', {
		serviceId,
		query: requestData.query,
		requestData
	});

	// 캐시 키 생성 (서비스ID, 쿼리, 정렬방식을 조합)
	// 뉴스는 빠르게 변하므로 15분 간격으로 캐시
	const cacheKey = generateTimeBasedKey(
		`naver_${serviceId}_${requestData.query}_${requestData.sort}_${requestData.display}_${requestData.start}`, 
		15
	);
	
	console.log('💾 캐시 키 생성:', cacheKey);
	
	return cachedApiCall(
		cacheKey,
		async () => {
			console.log('🎯 캐시되지 않은 새로운 API 호출 시작');
			
			// 먼저 백엔드 서버 시도
			try {
				const backendUrl = getBackendUrl();
				console.log(`🔄 백엔드 API 호출 시도: ${backendUrl}/api/naver/${serviceId}`);
				
				const response = await axios.post(`${backendUrl}/api/naver/${serviceId}`, {
					query: requestData.query,
					display: requestData.display,
					start: requestData.start,
					sort: requestData.sort,
					filter: requestData.filter
				}, {
					timeout: 5000  // 5초 타임아웃 설정
				});

				console.log('✅ 백엔드 응답 성공:', response.data);

				// 백엔드 응답 구조 처리
				if (response.data && response.data.isSuccess && response.data.data) {
					return response.data.data;
				} else {
					console.error('❌ 백엔드 응답 형식 오류:', response.data);
					throw new Error('Invalid backend response format');
				}
			} catch (backendError) {
				const errorMessage = backendError instanceof Error ? backendError.message : String(backendError);
				console.warn(`⚠️ 백엔드 API 실패, SSR로 폴백: ${errorMessage}`);
				console.warn('⚠️ 백엔드 에러 상세:', backendError);
				
				// 백엔드 실패시 SSR API로 폴백
				try {
					console.log('🔄 SSR API 폴백 시도');
					const body = {
						service: 'getSearchByNaver',
						serviceId: serviceId,
						data: requestData
					}

					const formData = new FormData();
					formData.append('body', JSON.stringify(body));

					const ssrResponse = await axios.post(`/api/naver`, formData);
					
					console.log('✅ SSR API 응답 성공:', ssrResponse.data);
					return ssrResponse.data;
				} catch (ssrError) {
					const ssrErrorMessage = ssrError instanceof Error ? ssrError.message : String(ssrError);
					console.error(`❌ SSR API도 실패: ${ssrErrorMessage}`);
					console.error('❌ SSR 에러 상세:', ssrError);
					return { isSuccess: false, data: 'fail-network' };
				}
			}
		},
		newsCache,
		serviceId === 'news' ? 15 : 30 // 뉴스는 15분, 다른 콘텐츠는 30분 캐시
	);
}