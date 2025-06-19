<script lang="ts">
  export let value: number = 50;
  export let min: number = 200;
  export let max: number = 3000;

  function handleInput(event: Event) {
    value = Number((event.target as HTMLInputElement).value);
  }
</script>

<div class="rangebar-container">
  <input 
    type="range" 
    autocomplete="off"
    min={min}
    max={max}
    bind:value 
    on:input={handleInput}
    class="range-slider"
  />
  <span class="range-value">{value}</span>
</div>

<style>
  .rangebar-container {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .range-slider {
    width: 200px;
    height: 6px;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border-radius: 50px;
    outline: none;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    -webkit-appearance: none;
    appearance: none;
  }

  .range-slider:hover {
    background: rgba(255, 255, 255, 0.15);
    border-color: rgba(255, 255, 255, 0.3);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
  }

  .range-slider:focus {
    background: rgba(255, 255, 255, 0.2);
    border-color: rgba(59, 130, 246, 0.5);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
  }

  /* Webkit 스타일 (Chrome, Safari) */
  .range-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 18px;
    height: 18px;
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    border-radius: 50%;
    cursor: pointer;
    border: 2px solid rgba(255, 255, 255, 0.3);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    transition: all 0.2s ease;
  }

  .range-slider::-webkit-slider-thumb:hover {
    background: linear-gradient(135deg, #2563eb, #4f46e5);
    transform: scale(1.1);
    box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
    border-color: rgba(255, 255, 255, 0.5);
  }

  .range-slider::-webkit-slider-thumb:active {
    transform: scale(0.95);
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.5);
  }

  /* Firefox 스타일 */
  .range-slider::-moz-range-thumb {
    width: 18px;
    height: 18px;
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    border-radius: 50%;
    cursor: pointer;
    border: 2px solid rgba(255, 255, 255, 0.3);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    transition: all 0.2s ease;
  }

  .range-slider::-moz-range-thumb:hover {
    background: linear-gradient(135deg, #2563eb, #4f46e5);
    transform: scale(1.1);
    box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
    border-color: rgba(255, 255, 255, 0.5);
  }

  .range-slider::-moz-range-track {
    background: transparent;
    border: none;
  }

  /* 값 표시 스타일 */
  .range-value {
    min-width: 60px;
    padding: 4px 12px;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    color: white;
    font-size: 0.875rem;
    font-weight: 500;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
  }

  .range-value:hover {
    background: rgba(255, 255, 255, 0.15);
    border-color: rgba(255, 255, 255, 0.3);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
  }

  /* 반응형 디자인 */
  @media (max-width: 768px) {
    .range-slider {
      width: 150px;
    }
    
    .range-value {
      min-width: 50px;
      padding: 3px 8px;
      font-size: 0.8rem;
    }
  }
</style>