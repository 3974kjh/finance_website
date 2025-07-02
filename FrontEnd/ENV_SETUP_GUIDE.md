# 환경 변수 설정 가이드

## 📋 **CloudFlare Pages 환경 변수 설정**

### 1. CloudFlare Pages Dashboard 설정

1. **CloudFlare Dashboard** 접속 → **Pages** → **프로젝트 선택**
2. **Settings** → **Environment variables** 클릭
3. **Add variable** 버튼으로 아래 변수들 추가

### 2. 필수 환경 변수 목록

#### Production Environment Variables
```bash
# 카카오 API 설정
VITE_KAKAO_API_KEY=your_actual_kakao_api_key_here
VITE_KAKAO_REDIRECT_URI=https://your-domain.pages.dev/oauth

# 네이버 API 설정
VITE_NAVER_CLIENT_ID=your_naver_client_id_here
VITE_NAVER_CLIENT_SECRET=your_naver_client_secret_here

# 백엔드 서버 URL
VITE_BACKEND_URL=https://your-backend-api-domain.com

# 환경 구분
VITE_NODE_ENV=production
```

#### Preview/Development Environment Variables
```bash
# 카카오 API 설정 (테스트용)
VITE_KAKAO_API_KEY=your_test_kakao_api_key_here
VITE_KAKAO_REDIRECT_URI=https://preview.your-domain.pages.dev/oauth

# 네이버 API 설정 (테스트용)
VITE_NAVER_CLIENT_ID=your_test_naver_client_id_here
VITE_NAVER_CLIENT_SECRET=your_test_naver_client_secret_here

# 백엔드 서버 URL (개발용 - ngrok 등)
VITE_BACKEND_URL=https://your-ngrok-url.ngrok-free.app

# 환경 구분
VITE_NODE_ENV=development
```

## 🏠 **로컬 개발 환경 설정**

### 1. .env 파일 생성 (FrontEnd 폴더에)

```bash
# FrontEnd/.env 파일 생성 후 아래 내용 추가

# 카카오 API 설정
VITE_KAKAO_API_KEY=3efc0a804d4103ba9fd00387adc2f8ca
VITE_KAKAO_REDIRECT_URI=http://localhost:7150/oauth

# 네이버 API 설정
VITE_NAVER_CLIENT_ID=your_naver_client_id_here
VITE_NAVER_CLIENT_SECRET=your_naver_client_secret_here

# 백엔드 서버 URL (로컬 개발용)
VITE_BACKEND_URL=http://localhost:8250

# 환경 구분
VITE_NODE_ENV=development
```

### 2. Backend 환경 변수 (선택사항)

Backend는 Frontend의 VITE_ 변수들을 자동으로 읽어오므로 별도 설정이 불필요하지만, 필요시 직접 설정 가능:

```bash
# BackEnd/.env 파일 생성 후 아래 내용 추가

# 카카오 API 설정
KAKAO_REST_API_KEY=3efc0a804d4103ba9fd00387adc2f8ca
KAKAO_REDIRECT_URI=http://localhost:7150/oauth

# 네이버 API 설정
NAVER_CLIENT_ID=your_naver_client_id_here
NAVER_CLIENT_SECRET=your_naver_client_secret_here
```

## 🔧 **환경 변수 우선순위**

### Frontend (SvelteKit)
1. `VITE_KAKAO_API_KEY` (최우선)
2. `PUBLIC_API_KEY` (기존 호환)
3. 하드코딩된 기본값 (없음)

### Backend (FastAPI)
1. `KAKAO_REST_API_KEY` (최우선)
2. `VITE_KAKAO_API_KEY` (Frontend와 공유)
3. `PUBLIC_API_KEY` (기존 호환)
4. 하드코딩된 기본값 (없음)

## ✅ **설정 확인 방법**

### 1. Frontend 확인
브라우저 개발자 도구 콘솔에서 다음 로그 확인:
```
🔧 환경 변수 상태 확인 (CloudFlare Pages)
환경: Development/Production
백엔드 URL: https://your-backend-url
카카오 API 키: 3efc0a804d...
카카오 Redirect URI: https://your-domain/oauth
```

### 2. Backend 확인
Backend 서버 시작 시 콘솔에서 다음 로그 확인:
```
🔧 Backend 환경 변수 상태 확인:
   - NAVER_CLIENT_ID: dqMtE_iRIg...
   - KAKAO_REST_API_KEY: 3efc0a804d...
   - KAKAO_REDIRECT_URI: https://your-domain/oauth
✅ 모든 필수 환경 변수가 설정되었습니다.
```

## ❌ **문제 해결**

### "환경 변수가 올바르게 설정되지 않았습니다" 오류
1. CloudFlare Pages Dashboard에서 환경 변수 확인
2. 변수명이 정확한지 확인 (`VITE_` 접두사 포함)
3. CloudFlare Pages 재배포 실행
4. 브라우저 캐시 클리어

### "백엔드 서버에 연결할 수 없습니다" 오류
1. `VITE_BACKEND_URL` 환경 변수 확인
2. Backend 서버가 실행 중인지 확인
3. CORS 설정 확인
4. 네트워크 방화벽 설정 확인

### 카카오/네이버 API 오류
1. API 키가 올바른지 확인
2. Redirect URI가 앱 설정과 일치하는지 확인
3. API 사용량 한도 확인
4. 도메인 화이트리스트 설정 확인

## 📚 **참고 링크**

- [CloudFlare Pages 환경 변수 문서](https://developers.cloudflare.com/pages/configuration/build-configuration/)
- [SvelteKit 환경 변수 문서](https://kit.svelte.dev/docs/modules#$env-static-public)
- [Vite 환경 변수 문서](https://vitejs.dev/guide/env-and-mode.html) 