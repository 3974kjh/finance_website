# 🔍 스마트 금융 분석 플랫폼

> **혁신적인 주식 분석과 투자 전략을 위한 올인원 솔루션**

## 📋 프로젝트 소개

스마트 금융 분석 플랫폼은 **SvelteKit**과 **FastAPI**를 기반으로 구축된 현대적인 웹 애플리케이션입니다. 
실시간 주식 데이터 분석, 기술적 분석, 투자 전략 수립을 위한 포괄적인 도구를 제공합니다.

## ✨ 주요 기능

### 📈 실시간 주식 데이터 분석
- **실시간 주가 데이터**: S&P500, KOSPI, NASDAQ 등 전 세계 주요 지수 데이터
- **다양한 기간 설정**: 일간, 주간, 월간 데이터 조회 및 분석
- **인터랙티브 차트**: 멀티 차트와 단일 차트 모드 지원

### 🎯 고급 기술적 분석
- **지지선/저항선 자동 탐지**: AI 기반 알고리즘으로 주요 가격 레벨 식별
- **가격 예측 모델**: 과거 데이터 기반 미래 가격 예측
- **고점/저점 분석**: 매매 타이밍 최적화를 위한 패턴 분석
- **추세 변화율 계산**: 정확한 변화 추세 예측

### 💼 투자 포트폴리오 관리
- **투자 내역 추적**: 매수/매도 기록 자동 저장
- **수익률 계산**: 실시간 포트폴리오 성과 분석
- **투자 전략 백테스팅**: 과거 데이터를 활용한 전략 검증

### 📊 데이터 시각화
- **실시간 차트**: 캔들스틱, 라인 차트 등 다양한 시각화
- **반응형 대시보드**: 모든 기기에 최적화된 UI/UX
- **커스터마이징**: 개인 맞춤형 차트 설정

### 🔍 웹 검색 및 뉴스 분석
- **실시간 금융 뉴스**: 관련 뉴스 자동 수집 및 분석
- **키워드 분석**: 시장 감정 분석을 통한 투자 신호 생성

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │    Database     │
│   (SvelteKit)   │◄───┤   (FastAPI)     │◄───┤   (XML/JSON)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────┤ FinanceDataReader├──────────────┘
                        │   (Data Source) │
                        └─────────────────┘
```

### 🎨 Frontend (SvelteKit)
- **현대적 UI/UX**: TailwindCSS 기반 반응형 디자인
- **고성능**: Vite 빌드 시스템으로 빠른 개발 및 배포
- **타입 안전성**: TypeScript로 개발된 안정적인 코드
- **컴포넌트 기반**: 재사용 가능한 모듈식 아키텍처

### ⚡ Backend (FastAPI)
- **고성능 API**: 비동기 처리로 빠른 응답 속도
- **자동 문서화**: Swagger/OpenAPI 자동 생성
- **데이터 검증**: Pydantic 기반 강력한 데이터 검증
- **CORS 지원**: 크로스 오리진 요청 완벽 지원

### 🗄️ 데이터 저장소
- **XML Database**: 구조화된 투자 데이터 저장
- **JSON Storage**: 분석 결과 및 설정 저장
- **실시간 캐싱**: 빠른 데이터 접근을 위한 메모리 캐시

## 🚀 기술 스택

### Frontend
- **Framework**: SvelteKit 4.x
- **Language**: TypeScript
- **Styling**: TailwindCSS + PostCSS
- **Build Tool**: Vite
- **Package Manager**: PNPM

### Backend  
- **Framework**: FastAPI
- **Language**: Python 3.8+
- **Data Analysis**: pandas, FinanceDataReader
- **Data Storage**: XML, JSON
- **HTTP Client**: axios

### Development Tools
- **Linting**: ESLint + Prettier
- **Type Checking**: TypeScript, svelte-check
- **Version Control**: Git

## 📦 설치 및 실행

### 📋 시스템 요구사항
- **Node.js**: 18.x 이상
- **Python**: 3.8 이상
- **PNPM**: 8.x 이상 (권장)

### 🔧 Backend 설정

```bash
# 백엔드 디렉토리로 이동
cd BackEnd

# Python 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate

# 의존성 설치
pip install fastapi uvicorn pandas FinanceDataReader python-multipart

# 서버 실행
uvicorn main:app --reload --port 8000
```

### 🎨 Frontend 설정

```bash
# 프론트엔드 디렉토리로 이동
cd FrontEnd

# 의존성 설치
pnpm install

# 개발 서버 실행
pnpm run dev
```

### 🌐 접속 정보
- **Frontend**: http://localhost:7150
- **Backend API**: http://localhost:8000

## 💡 주요 이점

### 📊 **투자 수익성 향상**
- 정확한 기술적 분석으로 매매 타이밍 최적화
- 데이터 기반 의사결정으로 감정적 투자 방지
- 백테스팅을 통한 전략 검증

### ⏱️ **시간 효율성**
- 자동화된 데이터 수집 및 분석
- 실시간 알림으로 기회 놓치지 않음
- 원클릭 포트폴리오 관리

### 🎯 **정확한 예측**
- AI 기반 가격 예측 모델
- 다양한 기술적 지표 조합 분석
- 시장 트렌드 패턴 인식

### 🔐 **안전한 데이터 관리**
- 로컬 데이터 저장으로 개인정보 보호
- 백업 및 복구 기능
- 투명한 데이터 처리 과정

## 📱 사용 가이드

### 1️⃣ **주식 데이터 조회**
```bash
POST /stock_data/
{
  "symbol": "AAPL",
  "duration": 3,
  "isMonth": true
}
```

### 2️⃣ **기술적 분석 실행**
```bash
POST /expect_stock/
{
  "symbol": "AAPL",
  "term": 52
}
```

### 3️⃣ **투자 내역 저장**
```bash
POST /save_buy_history/
{
  "data": {
    "symbol": "AAPL",
    "price": 150.00,
    "quantity": 10
  }
}
```

## 🤝 기여하기

프로젝트 개선에 참여해주세요!

1. **Fork** 프로젝트
2. **Feature Branch** 생성 (`git checkout -b feature/AmazingFeature`)
3. **Commit** 변경사항 (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to Branch (`git push origin feature/AmazingFeature`)
5. **Pull Request** 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의 및 지원

- **이메일**: 42.4.jukim@gmail.com

---

<div align="center">

**⭐ 이 프로젝트가 도움이 되었다면 스타를 눌러주세요! ⭐**

Made with ❤️ by Jukim

</div> 
