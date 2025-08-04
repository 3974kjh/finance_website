<script lang="ts">
  import { onMount } from 'svelte';
  import { getGameRanking } from '../../api-connector/GameApi';
  import { GAME_KIND_MODE } from '../enums';
  import toast from 'svelte-french-toast';

  // Props
  export let show = false;
  export let onClose: () => void = () => {};

  // Internal state
  let isLoading = false;
  let selectedGameType = 'SnakeGame';
  let rankings: any[] = [];
  let totalCount = 0;

  const gameTypes = [
    { id: 'SnakeGame', name: 'Snake Game', mode: GAME_KIND_MODE.SNAKE_GAME, icon: '🐍' },
    { id: 'SpaceShootingGame', name: 'Space Shooting Game', mode: GAME_KIND_MODE.SPACE_SHOOTING_GAME, icon: '🚀' }
  ];

  function closeModal() {
    show = false;
    onClose();
  }

  // 날짜 포맷팅 함수 (YYYY-MM-DD HH:MM)
  function formatDate(dateString: string): string {
    try {
      const date = new Date(dateString);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      
      return `${year}-${month}-${day} ${hours}:${minutes}`;
    } catch (error) {
      return dateString;
    }
  }

  // 랭킹 데이터 가져오기
  async function loadRankings() {
    if (isLoading) return;
    
    isLoading = true;
    
    try {
      const currentGame = gameTypes.find(game => game.id === selectedGameType);
      if (!currentGame) return;

      const result = await getGameRanking({
        gameType: selectedGameType,
        mode: currentGame.mode,
        limit: 50
      });

      if (result.success) {
        rankings = result.data || [];
        totalCount = result.totalCount || 0;
      } else {
        toast.error('랭킹 데이터를 불러오는데 실패했습니다.');
        rankings = [];
        totalCount = 0;
      }
    } catch (error) {
      console.error('랭킹 로딩 에러:', error);
      toast.error('랭킹 데이터를 불러오는 중 오류가 발생했습니다.');
      rankings = [];
      totalCount = 0;
    } finally {
      isLoading = false;
    }
  }

  // 게임 타입 변경 시 랭킹 재로드
  function changeGameType(gameType: string) {
    selectedGameType = gameType;
    loadRankings();
  }

  // 순위 메달 아이콘 반환
  function getRankIcon(rank: number): string {
    switch (rank) {
      case 1: return '🥇';
      case 2: return '🥈';
      case 3: return '🥉';
      default: return `${rank}`;
    }
  }

  // 키보드 이벤트 처리
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      closeModal();
    }
  }

  // 모달이 열릴 때 랭킹 로드
  $: if (show) {
    loadRankings();
  }

  onMount(() => {
    if (show) {
      loadRankings();
    }
  });
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
        <h2 id="modal-title">🏆 게임 랭킹</h2>
        <button class="close-btn" on:click={closeModal} aria-label="닫기">×</button>
      </div>

      <div class="modal-body">
        <!-- 게임 선택 탭 -->
        <div class="game-tabs">
          {#each gameTypes as gameType}
            <button
              class="tab-button"
              class:active={selectedGameType === gameType.id}
              on:click={() => changeGameType(gameType.id)}
            >
              <span class="tab-icon">{gameType.icon}</span>
              <span class="tab-name">{gameType.name}</span>
            </button>
          {/each}
        </div>

        <!-- 랭킹 헤더 -->
        <div class="ranking-header">
          <div class="ranking-title">
            {gameTypes.find(game => game.id === selectedGameType)?.icon || '🎮'} 
            {gameTypes.find(game => game.id === selectedGameType)?.name || '게임'} 랭킹
          </div>
          <div class="total-count">
            총 {totalCount}개의 기록
          </div>
        </div>

        <!-- 랭킹 리스트 -->
        <div class="ranking-list">
          {#if isLoading}
            <div class="loading-state">
              <div class="loading-spinner"></div>
              <p>랭킹을 불러오는 중...</p>
            </div>
          {:else if rankings.length === 0}
            <div class="empty-state">
              <div class="empty-icon">📊</div>
              <p>아직 등록된 랭킹이 없습니다.</p>
              <p>게임을 플레이하고 첫 번째 랭킹을 등록해보세요!</p>
            </div>
          {:else}
            <div class="rank-table-header">
              <div class="rank-col">순위</div>
              <div class="user-col">사용자</div>
              <div class="score-col">점수</div>
              <div class="date-col">달성일시</div>
            </div>
            
            <div class="rank-items">
              {#each rankings as ranking, index}
                <div class="rank-item" class:top-rank={index < 3}>
                  <div class="rank-col">
                    <span class="rank-icon">{getRankIcon(index + 1)}</span>
                  </div>
                  <div class="user-col">
                    <span class="user-name">{ranking.id}</span>
                  </div>
                  <div class="score-col">
                    <span class="score-value">{ranking.score.toLocaleString()}</span>
                  </div>
                  <div class="date-col">
                    <span class="date-value">{formatDate(ranking.timestamp)}</span>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" on:click={closeModal}>
          닫기
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
    border: 2px solid #22c55e;
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(34, 197, 94, 0.3);
    width: 90%;
    max-width: 800px;
    max-height: 90vh;
    overflow: hidden;
    animation: modalSlideIn 0.3s ease-out;
    display: flex;
    flex-direction: column;
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
    border-bottom: 1px solid #22c55e;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
  }

  .modal-header h2 {
    margin: 0;
    color: #22c55e;
    font-family: 'Courier New', monospace;
    font-size: 1.5rem;
    text-shadow: 0 0 10px rgba(34, 197, 94, 0.5);
  }

  .close-btn {
    background: none;
    border: none;
    color: #22c55e;
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
    background: rgba(34, 197, 94, 0.1);
    transform: scale(1.1);
  }

  .modal-body {
    padding: 25px;
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  /* 게임 선택 탭 */
  .game-tabs {
    display: flex;
    gap: 10px;
    margin-bottom: 25px;
    border-bottom: 1px solid rgba(34, 197, 94, 0.3);
    padding-bottom: 15px;
  }

  .tab-button {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 15px;
    background: rgba(34, 197, 94, 0.1);
    border: 2px solid rgba(34, 197, 94, 0.3);
    border-radius: 8px;
    color: #94a3b8;
    font-family: 'Courier New', monospace;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s ease;
    flex: 1;
    justify-content: center;
  }

  .tab-button:hover {
    background: rgba(34, 197, 94, 0.15);
    border-color: rgba(34, 197, 94, 0.5);
    color: #e2e8f0;
  }

  .tab-button.active {
    background: rgba(34, 197, 94, 0.2);
    border-color: #22c55e;
    color: #22c55e;
    box-shadow: 0 0 10px rgba(34, 197, 94, 0.3);
  }

  .tab-icon {
    font-size: 1.2rem;
  }

  .tab-name {
    font-size: 0.9rem;
  }

  /* 랭킹 헤더 */
  .ranking-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 15px 20px;
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.3);
    border-radius: 10px;
  }

  .ranking-title {
    font-size: 1.2rem;
    font-weight: bold;
    color: #22c55e;
    font-family: 'Courier New', monospace;
  }

  .total-count {
    font-size: 0.9rem;
    color: #94a3b8;
    font-family: 'Courier New', monospace;
  }

  /* 랭킹 리스트 */
  .ranking-list {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
  }

  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    padding: 40px 20px;
    color: #94a3b8;
    font-family: 'Courier New', monospace;
  }

  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid rgba(34, 197, 94, 0.3);
    border-top: 3px solid #22c55e;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 15px;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    padding: 40px 20px;
    color: #94a3b8;
    font-family: 'Courier New', monospace;
    text-align: center;
  }

  .empty-icon {
    font-size: 3rem;
    margin-bottom: 15px;
    opacity: 0.7;
  }

  .empty-state p {
    margin: 5px 0;
    line-height: 1.4;
  }

  /* 랭킹 테이블 */
  .rank-table-header {
    display: grid;
    grid-template-columns: 60px 1fr 120px 140px;
    gap: 15px;
    padding: 15px 20px;
    background: rgba(34, 197, 94, 0.15);
    border: 1px solid rgba(34, 197, 94, 0.3);
    border-radius: 8px 8px 0 0;
    font-family: 'Courier New', monospace;
    font-weight: bold;
    color: #22c55e;
    font-size: 0.9rem;
  }

  .rank-items {
    border: 1px solid rgba(34, 197, 94, 0.3);
    border-top: none;
    border-radius: 0 0 8px 8px;
    overflow: hidden;
    flex: 1;
    overflow-y: auto;
    min-height: 0;
  }

  .rank-item {
    display: grid;
    grid-template-columns: 60px 1fr 120px 140px;
    gap: 15px;
    padding: 12px 20px;
    border-bottom: 1px solid rgba(34, 197, 94, 0.2);
    transition: all 0.2s ease;
    font-family: 'Courier New', monospace;
  }

  .rank-item:hover {
    background: rgba(34, 197, 94, 0.05);
  }

  .rank-item:last-child {
    border-bottom: none;
  }

  .rank-item.top-rank {
    background: rgba(255, 215, 0, 0.05);
    border-bottom-color: rgba(255, 215, 0, 0.3);
  }

  .rank-item.top-rank:hover {
    background: rgba(255, 215, 0, 0.1);
  }

  .rank-col, .user-col, .score-col, .date-col {
    display: flex;
    align-items: center;
  }

  .rank-icon {
    font-size: 1.2rem;
    font-weight: bold;
  }

  .user-name {
    color: #e2e8f0;
    font-weight: bold;
    word-break: break-all;
  }

  .score-value {
    color: #22c55e;
    font-weight: bold;
    text-align: right;
    width: 100%;
  }

  .date-value {
    color: #94a3b8;
    font-size: 0.85rem;
  }

  .modal-footer {
    padding: 15px 25px 25px;
    display: flex;
    justify-content: center;
    border-top: 1px solid rgba(34, 197, 94, 0.3);
    flex-shrink: 0;
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

  .btn-secondary {
    background: transparent;
    border-color: #666666;
    color: #cccccc;
    min-width: 120px;
  }

  .btn-secondary:hover {
    border-color: #888888;
    color: #ffffff;
    background: rgba(255, 255, 255, 0.1);
  }

  /* 반응형 디자인 */
  @media (max-width: 768px) {
    .modal-content {
      width: 95%;
      max-height: 95vh;
    }

    .game-tabs {
      flex-direction: column;
      gap: 8px;
    }

    .tab-button {
      justify-content: flex-start;
    }

    .ranking-header {
      flex-direction: column;
      gap: 10px;
      text-align: center;
    }

    .rank-table-header {
      grid-template-columns: 50px 1fr 80px 110px;
      gap: 8px;
      padding: 12px 15px;
      font-size: 0.8rem;
    }

    .rank-item {
      grid-template-columns: 50px 1fr 80px 110px;
      gap: 8px;
      padding: 10px 15px;
    }

    .rank-icon {
      font-size: 1rem;
    }

    .score-value {
      font-size: 0.9rem;
    }

    .date-value {
      font-size: 0.75rem;
    }
  }

  @media (max-width: 480px) {
    .modal-content {
      width: 98%;
      max-height: 98vh;
    }

    .modal-header h2 {
      font-size: 1.3rem;
    }

    .ranking-title {
      font-size: 1rem;
    }

    .rank-table-header {
      grid-template-columns: 40px 1fr 70px 90px;
      gap: 5px;
      padding: 10px 12px;
      font-size: 0.75rem;
    }

    .rank-item {
      grid-template-columns: 40px 1fr 70px 90px;
      gap: 5px;
      padding: 8px 12px;
    }

    .user-name {
      font-size: 0.85rem;
    }

    .score-value {
      font-size: 0.8rem;
    }

    .date-value {
      font-size: 0.7rem;
    }
  }

  /* 스크롤바 스타일 */
  .rank-items::-webkit-scrollbar {
    width: 6px;
  }

  .rank-items::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.3);
    border-radius: 3px;
  }

  .rank-items::-webkit-scrollbar-thumb {
    background: linear-gradient(45deg, #22c55e, #16a34a);
    border-radius: 3px;
  }

  .rank-items::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(45deg, #4ade80, #22c55e);
  }
</style>
