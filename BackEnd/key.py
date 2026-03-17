# API 키 및 설정값 정의
# 이 파일은 민감한 정보를 포함하므로 .gitignore에 추가되어 Git에서 제외됩니다.

import os

# =====================================
# 네이버 API 설정
# =====================================
NAVER_CLIENT_ID = "dqMtE_iRIgA_8e9aB_dV"
NAVER_CLIENT_SECRET = "bg7d_nO_xJ"
NAVER_API_BASE_URL = "https://openapi.naver.com/v1/search"

# =====================================
# 카카오 API 설정
# =====================================
KAKAO_REST_API_KEY = "3efc0a804d4103ba9fd00387adc2f8ca"
KAKAO_REDIRECT_URI = "http://finance-website-687.pages.dev/oauth"
KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_API_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

# =====================================
# 공공데이터 포털 API 설정 (한국천문연구원 특일정보)
# =====================================
# 일반 decoding 인증키 (실제 API 호출에 사용)
KOREA_DATA_PORTAL_API_KEY = os.getenv("KOREA_DATA_PORTAL_API_KEY", "QPLZ7DP0Bbo5veUeCiha8XBtOpkcV/z/GL9cotW0mqXiCh1F6Tz7V50UlpKfs7BObepcf6i2iYzGuoTws3ynyw==")
# 일반 encoding 인증키 (참고용)
KOREA_DATA_PORTAL_API_KEY_ENCODED = "QPLZ7DP0Bbo5veUeCiha8XBtOpkcV%2Fz%2FGL9cotW0mqXiCh1F6Tz7V50UlpKfs7BObepcf6i2iYzGuoTws3ynyw%3D%3D"
# API 기본 URL
KOREA_DATA_PORTAL_BASE_URL = "http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService"
KOREA_DATA_PORTAL_HOLIDAY_URL = "http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo"

# =====================================
# 로그인 설정
# =====================================
LOGIN_USERNAME = "jukim"
LOGIN_PASSWORD = "jukim123$"

# =====================================
# 서버 설정
# =====================================
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8250

# =====================================
# 환경 변수 상태 확인 함수
# =====================================
def check_environment_variables():
    """환경 변수 및 설정값 상태를 확인하는 함수"""
    print("🔧 Backend 환경 변수 상태 확인:")
    print(f"   - NAVER_CLIENT_ID: {NAVER_CLIENT_ID[:10]}..." if NAVER_CLIENT_ID else "   - NAVER_CLIENT_ID: None")
    print(f"   - NAVER_CLIENT_SECRET: {NAVER_CLIENT_SECRET[:10]}..." if NAVER_CLIENT_SECRET else "   - NAVER_CLIENT_SECRET: None")
    print(f"   - KAKAO_REST_API_KEY: {KAKAO_REST_API_KEY[:10]}..." if KAKAO_REST_API_KEY else "   - KAKAO_REST_API_KEY: None")
    print(f"   - KAKAO_REDIRECT_URI: {KAKAO_REDIRECT_URI}")
    print(f"   - KOREA_DATA_PORTAL_API_KEY: {KOREA_DATA_PORTAL_API_KEY[:10]}..." if KOREA_DATA_PORTAL_API_KEY else "   - KOREA_DATA_PORTAL_API_KEY: None")
    print(f"   - 서버 설정: {SERVER_HOST}:{SERVER_PORT}")
    
    # 필수 환경 변수 체크
    missing_vars = []
    if not KAKAO_REST_API_KEY:
        missing_vars.append('KAKAO_REST_API_KEY (또는 VITE_KAKAO_API_KEY)')
    if not KAKAO_REDIRECT_URI:
        missing_vars.append('KAKAO_REDIRECT_URI (또는 VITE_KAKAO_REDIRECT_URI)')
    if not KOREA_DATA_PORTAL_API_KEY:
        missing_vars.append('KOREA_DATA_PORTAL_API_KEY')
    
    if missing_vars:
        print("❌ 설정되지 않은 필수 환경 변수들:")
        for var in missing_vars:
            print(f"   - {var}")
        print("📋 환경 변수를 설정해주세요.")
    else:
        print("✅ 모든 필수 환경 변수가 설정되었습니다.")

# =====================================
# API 키 유효성 검사
# =====================================
def validate_api_keys():
    """API 키들의 유효성을 검사하는 함수"""
    issues = []
    
    if not NAVER_CLIENT_ID or NAVER_CLIENT_ID == 'your_naver_client_id_here':
        issues.append('NAVER_CLIENT_ID')
    
    if not NAVER_CLIENT_SECRET or NAVER_CLIENT_SECRET == 'your_naver_client_secret_here':
        issues.append('NAVER_CLIENT_SECRET')
    
    if not KAKAO_REST_API_KEY:
        issues.append('KAKAO_REST_API_KEY')
    
    if not KAKAO_REDIRECT_URI:
        issues.append('KAKAO_REDIRECT_URI')
    
    if not KOREA_DATA_PORTAL_API_KEY:
        issues.append('KOREA_DATA_PORTAL_API_KEY')
    
    return issues

# =====================================
# 설정 요약 출력
# =====================================
def print_config_summary():
    """현재 설정 요약을 출력하는 함수"""
    print("="*50)
    print("🚀 Backend 서버 설정 요약")
    print("="*50)
    print(f"서버 주소: {SERVER_HOST}:{SERVER_PORT}")
    print(f"네이버 API: {'✅ 설정됨' if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET else '❌ 미설정'}")
    print(f"카카오 API: {'✅ 설정됨' if KAKAO_REST_API_KEY and KAKAO_REDIRECT_URI else '❌ 미설정'}")
    print(f"공공데이터 포털 API: {'✅ 설정됨' if KOREA_DATA_PORTAL_API_KEY else '❌ 미설정'}")
    print("="*50)
