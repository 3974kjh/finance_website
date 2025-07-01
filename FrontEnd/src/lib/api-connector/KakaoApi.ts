import axios from 'axios';

// 브라우저 환경 감지 함수
const isBrowserEnvironment = () => {
  return typeof window !== 'undefined' && typeof document !== 'undefined';
};

// 환경 변수에서 백엔드 URL 가져오기
const getBackendUrl = () => {
  const backendUrl = isBrowserEnvironment()
    ? (import.meta.env.VITE_BACKEND_URL || 'http://localhost:8250')
    : (process.env.VITE_BACKEND_URL || 'http://localhost:8250');
  
  return backendUrl;
};

// 카카오 API 환경 변수 가져오기
const getKakaoConfig = () => {
  if (isBrowserEnvironment()) {
    return {
      apiKey: import.meta.env.VITE_KAKAO_API_KEY || import.meta.env.PUBLIC_API_KEY || '',
      redirectUri: import.meta.env.VITE_KAKAO_REDIRECT_URI || import.meta.env.PUBLIC_REDIRECT_URI || 'http://localhost:7150/oauth'
    };
  } else {
    return {
      apiKey: process.env.VITE_KAKAO_API_KEY || process.env.PUBLIC_API_KEY || '',
      redirectUri: process.env.VITE_KAKAO_REDIRECT_URI || process.env.PUBLIC_REDIRECT_URI || 'http://localhost:7150/oauth'
    };
  }
};

/**
 * 카카오 api를 통해 결과 데이터 전송 (백엔드 API 전용)
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
    
    // 카카오 설정 가져오기
    const kakaoConfig = getKakaoConfig();
    console.log('🔧 카카오 설정:', {
      apiKey: kakaoConfig.apiKey ? `${kakaoConfig.apiKey.slice(0, 10)}...` : 'None',
      redirectUri: kakaoConfig.redirectUri
    });
    
    // 백엔드 서버 호출
    const backendUrl = getBackendUrl();
    console.log(`🔄 백엔드 카카오 API 호출: ${backendUrl}/api/kakao/send`);
    
    const requestPayload = {
      accessCode: accessCode,
      accessToken: accessToken,
      redirectUri: kakaoConfig.redirectUri, // redirectUri 추가
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
          message: '백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.' 
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