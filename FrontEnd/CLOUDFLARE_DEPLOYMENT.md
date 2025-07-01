# CloudFlare Pages 배포 가이드

## 🚀 배포 설정

### 1. CloudFlare Pages 기본 설정

```yaml
Framework preset: SvelteKit
Build command: npm run build
Build output directory: .svelte-kit/output
Root directory: FrontEnd
Node.js version: 18
```

### 2. 환경 변수 설정

CloudFlare Pages Dashboard > Settings > Environment Variables에서 다음 변수들을 설정하세요:

#### Production Environment Variables
```
VITE_KAKAO_API_KEY=your_kakao_api_key_here
VITE_NAVER_API_KEY=your_naver_api_key_here
VITE_BACKEND_URL=http://localhost:8250
VITE_NODE_ENV=production
```

#### 백엔드 연동 (필요시)
```
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
```

### 3. 프로젝트 구조

```
finance_website/
├── FrontEnd/              # SvelteKit 프론트엔드
│   ├── .svelte-kit/output/   # 빌드 출력 디렉토리
│   ├── src/
│   │   ├── routes/
│   │   │   └── api/          # CloudFlare Functions
│   │   └── lib/
│   ├── static/
│   ├── svelte.config.js      # CloudFlare adapter 설정
│   ├── wrangler.toml         # CloudFlare 설정
│   └── package.json
├── BackEnd/               # FastAPI 백엔드 (별도 배포)
└── README.md
```

### 4. 배포 과정

1. **GitHub Repository 연결**
   - CloudFlare Pages Dashboard에서 Git 연결
   - `finance_website` 레포지토리 선택

2. **빌드 설정**
   - Root directory: `FrontEnd`
   - Build command: `npm run build`
   - Build output directory: `.svelte-kit/output`

3. **환경 변수 설정**
   - 위의 환경 변수들을 CloudFlare Pages에서 설정

4. **배포 확인**
   - 빌드 로그 확인
   - API 라우트 동작 확인
   - 환경별 설정 검증

### 5. API 라우트 설정

현재 설정된 API 라우트들:
- `/api/kakao/*` - Kakao API 프록시
- `/api/naver/*` - Naver API 프록시

이들은 CloudFlare Pages Functions로 실행됩니다.

### 6. 트러블슈팅

#### 빌드 실패시
```bash
# 로컬에서 빌드 테스트
npm run build

# 의존성 재설치
npm install
```

#### API 라우트 오류시
- Environment Variables 확인
- CloudFlare Functions 로그 확인
- CORS 설정 검토

#### 정적 파일 404 오류시
- Build output directory 경로 확인
- `.svelte-kit/output` 디렉토리 존재 확인 