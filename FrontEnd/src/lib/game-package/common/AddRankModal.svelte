<script lang="ts">
	import toast from 'svelte-french-toast';
  import { saveGameScore } from '../../api-connector/GameApi';
	import { GAME_KIND_MODE } from '../enums';

  // Props
  export let show = false;
  export let gameType: 'SnakeGame' | 'SpaceShootingGame' = 'SnakeGame';
  export let gameDisplayName: string = 'Game';
  export let score: number = 0;
  export let mode: string = GAME_KIND_MODE.SNAKE_GAME;
  export let initialUserId: string = 'guest';
  export let onClose: () => void = () => {};
  export let onSuccess: () => void = () => {};

  // Internal state
  let modalUserId = initialUserId;
  let isSubmitting = false;

  // 컴포넌트가 표시될 때마다 사용자 ID 초기화
  $: if (show) {
    modalUserId = initialUserId;
    isSubmitting = false;
  }

  function closeModal() {
    show = false;
    isSubmitting = false;
    onClose();
  }

  async function submitRanking() {
    if (isSubmitting) return;
    
    isSubmitting = true;
    
    try {
      const result = await saveGameScore({
        gameType,
        userId: modalUserId.trim(),
        mode,
        score
      });
      
      if (result.success) {
        onSuccess();
        closeModal();
      } else {
        toast.error('랭킹 등록에 실패했습니다.');
      }
    } catch (error) {
      toast.error('랭킹 등록 중 오류가 발생했습니다.');
    } finally {
      isSubmitting = false;
    }
  }

  // 키보드 이벤트 처리
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      closeModal();
    } else if (event.key === 'Enter' && modalUserId.trim() && !isSubmitting) {
      submitRanking();
    }
  }
</script>

