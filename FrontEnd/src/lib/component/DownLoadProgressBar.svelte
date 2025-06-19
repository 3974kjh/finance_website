<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  
  export let min: number = 0;
  export let max: number = 100;
  export let nowCount: number;

  let progressBarElement: HTMLDivElement;
  let progressTrackElement: HTMLDivElement;
  let containerWidth: number = 0;
  let actualFillWidth: number = 0;
  let resizeObserver: ResizeObserver | null = null;

  // 퍼센트 계산 개선 - 정확한 계산과 범위 제한
  $: {
    const range = max - min;
    const current = Math.max(min, Math.min(max, nowCount));
    percentage = range > 0 ? Math.round(((current - min) / range) * 100) : 0;
    // 0-100 범위로 제한
    percentage = Math.max(0, Math.min(100, percentage));
  }
  
  // 실제 컨테이너 너비 기반으로 정확한 채움 너비 계산
  $: {
    if (containerWidth > 0) {
      if (percentage >= 100) {
        // 100%일 때는 정확히 전체 너비 사용
        actualFillWidth = containerWidth;
      } else {
        // 일반적인 경우 정확한 비율 계산
        actualFillWidth = Math.round((containerWidth * percentage) / 100);
      }
    }
  }
  
  $: progressWidth = containerWidth > 0 ? `${actualFillWidth}px` : `${percentage}%`;
  
  let percentage: number = 0;

  // 컨테이너 크기 측정 및 관찰
  const setupResizeObserver = () => {
    // progress-track 요소를 기준으로 측정 (실제 채움 영역)
    const targetElement = progressTrackElement || progressBarElement;
    
    if (targetElement && !resizeObserver) {
      resizeObserver = new ResizeObserver((entries) => {
        for (let entry of entries) {
          // contentRect는 border와 padding을 제외한 실제 콘텐츠 영역
          containerWidth = entry.contentRect.width;
        }
      });
      
      resizeObserver.observe(targetElement);
      
      // 초기 너비 설정 - clientWidth 사용 (border 제외, padding 포함)
      containerWidth = targetElement.clientWidth;
    }
  };

  // 프로그래스 바 엘리먼트가 바인딩되면 ResizeObserver 설정
  $: if (progressBarElement || progressTrackElement) {
    setupResizeObserver();
  }

  onDestroy(() => {
    if (resizeObserver) {
      resizeObserver.disconnect();
      resizeObserver = null;
    }
  });
</script>

<div class="download-progress">
  <div class="progress-container">
    <div class="progress-bar" bind:this={progressBarElement}>
      <div class="progress-track" bind:this={progressTrackElement}></div>
      <div class="progress-fill {percentage >= 100 ? 'progress-fill-complete' : ''}" style="width: {progressWidth}"></div>
      <div class="progress-glow" style="width: {progressWidth}"></div>
      <div class="progress-shimmer" style="width: {progressWidth}"></div>
    </div>
    <div class="percentage-display">
      <span class="percentage-text">{percentage}%</span>
    </div>
  </div>
</div>

