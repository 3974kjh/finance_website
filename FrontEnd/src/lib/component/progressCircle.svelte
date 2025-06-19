<script lang="ts">
  export let size: number = 50; // 로딩 서클의 크기 (기본값: 50px)
  export let color: string = "#3498db"; // 로딩 서클의 색상 (기본값: 파란색)
  export let thickness: number = 5; // 서클 두께 (기본값: 4px)
  export let text: string = "Loading..."; // 로딩 서클 아래에 표시할 텍스트
  export let isLarge: boolean = false;
  export let isTextBlack: boolean = true;
</script>

<div class="loading-container">
  <div class="loading-wrapper" class:large={isLarge}>
    <div
      class="loading-circle"
      class:large={isLarge}
      class:dark-theme={isTextBlack}
      class:light-theme={!isTextBlack}
      style="
        width: {isLarge ? size * 1.5 : size}px;
        height: {isLarge ? size * 1.5 : size}px;
        border-width: {isLarge ? thickness * 1.5 : thickness}px;
      "
    ></div>
    <div class="loading-glow" class:large={isLarge} class:dark-theme={isTextBlack} class:light-theme={!isTextBlack}></div>
  </div>
  {#if text}
    <div 
      class="loading-text" 
      class:large={isLarge}
      class:dark-theme={isTextBlack} 
      class:light-theme={!isTextBlack}
    >
      {text}
    </div>
  {/if}
</div>

<style>
  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 0.5rem;
  }

  .loading-wrapper {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 0.75rem;
  }

  .loading-wrapper.large {
    margin-bottom: 1rem;
  }

  .loading-circle {
    border-style: solid;
    border-radius: 50%;
    border-color: transparent;
    animation: spin 1s linear infinite;
    position: relative;
    z-index: 2;
    transition: all 0.3s ease;
  }

  /* 다크 테마 (isTextBlack = true) */
  .loading-circle.dark-theme {
    border-top-color: #1e293b;
    border-right-color: #334155;
    filter: drop-shadow(0 0 12px rgba(30, 41, 59, 0.6));
  }

  /* 라이트 테마 (isTextBlack = false) */
  .loading-circle.light-theme {
    border-top-color: #3b82f6;
    border-right-color: #6366f1;
    filter: drop-shadow(0 0 12px rgba(59, 130, 246, 0.6));
  }

  .loading-circle.large {
    filter: drop-shadow(0 0 20px rgba(59, 130, 246, 0.8));
  }

  .loading-circle.large.dark-theme {
    filter: drop-shadow(0 0 20px rgba(30, 41, 59, 0.8));
  }

  .loading-glow {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: calc(100% + 20px);
    height: calc(100% + 20px);
    border-radius: 50%;
    animation: pulse 2s ease-in-out infinite;
    z-index: 1;
    transition: all 0.3s ease;
  }

  .loading-glow.dark-theme {
    background: radial-gradient(circle, 
      rgba(30, 41, 59, 0.4) 0%, 
      rgba(51, 65, 85, 0.3) 30%, 
      transparent 70%
    );
  }

  .loading-glow.light-theme {
    background: radial-gradient(circle, 
      rgba(59, 130, 246, 0.4) 0%, 
      rgba(99, 102, 241, 0.3) 30%, 
      transparent 70%
    );
  }

  .loading-glow.large {
    width: calc(100% + 40px);
    height: calc(100% + 40px);
  }

  .loading-glow.large.dark-theme {
    background: radial-gradient(circle, 
      rgba(30, 41, 59, 0.6) 0%, 
      rgba(51, 65, 85, 0.4) 30%, 
      transparent 70%
    );
  }

  .loading-glow.large.light-theme {
    background: radial-gradient(circle, 
      rgba(59, 130, 246, 0.6) 0%, 
      rgba(99, 102, 241, 0.4) 30%, 
      transparent 70%
    );
  }

  .loading-text {
    font-weight: 600;
    text-align: center;
    letter-spacing: 0.025em;
    transition: all 0.3s ease;
    font-size: 0.875rem;
    margin-top: 0.5rem;
  }

  .loading-text.large {
    font-size: 1.125rem;
    font-weight: 700;
    margin-top: 0.75rem;
    letter-spacing: 0.05em;
  }

  .loading-text.dark-theme {
    color: #1e293b;
    text-shadow: 0 1px 3px rgba(30, 41, 59, 0.3);
    background: linear-gradient(135deg, #1e293b, #334155);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .loading-text.light-theme {
    color: #f8fafc;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
    background: linear-gradient(135deg, #f8fafc, #e2e8f0);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .loading-text.large.dark-theme {
    text-shadow: 0 2px 6px rgba(30, 41, 59, 0.4);
  }

  .loading-text.large.light-theme {
    text-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 0.6;
      transform: translate(-50%, -50%) scale(1);
    }
    50% {
      opacity: 1;
      transform: translate(-50%, -50%) scale(1.1);
    }
  }

  /* 반응형 디자인 */
  @media (max-width: 768px) {
    .loading-text {
      font-size: 0.8rem;
    }
    
    .loading-text.large {
      font-size: 1rem;
    }
  }
</style>
