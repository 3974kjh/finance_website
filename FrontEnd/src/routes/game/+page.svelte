<script lang="ts">
  import { onMount } from 'svelte';
  import { SnakeGame, SpaceShootingGame } from '$lib/game-package';
  import RankListModal from '$lib/game-package/common/RankListModal.svelte';
  
  // 게임 정보 데이터
  const gameList = [
    {
      id: 'snake',
      name: 'Snake Game',
      description: '클래식 스네이크 게임',
      component: SnakeGame,
      color: 'from-green-400 to-emerald-600',
      bgColor: 'bg-green-500/20',
      icon: '🐍'
    },
    {
      id: 'space-shooting',
      name: 'Space Shooter',
      description: '우주 비행기 슈팅 게임',
      component: SpaceShootingGame,
      color: 'from-blue-400 to-purple-600',
      bgColor: 'bg-blue-500/20',
      icon: '🚀'
    }
  ];

  // 상태 관리
  let selectedGame: any = null;
  let showGameScreen = false;
  let isGameLoading = false;
  let currentScreen = 'menu'; // 'menu' | 'game'
  let isGameExpanded = false; // 게임 전체화면 확장 상태
  let isGameReady = false; // 게임이 실제로 시작할 준비가 되었는지
  let gameExpandTimer: number | null = null;
  
  // 랭킹 모달 상태
  let showRankingModal = false;
  
  // CD 스크롤 관련 상태
  let cdContainer: HTMLElement;
  let scrollPosition = 0;
  let canScrollLeft = false;
  let canScrollRight = false;

  // 게임 선택 함수
  const selectGame = (game: any) => {
    if (isGameLoading) return;
    
    isGameLoading = true;
    selectedGame = game;
    isGameReady = false; // 게임 준비 상태 초기화
    
    // 로딩 애니메이션 후 게임 화면 표시 (하지만 게임은 아직 시작하지 않음)
    setTimeout(() => {
      currentScreen = 'game';
      showGameScreen = true;
      isGameLoading = false;
      
      // 게임 로딩 완료 후 잠시 대기하고 전체화면으로 확장
      gameExpandTimer = window?.setTimeout(() => {
        isGameExpanded = true;
        
        // 확장 애니메이션 완료 후 게임 시작
        setTimeout(() => {
          isGameReady = true; // 이제 게임 컴포넌트 렌더링
        }, 800); // 확장 애니메이션 시간과 맞춤
      }, 500); // 0.5초 후 확장
    }, 1000);
  };

  // 메인 메뉴로 돌아가기
  const backToMenu = () => {
    // 게임이 확장된 상태라면 먼저 축소
    if (isGameExpanded) {
      isGameExpanded = false;
      isGameReady = false; // 게임 컴포넌트 중지
      
      // 축소 애니메이션 완료 후 메뉴로 전환
      setTimeout(() => {
        currentScreen = 'menu';
        showGameScreen = false;
        selectedGame = null;
        
        // 타이머 정리
        if (gameExpandTimer) {
          clearTimeout(gameExpandTimer);
          gameExpandTimer = null;
        }
      }, 800); // 축소 애니메이션 시간과 맞춤
    } else {
      // 확장되지 않은 상태라면 바로 메뉴로
      currentScreen = 'menu';
      showGameScreen = false;
      selectedGame = null;
      isGameReady = false;
      
      if (gameExpandTimer) {
        clearTimeout(gameExpandTimer);
        gameExpandTimer = null;
      }
    }
  };

  // 랭킹 모달 열기
  const openRankingModal = () => {
    showRankingModal = true;
  };

  // 랭킹 모달 닫기
  const closeRankingModal = () => {
    showRankingModal = false;
  };

  // CD 스크롤 함수
  const scrollCDs = (direction: 'left' | 'right') => {
    if (!cdContainer) return;
    
    const scrollAmount = 200;
    const currentScroll = cdContainer.scrollLeft;
    const maxScroll = cdContainer.scrollWidth - cdContainer.clientWidth;
    
    if (direction === 'left') {
      scrollPosition = Math.max(0, currentScroll - scrollAmount);
    } else {
      scrollPosition = Math.min(maxScroll, currentScroll + scrollAmount);
    }
    
    cdContainer.scrollTo({
      left: scrollPosition,
      behavior: 'smooth'
    });
    
    updateScrollButtons();
  };

  // 스크롤 버튼 상태 업데이트
  const updateScrollButtons = () => {
    if (!cdContainer) return;
    
    const currentScroll = cdContainer.scrollLeft;
    const maxScroll = cdContainer.scrollWidth - cdContainer.clientWidth;
    
    canScrollLeft = currentScroll > 0;
    canScrollRight = currentScroll < maxScroll;
  };

  // 키보드 이벤트 처리
  const handleKeydown = (event: KeyboardEvent) => {
    if (event.key === 'Escape' && (showGameScreen || isGameExpanded)) {
      backToMenu();
    }
  };

  onMount(() => {
    // 키보드 이벤트 리스너 추가
    document.addEventListener('keydown', handleKeydown);
    
    // 스크롤 버튼 초기 상태 설정
    setTimeout(() => {
      if (cdContainer) {
        updateScrollButtons();
        cdContainer.addEventListener('scroll', updateScrollButtons);
      }
    }, 100); // DOM이 완전히 렌더링된 후 실행
    
    return () => {
      document.removeEventListener('keydown', handleKeydown);
      if (cdContainer) {
        cdContainer.removeEventListener('scroll', updateScrollButtons);
      }
      // 게임 확장 타이머 정리
      if (gameExpandTimer) {
        clearTimeout(gameExpandTimer);
        gameExpandTimer = null;
      }
    };
  });
</script>

<svelte:head>
  <title>아케이드 게임 - FinanceChart</title>
  <meta name="description" content="클래식 아케이드 게임 컬렉션" />
</svelte:head>

