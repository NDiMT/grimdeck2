const STARTER_DECK = [
  { id: 'strike',     name: 'Strike',      cost: 1, type: 'attack', value: 6,  desc: 'Deal 6 damage' },
  { id: 'strike',     name: 'Strike',      cost: 1, type: 'attack', value: 6,  desc: 'Deal 6 damage' },
  { id: 'strike',     name: 'Strike',      cost: 1, type: 'attack', value: 6,  desc: 'Deal 6 damage' },
  { id: 'heavy',      name: 'Heavy Blow',  cost: 2, type: 'attack', value: 14, desc: 'Deal 14 damage' },
  { id: 'defend',     name: 'Defend',      cost: 1, type: 'block',  value: 5,  desc: 'Gain 5 block' },
  { id: 'defend',     name: 'Defend',      cost: 1, type: 'block',  value: 5,  desc: 'Gain 5 block' },
  { id: 'quick_step', name: 'Quick Step',  cost: 0, type: 'block',  value: 3,  desc: 'Gain 3 block' },
];

export class Player {
  constructor(x, z) {
    this.x = x;
    this.z = z;
    this.dir = 0; // 0=N 1=E 2=S 3=W

    this.hp = 80;
    this.maxHp = 100;
    this.block = 0;

    this.deck = STARTER_DECK.map(c => ({ ...c }));
    this.hand = [];
    this.energy = 3;
    this.maxEnergy = 3;
  }

  // movement delta for current direction (forward)
  forwardDelta() {
    const DX = [0, 1, 0, -1];
    const DZ = [-1, 0, 1, 0];
    return { dx: DX[this.dir], dz: DZ[this.dir] };
  }

  turnLeft()  { this.dir = (this.dir + 3) % 4; }
  turnRight() { this.dir = (this.dir + 1) % 4; }
  moveTo(x, z) { this.x = x; this.z = z; }

  // Draw n cards from shuffled deck
  drawHand(n = 4) {
    const shuffled = [...this.deck].sort(() => Math.random() - 0.5);
    this.hand = shuffled.slice(0, n);
    this.energy = this.maxEnergy;
    this.block = 0;
  }
}
