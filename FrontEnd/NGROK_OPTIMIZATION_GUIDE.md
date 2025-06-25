# ngrok 무료 플랜 최적화 가이드 🚀

## 📊 현재 상황
- **ngrok 무료 플랜 제한**: 월 20,000 HTTP 요청
- **기존 문제**: API 호출이 너무 빈번하여 제한에 빠르게 도달
- **목표**: 요청 수를 **70% 이상 감소**시켜 안정적인 서비스 운영

## 🛠️ 구현된 최적화 방안

### 1. **통합 캐시 시스템** ⭐⭐⭐
**파일**: `FrontEnd/src/lib/utils/CacheManager.ts`

```typescript
// 주요 기능
- 시간 기반 캐시 (TTL 설정)
- 날짜 기반 캐시 (일별 데이터)
- 자동 만료 및 정리
- 메모리 최적화

// 캐시 전략
- 주식 데이터: 30분 캐시
- 뉴스 데이터: 15분 캐시
- 주식 목록: 1시간 캐시
- 분석 결과: 1시간 캐시
```

**예상 효과**: API 호출 **50-60% 감소**

### 2. **배치 API 처리** ⭐⭐
**파일**: `FrontEnd/src/lib/utils/BatchApiManager.ts`

```typescript
// 배치 처리 전략
- 동시 요청 수 제한 (최대 3-5개)
- 중복 요청 자동 제거
- 요청 간 딜레이 추가 (300-500ms)
- 그룹화된 API 호출
```

**적용 영역**:
- 뉴스 페이지: 실시간 검색어별 뉴스 (3개씩 배치)
- 멀티차트: 8개 지수 데이터 (4개씩 배치)
- 분석 페이지: 주식 목록 데이터

**예상 효과**: API 호출 **30-40% 감소**

### 3. **요청 제한 및 디바운싱** ⭐⭐
**파일**: `FrontEnd/src/lib/utils/RequestLimiter.ts`

```typescript
// 제한 설정
- 분당 최대 40회 요청
- 검색 입력 디바운싱 (300ms)
- 자동 대기 및 재시도
- 실시간 요청 통계
```

**예상 효과**: 불필요한 요청 **20-30% 감소**

### 4. **페이지별 최적화**

#### 🔸 뉴스 페이지 (`news/+page.svelte`)
```typescript
// 최적화 내용
- 배치 처리로 3개씩 동시 요청
- 이미 로드된 뉴스 재사용
- 중복 요청 방지
- 배치 간 500ms 딜레이
```

#### 🔸 멀티차트 (`MultiChartBasic.svelte`)
```typescript
// 최적화 내용
- 4개씩 배치 처리
- 주가+뉴스 데이터 병렬 로딩
- 스마트 캐시 정리
- 배치 간 300ms 딜레이
```

#### 🔸 Finance API (`FinanceApi.ts`)
```typescript
// 최적화 내용
- 모든 주식 데이터 API에 캐시 적용
- 심볼+기간 조합으로 캐시 키 생성
- 30분 TTL 설정
```

#### 🔸 Naver API (`NaverApi.ts`)
```typescript
// 최적화 내용
- 뉴스 검색 결과 15분 캐시
- 기타 콘텐츠 30분 캐시
- 쿼리+정렬 조합 캐시 키
```

## 📈 예상 성능 개선

### Before (최적화 전)
```
뉴스 페이지: 20개 검색어 × 1회 = 20 요청
멀티차트: 8개 지수 × 2회(주가+뉴스) = 16 요청
분석 페이지: 100개 주식 × 1회 = 100 요청
총 일일 예상: ~1,000-2,000 요청
```

### After (최적화 후)
```
뉴스 페이지: 캐시 적용 + 배치 처리 = ~6-8 요청
멀티차트: 캐시 적용 + 배치 처리 = ~4-6 요청  
분석 페이지: 캐시 적용 = ~20-30 요청
총 일일 예상: ~300-500 요청 (70% 감소)
```

## 🎯 사용법

### 1. 캐시 사용
```typescript
import { cachedApiCall, generateTimeBasedKey } from '../utils/CacheManager';

// 30분 캐시 적용
const cacheKey = generateTimeBasedKey('my_api_call', 30);
const result = await cachedApiCall(cacheKey, () => myApiCall(), stockDataCache, 30);
```

### 2. 배치 처리
```typescript
import { batchStockDataCall } from '../utils/BatchApiManager';

// 배치로 주식 데이터 호출
const result = await batchStockDataCall(symbol, duration, isMonth, () => apiCall());
```

### 3. 요청 제한
```typescript
import { limitedApiCall, debouncedSearch } from '../utils/RequestLimiter';

// 제한된 API 호출
const result = await limitedApiCall(() => myApiCall());

// 디바운스된 검색
const searchResult = await debouncedSearch('search_key', () => searchApi(), 500);
```

## 🔧 모니터링

### 개발자 콘솔에서 확인 가능한 로그
```
🎯 Using cached data for: [키]
🚀 Processing batch: [배치키] with [개수] requests  
✅ API call completed. Requests this minute: [개수]
💾 Chart data cached for: [날짜]
📊 Request Stats: [사용량]/[제한] used, [남은량] remaining
```

### 실시간 통계 확인
```typescript
import { logRequestStats } from '../utils/RequestLimiter';

// 콘솔에서 실행
logRequestStats();
```

## 🚨 주의사항

1. **캐시 무효화**: 중요한 데이터 변경 시 수동으로 캐시 클리어 필요
2. **메모리 사용량**: 캐시 데이터가 많아질 수 있으므로 주기적 정리 필요
3. **네트워크 오류**: 캐시 실패 시 원본 API 호출로 폴백
4. **개발 환경**: 개발 시에는 캐시를 비활성화하거나 짧은 TTL 사용 권장

## 📝 추가 최적화 아이디어

### 단기 개선 (1-2주)
- [ ] 이미지 캐싱 (차트 이미지 등)
- [ ] 페이지네이션 최적화
- [ ] 불필요한 API 호출 제거

### 중기 개선 (1-2개월)  
- [ ] Service Worker 캐싱
- [ ] IndexedDB 대용량 캐시
- [ ] 백그라운드 데이터 프리로딩

### 장기 개선 (3개월+)
- [ ] 서버 사이드 캐싱
- [ ] CDN 활용
- [ ] GraphQL 도입 (배치 쿼리)

## 🎉 결론

이 최적화를 통해 ngrok 무료 플랜으로도 안정적인 서비스 운영이 가능해졌습니다.
예상 효과: **월 20,000 요청 → 6,000-8,000 요청** (60-70% 감소) 