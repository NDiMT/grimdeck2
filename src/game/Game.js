import { Dungeon } from '../engine/Dungeon.js';
import { Renderer } from '../engine/Renderer.js';
import { Player } from './Player.js';

export class Game {
  constructor() {
    this.canvas = document.getElementById('dungeon-canvas');
    this.state = 'explore'; // 'explore' | 'combat'
    this.currentEnemy = null;
    this.lastTime = 0;
    this.floor = 1;

    this._newFloor();
    this._setupInput();
    this._resize();
    window.addEventListener('resize', () => this._resize());

    requestAnimationFrame(t => this._loop(t));
  }

  // ── Setup ─────────────────────────────────────

  _newFloor() {
    this.dungeon = new Dungeon();
    const { x, z } = this.dungeon.startPos;

    if (!this.renderer) {
      this.renderer = new Renderer(this.canvas);
    }
    if (!this.player) {
      this.player = new Player(x, z);
    } else {
      this.player.moveTo(x, z);
      this.player.dir = 0;
    }

    this.renderer.buildDungeon(this.dungeon.grid);
    this.renderer.buildEnemyMarkers(this.dungeon.enemies);
    this.renderer.setPlayer(this.player.x, this.player.z, this.player.dir);

    document.getElementById('floor-num').textContent = this.floor;
    this._updateHUD();
  }

  _resize() {
    const view = document.getElementById('dungeon-view');
    this.renderer.resize(view.clientWidth, view.clientHeight);
  }

  // ── Game loop ─────────────────────────────────

  _loop(time) {
    const dt = Math.min((time - this.lastTime) / 1000, 0.1);
    this.lastTime = time;
    this.renderer.render(dt);
    requestAnimationFrame(t => this._loop(t));
  }

  // ── Exploration ───────────────────────────────

  _move(fwd) {
    if (this.state !== 'explore') return;
    const { dx, dz } = this.player.forwardDelta();
    const nx = this.player.x + (fwd ? dx : -dx);
    const nz = this.player.z + (fwd ? dz : -dz);

    if (this.dungeon.isWall(nx, nz)) return;

    const enemy = this.dungeon.getEnemyAt(nx, nz);
    if (enemy && fwd) {
      this._startCombat(enemy);
      return;
    }

    this.player.moveTo(nx, nz);
    this.renderer.setPlayer(this.player.x, this.player.z, this.player.dir);
  }

  _turn(left) {
    if (this.state !== 'explore') return;
    left ? this.player.turnLeft() : this.player.turnRight();
    this.renderer.setPlayer(this.player.x, this.player.z, this.player.dir);
  }

  // ── Combat ────────────────────────────────────

  _startCombat(enemy) {
    this.state = 'combat';
    this.currentEnemy = enemy;

    document.getElementById('controls').classList.add('hidden');
    document.getElementById('combat-controls').classList.remove('hidden');
    document.getElementById('enemy-overlay').classList.remove('hidden');
    document.getElementById('enemy-name').textContent = enemy.name;
    document.getElementById('enemy-intent-val').textContent = enemy.attack;

    this.player.drawHand();
    this._updateCombatUI();
    this._updateHUD();
  }

  _endCombat() {
    this.currentEnemy.alive = false;
    this.renderer.updateEnemyMarkers();
    this.state = 'explore';
    this.currentEnemy = null;

    document.getElementById('controls').classList.remove('hidden');
    document.getElementById('combat-controls').classList.add('hidden');
    document.getElementById('enemy-overlay').classList.add('hidden');

    this._updateHUD();
  }

  playCard(index) {
    if (this.state !== 'combat') return;
    const card = this.player.hand[index];
    if (!card || this.player.energy < card.cost) return;

    this.player.energy -= card.cost;
    this.player.hand.splice(index, 1);

    if (card.type === 'attack') {
      this.currentEnemy.hp = Math.max(0, this.currentEnemy.hp - card.value);
      this._flashDungeonView();
      if (this.currentEnemy.hp <= 0) {
        setTimeout(() => this._endCombat(), 400);
        this._updateCombatUI();
        return;
      }
    } else if (card.type === 'block') {
      this.player.block += card.value;
    }

    this._updateCombatUI();
    this._updateHUD();
  }

  _enemyTurn() {
    if (this.state !== 'combat') return;
    const dmg = this.currentEnemy.attack;
    const absorbed = Math.min(this.player.block, dmg);
    this.player.block = Math.max(0, this.player.block - dmg);
    this.player.hp = Math.max(0, this.player.hp - (dmg - absorbed));

    this._updateHUD();
    this.player.drawHand();
    this._updateCombatUI();
  }

  // ── UI updates ────────────────────────────────

  _updateHUD() {
    const pct = (this.player.hp / this.player.maxHp) * 100;
    document.getElementById('health-fill').style.width = pct + '%';
    document.getElementById('health-text').textContent = `${this.player.hp}/${this.player.maxHp}`;
    document.getElementById('block-text').textContent = `🛡 ${this.player.block}`;
    document.getElementById('energy-text').textContent = `⚡ ${this.player.energy}`;
  }

  _updateCombatUI() {
    const enemy = this.currentEnemy;
    if (!enemy) return;

    const pct = Math.max(0, (enemy.hp / enemy.maxHp) * 100);
    document.getElementById('enemy-hp-fill').style.width = pct + '%';
    document.getElementById('enemy-hp-text').textContent = `${enemy.hp}/${enemy.maxHp}`;
    document.getElementById('energy-text').textContent = `⚡ ${this.player.energy}`;
    document.getElementById('block-text').textContent = `🛡 ${this.player.block}`;

    const handEl = document.getElementById('hand');
    handEl.innerHTML = '';

    this.player.hand.forEach((card, i) => {
      const el = document.createElement('div');
      el.className = `card ${card.type}${this.player.energy < card.cost ? ' disabled' : ''}`;
      el.innerHTML = `
        <div class="card-cost">${card.cost}</div>
        <div class="card-name">${card.name}</div>
        <div class="card-value">${card.value}</div>
        <div class="card-desc">${card.desc}</div>
      `;
      el.addEventListener('pointerdown', e => { e.preventDefault(); this.playCard(i); });
      handEl.appendChild(el);
    });
  }

  _flashDungeonView() {
    const view = document.getElementById('dungeon-view');
    view.classList.remove('damage-flash');
    void view.offsetWidth; // reflow to restart animation
    view.classList.add('damage-flash');
  }

  // ── Input ─────────────────────────────────────

  _setupInput() {
    const on = (id, fn) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.addEventListener('pointerdown', e => { e.preventDefault(); fn(); });
    };

    on('btn-forward', () => this._move(true));
    on('btn-back',    () => this._move(false));
    on('btn-left',    () => this._turn(true));
    on('btn-right',   () => this._turn(false));
    on('btn-end-turn', () => this._enemyTurn());

    window.addEventListener('keydown', e => {
      if (e.key === 'ArrowUp'    || e.key === 'w') this._move(true);
      if (e.key === 'ArrowDown'  || e.key === 's') this._move(false);
      if (e.key === 'ArrowLeft'  || e.key === 'a') this._turn(true);
      if (e.key === 'ArrowRight' || e.key === 'd') this._turn(false);
      if (e.key === 'Enter' || e.key === ' ')      this._enemyTurn();
    });
  }
}
