import { Dungeon } from '../engine/Dungeon.js';
import { Renderer } from '../engine/Renderer.js';
import { Minimap } from '../engine/Minimap.js';
import { Player, CARDS } from './Player.js';

export class Game {
  constructor() {
    this.canvas = document.getElementById('dungeon-canvas');
    this.state = 'explore';
    this.currentEnemy = null;
    this.lastTime = 0;
    this.floor = 1;

    this._newFloor();
    this._setupInput();
    this._resize();
    requestAnimationFrame(() => this._resize());
    window.addEventListener('resize', () => this._resize());
    requestAnimationFrame(t => this._loop(t));
  }

  // ── Setup ─────────────────────────────────────

  _newFloor() {
    this.dungeon = new Dungeon();
    const { x, z } = this.dungeon.startPos;

    if (!this.renderer) this.renderer = new Renderer(this.canvas);
    if (!this.player) {
      this.player = new Player(x, z);
    } else {
      this.player.moveTo(x, z);
      this.player.dir = 0;
    }

    this.visited = new Set();
    this._markVisible(x, z);

    this.renderer.buildDungeon(this.dungeon.grid);
    this.renderer.buildEnemyMarkers(this.dungeon.enemies);
    this.renderer.setPlayer(this.player.x, this.player.z, this.player.dir);
    this.minimap = new Minimap(document.getElementById('minimap'), this.dungeon);
    this.minimap.update(this.player, this.dungeon.enemies, this.visited);
    document.getElementById('floor-num').textContent = this.floor;
    this._updateHUD();
  }

  _resize() {
    const v = document.getElementById('dungeon-view');
    this.renderer.resize(v.clientWidth, v.clientHeight);
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
    if (enemy && fwd) { this._markVisible(nx, nz); this._startCombat(enemy); return; }

    this.player.moveTo(nx, nz);
    this._markVisible(nx, nz);
    this.renderer.setPlayer(this.player.x, this.player.z, this.player.dir);
    this.minimap.update(this.player, this.dungeon.enemies, this.visited);
  }

  _turn(left) {
    if (this.state !== 'explore') return;
    left ? this.player.turnLeft() : this.player.turnRight();
    this.renderer.setPlayer(this.player.x, this.player.z, this.player.dir);
    this.minimap.update(this.player, this.dungeon.enemies, this.visited);
  }

  _markVisible(x, z) {
    const g = this.dungeon.grid;
    const v = this.visited;
    const reveal = (cx, cz) => {
      v.add(`${cx},${cz}`);
      for (const [dx, dz] of [[1,0],[-1,0],[0,1],[0,-1]])
        if (g[cz+dz]?.[cx+dx] === 1) v.add(`${cx+dx},${cz+dz}`);
    };
    reveal(x, z);
    for (const [dx, dz] of [[1,0],[-1,0],[0,1],[0,-1]]) {
      let nx = x + dx, nz = z + dz;
      while (g[nz]?.[nx] === 0) { reveal(nx, nz); nx += dx; nz += dz; }
      if (g[nz]?.[nx] === 1) v.add(`${nx},${nz}`);
    }
  }

  // ── Combat ────────────────────────────────────

  _startCombat(enemy) {
    this.state = 'combat';
    this.currentEnemy = enemy;
    this.player.startCombat();

    document.getElementById('controls').classList.add('hidden');
    document.getElementById('weapon-sprite').classList.add('hidden');
    document.getElementById('combat-controls').classList.remove('hidden');
    document.getElementById('enemy-overlay').classList.remove('hidden');
    document.getElementById('enemy-name').textContent = enemy.name;
    document.getElementById('enemy-intent-val').textContent = enemy.attack;

    this._updateCombatUI();
    this._updateHUD();
  }

