<script lang="ts">
  export let min: number = 0;
  export let max: number = 100;
  export let nowCount: number;

  $: percentage = Math.round(((nowCount - min) / (max - min)) * 100);
  $: progressWidth = `${percentage}%`;
</script>

<div class="download-progress">
  <div class="progress-container">
    <div class="progress-bar">
      <div class="progress-track"></div>
      <div class="progress-fill" style="width: {progressWidth}"></div>
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
    max-width: 320px;
    margin: 1rem auto;
    padding: 0.5rem;
  }

  .progress-container {
    position: relative;
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
    border: 1px solid rgba(71, 85, 105, 0.2);
    border-radius: 16px;
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
    position: relative;
    overflow: hidden;
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
  }

  .percentage-display {
    margin-top: 1rem;
    text-align: center;
  }

  .percentage-text {
    display: inline-block;
    padding: 0.5rem 1.25rem;
    background: linear-gradient(135deg, 
      rgba(59, 130, 246, 0.1) 0%, 
      rgba(99, 102, 241, 0.1) 50%,
      rgba(139, 92, 246, 0.1) 100%
    );
    backdrop-filter: blur(10px);
    border: 2px solid transparent;
    background-clip: padding-box;
    border-radius: 16px;
    font-size: 0.875rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    
    /* 그라데이션 텍스트 */
    background: linear-gradient(135deg, #3b82f6, #6366f1, #8b5cf6);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    
    /* 글로우 효과 */
    filter: drop-shadow(0 0 8px rgba(59, 130, 246, 0.3));
  }

  .percentage-text::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, 
      rgba(59, 130, 246, 0.1) 0%, 
      rgba(99, 102, 241, 0.1) 50%,
      rgba(139, 92, 246, 0.1) 100%
    );
    border-radius: 14px;
    z-index: -1;
    transition: all 0.3s ease;
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
    opacity: 0.3;
    transition: all 0.3s ease;
  }

  .percentage-text:hover {
    transform: translateY(-1px);
    filter: drop-shadow(0 0 16px rgba(59, 130, 246, 0.5));
  }

  .percentage-text:hover::before {
    background: linear-gradient(135deg, 
      rgba(59, 130, 246, 0.2) 0%, 
      rgba(99, 102, 241, 0.2) 50%,
      rgba(139, 92, 246, 0.2) 100%
    );
  }

  .percentage-text:hover::after {
    opacity: 0.6;
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
</style>
