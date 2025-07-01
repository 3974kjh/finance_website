import { naverAxiosInstance } from "$lib/axios-provider/AxiosProvider";
import axios from 'axios';
import { json, error } from '@sveltejs/kit';

// POST 메서드 핸들러
export async function POST({ request }) {
  try {
    const formData = await request.formData();

    const bodyString = formData.get('body') as string;
    if (!bodyString) {
      return error(400, 'Body is required');
    }

    const body = JSON.parse(bodyString);

    const form = new FormData();
    for (const key in body.data) {
      form.append(key, body.data[key]);
    }

    switch (body.service) {
      case 'getSearchByNaver':
        return getSearchResultByNaverApi(body.serviceId, form);
      default:
        return error(400, 'Invalid service type');
    }
  } catch (err) {
    console.error('Naver API Error:', err);
    return error(500, 'Internal server error');
  }
}

// GET 메서드도 지원 (CloudFlare Pages 호환성)
export async function GET({ url }) {
  try {
    const serviceId = url.searchParams.get('serviceId') || 'news';
    const query = url.searchParams.get('query');
    const display = url.searchParams.get('display') || '10';
    const start = url.searchParams.get('start') || '1';
    const sort = url.searchParams.get('sort') || 'sim';

    if (!query) {
      return error(400, 'Query parameter is required');
    }

    const form = new FormData();
    form.append('query', query);
    form.append('display', display);
    form.append('start', start);
    form.append('sort', sort);

    return getSearchResultByNaverApi(serviceId, form);
  } catch (err) {
    console.error('Naver API GET Error:', err);
    return error(500, 'Internal server error');
  }
}

// 환경 변수에서 API 키 가져오기 (CloudFlare Pages 호환)
const NAVER_CLIENT_ID: string = process.env.NAVER_CLIENT_ID || 'dqMtE_iRIgA_8e9aB_dV';
const NAVER_CLIENT_SECRET: string = process.env.NAVER_CLIENT_SECRET || 'bg7d_nO_xJ';

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
  try {
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
  } catch (err) {
    console.error('Naver Search API Error:', err);
    return error(500, 'Failed to fetch data from Naver API');
  }
}