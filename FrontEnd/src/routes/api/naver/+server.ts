import { naverAxiosInstance } from "$lib/axios-provider/AxiosProvider";
import axios from 'axios';
import { json } from '@sveltejs/kit';

export async function POST({ request }) {
  const formData = await request.formData();

	const bodyString = formData.get('body') as string;
	const body = JSON.parse(bodyString);

	const form = new FormData();

	for (const key in body.data) {
		form.append(key, body.data[key]);
	}

  switch (body.service) {
		case 'getSearchByNaver':
			return getSearchResultByNaverApi(body.serviceId, form);
  }
}

const NAVER_CLIENT_ID: string = 'dqMtE_iRIgA_8e9aB_dV';
const NAVER_CLIENT_SECRET: string = 'bg7d_nO_xJ';

/**
 * 네이버 api를 통해 검색 결과 가져오기
 * 데이터 형식 : 
 *  serviceId: 'blog' | 'news' | 'book' | 'encyc' | 'cafearticle' | 'kin' | 'webkr' | 'image' | 'shop' | 'doc', // 블로그-> blog, 뉴스-> news, 책-> book, 백과사전->encyc, 카페글->cafearticle, 지식인->kin, 웹문서->webkr, 이미지->image, 쇼핑->shop, 전문자료->doc, 성인검색어 판별->adult, 오타변환->errata
 *  requestData: {
      query: any, 
      display: number,  // 검색결과 출력건수 (10 ~ 100)
      start: number,    // 검색시작위치 (1 ~ 1000)
      sort: 'sim' | 'date', 
      filter: 'all' | 'large' | 'medium' | 'small'
    }
 */
const getSearchResultByNaverApi = async (serviceId: string, requestData: FormData) => {
  const newAxiosInstance = naverAxiosInstance();

  const response = await newAxiosInstance.get(
    `/v1/search/${serviceId}`,
    {
      params: Object.fromEntries(requestData.entries()),
      headers: {
        'X-Naver-Client-Id': NAVER_CLIENT_ID,
        'X-Naver-Client-Secret': NAVER_CLIENT_SECRET
      }
    },
  );

  return json(response.data);
}