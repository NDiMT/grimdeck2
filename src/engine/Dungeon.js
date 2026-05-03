const FLOOR1_ENEMIES = [
  {name:'Skeleton',   hp:18, attack:5, sprite:'skeleton', glowColor:0xff3300, size:1.0},
  {name:'Goblin',     hp:14, attack:7, sprite:'goblin',   glowColor:0x44ff00, size:0.85},
  {name:'Zombie',     hp:26, attack:4, sprite:'zombie',   glowColor:0x77ff22, size:1.0},
  {name:'Dark Bat',   hp:10, attack:8, sprite:'bat',      glowColor:0x9933ff, size:0.85, floatY:0.3},
  {name:'Cave Troll', hp:32, attack:6, sprite:'troll',    glowColor:0x4488aa, size:1.3},
  {name:'Shade',      hp:20, attack:6, sprite:'shade',    glowColor:0x6600cc, size:1.0},
  {name:'Rat Pack',   hp:15, attack:5, sprite:'rat',      glowColor:0xff4400, size:0.8},
  {name:'Cursed Eye', hp:22, attack:7, sprite:'eye',      glowColor:0xff0000, size:0.75, floatY:0.4},
];

export class Dungeon {
  constructor(width = 22, height = 22) {
    this.width = width;
    this.height = height;
    this.grid = null;
    this.rooms = [];
    this.startPos = null;
    this.enemies = [];
    this.generate();
  }

  generate() {
    this.grid = Array.from({ length: this.height }, () => new Array(this.width).fill(1));
    this.rooms = [];

    for (let att = 0; att < 100 && this.rooms.length < 12; att++) {
      const rw = this.rand(3, 7), rh = this.rand(3, 6);
      const rx = this.rand(1, this.width - rw - 1);
      const ry = this.rand(1, this.height - rh - 1);
      const c = { x: rx, y: ry, w: rw, h: rh };
      if (this.rooms.every(r => !this.overlaps(r, c, 1))) {
        this.carveRoom(c);
        if (this.rooms.length > 0) this.connectRooms(this.rooms[this.rooms.length - 1], c);
        this.rooms.push(c);
      }
    }

    const f = this.rooms[0];
    this.startPos = { x: f.x + Math.floor(f.w / 2), z: f.y + Math.floor(f.h / 2) };

    this.enemies = this.rooms.slice(1).map(room => {
      const t = FLOOR1_ENEMIES[this.rand(0, FLOOR1_ENEMIES.length - 1)];
      return {
        x: room.x + Math.floor(room.w / 2),
        z: room.y + Math.floor(room.h / 2),
        hp: t.hp, maxHp: t.hp, attack: t.attack, name: t.name, alive: true,
        sprite: t.sprite, glowColor: t.glowColor, size: t.size, floatY: t.floatY || 0,
      };
    });
  }

  rand(a, b) { return Math.floor(Math.random() * (b - a + 1)) + a; }

  overlaps(a, b, p = 0) {
    return !(a.x + a.w + p <= b.x || b.x + b.w + p <= a.x ||
             a.y + a.h + p <= b.y || b.y + b.h + p <= a.y);
  }

  carveRoom(r) {
    for (let z = r.y; z < r.y + r.h; z++)
      for (let x = r.x; x < r.x + r.w; x++) this.grid[z][x] = 0;
  }

  connectRooms(a, b) {
    let cx = a.x + Math.floor(a.w / 2), cz = a.y + Math.floor(a.h / 2);
    const tx = b.x + Math.floor(b.w / 2), tz = b.y + Math.floor(b.h / 2);
    while (cx !== tx) { this.grid[cz][cx] = 0; cx += cx < tx ? 1 : -1; }
    while (cz !== tz) { this.grid[cz][cx] = 0; cz += cz < tz ? 1 : -1; }
  }

  isWall(x, z) {
    return x < 0 || z < 0 || x >= this.width || z >= this.height || this.grid[z][x] === 1;
  }

  getEnemyAt(x, z) { return this.enemies.find(e => e.alive && e.x === x && e.z === z); }
}
