# CloudFlare Pages 정적 사이트 배포 가이드

## 🚀 **최종 배포 설정 (정적 사이트)**

### 1. CloudFlare Pages 기본 설정

```yaml
Framework preset: SvelteKit
Build command: npm run build
Build output directory: build
Root directory: FrontEnd
Node.js version: 18
```

### 2. 환경 변수 설정

CloudFlare Pages Dashboard > Settings > Environment Variables에서 다음 변수들을 설정하세요:

#### Production Environment Variables
```
# 카카오 API 설정
VITE_KAKAO_API_KEY=your_actual_kakao_api_key_here
VITE_KAKAO_REDIRECT_URI=https://your-cloudflare-pages-domain.pages.dev/oauth

# 네이버 API 설정  
VITE_NAVER_CLIENT_ID=your_naver_client_id_here
VITE_NAVER_CLIENT_SECRET=your_naver_client_secret_here

# 백엔드 서버 URL (실제 배포된 백엔드 또는 ngrok URL)
VITE_BACKEND_URL=https://your-backend-api-domain.com

# 환경 설정
VITE_NODE_ENV=production
```

#### Preview Environment Variables (선택사항)
```
# 카카오 API 설정
VITE_KAKAO_API_KEY=your_test_kakao_api_key_here
VITE_KAKAO_REDIRECT_URI=https://preview-branch.your-project.pages.dev/oauth

# 네이버 API 설정
VITE_NAVER_CLIENT_ID=your_test_naver_client_id_here
VITE_NAVER_CLIENT_SECRET=your_test_naver_client_secret_here

# 백엔드 서버 URL (테스트용)
VITE_BACKEND_URL=https://your-test-backend.ngrok-free.app

# 환경 설정
VITE_NODE_ENV=preview
```

### 2-1. 환경 변수 설정 가이드

#### CloudFlare Pages에서 환경 변수 추가 방법:
1. CloudFlare Dashboard 로그인
2. Pages → 프로젝트 선택
3. Settings → Environment variables
4. "Add variable" 클릭
5. Variable name과 Value 입력
6. Environment는 "Production" 선택
7. "Save" 클릭

#### 📝 **중요한 주의사항**:
- `VITE_` 접두사가 붙은 변수만 클라이언트에서 접근 가능
- 민감한 정보(API Secret 등)는 백엔드에서만 처리
- CloudFlare Pages 재배포 시 환경 변수가 적용됨

### 3. 프로젝트 구조 (정적 사이트)

```
finance_website/
├── FrontEnd/              # SvelteKit 프론트엔드 (정적 사이트)
│   ├── build/                # 빌드 출력 디렉토리 ✅
│   │   ├── _app/            # SvelteKit 앱 파일들
│   │   ├── index.html       # 메인 HTML 파일 ✅
│   │   ├── favicon.svg      # 파비콘
│   │   └── robots.txt       # SEO 파일
│   ├── src/
│   │   ├── routes/
│   │   │   ├── api_disabled/    # 서버 API 비활성화됨 ✅
│   │   │   └── ...
│   │   └── ...
│   ├── svelte.config.js     # Static adapter 설정 ✅
│   └── package.json
├── BackEnd/              # FastAPI 백엔드 (별도 서버)
└── .git/
```

### 4. 주요 변경사항

#### ✅ **완료된 작업들**
1. **Static Adapter**: CloudFlare adapter → Static adapter 변경
2. **빌드 디렉토리**: `.svelte-kit/output` → `build` 변경  
3. **index.html 생성**: 정적 HTML 파일 생성 완료
4. **API 라우트 비활성화**: 서버사이드 API 라우트 제거
5. **SPA Fallback**: Single Page Application 모드 설정

#### 🚫 **비활성화된 기능들**
- **서버사이드 API 라우트**: `/api/kakao`, `/api/naver` 비활성화
- **서버사이드 렌더링**: 클라이언트 사이드만 작동
- **CloudFlare Functions**: 정적 사이트이므로 서버 함수 없음