<style>
  .download-progress {
    width: 100%;
    max-width: 304px;
    margin: 1rem auto;
    padding: 0;
  }

  .progress-container {
    position: relative;
    width: 100%;
    padding: 0;
    margin: 0;
  }

  .progress-bar {
    position: relative;
    width: 100%;
    height: 16px;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 
      0 4px 20px rgba(0, 0, 0, 0.15),
      inset 0 2px 4px rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(8px);
    /* 정확한 너비 계산을 위해 모든 여백 제거 */
    padding: 0;
    margin: 0;
    border: none;
    box-sizing: border-box;
  }

  .progress-track {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, 
      rgba(30, 41, 59, 0.3) 0%, 
      rgba(51, 65, 85, 0.2) 100%
    );
    border-radius: 16px;
    /* border 제거로 정확한 너비 확보 */
  }

  .progress-fill {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    background: linear-gradient(90deg, 
      #3b82f6 0%, 
      #6366f1 50%, 
      #8b5cf6 100%
    );
    border-radius: 16px;
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 
      0 0 30px rgba(59, 130, 246, 0.6),
      inset 0 1px 0 rgba(255, 255, 255, 0.3),
      inset 0 -1px 0 rgba(0, 0, 0, 0.1);
    overflow: hidden;
    /* 정확한 너비 계산을 위한 box-sizing */
    box-sizing: border-box;
    /* border와 padding 없이 정확한 너비 사용 */
    border: none;
    padding: 0;
    margin: 0;
    /* 최소/최대 너비 제한 */
    min-width: 0;
    max-width: 100%;
  }

  /* 100% 완료 시 특별 처리 */
  .progress-fill-complete {
    /* 100%일 때는 정확히 부모 크기와 일치 */
    width: 100% !important;
    border-radius: 16px;
    /* 모든 모서리를 정확히 채우도록 */
    right: 0;
  }

  .progress-fill::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, 
      transparent, 
      rgba(255, 255, 255, 0.4), 
      transparent
    );
    animation: progressFlow 2s infinite;
  }

  .progress-glow {
    position: absolute;
    top: -8px;
    left: 0;
    height: 32px;
    background: radial-gradient(ellipse, 
      rgba(59, 130, 246, 0.8) 0%, 
      rgba(99, 102, 241, 0.6) 40%, 
      rgba(139, 92, 246, 0.4) 70%,
      transparent 100%
    );
    border-radius: 16px;
    filter: blur(12px);
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    animation: glowPulse 3s ease-in-out infinite;
    opacity: 0.8;
    /* 정확한 너비 동기화 */
    box-sizing: border-box;
    min-width: 0;
    max-width: calc(100% + 16px); /* 글로우 효과를 위한 약간의 여유 */
  }

  .progress-shimmer {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    background: linear-gradient(45deg,
      transparent 30%,
      rgba(255, 255, 255, 0.2) 50%,
      transparent 70%
    );
    border-radius: 16px;
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    animation: shimmerSweep 4s ease-in-out infinite;
    /* 정확한 너비 동기화 */
    box-sizing: border-box;
    min-width: 0;
    max-width: 100%;
  }

  .percentage-display {
    margin-top: 0.75rem;
    text-align: center;
    padding: 0;
  }

  .percentage-text {
    display: inline-block;
    padding: 0.5rem 1.25rem;
    background: linear-gradient(135deg, 
      rgba(255, 255, 255, 0.95) 0%, 
      rgba(248, 250, 252, 0.95) 100%
    );
    backdrop-filter: blur(10px);
    border: 2px solid rgba(59, 130, 246, 0.3);
    border-radius: 16px;
    font-size: 0.875rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    
    /* 명확한 텍스트 색상 */
    color: #1e293b;
    text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
    
    /* 글로우 효과 */
    box-shadow: 
      0 4px 12px rgba(59, 130, 246, 0.2),
      0 2px 4px rgba(0, 0, 0, 0.1),
      inset 0 1px 0 rgba(255, 255, 255, 0.6);
  }

  .percentage-text::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, 
      rgba(59, 130, 246, 0.05) 0%, 
      rgba(99, 102, 241, 0.05) 100%
    );
    border-radius: 14px;
    z-index: -1;
    transition: all 0.3s ease;
    opacity: 0;
  }

  .percentage-text::after {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: linear-gradient(135deg, #3b82f6, #6366f1, #8b5cf6);
    border-radius: 16px;
    z-index: -2;
    opacity: 0.1;
    transition: all 0.3s ease;
  }

  .percentage-text:hover {
    transform: translateY(-1px);
    background: linear-gradient(135deg, 
      rgba(255, 255, 255, 1) 0%, 
      rgba(248, 250, 252, 1) 100%
    );
    box-shadow: 
      0 6px 20px rgba(59, 130, 246, 0.3),
      0 4px 8px rgba(0, 0, 0, 0.15),
      inset 0 1px 0 rgba(255, 255, 255, 0.8);
    border-color: rgba(59, 130, 246, 0.5);
  }

  .percentage-text:hover::before {
    opacity: 1;
  }

  .percentage-text:hover::after {
    opacity: 0.2;
  }

  @keyframes progressFlow {
    0% {
      left: -100%;
    }
    100% {
      left: 100%;
    }
  }

  @keyframes glowPulse {
    0%, 100% {
      opacity: 0.6;
      transform: scaleY(1);
    }
    50% {
      opacity: 1;
      transform: scaleY(1.2);
    }
  }

  @keyframes shimmerSweep {
    0% {
      transform: translateX(-100%);
      opacity: 0;
    }
    50% {
      opacity: 1;
    }
    100% {
      transform: translateX(100%);
      opacity: 0;
    }
  }

  /* 반응형 디자인 */
  @media (max-width: 768px) {
    .download-progress {
      max-width: 280px;
      padding: 0.25rem;
    }
    
    .progress-bar {
      height: 12px;
    }
    
    .percentage-text {
      font-size: 0.75rem;
      padding: 0.4rem 1rem;
    }
  }

  /* 디버그 정보 스타일 (개발용) */
  .debug-info {
    margin-top: 0.5rem;
    text-align: center;
    opacity: 0.6;
  }

  .debug-info small {
    color: #64748b;
    font-size: 0.75rem;
    font-family: monospace;
    background: rgba(0, 0, 0, 0.05);
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
  }
</style>
