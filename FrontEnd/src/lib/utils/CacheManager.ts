/**
 * 캐시 매니저 - ngrok 요청 수 최적화를 위한 통합 캐싱 시스템
 */

interface CacheItem {
  data: any;
  timestamp: number;
  expiry: number;
}

interface CacheConfig {
  defaultTTL: number; // 기본 캐시 유지 시간 (분)
  maxSize: number;    // 최대 캐시 항목 수
}

class CacheManager {
  private cache: Map<string, CacheItem> = new Map();
  private config: CacheConfig;

  constructor(config: CacheConfig = { defaultTTL: 30, maxSize: 100 }) {
    this.config = config;
    this.cleanupExpiredItems();
  }

  /**
   * 캐시에서 데이터 가져오기
   */
  get(key: string): any | null {
    const item = this.cache.get(key);
    
    if (!item) {
      return null;
    }

    // 만료 확인
    if (Date.now() > item.expiry) {
      this.cache.delete(key);
      return null;
    }

    return item.data;
  }

  /**
   * 캐시에 데이터 저장
   */
  set(key: string, data: any, ttlMinutes?: number): void {
    const ttl = (ttlMinutes || this.config.defaultTTL) * 60 * 1000;
    const expiry = Date.now() + ttl;

    // 캐시 크기 제한
    if (this.cache.size >= this.config.maxSize) {
      this.evictOldest();
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      expiry
    });
  }

  /**
   * 특정 패턴의 캐시 무효화
   */
  invalidatePattern(pattern: string): void {
    const regex = new RegExp(pattern);
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * 전체 캐시 삭제
   */
  clear(): void {
    this.cache.clear();
  }

  /**
   * 가장 오래된 항목 제거
   */
  private evictOldest(): void {
    let oldestKey = '';
    let oldestTime = Date.now();

    for (const [key, item] of this.cache.entries()) {
      if (item.timestamp < oldestTime) {
        oldestTime = item.timestamp;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey);
    }
  }

  /**
   * 만료된 항목들 정리
   */
  private cleanupExpiredItems(): void {
    const now = Date.now();
    for (const [key, item] of this.cache.entries()) {
      if (now > item.expiry) {
        this.cache.delete(key);
      }
    }

    // 5분마다 정리
    setTimeout(() => this.cleanupExpiredItems(), 5 * 60 * 1000);
  }

  /**
   * 캐시 통계 정보
   */
  getStats(): { size: number; hitRate: number } {
    return {
      size: this.cache.size,
      hitRate: 0 // 필요시 히트율 추적 구현
    };
  }
}

// 각 데이터 타입별 캐시 인스턴스
export const stockDataCache = new CacheManager({ defaultTTL: 60, maxSize: 50 }); // 주가 데이터: 1시간
export const newsCache = new CacheManager({ defaultTTL: 30, maxSize: 100 });     // 뉴스 데이터: 30분
export const stockListCache = new CacheManager({ defaultTTL: 240, maxSize: 20 }); // 주식 목록: 4시간
export const analysisCache = new CacheManager({ defaultTTL: 120, maxSize: 30 });  // 분석 데이터: 2시간

/**
 * API 호출 래퍼 - 캐시 우선 조회
 */
export async function cachedApiCall<T>(
  cacheKey: string,
  apiCall: () => Promise<T>,
  cache: CacheManager,
  ttlMinutes?: number
): Promise<T> {
  // 캐시에서 먼저 확인
  const cachedData = cache.get(cacheKey);
  if (cachedData) {
    console.log(`🎯 Cache HIT: ${cacheKey}`);
    return cachedData;
  }

  // 캐시 미스 - API 호출
  console.log(`🌐 Cache MISS: ${cacheKey} - API 호출`);
  const data = await apiCall();
  
  // 성공적인 응답만 캐시
  if (data && (data as any).isSuccess !== false) {
    cache.set(cacheKey, data, ttlMinutes);
  }

  return data;
}

/**
 * 시간 기반 캐시 키 생성
 */
export function generateTimeBasedKey(baseKey: string, intervalMinutes: number = 30): string {
  const now = new Date();
  const interval = Math.floor(now.getTime() / (intervalMinutes * 60 * 1000));
  return `${baseKey}_${interval}`;
}

/**
 * 날짜 기반 캐시 키 생성
 */
export function generateDateBasedKey(baseKey: string): string {
  const today = new Date().toISOString().slice(0, 10);
  return `${baseKey}_${today}`;
} 