import axios from 'axios';

/**
 * 네이버 api를 통해 검색 결과 가져오기
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
}