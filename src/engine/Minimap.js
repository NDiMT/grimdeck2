export class Minimap {
  constructor(canvas, dungeon) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.cs = 5;
    this.grid = dungeon.grid;
    canvas.width  = dungeon.width  * this.cs;
    canvas.height = dungeon.height * this.cs;
    const display = Math.min(110, dungeon.width * this.cs);
    canvas.style.width  = display + 'px';
    canvas.style.height = display + 'px';
  }

  update(player, enemies, visited) {
    const { ctx, cs, grid } = this;

    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    for (let z = 0; z < grid.length; z++) {
      for (let x = 0; x < grid[z].length; x++) {
        if (!visited.has(`${x},${z}`)) continue;
        ctx.fillStyle = grid[z][x] === 1 ? '#1a1510' : '#5a4838';
        ctx.fillRect(x * cs, z * cs, cs, cs);
      }
    }

    enemies.forEach(e => {
      if (e.alive || !visited.has(`${e.x},${e.z}`)) return;
      ctx.fillStyle = 'rgba(80,60,50,.6)';
      ctx.fillRect(e.x * cs + 1, e.z * cs + 1, cs - 2, cs - 2);
    });

    enemies.forEach(e => {
      if (!e.alive || !visited.has(`${e.x},${e.z}`)) return;
      ctx.fillStyle = '#cc2200';
      ctx.beginPath();
      ctx.arc((e.x + .5) * cs, (e.z + .5) * cs, cs * .42, 0, Math.PI * 2);
      ctx.fill();
    });

    const px = (player.x + .5) * cs;
    const pz = (player.z + .5) * cs;
    ctx.fillStyle = '#c9a84c';
    ctx.beginPath();
    ctx.arc(px, pz, cs * .55, 0, Math.PI * 2);
    ctx.fill();

    const angle = [-Math.PI / 2, 0, Math.PI / 2, Math.PI][player.dir];
    ctx.strokeStyle = '#ffe080';
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(px, pz);
    ctx.lineTo(px + Math.cos(angle) * cs * 1.4, pz + Math.sin(angle) * cs * 1.4);
    ctx.stroke();
  }
}
