export const CARDS = [
  // Starter deck
  {id:'st1',name:'Strike',       cost:1,type:'attack',effect:'damage',    value:6,  starter:true, desc:'Deal 6 dmg'},
  {id:'st2',name:'Strike',       cost:1,type:'attack',effect:'damage',    value:6,  starter:true, desc:'Deal 6 dmg'},
  {id:'st3',name:'Strike',       cost:1,type:'attack',effect:'damage',    value:6,  starter:true, desc:'Deal 6 dmg'},
  {id:'st4',name:'Heavy Blow',   cost:2,type:'attack',effect:'damage',    value:14, starter:true, desc:'Deal 14 dmg'},
  {id:'st5',name:'Defend',       cost:1,type:'block', effect:'block',     value:5,  starter:true, desc:'Gain 5 block'},
  {id:'st6',name:'Defend',       cost:1,type:'block', effect:'block',     value:5,  starter:true, desc:'Gain 5 block'},
  {id:'st7',name:'Quick Step',   cost:0,type:'block', effect:'block',     value:3,  starter:true, desc:'Gain 3 block'},
  // Rewards — Attacks
  {id:'r01',name:'Twin Strike',  cost:1,type:'attack',effect:'damage',    value:5,  hits:2,        desc:'5 dmg twice'},
  {id:'r02',name:'Whirlwind',    cost:0,type:'attack',effect:'whirlwind', value:6,                 desc:'6 dmg × energy left'},
  {id:'r03',name:'Body Slam',    cost:1,type:'attack',effect:'bodyslam',  value:0,                 desc:'dmg = your Block'},
  {id:'r04',name:'Pommel Strike',cost:1,type:'attack',effect:'damage',    value:9,  draw:1,        desc:'9 dmg + draw 1'},
  {id:'r05',name:'Headbutt',     cost:1,type:'attack',effect:'damage',    value:9,                 desc:'Deal 9 dmg'},
  {id:'r06',name:'Cleave',       cost:1,type:'attack',effect:'damage',    value:8,                 desc:'Deal 8 dmg'},
  {id:'r07',name:'Thunderclap',  cost:1,type:'attack',effect:'damage',    value:11,                desc:'Deal 11 dmg'},
  {id:'r08',name:'Carnage',      cost:2,type:'attack',effect:'damage',    value:20, exhaust:true,  desc:'20 dmg. Exhaust'},
  // Rewards — Blocks
  {id:'r09',name:'Shrug It Off', cost:1,type:'block', effect:'block',     value:11, draw:1,        desc:'11 block + draw 1'},
  {id:'r10',name:'Impervious',   cost:2,type:'block', effect:'block',     value:30, exhaust:true,  desc:'30 block. Exhaust'},
  {id:'r11',name:'Entrench',     cost:2,type:'block', effect:'entrench',  value:0,                 desc:'Double your Block'},
  {id:'r12',name:'Iron Wave',    cost:1,type:'block', effect:'iron_wave', value:5,                 desc:'5 dmg and 5 block'},
  // Rewards — Powers
  {id:'r13',name:'Inflame',      cost:1,type:'power', effect:'strength',  value:2,                 desc:'+2 STR this combat'},
  {id:'r14',name:'Armaments',    cost:1,type:'power', effect:'dexterity', value:2,                 desc:'+2 DEX this combat'},
  {id:'r15',name:'Flex',         cost:0,type:'power', effect:'strength',  value:2,                 desc:'+2 STR this combat'},
  {id:'r16',name:'Spot Weakness',cost:1,type:'power', effect:'strength',  value:3, exhaust:true,   desc:'+3 STR. Exhaust'},
  // Rewards — Skills
  {id:'r17',name:'Bloodletting', cost:0,type:'skill', effect:'bloodletting',value:0,               desc:'−3 HP, gain 2 energy'},
  {id:'r18',name:'Battle Trance',cost:0,type:'skill', effect:'draw',      value:3,                 desc:'Draw 3 cards'},
  {id:'r19',name:'Seeing Red',   cost:1,type:'skill', effect:'energy',    value:2, exhaust:true,   desc:'+2 energy. Exhaust'},
  {id:'r20',name:'Second Wind',  cost:1,type:'skill', effect:'second_wind',value:5,                desc:'5 block per non-attack in hand'},
  {id:'r21',name:'Offering',     cost:0,type:'skill', effect:'offering',  value:0, exhaust:true,   desc:'−6 HP, +2 energy, draw 3'},
];

export class Player {
  constructor(x, z) {
    this.x = x; this.z = z; this.dir = 0;
    this.hp = 80; this.maxHp = 100;
    this.block = 0; this.strength = 0; this.dexterity = 0;
    this.deck = CARDS.filter(c => c.starter).map(c => ({ ...c }));
    this.hand = []; this.energy = 3; this.maxEnergy = 3;
  }

  forwardDelta() {
    return { dx: [0, 1, 0, -1][this.dir], dz: [-1, 0, 1, 0][this.dir] };
  }

  turnLeft()  { this.dir = (this.dir + 3) % 4; }
  turnRight() { this.dir = (this.dir + 1) % 4; }
  moveTo(x, z) { this.x = x; this.z = z; }

  startCombat() {
    this.strength = 0;
    this.dexterity = 0;
    this.drawHand();
  }

  drawHand(n = 7) {
    this.hand = [...this.deck].sort(() => Math.random() - 0.5).slice(0, n);
    this.energy = this.maxEnergy;
    this.block = 0;
  }
}