  playCard(i) {
    if (this.state !== 'combat') return;
    const card = this.player.hand[i];
    if (!card || this.player.energy < card.cost) return;

    const p = this.player, e = this.currentEnemy;
    p.energy -= card.cost;
    p.hand.splice(i, 1);

    switch (card.effect) {
      case 'damage': {
        const hits = card.hits || 1;
        const dmg = Math.max(0, card.value + p.strength);
        for (let h = 0; h < hits; h++) e.hp = Math.max(0, e.hp - dmg);
        this._flash();
        break;
      }
      case 'block':
        p.block += card.value + p.dexterity;
        break;
      case 'entrench':
        p.block *= 2;
        break;
      case 'bodyslam':
        e.hp = Math.max(0, e.hp - p.block);
        this._flash();
        break;
      case 'iron_wave':
        p.block += card.value + p.dexterity;
        e.hp = Math.max(0, e.hp - card.value - p.strength);
        this._flash();
        break;
      case 'whirlwind': {
        const spent = p.energy;
        e.hp = Math.max(0, e.hp - card.value * spent);
        p.energy = 0;
        this._flash();
        break;
      }
      case 'strength':
        p.strength += card.value;
        break;
      case 'dexterity':
        p.dexterity += card.value;
        break;
      case 'bloodletting':
        p.hp = Math.max(1, p.hp - 3);
        p.energy += 2;
        break;
      case 'draw': {
        const drawn = [...p.deck].sort(() => Math.random() - 0.5).slice(0, card.value);
        p.hand.push(...drawn);
        break;
      }
      case 'energy':
        p.energy += card.value;
        break;
      case 'second_wind': {
        const nonAtk = p.hand.filter(c => c.type !== 'attack');
        p.block += nonAtk.length * card.value;
        p.hand = p.hand.filter(c => c.type === 'attack');
        break;
      }
      case 'offering':
        p.hp = Math.max(1, p.hp - 6);
        p.energy += 2;
        p.hand.push(...[...p.deck].sort(() => Math.random() - 0.5).slice(0, 3));
        break;
    }

    if (card.draw) {
      p.hand.push(...[...p.deck].sort(() => Math.random() - 0.5).slice(0, card.draw));
    }

    if (e.hp <= 0) {
      setTimeout(() => this._victory(), 350);
      this._updateCombatUI();
      this._updateHUD();
      return;
    }
    this._updateCombatUI();
    this._updateHUD();
  }

  _enemyTurn() {
    if (this.state !== 'combat') return;
    const dmg = this.currentEnemy.attack;
    const abs = Math.min(this.player.block, dmg);
    this.player.block = Math.max(0, this.player.block - dmg);
    this.player.hp = Math.max(0, this.player.hp - (dmg - abs));
    this._updateHUD();
    this.player.drawHand();
    this._updateCombatUI();
  }

  // ── Victory / Reward ──────────────────────────

  _victory() {
    this.currentEnemy.alive = false;
    this.renderer.updateEnemyMarkers();
    this.minimap.update(this.player, this.dungeon.enemies, this.visited);
    document.getElementById('combat-controls').classList.add('hidden');
    document.getElementById('enemy-overlay').classList.add('hidden');
    this._showReward();
  }

  _showReward() {
    const pool = CARDS.filter(c => !c.starter);
    const picks = [...pool].sort(() => Math.random() - 0.5).slice(0, 3);
    const el = document.getElementById('reward-cards');
    el.innerHTML = '';
    picks.forEach(card => {
      const div = document.createElement('div');
      div.className = `card ${card.type}`;
      div.innerHTML = `
        <div class="card-cost">${card.cost}</div>
        <div class="card-name">${card.name}</div>
        <div class="card-value">${card.value || '✦'}</div>
        <div class="card-desc">${card.desc}${card.exhaust ? ' <em>(Exhaust)</em>' : ''}</div>`;
      let rx, ry;
      div.addEventListener('pointerdown', ev => { rx = ev.clientX; ry = ev.clientY; });
      div.addEventListener('pointerup', ev => {
        if (Math.hypot(ev.clientX - rx, ev.clientY - ry) < 12) { ev.preventDefault(); this._pickReward(card); }
      });
      el.appendChild(div);
    });
    document.getElementById('reward-overlay').classList.remove('hidden');
  }

