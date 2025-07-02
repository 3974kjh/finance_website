# Backend 설정 가이드

## 📋 **필수 설정: key.py 파일 생성**

### 1. key.py 파일 설정

본 프로젝트는 보안을 위해 API 키와 중요한 설정값들을 별도의 `key.py` 파일로 관리합니다.

#### Step 1: key.py 파일 생성
```bash
# BackEnd 폴더에서 실행
cp key.py.example key.py
```

#### Step 2: key.py 파일 수정
`key.py` 파일을 열어서 다음 값들을 실제 값으로 변경하세요:

```python
# =====================================
# 네이버 API 설정
# =====================================
NAVER_CLIENT_ID = "your_actual_naver_client_id"
NAVER_CLIENT_SECRET = "your_actual_naver_client_secret"

# =====================================
# 카카오 API 설정
# =====================================
KAKAO_REST_API_KEY = "your_actual_kakao_api_key"
KAKAO_REDIRECT_URI = "http://localhost:7150/oauth"  # 또는 실제 도메인

# =====================================
# 로그인 설정
# =====================================
LOGIN_USERNAME = "your_admin_username"
LOGIN_PASSWORD = "your_admin_password"
```

### 2. 환경 변수 우선순위

`key.py`는 다음 순서로 환경 변수를 확인합니다:

1. **직접 환경 변수** (최우선)
   - `NAVER_CLIENT_ID`, `KAKAO_REST_API_KEY` 등

2. **VITE_ 환경 변수** (Frontend와 공유)
   - `VITE_NAVER_CLIENT_ID`, `VITE_KAKAO_API_KEY` 등

3. **기존 호환 변수** (Fallback)
   - `PUBLIC_API_KEY` 등

4. **기본값** (개발용 또는 빈 값)

### 3. 보안 중요사항

⚠️ **중요**: `key.py` 파일은 절대 Git에 커밋하지 마세요!

- ✅ `key.py.example` - Git에 포함됨 (참고용)
- ❌ `key.py` - Git에서 제외됨 (실제 키 포함)

## 🚀 **서버 실행**

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 서버 시작
```bash
python main.py
```

### 3. 설정 확인
서버 시작 시 다음과 같은 로그가 출력됩니다:

```
==================================================
🚀 Backend 서버 설정 요약
==================================================
서버 주소: 0.0.0.0:8250
네이버 API: ✅ 설정됨
카카오 API: ✅ 설정됨
==================================================

🔧 Backend 환경 변수 상태 확인:
   - NAVER_CLIENT_ID: dqMtE_iRIg...
   - NAVER_CLIENT_SECRET: bg7d_nO_x...
   - KAKAO_REST_API_KEY: 3efc0a804d...
   - KAKAO_REDIRECT_URI: http://localhost:7150/oauth
   - 서버 설정: 0.0.0.0:8250
✅ 모든 필수 환경 변수가 설정되었습니다.
```

## ❌ **문제 해결**

### "ModuleNotFoundError: No module named 'key'" 오류
1. `key.py` 파일이 `BackEnd` 폴더에 있는지 확인
2. `key.py.example`을 복사해서 `key.py`로 이름 변경
3. 실제 API 키 값들로 수정

### "❌ 설정되지 않은 필수 환경 변수들" 오류
1. `key.py` 파일에서 해당 변수들이 올바르게 설정되었는지 확인
2. API 키가 'your_xxx_here' 형태의 플레이스홀더가 아닌 실제 값인지 확인
3. 환경 변수가 올바르게 설정되었는지 확인

### API 호출 실패
1. 네이버/카카오 개발자 콘솔에서 API 키가 활성화되어 있는지 확인
2. Redirect URI가 앱 설정과 일치하는지 확인
3. 도메인 화이트리스트 설정 확인

## 📚 **API 엔드포인트**

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8250/docs
- **ReDoc**: http://localhost:8250/redoc

## 🔧 **프로젝트 구조**

```
BackEnd/
├── main.py              # 메인 서버 파일
├── key.py               # API 키 설정 (Git 제외)
├── key.py.example       # 설정 예시 파일
├── README.md            # 이 파일
├── CalculateLogic.py    # 계산 로직
├── XmlDataBase.py       # XML 데이터베이스
├── JsonDataBase.py      # JSON 데이터베이스
├── WebCrawling.py       # 웹 크롤링
└── requirements.txt     # Python 의존성
```

## 📞 **지원**

설정 관련 문제가 있다면 다음을 확인해보세요:

1. `key.py` 파일이 올바르게 설정되었는지
2. 필요한 Python 패키지가 모두 설치되었는지
3. API 키들이 유효한지
4. 네트워크 연결 상태 