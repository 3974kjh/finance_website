// CloudFlare Pages 환경 변수 관리 유틸리티

// 브라우저 환경 감지
const isBrowserEnvironment = () => {
  return typeof window !== 'undefined' && typeof document !== 'undefined';
};

// 환경 변수 가져오기 (CloudFlare Pages 최적화)
const getEnvVar = (key: string, fallback: string = ''): string => {
  if (isBrowserEnvironment()) {
    return import.meta.env[key] || fallback;
  } else {
    return process.env[key] || fallback;
  }
};

// 환경 변수 검증
const validateEnvVar = (key: string, value: string, required: boolean = true): boolean => {
  if (required && (!value || value.trim() === '')) {
    console.error(`❌ 필수 환경 변수가 설정되지 않았습니다: ${key}`);
    return false;
  }
  return true;
};

// 환경 설정 클래스
export class EnvConfig {
  // 개발/운영 환경 구분
  static get isDevelopment(): boolean {
    return getEnvVar('VITE_NODE_ENV', 'development') === 'development';
  }

  static get isProduction(): boolean {
    return getEnvVar('VITE_NODE_ENV', 'development') === 'production';
  }

  // 백엔드 URL 설정
  static get backendUrl(): string {
    const url = getEnvVar('VITE_BACKEND_URL', '');
    if (!validateEnvVar('VITE_BACKEND_URL', url, true)) {
      console.warn('⚠️ VITE_BACKEND_URL이 설정되지 않아 기본값을 사용합니다.');
      return 'http://localhost:8250'; // 로컬 개발용 기본값
    }
    return url;
  }

  // 카카오 API 설정
  static get kakao() {
    const apiKey = getEnvVar('VITE_KAKAO_API_KEY', '');
    const redirectUri = getEnvVar('VITE_KAKAO_REDIRECT_URI', '');
    
    // 환경 변수 검증
    validateEnvVar('VITE_KAKAO_API_KEY', apiKey, true);
    
    // redirectUri가 없으면 현재 도메인 기반으로 생성
    let finalRedirectUri = redirectUri;
    if (!redirectUri && isBrowserEnvironment()) {
      const currentDomain = window.location.origin;
      finalRedirectUri = `${currentDomain}/oauth`;
      console.log(`🔧 카카오 Redirect URI 자동 생성: ${finalRedirectUri}`);
    }

    return {
      apiKey,
      redirectUri: finalRedirectUri || 'http://localhost:7150/oauth', // 기본값
    };
  }

  // 네이버 API 설정
  static get naver() {
    const clientId = getEnvVar('VITE_NAVER_CLIENT_ID', '');
    const clientSecret = getEnvVar('VITE_NAVER_CLIENT_SECRET', '');
    
    // 환경 변수 검증
    validateEnvVar('VITE_NAVER_CLIENT_ID', clientId, true);
    validateEnvVar('VITE_NAVER_CLIENT_SECRET', clientSecret, true);

    return {
      clientId,
      clientSecret,
    };
  }

  // 환경 변수 상태 출력 (디버깅용)
  static logEnvStatus(): void {
    console.group('🔧 환경 변수 상태 확인 (CloudFlare Pages)');
    console.log('환경:', this.isDevelopment ? 'Development' : 'Production');
    console.log('백엔드 URL:', this.backendUrl);
    console.log('카카오 API 키:', this.kakao.apiKey ? `${this.kakao.apiKey.slice(0, 10)}...` : 'None');
    console.log('카카오 Redirect URI:', this.kakao.redirectUri);
    console.log('네이버 Client ID:', this.naver.clientId ? `${this.naver.clientId.slice(0, 10)}...` : 'None');
    console.log('네이버 Client Secret:', this.naver.clientSecret ? `${this.naver.clientSecret.slice(0, 10)}...` : 'None');
    console.groupEnd();
  }

  // 환경 변수 유효성 검사
  static validateAll(): boolean {
    const issues: string[] = [];

    if (!this.backendUrl) issues.push('VITE_BACKEND_URL');
    if (!this.kakao.apiKey) issues.push('VITE_KAKAO_API_KEY');
    if (!this.naver.clientId) issues.push('VITE_NAVER_CLIENT_ID');
    if (!this.naver.clientSecret) issues.push('VITE_NAVER_CLIENT_SECRET');

    if (issues.length > 0) {
      console.error('❌ 설정되지 않은 환경 변수들:', issues);
      console.error('📋 CloudFlare Pages Dashboard에서 다음 환경 변수들을 설정해주세요:');
      issues.forEach(issue => console.error(`   - ${issue}`));
      return false;
    }

    console.log('✅ 모든 환경 변수가 올바르게 설정되었습니다.');
    return true;
  }
} 