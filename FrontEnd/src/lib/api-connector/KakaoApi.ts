import axios from 'axios';

/**
 * 카카오 api를 통해 결과 데이터 전송
 */
export const sendFinanceResultByKakaoApi = async (
  accessCode: string,
  accessToken: string,
  link: {
    'web_url': string,
    'mobile_web_url': string
  } | Object,
  requestData: {
    object_type: string, // 'text' 기본 값 
    text: string,  // 전송문자
    button_title?: string
  }) => {
	try {
    const body = {
      service: 'sendResultToKakao',
      accessCode: accessCode,
      accessToken: accessToken,
      link: link,
      data: requestData
    }

    const formData = new FormData();
    formData.append('body', JSON.stringify(body));

		const response = await axios.post(`/api/kakao`, formData);

		return response.data;
	} catch (error) {
		if (error) {
			console.error('에러 발생 : ' + error);
			return { isFail: true, token: '' };
		}
	}
}