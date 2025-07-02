import axios from 'axios';
import { EnvConfig } from '../utils/EnvConfig';

/**
 * 카카오 api를 통해 결과 데이터 전송 (백엔드 API 전용)
 * CloudFlare Pages 환경 변수 기반 설정
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
    console.log('🎯 카카오 API 호출 시작 [' + new Date().toISOString() + ']');
    
    // CloudFlare Pages 환경 변수 상태 확인
    EnvConfig.logEnvStatus();
    
    // 환경 변수 유효성 검사
    if (!EnvConfig.validateAll()) {
      return {
        isFail: true,
        token: '',
        message: '환경 변수가 올바르게 설정되지 않았습니다. CloudFlare Pages Dashboard에서 환경 변수를 확인해주세요.'
      };
    }
    
    // 카카오 설정 가져오기
    const kakaoConfig = EnvConfig.kakao;
    const backendUrl = EnvConfig.backendUrl;
    
    console.log(`🔄 백엔드 카카오 API 호출: ${backendUrl}/api/kakao/send`);
    
    const requestPayload = {
      accessCode: accessCode,
      accessToken: accessToken,
      redirectUri: kakaoConfig.redirectUri,
      link: link,
      data: requestData
    };
    
    console.log('📤 요청 데이터:', {
      accessCode: accessCode ? `${accessCode.slice(0, 10)}...` : 'None',
      accessToken: accessToken ? `${accessToken.slice(0, 10)}...` : 'None',
      redirectUri: requestPayload.redirectUri,
      link: link,
      data: requestData
    });
    
    const response = await axios.post(`${backendUrl}/api/kakao/send`, requestPayload, {
      timeout: 10000  // 10초 타임아웃 설정
    });

    console.log('✅ 백엔드 카카오 응답 성공:', response.data);

    // 백엔드 응답 구조 처리
    if (response.data) {
      return {
        isFail: response.data.isFail || false,
        token: response.data.token || accessToken,
        message: response.data.message || ''
      };
    } else {
      console.error('❌ 백엔드 카카오 응답 형식 오류:', response.data);
      return { 
        isFail: true, 
        token: '', 
        message: '백엔드 응답 형식 오류' 
      };
    }
	} catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error('❌ 카카오 API 호출 실패:', errorMessage);
    console.error('❌ 에러 상세:', error);
    
    // 네트워크 오류인지 확인
    if (axios.isAxiosError(error)) {
      if (error.code === 'ECONNREFUSED' || error.code === 'NETWORK_ERROR') {
        return { 
          isFail: true, 
          token: '', 
          message: `백엔드 서버(${EnvConfig.backendUrl})에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.` 
        };
      }
      
      if (error.response) {
        const errorDetail = error.response.data?.message || error.response.statusText;
        return { 
          isFail: true, 
          token: '', 
          message: `서버 오류: ${error.response.status} - ${errorDetail}` 
        };
      }
      
      if (error.request) {
        return { 
          isFail: true, 
          token: '', 
          message: '서버로부터 응답을 받지 못했습니다.' 
        };
      }
    }
    
    return { 
      isFail: true, 
      token: '', 
      message: `카카오 API 호출 중 오류 발생: ${errorMessage}` 
    };
	}
}