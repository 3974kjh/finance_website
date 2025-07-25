import axios from 'axios';
import { EnvConfig } from '../utils/EnvConfig';

/**
 * axios의 기본 URL 및 header의 content-type을 설정한다.
 * CloudFlare Pages 환경 변수 기반 백엔드 URL 사용
 * REST 통신을 하기 때문에 Content-Type은 application/json을 기본으로 했다.
 */
export const localAxiosInstance = () => {
	return axios.create({
		baseURL: EnvConfig.backendUrl,
		headers: {
			'Content-Type': 'application/json'
		}
	});
}

/**
 * axios의 기본 URL 및 header의 content-type을 설정한다.
 * REST 통신을 하기 때문에 Content-Type은 application/json을 기본으로 했다.
 */
export const naverAxiosInstance = () => {
	return axios.create({
		baseURL: 'https://openapi.naver.com',
		headers: {
			'Content-Type': 'application/json'
		}
	});
}

/**
 * axios의 기본 URL 및 header의 content-type을 설정한다.
 * REST 통신을 하기 때문에 Content-Type은 application/json을 기본으로 했다.
 */
export const kakaoAccessTokenAxiosInstance = () => {
	return axios.create({
		baseURL: 'https://kauth.kakao.com/oauth/token',
		headers: {
			'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'
		}
	});
}

/**
 * 전송취소
 * @param cancelController 
 * @returns 
 */
export const cancelRequest = (cancelController: AbortController | null) => {
	if (!!!cancelController) {
		return;
	}

	cancelController?.abort();
}