  _pickReward(card) {
    this.player.deck.push({ ...card, id: card.id + '_' + Date.now() });
    this._returnToExplore();
  }

  _returnToExplore() {
    this.state = 'explore';
    this.currentEnemy = null;
    document.getElementById('reward-overlay').classList.add('hidden');
    document.getElementById('controls').classList.remove('hidden');
    document.getElementById('weapon-sprite').classList.remove('hidden');
    this._updateHUD();
  }

  // ── UI ────────────────────────────────────────

  _updateHUD() {
    const p = this.player;
    document.getElementById('health-fill').style.width = (p.hp / p.maxHp * 100) + '%';
    document.getElementById('health-text').textContent = `${p.hp}/${p.maxHp}`;
    document.getElementById('block-text').textContent = `🛡 ${p.block}`;
    document.getElementById('energy-text').textContent = `⚡ ${p.energy}`;
  }

  _updateCombatUI() {
    const p = this.player, e = this.currentEnemy;
    if (!e) return;

    document.getElementById('enemy-hp-fill').style.width = Math.max(0, e.hp / e.maxHp * 100) + '%';
    document.getElementById('enemy-hp-text').textContent = `${e.hp}/${e.maxHp}`;
    document.getElementById('energy-text').textContent = `⚡ ${p.energy}`;
    document.getElementById('block-text').textContent = `🛡 ${p.block}`;

    const stats = document.getElementById('combat-stats');
    stats.innerHTML = '';
    if (p.strength > 0) stats.innerHTML += `<span class="stat-badge">⚔ STR +${p.strength}</span>`;
    if (p.dexterity > 0) stats.innerHTML += `<span class="stat-badge">🛡 DEX +${p.dexterity}</span>`;

    const hand = document.getElementById('hand');
    hand.innerHTML = '';
    p.hand.forEach((card, i) => {
      const el = document.createElement('div');
      el.className = `card ${card.type}${p.energy < card.cost ? ' disabled' : ''}`;
      el.innerHTML = `
        <div class="card-cost">${card.cost}</div>
        <div class="card-name">${card.name}</div>
        <div class="card-value">${card.value || '✦'}</div>
        <div class="card-desc">${card.desc}</div>`;
      let tx, ty;
      el.addEventListener('pointerdown', ev => { tx = ev.clientX; ty = ev.clientY; });
      el.addEventListener('pointerup', ev => {
        if (Math.hypot(ev.clientX - tx, ev.clientY - ty) < 12) { ev.preventDefault(); this.playCard(i); }
      });
      hand.appendChild(el);
    });
  }

  _flash() {
    const v = document.getElementById('dungeon-view');
    v.classList.remove('damage-flash');
    void v.offsetWidth;
    v.classList.add('damage-flash');
  }

  // ── Input ─────────────────────────────────────

  _setupInput() {
    const on = (id, fn) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.addEventListener('pointerdown', e => { e.preventDefault(); fn(); });
    };
    on('btn-forward',     () => this._move(true));
    on('btn-back',        () => this._move(false));
    on('btn-left',        () => this._turn(true));
    on('btn-right',       () => this._turn(false));
    on('btn-end-turn',    () => this._enemyTurn());
    on('btn-skip-reward', () => this._returnToExplore());
    on('btn-toggle-map',  () => document.getElementById('minimap').classList.toggle('hidden'));

    window.addEventListener('keydown', e => {
      if (e.key === 'ArrowUp'    || e.key === 'w') this._move(true);
      if (e.key === 'ArrowDown'  || e.key === 's') this._move(false);
      if (e.key === 'ArrowLeft'  || e.key === 'a') this._turn(true);
      if (e.key === 'ArrowRight' || e.key === 'd') this._turn(false);
      if (e.key === 'Enter' || e.key === ' ')      this._enemyTurn();
    });
  }
}
