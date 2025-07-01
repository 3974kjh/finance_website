/**
 * 배치 API 매니저 - 여러 API 호출을 묶어서 처리하여 요청 수 최적화
 */

interface BatchRequest {
  id: string;
  apiCall: () => Promise<any>;
  resolve: (value: any) => void;
  reject: (error: any) => void;
}

interface RequestQueue {
  [key: string]: BatchRequest[];
}

class BatchApiManager {
  private requestQueue: RequestQueue = {};
  private batchDelay: number = 100; // 100ms 후 배치 실행
  private maxBatchSize: number = 5;  // 최대 5개씩 배치 처리
  private pendingBatches: Set<string> = new Set();

  /**
   * API 호출을 배치에 추가
   */
  async addToBatch<T>(
    batchKey: string,
    requestId: string,
    apiCall: () => Promise<T>
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      // 큐 초기화
      if (!this.requestQueue[batchKey]) {
        this.requestQueue[batchKey] = [];
      }

      // 중복 요청 확인
      const existingRequest = this.requestQueue[batchKey].find(req => req.id === requestId);
      if (existingRequest) {
        console.log(`🔄 Duplicate request detected: ${requestId}`);
        return existingRequest.resolve; // 기존 요청의 결과를 반환
      }

      // 새 요청 추가
      this.requestQueue[batchKey].push({
        id: requestId,
        apiCall,
        resolve,
        reject
      });

      // 배치 처리 스케줄링
      this.scheduleBatch(batchKey);
    });
  }

  /**
   * 배치 처리 스케줄링
   */
  private scheduleBatch(batchKey: string): void {
    if (this.pendingBatches.has(batchKey)) {
      return; // 이미 스케줄된 배치
    }

    this.pendingBatches.add(batchKey);

    setTimeout(() => {
      this.processBatch(batchKey);
    }, this.batchDelay);
  }

  /**
   * 배치 처리 실행
   */
  private async processBatch(batchKey: string): Promise<void> {
    const requests = this.requestQueue[batchKey] || [];
    if (requests.length === 0) {
      this.pendingBatches.delete(batchKey);
      return;
    }

    console.log(`🚀 Processing batch: ${batchKey} with ${requests.length} requests`);

    // 배치 크기에 따라 분할 처리
    const batches = this.chunkArray(requests, this.maxBatchSize);
    
    for (const batch of batches) {
      await this.executeBatch(batch);
    }

    // 큐 정리
    delete this.requestQueue[batchKey];
    this.pendingBatches.delete(batchKey);
  }

  /**
   * 실제 배치 실행
   */
  private async executeBatch(batch: BatchRequest[]): Promise<void> {
    const promises = batch.map(async (request) => {
      try {
        const result = await request.apiCall();
        request.resolve(result);
        return { success: true, id: request.id };
      } catch (error) {
        request.reject(error);
        return { success: false, id: request.id, error };
      }
    });

    await Promise.allSettled(promises);
  }

  /**
   * 배열을 청크로 분할
   */
  private chunkArray<T>(array: T[], chunkSize: number): T[][] {
    const chunks: T[][] = [];
    for (let i = 0; i < array.length; i += chunkSize) {
      chunks.push(array.slice(i, i + chunkSize));
    }
    return chunks;
  }

  /**
   * 특정 배치 큐 정리
   */
  clearBatch(batchKey: string): void {
    delete this.requestQueue[batchKey];
    this.pendingBatches.delete(batchKey);
  }

  /**
   * 모든 배치 큐 정리
   */
  clearAll(): void {
    this.requestQueue = {};
    this.pendingBatches.clear();
  }
}

// 싱글톤 인스턴스
export const batchApiManager = new BatchApiManager();

/**
 * 배치 API 호출 헬퍼
 */
export async function batchApiCall<T>(
  batchKey: string,
  requestId: string,
  apiCall: () => Promise<T>
): Promise<T> {
  return batchApiManager.addToBatch(batchKey, requestId, apiCall);
}

/**
 * 주식 데이터 배치 호출
 */
export async function batchStockDataCall(
  symbol: string,
  duration: number,
  isMonth: boolean,
  apiCall: () => Promise<any>
): Promise<any> {
  const batchKey = `stock_data_${duration}_${isMonth}`;
  const requestId = `${symbol}_${duration}_${isMonth}`;
  
  return batchApiCall(batchKey, requestId, apiCall);
}

/**
 * 뉴스 데이터 배치 호출
 */
export async function batchNewsCall(
  query: string,
  serviceId: string,
  apiCall: () => Promise<any>
): Promise<any> {
  const batchKey = `news_${serviceId}`;
  const requestId = `${query}_${serviceId}`;
  
  return batchApiCall(batchKey, requestId, apiCall);
} 