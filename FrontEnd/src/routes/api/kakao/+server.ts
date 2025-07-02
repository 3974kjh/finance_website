import { kakaoAccessTokenAxiosInstance } from "$lib/axios-provider/AxiosProvider";
import { json } from '@sveltejs/kit';
import axios from 'axios';
import { EnvConfig } from "$lib/utils/EnvConfig";

const KAKAO_REST_API_KEY = EnvConfig.kakao.apiKey;
const REDIRECT_URI = EnvConfig.kakao.redirectUri;

export async function POST({ request }) {
  const formData = await request.formData();

	const bodyString = formData.get('body') as string;
	const body = JSON.parse(bodyString);

	const form = new FormData();

	for (const key in body.data) {
		form.append(key, body.data[key]);
	}

  switch (body.service) {
		case 'sendResultToKakao':
			return sendResultToKakaoApi(body.accessCode, body.accessToken, body.link, form);
  }
}

const getKakaoAccessToken = async (accessCode: string) => {
  const kakaoAccessTokenAxios = kakaoAccessTokenAxiosInstance();

  const response = await kakaoAccessTokenAxios.post('', {
    grant_type: 'authorization_code',
    client_id: KAKAO_REST_API_KEY,
    redirect_uri: REDIRECT_URI,
    code: accessCode
  });

  return response?.data?.access_token;
}

const sendResultToKakaoApi = async (
  accessCode: string,
  accessToken: string,
  requestLink: {'web_url': string, 'mobile_web_url': string}, 
  requestData: FormData
) => {
  try {
    let kakaoAccessToken: string = '';

    kakaoAccessToken = !!!accessToken ? await getKakaoAccessToken(accessCode) : accessToken;

    if (!!!kakaoAccessToken) {
      return json({
        'isFail': true,
        'token': ''
      })
    }

    const kakaoSendAxiosInstance = axios.create({
      baseURL: '',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': `Bearer ${kakaoAccessToken}`
      },
    });

    const requestParam = Object.fromEntries(requestData.entries());
    let objectType = requestParam?.object_type ?? 'text';
    let text = requestParam?.text ?? '전달 데이터 없음';
    let link = requestLink;
    let buttonTitle = requestParam?.button_title ?? undefined;

    const response = await kakaoSendAxiosInstance.post('https://kapi.kakao.com/v2/api/talk/memo/default/send', {
      template_object: JSON.stringify({
        object_type: objectType,
        text: text,
        link: link,
        button_title: buttonTitle
      })
    });

    return json({
      'isFail': false,
      'token': kakaoAccessToken
    });
  } catch (error) {
    return json({
      'isFail': true,
      'token': ''
    });
	}
}