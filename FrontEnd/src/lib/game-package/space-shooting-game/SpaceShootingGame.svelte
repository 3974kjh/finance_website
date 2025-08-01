<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Phaser from 'phaser';

  let gameContainer: HTMLDivElement;
  let game: Phaser.Game | null = null;

  // 게임 설정 (동적으로 조정될 예정)
  let GAME_WIDTH = 800;
  let GAME_HEIGHT = 600;

  class SpaceScene extends Phaser.Scene {
    private player: Phaser.GameObjects.Rectangle | null = null;
    private bullets: Phaser.GameObjects.Group | null = null;
    private enemies: Phaser.GameObjects.Group | null = null;
    private stars: Phaser.GameObjects.Group | null = null;
    private boss: Phaser.GameObjects.Rectangle | null = null;
    private bossBullets: Phaser.GameObjects.Group | null = null;
    private cursors: Phaser.Types.Input.Keyboard.CursorKeys | null = null;
    private wasd: any = null;
    private spaceKey: Phaser.Input.Keyboard.Key | null = null;
    private lastFired: number = 0;
    private score: number = 0;
    private lives: number = 3;
    private stage: number = 1;
    private scoreText: Phaser.GameObjects.Text | null = null;
    private livesText: Phaser.GameObjects.Text | null = null;
    private stageText: Phaser.GameObjects.Text | null = null;
    private gameOverText: Phaser.GameObjects.Text | null = null;
    private bossHealthBar: Phaser.GameObjects.Graphics | null = null;
    private bossHealthText: Phaser.GameObjects.Text | null = null;
    private gameOver: boolean = false;
    private enemySpawnTimer: number = 0;
    private graphics: Phaser.GameObjects.Graphics | null = null;
    private level: number = 1;
    
    // 보스 관련 변수
    private isBossStage: boolean = false;
    private bossMaxHealth: number = 100;
    private bossCurrentHealth: number = 100;
    private bossDirection: number = 1; // 1: 아래, -1: 위
    private bossLastShot: number = 0;
    private stageTransitionTimer: number = 0;
    private isStageTransition: boolean = false;

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

      // 키보드 입력 설정
      this.cursors = this.input.keyboard?.createCursorKeys() || null;
      
      if (this.input.keyboard) {
        this.wasd = this.input.keyboard.addKeys('W,S,A,D');
        this.spaceKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.SPACE);
      }

      // UI 텍스트
      this.scoreText = this.add.text(20, 20, 'Score: 0', {
        fontSize: Math.max(14, Math.min(20, GAME_WIDTH / 40)) + 'px',
        color: '#00ff00',
        fontFamily: 'monospace'
      });

      this.livesText = this.add.text(20, 50, 'Lives: 3', {
        fontSize: Math.max(14, Math.min(20, GAME_WIDTH / 40)) + 'px',
        color: '#ff0000',
        fontFamily: 'monospace'
      });

      this.stageText = this.add.text(20, 80, 'Stage: 1', {
        fontSize: Math.max(14, Math.min(20, GAME_WIDTH / 40)) + 'px',
        color: '#ffff00',
        fontFamily: 'monospace'
      });

      this.bossHealthText = this.add.text(GAME_WIDTH / 2, 30, '', {
        fontSize: Math.max(16, Math.min(24, GAME_WIDTH / 35)) + 'px',
        color: '#ff0000',
        fontFamily: 'monospace'
      }).setOrigin(0.5).setVisible(false);

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
      this.stage = 1;
      this.level = 1;
      this.gameOver = false;
      this.enemySpawnTimer = 0;
      this.isBossStage = false;
      this.isStageTransition = false;
      
      // UI 업데이트
      this.scoreText?.setText('Score: 0');
      this.livesText?.setText('Lives: 3');
      this.stageText?.setText('Stage: 1');
      this.bossHealthText?.setVisible(false);

      // 플레이어 위치 리셋 (좌측)
      if (this.player) {
        this.player.setPosition(100, GAME_HEIGHT / 2);
      }

      // 게임 오브젝트들 정리
      this.bullets?.clear(true, true);
      this.enemies?.clear(true, true);
      this.bossBullets?.clear(true, true);
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

      // 총알 발사 (우측으로)
      if (this.spaceKey?.isDown && time > this.lastFired + 150) { // 0.15초 간격
        this.fireBullet();
        this.lastFired = time;
      }
    }

    private updatePlayer() {
      if (!this.player || !this.graphics) return;

      // 플레이어 우주선 그리기 (우측을 향하는 개선된 디자인)
      this.graphics.clear();
      
      const shipSize = Math.max(10, Math.min(20, GAME_HEIGHT / 30));
      
      // 우주선 메인 바디 (그라데이션 효과)
      this.graphics.fillStyle(0x00ff44);
      this.graphics.beginPath();
      // 우측을 향하는 삼각형
      this.graphics.moveTo(this.player.x + shipSize, this.player.y); // 앞부분 (우측)
      this.graphics.lineTo(this.player.x - shipSize, this.player.y - shipSize * 0.7); // 왼쪽 위
      this.graphics.lineTo(this.player.x - shipSize, this.player.y + shipSize * 0.7); // 왼쪽 아래
      this.graphics.closePath();
      this.graphics.fillPath();

      // 우주선 하이라이트
      this.graphics.fillStyle(0x88ff88);
      this.graphics.beginPath();
      this.graphics.moveTo(this.player.x + shipSize * 0.8, this.player.y);
      this.graphics.lineTo(this.player.x - shipSize * 0.5, this.player.y - shipSize * 0.4);
      this.graphics.lineTo(this.player.x - shipSize * 0.5, this.player.y + shipSize * 0.4);
      this.graphics.closePath();
      this.graphics.fillPath();

      // 엔진 불꽃 효과 (좌측) - 개선된 효과
      this.graphics.fillStyle(0xff6600);
      this.graphics.beginPath();
      this.graphics.moveTo(this.player.x - shipSize, this.player.y - shipSize * 0.35);
      this.graphics.lineTo(this.player.x - shipSize * 1.7, this.player.y);
      this.graphics.lineTo(this.player.x - shipSize, this.player.y + shipSize * 0.35);
      this.graphics.closePath();
      this.graphics.fillPath();
      
      // 내부 불꽃 효과
      this.graphics.fillStyle(0xffaa00);
      this.graphics.beginPath();
      this.graphics.moveTo(this.player.x - shipSize, this.player.y - shipSize * 0.2);
      this.graphics.lineTo(this.player.x - shipSize * 1.4, this.player.y);
      this.graphics.lineTo(this.player.x - shipSize, this.player.y + shipSize * 0.2);
      this.graphics.closePath();
      this.graphics.fillPath();
    }

    private fireBullet() {
      if (!this.player || !this.bullets) return;

      const bulletSize = Math.max(3, Math.min(6, GAME_WIDTH / 150));
      // 우측으로 발사 - 개선된 총알 디자인
      const bullet = this.add.rectangle(this.player.x + 20, this.player.y, bulletSize * 2, bulletSize, 0xffff00);
      bullet.setData('speed', Math.max(6, Math.min(10, GAME_WIDTH / 80)));
      this.bullets.add(bullet);
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

      // 적 생성
      const spawnRate = Math.max(1000 - (this.level * 100), 300); // 레벨이 올라갈수록 빠르게
      if (time > this.enemySpawnTimer + spawnRate) {
        this.spawnEnemy();
        this.enemySpawnTimer = time;
      }

      // 적 이동 (좌측으로)
      this.enemies.children.entries.forEach(enemy => {
        const enemyObj = enemy as Phaser.GameObjects.Rectangle;
        enemyObj.x -= enemyObj.getData('speed');

        // 화면 밖으로 나간 적 제거
        if (enemyObj.x < -50) {
          this.enemies?.remove(enemyObj);
          enemyObj.destroy();
        }
      });
    }

    private spawnEnemy() {
      if (!this.enemies) return;

      const x = GAME_WIDTH + 20; // 우측에서 생성
      const y = Phaser.Math.Between(20, GAME_HEIGHT - 20);
      const speed = Phaser.Math.Between(2, 4 + this.level);
      const enemySize = Math.max(15, Math.min(30, GAME_HEIGHT / 25));
      
      const enemy = this.add.rectangle(x, y, enemySize, enemySize, 0xff0000);
      enemy.setData('speed', speed);
      enemy.setData('points', 10);
      
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

    private checkCollisions() {
      if (!this.bullets || !this.enemies || !this.player) return;

      // 총알과 적의 충돌
      this.bullets.children.entries.forEach(bullet => {
        const bulletObj = bullet as Phaser.GameObjects.Rectangle;
        
        this.enemies?.children.entries.forEach(enemy => {
          const enemyObj = enemy as Phaser.GameObjects.Rectangle;
          
          if (Phaser.Geom.Rectangle.Overlaps(bulletObj.getBounds(), enemyObj.getBounds())) {
            // 점수 증가
            this.score += enemyObj.getData('points');
            this.scoreText?.setText(`Score: ${this.score}`);
            
            // 레벨 업 체크
            if (this.score > 0 && this.score % 200 === 0) {
              this.level++;
            }

            // 오브젝트 제거
            this.bullets?.remove(bulletObj);
            this.enemies?.remove(enemyObj);
            bulletObj.destroy();
            enemyObj.destroy();

            // 폭발 이펙트
            this.createExplosion(enemyObj.x, enemyObj.y);
          }
        });
      });

      // 플레이어와 적의 충돌
      this.enemies.children.entries.forEach(enemy => {
        const enemyObj = enemy as Phaser.GameObjects.Rectangle;
        
        if (Phaser.Geom.Rectangle.Overlaps(this.player!.getBounds(), enemyObj.getBounds())) {
          // 생명 감소
          this.lives--;
          this.livesText?.setText(`Lives: ${this.lives}`);

          // 적 제거
          this.enemies?.remove(enemyObj);
          enemyObj.destroy();

          // 폭발 이펙트
          this.createExplosion(this.player!.x, this.player!.y);

          // 게임 오버 체크
          if (this.lives <= 0) {
            this.endGame();
          }
        }
      });
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
        fontFamily: 'monospace'
      }).setOrigin(0.5);

      this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2, `Final Score: ${this.score}`, {
        fontSize: Math.max(16, Math.min(24, GAME_WIDTH / 35)) + 'px',
        color: '#ffffff',
        fontFamily: 'monospace'
      }).setOrigin(0.5);

      this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2 + 40, `Level Reached: ${this.level}`, {
        fontSize: Math.max(14, Math.min(20, GAME_WIDTH / 40)) + 'px',
        color: '#00ff00',
        fontFamily: 'monospace'
      }).setOrigin(0.5);

      this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2 + 80, 'Press SPACE to restart', {
        fontSize: Math.max(12, Math.min(16, GAME_WIDTH / 50)) + 'px',
        color: '#00ffff',
        fontFamily: 'monospace'
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

    private checkStageProgression() {
      // 스코어에 따른 스테이지 진행 체크
      const requiredScore = this.stage * 300; // 스테이지마다 300점 필요
      if (this.score >= requiredScore && !this.isBossStage) {
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
      
      // 보스 체력 설정 (스테이지에 따라 증가)
      this.bossMaxHealth = 50 + (this.stage * 30);
      this.bossCurrentHealth = this.bossMaxHealth;
      this.bossDirection = 1;
      this.bossLastShot = 0;
      
      this.updateBossHealthDisplay();
    }

    private updateBoss(time: number) {
      if (!this.boss) return;

      // 보스 이동 (위아래)
      const bossSpeed = 2 + Math.floor(this.stage * 0.5);
      this.boss.y += this.bossDirection * bossSpeed;

      // 화면 경계에서 방향 전환
      if (this.boss.y <= 80 || this.boss.y >= GAME_HEIGHT - 80) {
        this.bossDirection *= -1;
      }

      // 보스 미사일 발사
      const shootInterval = Math.max(800, 1500 - (this.stage * 100)); // 스테이지가 높을수록 빠른 발사
      if (time > this.bossLastShot + shootInterval) {
        this.fireBossBullet();
        this.bossLastShot = time;
      }

      // 보스 그리기 (개선된 디자인)
      this.drawBoss();
    }

    private drawBoss() {
      if (!this.boss || !this.graphics) return;

      // 보스 메인 바디 (큰 육각형)
      this.graphics.fillStyle(0x8800ff);
      this.graphics.beginPath();
      const centerX = this.boss.x;
      const centerY = this.boss.y;
      const size = 40;
      
      for (let i = 0; i < 6; i++) {
        const angle = (i * Math.PI) / 3;
        const x = centerX + Math.cos(angle) * size;
        const y = centerY + Math.sin(angle) * size;
        if (i === 0) {
          this.graphics.moveTo(x, y);
        } else {
          this.graphics.lineTo(x, y);
        }
      }
      this.graphics.closePath();
      this.graphics.fillPath();

      // 보스 코어 (중앙 빨간 원)
      this.graphics.fillStyle(0xff0000);
      this.graphics.fillCircle(centerX, centerY, 15);

      // 보스 엔진 (좌측 불꽃)
      this.graphics.fillStyle(0xff6600);
      this.graphics.beginPath();
      this.graphics.moveTo(centerX - size, centerY - 10);
      this.graphics.lineTo(centerX - size - 20, centerY);
      this.graphics.lineTo(centerX - size, centerY + 10);
      this.graphics.closePath();
      this.graphics.fillPath();
    }

    private fireBossBullet() {
      if (!this.boss || !this.bossBullets || !this.player) return;

      // 플레이어를 향해 미사일 발사
      const angle = Phaser.Math.Angle.Between(this.boss.x, this.boss.y, this.player.x, this.player.y);
      const speed = 4 + Math.floor(this.stage * 0.5);
      
      const bullet = this.add.rectangle(this.boss.x - 30, this.boss.y, 12, 6, 0xff3300);
      bullet.setData('speedX', Math.cos(angle) * speed);
      bullet.setData('speedY', Math.sin(angle) * speed);
      bullet.setData('damage', 1);
      
      this.bossBullets.add(bullet);
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

    private checkBossCollisions() {
      if (!this.boss || !this.bullets || !this.player || !this.bossBullets) return;

      // 플레이어 총알과 보스 충돌
      this.bullets.children.entries.forEach(bullet => {
        const bulletObj = bullet as Phaser.GameObjects.Rectangle;
        
        if (Phaser.Geom.Rectangle.Overlaps(bulletObj.getBounds(), this.boss!.getBounds())) {
          // 보스 체력 감소
          this.bossCurrentHealth -= 10;
          this.updateBossHealthDisplay();
          
          // 총알 제거
          this.bullets?.remove(bulletObj);
          bulletObj.destroy();
          
          // 점수 증가
          this.score += 20;
          this.scoreText?.setText(`Score: ${this.score}`);
          
          // 폭발 이펙트
          this.createExplosion(bulletObj.x, bulletObj.y);
          
          // 보스 처치 체크
          if (this.bossCurrentHealth <= 0) {
            this.defeatBoss();
          }
        }
      });

      // 보스 미사일과 플레이어 충돌
      this.bossBullets.children.entries.forEach(bullet => {
        const bulletObj = bullet as Phaser.GameObjects.Rectangle;
        
        if (Phaser.Geom.Rectangle.Overlaps(this.player!.getBounds(), bulletObj.getBounds())) {
          // 플레이어 라이프 감소
          this.lives--;
          this.livesText?.setText(`Lives: ${this.lives}`);
          
          // 미사일 제거
          this.bossBullets?.remove(bulletObj);
          bulletObj.destroy();
          
          // 폭발 이펙트
          this.createExplosion(this.player!.x, this.player!.y);
          
          // 게임 오버 체크
          if (this.lives <= 0) {
            this.endGame();
          }
        }
      });
    }

    private defeatBoss() {
      if (!this.boss) return;
      
      // 보스 처치 점수
      this.score += 200 * this.stage;
      this.scoreText?.setText(`Score: ${this.score}`);
      
      // 폭발 이펙트
      this.createExplosion(this.boss.x, this.boss.y);
      
      // 보스 제거
      this.clearBoss();
      
      // 다음 스테이지로
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
        fontFamily: 'monospace'
      }).setOrigin(0.5);

      this.add.text(GAME_WIDTH / 2, GAME_HEIGHT / 2 + 40, `NEXT STAGE: ${this.stage}`, {
        fontSize: Math.max(16, Math.min(24, GAME_WIDTH / 35)) + 'px',
        color: '#ffff00',
        fontFamily: 'monospace'
      }).setOrigin(0.5);

      // 2초 후 텍스트 제거
      this.time.delayedCall(2000, () => {
        stageCompleteText.destroy();
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
      const healthPercent = this.bossCurrentHealth / this.bossMaxHealth;
      this.bossHealthBar.fillStyle(0xff0000);
      this.bossHealthBar.fillRect(x + 2, y + 2, (barWidth - 4) * healthPercent, barHeight - 4);
      
      // 테두리 (하얀색)
      this.bossHealthBar.lineStyle(2, 0xffffff);
      this.bossHealthBar.strokeRect(x, y, barWidth, barHeight);
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