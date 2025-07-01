/**
 * 요청 제한 및 디바운싱 유틸리티 - ngrok 제한 최적화
 */

interface RequestLimiterConfig {
  maxRequestsPerMinute: number;
  debounceDelay: number;
}

class RequestLimiter {
  private requestTimes: number[] = [];
  private debounceTimers: Map<string, NodeJS.Timeout> = new Map();
  private config: RequestLimiterConfig;

  constructor(config: RequestLimiterConfig = { maxRequestsPerMinute: 40, debounceDelay: 300 }) {
    this.config = config;
  }

  /**
   * 요청 가능 여부 확인
   */
  canMakeRequest(): boolean {
    const now = Date.now();
    const oneMinuteAgo = now - 60000; // 1분 전

    // 1분 이내의 요청만 필터링
    this.requestTimes = this.requestTimes.filter(time => time > oneMinuteAgo);

    // 최대 요청 수 확인
    if (this.requestTimes.length >= this.config.maxRequestsPerMinute) {
      console.warn(`🚫 Request limit reached: ${this.requestTimes.length}/${this.config.maxRequestsPerMinute} per minute`);
      return false;
    }

    return true;
  }

  /**
   * 요청 기록
   */
  recordRequest(): void {
    this.requestTimes.push(Date.now());
  }

  /**
   * 제한된 API 호출
   */
  async limitedApiCall<T>(apiCall: () => Promise<T>): Promise<T | null> {
    if (!this.canMakeRequest()) {
      // 대기 시간 계산
      const oldestRequest = this.requestTimes[0];
      const waitTime = oldestRequest + 60000 - Date.now();
      
      console.log(`⏳ Waiting ${Math.ceil(waitTime / 1000)}s before next request`);
      
      // 잠시 대기 후 재시도
      await new Promise(resolve => setTimeout(resolve, Math.max(waitTime, 1000)));
      
      return this.limitedApiCall(apiCall);
    }

    this.recordRequest();
    
    try {
      const result = await apiCall();
      console.log(`✅ API call completed. Requests this minute: ${this.requestTimes.length}`);
      return result;
    } catch (error) {
      console.error('❌ API call failed:', error);
      throw error;
    }
  }

  /**
   * 디바운스된 함수 실행
   */
  debounce<T extends (...args: any[]) => any>(
    key: string,
    func: T,
    ...args: Parameters<T>
  ): Promise<ReturnType<T>> {
    return new Promise((resolve, reject) => {
      // 기존 타이머 정리
      const existingTimer = this.debounceTimers.get(key);
      if (existingTimer) {
        clearTimeout(existingTimer);
      }

      // 새 타이머 설정
      const timer = setTimeout(async () => {
        try {
          const result = await func(...args);
          resolve(result);
        } catch (error) {
          reject(error);
        } finally {
          this.debounceTimers.delete(key);
        }
      }, this.config.debounceDelay);

      this.debounceTimers.set(key, timer);
    });
  }

  /**
   * 특정 키의 디바운스 취소
   */
  cancelDebounce(key: string): void {
    const timer = this.debounceTimers.get(key);
    if (timer) {
      clearTimeout(timer);
      this.debounceTimers.delete(key);
    }
  }

  /**
   * 모든 디바운스 취소
   */
  cancelAllDebounce(): void {
    this.debounceTimers.forEach(timer => clearTimeout(timer));
    this.debounceTimers.clear();
  }

  /**
   * 통계 정보 반환
   */
  getStats(): { requestsThisMinute: number; maxRequests: number; remainingRequests: number } {
    const now = Date.now();
    const oneMinuteAgo = now - 60000;
    const requestsThisMinute = this.requestTimes.filter(time => time > oneMinuteAgo).length;
    
    return {
      requestsThisMinute,
      maxRequests: this.config.maxRequestsPerMinute,
      remainingRequests: Math.max(0, this.config.maxRequestsPerMinute - requestsThisMinute)
    };
  }

  /**
   * 설정 업데이트
   */
  updateConfig(newConfig: Partial<RequestLimiterConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }
}

// 싱글톤 인스턴스
export const requestLimiter = new RequestLimiter();

/**
 * 제한된 API 호출 헬퍼
 */
export async function limitedApiCall<T>(apiCall: () => Promise<T>): Promise<T | null> {
  return requestLimiter.limitedApiCall(apiCall);
}

/**
 * 디바운스된 검색 헬퍼
 */
export async function debouncedSearch<T>(
  searchKey: string,
  searchFunction: () => Promise<T>,
  delay: number = 300
): Promise<T> {
  // 커스텀 디바운스 딜레이 적용
  const originalDelay = requestLimiter['config'].debounceDelay;
  requestLimiter.updateConfig({ debounceDelay: delay });
  
  try {
    const result = await requestLimiter.debounce(searchKey, searchFunction);
    return result;
  } finally {
    // 원래 딜레이로 복원
    requestLimiter.updateConfig({ debounceDelay: originalDelay });
  }
}

/**
 * 요청 통계 표시 (개발용)
 */
export function logRequestStats(): void {
  const stats = requestLimiter.getStats();
  console.log(`📊 Request Stats: ${stats.requestsThisMinute}/${stats.maxRequests} used, ${stats.remainingRequests} remaining`);
} 