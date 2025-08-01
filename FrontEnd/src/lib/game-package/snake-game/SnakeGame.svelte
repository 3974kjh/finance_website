<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Phaser from 'phaser';

  let gameContainer: HTMLDivElement;
  let game: Phaser.Game | null = null;

  // 게임 설정 (동적으로 조정될 예정)
  let GAME_WIDTH = 800;
  let GAME_HEIGHT = 600;
  const GRID_SIZE = 20;

  class SnakeScene extends Phaser.Scene {
    private snake: Phaser.Geom.Point[] = [];
    private food: Phaser.Geom.Point = new Phaser.Geom.Point();
    private direction: Phaser.Geom.Point = new Phaser.Geom.Point();
    private newDirection: Phaser.Geom.Point = new Phaser.Geom.Point();
    private directionQueue: Phaser.Geom.Point[] = []; // 방향 큐 시스템
    private addNew: boolean = false;
    private score: number = 0;
    private gameOver: boolean = false;
    private scoreText: Phaser.GameObjects.Text | null = null;
    private gameOverText: Phaser.GameObjects.Text | null = null;
    private gameOverTexts: Phaser.GameObjects.Text[] = []; // 게임 오버 텍스트들 추적
    private speedText: Phaser.GameObjects.Text | null = null; // 속도 표시
    private graphics: Phaser.GameObjects.Graphics | null = null;
    private cursors: Phaser.Types.Input.Keyboard.CursorKeys | null = null;
    private wasd: any = null;
    private moveTimer: number = 0;
    private baseMoveDelay: number = 150; // 기본 이동 속도
    private currentMoveDelay: number = 150; // 현재 이동 속도
    private spacePressed: boolean = false; // 스페이스바 상태 추적
    private lastKeyPressed: string = ''; // 마지막 눌린 키 추적
    private keyPressTime: number = 0; // 키 눌린 시간 추적

    constructor() {
      super({ key: 'SnakeScene' });
    }

    preload() {
      // 단색 텍스처 생성
      this.load.image('background', 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==');
    }

    create() {
      // 배경 설정
      this.add.rectangle(GAME_WIDTH / 2, GAME_HEIGHT / 2, GAME_WIDTH, GAME_HEIGHT, 0x1a1a2e);
      
      // 그리드 라인 그리기
      this.graphics = this.add.graphics();
      this.drawGrid();

      // 게임 초기화
      this.resetGame();

      // 키보드 입력 설정
      this.cursors = this.input.keyboard?.createCursorKeys() || null;
      
      // WASD 키 설정
      if (this.input.keyboard) {
        this.wasd = this.input.keyboard.addKeys('W,S,A,D');
      }

      // 스코어 텍스트
      this.scoreText = this.add.text(20, 20, 'Score: 0', {
        fontSize: Math.max(16, Math.min(24, GAME_WIDTH / 40)) + 'px',
        color: '#00ff00',
        fontFamily: 'monospace'
      });

      // 속도 텍스트 추가
      this.speedText = this.add.text(20, 50, 'Speed: 1x', {
        fontSize: Math.max(14, Math.min(20, GAME_WIDTH / 45)) + 'px',
        color: '#ffff00',
        fontFamily: 'monospace'
      });

      // 첫 렌더링
      this.render();
    }

    update(time: number) {
      // 키보드 입력은 매 프레임마다 처리 (즉시 반응)
      this.handleInput(time);
      
      if (this.gameOver) {
        // 게임 오버 상태에서도 스페이스바 재시작 처리
        this.handleGameOverInput();
        return;
      }
      
      // 타이머 기반 이동 (일정 시간마다만 이동)
      if (time > this.moveTimer + this.currentMoveDelay) {
        this.moveSnake();
        this.checkCollisions();
        this.render();
        this.moveTimer = time;
      }
    }

    private drawGrid() {
      if (!this.graphics) return;

      this.graphics.clear();
      this.graphics.lineStyle(1, 0x0e4b99, 0.3);

      // 세로 선
      for (let x = 0; x <= GAME_WIDTH; x += GRID_SIZE) {
        this.graphics.moveTo(x, 0);
        this.graphics.lineTo(x, GAME_HEIGHT);
      }

      // 가로 선
      for (let y = 0; y <= GAME_HEIGHT; y += GRID_SIZE) {
        this.graphics.moveTo(0, y);
        this.graphics.lineTo(GAME_WIDTH, y);
      }

      this.graphics.strokePath();
    }

    private resetGame() {
      // 뱀 초기화 (중앙에서 시작)
      this.snake = [];
      const startX = Math.floor(GAME_WIDTH / 2 / GRID_SIZE);
      const startY = Math.floor(GAME_HEIGHT / 2 / GRID_SIZE);
      
      for (let i = 0; i < 3; i++) {
        this.snake.push(new Phaser.Geom.Point(startX - i, startY));
      }

      // 방향 초기화 (오른쪽으로)
      this.direction = new Phaser.Geom.Point(1, 0);
      this.newDirection = new Phaser.Geom.Point(1, 0);
      this.directionQueue = []; // 방향 큐 초기화

      // 게임 상태 초기화
      this.addNew = false;
      this.score = 0;
      this.gameOver = false;
      this.moveTimer = 0;
      this.spacePressed = false; // 게임 재시작 시 스페이스바 상태 초기화
      this.lastKeyPressed = '';
      this.keyPressTime = 0;

      // 속도 초기화
      this.currentMoveDelay = this.baseMoveDelay;
      this.updateSpeedDisplay();

      // 음식 생성
      this.generateFood();
      
      // 스코어 업데이트
      if (this.scoreText) {
        this.scoreText.setText('Score: 0');
      }

      console.log('Snake game initialized:', {
        snakeLength: this.snake.length,
        direction: this.direction,
        food: this.food
      });
    }

    private generateFood() {
      let foodX: number, foodY: number;
      const gridWidth = Math.floor(GAME_WIDTH / GRID_SIZE);
      const gridHeight = Math.floor(GAME_HEIGHT / GRID_SIZE);

      do {
        foodX = Phaser.Math.Between(0, gridWidth - 1);
        foodY = Phaser.Math.Between(0, gridHeight - 1);
      } while (this.isSnakePosition(foodX, foodY));

      this.food.setTo(foodX, foodY);
    }

    private isSnakePosition(x: number, y: number): boolean {
      return this.snake.some(segment => segment.x === x && segment.y === y);
    }

    private handleInput(time: number) {
      if (!this.cursors && !this.wasd) return;

      // 방향 큐 시스템으로 빠른 입력 처리
      let newDir: Phaser.Geom.Point | null = null;
      let keyPressed = '';

      if ((this.cursors?.left?.isDown || this.wasd?.A?.isDown) && this.direction.x !== 1) {
        newDir = new Phaser.Geom.Point(-1, 0);
        keyPressed = 'left';
      } else if ((this.cursors?.right?.isDown || this.wasd?.D?.isDown) && this.direction.x !== -1) {
        newDir = new Phaser.Geom.Point(1, 0);
        keyPressed = 'right';
      } else if ((this.cursors?.up?.isDown || this.wasd?.W?.isDown) && this.direction.y !== 1) {
        newDir = new Phaser.Geom.Point(0, -1);
        keyPressed = 'up';
      } else if ((this.cursors?.down?.isDown || this.wasd?.S?.isDown) && this.direction.y !== -1) {
        newDir = new Phaser.Geom.Point(0, 1);
        keyPressed = 'down';
      }

      // 새로운 방향이 감지되고, 마지막 키와 다르거나 일정 시간이 지났을 때
      if (newDir && (keyPressed !== this.lastKeyPressed || time > this.keyPressTime + 50)) {
        // 큐가 비어있거나, 큐의 마지막 방향과 다를 때만 추가
        if (this.directionQueue.length === 0 || 
            !this.isSameDirection(this.directionQueue[this.directionQueue.length - 1], newDir)) {
          
          // 큐 크기 제한 (최대 2개까지만 저장)
          if (this.directionQueue.length >= 2) {
            this.directionQueue.shift();
          }
          
          this.directionQueue.push(newDir);
          this.lastKeyPressed = keyPressed;
          this.keyPressTime = time;
        }
      }
    }

    private isSameDirection(dir1: Phaser.Geom.Point, dir2: Phaser.Geom.Point): boolean {
      return dir1.x === dir2.x && dir1.y === dir2.y;
    }

    private handleGameOverInput() {
      if (!this.cursors) return;
      
      // 스페이스바로 재시작 (JustDown 사용으로 한 번만 처리)
      if (this.cursors.space?.isDown && !this.spacePressed) {
        this.restart();
        this.spacePressed = true; // 스페이스바 상태를 true로 변경
      } else if (!this.cursors.space?.isDown) {
        this.spacePressed = false; // 스페이스바가 떼지면 상태를 false로 변경
      }
    }

    private moveSnake() {
      // 큐에서 다음 방향 가져오기
      if (this.directionQueue.length > 0) {
        const nextDirection = this.directionQueue.shift()!;
        // 반대 방향이 아닌 경우에만 적용
        if (!this.isOppositeDirection(nextDirection)) {
          this.direction.setTo(nextDirection.x, nextDirection.y);
        }
      }

      // 머리 위치 계산
      const head = this.snake[0];
      const newHead = new Phaser.Geom.Point(
        head.x + this.direction.x,
        head.y + this.direction.y
      );

      // 새 머리를 뱀의 앞에 추가
      this.snake.unshift(newHead);

      // 음식을 먹었는지 확인
      if (newHead.x === this.food.x && newHead.y === this.food.y) {
        this.score += 10;
        this.scoreText?.setText(`Score: ${this.score}`);
        this.generateFood();
        this.addNew = true;
        
        // 뱀 길이에 따른 속도 증가
        this.updateSpeed();
      }

      // 새로운 세그먼트가 추가되지 않았다면 꼬리 제거
      if (!this.addNew) {
        this.snake.pop();
      } else {
        this.addNew = false;
      }
    }

    private checkCollisions() {
      const head = this.snake[0];

      // 벽 충돌 검사
      const gridWidth = Math.floor(GAME_WIDTH / GRID_SIZE);
      const gridHeight = Math.floor(GAME_HEIGHT / GRID_SIZE);

      if (head.x < 0 || head.x >= gridWidth || head.y < 0 || head.y >= gridHeight) {
        console.log('Wall collision detected!');
        this.endGame('벽에 부딪혔습니다!');
        return;
      }

      // 자기 몸과 충돌 검사 (뱀의 길이가 4 이상일 때만 가능)
      if (this.snake.length >= 4) {
        for (let i = 1; i < this.snake.length; i++) {
          if (head.x === this.snake[i].x && head.y === this.snake[i].y) {
            console.log('Self collision detected at segment', i);
            this.endGame('자기 몸에 부딪혔습니다!');
            return;
          }
        }
      }
    }

    private render() {
      if (!this.graphics) return;

      // 이전 그래픽 지우기
      this.graphics.clear();
      
      // 그리드 다시 그리기
      this.drawGrid();

      // 뱀 그리기 (개선된 그래픽스)
      this.snake.forEach((segment, index) => {
        const x = segment.x * GRID_SIZE;
        const y = segment.y * GRID_SIZE;

        if (index === 0) {
          // 머리 - 그라데이션과 더 나은 디자인
          this.graphics!.fillStyle(0x00ff00);
          this.graphics!.fillRoundedRect(x + 1, y + 1, GRID_SIZE - 2, GRID_SIZE - 2, 3);
          
          // 머리 하이라이트
          this.graphics!.fillStyle(0x44ff44);
          this.graphics!.fillRoundedRect(x + 2, y + 2, GRID_SIZE - 4, GRID_SIZE - 4, 2);
          
          // 눈 그리기
          this.graphics!.fillStyle(0x000000);
          const eyeSize = 3;
          const eyeOffset = 5;
          
          if (this.direction.x === 1) { // 오른쪽
            this.graphics!.fillRect(x + GRID_SIZE - eyeOffset, y + 4, eyeSize, eyeSize);
            this.graphics!.fillRect(x + GRID_SIZE - eyeOffset, y + GRID_SIZE - 7, eyeSize, eyeSize);
          } else if (this.direction.x === -1) { // 왼쪽
            this.graphics!.fillRect(x + 2, y + 4, eyeSize, eyeSize);
            this.graphics!.fillRect(x + 2, y + GRID_SIZE - 7, eyeSize, eyeSize);
          } else if (this.direction.y === -1) { // 위
            this.graphics!.fillRect(x + 4, y + 2, eyeSize, eyeSize);
            this.graphics!.fillRect(x + GRID_SIZE - 7, y + 2, eyeSize, eyeSize);
          } else if (this.direction.y === 1) { // 아래
            this.graphics!.fillRect(x + 4, y + GRID_SIZE - eyeOffset, eyeSize, eyeSize);
            this.graphics!.fillRect(x + GRID_SIZE - 7, y + GRID_SIZE - eyeOffset, eyeSize, eyeSize);
          }
        } else {
          // 몸 - 더 어두운 초록색과 그라데이션
          this.graphics!.fillStyle(0x00cc00);
          this.graphics!.fillRoundedRect(x + 1, y + 1, GRID_SIZE - 2, GRID_SIZE - 2, 2);
          
          // 몸통 하이라이트
          this.graphics!.fillStyle(0x22dd22);
          this.graphics!.fillRoundedRect(x + 3, y + 3, GRID_SIZE - 6, GRID_SIZE - 6, 1);
        }
      });

      // 음식 그리기 (개선된 디자인)
      const foodX = this.food.x * GRID_SIZE;
      const foodY = this.food.y * GRID_SIZE;
      
      // 음식 외곽 (어두운 빨강)
      this.graphics.fillStyle(0xcc0000);
      this.graphics.fillRoundedRect(foodX + 1, foodY + 1, GRID_SIZE - 2, GRID_SIZE - 2, 4);
      
      // 음식 메인 (밝은 빨강)
      this.graphics.fillStyle(0xff3333);
      this.graphics.fillRoundedRect(foodX + 3, foodY + 3, GRID_SIZE - 6, GRID_SIZE - 6, 3);
      
      // 음식 하이라이트
      this.graphics.fillStyle(0xff6666);
      this.graphics.fillRoundedRect(foodX + 5, foodY + 5, GRID_SIZE - 10, GRID_SIZE - 10, 2);
      
      // 음식 반짝임 효과
      this.graphics.fillStyle(0xffffff);
      this.graphics.fillRect(foodX + 6, foodY + 6, 2, 2);
    }

    private endGame(reason: string = '게임 오버') {
      this.gameOver = true;
      console.log('Game Over:', reason);

      // 기존 게임 오버 텍스트들 초기화
      this.gameOverTexts = [];

      // 게임 오버 텍스트
      this.gameOverText = this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2 - 60, 'GAME OVER', {
        fontSize: Math.max(32, Math.min(48, GAME_WIDTH / 20)) + 'px',
        color: '#ff0000',
        fontFamily: 'monospace'
      }).setOrigin(0.5);
      this.gameOverTexts.push(this.gameOverText);

      const reasonText = this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2 - 10, reason, {
        fontSize: Math.max(14, Math.min(20, GAME_WIDTH / 40)) + 'px',
        color: '#ffaa00',
        fontFamily: 'monospace'
      }).setOrigin(0.5);
      this.gameOverTexts.push(reasonText);

      const scoreText = this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2 + 30, `최종 점수: ${this.score}`, {
        fontSize: Math.max(16, Math.min(24, GAME_WIDTH / 35)) + 'px',
        color: '#ffffff',
        fontFamily: 'monospace'
      }).setOrigin(0.5);
      this.gameOverTexts.push(scoreText);

      const lengthText = this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2 + 70, `뱀 길이: ${this.snake.length}`, {
        fontSize: Math.max(12, Math.min(18, GAME_WIDTH / 45)) + 'px',
        color: '#00ff00',
        fontFamily: 'monospace'
      }).setOrigin(0.5);
      this.gameOverTexts.push(lengthText);

      const restartText = this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2 + 110, 'SPACE를 눌러 재시작', {
        fontSize: Math.max(12, Math.min(16, GAME_WIDTH / 50)) + 'px',
        color: '#00ff00',
        fontFamily: 'monospace'
      }).setOrigin(0.5);
      this.gameOverTexts.push(restartText);
    }

    private restart() {
      console.log('Restarting game...');
      
      // 게임 오버 텍스트들을 배열에서 추적하여 제거
      this.gameOverTexts.forEach(text => {
        if (text && text.active) {
          text.destroy();
        }
      });
      this.gameOverTexts = [];

      // gameOverText 참조 초기화
      this.gameOverText = null;

      // 게임 상태 재설정
      this.resetGame();

      // 첫 렌더링
      this.render();
    }

    private isOppositeDirection(newDir: Phaser.Geom.Point): boolean {
      return (this.direction.x === -newDir.x && this.direction.y === -newDir.y);
    }

    private updateSpeed() {
      // 뱀 길이에 따른 속도 조절 (길수록 빨라짐)
      const speedMultiplier = Math.max(0.5, 1 - (this.snake.length - 3) * 0.05);
      this.currentMoveDelay = Math.max(80, Math.floor(this.baseMoveDelay * speedMultiplier));
      this.updateSpeedDisplay();
    }

    private updateSpeedDisplay() {
      const speedLevel = ((this.baseMoveDelay / this.currentMoveDelay)).toFixed(1);
      this.speedText?.setText(`Speed: ${speedLevel}x`);
    }
  }

  // 컨테이너 크기에 맞춰 게임 크기 조정
  function adjustGameSize() {
    if (gameContainer) {
      const containerRect = gameContainer.getBoundingClientRect();
      GAME_WIDTH = Math.floor(containerRect.width);
      GAME_HEIGHT = Math.floor(containerRect.height);
      
      // 최소 크기 보장
      GAME_WIDTH = Math.max(400, GAME_WIDTH);
      GAME_HEIGHT = Math.max(300, GAME_HEIGHT);
      
      // 그리드에 맞춰 조정
      GAME_WIDTH = Math.floor(GAME_WIDTH / GRID_SIZE) * GRID_SIZE;
      GAME_HEIGHT = Math.floor(GAME_HEIGHT / GRID_SIZE) * GRID_SIZE;
    }
  }

  onMount(() => {
    // 게임 크기 조정
    adjustGameSize();

    const config: Phaser.Types.Core.GameConfig = {
      type: Phaser.AUTO,
      width: GAME_WIDTH,
      height: GAME_HEIGHT,
      parent: gameContainer,
      backgroundColor: '#1a1a2e',
      scene: SnakeScene,
      physics: {
        default: 'arcade'
      },
      scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH
      }
    };

    game = new Phaser.Game(config);

    return () => {
      if (game) {
        game.destroy(true);
        game = null;
      }
    };
  });

  onDestroy(() => {
    if (game) {
      game.destroy(true);
      game = null;
    }
  });
</script>

<div bind:this={gameContainer} class="w-full h-full bg-black" />