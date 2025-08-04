<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Phaser from 'phaser';

  let gameContainer: HTMLDivElement;
  let game: Phaser.Game | null = null;

  // 게임 설정 (동적으로 조정될 예정)
  let GAME_WIDTH = 800;
  let GAME_HEIGHT = 600;
  const GRID_SIZE = 20;

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
      
      // 게임이 실행 중이라면 크기 조정
      if (game) {
        game.scale.resize(GAME_WIDTH, GAME_HEIGHT);
        
        // 씬이 존재한다면 씬의 크기도 업데이트
        const scene = game.scene.getScene('SnakeScene') as SnakeScene;
        if (scene && scene.scene.isActive()) {
          scene.updateGameSize(GAME_WIDTH, GAME_HEIGHT);
        }
      }
    }
  }

  // 리사이즈 핸들러
  const handleResize = () => {
    adjustGameSize();
  };

  class SnakeScene extends Phaser.Scene {
    private snake: Phaser.Geom.Point[] = [];
    private foods: Phaser.Geom.Point[] = []; // 음식 배열로 변경 (5개)
    private powerUpItem: Phaser.Geom.Point | null = null; // 무적 아이템
    private poisonApple: Phaser.Geom.Point | null = null; // 독사과 아이템
    private direction: Phaser.Geom.Point = new Phaser.Geom.Point();
    private newDirection: Phaser.Geom.Point = new Phaser.Geom.Point();
    private directionQueue: Phaser.Geom.Point[] = []; // 방향 큐 시스템
    private addNew: number = 0; // boolean에서 number로 변경하여 여러 세그먼트 추가 지원
    private score: number = 0;
    private gameOver: boolean = false;
    private scoreText: Phaser.GameObjects.Text | null = null;
    private gameOverText: Phaser.GameObjects.Text | null = null;
    private gameOverTexts: Phaser.GameObjects.Text[] = []; // 게임 오버 텍스트들 추적
    private speedText: Phaser.GameObjects.Text | null = null; // 속도 표시
    private powerUpText: Phaser.GameObjects.Text | null = null; // 무적 모드 표시
    private itemDescriptionUI: Phaser.GameObjects.Text | null = null; // 아이템 설명 UI
    private graphics: Phaser.GameObjects.Graphics | null = null;
    private cursors: Phaser.Types.Input.Keyboard.CursorKeys | null = null;
    private wasd: any = null;
    private moveTimer: number = 0;
    private baseMoveDelay: number = 150; // 기본 이동 속도
    private currentMoveDelay: number = 150; // 현재 이동 속도
    private spacePressed: boolean = false; // 스페이스바 상태 추적
    private lastKeyPressed: string = ''; // 마지막 눌린 키 추적
    private keyPressTime: number = 0; // 키 눌린 시간 추적
    
    // 무적 모드 관련 변수
    private isInvincible: boolean = false;
    private invincibleTimeLeft: number = 0;
    private invincibleStartTime: number = 0;
    private normalSpeed: number = 150; // 무적 모드 전 속도 저장
    private blinkTimer: number = 0; // 번쩍이는 효과
    private powerUpSpawnTimer: number = 0; // 무적 아이템 생성 타이머
    private powerUpItemSpawnTime: number = 0; // 아이템 생성 시간 추적
    
    // 독사과 관련 변수
    private poisonAppleSpawnTimer: number = 0; // 독사과 생성 타이머
    private poisonAppleSpawnTime: number = 0; // 독사과 생성 시간 추적
    private nextPoisonAppleSpawn: number = 0; // 다음 독사과 생성 시간

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

      // 키보드 입력 설정 (강화된 버전)
      if (this.input && this.input.keyboard) {
        this.cursors = this.input.keyboard.createCursorKeys();
        
        // WASD 키 설정
        this.wasd = this.input.keyboard.addKeys('W,S,A,D');
        
        // 키보드 캡처 활성화
        this.input.keyboard.enableGlobalCapture();
        
        console.log('Keyboard input initialized successfully');
      } else {
        console.error('Keyboard input initialization failed');
      }

      // 스코어 텍스트
      this.scoreText = this.add.text(20, 20, 'Score: 0', {
        fontSize: Math.max(16, Math.min(24, GAME_WIDTH / 40)) + 'px',
        color: '#00ff00',
        fontFamily: 'Courier New, monospace',
        stroke: '#003300',
        strokeThickness: 2,
        shadow: {
          offsetX: 2,
          offsetY: 2,
          color: '#000000',
          blur: 4,
          stroke: true,
          fill: true
        }
      });

      // 속도 텍스트 추가
      this.speedText = this.add.text(20, 50, 'Speed: 1x', {
        fontSize: Math.max(14, Math.min(20, GAME_WIDTH / 45)) + 'px',
        color: '#ffff00',
        fontFamily: 'Courier New, monospace',
        stroke: '#333300',
        strokeThickness: 2,
        shadow: {
          offsetX: 2,
          offsetY: 2,
          color: '#000000',
          blur: 4,
          stroke: true,
          fill: true
        }
      });

      // 무적 모드 텍스트 추가
      this.powerUpText = this.add.text(20, 80, '', {
        fontSize: Math.max(16, Math.min(22, GAME_WIDTH / 40)) + 'px',
        color: '#ffffff',
        fontFamily: 'Courier New, monospace',
        stroke: '#666666',
        strokeThickness: 3,
        shadow: {
          offsetX: 3,
          offsetY: 3,
          color: '#000000',
          blur: 6,
          stroke: true,
          fill: true
        }
      });

      // 아이템 설명 UI 추가 (하단)
      this.itemDescriptionUI = this.add.text(GAME_WIDTH / 2, GAME_HEIGHT - 30, '', {
        fontSize: Math.max(10, Math.min(14, GAME_WIDTH / 60)) + 'px',
        color: '#ffff00',
        fontFamily: 'Courier New, monospace',
        stroke: '#333300',
        strokeThickness: 1,
        shadow: {
          offsetX: 1,
          offsetY: 1,
          color: '#000000',
          blur: 3,
          stroke: true,
          fill: true
        },
        align: 'center'
      }).setOrigin(0.5);

      // 첫 렌더링
      this.render();
      
      console.log('Snake game created successfully');
    }

    update(time: number) {
      // 키보드 입력은 매 프레임마다 처리 (즉시 반응)
      this.handleInput(time);
      
      if (this.gameOver) {
        // 게임 오버 상태에서도 스페이스바 재시작 처리
        this.handleGameOverInput();
        return;
      }
      
      // 무적 모드 업데이트
      this.updateInvincibleMode(time);
      
      // 무적 아이템 생성 로직
      this.updatePowerUpSpawn(time);
      
      // 독사과 생성 로직
      this.updatePoisonAppleSpawn(time);
      
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
      this.addNew = 0;
      this.score = 0;
      this.gameOver = false;
      this.moveTimer = 0;
      this.spacePressed = false; // 게임 재시작 시 스페이스바 상태 초기화
      this.lastKeyPressed = '';
      this.keyPressTime = 0;

      // 속도 초기화
      this.currentMoveDelay = this.baseMoveDelay;
      this.updateSpeedDisplay();

      // 무적 모드 관련 초기화
      this.isInvincible = false;
      this.invincibleTimeLeft = 0;
      this.invincibleStartTime = 0;
      this.normalSpeed = 150;
      this.blinkTimer = 0;
      this.powerUpItem = null;
      this.powerUpItemSpawnTime = 0; // 아이템 생성 시간 초기화
      
      // 독사과 관련 초기화
      this.poisonApple = null;
      this.poisonAppleSpawnTimer = this.time?.now ? this.time.now - 3000 : Date.now() - 3000; // 첫 독사과는 2초 후에 스폰 가능
      this.poisonAppleSpawnTime = 0;
      this.nextPoisonAppleSpawn = 0;
      
      // 무적 아이템을 빠르게 테스트할 수 있도록 타이머 설정 (5초 후 첫 아이템)
      this.powerUpSpawnTimer = this.time?.now ? this.time.now - 25000 : Date.now() - 25000; // 30초 - 25초 = 5초 후
      this.powerUpText?.setText('');
      this.itemDescriptionUI?.setText('⏰ Invincible item spawns every 20s (auto-delete after 10s) | 🍎 5 foods available | ⚡ Invincible: +3 length | 💀 Poison apple: -3 length'); // 아이템 설명 UI 초기화

      // 음식 배열 초기화 후 5개 생성
      this.foods = [];
      this.generateFood();
      
      // 스코어 업데이트
      if (this.scoreText) {
        this.scoreText.setText('Score: 0');
      }

      console.log('Snake game reset:', {
        snakeLength: this.snake.length,
        direction: this.direction,
        food: this.foods,
        gameSize: `${GAME_WIDTH}x${GAME_HEIGHT}`,
        gridSize: `${Math.floor(GAME_WIDTH / GRID_SIZE)}x${Math.floor(GAME_HEIGHT / GRID_SIZE)}`
      });
    }

    private generateFood() {
      let foodX: number, foodY: number;
      const gridWidth = Math.floor(GAME_WIDTH / GRID_SIZE);
      const gridHeight = Math.floor(GAME_HEIGHT / GRID_SIZE);

      // 유효한 게임 영역 확인
      if (gridWidth <= 2 || gridHeight <= 2) {
        this.foods = []; // 게임 영역이 너무 작으면 음식 배열 초기화
        return;
      }

      // 5개의 음식 아이템 생성
      for (let i = 0; i < 5; i++) {
        let attempts = 0;
        const maxAttempts = 50;
        do {
          foodX = Phaser.Math.Between(1, gridWidth - 2); // 여백 확보
          foodY = Phaser.Math.Between(1, gridHeight - 2); // 여백 확보
          attempts++;
          if (attempts > maxAttempts) {
            console.log('Failed to generate food item after', maxAttempts, 'attempts');
            return;
          }
        } while (this.isSnakePosition(foodX, foodY));
        this.foods.push(new Phaser.Geom.Point(foodX, foodY));
      }
    }

    private addNewFood() {
      let foodX: number, foodY: number;
      const gridWidth = Math.floor(GAME_WIDTH / GRID_SIZE);
      const gridHeight = Math.floor(GAME_HEIGHT / GRID_SIZE);

      // 유효한 게임 영역 확인
      if (gridWidth <= 2 || gridHeight <= 2) {
        return;
      }

      let attempts = 0;
      const maxAttempts = 50;
      do {
        foodX = Phaser.Math.Between(1, gridWidth - 2);
        foodY = Phaser.Math.Between(1, gridHeight - 2);
        attempts++;
        if (attempts > maxAttempts) {
          console.log('Failed to generate new food after', maxAttempts, 'attempts');
          return;
        }
      } while (this.isSnakePosition(foodX, foodY));

      this.foods.push(new Phaser.Geom.Point(foodX, foodY));
    }

    private isSnakePosition(x: number, y: number): boolean {
      return this.snake.some(segment => segment.x === x && segment.y === y) ||
             this.foods.some(food => food.x === x && food.y === y) ||
             this.powerUpItem?.x === x && this.powerUpItem?.y === y ||
             this.poisonApple?.x === x && this.poisonApple?.y === y;
    }

    private handleInput(time: number) {
      if (!this.cursors && !this.wasd) {
        console.warn('No keyboard input available');
        return;
      }

      // 방향 큐 시스템으로 빠른 입력 처리
      let newDir: Phaser.Geom.Point | null = null;
      let keyPressed = '';

      // 키 상태 체크 및 디버깅
      const leftPressed = this.cursors?.left?.isDown || this.wasd?.A?.isDown;
      const rightPressed = this.cursors?.right?.isDown || this.wasd?.D?.isDown;
      const upPressed = this.cursors?.up?.isDown || this.wasd?.W?.isDown;
      const downPressed = this.cursors?.down?.isDown || this.wasd?.S?.isDown;

      if (leftPressed && this.direction.x !== 1) {
        newDir = new Phaser.Geom.Point(-1, 0);
        keyPressed = 'left';
        console.log('Left key pressed');
      } else if (rightPressed && this.direction.x !== -1) {
        newDir = new Phaser.Geom.Point(1, 0);
        keyPressed = 'right';
        console.log('Right key pressed');
      } else if (upPressed && this.direction.y !== 1) {
        newDir = new Phaser.Geom.Point(0, -1);
        keyPressed = 'up';
        console.log('Up key pressed');
      } else if (downPressed && this.direction.y !== -1) {
        newDir = new Phaser.Geom.Point(0, 1);
        keyPressed = 'down';
        console.log('Down key pressed');
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
          console.log('Direction added to queue:', keyPressed, 'Queue length:', this.directionQueue.length);
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
      const eatenFoodIndex = this.foods.findIndex(food => newHead.x === food.x && newHead.y === food.y);
      if (eatenFoodIndex !== -1) {
        const baseScore = 10;
        const scoreMultiplier = this.isInvincible ? 10 : 1; // 무적 모드시 10배 점수
        this.score += baseScore * scoreMultiplier;
        this.scoreText?.setText(`Score: ${this.score}`);
        
        // 먹은 음식 제거
        this.foods.splice(eatenFoodIndex, 1);
        
        // 새로운 음식 1개 추가
        this.addNewFood();
        
        // 무적 상태에서는 3만큼, 일반 상태에서는 1만큼 성장
        if (this.isInvincible) {
          this.addNew = 3; // 무적 상태에서 3 세그먼트 증가
        } else {
          this.addNew = 1; // 일반 상태에서 1 세그먼트 증가
        }
        
        // 뱀 길이에 따른 속도 증가 (무적 모드가 아닐 때만)
        if (!this.isInvincible) {
          this.updateSpeed();
        }
      }

      // 무적 아이템을 먹었는지 확인
      if (this.powerUpItem && newHead.x === this.powerUpItem.x && newHead.y === this.powerUpItem.y) {
        this.activateInvincibleMode();
        // 무적 아이템은 뱀 길이를 늘리지 않음
      }

      // 독사과를 먹었는지 확인
      if (this.poisonApple && newHead.x === this.poisonApple.x && newHead.y === this.poisonApple.y) {
        if (!this.isInvincible) {
          // 무적 상태가 아닐 때만 독사과 효과 적용
          this.poisonApple = null; // 독사과 제거
          
          // 뱀 길이 3 줄이기
          for (let i = 0; i < 3 && this.snake.length > 1; i++) {
            this.snake.pop();
          }
          
          // 길이가 3 미만이 되면 게임 오버
          if (this.snake.length < 3) {
            this.endGame('독사과를 먹어 뱀이 너무 짧아졌습니다!');
            return;
          }
          
          console.log('Poison apple eaten! Snake length reduced to:', this.snake.length);
        } else {
          // 무적 상태에서는 독사과 효과 없음
          this.poisonApple = null;
          console.log('Poison apple eaten but no effect due to invincibility!');
        }
      }

      // 새로운 세그먼트가 추가되지 않았다면 꼬리 제거
      if (this.addNew <= 0) {
        this.snake.pop();
      } else {
        this.addNew--; // 카운터 감소
      }
    }

    private checkCollisions() {
      // 무적 모드에서는 벽과 자기 몸 충돌 무시
      if (this.isInvincible) {
        return;
      }

      const head = this.snake[0];
      const gridWidth = Math.floor(GAME_WIDTH / GRID_SIZE);
      const gridHeight = Math.floor(GAME_HEIGHT / GRID_SIZE);

      // 벽 충돌 시 텔레포트 처리 (게임 오버 없음)
      let teleported = false;
      
      if (head.x < 0) {
        // 왼쪽 벽: 오른쪽 끝으로 텔레포트
        head.x = gridWidth - 1;
        teleported = true;
      } else if (head.x >= gridWidth) {
        // 오른쪽 벽: 왼쪽 끝으로 텔레포트
        head.x = 0;
        teleported = true;
      }
      
      if (head.y < 0) {
        // 위쪽 벽: 아래쪽 끝으로 텔레포트
        head.y = gridHeight - 1;
        teleported = true;
      } else if (head.y >= gridHeight) {
        // 아래쪽 벽: 위쪽 끝으로 텔레포트
        head.y = 0;
        teleported = true;
      }
      
      if (teleported) {
        console.log('Snake teleported to:', head.x, head.y);
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

      // 무적 아이템 먼저 그리기 (가장 뒤에 표시되도록)
      if (this.powerUpItem) {
        const powerUpX = this.powerUpItem.x * GRID_SIZE;
        const powerUpY = this.powerUpItem.y * GRID_SIZE;
        
        // 무적 아이템 (흰색, 번쩍이는 효과)
        const itemBlink = Math.sin(this.time.now * 0.01) * 0.3 + 0.7;
        const itemColor = Phaser.Display.Color.GetColor(255 * itemBlink, 255 * itemBlink, 255 * itemBlink);
        
        // 배경 글로우 효과 (더 눈에 띄게)
        this.graphics.lineStyle(4, itemColor, 0.6);
        this.graphics.strokeRect(powerUpX - 2, powerUpY - 2, GRID_SIZE + 4, GRID_SIZE + 4);
        
        this.graphics.fillStyle(itemColor);
        this.graphics.fillRoundedRect(powerUpX + 1, powerUpY + 1, GRID_SIZE - 2, GRID_SIZE - 2, 6);
        
        // 중앙에 십자가 표시 (무적 표시)
        this.graphics.fillStyle(0x000000);
        this.graphics.fillRect(powerUpX + GRID_SIZE/2 - 1, powerUpY + 4, 2, GRID_SIZE - 8);
        this.graphics.fillRect(powerUpX + 4, powerUpY + GRID_SIZE/2 - 1, GRID_SIZE - 8, 2);
        
        // 추가 외곽 글로우 효과
        this.graphics.lineStyle(2, itemColor, 0.8);
        this.graphics.strokeRect(powerUpX - 1, powerUpY - 1, GRID_SIZE + 2, GRID_SIZE + 2);
        
        console.log('Rendering power-up item at pixel position:', powerUpX, powerUpY);
      }

      // 독사과 그리기 (빨간색, 번쩍이는 효과)
      if (this.poisonApple) {
        const poisonAppleX = this.poisonApple.x * GRID_SIZE;
        const poisonAppleY = this.poisonApple.y * GRID_SIZE;

        const poisonBlink = Math.sin(this.time.now * 0.015) * 0.4 + 0.6; // 더 강한 번쩍임
        const poisonColor = Phaser.Display.Color.GetColor(255 * poisonBlink, 0, 0); // 빨간색 번쩍임
        const darkRed = Phaser.Display.Color.GetColor(150, 0, 0);

        // 외곽 위험 표시 (번쩍이는 테두리)
        this.graphics.lineStyle(4, poisonColor, 0.8);
        this.graphics.strokeRect(poisonAppleX - 3, poisonAppleY - 3, GRID_SIZE + 6, GRID_SIZE + 6);

        // 독사과 메인 바디 (어두운 빨강)
        this.graphics.fillStyle(darkRed);
        this.graphics.fillRoundedRect(poisonAppleX + 1, poisonAppleY + 1, GRID_SIZE - 2, GRID_SIZE - 2, 6);

        // 독사과 표면 (번쩍이는 빨강)
        this.graphics.fillStyle(poisonColor);
        this.graphics.fillRoundedRect(poisonAppleX + 2, poisonAppleY + 2, GRID_SIZE - 4, GRID_SIZE - 4, 4);

        // 해골 표시 (X 마크로 위험 표시)
        this.graphics.lineStyle(3, 0x000000, 1);
        const centerX = poisonAppleX + GRID_SIZE / 2;
        const centerY = poisonAppleY + GRID_SIZE / 2;
        const crossSize = GRID_SIZE / 3;
        
        // X 표시 (위험 기호)
        this.graphics.beginPath();
        this.graphics.moveTo(centerX - crossSize/2, centerY - crossSize/2);
        this.graphics.lineTo(centerX + crossSize/2, centerY + crossSize/2);
        this.graphics.moveTo(centerX + crossSize/2, centerY - crossSize/2);
        this.graphics.lineTo(centerX - crossSize/2, centerY + crossSize/2);
        this.graphics.strokePath();

        // 추가 위험 표시 (작은 점들)
        this.graphics.fillStyle(0x000000);
        this.graphics.fillCircle(centerX - 3, centerY - 6, 1);
        this.graphics.fillCircle(centerX + 3, centerY - 6, 1);
        this.graphics.fillCircle(centerX, centerY + 6, 1);

        // 독사과 주변 경고 효과
        this.graphics.lineStyle(2, poisonColor, 0.4 * poisonBlink);
        this.graphics.strokeRect(poisonAppleX - 1, poisonAppleY - 1, GRID_SIZE + 2, GRID_SIZE + 2);

        console.log('Rendering poison apple at pixel position:', poisonAppleX, poisonAppleY);
      }

      // 음식 그리기 (개선된 디자인)
      this.foods.forEach(food => {
        const foodX = food.x * GRID_SIZE;
        const foodY = food.y * GRID_SIZE;
        
        // 음식 외곽 (어두운 빨강)
        this.graphics!.fillStyle(0xcc0000);
        this.graphics!.fillRoundedRect(foodX + 1, foodY + 1, GRID_SIZE - 2, GRID_SIZE - 2, 4);
        
        // 음식 메인 (밝은 빨강)
        this.graphics!.fillStyle(0xff3333);
        this.graphics!.fillRoundedRect(foodX + 3, foodY + 3, GRID_SIZE - 6, GRID_SIZE - 6, 3);
        
        // 음식 하이라이트
        this.graphics!.fillStyle(0xff6666);
        this.graphics!.fillRoundedRect(foodX + 5, foodY + 5, GRID_SIZE - 10, GRID_SIZE - 10, 2);
        
        // 음식 반짝임 효과
        this.graphics!.fillStyle(0xffffff);
        this.graphics!.fillRect(foodX + 6, foodY + 6, 2, 2);
      });

      // 뱀 그리기 (개선된 그래픽스) - 가장 위에 표시
      this.snake.forEach((segment, index) => {
        const x = segment.x * GRID_SIZE;
        const y = segment.y * GRID_SIZE;

        if (index === 0) {
          // 머리 - 무적 모드시 번쩍이는 효과
          let headColor = 0x00ff00;
          let highlightColor = 0x44ff44;
          
          if (this.isInvincible) {
            // 번쩍이는 효과
            const blinkIntensity = Math.sin(this.blinkTimer * 10) * 0.5 + 0.5;
            headColor = blinkIntensity > 0.5 ? 0xffffff : 0x00ff00;
            highlightColor = blinkIntensity > 0.5 ? 0xffffaa : 0x44ff44;
          }
          
          this.graphics!.fillStyle(headColor);
          this.graphics!.fillRoundedRect(x + 1, y + 1, GRID_SIZE - 2, GRID_SIZE - 2, 3);
          
          // 머리 하이라이트
          this.graphics!.fillStyle(highlightColor);
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
        } else if (index === this.snake.length - 1) {
          // 꼬리 - 삼각형으로 표현
          let tailColor = 0x008800;
          
          if (this.isInvincible) {
            const blinkIntensity = Math.sin(this.blinkTimer * 10) * 0.5 + 0.5;
            tailColor = blinkIntensity > 0.5 ? 0xcccccc : 0x008800;
          }
          
          this.graphics!.fillStyle(tailColor);
          
          // 이전 세그먼트의 방향에 따라 꼬리 방향 결정
          const prevSegment = this.snake[index - 1];
          const tailDirection = {
            x: segment.x - prevSegment.x,
            y: segment.y - prevSegment.y
          };
          
          this.graphics!.beginPath();
          
          if (tailDirection.x === 1) { // 꼬리가 오른쪽을 향함
            this.graphics!.moveTo(x + GRID_SIZE - 2, y + GRID_SIZE / 2); // 오른쪽 끝점
            this.graphics!.lineTo(x + 2, y + 2); // 왼쪽 위
            this.graphics!.lineTo(x + 2, y + GRID_SIZE - 2); // 왼쪽 아래
          } else if (tailDirection.x === -1) { // 꼬리가 왼쪽을 향함
            this.graphics!.moveTo(x + 2, y + GRID_SIZE / 2); // 왼쪽 끝점
            this.graphics!.lineTo(x + GRID_SIZE - 2, y + 2); // 오른쪽 위
            this.graphics!.lineTo(x + GRID_SIZE - 2, y + GRID_SIZE - 2); // 오른쪽 아래
          } else if (tailDirection.y === 1) { // 꼬리가 아래를 향함
            this.graphics!.moveTo(x + GRID_SIZE / 2, y + GRID_SIZE - 2); // 아래 끝점
            this.graphics!.lineTo(x + 2, y + 2); // 왼쪽 위
            this.graphics!.lineTo(x + GRID_SIZE - 2, y + 2); // 오른쪽 위
          } else if (tailDirection.y === -1) { // 꼬리가 위를 향함
            this.graphics!.moveTo(x + GRID_SIZE / 2, y + 2); // 위 끝점
            this.graphics!.lineTo(x + 2, y + GRID_SIZE - 2); // 왼쪽 아래
            this.graphics!.lineTo(x + GRID_SIZE - 2, y + GRID_SIZE - 2); // 오른쪽 아래
          }
          
          this.graphics!.closePath();
          this.graphics!.fillPath();
        } else {
          // 몸 - 무적 모드시 번쩍이는 효과
          let bodyColor = 0x00cc00;
          let bodyHighlight = 0x22dd22;
          
          if (this.isInvincible) {
            const blinkIntensity = Math.sin(this.blinkTimer * 10) * 0.5 + 0.5;
            bodyColor = blinkIntensity > 0.5 ? 0xdddddd : 0x00cc00;
            bodyHighlight = blinkIntensity > 0.5 ? 0xffffff : 0x22dd22;
          }
          
          this.graphics!.fillStyle(bodyColor);
          this.graphics!.fillRoundedRect(x + 1, y + 1, GRID_SIZE - 2, GRID_SIZE - 2, 2);
          
          // 몸통 하이라이트
          this.graphics!.fillStyle(bodyHighlight);
          this.graphics!.fillRoundedRect(x + 3, y + 3, GRID_SIZE - 6, GRID_SIZE - 6, 1);
        }
      });
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
        fontFamily: 'Courier New, monospace',
        stroke: '#330000',
        strokeThickness: 4,
        shadow: {
          offsetX: 4,
          offsetY: 4,
          color: '#000000',
          blur: 8,
          stroke: true,
          fill: true
        }
      }).setOrigin(0.5);
      this.gameOverTexts.push(this.gameOverText);

      const reasonText = this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2 - 10, reason, {
        fontSize: Math.max(14, Math.min(20, GAME_WIDTH / 40)) + 'px',
        color: '#ffaa00',
        fontFamily: 'Courier New, monospace',
        stroke: '#333300',
        strokeThickness: 2,
        shadow: {
          offsetX: 2,
          offsetY: 2,
          color: '#000000',
          blur: 4,
          stroke: true,
          fill: true
        }
      }).setOrigin(0.5);
      this.gameOverTexts.push(reasonText);

      const scoreText = this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2 + 30, `최종 점수: ${this.score}`, {
        fontSize: Math.max(16, Math.min(24, GAME_WIDTH / 35)) + 'px',
        color: '#ffffff',
        fontFamily: 'Courier New, monospace',
        stroke: '#003300',
        strokeThickness: 2,
        shadow: {
          offsetX: 2,
          offsetY: 2,
          color: '#000000',
          blur: 4,
          stroke: true,
          fill: true
        }
      }).setOrigin(0.5);
      this.gameOverTexts.push(scoreText);

      const lengthText = this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2 + 70, `뱀 길이: ${this.snake.length}`, {
        fontSize: Math.max(12, Math.min(18, GAME_WIDTH / 45)) + 'px',
        color: '#00ff00',
        fontFamily: 'Courier New, monospace',
        stroke: '#003300',
        strokeThickness: 2,
        shadow: {
          offsetX: 2,
          offsetY: 2,
          color: '#000000',
          blur: 4,
          stroke: true,
          fill: true
        }
      }).setOrigin(0.5);
      this.gameOverTexts.push(lengthText);

      const restartText = this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2 + 110, 'SPACE를 눌러 재시작', {
        fontSize: Math.max(12, Math.min(16, GAME_WIDTH / 50)) + 'px',
        color: '#00ff00',
        fontFamily: 'Courier New, monospace',
        stroke: '#003300',
        strokeThickness: 2,
        shadow: {
          offsetX: 2,
          offsetY: 2,
          color: '#000000',
          blur: 4,
          stroke: true,
          fill: true
        }
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

      // 무적 모드 텍스트 초기화
      this.powerUpText?.setText('');
      this.itemDescriptionUI?.setText('⏰ Invincible item spawns every 20s (auto-delete after 10s) | 🍎 5 foods available | ⚡ Invincible: +3 length | 💀 Poison apple: -3 length'); // 아이템 설명 UI 초기화

      // 게임 상태 재설정
      this.resetGame();

      // 첫 렌더링
      this.render();
    }

    private isOppositeDirection(newDir: Phaser.Geom.Point): boolean {
      return (this.direction.x === -newDir.x && this.direction.y === -newDir.y);
    }

    private updateSpeed() {
      // 뱀 길이에 따른 속도 조절 (길수록 빨라짐) - 최대 3배까지
      const maxSpeedMultiplier = 3.0;
      const speedMultiplier = Math.min(maxSpeedMultiplier, 1 + (this.snake.length - 3) * 0.1);
      this.currentMoveDelay = Math.max(50, Math.floor(this.baseMoveDelay / speedMultiplier));
      this.updateSpeedDisplay();
    }

    private updateSpeedDisplay() {
      const speedLevel = ((this.baseMoveDelay / this.currentMoveDelay)).toFixed(1);
      const speedText = this.isInvincible ? `Speed: ${speedLevel}x (INVINCIBLE)` : `Speed: ${speedLevel}x`;
      this.speedText?.setText(speedText);
    }

    private updateInvincibleMode(time: number) {
      if (this.isInvincible) {
        this.invincibleTimeLeft = Math.max(0, 10000 - (time - this.invincibleStartTime));
        
        if (this.invincibleTimeLeft <= 0) {
          // 무적 모드 종료
          this.isInvincible = false;
          this.currentMoveDelay = this.normalSpeed;
          this.powerUpText?.setText('');
          this.updateSpeedDisplay();
        } else {
          // 무적 모드 타이머 표시
          const secondsLeft = Math.ceil(this.invincibleTimeLeft / 1000);
          this.powerUpText?.setText(`INVINCIBLE: ${secondsLeft}s`);
          this.powerUpText?.setColor('#ffffff');
          
          // 번쩍이는 효과
          this.blinkTimer += 0.1;
          if (this.blinkTimer > 1) this.blinkTimer = 0;
        }
      }
    }

    private updatePowerUpSpawn(time: number) {
      // 무적 아이템 생성 (20초마다, 아이템이 없을 때만)
      const spawnInterval = 20000; // 20초로 설정
      const timeSinceLastSpawn = time - this.powerUpSpawnTimer;
      
      if (!this.powerUpItem && timeSinceLastSpawn >= spawnInterval) {
        console.log('🎯 Attempting to spawn power-up item...');
        console.log('Time since last spawn:', Math.floor(timeSinceLastSpawn / 1000), 'seconds');
        console.log('Game size:', GAME_WIDTH, 'x', GAME_HEIGHT);
        console.log('Grid size:', Math.floor(GAME_WIDTH / GRID_SIZE), 'x', Math.floor(GAME_HEIGHT / GRID_SIZE));
        
        this.generatePowerUpItem();
        this.powerUpSpawnTimer = time;
        
        if (this.powerUpItem) {
          console.log('✅ Power-up item successfully spawned!');
          // 아이템 생성 시간 기록 (10초 후 자동 삭제용)
          this.powerUpItemSpawnTime = time;
        } else {
          console.log('❌ Failed to spawn power-up item - check game area size');
        }
      } else if (!this.powerUpItem && timeSinceLastSpawn < spawnInterval) {
        const timeRemaining = Math.ceil((spawnInterval - timeSinceLastSpawn) / 1000);
        if (timeRemaining > 0 && timeRemaining <= 3) {
          console.log('⏰ Next power-up item in', timeRemaining, 'seconds');
        }
      }
      
      // 아이템 생성 후 10초가 지나면 자동 삭제
      if (this.powerUpItem) {
        const itemSpawnTime = this.powerUpItemSpawnTime;
        if (itemSpawnTime && time - itemSpawnTime >= 10000) { // 10초 후 삭제
          console.log('⚠️ Power-up item auto-deleted after 10 seconds');
          this.powerUpItem = null;
          // 새로운 스폰 주기 시작
          this.powerUpSpawnTimer = time;
        }
      }
      
      // 아이템 설명 UI 업데이트
      this.updateItemDescriptionUI(time, spawnInterval);
    }

    private updatePoisonAppleSpawn(time: number) {
      // 독사과 생성 (5초마다, 아이템이 없을 때만)
      const spawnInterval = 5000; // 5초로 설정
      const timeSinceLastSpawn = time - this.poisonAppleSpawnTimer;
      
      if (!this.poisonApple && timeSinceLastSpawn >= spawnInterval) {
        console.log('💀 Attempting to spawn poison apple...');
        console.log('Time since last spawn:', Math.floor(timeSinceLastSpawn / 1000), 'seconds');
        console.log('Game size:', GAME_WIDTH, 'x', GAME_HEIGHT);
        console.log('Grid size:', Math.floor(GAME_WIDTH / GRID_SIZE), 'x', Math.floor(GAME_HEIGHT / GRID_SIZE));
        
        this.generatePoisonApple();
        this.poisonAppleSpawnTimer = time;
        
        if (this.poisonApple) {
          console.log('✅ Poison apple successfully spawned!');
          // 아이템 생성 시간 기록 (30초 후 자동 삭제용)
          this.poisonAppleSpawnTime = time;
        } else {
          console.log('❌ Failed to spawn poison apple - check game area size');
        }
      } else if (!this.poisonApple && timeSinceLastSpawn < spawnInterval) {
        const timeRemaining = Math.ceil((spawnInterval - timeSinceLastSpawn) / 1000);
        if (timeRemaining > 0 && timeRemaining <= 3) {
          console.log('⏰ Next poison apple in', timeRemaining, 'seconds');
        }
      }
      
      // 아이템 생성 후 30초가 지나면 자동 삭제
      if (this.poisonApple) {
        const itemSpawnTime = this.poisonAppleSpawnTime;
        if (itemSpawnTime && time - itemSpawnTime >= 30000) { // 30초 후 삭제
          console.log('⚠️ Poison apple auto-deleted after 30 seconds');
          this.poisonApple = null;
          // 새로운 스폰 주기 시작
          this.poisonAppleSpawnTimer = time;
        }
      }
      
      // 아이템 설명 UI 업데이트
      this.updateItemDescriptionUI(time, spawnInterval);
    }

    private updateItemDescriptionUI(time: number, spawnInterval: number) {
      if (!this.itemDescriptionUI) return;

      const timeSinceLastSpawn = time - this.powerUpSpawnTimer;
      const foodCount = this.foods.length;
      
      // 독사과 정보
      const poisonAppleSpawnInterval = 5000; // 5초
      const timeSincePoisonSpawn = time - this.poisonAppleSpawnTimer;
      const poisonTimeRemaining = Math.ceil((poisonAppleSpawnInterval - timeSincePoisonSpawn) / 1000);

      if (this.powerUpItem) {
        const itemLifeTime = this.powerUpItemSpawnTime;
        if (itemLifeTime) {
          const timeLeft = Math.ceil((10000 - (time - itemLifeTime)) / 1000);
          this.itemDescriptionUI.setText(`⚡ INVINCIBLE ITEM: Eat within ${timeLeft}s for 10sec invincibility! | 🍎 Foods: ${foodCount}/5 | 💀 Poison: ${this.poisonApple ? 'Available' : `${poisonTimeRemaining}s`}`);
        } else {
          this.itemDescriptionUI.setText(`⚡ INVINCIBLE ITEM: Eat for 10sec invincibility & 3x speed! | 🍎 Foods: ${foodCount}/5 | 💀 Poison: ${this.poisonApple ? 'Available' : `${poisonTimeRemaining}s`}`);
        }
      } else {
        const timeRemaining = Math.ceil((spawnInterval - timeSinceLastSpawn) / 1000);
        if (timeRemaining > 0) {
          this.itemDescriptionUI.setText(`⏰ Next invincible item in: ${timeRemaining}s | 🍎 Foods: ${foodCount}/5 | 💀 Poison: ${this.poisonApple ? 'Available' : `${poisonTimeRemaining}s`} | ⚡ Invincible: +3 length`);
        } else {
          this.itemDescriptionUI.setText(`⏰ Invincible item spawning... | 🍎 Foods: ${foodCount}/5 | 💀 Poison: ${this.poisonApple ? 'Available' : `${poisonTimeRemaining}s`} | ⚡ Invincible: +3 length`);
        }
      }
    }

    private generatePowerUpItem() {
      let powerUpX: number, powerUpY: number;
      const gridWidth = Math.floor(GAME_WIDTH / GRID_SIZE);
      const gridHeight = Math.floor(GAME_HEIGHT / GRID_SIZE);

      // 유효한 게임 영역 확인 (더 엄격한 체크)
      if (gridWidth <= 4 || gridHeight <= 4) {
        console.log('Game area too small for power-up item:', gridWidth, gridHeight);
        this.powerUpItem = null;
        return;
      }

      let attempts = 0;
      const maxAttempts = 50; // 무한 루프 방지

      do {
        powerUpX = Phaser.Math.Between(2, gridWidth - 3); // 더 안전한 여백 확보
        powerUpY = Phaser.Math.Between(2, gridHeight - 3); // Y 좌표 초기화 추가!
        attempts++;
        
        if (attempts > maxAttempts) {
          console.log('Failed to generate power-up item after', maxAttempts, 'attempts');
          this.powerUpItem = null;
          return;
        }
      } while (this.isSnakePosition(powerUpX, powerUpY) || 
               this.foods.some(food => powerUpX === food.x && powerUpY === food.y) ||
               (this.poisonApple && powerUpX === this.poisonApple.x && powerUpY === this.poisonApple.y)); // 모든 아이템과의 충돌 체크

      this.powerUpItem = new Phaser.Geom.Point(powerUpX, powerUpY);
      console.log('Power-up item generated at:', powerUpX, powerUpY, 'Grid size:', gridWidth, 'x', gridHeight);
    }

    private generatePoisonApple() {
      let poisonAppleX: number, poisonAppleY: number;
      const gridWidth = Math.floor(GAME_WIDTH / GRID_SIZE);
      const gridHeight = Math.floor(GAME_HEIGHT / GRID_SIZE);

      // 유효한 게임 영역 확인 (더 엄격한 체크)
      if (gridWidth <= 4 || gridHeight <= 4) {
        console.log('Game area too small for poison apple:', gridWidth, gridHeight);
        this.poisonApple = null;
        return;
      }

      let attempts = 0;
      const maxAttempts = 50; // 무한 루프 방지

      do {
        poisonAppleX = Phaser.Math.Between(2, gridWidth - 3); // 더 안전한 여백 확보
        poisonAppleY = Phaser.Math.Between(2, gridHeight - 3); // Y 좌표 초기화 추가!
        attempts++;
        
        if (attempts > maxAttempts) {
          console.log('Failed to generate poison apple after', maxAttempts, 'attempts');
          this.poisonApple = null;
          return;
        }
      } while (this.isSnakePosition(poisonAppleX, poisonAppleY) || 
               this.foods.some(food => poisonAppleX === food.x && poisonAppleY === food.y) ||
               (this.powerUpItem && poisonAppleX === this.powerUpItem.x && poisonAppleY === this.powerUpItem.y)); // 모든 아이템과의 충돌 체크

      this.poisonApple = new Phaser.Geom.Point(poisonAppleX, poisonAppleY);
      console.log('Poison apple generated at:', poisonAppleX, poisonAppleY, 'Grid size:', gridWidth, 'x', gridHeight);
    }

    private activateInvincibleMode() {
      console.log('Invincible mode activated!');
      this.isInvincible = true;
      this.invincibleStartTime = this.time.now;
      this.normalSpeed = this.currentMoveDelay; // 현재 속도 저장
      this.currentMoveDelay = Math.floor(this.baseMoveDelay / 3); // 3배 속도
      this.blinkTimer = 0;
      this.powerUpItem = null; // 아이템 제거
      
      // 다음 아이템이 더 빨리 나오도록 타이머 조정 (15초 후)
      this.powerUpSpawnTimer = this.time.now - 15000; // 30초 - 15초 = 15초 후 생성
    }

    // 컨테이너 크기가 변경될 때 호출되는 메서드
    public updateGameSize(newWidth: number, newHeight: number) {
      GAME_WIDTH = newWidth;
      GAME_HEIGHT = newHeight;
      
      // 배경 크기 조정
      this.add.rectangle(GAME_WIDTH / 2, GAME_HEIGHT / 2, GAME_WIDTH, GAME_HEIGHT, 0x1a1a2e);
      
      // UI 텍스트 크기와 위치 조정
      if (this.scoreText) {
        this.scoreText.setFontSize(Math.max(16, Math.min(24, GAME_WIDTH / 40)));
        this.scoreText.setPosition(20, 20);
      }
      
      if (this.speedText) {
        this.speedText.setFontSize(Math.max(14, Math.min(20, GAME_WIDTH / 45)));
        this.speedText.setPosition(20, 50);
      }
      
      if (this.powerUpText) {
        this.powerUpText.setFontSize(Math.max(16, Math.min(22, GAME_WIDTH / 40)));
        this.powerUpText.setPosition(20, 80);
      }

      if (this.itemDescriptionUI) {
        this.itemDescriptionUI.setFontSize(Math.max(10, Math.min(14, GAME_WIDTH / 60)));
        this.itemDescriptionUI.setPosition(GAME_WIDTH / 2, GAME_HEIGHT - 30);
      }
      
      // 무적 아이템 위치 조정 (화면 밖에 있으면 다시 생성)
      if (this.powerUpItem) {
        const gridWidth = Math.floor(GAME_WIDTH / GRID_SIZE);
        const gridHeight = Math.floor(GAME_HEIGHT / GRID_SIZE);
        
        // 아이템이 화면 밖에 있으면 새로운 위치로 이동
        if (this.powerUpItem.x >= gridWidth || this.powerUpItem.y >= gridHeight || 
            this.powerUpItem.x < 0 || this.powerUpItem.y < 0) {
          this.generatePowerUpItem();
        }
      }
      
      // 뱀이 화면 밖에 있으면 위치 조정
      const gridWidth = Math.floor(GAME_WIDTH / GRID_SIZE);
      const gridHeight = Math.floor(GAME_HEIGHT / GRID_SIZE);
      
      this.snake.forEach((segment, index) => {
        if (segment.x >= gridWidth) segment.x = gridWidth - 1;
        if (segment.y >= gridHeight) segment.y = gridHeight - 1;
        if (segment.x < 0) segment.x = 0;
        if (segment.y < 0) segment.y = 0;
      });
      
      // 음식이 화면 밖에 있으면 다시 생성
      let needsNewFood = false;
      this.foods.forEach((food, index) => {
        if (food.x >= gridWidth || food.y >= gridHeight || 
            food.x < 0 || food.y < 0) {
          this.foods.splice(index, 1); // 잘못된 위치의 음식 제거
          needsNewFood = true;
        }
      });
      
      if (needsNewFood) {
        this.addNewFood(); // 새로운 음식 추가
      }

      // 독사과가 화면 밖에 있으면 다시 생성
      if (this.poisonApple) {
        const gridWidth = Math.floor(GAME_WIDTH / GRID_SIZE);
        const gridHeight = Math.floor(GAME_HEIGHT / GRID_SIZE);
        
        if (this.poisonApple.x >= gridWidth || this.poisonApple.y >= gridHeight || 
            this.poisonApple.x < 0 || this.poisonApple.y < 0) {
          this.generatePoisonApple();
        }
      }
      
      // 그리드와 게임 요소들 다시 그리기
      this.drawGrid(); 
      this.render(); 
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
      },
      input: {
        keyboard: true
      }
    };

    game = new Phaser.Game(config);

    // 게임 컨테이너를 포커스 가능하게 설정
    if (gameContainer) {
      gameContainer.tabIndex = 0;
      gameContainer.style.outline = 'none';
      gameContainer.focus();
      
      // 클릭했을 때도 포커스 받도록
      gameContainer.addEventListener('click', () => {
        gameContainer.focus();
      });
      
      console.log('Game container focused and input enabled');
    }

    // 리사이즈 이벤트 리스너 추가
    window.addEventListener('resize', handleResize);

    return () => {
      if (game) {
        game.destroy(true);
        game = null;
      }
      // 리사이즈 이벤트 리스너 제거
      window.removeEventListener('resize', handleResize);
    };
  });

  onDestroy(() => {
    if (game) {
      game.destroy(true);
      game = null;
    }
    // 리사이즈 이벤트 리스너 제거
    window.removeEventListener('resize', handleResize);
  });
</script>

<div bind:this={gameContainer} class="w-full h-full bg-black" />

<style>
  /* 게임 컨테이너가 전체 공간을 차지하도록 설정 */
  :global(.w-full.h-full) {
    width: 100% !important;
    height: 100% !important;
    min-height: 100%;
  }
</style>