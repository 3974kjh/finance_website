<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Phaser from 'phaser';

  let gameContainer: HTMLDivElement;
  let game: Phaser.Game | null = null;

  // 게임 설정 (동적으로 조정될 예정)
  let GAME_WIDTH = 800;
  let GAME_HEIGHT = 600;

  // 컨테이너 크기에 맞춰 게임 크기 조정
  function adjustGameSize() {
    if (gameContainer) {
      const containerRect = gameContainer.getBoundingClientRect();
      GAME_WIDTH = Math.floor(containerRect.width);
      GAME_HEIGHT = Math.floor(containerRect.height);
      
      // 최소 크기 보장
      GAME_WIDTH = Math.max(400, GAME_WIDTH);
      GAME_HEIGHT = Math.max(300, GAME_HEIGHT);
      
      // 게임이 실행 중이라면 크기 조정
      if (game) {
        game.scale.resize(GAME_WIDTH, GAME_HEIGHT);
        
        // 씬이 존재한다면 씬의 크기도 업데이트
        const scene = game.scene.getScene('SpaceScene') as SpaceScene;
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

  class SpaceScene extends Phaser.Scene {
    private player: Phaser.GameObjects.Rectangle | null = null;
    private bullets: Phaser.GameObjects.Group | null = null;
    private enemies: Phaser.GameObjects.Group | null = null;
    private stars: Phaser.GameObjects.Group | null = null;
    private boss: Phaser.GameObjects.Rectangle | null = null;
    private bossBullets: Phaser.GameObjects.Group | null = null;
    private items: Phaser.GameObjects.Group | null = null; // 새로운 아이템 그룹
    private cursors: Phaser.Types.Input.Keyboard.CursorKeys | null = null;
    private wasd: any = null;
    private spaceKey: Phaser.Input.Keyboard.Key | null = null;
    private gKey: Phaser.Input.Keyboard.Key | null = null; // 궁극기 키
    private lastFired: number = 0;
    private score: number = 0;
    private lives: number = 3;
    private maxLives: number = 3; // 최대 체력
    private stage: number = 1;
    private scoreText: Phaser.GameObjects.Text | null = null;
    private livesText: Phaser.GameObjects.Text | null = null;
    private stageText: Phaser.GameObjects.Text | null = null;
    private gameOverText: Phaser.GameObjects.Text | null = null;
    private bossHealthBar: Phaser.GameObjects.Graphics | null = null;
    private bossHealthText: Phaser.GameObjects.Text | null = null;
    private itemsUI: Phaser.GameObjects.Text | null = null; // 아이템 상태 표시
    private itemDescriptionUI: Phaser.GameObjects.Text | null = null; // 아이템 설명 UI
    private gameOver: boolean = false;
    private enemySpawnTimer: number = 0;
    private itemSpawnTimer: number = 0; // 아이템 생성 타이머 (레거시)
    
    // 아이템별 독립적인 타이머 시스템
    private bulletUpgradeTimer: number = 0;
    private ultimateTimer: number = 0;
    private healthTimer: number = 0;
    private shieldTimer: number = 0;
    
    // 각 아이템의 다음 스폰 시간 추적
    private bulletUpgradeTimerNextSpawn: number = 0;
    private ultimateTimerNextSpawn: number = 0;
    private healthTimerNextSpawn: number = 0;
    private shieldTimerNextSpawn: number = 0;
    
    private graphics: Phaser.GameObjects.Graphics | null = null;
    private level: number = 1;
    
    // 보스 관련 변수
    private isBossStage: boolean = false;
    private bossMaxHealth: number = 200; // 보스 체력 증가
    private bossCurrentHealth: number = 200;
    private bossDirection: number = 1; // 1: 아래, -1: 위
    private bossLastShot: number = 0;
    private stageTransitionTimer: number = 0;
    private isStageTransition: boolean = false;

    // 새로운 게임 시스템
    private bulletUpgrade: number = 1; // 총알 업그레이드 레벨 (1-5)
    private ultimateCount: number = 0; // 궁극기 개수 (최대 3)
    private hasShield: boolean = false; // 보호막 상태
    
    // 차지 어택 시스템
    private isCharging: boolean = false;
    private chargeStartTime: number = 0;
    private chargeEffect: Phaser.GameObjects.Graphics | null = null;
    
    // 플레이어 시각 효과
    private playerBlinkTimer: number = 0;
    private shieldGraphics: Phaser.GameObjects.Graphics | null = null;

    constructor() {
      super({ key: 'SpaceScene' });
    }

    preload() {
      // 간단한 픽셀 이미지 생성 (base64 인코딩)
      this.load.image('pixel', 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==');
    }

    create() {
      // 우주 배경
      this.add.rectangle(GAME_WIDTH / 2, GAME_HEIGHT / 2, GAME_WIDTH, GAME_HEIGHT, 0x000011);
      
      // 그래픽스 객체 생성
      this.graphics = this.add.graphics();
      this.bossHealthBar = this.add.graphics();

      // 별 배경 생성
      this.createStars();

      // 플레이어 생성
      this.createPlayer();

      // 그룹들 생성
      this.bullets = this.add.group();
      this.enemies = this.add.group();
      this.bossBullets = this.add.group();
      this.items = this.add.group(); // 아이템 그룹 추가

      // 키보드 입력 설정
      this.cursors = this.input.keyboard?.createCursorKeys() || null;
      
      if (this.input.keyboard) {
        this.wasd = this.input.keyboard.addKeys('W,S,A,D');
        this.spaceKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.SPACE);
        this.gKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.G); // 궁극기 키 추가
      }

      // UI 텍스트
      this.scoreText = this.add.text(20, 20, 'Score: 0', {
        fontSize: Math.max(14, Math.min(20, GAME_WIDTH / 40)) + 'px',
        color: '#00ff00',
        fontFamily: 'Courier New, monospace',
        stroke: '#003300',
        strokeThickness: 2,
        shadow: {
          offsetX: 2,
          offsetY: 2,
          color: '#000000',
          blur: 6,
          stroke: true,
          fill: true
        }
      });

      this.livesText = this.add.text(20, 50, '', {
        fontSize: Math.max(14, Math.min(20, GAME_WIDTH / 40)) + 'px',
        color: '#ff3333',
        fontFamily: 'Courier New, monospace',
        stroke: '#330000',
        strokeThickness: 2,
        shadow: {
          offsetX: 2,
          offsetY: 2,
          color: '#000000',
          blur: 6,
          stroke: true,
          fill: true
        }
      });

      this.stageText = this.add.text(20, 80, 'Stage: 1', {
        fontSize: Math.max(14, Math.min(20, GAME_WIDTH / 40)) + 'px',
        color: '#ffff00',
        fontFamily: 'Courier New, monospace',
        stroke: '#333300',
        strokeThickness: 2,
        shadow: {
          offsetX: 2,
          offsetY: 2,
          color: '#000000',
          blur: 6,
          stroke: true,
          fill: true
        }
      });

      this.bossHealthText = this.add.text(GAME_WIDTH / 2, 30, '', {
        fontSize: Math.max(16, Math.min(24, GAME_WIDTH / 35)) + 'px',
        color: '#ff0000',
        fontFamily: 'Courier New, monospace',
        stroke: '#330000',
        strokeThickness: 3,
        shadow: {
          offsetX: 3,
          offsetY: 3,
          color: '#000000',
          blur: 8,
          stroke: true,
          fill: true
        }
      }).setOrigin(0.5).setVisible(false);

      this.itemsUI = this.add.text(GAME_WIDTH - 150, 20, '', {
        fontSize: Math.max(14, Math.min(20, GAME_WIDTH / 40)) + 'px',
        color: '#00ffff',
        fontFamily: 'Courier New, monospace',
        stroke: '#003333',
        strokeThickness: 2,
        shadow: {
          offsetX: 2,
          offsetY: 2,
          color: '#000000',
          blur: 6,
          stroke: true,
          fill: true
        }
      }).setOrigin(1, 0);

      // 아이템 설명 UI 추가 (하단)
      this.itemDescriptionUI = this.add.text(GAME_WIDTH / 2, GAME_HEIGHT - 40, '', {
        fontSize: Math.max(10, Math.min(12, GAME_WIDTH / 60)) + 'px',
        color: '#cccccc',
        fontFamily: 'Courier New, monospace',
        stroke: '#222222',
        strokeThickness: 1,
        shadow: {
          offsetX: 1,
          offsetY: 1,
          color: '#000000',
          blur: 2,
          stroke: true,
          fill: true
        },
        align: 'center'
      }).setOrigin(0.5);

      // 게임 리셋
      this.resetGame();
    }

    update(time: number) {
      if (this.gameOver) {
        this.handleGameOverInput();
        return;
      }

      if (this.isStageTransition) {
        this.handleStageTransition(time);
        return;
      }

      this.handleInput(time);
      this.updatePlayer();
      this.updateBullets();
      
      if (this.isBossStage) {
        this.updateBoss(time);
        this.updateBossBullets();
        this.checkBossCollisions();
        this.drawBossHealthBar();
      } else {
        this.updateEnemies(time);
        this.checkCollisions();
        this.checkStageProgression();
      }
      
      this.updateStars();
      this.updateItems(time);
      this.checkItemCollisions();
    }

    private createStars() {
      this.stars = this.add.group();
      
      // 별의 개수를 화면 크기에 비례하여 조정
      const starCount = Math.max(50, Math.min(150, (GAME_WIDTH * GAME_HEIGHT) / 5000));
      
      for (let i = 0; i < starCount; i++) {
        const x = Phaser.Math.Between(0, GAME_WIDTH);
        const y = Phaser.Math.Between(0, GAME_HEIGHT);
        const size = Phaser.Math.Between(1, 3);
        
        const star = this.add.rectangle(x, y, size, size, 0xffffff);
        star.setData('speed', Phaser.Math.Between(1, 3));
        this.stars.add(star);
      }
    }

    private createPlayer() {
      // 플레이어 우주선 (좌측에서 시작)
      this.player = this.add.rectangle(100, GAME_HEIGHT / 2, 0, 0, 0x00ff00);
      this.player.setSize(30, 20);
    }

    private resetGame() {
      this.score = 0;
      this.lives = 3;
      this.maxLives = 3;
      this.stage = 1;
      this.level = 1;
      this.gameOver = false;
      this.enemySpawnTimer = 0;
      this.itemSpawnTimer = 0;
      this.isBossStage = false;
      this.isStageTransition = false;
      
      // 아이템별 타이머 초기화
      this.bulletUpgradeTimer = 0;
      this.ultimateTimer = 0;
      this.healthTimer = 0;
      this.shieldTimer = 0;
      
      // 첫 스폰 시간 초기화 (resetGame 호출 시점에서는 아직 정확한 시간을 알 수 없음)
      this.bulletUpgradeTimerNextSpawn = 0;
      this.ultimateTimerNextSpawn = 0;
      this.healthTimerNextSpawn = 0;
      this.shieldTimerNextSpawn = 0;
      
      // 새로운 게임 시스템 초기화
      this.bulletUpgrade = 1;
      this.ultimateCount = 0;
      this.hasShield = false;
      
      // 차지 어택 시스템 초기화
      this.isCharging = false;
      this.chargeStartTime = 0;
      this.playerBlinkTimer = 0;
      
      // 그래픽 객체 정리
      this.shieldGraphics?.destroy();
      this.shieldGraphics = null;
      this.chargeEffect?.destroy();
      this.chargeEffect = null;
      
      // UI 업데이트
      this.scoreText?.setText('Score: 0');
      this.updateLivesDisplay();
      this.stageText?.setText('Stage: 1');
      this.bossHealthText?.setVisible(false);
      this.updateItemsDisplay();

      // 아이템 설명 UI 초기화
      this.itemDescriptionUI?.setText('Active Items: 0\n🟢BULLET+ | 🔴ULTIMATE | 🔵HEALTH+ | 🟡SHIELD - Spawning...');

      // 플레이어 위치 리셋 (좌측)
      if (this.player) {
        this.player.setPosition(100, GAME_HEIGHT / 2);
        this.player.setVisible(true);
      }

      // 게임 오브젝트들 정리
      this.bullets?.clear(true, true);
      this.enemies?.clear(true, true);
      this.bossBullets?.clear(true, true);
      this.items?.clear(true, true);
      this.clearBoss();
    }

    private handleInput(time: number) {
      if (!this.player || !this.cursors) return;

      const playerSpeed = Math.max(3, Math.min(7, GAME_HEIGHT / 100)); // 세로 이동용 속도

      // 위아래 이동만 처리
      if (this.cursors.up?.isDown || this.wasd?.W?.isDown) {
        this.player.y -= playerSpeed;
      }
      if (this.cursors.down?.isDown || this.wasd?.S?.isDown) {
        this.player.y += playerSpeed;
      }

      // 화면 경계 제한 (세로만)
      this.player.y = Phaser.Math.Clamp(this.player.y, 15, GAME_HEIGHT - 15);

      // 차지 어택 시스템 개선
      if (this.spaceKey?.isDown) {
        if (!this.isCharging) {
          // 차지 시작
          this.isCharging = true;
          this.chargeStartTime = time;
        }
      } else if (this.isCharging) {
        // 스페이스 키를 떼었을 때
        const chargeDuration = time - this.chargeStartTime;
        
        if (chargeDuration >= 2000) { // 2초 이상 충전했으면 차지 어택
          this.fireChargedBullet();
        } else if (time > this.lastFired + 150) { // 일반 발사 (0.15초 간격)
          this.fireBullet();
          this.lastFired = time;
        }
        
        this.isCharging = false;
      }

      // 궁극기 발동 (G키)
      if (this.gKey?.isDown && time > this.lastFired + 1000 && this.ultimateCount > 0) { // 1초 간격
        this.useUltimate();
        this.lastFired = time;
      }
    }

    private updatePlayer() {
      if (!this.player || !this.graphics) return;

      // 플레이어 우주선 그리기 (더 미래지향적이고 세련된 디자인)
      this.graphics.clear();
      
      const shipSize = Math.max(10, Math.min(20, GAME_HEIGHT / 30));
      
      // 차지 중일 때 색상 변경
      let mainColor = 0x00ff44;
      let highlightColor = 0x88ff88;
      let coreColor = 0x44ff44;
      
      if (this.isCharging) {
        const chargeDuration = this.time.now - this.chargeStartTime;
        const blinkSpeed = Math.min(chargeDuration / 2000, 1) * 10; // 충전도에 따라 깜빡임 속도 증가
        const blinkIntensity = Math.sin(this.time.now * blinkSpeed * 0.01) * 0.5 + 0.5;
        
        if (chargeDuration >= 2000) {
          // 2초 이상 충전 시 파란색/청록색으로 변경
          mainColor = blinkIntensity > 0.5 ? 0x00ffff : 0x0088ff;
          highlightColor = blinkIntensity > 0.5 ? 0x88ffff : 0x44aaff;
          coreColor = blinkIntensity > 0.5 ? 0x44ffff : 0x0066aa;
        } else {
          // 충전 중일 때 노란색/주황색으로 변경
          mainColor = blinkIntensity > 0.5 ? 0xffff00 : 0x00ff44;
          highlightColor = blinkIntensity > 0.5 ? 0xffff88 : 0x88ff88;
          coreColor = blinkIntensity > 0.5 ? 0xffaa00 : 0x44ff44;
        }
      }
      
      // 우주선 메인 바디 (더 세련된 디자인)
      this.graphics.fillStyle(mainColor);
      this.graphics.beginPath();
      // 더 미래지향적인 형태
      this.graphics.moveTo(this.player.x + shipSize * 1.4, this.player.y); // 앞부분 (더 뾰족하게)
      this.graphics.lineTo(this.player.x - shipSize * 0.6, this.player.y - shipSize * 0.7); // 왼쪽 위
      this.graphics.lineTo(this.player.x - shipSize * 0.2, this.player.y - shipSize * 0.3); // 중간 위
      this.graphics.lineTo(this.player.x - shipSize * 0.2, this.player.y + shipSize * 0.3); // 중간 아래
      this.graphics.lineTo(this.player.x - shipSize * 0.6, this.player.y + shipSize * 0.7); // 왼쪽 아래
      this.graphics.closePath();
      this.graphics.fillPath();

      // 우주선 상부 장갑
      this.graphics.fillStyle(highlightColor);
      this.graphics.beginPath();
      this.graphics.moveTo(this.player.x + shipSize * 1.1, this.player.y);
      this.graphics.lineTo(this.player.x - shipSize * 0.3, this.player.y - shipSize * 0.4);
      this.graphics.lineTo(this.player.x - shipSize * 0.3, this.player.y + shipSize * 0.4);
      this.graphics.closePath();
      this.graphics.fillPath();

      // 코어/조종석 (중앙 발광부)
      this.graphics.fillStyle(coreColor);
      this.graphics.fillCircle(this.player.x + shipSize * 0.3, this.player.y, shipSize * 0.3);
      
      // 코어 내부
      this.graphics.fillStyle(0xffffff);
      this.graphics.fillCircle(this.player.x + shipSize * 0.3, this.player.y, shipSize * 0.15);

      // 날개 구조 (상하)
      this.graphics.fillStyle(mainColor);
      this.graphics.fillRect(this.player.x - shipSize * 0.1, this.player.y - shipSize * 0.8, shipSize * 0.6, shipSize * 0.2);
      this.graphics.fillRect(this.player.x - shipSize * 0.1, this.player.y + shipSize * 0.6, shipSize * 0.6, shipSize * 0.2);

      // 무기 시스템 (상하 레이저 포트)
      this.graphics.fillStyle(0x00aaff);
      this.graphics.fillCircle(this.player.x + shipSize * 0.8, this.player.y - shipSize * 0.3, 3);
      this.graphics.fillCircle(this.player.x + shipSize * 0.8, this.player.y + shipSize * 0.3, 3);

      // 엔진 불꽃 효과 (좌측) - 더 강력하고 미래지향적
      const engineColor = this.isCharging ? 0xff0088 : 0xff6600;
      this.graphics.fillStyle(engineColor);
      this.graphics.beginPath();
      this.graphics.moveTo(this.player.x - shipSize * 0.6, this.player.y - shipSize * 0.4);
      this.graphics.lineTo(this.player.x - shipSize * 1.8, this.player.y - shipSize * 0.1);
      this.graphics.lineTo(this.player.x - shipSize * 2, this.player.y);
      this.graphics.lineTo(this.player.x - shipSize * 1.8, this.player.y + shipSize * 0.1);
      this.graphics.lineTo(this.player.x - shipSize * 0.6, this.player.y + shipSize * 0.4);
      this.graphics.closePath();
      this.graphics.fillPath();
      
      // 내부 불꽃 효과 (더 밝고 강렬하게)
      const innerEngineColor = this.isCharging ? 0xff44aa : 0xffaa00;
      this.graphics.fillStyle(innerEngineColor);
      this.graphics.beginPath();
      this.graphics.moveTo(this.player.x - shipSize * 0.6, this.player.y - shipSize * 0.25);
      this.graphics.lineTo(this.player.x - shipSize * 1.4, this.player.y - shipSize * 0.05);
      this.graphics.lineTo(this.player.x - shipSize * 1.6, this.player.y);
      this.graphics.lineTo(this.player.x - shipSize * 1.4, this.player.y + shipSize * 0.05);
      this.graphics.lineTo(this.player.x - shipSize * 0.6, this.player.y + shipSize * 0.25);
      this.graphics.closePath();
      this.graphics.fillPath();

      // 최내부 불꽃 코어 (하얀색 중심)
      this.graphics.fillStyle(0xffffff);
      this.graphics.beginPath();
      this.graphics.moveTo(this.player.x - shipSize * 0.6, this.player.y - shipSize * 0.1);
      this.graphics.lineTo(this.player.x - shipSize * 1.2, this.player.y);
      this.graphics.lineTo(this.player.x - shipSize * 0.6, this.player.y + shipSize * 0.1);
      this.graphics.closePath();
      this.graphics.fillPath();

      // 보호막 시각 효과 업데이트
      if (this.hasShield) {
        this.updateShieldVisual();
      }

      // 플레이어 깜빡임 효과 (무적 시간)
      if (this.playerBlinkTimer > 0) {
        this.playerBlinkTimer--;
        if (this.playerBlinkTimer % 10 === 0) {
          this.player.setVisible(!this.player.visible);
        }
      } else {
        this.player.setVisible(true);
      }
    }

    private fireBullet() {
      if (!this.player || !this.bullets) return;

      const bulletSize = Math.max(3, Math.min(6, GAME_WIDTH / 150));
      
      // 총알 업그레이드에 따른 발사 패턴
      const bulletCount = this.bulletUpgrade;
      const spreadAngle = 10; // 퍼짐 각도
      
      for (let i = 0; i < bulletCount; i++) {
        let offsetY = 0;
        
        if (bulletCount > 1) {
          // 여러 발 발사 시 Y축 분산
          offsetY = (i - (bulletCount - 1) / 2) * spreadAngle;
        }
        
        const bullet = this.add.rectangle(
          this.player.x + 20, 
          this.player.y + offsetY, 
          bulletSize * 2, 
          bulletSize, 
          0xffff00
        );
        bullet.setData('speed', Math.max(6, Math.min(10, GAME_WIDTH / 80)));
        bullet.setData('damage', 1);
        bullet.setData('upgradeLevel', this.bulletUpgrade);
        this.bullets.add(bullet);
      }
    }

    private updateBullets() {
      if (!this.bullets) return;

      this.bullets.children.entries.forEach(bullet => {
        const bulletObj = bullet as Phaser.GameObjects.Rectangle;
        bulletObj.x += bulletObj.getData('speed'); // 우측으로 이동

        // 화면 밖으로 나간 총알 제거
        if (bulletObj.x > GAME_WIDTH) {
          this.bullets?.remove(bulletObj);
          bulletObj.destroy();
        }
      });
    }

    private updateEnemies(time: number) {
      if (!this.enemies) return;

      // 적 생성 간격을 스테이지에 따라 더 적극적으로 조정 (더 빠르게, 더 많이)
      const baseSpawnInterval = Math.max(400, 1800 - (this.stage * 150)); // 스테이지당 150ms 감소, 최소 400ms
      const enemiesPerWave = Math.min(3, 1 + Math.floor(this.stage / 2)); // 2스테이지마다 적 1마리씩 추가 (최대 3마리)
      
      if (time > this.enemySpawnTimer + baseSpawnInterval) {
        // 여러 마리 동시 생성
        for (let i = 0; i < enemiesPerWave; i++) {
          this.spawnEnemy();
        }
        this.enemySpawnTimer = time;
      }

      // 적 이동 및 업데이트 - 스테이지별 속도 대폭 증가
      this.enemies.children.entries.forEach(enemy => {
        const enemyObj = enemy as Phaser.GameObjects.Rectangle;
        const baseSpeed = 2.5; // 기본 속도 증가
        const stageSpeedBonus = Math.floor(this.stage * 1.2); // 스테이지당 1.2배 속도 증가
        const speed = baseSpeed + stageSpeedBonus;
        enemyObj.x -= speed;

        // 적 시각 효과 개선 (스테이지별 색상 적용)
        this.drawEnhancedEnemy(enemyObj);

        // 화면 밖으로 나가면 제거
        if (enemyObj.x < -50) {
          this.enemies?.remove(enemyObj);
          enemyObj.destroy();
        }
      });
    }

    private spawnEnemy() {
      if (!this.enemies) return;

      const enemySize = Math.max(15, Math.min(25, GAME_HEIGHT / 25));
      const y = Phaser.Math.Between(50, GAME_HEIGHT - 50);
      
      // 스테이지별 색상 계산 (더 화려하고 위협적으로)
      let enemyColor = 0xff4444; // 기본 빨간색
      const stageColorShift = this.stage - 1;
      
      if (stageColorShift >= 1) {
        // 스테이지별 색상 변화: 빨강 -> 주황 -> 노랑 -> 초록 -> 파랑 -> 보라 -> 분홍 등
        const hue = (stageColorShift * 30) % 360; // 30도씩 색상 변화
        const saturation = Math.min(100, 70 + (stageColorShift * 5)); // 채도 증가
        const lightness = Math.max(40, 60 - (stageColorShift * 2)); // 명도 조정
        
        // HSL to RGB 변환을 위한 간단한 색상 팔레트
        const colorPalette = [
          0xff4444, // 1단계: 빨강
          0xff8844, // 2단계: 주황
          0xffcc44, // 3단계: 노랑
          0x88ff44, // 4단계: 연두
          0x44ff88, // 5단계: 청록
          0x4488ff, // 6단계: 파랑
          0x8844ff, // 7단계: 보라
          0xff44cc, // 8단계: 분홍
          0xff4488, // 9단계: 마젠타
          0xccff44  // 10단계: 라임
        ];
        
        const colorIndex = Math.min(stageColorShift - 1, colorPalette.length - 1);
        enemyColor = colorPalette[colorIndex];
        
        // 고단계에서는 더 강렬한 색상 효과
        if (this.stage >= 10) {
          const intensity = Math.min(255, 180 + (this.stage * 8));
          enemyColor = Phaser.Display.Color.GetColor(intensity, intensity * 0.3, intensity * 0.7);
        }
      }
      
      const enemy = this.add.rectangle(GAME_WIDTH + 50, y, enemySize, enemySize, enemyColor);
      
      // 스테이지별 체력 대폭 증가 - 더 도전적으로
      const baseHealth = 1;
      const stageHealthBonus = Math.floor(this.stage / 2) + Math.floor(this.stage * 0.8); // 2스테이지마다 +1, 스테이지당 +0.8
      const enemyHealth = baseHealth + stageHealthBonus;
      
      enemy.setData('health', enemyHealth);
      enemy.setData('maxHealth', enemyHealth);
      enemy.setData('animTimer', 0);
      enemy.setData('stageColor', enemyColor); // 스테이지별 색상 저장
      
      console.log(`Stage ${this.stage}: Enemy spawned with ${enemyHealth} HP, color: ${enemyColor.toString(16)}`);
      
      this.enemies.add(enemy);
    }

    private updateStars() {
      if (!this.stars) return;

      this.stars.children.entries.forEach(star => {
        const starObj = star as Phaser.GameObjects.Rectangle;
        starObj.x -= starObj.getData('speed'); // 좌측으로 이동

        // 화면 왼쪽으로 나간 별을 우측으로 재배치
        if (starObj.x < -5) {
          starObj.x = GAME_WIDTH + 5;
          starObj.y = Phaser.Math.Between(0, GAME_HEIGHT);
        }
      });
    }

    private updateItems(time: number) {
      if (!this.items) return;

      // 각 아이템별 간단한 설명 (짧고 간결하게)
      const itemConfigs = {
        bulletUpgrade: { minInterval: 5000, maxInterval: 40000, timer: 'bulletUpgradeTimer', description: '🟢 Bullet+' },
        ultimate: { minInterval: 5000, maxInterval: 40000, timer: 'ultimateTimer', description: '🔴 Ultimate' },
        health: { minInterval: 5000, maxInterval: 40000, timer: 'healthTimer', description: '🔵 Health+' },
        shield: { minInterval: 5000, maxInterval: 40000, timer: 'shieldTimer', description: '🟡 Shield' }
      };

      // 각 아이템별로 독립적인 랜덤 스폰 체크
      Object.entries(itemConfigs).forEach(([itemType, config]) => {
        const currentTimer = this[config.timer as keyof this] as number;
        const nextSpawnTime = this[`${config.timer}NextSpawn` as keyof this] as number || 0;
        
        // 다음 스폰 시간이 설정되지 않았다면 랜덤하게 설정
        if (nextSpawnTime === 0) {
          // 첫 스폰은 5-25초 사이 랜덤하게 (더 짧고 다양하게)
          const firstSpawnInterval = Phaser.Math.Between(5000, 25000);
          (this as any)[`${config.timer}NextSpawn`] = time + firstSpawnInterval;
          console.log(`${itemType} first spawn in ${Math.floor(firstSpawnInterval/1000)}s`);
        } else if (time >= nextSpawnTime) {
          // 스폰 시간이 되었으면 아이템 생성
          this.spawnSpecificItem(itemType);
          
          // 다음 스폰 시간을 새로운 랜덤 간격으로 설정
          const randomInterval = Phaser.Math.Between(config.minInterval, config.maxInterval);
          (this as any)[config.timer] = time;
          (this as any)[`${config.timer}NextSpawn`] = time + randomInterval;
        }
      });

      // 아이템 이동 및 수명 관리
      this.items.children.entries.forEach(item => {
        const itemObj = item as Phaser.GameObjects.Rectangle;
        const speed = Math.max(3, Math.min(6, GAME_WIDTH / 150));
        itemObj.x -= speed;

        // 연결된 라벨 텍스트도 함께 이동
        const labelText = itemObj.getData('labelText') as Phaser.GameObjects.Text;
        if (labelText) {
          labelText.x -= speed;
        }

        // 아이템 시각 효과 개선
        this.drawEnhancedItem(itemObj);

        // 화면 밖으로 나가면 제거
        if (itemObj.x < -50) {
          // 라벨 텍스트도 함께 제거
          if (labelText) {
            labelText.destroy();
          }
          this.items?.remove(itemObj);
          itemObj.destroy();
        }
      });

      // 아이템 설명 UI 업데이트
      this.updateItemDescriptionUI(time, itemConfigs);
    }

    private spawnSpecificItem(itemType: string) {
      if (!this.items) return;

      const y = Phaser.Math.Between(50, GAME_HEIGHT - 50);
      const itemSize = 20;

      // 아이템 타입별로 다른 기본 색상 설정
      let baseColor = 0xffffff;
      let itemLabel = '';
      switch (itemType) {
        case 'bulletUpgrade':
          baseColor = 0x00ff00; // 초록색
          itemLabel = 'BULLET+';
          break;
        case 'ultimate':
          baseColor = 0xff0000; // 빨간색
          itemLabel = 'ULTIMATE';
          break;
        case 'health':
          baseColor = 0x0099ff; // 파란색
          itemLabel = 'HEALTH+';
          break;
        case 'shield':
          baseColor = 0xffff00; // 노란색
          itemLabel = 'SHIELD';
          break;
      }

      const item = this.add.rectangle(GAME_WIDTH + 50, y, itemSize, itemSize, baseColor);
      item.setData('type', itemType);
      item.setData('animTimer', 0);
      
      // 아이템 위에 라벨 텍스트 추가
      const itemText = this.add.text(GAME_WIDTH + 50, y - 25, itemLabel, {
        fontSize: '10px',
        color: '#ffffff',
        fontFamily: 'Courier New, monospace',
        stroke: '#000000',
        strokeThickness: 2,
        shadow: {
          offsetX: 1,
          offsetY: 1,
          color: '#000000',
          blur: 3,
          stroke: true,
          fill: true
        }
      }).setOrigin(0.5);
      
      // 텍스트를 아이템과 함께 움직이도록 연결
      item.setData('labelText', itemText);
      
      this.items.add(item);
      
      console.log(`Spawned ${itemType} item with label at position ${GAME_WIDTH + 50}, ${y}`);
    }

    private updateItemDescriptionUI(time: number, itemConfigs: any) {
      if (!this.itemDescriptionUI) return;

      let itemDescriptions: string[] = [];
      let totalActiveItems = 0;

      // 각 아이템별 상세 정보 생성
      Object.entries(itemConfigs).forEach(([itemType, config]: [string, any]) => {
        const nextSpawnTime = this[`${config.timer}NextSpawn` as keyof this] as number;
        const timeUntilNext = Math.max(0, nextSpawnTime - time);
        const secondsUntilNext = Math.ceil(timeUntilNext / 1000);

        // 현재 화면에 있는 해당 타입 아이템 개수 확인
        let itemCount = 0;
        this.items?.children.entries.forEach(item => {
          const itemObj = item as Phaser.GameObjects.Rectangle;
          if (itemObj.getData('type') === itemType) {
            itemCount++;
          }
        });
        totalActiveItems += itemCount;

        // 아이템별 UI 아이콘과 설명
        let itemIcon = '';
        let itemName = '';
        switch (itemType) {
          case 'bulletUpgrade':
            itemIcon = '🟢';
            itemName = 'BULLET+';
            break;
          case 'ultimate':
            itemIcon = '🔴';
            itemName = 'ULTIMATE';
            break;
          case 'health':
            itemIcon = '🔵';
            itemName = 'HEALTH+';
            break;
          case 'shield':
            itemIcon = '🟡';
            itemName = 'SHIELD';
            break;
        }

        // 타이머 정보
        let timerInfo = '';
        if (secondsUntilNext > 0) {
          timerInfo = `${secondsUntilNext}s`;
        } else {
          timerInfo = 'NOW!';
        }

        // 화면상 아이템 개수 표시 (있을 경우에만)
        const countInfo = itemCount > 0 ? `(${itemCount})` : '';
        
        itemDescriptions.push(`${itemIcon}${itemName}${countInfo}:${timerInfo}`);
      });

      // 최종 UI 텍스트 구성 - 2줄로 표시
      const totalInfo = `Active Items: ${totalActiveItems}`;
      const itemsInfo = itemDescriptions.join(' | ');
      
      this.itemDescriptionUI.setText(`${totalInfo}\n${itemsInfo}`);
    }

    private updateShieldEffect(item: Phaser.GameObjects.Rectangle) {
      if (!this.player || !this.shieldGraphics) return;

      const itemDuration = item.getData('duration');
      if (this.time.now > itemDuration) {
        this.hasShield = false;
        this.shieldGraphics.destroy();
        this.shieldGraphics = null;
        item.destroy();
        return;
      }

      this.shieldGraphics.clear();
      this.shieldGraphics.fillStyle(0x00ff00); // 초록색
      this.shieldGraphics.beginPath();
      this.shieldGraphics.moveTo(this.player!.x - 15, this.player!.y - 10);
      this.shieldGraphics.lineTo(this.player!.x - 15 - 10, this.player!.y);
      this.shieldGraphics.lineTo(this.player!.x - 15, this.player!.y + 10);
      this.shieldGraphics.closePath();
      this.shieldGraphics.fillPath();
    }

    private useUltimate() {
      if (this.ultimateCount <= 0) return;

      this.ultimateCount--;
      this.updateItemsDisplay();

      // 모든 몬스터에게 2 데미지
      this.enemies?.children.entries.forEach(enemy => {
        const enemyObj = enemy as Phaser.GameObjects.Rectangle;
        const currentHealth = enemyObj.getData('health') || 1;
        enemyObj.setData('health', currentHealth - 2);
        
        if (enemyObj.getData('health') <= 0) {
          this.score += 50;
          this.enemies?.remove(enemyObj);
          enemyObj.destroy();
          this.createExplosion(enemyObj.x, enemyObj.y);
        }
      });

      // 보스에게도 2 데미지
      if (this.boss && this.isBossStage) {
        this.bossCurrentHealth = Math.max(0, this.bossCurrentHealth - 2);
        this.updateBossHealthDisplay();
        
        if (this.bossCurrentHealth <= 0) {
          this.defeatBoss();
        }
      }

      this.scoreText?.setText(`Score: ${this.score}`);

      // 궁극기 시각 효과
      this.createUltimateEffect();
    }

    private createUltimateEffect() {
      // 화면 전체에 궁극기 효과
      const effectGraphics = this.add.graphics();
      effectGraphics.fillStyle(0xff0000, 0.3);
      effectGraphics.fillRect(0, 0, GAME_WIDTH, GAME_HEIGHT);
      
      this.time.delayedCall(200, () => {
        effectGraphics.destroy();
      });
    }

    private fireChargedBullet() {
      if (!this.player || !this.bullets) return;

      // 탄 강화 레벨에 따른 차지 공격 강화
      const baseChargedBullets = 5;
      const upgradeBonusBullets = (this.bulletUpgrade - 1) * 2; // 레벨당 2발씩 추가
      const totalChargedBullets = baseChargedBullets + upgradeBonusBullets;
      
      // 탄 강화 레벨에 따른 데미지 증가
      const baseDamage = 5;
      const upgradeDamageBonus = this.bulletUpgrade * 2; // 레벨당 +2 데미지
      const chargedDamage = baseDamage + upgradeDamageBonus;
      
      // 탄 강화 레벨에 따른 총알 크기 증가
      const baseSize = Math.max(6, Math.min(12, GAME_WIDTH / 100));
      const sizeMultiplier = 1 + (this.bulletUpgrade * 0.3); // 레벨당 30% 크기 증가
      const bulletSize = baseSize * sizeMultiplier;
      
      // 탄 강화 레벨에 따른 속도 증가
      const baseSpeed = Math.max(10, Math.min(15, GAME_WIDTH / 50));
      const speedBonus = this.bulletUpgrade * 2; // 레벨당 +2 속도
      const bulletSpeed = baseSpeed + speedBonus;
      
      // 탄 강화 레벨에 따른 확산 범위 조정
      const baseSpread = 25;
      const spreadMultiplier = 1 + (this.bulletUpgrade * 0.2); // 레벨당 20% 범위 증가
      const spreadRange = baseSpread * spreadMultiplier;
      
      console.log(`Charged attack: Level ${this.bulletUpgrade}, ${totalChargedBullets} bullets, ${chargedDamage} damage, ${bulletSpeed} speed`);
      
      // 강화된 차지 총알 발사
      for (let i = 0; i < totalChargedBullets; i++) {
        const spread = (i - (totalChargedBullets - 1) / 2) * spreadRange / totalChargedBullets;
        
        const bullet = this.add.rectangle(
          this.player.x + 25, 
          this.player.y + spread, 
          bulletSize * 4, 
          bulletSize * 2, 
          this.getChargedBulletColor() // 레벨별 색상
        );
        
        bullet.setData('speed', bulletSpeed);
        bullet.setData('damage', chargedDamage);
        bullet.setData('charged', true);
        bullet.setData('upgradeLevel', this.bulletUpgrade);
        this.bullets.add(bullet);
      }

      // 탄 강화 레벨에 따른 강화된 차지 어택 시각 효과
      this.createEnhancedChargeEffect();
    }

    private getChargedBulletColor(): number {
      // 탄 강화 레벨에 따른 차지 총알 색상 변화
      const colorsByLevel = [
        0x00ffff, // 레벨 1: 청록색 (기본)
        0x00aaff, // 레벨 2: 하늘색
        0x0066ff, // 레벨 3: 파란색
        0x6600ff, // 레벨 4: 보라색
        0xff00ff  // 레벨 5: 마젠타 (최고급)
      ];
      
      const colorIndex = Math.min(this.bulletUpgrade - 1, colorsByLevel.length - 1);
      return colorsByLevel[colorIndex];
    }

    private createEnhancedChargeEffect() {
      if (!this.player) return;

      // 기본 차지 효과
      const chargeEffect = this.add.graphics();
      
      // 탄 강화 레벨에 따른 효과 크기 증가
      const baseEffectSize = 30;
      const sizeMultiplier = 1 + (this.bulletUpgrade * 0.4); // 레벨당 40% 크기 증가
      const effectSize = baseEffectSize * sizeMultiplier;
      
      // 탄 강화 레벨에 따른 효과 색상
      const effectColor = this.getChargedBulletColor();
      const secondaryColor = 0xffffff;
      
      // 메인 폭발 효과 (레벨별 크기 조정)
      chargeEffect.fillStyle(effectColor, 0.6);
      chargeEffect.fillCircle(this.player.x, this.player.y, effectSize);
      chargeEffect.fillStyle(secondaryColor, 0.8);
      chargeEffect.fillCircle(this.player.x, this.player.y, effectSize * 0.7);
      
      // 외곽 링 효과 (레벨별 다중 링)
      const ringCount = Math.min(5, 1 + this.bulletUpgrade); // 레벨당 링 1개 추가
      for (let i = 0; i < ringCount; i++) {
        const ringRadius = effectSize + (i * 15);
        const ringOpacity = 0.8 - (i * 0.15);
        chargeEffect.lineStyle(3 + i, effectColor, ringOpacity);
        chargeEffect.strokeCircle(this.player.x, this.player.y, ringRadius);
      }
      
      // 탄 강화 레벨에 따른 에너지 빔 효과
      const beamCount = Math.min(12, 4 + (this.bulletUpgrade * 2)); // 레벨당 빔 2개 추가
      for (let i = 0; i < beamCount; i++) {
        const angle = (i * (360 / beamCount)) * Math.PI / 180;
        const beamLength = effectSize + (this.bulletUpgrade * 10);
        const beamEndX = this.player.x + Math.cos(angle) * beamLength;
        const beamEndY = this.player.y + Math.sin(angle) * beamLength;
        
        chargeEffect.lineStyle(2 + Math.floor(this.bulletUpgrade / 2), effectColor, 0.7);
        chargeEffect.lineBetween(this.player.x, this.player.y, beamEndX, beamEndY);
      }
      
      // 탄 강화 레벨에 따른 파티클 효과
      const particleCount = Math.min(20, 8 + (this.bulletUpgrade * 3)); // 레벨당 파티클 3개 추가
      for (let i = 0; i < particleCount; i++) {
        const particleAngle = (i * (360 / particleCount)) * Math.PI / 180;
        const particleDistance = effectSize + Phaser.Math.Between(10, 30);
        const particleX = this.player.x + Math.cos(particleAngle) * particleDistance;
        const particleY = this.player.y + Math.sin(particleAngle) * particleDistance;
        
        const particleSize = 3 + Math.floor(this.bulletUpgrade / 2);
        chargeEffect.fillStyle(secondaryColor, 0.9);
        chargeEffect.fillCircle(particleX, particleY, particleSize);
      }
      
      // 레벨별 특수 효과
      if (this.bulletUpgrade >= 3) {
        // 레벨 3 이상: 십자 에너지 방출
        const crossLength = effectSize * 1.5;
        chargeEffect.lineStyle(4, effectColor, 0.8);
        // 수평선
        chargeEffect.lineBetween(this.player.x - crossLength, this.player.y, 
                                 this.player.x + crossLength, this.player.y);
        // 수직선  
        chargeEffect.lineBetween(this.player.x, this.player.y - crossLength, 
                                 this.player.x, this.player.y + crossLength);
      }
      
      if (this.bulletUpgrade >= 5) {
        // 레벨 5: 최고급 오라 효과
        const auraSize = effectSize * 2;
        chargeEffect.fillStyle(effectColor, 0.2);
        chargeEffect.fillCircle(this.player.x, this.player.y, auraSize);
        
        // 회전하는 에너지 오라
        const auraBeamCount = 8;
        for (let i = 0; i < auraBeamCount; i++) {
          const angle = (i * 45 + this.time.now * 0.1) * Math.PI / 180;
          const auraBeamLength = auraSize * 0.8;
          const beamEndX = this.player.x + Math.cos(angle) * auraBeamLength;
          const beamEndY = this.player.y + Math.sin(angle) * auraBeamLength;
          
          chargeEffect.lineStyle(3, 0xff00ff, 0.6);
          chargeEffect.lineBetween(this.player.x, this.player.y, beamEndX, beamEndY);
        }
      }
      
      // 효과 지속 시간 (레벨별 조정)
      const effectDuration = Math.min(500, 200 + (this.bulletUpgrade * 50)); // 레벨당 50ms 추가
      this.time.delayedCall(effectDuration, () => {
        chargeEffect.destroy();
      });
    }

    private updateItemsDisplay() {
      const shieldStatus = this.hasShield ? '🛡️' : '';
      this.itemsUI?.setText(`ULT: ${this.ultimateCount} | LV${this.bulletUpgrade} ${shieldStatus}`);
    }

    private updateLivesDisplay() {
      // 라이프를 우주선 아이콘으로 표시
      let livesDisplay = 'LIVES: ';
      for (let i = 0; i < this.maxLives; i++) {
        if (i < this.lives) {
          livesDisplay += '🚀'; // 살아있는 라이프
        } else {
          livesDisplay += '💥'; // 잃은 라이프
        }
        if (i < this.maxLives - 1) livesDisplay += ' ';
      }
      this.livesText?.setText(livesDisplay);
    }

    private drawLifeIcon(x: number, y: number, isAlive: boolean = true) {
      if (!this.graphics) return;

      const iconSize = 12;
      
      if (isAlive) {
        // 살아있는 우주선 아이콘 (초록색)
        this.graphics.fillStyle(0x00ff00);
        this.graphics.beginPath();
        this.graphics.moveTo(x + iconSize, y); // 앞쪽 끝
        this.graphics.lineTo(x - iconSize * 0.5, y - iconSize * 0.4); // 왼쪽 위
        this.graphics.lineTo(x - iconSize * 0.2, y); // 중간
        this.graphics.lineTo(x - iconSize * 0.5, y + iconSize * 0.4); // 왼쪽 아래
        this.graphics.closePath();
        this.graphics.fillPath();
        
        // 엔진 불꽃
        this.graphics.fillStyle(0xff6600);
        this.graphics.beginPath();
        this.graphics.moveTo(x - iconSize * 0.5, y - iconSize * 0.2);
        this.graphics.lineTo(x - iconSize, y);
        this.graphics.lineTo(x - iconSize * 0.5, y + iconSize * 0.2);
        this.graphics.closePath();
        this.graphics.fillPath();
      } else {
        // 파괴된 우주선 아이콘 (빨간색 X)
        this.graphics.lineStyle(3, 0xff0000);
        this.graphics.beginPath();
        this.graphics.moveTo(x - iconSize * 0.5, y - iconSize * 0.5);
        this.graphics.lineTo(x + iconSize * 0.5, y + iconSize * 0.5);
        this.graphics.moveTo(x + iconSize * 0.5, y - iconSize * 0.5);
        this.graphics.lineTo(x - iconSize * 0.5, y + iconSize * 0.5);
        this.graphics.strokePath();
      }
    }

    private checkStageProgression() {
      // 보스 스테이지이거나 스테이지 전환 중이면 체크하지 않음
      if (this.isBossStage || this.isStageTransition) {
        return;
      }

      const requiredScore = this.stage * 500; // 스테이지마다 500점 필요 (증가)
      if (this.score >= requiredScore) {
        console.log(`Score threshold reached for stage ${this.stage + 1}. Starting boss stage.`);
        this.startBossStage();
      }
    }

    private startBossStage() {
      this.isBossStage = true;
      this.enemies?.clear(true, true); // 기존 적들 제거
      
      // 보스 생성
      this.createBoss();
      
      // 보스 UI 표시
      this.bossHealthText?.setVisible(true);
      this.updateBossHealthDisplay();
    }

    private createBoss() {
      const bossSize = Math.max(80, Math.min(120, GAME_HEIGHT / 8));
      this.boss = this.add.rectangle(GAME_WIDTH - 150, GAME_HEIGHT / 2, bossSize, bossSize, 0x8800ff);
      
      // 보스 체력 설정 - 스테이지별 대폭 증가
      const baseHealth = 30; // 기본 체력 증가
      const stageHealthMultiplier = this.stage * 15; // 스테이지당 15씩 증가
      const exponentialBonus = Math.floor(Math.pow(this.stage, 1.5) * 5); // 지수적 증가 요소
      this.bossMaxHealth = baseHealth + stageHealthMultiplier + exponentialBonus;
      this.bossCurrentHealth = this.bossMaxHealth;
      this.bossDirection = 1;
      this.bossLastShot = 0;
      
      console.log(`Stage ${this.stage}: Boss created with ${this.bossMaxHealth} HP (Base: ${baseHealth}, Stage: ${stageHealthMultiplier}, Exponential: ${exponentialBonus})`);
      this.updateBossHealthDisplay();
    }

    private updateBoss(time: number) {
      if (!this.boss) return;

      // 보스 이동 (위아래) - 스테이지별 속도 대폭 증가
      const baseSpeed = 2;
      const stageSpeedBonus = Math.floor(this.stage * 1.5); // 스테이지당 1.5배 속도 증가
      const bossSpeed = baseSpeed + stageSpeedBonus;
      this.boss.y += this.bossDirection * bossSpeed;

      // 화면 경계에서 방향 전환
      if (this.boss.y <= 80 || this.boss.y >= GAME_HEIGHT - 80) {
        this.bossDirection *= -1;
      }

      // 보스 미사일 발사 - 스테이지별 공격속도 대폭 증가
      const baseShootInterval = 800; // 기본 간격 감소
      const stageIntervalReduction = Math.min(600, this.stage * 60); // 스테이지당 60ms 감소, 최대 600ms 감소
      const shootInterval = Math.max(200, baseShootInterval - stageIntervalReduction); // 최소 200ms
      
      if (time > this.bossLastShot + shootInterval) {
        this.fireBossBullet();
        this.bossLastShot = time;
      }

      // 보스 그리기
      this.drawBoss();
    }

    private drawBoss() {
      if (!this.boss || !this.graphics) return;

      // 보스 메인 바디 (더 위협적이고 악당스러운 디자인)
      const centerX = this.boss.x;
      const centerY = this.boss.y;
      const size = 40 + (this.stage * 4); // 스테이지별 크기 증가
      const pulse = Math.sin(this.time.now * 0.005) * 0.3 + 0.7;
      const healthPercent = this.bossCurrentHealth / this.bossMaxHealth;

      // 보스 외곽 장갑 (어두운 보라색/검은색)
      this.graphics.fillStyle(Phaser.Display.Color.GetColor(80 * pulse, 0, 120 * pulse));
      this.graphics.beginPath();
      
      // 12각형으로 더 복잡하고 위협적으로
      for (let i = 0; i < 12; i++) {
        const angle = (i * 30) * Math.PI / 180;
        const outerSize = size + Math.sin(this.time.now * 0.01 + i) * 4; // 각 면마다 독립적인 펄스
        const x = centerX + Math.cos(angle) * outerSize;
        const y = centerY + Math.sin(angle) * outerSize;
        
        if (i === 0) this.graphics.moveTo(x, y);
        else this.graphics.lineTo(x, y);
      }
      this.graphics.closePath();
      this.graphics.fillPath();

      // 보스 중간 장갑 레이어 (메탈릭)
      this.graphics.fillStyle(Phaser.Display.Color.GetColor(150 * pulse, 150 * pulse, 180 * pulse));
      this.graphics.beginPath();
      for (let i = 0; i < 8; i++) {
        const angle = (i * 45 + this.time.now * 0.02) * Math.PI / 180; // 회전 효과
        const x = centerX + Math.cos(angle) * (size * 0.8);
        const y = centerY + Math.sin(angle) * (size * 0.8);
        if (i === 0) this.graphics.moveTo(x, y);
        else this.graphics.lineTo(x, y);
      }
      this.graphics.closePath();
      this.graphics.fillPath();

      // 보스 내부 장갑 (어두운 빨강)
      this.graphics.fillStyle(Phaser.Display.Color.GetColor(120 * pulse, 0, 0));
      this.graphics.beginPath();
      for (let i = 0; i < 6; i++) {
        const angle = (i * 60) * Math.PI / 180;
        const x = centerX + Math.cos(angle) * (size * 0.6);
        const y = centerY + Math.sin(angle) * (size * 0.6);
        if (i === 0) this.graphics.moveTo(x, y);
        else this.graphics.lineTo(x, y);
      }
      this.graphics.closePath();
      this.graphics.fillPath();

      // 보스 코어 (위협적인 빨간 눈)
      const coreSize = 15 + Math.floor(this.stage / 2);
      this.graphics.fillStyle(Phaser.Display.Color.GetColor(255, 0, 0));
      this.graphics.fillCircle(centerX, centerY, coreSize);
      
      // 코어 내부 펄스 (더 위협적)
      const corePulse = Math.sin(this.time.now * 0.01) * 0.5 + 0.5;
      this.graphics.fillStyle(Phaser.Display.Color.GetColor(255, 50 * corePulse, 0));
      this.graphics.fillCircle(centerX, centerY, coreSize * 0.7);
      
      // 코어 중심 (하얀 광선)
      this.graphics.fillStyle(Phaser.Display.Color.GetColor(255, 255, 255));
      this.graphics.fillCircle(centerX, centerY, coreSize * 0.3);

      // 보스 주무기 시스템 (대형 포탑들)
      this.graphics.fillStyle(0x333333);
      // 상단 대형 포탑
      this.graphics.fillRect(centerX - size, centerY - 20, 25, 20);
      // 하단 대형 포탑  
      this.graphics.fillRect(centerX - size, centerY, 25, 20);
      // 중앙 메인 캐논
      this.graphics.fillRect(centerX - size - 15, centerY - 8, 20, 16);
      
      // 포탑 무기구 (빨간 레이저 포인트)
      this.graphics.fillStyle(0xff0000);
      this.graphics.fillCircle(centerX - size + 5, centerY - 10, 3);
      this.graphics.fillCircle(centerX - size + 5, centerY + 10, 3);
      this.graphics.fillCircle(centerX - size - 5, centerY, 4); // 메인 캐논

      // 보조 무기 시스템 (미사일 런처)
      this.graphics.fillStyle(0x444444);
      for (let i = 0; i < 4; i++) {
        const angle = (i * 90) * Math.PI / 180;
        const weaponX = centerX + Math.cos(angle) * (size * 0.7);
        const weaponY = centerY + Math.sin(angle) * (size * 0.7);
        this.graphics.fillRect(weaponX - 3, weaponY - 3, 6, 6);
      }

      // 보스 엔진 시스템 (더 강력하고 위협적)
      this.graphics.fillStyle(Phaser.Display.Color.GetColor(255, 80 * pulse, 0));
      this.graphics.beginPath();
      this.graphics.moveTo(centerX - size, centerY - 30);
      this.graphics.lineTo(centerX - size - 40, centerY - 15);
      this.graphics.lineTo(centerX - size - 50, centerY);
      this.graphics.lineTo(centerX - size - 40, centerY + 15);
      this.graphics.lineTo(centerX - size, centerY + 30);
      this.graphics.closePath();
      this.graphics.fillPath();

      // 내부 엔진 불꽃 (더 강렬한 효과)
      this.graphics.fillStyle(Phaser.Display.Color.GetColor(255, 150 * pulse, 0));
      this.graphics.beginPath();
      this.graphics.moveTo(centerX - size, centerY - 20);
      this.graphics.lineTo(centerX - size - 30, centerY - 8);
      this.graphics.lineTo(centerX - size - 40, centerY);
      this.graphics.lineTo(centerX - size - 30, centerY + 8);
      this.graphics.lineTo(centerX - size, centerY + 20);
      this.graphics.closePath();
      this.graphics.fillPath();

      // 최내부 엔진 코어
      this.graphics.fillStyle(0xffffff);
      this.graphics.beginPath();
      this.graphics.moveTo(centerX - size, centerY - 10);
      this.graphics.lineTo(centerX - size - 20, centerY);
      this.graphics.lineTo(centerX - size, centerY + 10);
      this.graphics.closePath();
      this.graphics.fillPath();

      // 보스 체력에 따른 강화된 데미지 효과
      if (healthPercent < 0.6) {
        // 체력이 60% 이하일 때 더 많은 스파크
        for (let i = 0; i < 5; i++) {
          const sparkX = centerX + Phaser.Math.Between(-size, size);
          const sparkY = centerY + Phaser.Math.Between(-size, size);
          this.graphics.fillStyle(0xffff00);
          this.graphics.fillCircle(sparkX, sparkY, 3);
        }
      }

      if (healthPercent < 0.3) {
        // 체력이 30% 이하일 때 연기와 화염
        this.graphics.fillStyle(0x444444, 0.5);
        this.graphics.fillCircle(centerX + 15, centerY - 20, 10);
        this.graphics.fillCircle(centerX - 10, centerY + 15, 8);
        
        this.graphics.fillStyle(0xff4400, 0.7);
        this.graphics.fillCircle(centerX + 10, centerY - 15, 6);
        this.graphics.fillCircle(centerX - 5, centerY + 10, 5);
      }

      // 위협적인 에너지 오라 (스테이지와 체력에 따라 변화)
      const auraIntensity = 0.4 + (this.stage * 0.1) + ((1 - healthPercent) * 0.3);
      const auraColor = healthPercent > 0.5 ? 0xff0000 : 0xff4400; // 체력 낮으면 주황색
      
      this.graphics.lineStyle(3, auraColor, auraIntensity * pulse);
      this.graphics.strokeCircle(centerX, centerY, size + 8);
      this.graphics.lineStyle(2, auraColor, auraIntensity * pulse * 0.7);
      this.graphics.strokeCircle(centerX, centerY, size + 15);
      
      // 위협적인 에너지 방출 (저체력 시)
      if (healthPercent < 0.2) {
        for (let i = 0; i < 8; i++) {
          const beamAngle = (i * 45 + this.time.now * 0.1) * Math.PI / 180;
          const beamLength = 20 + Math.sin(this.time.now * 0.02 + i) * 10;
          const beamX = centerX + Math.cos(beamAngle) * (size + beamLength);
          const beamY = centerY + Math.sin(beamAngle) * (size + beamLength);
          
          this.graphics.lineStyle(2, 0xff0000, 0.8);
          this.graphics.lineBetween(centerX, centerY, beamX, beamY);
        }
      }
    }

    private fireBossBullet() {
      if (!this.boss || !this.bossBullets || !this.player) return;

      // 스테이지별 미사일 개수 및 속도 증가
      const baseMissileCount = 1;
      const stageMissileBonus = Math.min(5, Math.floor(this.stage / 2)); // 2스테이지마다 미사일 1개 추가, 최대 5개
      const missileCount = baseMissileCount + stageMissileBonus;
      
      const baseSpeed = 4;
      const stageSpeedBonus = Math.floor(this.stage * 0.8); // 스테이지당 0.8배 속도 증가
      const missileSpeed = baseSpeed + stageSpeedBonus;
      
      // 여러 미사일 발사 (부채꼴 패턴)
      for (let i = 0; i < missileCount; i++) {
        let targetX = this.player.x;
        let targetY = this.player.y;
        
        if (missileCount > 1) {
          // 여러 미사일일 때는 플레이어 주변으로 분산 발사
          const spreadAngle = (missileCount - 1) * 15; // 총 확산 각도
          const angleStep = spreadAngle / (missileCount - 1);
          const currentAngle = -spreadAngle / 2 + (i * angleStep);
          
          // 플레이어 위치에서 각도만큼 오프셋
          const distance = 100;
          targetX += Math.cos(currentAngle * Math.PI / 180) * distance;
          targetY += Math.sin(currentAngle * Math.PI / 180) * distance;
        }
        
        const angle = Phaser.Math.Angle.Between(this.boss.x, this.boss.y, targetX, targetY);
        
        // 미사일 크기도 스테이지별 증가
        const missileSize = Math.max(6, Math.min(16, 8 + this.stage));
        const bullet = this.add.rectangle(this.boss.x - 30, this.boss.y, missileSize, missileSize * 0.7, 0xff3300);
        
        bullet.setData('speedX', Math.cos(angle) * missileSpeed);
        bullet.setData('speedY', Math.sin(angle) * missileSpeed);
        bullet.setData('damage', 1);
        bullet.setData('stage', this.stage); // 스테이지 정보 저장
        
        this.bossBullets.add(bullet);
      }
      
      console.log(`Stage ${this.stage}: Boss fired ${missileCount} missiles at speed ${missileSpeed}`);
    }

    private updateBossBullets() {
      if (!this.bossBullets) return;

      this.bossBullets.children.entries.forEach(bullet => {
        const bulletObj = bullet as Phaser.GameObjects.Rectangle;
        bulletObj.x += bulletObj.getData('speedX');
        bulletObj.y += bulletObj.getData('speedY');

        // 화면 밖으로 나간 미사일 제거
        if (bulletObj.x < -50 || bulletObj.x > GAME_WIDTH + 50 || 
            bulletObj.y < -50 || bulletObj.y > GAME_HEIGHT + 50) {
          this.bossBullets?.remove(bulletObj);
          bulletObj.destroy();
        }
      });
    }

    private defeatBoss() {
      if (!this.boss) return;
      
      console.log(`Boss defeated on stage ${this.stage}!`);
      
      // 보스 처치 점수
      this.score += 300 * this.stage;
      this.scoreText?.setText(`Score: ${this.score}`);
      
      // 폭발 이펙트
      this.createExplosion(this.boss.x, this.boss.y);
      
      // 보스 제거
      this.clearBoss();
      
      // 다음 스테이지로 즉시 진행
      this.nextStage();
    }

    private clearBoss() {
      if (this.boss) {
        this.boss.destroy();
        this.boss = null;
      }
      this.bossBullets?.clear(true, true);
      this.bossHealthText?.setVisible(false);
      this.bossHealthBar?.clear();
    }

    private nextStage() {
      this.stage++;
      this.level++;
      this.isBossStage = false;
      this.isStageTransition = true;
      this.stageTransitionTimer = this.time.now + 2000; // 2초 대기
      
      this.stageText?.setText(`Stage: ${this.stage}`);
      
      // 스테이지 클리어 메시지
      const stageCompleteText = this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2, `STAGE ${this.stage - 1} COMPLETE!`, {
        fontSize: Math.max(24, Math.min(36, GAME_WIDTH / 25)) + 'px',
        color: '#00ff00',
        fontFamily: 'Courier New, monospace',
        stroke: '#003300',
        strokeThickness: 3,
        shadow: {
          offsetX: 3,
          offsetY: 3,
          color: '#000000',
          blur: 8,
          stroke: true,
          fill: true
        }
      }).setOrigin(0.5);

      const nextStageText = this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2 + 40, `NEXT STAGE: ${this.stage}`, {
        fontSize: Math.max(16, Math.min(24, GAME_WIDTH / 35)) + 'px',
        color: '#ffff00',
        fontFamily: 'Courier New, monospace',
        stroke: '#333300',
        strokeThickness: 3,
        shadow: {
          offsetX: 3,
          offsetY: 3,
          color: '#000000',
          blur: 8,
          stroke: true,
          fill: true
        }
      }).setOrigin(0.5);

      // 2초 후 텍스트 제거
      this.time.delayedCall(2000, () => {
        stageCompleteText.destroy();
        nextStageText.destroy();
      });
    }

    private handleStageTransition(time: number) {
      if (time > this.stageTransitionTimer) {
        this.isStageTransition = false;
        // 새 스테이지 준비
        this.enemies?.clear(true, true);
      }
    }

    private updateBossHealthDisplay() {
      this.bossHealthText?.setText(`BOSS HP: ${this.bossCurrentHealth}/${this.bossMaxHealth}`);
    }

    private drawBossHealthBar() {
      if (!this.bossHealthBar || !this.isBossStage) return;

      this.bossHealthBar.clear();
      
      const barWidth = 300;
      const barHeight = 20;
      const x = (GAME_WIDTH - barWidth) / 2;
      const y = 50;
      
      // 배경 (검은색)
      this.bossHealthBar.fillStyle(0x000000);
      this.bossHealthBar.fillRect(x, y, barWidth, barHeight);
      
      // 체력 바 (빨간색)
      const healthPercent = Math.max(0, this.bossCurrentHealth / this.bossMaxHealth);
      this.bossHealthBar.fillStyle(0xff0000);
      this.bossHealthBar.fillRect(x + 2, y + 2, (barWidth - 4) * healthPercent, barHeight - 4);
      
      // 테두리 (하얀색)
      this.bossHealthBar.lineStyle(2, 0xffffff);
      this.bossHealthBar.strokeRect(x, y, barWidth, barHeight);
    }

    private createExplosion(x: number, y: number) {
      if (!this.graphics) return;

      // 간단한 폭발 이펙트
      const explosionSize = Math.max(15, Math.min(30, GAME_WIDTH / 40));
      const explosion = this.add.circle(x, y, explosionSize, 0xff8800, 0.8);
      
      this.tweens.add({
        targets: explosion,
        scaleX: 2,
        scaleY: 2,
        alpha: 0,
        duration: 300,
        onComplete: () => {
          explosion.destroy();
        }
      });
    }

    private endGame() {
      this.gameOver = true;

      // 게임 오버 오버레이
      const overlay = this.add.rectangle(GAME_WIDTH / 2, GAME_HEIGHT / 2, GAME_WIDTH, GAME_HEIGHT, 0x000000, 0.7);

      // 게임 오버 텍스트
      this.gameOverText = this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2 - 50, 'GAME OVER', {
        fontSize: Math.max(24, Math.min(48, GAME_WIDTH / 20)) + 'px',
        color: '#ff0000',
        fontFamily: 'Courier New, monospace',
        stroke: '#330000',
        strokeThickness: 3,
        shadow: {
          offsetX: 3,
          offsetY: 3,
          color: '#000000',
          blur: 8,
          stroke: true,
          fill: true
        }
      }).setOrigin(0.5);

      this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2, `Final Score: ${this.score}`, {
        fontSize: Math.max(16, Math.min(24, GAME_WIDTH / 35)) + 'px',
        color: '#ffffff',
        fontFamily: 'Courier New, monospace',
        stroke: '#003300',
        strokeThickness: 2,
        shadow: {
          offsetX: 2,
          offsetY: 2,
          color: '#000000',
          blur: 6,
          stroke: true,
          fill: true
        }
      }).setOrigin(0.5);

      this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2 + 40, `Stage Reached: ${this.stage}`, {
        fontSize: Math.max(14, Math.min(20, GAME_WIDTH / 40)) + 'px',
        color: '#00ff00',
        fontFamily: 'Courier New, monospace',
        stroke: '#003300',
        strokeThickness: 2,
        shadow: {
          offsetX: 2,
          offsetY: 2,
          color: '#000000',
          blur: 6,
          stroke: true,
          fill: true
        }
      }).setOrigin(0.5);

      this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2 + 80, 'Press SPACE to restart', {
        fontSize: Math.max(12, Math.min(16, GAME_WIDTH / 50)) + 'px',
        color: '#00ffff',
        fontFamily: 'Courier New, monospace',
        stroke: '#003333',
        strokeThickness: 2,
        shadow: {
          offsetX: 2,
          offsetY: 2,
          color: '#000000',
          blur: 6,
          stroke: true,
          fill: true
        }
      }).setOrigin(0.5);
    }

    private handleGameOverInput() {
      if (this.spaceKey?.isDown) {
        this.restartGame();
      }
    }

    private restartGame() {
      // 씬 재시작
      this.scene.restart();
    }

    private checkCollisions() {
      if (!this.player || !this.bullets || !this.enemies) return;

      // 총알과 적 충돌
      this.bullets.children.entries.forEach(bullet => {
        const bulletObj = bullet as Phaser.GameObjects.Rectangle;
        
        this.enemies?.children.entries.forEach(enemy => {
          const enemyObj = enemy as Phaser.GameObjects.Rectangle;
          
          if (Phaser.Geom.Rectangle.Overlaps(bulletObj.getBounds(), enemyObj.getBounds())) {
            // 적 체력 감소
            const damage = bulletObj.getData('damage') || 1;
            const currentHealth = enemyObj.getData('health') || 1;
            const newHealth = currentHealth - damage;
            
            enemyObj.setData('health', newHealth);
            
            // 총알 제거
            if (this.bullets) {
              this.bullets.remove(bulletObj);
              bulletObj.destroy();
            }
            
            // 적 처치
            if (newHealth <= 0) {
              this.score += 25 * this.stage; // 스테이지별 점수 증가
              this.scoreText?.setText(`Score: ${this.score}`);
              
              if (this.enemies) {
                this.enemies.remove(enemyObj);
                enemyObj.destroy();
                this.createExplosion(enemyObj.x, enemyObj.y);
              }
            }
          }
        });
      });

      // 플레이어와 적 충돌
      this.enemies.children.entries.forEach(enemy => {
        const enemyObj = enemy as Phaser.GameObjects.Rectangle;
        
        if (Phaser.Geom.Rectangle.Overlaps(this.player!.getBounds(), enemyObj.getBounds())) {
          // 보호막이 있으면 보호막만 제거
          if (this.hasShield) {
            this.hasShield = false;
            this.shieldGraphics?.destroy();
            this.shieldGraphics = null;
            this.updateItemsDisplay();
          } else {
            // 생명 감소
            this.lives--;
            this.updateLivesDisplay();
            
            // 무적 시간 (깜빡임 효과)
            this.playerBlinkTimer = 60; // 1초간 깜빡임
          }
          
          // 적 제거
          if (this.enemies) {
            this.enemies.remove(enemyObj);
            enemyObj.destroy();
            this.createExplosion(enemyObj.x, enemyObj.y);
          }
          
          // 게임 오버 체크
          if (this.lives <= 0) {
            this.endGame();
          }
        }
      });

      // 보스 미사일과 플레이어 충돌 (보스 스테이지일 때만)
      if (this.isBossStage && this.bossBullets) {
        this.bossBullets.children.entries.forEach(bullet => {
          const bulletObj = bullet as Phaser.GameObjects.Rectangle;
          
          if (this.player && Phaser.Geom.Rectangle.Overlaps(this.player.getBounds(), bulletObj.getBounds())) {
            // 보호막이 있으면 보호막만 제거
            if (this.hasShield) {
              this.hasShield = false;
              this.shieldGraphics?.destroy();
              this.shieldGraphics = null;
              this.updateItemsDisplay();
            } else {
              // 플레이어 라이프 감소
              this.lives--;
              this.updateLivesDisplay();
              
              // 무적 시간
              this.playerBlinkTimer = 60;
            }
            
            // 미사일 제거
            if (this.bossBullets) {
              this.bossBullets.remove(bulletObj);
              bulletObj.destroy();
            }
            
            // 폭발 이펙트
            if (this.player) {
              this.createExplosion(this.player.x, this.player.y);
            }
            
            // 게임 오버 체크
            if (this.lives <= 0) {
              this.endGame();
            }
          }
        });
      }
    }

    private checkBossCollisions() {
      if (!this.player || !this.bullets || !this.boss || !this.bossBullets || !this.isBossStage) return;

      // 플레이어 총알과 보스 충돌
      this.bullets.children.entries.forEach(bullet => {
        const bulletObj = bullet as Phaser.GameObjects.Rectangle;
        
        // 보스가 아직 존재하는지 다시 확인
        if (!this.boss) return;
        
        if (Phaser.Geom.Rectangle.Overlaps(this.boss.getBounds(), bulletObj.getBounds())) {
          // 보스 체력 감소
          const damage = bulletObj.getData('damage') || 1;
          this.bossCurrentHealth = Math.max(0, this.bossCurrentHealth - damage);
          this.updateBossHealthDisplay();
          
          // 보스 타격 효과 추가
          this.createBossHitEffect(this.boss.x, this.boss.y, damage);
          
          // 총알 제거
          if (this.bullets) {
            this.bullets.remove(bulletObj);
            bulletObj.destroy();
          }
          
          // 점수 증가
          this.score += 10;
          this.scoreText?.setText(`Score: ${this.score}`);
          
          // 보스 처치 체크 (보스가 아직 존재할 때만)
          if (this.boss && this.bossCurrentHealth <= 0) {
            this.defeatBoss();
            return; // 보스가 처치되면 더 이상 충돌 체크하지 않음
          }
        }
      });
    }

    private checkItemCollisions() {
      if (!this.player || !this.items) return;

      this.items.children.entries.forEach(item => {
        const itemObj = item as Phaser.GameObjects.Rectangle;
        
        if (Phaser.Geom.Rectangle.Overlaps(this.player!.getBounds(), itemObj.getBounds())) {
          this.collectItem(itemObj);
        }
      });
    }

    private collectItem(item: Phaser.GameObjects.Rectangle) {
      const type = item.getData('type');
      
      switch (type) {
        case 'bulletUpgrade':
          if (this.bulletUpgrade < 5) { // 최대 5레벨
            this.bulletUpgrade++;
          }
          break;
          
        case 'ultimate':
          if (this.ultimateCount < 3) { // 최대 3개
            this.ultimateCount++;
          }
          break;
          
        case 'health':
          if (this.lives < this.maxLives) { // 최대 체력까지만
            this.lives++;
            this.updateLivesDisplay();
          }
          break;
          
        case 'shield':
          if (!this.hasShield) { // 이미 보호막이 있으면 무시
            this.hasShield = true;
            this.createShieldEffect();
          }
          break;
      }
      
      this.updateItemsDisplay();
      
      // 연결된 라벨 텍스트 제거
      const labelText = item.getData('labelText') as Phaser.GameObjects.Text;
      if (labelText) {
        labelText.destroy();
      }
      
      // 아이템 제거
      this.items?.remove(item);
      item.destroy();
      
      // 수집 효과
      this.createCollectEffect(item.x, item.y);
    }

    private createShieldEffect() {
      if (this.shieldGraphics) {
        this.shieldGraphics.destroy();
      }
      
      this.shieldGraphics = this.add.graphics();
      this.updateShieldVisual();
    }

    private updateShieldVisual() {
      if (!this.shieldGraphics || !this.player) return;

      this.shieldGraphics.clear();
      
      const shieldRadius = 30;
      const time = this.time.now * 0.01;
      const pulse = Math.sin(time) * 0.3 + 0.7;
      
      // 외곽 에너지 실드 (육각형 패턴)
      this.shieldGraphics.lineStyle(3, 0x00ff88, 0.8 * pulse);
      
      // 메인 실드 원
      this.shieldGraphics.strokeCircle(this.player.x, this.player.y, shieldRadius);
      
      // 육각형 에너지 패턴
      this.shieldGraphics.lineStyle(2, 0x44ffaa, 0.6 * pulse);
      this.shieldGraphics.beginPath();
      for (let i = 0; i < 6; i++) {
        const angle = (i * 60) * Math.PI / 180;
        const x = this.player.x + Math.cos(angle) * shieldRadius;
        const y = this.player.y + Math.sin(angle) * shieldRadius;
        
        if (i === 0) this.shieldGraphics.moveTo(x, y);
        else this.shieldGraphics.lineTo(x, y);
      }
      this.shieldGraphics.closePath();
      this.shieldGraphics.strokePath();
      
      // 내부 에너지 그리드
      for (let ring = 1; ring <= 2; ring++) {
        const innerRadius = shieldRadius * (0.4 + ring * 0.2);
        this.shieldGraphics.lineStyle(1, 0x88ffcc, 0.4 * pulse);
        this.shieldGraphics.strokeCircle(this.player.x, this.player.y, innerRadius);
      }
      
      // 에너지 노드 (실드 강화점)
      this.shieldGraphics.fillStyle(0x00ffaa, 0.9 * pulse);
      for (let i = 0; i < 6; i++) {
        const angle = (i * 60 + time * 20) * Math.PI / 180; // 회전 효과
        const nodeX = this.player.x + Math.cos(angle) * shieldRadius;
        const nodeY = this.player.y + Math.sin(angle) * shieldRadius;
        this.shieldGraphics.fillCircle(nodeX, nodeY, 3);
      }
      
      // 중앙 에너지 코어
      this.shieldGraphics.fillStyle(0x66ffaa, 0.5 * pulse);
      this.shieldGraphics.fillCircle(this.player.x, this.player.y, 8);
      this.shieldGraphics.fillStyle(0xaaffcc, 0.8 * pulse);
      this.shieldGraphics.fillCircle(this.player.x, this.player.y, 4);
      
      // 실드 파티클 효과
      for (let i = 0; i < 8; i++) {
        const particleAngle = (i * 45 + time * 30) * Math.PI / 180;
        const particleDistance = shieldRadius + Math.sin(time * 2 + i) * 5;
        const particleX = this.player.x + Math.cos(particleAngle) * particleDistance;
        const particleY = this.player.y + Math.sin(particleAngle) * particleDistance;
        
        this.shieldGraphics.fillStyle(0x44ff88, 0.6);
        this.shieldGraphics.fillCircle(particleX, particleY, 2);
      }
    }

    private createCollectEffect(x: number, y: number) {
      const effectGraphics = this.add.graphics();
      effectGraphics.fillStyle(0xffff00, 0.8);
      effectGraphics.fillCircle(x, y, 15);
      
      this.time.delayedCall(150, () => {
        effectGraphics.destroy();
      });
    }

    private drawEnhancedItem(item: Phaser.GameObjects.Rectangle) {
      if (!this.graphics) return;

      const type = item.getData('type');
      let animTimer = item.getData('animTimer') || 0;
      animTimer += 0.15; // 더 빠른 애니메이션
      item.setData('animTimer', animTimer);

      const x = item.x;
      const y = item.y;
      const pulse = Math.sin(animTimer) * 0.4 + 0.8; // 더 강한 펄스 효과
      const rotate = animTimer * 0.3; // 회전 효과

      // 아이템별 강화된 모양과 색상으로 재디자인
      switch (type) {
        case 'bulletUpgrade':
          // 초록색 다이아몬드 (총알 업그레이드)
          this.graphics.fillStyle(Phaser.Display.Color.GetColor(0, 255 * pulse, 0));
          this.graphics.beginPath();
          this.graphics.moveTo(x, y - 15 * pulse);
          this.graphics.lineTo(x + 12 * pulse, y);
          this.graphics.lineTo(x, y + 15 * pulse);
          this.graphics.lineTo(x - 12 * pulse, y);
          this.graphics.closePath();
          this.graphics.fillPath();
          
          // 내부 하이라이트 (십자 패턴)
          this.graphics.fillStyle(0xaaffaa);
          this.graphics.fillRect(x - 2, y - 8, 4, 16);
          this.graphics.fillRect(x - 8, y - 2, 16, 4);
          
          // 외곽 글로우
          this.graphics.lineStyle(3, 0x44ff44, 0.6 * pulse);
          this.graphics.strokeRect(x - 18, y - 18, 36, 36);
          break;

        case 'ultimate':
          // 빨간색 폭발 별 (궁극기)
          this.graphics.fillStyle(Phaser.Display.Color.GetColor(255 * pulse, 50, 0));
          this.graphics.beginPath();
          for (let i = 0; i < 8; i++) { // 8개 끝점
            const angle = (i * 45 + rotate * 30) * Math.PI / 180;
            const radius = i % 2 === 0 ? 16 * pulse : 8;
            const px = x + Math.cos(angle) * radius;
            const py = y + Math.sin(angle) * radius;
            
            if (i === 0) this.graphics.moveTo(px, py);
            else this.graphics.lineTo(px, py);
          }
          this.graphics.closePath();
          this.graphics.fillPath();
          
          // 중앙 코어
          this.graphics.fillStyle(0xffaa00);
          this.graphics.fillCircle(x, y, 6 * pulse);
          this.graphics.fillStyle(0xffffff);
          this.graphics.fillCircle(x, y, 3);
          
          // 외곽 글로우
          this.graphics.lineStyle(3, 0xff4444, 0.8 * pulse);
          this.graphics.strokeCircle(x, y, 20);
          break;

        case 'health':
          // 파란색 의료 십자가 (체력)
          this.graphics.fillStyle(Phaser.Display.Color.GetColor(50, 150, 255 * pulse));
          // 메인 십자가 (더 두껍게)
          this.graphics.fillRoundedRect(x - 12, y - 4, 24, 8, 2); // 가로
          this.graphics.fillRoundedRect(x - 4, y - 12, 8, 24, 2); // 세로
          
          // 하이라이트 십자가
          this.graphics.fillStyle(0xaaccff);
          this.graphics.fillRoundedRect(x - 10, y - 3, 20, 6, 2);
          this.graphics.fillRoundedRect(x - 3, y - 10, 6, 20, 2);
          
          // 중앙 하트 마크
          this.graphics.fillStyle(0xff6666);
          this.graphics.fillCircle(x - 3, y - 2, 3);
          this.graphics.fillCircle(x + 3, y - 2, 3);
          this.graphics.beginPath();
          this.graphics.moveTo(x - 6, y);
          this.graphics.lineTo(x, y + 6);
          this.graphics.lineTo(x + 6, y);
          this.graphics.closePath();
          this.graphics.fillPath();
          
          // 외곽 글로우
          this.graphics.lineStyle(3, 0x6699ff, 0.7 * pulse);
          this.graphics.strokeRect(x - 16, y - 16, 32, 32);
          break;

        case 'shield':
          // 노란색 방패 (보호막)
          const shieldRotate = Math.sin(animTimer) * 0.1;
          this.graphics.fillStyle(Phaser.Display.Color.GetColor(255 * pulse, 255 * pulse, 0));
          this.graphics.beginPath();
          // 방패 모양 (더 큰 육각형)
          for (let i = 0; i < 6; i++) {
            const angle = (i * 60 + shieldRotate * 10) * Math.PI / 180;
            const radius = i % 2 === 0 ? 14 * pulse : 12;
            const px = x + Math.cos(angle) * radius;
            const py = y + Math.sin(angle) * radius;
            
            if (i === 0) this.graphics.moveTo(px, py);
            else this.graphics.lineTo(px, py);
          }
          this.graphics.closePath();
          this.graphics.fillPath();
          
          // 내부 패턴 (방패 엠블럼)
          this.graphics.fillStyle(0xffff88);
          this.graphics.fillCircle(x, y, 8);
          this.graphics.fillStyle(0xffaa00);
          this.graphics.fillCircle(x, y, 5);
          
          // 방패 라인
          this.graphics.lineStyle(2, 0xff8800, 0.8);
          this.graphics.beginPath();
          this.graphics.moveTo(x, y - 12);
          this.graphics.lineTo(x, y + 12);
          this.graphics.moveTo(x - 10, y);
          this.graphics.lineTo(x + 10, y);
          this.graphics.strokePath();
          
          // 외곽 글로우
          this.graphics.lineStyle(3, 0xffdd44, 0.6 * pulse);
          this.graphics.strokeCircle(x, y, 18);
          break;
      }

      // 공통 효과: 아이템 주변 반짝이는 파티클
      for (let i = 0; i < 4; i++) {
        const particleAngle = (animTimer * 50 + i * 90) * Math.PI / 180;
        const particleDistance = 25 + Math.sin(animTimer + i) * 5;
        const particleX = x + Math.cos(particleAngle) * particleDistance;
        const particleY = y + Math.sin(particleAngle) * particleDistance;
        
        this.graphics.fillStyle(0xffffff, 0.8 * pulse);
        this.graphics.fillCircle(particleX, particleY, 2);
      }
    }

    private drawEnhancedEnemy(enemy: Phaser.GameObjects.Rectangle) {
      if (!this.graphics) return;

      let animTimer = enemy.getData('animTimer') || 0;
      animTimer += 0.15;
      enemy.setData('animTimer', animTimer);

      const x = enemy.x;
      const y = enemy.y;
      const size = Math.max(10, Math.min(15, GAME_HEIGHT / 40));
      const pulse = Math.sin(animTimer) * 0.3 + 0.7;
      const health = enemy.getData('health') || 1;
      const maxHealth = enemy.getData('maxHealth') || 1;
      const healthPercent = health / maxHealth;
      
      // 스테이지별 색상 가져오기
      const stageColor = enemy.getData('stageColor') || 0xff4444;
      const baseR = (stageColor >> 16) & 0xFF;
      const baseG = (stageColor >> 8) & 0xFF;
      const baseB = stageColor & 0xFF;

      // 적 메인 바디 (스테이지별 색상 적용, 더 위협적인 10각형)
      const bodyColor = Phaser.Display.Color.GetColor(
        Math.floor(baseR * pulse), 
        Math.floor(baseG * pulse), 
        Math.floor(baseB * pulse)
      );
      
      this.graphics.fillStyle(bodyColor);
      this.graphics.beginPath();
      
      // 10각형으로 변경하여 더 복잡하고 위협적으로
      for (let i = 0; i < 10; i++) {
        const angle = (i * 36) * Math.PI / 180;
        const outerSize = size + Math.sin(animTimer + i) * 3; // 각 면마다 다른 펄스
        const px = x + Math.cos(angle) * outerSize;
        const py = y + Math.sin(angle) * outerSize;
        
        if (i === 0) this.graphics.moveTo(px, py);
        else this.graphics.lineTo(px, py);
      }
      this.graphics.closePath();
      this.graphics.fillPath();

      // 적 중간 장갑 레이어 (스테이지별 강화된 메탈릭)
      const armorIntensity = Math.min(255, 120 + (this.stage * 15)); // 스테이지별 장갑 강도
      this.graphics.fillStyle(Phaser.Display.Color.GetColor(
        Math.floor(armorIntensity * pulse), 
        Math.floor(armorIntensity * pulse), 
        Math.floor(armorIntensity * pulse * 1.2)
      ));
      this.graphics.beginPath();
      for (let i = 0; i < 8; i++) {
        const angle = (i * 45 + animTimer * this.stage * 0.1) * Math.PI / 180; // 스테이지별 회전 속도
        const px = x + Math.cos(angle) * (size * 0.75);
        const py = y + Math.sin(angle) * (size * 0.75);
        if (i === 0) this.graphics.moveTo(px, py);
        else this.graphics.lineTo(px, py);
      }
      this.graphics.closePath();
      this.graphics.fillPath();

      // 적 코어 (스테이지별 강화된 위협적인 눈)
      const coreR = Math.min(255, baseR + (this.stage * 20));
      const coreColor = Phaser.Display.Color.GetColor(coreR, 0, 0);
      this.graphics.fillStyle(coreColor);
      this.graphics.fillCircle(x, y, size * 0.5);
      
      // 코어 내부 펄스 (스테이지별 더 강렬한 효과)
      const corePulse = Math.sin(animTimer * (2 + this.stage * 0.3)) * 0.5 + 0.5;
      const innerCoreColor = Phaser.Display.Color.GetColor(
        Math.min(255, coreR + 50), 
        Math.floor(100 * corePulse * this.stage * 0.2), 
        0
      );
      this.graphics.fillStyle(innerCoreColor);
      this.graphics.fillCircle(x, y, size * 0.3);

      // 스테이지별 강화된 무기 시스템
      const weaponCount = Math.min(6, 2 + Math.floor(this.stage / 2)); // 스테이지별 무기 개수 증가
      this.graphics.fillStyle(0x444444);
      for (let i = 0; i < weaponCount; i++) {
        const weaponAngle = (i * (360 / weaponCount)) * Math.PI / 180;
        const weaponDistance = size * 0.9;
        const weaponX = x + Math.cos(weaponAngle) * weaponDistance;
        const weaponY = y + Math.sin(weaponAngle) * weaponDistance;
        this.graphics.fillRect(weaponX - 4, weaponY - 4, 8, 8);
        
        // 무기 레이저 포인트 (스테이지별 색상)
        this.graphics.fillStyle(stageColor);
        this.graphics.fillCircle(weaponX, weaponY, 2);
        this.graphics.fillStyle(0x444444); // 다음 무기를 위해 색상 리셋
      }

      // 스테이지별 강화된 엔진 (더 강력하고 다채로운 색상)
      const engineR = Math.min(255, 200 + (this.stage * 10));
      const engineG = Math.min(255, 80 * pulse + (this.stage * 5));
      const engineColor = Phaser.Display.Color.GetColor(engineR, engineG, 0);
      
      this.graphics.fillStyle(engineColor);
      this.graphics.beginPath();
      this.graphics.moveTo(x - size, y - size * 0.4);
      this.graphics.lineTo(x - size * (1.8 + this.stage * 0.1), y - size * 0.15); // 스테이지별 엔진 크기 증가
      this.graphics.lineTo(x - size * (2 + this.stage * 0.1), y);
      this.graphics.lineTo(x - size * (1.8 + this.stage * 0.1), y + size * 0.15);
      this.graphics.lineTo(x - size, y + size * 0.4);
      this.graphics.closePath();
      this.graphics.fillPath();

      // 내부 엔진 불꽃 (스테이지별 더 강렬한 효과)
      const innerEngineColor = Phaser.Display.Color.GetColor(
        Math.min(255, 255),
        Math.min(255, 150 * pulse + (this.stage * 10)),
        Math.floor(this.stage * 20)
      );
      this.graphics.fillStyle(innerEngineColor);
      this.graphics.beginPath();
      this.graphics.moveTo(x - size, y - size * 0.25);
      this.graphics.lineTo(x - size * (1.5 + this.stage * 0.05), y - size * 0.08);
      this.graphics.lineTo(x - size * (1.6 + this.stage * 0.05), y);
      this.graphics.lineTo(x - size * (1.5 + this.stage * 0.05), y + size * 0.08);
      this.graphics.lineTo(x - size, y + size * 0.25);
      this.graphics.closePath();
      this.graphics.fillPath();

      // 체력에 따른 데미지 효과 (스테이지별 더 많은 스파크)
      if (healthPercent < 0.7) {
        const sparkCount = Math.min(8, 2 + this.stage);
        for (let i = 0; i < sparkCount; i++) {
          const sparkX = x + Phaser.Math.Between(-size, size);
          const sparkY = y + Phaser.Math.Between(-size, size);
          this.graphics.fillStyle(0xffff00);
          this.graphics.fillCircle(sparkX, sparkY, 1);
        }
      }

      if (healthPercent < 0.4) {
        // 체력이 40% 이하일 때 더 많은 연기와 불꽃
        const smokeCount = Math.min(4, 1 + Math.floor(this.stage / 2));
        for (let i = 0; i < smokeCount; i++) {
          this.graphics.fillStyle(0x666666, 0.4);
          this.graphics.fillCircle(x + Phaser.Math.Between(-8, 8), y + Phaser.Math.Between(-8, 8), 4);
          this.graphics.fillStyle(0xff4400, 0.6);
          this.graphics.fillCircle(x + Phaser.Math.Between(-6, 6), y + Phaser.Math.Between(-6, 6), 3);
        }
      }

      // 스테이지별 강화된 위협적인 외곽 글로우
      const glowIntensity = Math.min(1.0, 0.3 + (this.stage * 0.08));
      const glowColor = stageColor;
      this.graphics.lineStyle(Math.min(4, 2 + Math.floor(this.stage / 3)), glowColor, glowIntensity * pulse);
      this.graphics.strokeCircle(x, y, size + 3 + this.stage);
      
      // 고단계에서는 추가 외곽 링
      if (this.stage >= 5) {
        this.graphics.lineStyle(2, glowColor, glowIntensity * pulse * 0.6);
        this.graphics.strokeCircle(x, y, size + 8 + this.stage);
      }
    }

    // 게임 크기가 변경될 때 호출되는 메서드
    updateGameSize(newWidth: number, newHeight: number) {
      GAME_WIDTH = newWidth;
      GAME_HEIGHT = newHeight;
      
      // 배경 크기 조정
      this.add.rectangle(GAME_WIDTH / 2, GAME_HEIGHT / 2, GAME_WIDTH, GAME_HEIGHT, 0x000011);
      
      // 플레이어 위치 조정 (화면 중앙 좌측으로)
      if (this.player) {
        this.player.setPosition(100, GAME_HEIGHT / 2);
      }
      
      // 별들 재생성
      if (this.stars) {
        this.stars.clear(true, true);
        this.createStars();
      }
      
      // UI 텍스트 위치 조정
      if (this.scoreText) {
        this.scoreText.setPosition(20, 20);
      }
      if (this.livesText) {
        this.livesText.setPosition(20, 50);
      }
      if (this.stageText) {
        this.stageText.setPosition(20, 80);
      }
      if (this.bossHealthText) {
        this.bossHealthText.setPosition(GAME_WIDTH / 2, 30);
      }
      if (this.itemsUI) {
        this.itemsUI.setFontSize(Math.max(14, Math.min(20, GAME_WIDTH / 40)));
        this.itemsUI.setPosition(GAME_WIDTH - 150, 20);
      }
      
      // 아이템 설명 UI 위치 업데이트
      if (this.itemDescriptionUI) {
        this.itemDescriptionUI.setFontSize(Math.max(10, Math.min(12, GAME_WIDTH / 60)));
        this.itemDescriptionUI.setPosition(GAME_WIDTH / 2, GAME_HEIGHT - 40);
      }
    }

    private createBossHitEffect(x: number, y: number, damage: number) {
      if (!this.graphics) return;

      // 보스 타격 시 시각적 효과
      const hitSize = Math.max(10, Math.min(20, damage * 8));
      const hitColor = damage >= 5 ? 0x00ffff : 0xffff00; // 차지 어택은 청록색, 일반은 노란색
      
      // 타격 폭발 효과
      const hitEffect = this.add.circle(x, y, hitSize, hitColor, 0.8);
      
      // 타격 점 주변에 스파크 효과
      for (let i = 0; i < 6; i++) {
        const sparkAngle = (i * 60) * Math.PI / 180;
        const sparkDistance = hitSize + Phaser.Math.Between(5, 15);
        const sparkX = x + Math.cos(sparkAngle) * sparkDistance;
        const sparkY = y + Math.sin(sparkAngle) * sparkDistance;
        
        const spark = this.add.circle(sparkX, sparkY, 3, 0xffffff, 0.9);
        
        // 스파크 애니메이션
        this.tweens.add({
          targets: spark,
          scaleX: 0,
          scaleY: 0,
          alpha: 0,
          duration: 300,
          onComplete: () => {
            spark.destroy();
          }
        });
      }
      
      // 메인 타격 효과 애니메이션
      this.tweens.add({
        targets: hitEffect,
        scaleX: 2,
        scaleY: 2,
        alpha: 0,
        duration: 400,
        ease: 'Power2',
        onComplete: () => {
          hitEffect.destroy();
        }
      });
      
      // 데미지 텍스트 표시
      const damageText = this.add.text(x, y - 30, `-${damage}`, {
        fontSize: Math.max(14, Math.min(20, damage * 4)) + 'px',
        color: damage >= 5 ? '#00ffff' : '#ffff00',
        fontFamily: 'Courier New, monospace',
        stroke: '#000000',
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
      
      // 데미지 텍스트 애니메이션
      this.tweens.add({
        targets: damageText,
        y: y - 60,
        alpha: 0,
        duration: 1000,
        ease: 'Power2',
        onComplete: () => {
          damageText.destroy();
        }
      });
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
      backgroundColor: '#000011',
      scene: SpaceScene,
      physics: {
        default: 'arcade',
        arcade: {
          gravity: { x: 0, y: 0 },
          debug: false
        }
      },
      scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH
      }
    };

    game = new Phaser.Game(config);

    // 리사이즈 이벤트 리스너 추가
    window.addEventListener('resize', handleResize);

    return () => {
      if (game) {
        game.destroy(true);
        game = null;
      }
      window.removeEventListener('resize', handleResize);
    };
  });

  onDestroy(() => {
    if (game) {
      game.destroy(true);
      game = null;
    }
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