{#if show}
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
  <div 
    class="modal-overlay" 
    on:click={closeModal}
    on:keydown={handleKeydown}
    role="dialog"
    aria-modal="true"
    aria-labelledby="modal-title"
  >
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="modal-content" on:click|stopPropagation on:keydown={handleKeydown}>
      <div class="modal-header">
        <h2 id="modal-title">🏆 랭킹 등록</h2>
        <button class="close-btn" on:click={closeModal} aria-label="닫기">×</button>
      </div>
      
      <div class="modal-body">
        <div class="score-info">
          <div class="game-info">
            <span class="label">게임:</span>
            <span class="value">{gameDisplayName}</span>
          </div>
          <div class="mode-info">
            <span class="label">모드:</span>
            <span class="value">{mode}</span>
          </div>
          <div class="score-display">
            <span class="label">점수:</span>
            <span class="value score">{score.toLocaleString()}</span>
          </div>
        </div>
        
        <div class="input-section">
          <label for="userId">사용자 ID:</label>
          <input 
            id="userId"
            type="text" 
            bind:value={modalUserId} 
            placeholder="사용자 ID를 입력하세요"
            maxlength="20"
            autocomplete="off"
            on:keydown={handleKeydown}
          />
        </div>
      </div>
      
      <div class="modal-footer">
        <button 
          class="btn btn-primary" 
          on:click={submitRanking}
          disabled={isSubmitting || !modalUserId.trim()}
        >
          {isSubmitting ? '등록 중...' : '예'}
        </button>
        <button class="btn btn-secondary" on:click={closeModal}>
          아니오
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    backdrop-filter: blur(5px);
    animation: fadeIn 0.3s ease-out;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .modal-content {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 2px solid var(--theme-color, #44ff44);
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(68, 255, 68, 0.3);
    width: 90%;
    max-width: 450px;
    max-height: 90vh;
    overflow-y: auto;
    animation: modalSlideIn 0.3s ease-out;
  }

  /* SpaceShootingGame 테마 */
  :global(.space-theme) .modal-content {
    border-color: #00ff88;
    box-shadow: 0 10px 30px rgba(0, 255, 136, 0.3);
  }

  @keyframes modalSlideIn {
    from {
      opacity: 0;
      transform: translateY(-30px) scale(0.95);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  .modal-header {
    padding: 20px 25px 15px;
    border-bottom: 1px solid var(--theme-color, #44ff44);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .modal-header h2 {
    margin: 0;
    color: var(--theme-color, #44ff44);
    font-family: 'Courier New', monospace;
    font-size: 1.5rem;
    text-shadow: 0 0 10px rgba(68, 255, 68, 0.5);
  }

  /* SpaceShootingGame 테마 */
  :global(.space-theme) .modal-header {
    border-bottom-color: #00ff88;
  }

  :global(.space-theme) .modal-header h2 {
    color: #00ff88;
    text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
  }

  .close-btn {
    background: none;
    border: none;
    color: var(--theme-color, #44ff44);
    font-size: 1.8rem;
    cursor: pointer;
    padding: 0;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all 0.2s ease;
  }

  .close-btn:hover {
    background: rgba(68, 255, 68, 0.1);
    transform: scale(1.1);
  }

  :global(.space-theme) .close-btn {
    color: #00ff88;
  }

  :global(.space-theme) .close-btn:hover {
    background: rgba(0, 255, 136, 0.1);
  }

  .modal-body {
    padding: 25px;
  }

  .score-info {
    background: rgba(68, 255, 68, 0.1);
    border: 1px solid rgba(68, 255, 68, 0.3);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 25px;
  }

  :global(.space-theme) .score-info {
    background: rgba(0, 255, 136, 0.1);
    border-color: rgba(0, 255, 136, 0.3);
  }

  .game-info, .mode-info, .score-display {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    font-family: 'Courier New', monospace;
  }

  .score-display {
    margin-bottom: 0;
    padding-top: 10px;
    border-top: 1px solid rgba(68, 255, 68, 0.3);
  }

  :global(.space-theme) .score-display {
    border-top-color: rgba(0, 255, 136, 0.3);
  }

  .label {
    color: #cccccc;
    font-weight: bold;
  }

  .value {
    color: #ffffff;
    font-weight: bold;
  }

  .value.score {
    color: var(--theme-color, #44ff44);
    font-size: 1.2rem;
    text-shadow: 0 0 5px rgba(68, 255, 68, 0.5);
  }

  :global(.space-theme) .value.score {
    color: #00ff88;
    text-shadow: 0 0 5px rgba(0, 255, 136, 0.5);
  }

  .input-section {
    margin-bottom: 20px;
  }

  .input-section label {
    display: block;
    color: var(--theme-color, #44ff44);
    font-family: 'Courier New', monospace;
    font-weight: bold;
    margin-bottom: 8px;
    font-size: 0.95rem;
  }

  :global(.space-theme) .input-section label {
    color: #00ff88;
  }

  .input-section input {
    width: 100%;
    padding: 12px 15px;
    border: 2px solid rgba(68, 255, 68, 0.3);
    border-radius: 8px;
    background: rgba(0, 0, 0, 0.3);
    color: #ffffff;
    font-family: 'Courier New', monospace;
    font-size: 1rem;
    transition: all 0.3s ease;
    box-sizing: border-box;
  }

  .input-section input:focus {
    outline: none;
    border-color: var(--theme-color, #44ff44);
    box-shadow: 0 0 10px rgba(68, 255, 68, 0.3);
    background: rgba(0, 0, 0, 0.5);
  }

  :global(.space-theme) .input-section input {
    border-color: rgba(0, 255, 136, 0.3);
  }

  :global(.space-theme) .input-section input:focus {
    border-color: #00ff88;
    box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
  }

  .input-section input::placeholder {
    color: #888888;
  }

  .modal-footer {
    padding: 15px 25px 25px;
    display: flex;
    gap: 15px;
    justify-content: flex-end;
  }

  .btn {
    padding: 12px 25px;
    border: 2px solid;
    border-radius: 8px;
    font-family: 'Courier New', monospace;
    font-weight: bold;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.3s ease;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .btn-primary {
    background: var(--theme-color, #44ff44);
    border-color: var(--theme-color, #44ff44);
    color: #001133;
  }

  .btn-primary:hover:not(:disabled) {
    background: #33cc33;
    border-color: #33cc33;
    box-shadow: 0 0 15px rgba(68, 255, 68, 0.4);
    transform: translateY(-2px);
  }

  :global(.space-theme) .btn-primary {
    background: #00ff88;
    border-color: #00ff88;
  }

  :global(.space-theme) .btn-primary:hover:not(:disabled) {
    background: #00cc6a;
    border-color: #00cc6a;
    box-shadow: 0 0 15px rgba(0, 255, 136, 0.4);
  }

  .btn-primary:disabled {
    background: #666666;
    border-color: #666666;
    color: #cccccc;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  .btn-secondary {
    background: transparent;
    border-color: #666666;
    color: #cccccc;
  }

  .btn-secondary:hover {
    border-color: #888888;
    color: #ffffff;
    background: rgba(255, 255, 255, 0.1);
  }

  @media (max-width: 480px) {
    .modal-content {
      width: 95%;
      margin: 10px;
    }
    
    .modal-header h2 {
      font-size: 1.3rem;
    }
    
    .modal-footer {
      flex-direction: column;
    }
    
    .btn {
      width: 100%;
    }
  }
</style>