<!-- 아케이드 게임기 메인 화면 -->
<div class="w-full h-screen bg-gradient-to-b from-gray-800 via-gray-900 to-black relative overflow-hidden flex items-center justify-center">
  <!-- 배경 패턴 -->
  <div class="absolute inset-0 bg-[radial-gradient(circle_at_50%_20%,_rgba(59,130,246,0.1),_transparent_50%)]"></div>
  
  <!-- 게임 확장 컨테이너 -->
  <div class="game-expansion-container" class:expanded={isGameExpanded}>
    <!-- 아케이드 게임기 본체 -->
    <div class="arcade-machine" class:game-playing={isGameExpanded}>
      <!-- 게임기 상단부 (마키/헤더) -->
      <div class="arcade-top">
        <!-- 마키 장식 -->
        <div class="marquee-decoration">
          <div class="marquee-light left"></div>
          <div class="marquee-text">
            <span class="arcade-title">RETRO ARCADE</span>
          </div>
          <div class="marquee-light right"></div>
        </div>
        <!-- 전원 표시등 -->
        <div class="power-indicator"></div>
      </div>
      
      <!-- 게임기 메인 바디 -->
      <div class="arcade-body">
        <!-- 상단 장식 패널 -->
        <div class="top-panel">
          <div class="speaker-grille left">
            <div class="speaker-holes">
              {#each Array(12) as _, i}
                <div class="speaker-hole" style="animation-delay: {i * 0.1}s;"></div>
              {/each}
            </div>
          </div>
          
          <div class="center-logo">
            <div class="logo-text">ARCADE</div>
            <div class="logo-subtext">GAMING STATION</div>
          </div>
          
          <div class="speaker-grille right">
            <div class="speaker-holes">
              {#each Array(12) as _, i}
                <div class="speaker-hole" style="animation-delay: {i * 0.1 + 0.6}s;"></div>
              {/each}
            </div>
          </div>
        </div>
        
        <!-- 모니터 영역 -->
        <div class="monitor-container">
          <!-- 모니터 베젤 -->
          <div class="monitor-bezel">
            <!-- 화면 영역 -->
            <div class="screen-area">
              <!-- 랭킹 버튼 (모니터 화면 내 우상단) -->
              <!-- svelte-ignore a11y-click-events-have-key-events -->
              <!-- svelte-ignore a11y-no-static-element-interactions -->
              <div class="monitor-ranking-button" on:click={openRankingModal}>
                <span class="ranking-icon">🏆</span>
                <span class="ranking-text">RANK</span>
              </div>
              
              {#if currentScreen === 'menu'}
                <!-- 게임 선택 메뉴 화면 -->
                <div class="menu-screen">
                  <!-- 스캔라인 효과 -->
                  <div class="scanlines"></div>
                  
                  <!-- 메뉴 헤더 -->
                  <div class="menu-header">
                    <h1 class="arcade-menu-title crt-text">
                      ◄ GAME LIBRARY ►
                    </h1>
                    <p class="menu-subtitle crt-text">
                      SELECT YOUR GAME
                    </p>
                  </div>

                  <!-- CD 게임 선택 영역 -->
                  <div class="cd-selection-area">
                    <!-- 좌측 스크롤 버튼 -->
                    {#if canScrollLeft}
                      <!-- svelte-ignore a11y-click-events-have-key-events -->
                      <!-- svelte-ignore a11y-no-static-element-interactions -->
                      <div class="scroll-button left" on:click={() => scrollCDs('left')}>
                        <div class="scroll-arrow">◀</div>
                      </div>
                    {/if}
                    
                    <!-- CD 컨테이너 -->
                    <div class="cd-container" bind:this={cdContainer}>
                      {#each gameList as game}
                        <!-- svelte-ignore a11y-click-events-have-key-events -->
                        <!-- svelte-ignore a11y-no-static-element-interactions -->
                        <div 
                          class="cd-case"
                          on:click={() => selectGame(game)}
                        >
                          <!-- CD 디스크 -->
                          <div class="cd-disc {game.color}">
                            <!-- CD 중앙 홀 -->
                            <div class="cd-hole"></div>
                            
                            <!-- CD 반사 효과 -->
                            <div class="cd-reflection"></div>
                            <div class="cd-shine"></div>
                            
                            <!-- 게임 아이콘 -->
                            <div class="game-icon">
                              {game.icon}
                            </div>
                            
                            <!-- CD 회전 라인들 -->
                            <div class="cd-lines"></div>
                          </div>
                          
                          <!-- CD 레이블 -->
                          <div class="cd-label">
                            <h3 class="game-title crt-text">{game.name}</h3>
                            <p class="game-desc crt-text">{game.description}</p>
                          </div>
                        </div>
                      {/each}
                    </div>
                    
                    <!-- 우측 스크롤 버튼 -->
                    {#if canScrollRight}
                      <!-- svelte-ignore a11y-click-events-have-key-events -->
                      <!-- svelte-ignore a11y-no-static-element-interactions -->
                      <div class="scroll-button right" on:click={() => scrollCDs('right')}>
                        <div class="scroll-arrow">▶</div>
                      </div>
                    {/if}
                  </div>

                  <!-- 하단 안내 -->
                  <div class="menu-footer">
                    <p class="instruction-text crt-text">
                      🎮 CLICK CD TO START GAME • ESC TO EXIT 🎮
                    </p>
                  </div>
                </div>
                
              {:else if currentScreen === 'game' && selectedGame}
                <!-- 게임 플레이 화면 -->
                <div class="game-screen relative">
                  <!-- 스캔라인 효과 -->
                  <div class="scanlines"></div>
                  
                  <!-- 게임 대기 화면 -->
                  <div class="game-waiting-screen">
                    <div class="game-preview">
                      <h2 class="game-preview-title crt-text">
                        {selectedGame.name}
                      </h2>
                      <p class="game-preview-desc crt-text">
                        {selectedGame.description}
                      </p>
                      <div class="expansion-indicator">
                        <div class="expansion-dots">
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                        <p class="expansion-text crt-text">
                          PREPARING FULL SCREEN...
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              {/if}
              
              <!-- 모니터 내부 로딩 오버레이 -->
              {#if isGameLoading}
                <div class="monitor-loading-overlay">
                  <div class="loading-content">
                    <div class="loading-spinner">
                      <div class="spinner-ring"></div>
                    </div>
                    <p class="loading-text crt-text">
                      LOADING GAME...
                    </p>
                  </div>
                </div>
              {/if}
            </div>
          </div>
        </div>
        
        <!-- 컨트롤 패널 -->
        <div class="control-panel">
          <!-- 패널 상단 장식 -->
          <div class="control-panel-header">
            <div class="player-indicator">
              <span class="player-text">PLAYER 1</span>
              <div class="player-led active"></div>
            </div>
            <div class="control-center">
              <div class="credits-display">
                <span class="credits-text">CREDITS: 99</span>
              </div>
            </div>
            <div class="player-indicator">
              <span class="player-text">PLAYER 2</span>
              <div class="player-led"></div>
            </div>
          </div>
          
          <!-- 메인 컨트롤 영역 -->
          <div class="main-controls">
            <!-- 조이스틱 영역 -->
            <div class="joystick-area">
              <div class="joystick">
                <div class="joystick-base"></div>
                <div class="joystick-stick"></div>
              </div>
            </div>
            
            <!-- 버튼 영역 -->
            <div class="button-area">
              <div class="buttons-grid">
                <div class="action-button red" data-label="A"></div>
                <div class="action-button blue" data-label="B"></div>
              </div>
            </div>
            
            <!-- 시스템 버튼들 -->
            <div class="system-buttons">
              <div class="coin-slot">
                <div class="coin-opening"></div>
                <div class="coin-label">INSERT COIN</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 게임기 하단부 -->
      <div class="arcade-bottom">
        <!-- 하단 장식 그릴 -->
        <div class="bottom-grille">
          {#each Array(20) as _, i}
            <div class="grille-line"></div>
          {/each}
        </div>
        <!-- 브랜드 로고 -->
        <div class="brand-logo">RETRO GAMING CO.</div>
      </div>
    </div>
    
    <!-- 확장된 게임 화면 -->
    {#if isGameExpanded && selectedGame}
      <div class="expanded-game-screen">
        <!-- 게임 종료 버튼 -->
        <div class="game-exit-overlay">
          <!-- svelte-ignore a11y-click-events-have-key-events -->
          <!-- svelte-ignore a11y-no-static-element-interactions -->
          <div class="exit-button" on:click={backToMenu}>
            <span class="exit-text">ESC</span>
            <span class="exit-label">EXIT GAME</span>
          </div>
        </div>
        
        <!-- 확장된 게임 컨텐츠 -->
        <div class="expanded-game-content">
          {#if isGameReady}
            <svelte:component this={selectedGame.component} />
          {:else}
            <!-- 확장 완료 대기 화면 -->
            <div class="game-expansion-waiting">
              <div class="expansion-complete-indicator">
                <div class="game-start-icon">
                  {selectedGame.icon}
                </div>
                <h2 class="game-start-title">
                  {selectedGame.name}
                </h2>
                <div class="start-countdown">
                  <div class="countdown-spinner"></div>
                  <p class="countdown-text">STARTING GAME...</p>
                </div>
              </div>
            </div>
          {/if}
        </div>
      </div>
    {/if}
  </div>
</div>

<!-- 랭킹 모달 -->
<RankListModal
  bind:show={showRankingModal}
  onClose={closeRankingModal}
/>

<style>
  /* 아케이드 게임기 스타일 */
  /* .arcade-machine 스타일은 게임 확장 시스템에서 정의됨 */

  /* 상단 마키 영역 */
  .arcade-top {
    height: 6%;
    background: linear-gradient(180deg, #e2e8f0 0%, #94a3b8 50%, #64748b 100%);
    border-radius: 20px 20px 0 0;
    border: 4px solid #334155;
    position: relative;
    overflow: hidden;
    box-shadow: 
      inset 0 2px 4px rgba(255,255,255,0.3),
      inset 0 -2px 4px rgba(0,0,0,0.2);
  }

  .marquee-decoration {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 100%;
    padding: 0 20px;
    background: linear-gradient(90deg, 
      rgba(59,130,246,0.1) 0%, 
      rgba(147,51,234,0.1) 50%, 
      rgba(239,68,68,0.1) 100%);
  }

  .marquee-light {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: radial-gradient(circle, #fbbf24, #f59e0b);
    box-shadow: 
      0 0 10px #fbbf24,
      inset 0 2px 4px rgba(255,255,255,0.4),
      inset 0 -2px 4px rgba(0,0,0,0.2);
    animation: marquee-blink 2s infinite alternate;
  }

  .marquee-light.right {
    animation-delay: 1s;
  }

  .marquee-text {
    flex: 1;
    text-align: center;
  }

  .arcade-title {
    font-family: 'Impact', 'Arial Black', sans-serif;
    font-size: 2rem;
    font-weight: 900;
    color: #1e293b;
    text-shadow: 
      0 1px 0 #94a3b8,
      0 2px 0 #64748b,
      0 3px 6px rgba(0,0,0,0.3);
    letter-spacing: 3px;
  }

  /* 게임 컨트롤 헤더 */
  .game-controls-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 20px;
    background: linear-gradient(90deg, #374151 0%, #4b5563 50%, #374151 100%);
    border: 2px solid #1f2937;
    border-radius: 8px;
    margin-bottom: 15px;
    box-shadow: 
      inset 0 2px 4px rgba(255, 255, 255, 0.1),
      inset 0 -2px 4px rgba(0, 0, 0, 0.3),
      0 2px 4px rgba(0, 0, 0, 0.2);
  }

  .game-status-info {
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 100px;
  }

  .game-status-text {
    font-family: 'Impact', sans-serif;
    font-size: 0.9rem;
    font-weight: bold;
    color: #e2e8f0;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
    letter-spacing: 1px;
  }

  .game-status-indicator {
    font-family: 'Courier New', monospace;
    font-size: 0.8rem;
    font-weight: bold;
    color: #94a3b8;
    padding: 4px 8px;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid #374151;
    border-radius: 4px;
    text-shadow: 0 0 4px currentColor;
  }

  .game-status-indicator.active {
    color: #22c55e;
    border-color: rgba(34, 197, 94, 0.5);
    box-shadow: 0 0 8px rgba(34, 197, 94, 0.3);
  }

  /* 랭킹 버튼 (새 위치) */
  .ranking-button {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    background: linear-gradient(145deg, rgba(34, 197, 94, 0.15), rgba(22, 163, 74, 0.25));
    border: 2px solid rgba(34, 197, 94, 0.4);
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 
      0 3px 6px rgba(0, 0, 0, 0.2),
      inset 0 1px 2px rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(3px);
  }

  .ranking-button:hover {
    background: linear-gradient(145deg, rgba(34, 197, 94, 0.25), rgba(22, 163, 74, 0.35));
    border-color: rgba(34, 197, 94, 0.6);
    transform: translateY(-2px);
    box-shadow: 
      0 5px 10px rgba(0, 0, 0, 0.3),
      inset 0 1px 2px rgba(255, 255, 255, 0.3),
      0 0 15px rgba(34, 197, 94, 0.3);
  }

  .ranking-button:active {
    transform: translateY(0);
    box-shadow: 
      0 2px 4px rgba(0, 0, 0, 0.3),
      inset 0 1px 2px rgba(0, 0, 0, 0.1);
  }

  .ranking-icon {
    font-size: 1.4rem;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5));
    animation: trophy-glow 3s ease-in-out infinite;
  }

  @keyframes trophy-glow {
    0%, 100% {
      filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5));
    }
    50% {
      filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5)) drop-shadow(0 0 8px rgba(255, 215, 0, 0.6));
    }
  }

  .ranking-text {
    font-family: 'Impact', sans-serif;
    font-size: 1rem;
    font-weight: 900;
    color: #e2e8f0;
    text-shadow: 
      0 1px 0 #4b5563,
      0 2px 4px rgba(0, 0, 0, 0.5);
    letter-spacing: 1px;
  }

  .power-indicator {
    position: absolute;
    top: 10px;
    right: 20px;
    width: 12px;
    height: 12px;
    background: radial-gradient(circle, #22c55e, #16a34a);
    border-radius: 50%;
    box-shadow: 
      0 0 8px #22c55e,
      inset 0 1px 2px rgba(255,255,255,0.4);
    animation: power-pulse 3s infinite;
  }

  /* 상단 장식 패널 */
  .top-panel {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 25px;
    background: linear-gradient(180deg, #374151 0%, #1f2937 100%);
    border-bottom: 3px solid #111827;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
  }

  .speaker-grille {
    width: 120px;
    height: 70px;
    background: linear-gradient(145deg, #1f2937, #111827);
    border-radius: 8px;
    border: 2px solid #374151;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 
      inset 0 2px 4px rgba(0,0,0,0.4),
      0 2px 4px rgba(0,0,0,0.2);
  }

  .speaker-holes {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 4px;
  }

  .speaker-hole {
    width: 8px;
    height: 8px;
    background: #000;
    border-radius: 50%;
    box-shadow: 
      inset 0 1px 2px rgba(0,0,0,0.8),
      0 0 4px rgba(59,130,246,0.3);
    animation: speaker-pulse 4s infinite;
  }

  .center-logo {
    flex: 1;
    text-align: center;
    padding: 0 20px;
  }

  .logo-text {
    font-family: 'Impact', sans-serif;
    font-size: 2.2rem;
    font-weight: 900;
    color: #e2e8f0;
    text-shadow: 
      0 0 10px #3b82f6,
      0 0 20px #1d4ed8,
      0 2px 4px rgba(0,0,0,0.5);
    letter-spacing: 4px;
    margin-bottom: 5px;
  }

  .logo-subtext {
    font-size: 0.875rem;
    color: #94a3b8;
    font-weight: bold;
    letter-spacing: 2px;
  }

  /* 메인 바디 */
  .arcade-body {
    flex: 1;
    background: linear-gradient(180deg, #374151 0%, #1f2937 50%, #111827 100%);
    border-left: 4px solid #0f172a;
    border-right: 4px solid #0f172a;
    display: flex;
    flex-direction: column;
    padding: 15px;
    box-shadow: 
      inset 0 4px 8px rgba(0,0,0,0.3),
      inset 4px 0 8px rgba(0,0,0,0.2),
      inset -4px 0 8px rgba(0,0,0,0.2);
  }

  /* 모니터 영역 */
  .monitor-container {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 15px;
  }

  .monitor-bezel {
    width: 100%;
    height: 100%;
    max-width: 95%;
    max-height: 95%;
    background: linear-gradient(145deg, #64748b, #334155);
    border-radius: 20px;
    padding: 20px;
    box-shadow: 
      inset 0 0 30px rgba(0,0,0,0.5),
      0 0 40px rgba(0,0,0,0.3),
      inset 0 4px 8px rgba(255,255,255,0.1),
      inset 0 -4px 8px rgba(0,0,0,0.3);
    border: 6px solid #1e293b;
    position: relative;
  }

  .monitor-bezel::before {
    content: '';
    position: absolute;
    top: 10px;
    left: 10px;
    right: 10px;
    bottom: 10px;
    border: 2px solid #475569;
    border-radius: 15px;
    pointer-events: none;
  }

  .screen-area {
    width: 100%;
    height: 100%;
    background: #000;
    border-radius: 15px;
    position: relative;
    overflow: hidden;
    box-shadow: 
      inset 0 0 30px rgba(0,0,0,0.8),
      inset 0 0 60px rgba(0,100,0,0.1);
    border: 3px solid #0f172a;
  }

  /* 모니터 화면 내 랭킹 버튼 */
  .monitor-ranking-button {
    position: absolute;
    top: 15px;
    right: 15px;
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    background: linear-gradient(145deg, rgba(34, 197, 94, 0.2), rgba(22, 163, 74, 0.3));
    border: 2px solid rgba(34, 197, 94, 0.5);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 
      0 2px 8px rgba(0, 0, 0, 0.3),
      inset 0 1px 2px rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(5px);
    z-index: 10;
  }

  .monitor-ranking-button:hover {
    background: linear-gradient(145deg, rgba(34, 197, 94, 0.3), rgba(22, 163, 74, 0.4));
    border-color: rgba(34, 197, 94, 0.7);
    transform: translateY(-2px);
    box-shadow: 
      0 4px 12px rgba(0, 0, 0, 0.4),
      inset 0 1px 2px rgba(255, 255, 255, 0.3),
      0 0 15px rgba(34, 197, 94, 0.4);
  }

  .monitor-ranking-button:active {
    transform: translateY(0);
    box-shadow: 
      0 1px 4px rgba(0, 0, 0, 0.4),
      inset 0 1px 2px rgba(0, 0, 0, 0.1);
  }

  .monitor-ranking-button .ranking-icon {
    font-size: 1.2rem;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.7));
    animation: trophy-glow 3s ease-in-out infinite;
  }

  .monitor-ranking-button .ranking-text {
    font-family: 'Impact', sans-serif;
    font-size: 0.9rem;
    font-weight: 900;
    color: #e2e8f0;
    text-shadow: 
      0 1px 0 #1f2937,
      0 2px 4px rgba(0, 0, 0, 0.7);
    letter-spacing: 1px;
  }

  /* 메뉴 화면 */
  .menu-screen {
    width: 100%;
    height: 100%;
    background: linear-gradient(180deg, #001100 0%, #000800 100%);
    position: relative;
    display: flex;
    flex-direction: column;
    padding: 10px;
  }

  .menu-header {
    text-align: center;
  }

  .arcade-menu-title {
    font-size: clamp(2rem, 4vw, 3.5rem);
    font-weight: 900;
    color: #22c55e;
    margin-bottom: 10px;
    font-family: 'Impact', sans-serif;
  }

  .menu-subtitle {
    font-size: clamp(1rem, 2vw, 1.5rem);
    color: #4ade80;
    font-weight: bold;
  }

  /* CD 선택 영역 */
  .cd-selection-area {
    flex: 1;
    display: flex;
    align-items: center;
    position: relative;
    margin: 20px 0;
  }

  .scroll-button {
    width: 60px;
    height: 60px;
    background: linear-gradient(145deg, #374151, #1f2937);
    border: 3px solid #22c55e;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease;
    z-index: 10;
    box-shadow: 
      0 4px 8px rgba(0,0,0,0.3),
      inset 0 2px 4px rgba(255,255,255,0.1);
  }

  .scroll-button:hover {
    background: linear-gradient(145deg, #4b5563, #374151);
    border-color: #4ade80;
    transform: scale(1.1);
  }

  .scroll-button:active {
    transform: scale(0.95);
  }

  .scroll-button.left {
    margin-right: 15px;
  }

  .scroll-button.right {
    margin-left: 15px;
  }

  .scroll-arrow {
    font-size: 1.5rem;
    color: #22c55e;
    font-weight: bold;
  }

  .cd-container {
    flex: 1;
    display: flex;
    gap: 30px;
    overflow-x: auto;
    overflow-y: hidden;
    scroll-behavior: smooth;
    padding: 20px 10px;
    align-items: center;
    justify-content: flex-start;
  }

  .cd-container::-webkit-scrollbar {
    display: none;
  }

  .cd-case {
    display: flex;
    flex-direction: column;
    align-items: center;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    min-width: 180px;
  }

  .cd-case:hover {
    transform: translateY(-5px);
  }

  .cd-case:hover .cd-disc {
    transform: scale(1.1);
  }

  .cd-disc {
    width: 140px;
    height: 140px;
    border-radius: 50%;
    position: relative;
    background: conic-gradient(from 0deg, #1f2937, #374151, #4b5563, #374151, #1f2937);
    box-shadow: 
      0 8px 16px rgba(0,0,0,0.4),
      inset 0 2px 4px rgba(255,255,255,0.2);
    animation: cd-spin 10s linear infinite;
    margin-bottom: 20px;
    transition: transform 0.3s ease;
  }

  .cd-disc.from-green-400 {
    background: conic-gradient(from 0deg, #22c55e, #16a34a, #15803d, #16a34a, #22c55e);
  }

  .cd-disc.from-blue-400 {
    background: conic-gradient(from 0deg, #3b82f6, #2563eb, #1d4ed8, #2563eb, #3b82f6);
  }

  .cd-hole {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 20px;
    height: 20px;
    background: #000;
    border-radius: 50%;
    box-shadow: 
      inset 0 2px 4px rgba(0,0,0,0.8),
      0 0 8px rgba(0,0,0,0.5);
  }

  .cd-reflection {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 50%;
    background: linear-gradient(45deg, 
      transparent 30%, 
      rgba(255,255,255,0.3) 50%, 
      transparent 70%);
    pointer-events: none;
  }

  .cd-shine {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 50%;
    background: conic-gradient(from 0deg, 
      transparent, 
      rgba(255,255,255,0.2), 
      transparent);
    animation: cd-shine 3s linear infinite;
    pointer-events: none;
  }

  .game-icon {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 3rem;
    z-index: 5;
    text-shadow: 0 2px 4px rgba(0,0,0,0.8);
    animation: float 3s ease-in-out infinite;
  }

  .cd-lines {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 50%;
    background: repeating-conic-gradient(from 0deg, 
      transparent 0deg, 
      rgba(255,255,255,0.1) 0.5deg, 
      transparent 1deg);
    pointer-events: none;
  }

  .cd-label {
    text-align: center;
    max-width: 160px;
  }

  .game-title {
    font-size: 1.2rem;
    font-weight: bold;
    color: #22c55e;
    margin-bottom: 5px;
  }

  .game-desc {
    font-size: 0.9rem;
    color: #4ade80;
    line-height: 1.3;
  }

  .menu-footer {
    text-align: center;
    margin-bottom: 20px;
  }

  .instruction-text {
    font-size: clamp(0.9rem, 1.5vw, 1.2rem);
    color: #4ade80;
    font-weight: bold;
  }

  /* 게임 화면 */
  .game-screen {
    width: 100%;
    height: 100%;
    background: #000;
    position: relative;
    display: flex;
    flex-direction: column;
  }

  .game-content {
    width: 100%;
    height: 100%;
    overflow: hidden;
  }

  /* 게임 대기 화면 (모니터) */
  .game-waiting-screen {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(180deg, #001100 0%, #000800 100%);
    padding: clamp(5px, 1vh, 15px);
    box-sizing: border-box;
    overflow: hidden;
  }

  .game-preview {
    text-align: center;
    max-width: 90%;
    max-height: 95%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    overflow: hidden;
  }

  .game-preview-icon {
    font-size: clamp(2.5rem, 6vw, 6rem);
    margin-bottom: clamp(8px, 2vh, 20px);
    animation: float 3s ease-in-out infinite;
    flex-shrink: 0;
  }

  .game-preview-title {
    font-size: clamp(1rem, 2.5vw, 2.5rem);
    color: #22c55e;
    margin-bottom: clamp(5px, 1vh, 10px);
    font-weight: bold;
    line-height: 1.2;
    text-align: center;
  }

  .game-preview-desc {
    font-size: clamp(0.8rem, 1.5vw, 1.5rem);
    color: #4ade80;
    margin-bottom: clamp(10px, 2vh, 30px);
    line-height: 1.3;
    text-align: center;
  }

  .expansion-indicator {
    margin-top: clamp(10px, 2vh, 40px);
    flex-shrink: 0;
  }

  .expansion-dots {
    display: flex;
    justify-content: center;
    gap: clamp(4px, 0.8vw, 8px);
    margin-bottom: clamp(8px, 1.5vh, 15px);
  }

  .expansion-dots span {
    width: clamp(6px, 1vw, 8px);
    height: clamp(6px, 1vw, 8px);
    background: #22c55e;
    border-radius: 50%;
    animation: expansion-pulse 1.5s infinite;
  }

  .expansion-dots span:nth-child(2) {
    animation-delay: 0.3s;
  }

  .expansion-dots span:nth-child(3) {
    animation-delay: 0.6s;
  }

  .expansion-text {
    font-size: clamp(0.7rem, 1.2vw, 1.2rem);
    color: #4ade80;
    font-weight: bold;
    text-align: center;
    line-height: 1.2;
  }

  /* 확장 완료 대기 화면 (전체화면) */
  .game-expansion-waiting {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #000;
    animation: fade-in-scale 0.5s ease-out;
    padding: clamp(10px, 2vh, 20px);
    box-sizing: border-box;
  }

  .expansion-complete-indicator {
    text-align: center;
    animation: pulse-glow 2s ease-in-out infinite;
    max-width: 90%;
    max-height: 90%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }

  .game-start-icon {
    font-size: clamp(4rem, 12vw, 8rem);
    margin-bottom: clamp(15px, 3vh, 30px);
    animation: float 2s ease-in-out infinite, icon-pulse 1.5s ease-in-out infinite;
    flex-shrink: 0;
  }

  .game-start-title {
    font-size: clamp(1.5rem, 4vw, 3rem);
    color: #22c55e;
    margin-bottom: clamp(20px, 4vh, 40px);
    font-weight: bold;
    font-family: 'Impact', sans-serif;
    text-shadow: 
      0 0 10px #22c55e,
      0 0 20px #22c55e,
      0 0 30px #22c55e;
    animation: title-glow 2s ease-in-out infinite;
    line-height: 1.1;
    text-align: center;
  }

  .start-countdown {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: clamp(10px, 2vh, 20px);
    flex-shrink: 0;
  }

  .countdown-spinner {
    width: clamp(40px, 8vw, 60px);
    height: clamp(40px, 8vw, 60px);
    border: clamp(3px, 0.6vw, 4px) solid rgba(34, 197, 94, 0.3);
    border-top: clamp(3px, 0.6vw, 4px) solid #22c55e;
    border-radius: 50%;
    animation: spin 1s linear infinite, spinner-pulse 2s ease-in-out infinite;
  }

  .countdown-text {
    font-size: clamp(1rem, 2.5vw, 1.5rem);
    color: #4ade80;
    font-weight: bold;
    font-family: 'Courier New', monospace;
    text-shadow: 0 0 10px #4ade80;
    animation: text-blink 1s ease-in-out infinite;
    text-align: center;
    line-height: 1.2;
  }

  /* 대기 화면 애니메이션 */
  @keyframes expansion-pulse {
    0%, 100% {
      opacity: 0.3;
      transform: scale(1);
    }
    50% {
      opacity: 1;
      transform: scale(1.2);
    }
  }

  /* 로딩 오버레이 */
  .monitor-loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.85);
    backdrop-filter: blur(8px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    border-radius: 15px;
  }

  .loading-content {
    text-align: center;
  }

  .loading-spinner {
    width: 80px;
    height: 80px;
    margin: 0 auto 20px;
    position: relative;
  }

  .spinner-ring {
    width: 100%;
    height: 100%;
    border: 4px solid rgba(34, 197, 94, 0.3);
    border-top: 4px solid #22c55e;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  .loading-text {
    font-size: 1.5rem;
    color: #22c55e;
    font-weight: bold;
    animation: pulse 2s infinite;
  }

  /* 스캔라인 효과 */
  .scanlines {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      transparent 50%,
      rgba(0, 255, 0, 0.03) 51%,
      transparent 52%
    );
    background-size: 100% 4px;
    animation: scanlines 0.1s linear infinite;
    pointer-events: none;
    z-index: 100;
  }

  /* CRT 텍스트 효과 */
  .crt-text {
    text-shadow: 
      0 0 5px currentColor,
      0 0 10px currentColor,
      0 0 15px currentColor;
    font-family: 'Courier New', monospace;
  }

  /* 컨트롤 패널 */
  .control-panel {
    height: clamp(120px, 15vh, 160px);
    background: linear-gradient(145deg, #64748b, #374151);
    border-radius: 15px;
    border: 4px solid #1e293b;
    position: relative;
    overflow: hidden;
    box-shadow: 
      inset 0 4px 8px rgba(255,255,255,0.1),
      inset 0 -4px 8px rgba(0,0,0,0.3),
      0 4px 8px rgba(0,0,0,0.2);
  }

  .control-panel::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 40%;
    background: linear-gradient(180deg, rgba(255,255,255,0.15) 0%, transparent 100%);
    border-radius: 15px 15px 0 0;
  }

  .control-panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: clamp(6px, 1.2vh, 12px) clamp(15px, 3vw, 25px);
    background: linear-gradient(90deg, #1f2937, #374151, #1f2937);
    border-bottom: 2px solid #111827;
    height: clamp(35px, 5vh, 50px);
  }

  .player-indicator {
    display: flex;
    align-items: center;
    gap: clamp(6px, 1vw, 10px);
  }

  .player-text {
    font-size: clamp(0.7rem, 1.1vw, 0.875rem);
    font-weight: bold;
    color: #94a3b8;
    font-family: 'Arial', sans-serif;
  }

  .player-led {
    width: clamp(8px, 1.2vw, 12px);
    height: clamp(8px, 1.2vw, 12px);
    border-radius: 50%;
    background: #374151;
    border: 2px solid #1f2937;
    box-shadow: inset 0 1px 2px rgba(0,0,0,0.3);
  }

  .player-led.active {
    background: radial-gradient(circle, #22c55e, #16a34a);
    box-shadow: 
      0 0 8px #22c55e,
      inset 0 1px 2px rgba(255,255,255,0.3);
    animation: led-pulse 2s infinite;
  }

  .control-center {
    flex: 1;
    text-align: center;
    min-width: 0;
  }

  .credits-display {
    padding: clamp(3px, 0.6vh, 6px) clamp(8px, 1.8vw, 12px);
    background: #000;
    border: 2px solid #374151;
    border-radius: 4px;
    display: inline-block;
    max-width: 100%;
  }

  .credits-text {
    font-family: 'Courier New', monospace;
    color: #22c55e;
    font-weight: bold;
    font-size: clamp(0.7rem, 1.1vw, 0.875rem);
    text-shadow: 0 0 4px #22c55e;
    white-space: nowrap;
  }

  .main-controls {
    display: flex;
    align-items: center;
    justify-content: space-around;
    padding: clamp(8px, 1.5vh, 15px) clamp(15px, 3vw, 25px);
    height: calc(100% - clamp(35px, 5vh, 50px));
    gap: clamp(10px, 2vw, 20px);
    flex-wrap: nowrap;
  }

  /* 조이스틱 */
  .joystick-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    min-width: clamp(50px, 7vw, 80px);
  }

  .joystick {
    position: relative;
    width: clamp(40px, 6vw, 70px);
    height: clamp(40px, 6vw, 70px);
  }

  .joystick-base {
    width: 100%;
    height: 100%;
    background: radial-gradient(circle at 30% 30%, #374151, #1f2937);
    border-radius: 50%;
    border: clamp(2px, 0.4vw, 3px) solid #111827;
    position: absolute;
    box-shadow: 
      inset 0 4px 8px rgba(0,0,0,0.4),
      0 4px 8px rgba(0,0,0,0.3);
  }

  .joystick-base::before {
    content: '';
    position: absolute;
    top: 18%;
    left: 18%;
    right: 18%;
    bottom: 18%;
    border: clamp(1px, 0.2vw, 2px) solid #4b5563;
    border-radius: 50%;
    background: radial-gradient(circle at 30% 30%, #4b5563, #374151);
  }

  .joystick-stick {
    width: clamp(15px, 3vw, 25px);
    height: clamp(15px, 3vw, 25px);
    background: linear-gradient(145deg, #dc2626, #991b1b);
    border-radius: 50%;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    border: clamp(2px, 0.3vw, 3px) solid #7f1d1d;
    box-shadow: 
      0 4px 8px rgba(0,0,0,0.4),
      inset 0 2px 4px rgba(255,255,255,0.2);
    cursor: pointer;
    transition: all 0.1s ease;
  }

  .joystick-stick:hover {
    transform: translate(-50%, -50%) scale(1.05);
  }

  .joystick-stick:active {
    transform: translate(-50%, -50%) scale(0.95);
  }

  /* 액션 버튼 */
  .button-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    min-width: clamp(70px, 10vw, 120px);
  }

  .buttons-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: clamp(8px, 1.5vw, 15px);
  }

  .action-button {
    width: clamp(30px, 4.5vw, 55px);
    height: clamp(30px, 4.5vw, 55px);
    border-radius: 50%;
    border: clamp(2px, 0.3vw, 3px) solid #1a202c;
    cursor: pointer;
    transition: all 0.1s ease;
    box-shadow: 
      0 6px 12px rgba(0,0,0,0.4),
      inset 0 2px 4px rgba(255,255,255,0.2);
    position: relative;
    font-weight: bold;
    font-size: clamp(0.7rem, 1.2vw, 1rem);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .action-button::before {
    content: attr(data-label);
    position: absolute;
    font-family: 'Arial', sans-serif;
    text-shadow: 0 1px 2px rgba(0,0,0,0.8);
  }

  .action-button:hover {
    transform: translateY(-2px);
    box-shadow: 
      0 8px 16px rgba(0,0,0,0.3),
      inset 0 2px 4px rgba(255,255,255,0.3);
  }

  .action-button:active {
    transform: translateY(2px);
    box-shadow: 
      0 2px 4px rgba(0,0,0,0.4),
      inset 0 2px 4px rgba(0,0,0,0.2);
  }

  .action-button.red {
    background: linear-gradient(145deg, #ef4444, #dc2626);
  }

  .action-button.blue {
    background: linear-gradient(145deg, #3b82f6, #2563eb);
  }

  /* 시스템 버튼 */
  .system-buttons {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: clamp(6px, 1.2vh, 12px);
    flex-shrink: 0;
    min-width: clamp(60px, 8vw, 100px);
  }

  .coin-slot {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: clamp(4px, 0.8vh, 8px);
    width: 100%;
  }

  .coin-opening {
    width: clamp(20px, 3vw, 35px);
    height: clamp(4px, 0.8vh, 7px);
    background: #000;
    border-radius: clamp(2px, 0.4vw, 4px);
    border: clamp(1px, 0.2vw, 2px) solid #374151;
    box-shadow: 
      inset 0 2px 4px rgba(0,0,0,0.8),
      0 0 8px rgba(255,215,0,0.3);
  }

  .coin-label {
    font-size: clamp(0.5rem, 0.8vw, 0.625rem);
    color: #94a3b8;
    font-weight: bold;
    letter-spacing: 1px;
    text-align: center;
    line-height: 1.2;
  }

  /* 하단부 */
  .arcade-bottom {
    height: 8%;
    background: linear-gradient(180deg, #1f2937 0%, #111827 50%, #0f172a 100%);
    border-radius: 0 0 20px 20px;
    border: 4px solid #0f172a;
    border-top: none;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 30px;
    box-shadow: 
      inset 0 4px 8px rgba(0,0,0,0.4),
      0 -2px 4px rgba(0,0,0,0.2);
  }

  .bottom-grille {
    display: flex;
    gap: 3px;
    flex: 1;
  }

  .grille-line {
    width: 2px;
    height: 60%;
    background: linear-gradient(180deg, #374151, #1f2937);
    border-radius: 1px;
    opacity: 0.7;
  }

  .brand-logo {
    font-family: 'Arial', sans-serif;
    font-size: 0.875rem;
    font-weight: bold;
    color: #64748b;
    letter-spacing: 2px;
  }

  /* 애니메이션 */
  @keyframes marquee-blink {
    0%, 100% { opacity: 1; box-shadow: 0 0 10px #fbbf24; }
    50% { opacity: 0.7; box-shadow: 0 0 5px #fbbf24; }
  }

  @keyframes power-pulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 8px #22c55e; }
    50% { opacity: 0.8; box-shadow: 0 0 12px #22c55e; }
  }

  @keyframes speaker-pulse {
    0%, 100% { box-shadow: inset 0 1px 2px rgba(0,0,0,0.8), 0 0 4px rgba(59,130,246,0.3); }
    50% { box-shadow: inset 0 1px 2px rgba(0,0,0,0.8), 0 0 8px rgba(59,130,246,0.6); }
  }

  @keyframes led-pulse {
    0%, 100% { box-shadow: 0 0 8px #22c55e, inset 0 1px 2px rgba(255,255,255,0.3); }
    50% { box-shadow: 0 0 16px #22c55e, inset 0 1px 2px rgba(255,255,255,0.3); }
  }

  @keyframes scanlines {
    0% { transform: translateY(0); }
    100% { transform: translateY(4px); }
  }

  @keyframes cd-spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  @keyframes cd-shine {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  @keyframes float {
    0%, 100% { transform: translate(-50%, -50%) translateY(0px); }
    50% { transform: translate(-50%, -50%) translateY(-8px); }
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }

  /* 반응형 디자인 */
  
  /* 매우 큰 화면 (1400px 이상) */
  @media (min-width: 1400px) {
    .arcade-machine {
      width: 90vw;
      max-width: 1600px;
    }
    
    .control-panel {
      height: clamp(140px, 18vh, 180px);
    }
  }

  /* 큰 화면 (1024px - 1399px) */
  @media (max-width: 1399px) and (min-width: 1024px) {
    .arcade-machine {
      width: 92vw;
      max-width: 1300px;
    }
  }

  /* 중간 화면 (768px - 1023px) */
  @media (max-width: 1023px) and (min-width: 768px) {
    .arcade-machine {
      width: 95vw;
      height: 95vh;
      margin: 2.5vh 0;
    }
    
    .arcade-title {
      font-size: 1.8rem;
      letter-spacing: 2px;
    }

    .ranking-button {
      padding: 7px 11px;
      margin-left: 12px;
      gap: 5px;
    }

    .ranking-icon {
      font-size: 1.1rem;
    }

    .ranking-text {
      font-size: 0.85rem;
      letter-spacing: 0.8px;
    }
    
    .logo-text {
      font-size: 2rem;
      letter-spacing: 3px;
    }
    
    .top-panel {
      padding: 10px 20px;
    }
    
    .speaker-grille {
      width: 100px;
      height: 60px;
    }
    
    .cd-disc {
      width: 120px;
      height: 120px;
    }
    
    .game-icon {
      font-size: 2.5rem;
    }
  }

  /* 작은 화면 (480px - 767px) */
  @media (max-width: 767px) and (min-width: 480px) {
    .arcade-machine {
      width: 98vw;
      height: 98vh;
      margin: 1vh 0;
    }
    
    .arcade-title {
      font-size: 1.5rem;
      letter-spacing: 1px;
    }
    
    .game-controls-header {
      padding: 8px 15px;
      margin-bottom: 10px;
    }

    .game-status-text {
      font-size: 0.75rem;
    }

    .ranking-button {
      padding: 6px 10px;
      gap: 4px;
    }

    .ranking-icon {
      font-size: 1rem;
    }

    .ranking-text {
      font-size: 0.8rem;
      letter-spacing: 0.5px;
    }
    
    .logo-text {
      font-size: 1.8rem;
      letter-spacing: 2px;
    }
  }

  /* 매우 작은 화면 (479px 이하) */
  @media (max-width: 479px) {
    .arcade-machine {
      width: 100vw;
      height: 100vh;
      max-width: none;
      max-height: none;
      margin: 0;
    }
    
    .arcade-title {
      font-size: 1.2rem;
      letter-spacing: 0.5px;
    }

    .game-controls-header {
      padding: 6px 12px;
      margin-bottom: 8px;
    }

    .game-status-text {
      font-size: 0.7rem;
    }

    .game-status-indicator {
      padding: 2px 6px;
      font-size: 0.7rem;
    }

    .ranking-button {
      padding: 4px 8px;
      gap: 3px;
    }

    .ranking-icon {
      font-size: 0.9rem;
    }

    .ranking-text {
      display: none;
    }
    
    .logo-text {
      font-size: 1.5rem;
      letter-spacing: 1px;
    }
    
    .top-panel {
      padding: 5px 10px;
    }
    
    .speaker-grille {
      display: none;
    }
    
    .cd-disc {
      width: 80px;
      height: 80px;
    }
    
    .game-icon {
      font-size: 1.5rem;
    }
    
    .cd-container {
      gap: 20px;
      padding: 15px 5px;
    }
    
    .cd-case {
      min-width: 100px;
    }
    
    .scroll-button {
      width: 40px;
      height: 40px;
    }
    
    .scroll-arrow {
      font-size: 1rem;
    }
    
    .game-title {
      font-size: 1rem;
    }
    
    .game-desc {
      font-size: 0.8rem;
    }

    /* 게임 대기 화면 - 매우 작은 화면 최적화 */
    .game-waiting-screen {
      padding: clamp(3px, 0.5vh, 8px);
    }

    .game-preview {
      max-width: 95%;
      max-height: 98%;
    }

    .game-preview-icon {
      font-size: clamp(2rem, 8vw, 3rem);
      margin-bottom: clamp(4px, 1vh, 8px);
    }

    .game-preview-title {
      font-size: clamp(0.9rem, 3.5vw, 1.2rem);
      margin-bottom: clamp(3px, 0.5vh, 6px);
      line-height: 1.1;
    }

    .game-preview-desc {
      font-size: clamp(0.7rem, 2.5vw, 0.9rem);
      margin-bottom: clamp(6px, 1vh, 12px);
      line-height: 1.2;
    }

    .expansion-indicator {
      margin-top: clamp(5px, 1vh, 15px);
    }

    .expansion-dots {
      gap: clamp(3px, 0.5vw, 5px);
      margin-bottom: clamp(4px, 0.8vh, 8px);
    }

    .expansion-dots span {
      width: clamp(4px, 0.8vw, 6px);
      height: clamp(4px, 0.8vw, 6px);
    }

    .expansion-text {
      font-size: clamp(0.6rem, 2vw, 0.8rem);
      line-height: 1.1;
    }

    /* 확장 대기 화면 - 매우 작은 화면 */
    .game-expansion-waiting {
      padding: clamp(5px, 1vh, 10px);
    }

    .expansion-complete-indicator {
      max-width: 95%;
      max-height: 95%;
    }

    .game-start-icon {
      font-size: clamp(3rem, 15vw, 5rem);
      margin-bottom: clamp(8px, 2vh, 15px);
    }

    .game-start-title {
      font-size: clamp(1.2rem, 6vw, 2rem);
      margin-bottom: clamp(10px, 2vh, 20px);
      line-height: 1;
    }

    .start-countdown {
      gap: clamp(5px, 1vh, 10px);
    }

    .countdown-spinner {
      width: clamp(30px, 10vw, 40px);
      height: clamp(30px, 10vw, 40px);
      border: clamp(2px, 0.4vw, 3px) solid rgba(34, 197, 94, 0.3);
      border-top: clamp(2px, 0.4vw, 3px) solid #22c55e;
    }

    .countdown-text {
      font-size: clamp(0.8rem, 3vw, 1rem);
    }
  }

  /* 세로 모드 추가 최적화 */
  @media (orientation: portrait) and (max-width: 768px) {
    .arcade-machine {
      height: 100vh;
    }
    
    .monitor-bezel {
      max-height: 90%;
    }

    /* 게임 대기 화면 - 세로 모드 최적화 */
    .game-waiting-screen {
      padding: clamp(2px, 0.3vh, 6px);
    }

    .game-preview {
      max-height: 96%;
    }

    .game-preview-icon {
      font-size: clamp(2rem, 6vw, 4rem);
      margin-bottom: clamp(5px, 1vh, 10px);
    }

    .game-preview-title {
      font-size: clamp(0.9rem, 2.8vw, 1.5rem);
      margin-bottom: clamp(3px, 0.6vh, 8px);
    }

    .game-preview-desc {
      font-size: clamp(0.7rem, 2.2vw, 1rem);
      margin-bottom: clamp(5px, 1.2vh, 15px);
    }

    .expansion-indicator {
      margin-top: clamp(5px, 1.2vh, 20px);
    }

    .expansion-text {
      font-size: clamp(0.6rem, 1.8vw, 0.9rem);
    }

    /* 확장 대기 화면 - 세로 모드 */
    .game-start-icon {
      font-size: clamp(3rem, 10vw, 6rem);
      margin-bottom: clamp(10px, 2vh, 20px);
    }

    .game-start-title {
      font-size: clamp(1.2rem, 4.5vw, 2.5rem);
      margin-bottom: clamp(15px, 3vh, 30px);
    }

    .countdown-text {
      font-size: clamp(0.9rem, 2.8vw, 1.2rem);
    }
  }

  /* 가로 모드이지만 높이가 작은 경우 */
  @media (orientation: landscape) and (max-height: 600px) {
    .arcade-machine {
      height: 100vh;
      margin: 0;
    }
    
    .arcade-top {
      height: 5%;
    }
    
    .arcade-bottom {
      height: 6%;
    }
    
    .top-panel {
      padding: 5px 15px;
    }
    
    .control-panel {
      height: clamp(80px, 10vh, 100px);
    }

    /* 게임 대기 화면 - 낮은 높이 최적화 */
    .game-waiting-screen {
      padding: clamp(2px, 0.5vh, 5px);
    }

    .game-preview {
      max-height: 98%;
    }

    .game-preview-icon {
      font-size: clamp(1.8rem, 4vh, 3rem);
      margin-bottom: clamp(3px, 0.8vh, 8px);
    }

    .game-preview-title {
      font-size: clamp(0.8rem, 2vh, 1.5rem);
      margin-bottom: clamp(2px, 0.5vh, 5px);
    }

    .game-preview-desc {
      font-size: clamp(0.6rem, 1.5vh, 1rem);
      margin-bottom: clamp(3px, 0.8vh, 10px);
    }

    .expansion-indicator {
      margin-top: clamp(3px, 1vh, 15px);
    }

    .expansion-dots {
      margin-bottom: clamp(3px, 0.8vh, 8px);
    }

    .expansion-text {
      font-size: clamp(0.5rem, 1.2vh, 0.8rem);
    }

    /* 확장 대기 화면 - 낮은 높이 */
    .game-start-icon {
      font-size: clamp(2.5rem, 8vh, 5rem);
      margin-bottom: clamp(5px, 1.5vh, 15px);
    }

    .game-start-title {
      font-size: clamp(1rem, 3vh, 2rem);
      margin-bottom: clamp(8px, 2vh, 20px);
    }

    .countdown-spinner {
      width: clamp(25px, 5vh, 40px);
      height: clamp(25px, 5vh, 40px);
    }

    .countdown-text {
      font-size: clamp(0.7rem, 1.8vh, 1rem);
    }
  }

  /* 매우 넓은 화면 (울트라와이드) */
  @media (min-aspect-ratio: 21/9) {
    .arcade-machine {
      width: 80vw;
      max-width: 1400px;
    }
  }

  /* 사용자 정의 스크롤바 */
  :global(::-webkit-scrollbar) {
    width: 8px;
  }
  
  :global(::-webkit-scrollbar-track) {
    background: rgba(0, 0, 0, 0.3);
    border-radius: 10px;
  }
  
  :global(::-webkit-scrollbar-thumb) {
    background: linear-gradient(45deg, #22c55e, #16a34a);
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  :global(::-webkit-scrollbar-thumb:hover) {
    background: linear-gradient(45deg, #4ade80, #22c55e);
  }

  /* 게임 확장 시스템 */
  .game-expansion-container {
    position: relative;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  }

  .game-expansion-container.expanded {
    transform: scale(1);
  }

  .arcade-machine {
    width: 95vw;
    max-width: 1400px;
    height: 98vh;
    max-height: 1100px;
    display: flex;
    flex-direction: column;
    filter: drop-shadow(0 20px 40px rgba(0,0,0,0.6));
    margin: 1vh 0;
    transition: all 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    position: relative;
    z-index: 1;
  }

  .arcade-machine.game-playing {
    opacity: 0;
    transform: scale(0.8);
    pointer-events: none;
  }

  /* 확장된 게임 화면 */
  .expanded-game-screen {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: #000;
    z-index: 10;
    opacity: 0;
    animation: game-expand-in 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
    display: flex;
    flex-direction: column;
  }

  .expanded-game-content {
    flex: 1;
    width: 100%;
    height: 100vh;
    overflow: hidden;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .expanded-game-content > :global(*) {
    width: 100%;
    height: 100%;
    max-width: 100%;
    max-height: 100vh;
  }

  /* 매우 작은 화면에서는 사이드바 완전 숨김 */
  @media (max-width: 640px) {
    .expanded-game-content {
      width: 100vw;
      margin-left: 0;
    }
    
    .expanded-game-content > :global(*) {
      max-width: 100vw;
    }
  }

  /* 게임 종료 오버레이 */
  .game-exit-overlay {
    position: absolute;
    top: 20px;
    right: 20px;
    z-index: 100;
    opacity: 0;
    animation: exit-button-fade-in 1s ease-out 0.5s forwards;
  }

  .exit-button {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 12px 16px;
    background: linear-gradient(145deg, rgba(239, 68, 68, 0.15), rgba(185, 28, 28, 0.15));
    border: 2px solid rgba(220, 38, 38, 0.3);
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 
      0 4px 12px rgba(0, 0, 0, 0.2),
      inset 0 2px 4px rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(5px);
    min-width: 80px;
  }

  .exit-button:hover {
    background: linear-gradient(145deg, rgba(248, 113, 113, 0.25), rgba(239, 68, 68, 0.25));
    border-color: rgba(248, 113, 113, 0.4);
    transform: translateY(-2px);
    box-shadow: 
      0 6px 16px rgba(0, 0, 0, 0.25),
      inset 0 2px 4px rgba(255, 255, 255, 0.15);
  }

  .exit-button:active {
    transform: translateY(0);
    box-shadow: 
      0 2px 8px rgba(0, 0, 0, 0.3),
      inset 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .exit-text {
    font-family: 'Courier New', monospace;
    font-size: 1.2rem;
    font-weight: bold;
    color: rgba(255, 255, 255, 0.9);
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
    margin-bottom: 2px;
  }

  .exit-label {
    font-family: 'Arial', sans-serif;
    font-size: 0.7rem;
    font-weight: bold;
    color: rgba(252, 165, 165, 0.8);
    text-transform: uppercase;
    letter-spacing: 1px;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
  }

  /* 게임 확장 애니메이션 */
  @keyframes game-expand-in {
    0% {
      opacity: 0;
      transform: scale(0.1);
      border-radius: 20px;
    }
    50% {
      opacity: 0.8;
      transform: scale(0.7);
      border-radius: 10px;
    }
    100% {
      opacity: 1;
      transform: scale(1);
      border-radius: 0;
    }
  }

  @keyframes exit-button-fade-in {
    0% {
      opacity: 0;
      transform: translateX(50px);
    }
    100% {
      opacity: 1;
      transform: translateX(0);
    }
  }

  /* 게임 축소 애니메이션 (JavaScript로 제어) */
  .expanded-game-screen.closing {
    animation: game-expand-out 0.8s cubic-bezier(0.55, 0.06, 0.68, 0.19) forwards;
  }

  @keyframes game-expand-out {
    0% {
      opacity: 1;
      transform: scale(1);
      border-radius: 0;
    }
    50% {
      opacity: 0.8;
      transform: scale(0.7);
      border-radius: 10px;
    }
    100% {
      opacity: 0;
      transform: scale(0.1);
      border-radius: 20px;
    }
  }

  /* 반응형 조정 - 게임 확장 모드 */
  @media (max-width: 768px) {
    .game-exit-overlay {
      top: 10px;
      right: 10px;
    }
    
    .exit-button {
      padding: 8px 12px;
      min-width: 60px;
      background: linear-gradient(145deg, rgba(239, 68, 68, 0.12), rgba(185, 28, 28, 0.12));
      border: 2px solid rgba(220, 38, 38, 0.25);
    }
    
    .exit-button:hover {
      background: linear-gradient(145deg, rgba(248, 113, 113, 0.2), rgba(239, 68, 68, 0.2));
      border-color: rgba(248, 113, 113, 0.35);
    }
    
    .exit-text {
      font-size: 1rem;
      color: rgba(255, 255, 255, 0.85);
    }
    
    .exit-label {
      font-size: 0.6rem;
      color: rgba(252, 165, 165, 0.75);
    }
  }

  @media (max-width: 480px) {
    .exit-button {
      padding: 6px 10px;
      min-width: 50px;
      background: linear-gradient(145deg, rgba(239, 68, 68, 0.1), rgba(185, 28, 28, 0.1));
      border: 2px solid rgba(220, 38, 38, 0.2);
    }
    
    .exit-button:hover {
      background: linear-gradient(145deg, rgba(248, 113, 113, 0.18), rgba(239, 68, 68, 0.18));
      border-color: rgba(248, 113, 113, 0.3);
    }
    
    .exit-text {
      font-size: 0.9rem;
      color: rgba(255, 255, 255, 0.8);
    }
    
    .exit-label {
      font-size: 0.5rem;
      color: rgba(252, 165, 165, 0.7);
    }
  }

  /* 게임 확장 중 아케이드 머신 숨김 효과 개선 */
  .arcade-machine.game-playing .arcade-top,
  .arcade-machine.game-playing .arcade-body,
  .arcade-machine.game-playing .arcade-bottom {
    transition: all 0.6s ease-out;
  }

  .arcade-machine.game-playing {
    transition: all 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  }

  /* 개선된 애니메이션들 */
  @keyframes fade-in-scale {
    0% {
      opacity: 0;
      transform: scale(0.9);
    }
    100% {
      opacity: 1;
      transform: scale(1);
    }
  }

  @keyframes pulse-glow {
    0%, 100% {
      filter: brightness(1);
    }
    50% {
      filter: brightness(1.1);
    }
  }

  @keyframes icon-pulse {
    0%, 100% {
      transform: translate(-50%, -50%) scale(1);
    }
    50% {
      transform: translate(-50%, -50%) scale(1.05);
    }
  }

  @keyframes title-glow {
    0%, 100% {
      text-shadow: 
        0 0 10px #22c55e,
        0 0 20px #22c55e,
        0 0 30px #22c55e;
    }
    50% {
      text-shadow: 
        0 0 15px #22c55e,
        0 0 25px #22c55e,
        0 0 35px #22c55e,
        0 0 45px #22c55e;
    }
  }

  @keyframes spinner-pulse {
    0%, 100% {
      box-shadow: 0 0 0 rgba(34, 197, 94, 0.4);
    }
    50% {
      box-shadow: 0 0 20px rgba(34, 197, 94, 0.6);
    }
  }

  @keyframes text-blink {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.7;
    }
  }

  /* 모니터 랭킹 버튼 반응형 */
  .monitor-ranking-button {
    top: 12px;
    right: 12px;
    padding: 6px 10px;
    gap: 4px;
  }

  .monitor-ranking-button .ranking-icon {
    font-size: 1rem;
  }

  .monitor-ranking-button .ranking-text {
    font-size: 0.8rem;
  }
  
  .top-panel {
    padding: 8px 15px;
  }

  /* 모니터 랭킹 버튼 - 매우 작은 화면 */
  .monitor-ranking-button {
    top: 8px;
    right: 8px;
    padding: 4px 6px;
    gap: 0;
  }

  .monitor-ranking-button .ranking-icon {
    font-size: 0.9rem;
  }

  .monitor-ranking-button .ranking-text {
    display: none;
  }

  /* 게임 대기 화면 - 매우 작은 화면 최적화 */
  .arcade-title {
    font-size: 1.8rem;
    letter-spacing: 2px;
  }
  
  /* 모니터 랭킹 버튼 반응형 - 중간 화면 */
  .monitor-ranking-button {
    top: 14px;
    right: 14px;
    padding: 7px 11px;
    gap: 5px;
  }

  .monitor-ranking-button .ranking-icon {
    font-size: 1.1rem;
  }

  .monitor-ranking-button .ranking-text {
    font-size: 0.85rem;
  }
  
  .logo-text {
    font-size: 2rem;
    letter-spacing: 3px;
  }
</style>

