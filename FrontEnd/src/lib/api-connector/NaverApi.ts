import axios from 'axios';
import { newsCache, cachedApiCall, generateTimeBasedKey } from "../utils/CacheManager";

/**
 * 네이버 api를 통해 검색 결과 가져오기 (캐시 적용)
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
	
	// 캐시 키 생성 (서비스ID, 쿼리, 정렬방식을 조합)
	// 뉴스는 빠르게 변하므로 15분 간격으로 캐시
	const cacheKey = generateTimeBasedKey(
		`naver_${serviceId}_${requestData.query}_${requestData.sort}_${requestData.display}_${requestData.start}`, 
		15
	);
	
	return cachedApiCall(
		cacheKey,
		async () => {
			try {
				const body = {
					service: 'getSearchByNaver',
					serviceId: serviceId,
					data: requestData
				}

				const formData = new FormData();
				formData.append('body', JSON.stringify(body));

				const response = await axios.post(`/api/naver`, formData);

				return response.data;
			} catch (error) {
				if (error) {
					console.error('에러 발생 : ' + error);
					return { isSuccess: false, data: 'fail-network' };
				}
			}
		},
		newsCache,
		serviceId === 'news' ? 15 : 30 // 뉴스는 15분, 다른 콘텐츠는 30분 캐시
	);
}