### 5. 배포 후 확인사항

#### ✅ **정상 작동할 기능들**
- 🌐 **프론트엔드 페이지들**: 모든 페이지 정상 작동
- 📊 **차트 및 시각화**: devextreme 차트 작동
- 🎨 **UI/UX**: Tailwind CSS 스타일링 적용
- 📱 **반응형 디자인**: 모바일/데스크톱 대응

#### ⚠️ **제한사항 (정적 사이트)**
- 🚫 **서버 API 호출**: 내부 API 라우트 비활성화
- 🚫 **서버사이드 데이터 처리**: 클라이언트에서만 처리
- 🚫 **실시간 백엔드 연동**: 별도 백엔드 서버 필요

### 6. 배포 과정

#### Step 1: CloudFlare Pages 연결
1. CloudFlare Dashboard → Pages
2. "Connect to Git" 선택
3. GitHub 저장소 연결

#### Step 2: 빌드 설정
```yaml
Framework preset: SvelteKit
Build command: npm run build
Build output directory: build
Root directory: FrontEnd
Node.js version: 18
```

#### Step 3: 환경 변수 설정
- Dashboard에서 환경 변수 추가
- Production 환경에 API 키들 설정

**⚠️ 중요**: 다음 환경 변수들을 반드시 설정해야 합니다:
- `VITE_KAKAO_API_KEY`: 카카오 API 키
- `VITE_KAKAO_REDIRECT_URI`: 카카오 Redirect URI  
- `VITE_NAVER_CLIENT_ID`: 네이버 Client ID
- `VITE_NAVER_CLIENT_SECRET`: 네이버 Client Secret
- `VITE_BACKEND_URL`: 백엔드 서버 URL
- `VITE_NODE_ENV`: 환경 구분 (production)

**📋 자세한 환경 변수 설정 방법은 `ENV_SETUP_GUIDE.md` 파일을 참고하세요.**

#### Step 4: 배포 실행
- "Save and Deploy" 클릭
- 빌드 로그 모니터링
- 배포 완료 확인

### 7. 트러블슈팅

#### 빌드 실패 시
```bash
# 로컬에서 빌드 테스트
npm run build

# 빌드 결과 확인
ls -la build/
```

#### 페이지 404 오류 시
- Build output directory가 `build`로 설정되었는지 확인
- index.html이 build 폴더에 생성되었는지 확인

#### API 호출 오류 시
- 정적 사이트에서는 서버 API 라우트 사용 불가
- 외부 API는 클라이언트에서 직접 호출 필요
- CORS 설정 확인 필요

### 8. 성능 최적화

#### 이미 적용된 최적화
- 📦 **코드 분할**: SvelteKit 자동 청킹
- 🗜️ **압축**: Vite 빌드 최적화
- 🚀 **CDN**: CloudFlare Pages 글로벌 CDN
- 📱 **반응형**: Tailwind CSS 최적화

#### 추가 최적화 권장사항
- 🖼️ **이미지 최적화**: WebP, AVIF 포맷 사용
- 📈 **Bundle 분석**: `npm run build` 결과 확인
- 🔍 **SEO**: robots.txt, sitemap.xml 추가

---

## 🎉 **배포 완료 체크리스트**

- [ ] CloudFlare Pages 프로젝트 생성
- [ ] 빌드 설정 (Framework: SvelteKit, Output: build)
- [ ] 환경 변수 설정 (API 키들)
- [ ] 첫 배포 실행 및 확인
- [ ] 도메인 설정 (선택사항)
- [ ] HTTPS 인증서 확인
- [ ] 성능 테스트 실행

---

**📝 참고**: 이 설정은 정적 사이트 배포용입니다. 서버사이드 기능이 필요하다면 CloudFlare Functions 또는 별도 백엔드 서버를 사용하세요. 