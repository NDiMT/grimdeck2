const ENEMY_NAMES = ['Skeleton', 'Goblin', 'Wraith', 'Zombie', 'Cultist'];

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

    for (let attempt = 0; attempt < 100 && this.rooms.length < 12; attempt++) {
      const rw = this.rand(3, 7);
      const rh = this.rand(3, 6);
      const rx = this.rand(1, this.width - rw - 1);
      const ry = this.rand(1, this.height - rh - 1);
      const candidate = { x: rx, y: ry, w: rw, h: rh };

      if (this.rooms.every(r => !this.overlaps(r, candidate, 1))) {
        this.carveRoom(candidate);
        if (this.rooms.length > 0) {
          this.connectRooms(this.rooms[this.rooms.length - 1], candidate);
        }
        this.rooms.push(candidate);
      }
    }

    const first = this.rooms[0];
    this.startPos = {
      x: first.x + Math.floor(first.w / 2),
      z: first.y + Math.floor(first.h / 2),
    };

    this.enemies = this.rooms.slice(1).map(room => {
      const hp = 20 + this.rand(0, 20);
      return {
        x: room.x + Math.floor(room.w / 2),
        z: room.y + Math.floor(room.h / 2),
        hp,
        maxHp: hp,
        attack: 5 + this.rand(0, 5),
        name: ENEMY_NAMES[this.rand(0, ENEMY_NAMES.length - 1)],
        alive: true,
      };
    });
  }

  rand(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  overlaps(a, b, pad = 0) {
    return !(
      a.x + a.w + pad <= b.x || b.x + b.w + pad <= a.x ||
      a.y + a.h + pad <= b.y || b.y + b.h + pad <= a.y
    );
  }

  carveRoom(room) {
    for (let z = room.y; z < room.y + room.h; z++) {
      for (let x = room.x; x < room.x + room.w; x++) {
        this.grid[z][x] = 0;
      }
    }
  }

  connectRooms(a, b) {
    let cx = a.x + Math.floor(a.w / 2);
    let cz = a.y + Math.floor(a.h / 2);
    const tx = b.x + Math.floor(b.w / 2);
    const tz = b.y + Math.floor(b.h / 2);

    while (cx !== tx) {
      this.grid[cz][cx] = 0;
      cx += cx < tx ? 1 : -1;
    }
    while (cz !== tz) {
      this.grid[cz][cx] = 0;
      cz += cz < tz ? 1 : -1;
    }
  }

  isWall(x, z) {
    if (x < 0 || z < 0 || x >= this.width || z >= this.height) return true;
    return this.grid[z][x] === 1;
  }

  getEnemyAt(x, z) {
    return this.enemies.find(e => e.alive && e.x === x && e.z === z);
  }
}
