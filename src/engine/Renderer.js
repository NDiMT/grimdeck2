import * as THREE from 'three';

const TILE = 2;
const WALL_H = 2.6;
const EYE_Y = 1.15;

// camera.rotation.y per direction: N=0, E=1, S=2, W=3
const DIR_ANGLE = [0, -Math.PI / 2, Math.PI, Math.PI / 2];

// movement deltas per direction
const DIR_DX = [0, 1, 0, -1];
const DIR_DZ = [-1, 0, 1, 0];

export { TILE, DIR_DX, DIR_DZ };

export class Renderer {
  constructor(canvas) {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x000000);
    this.scene.fog = new THREE.FogExp2(0x000000, 0.09);

    this.camera = new THREE.PerspectiveCamera(72, 1, 0.05, 60);

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: false });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));

    this._setupLights();

    this.dungeonGroup = new THREE.Group();
    this.enemyGroup = new THREE.Group();
    this.scene.add(this.dungeonGroup, this.enemyGroup);

    this.torchTime = 0;
  }

  _setupLights() {
    // Very dark ambient, slightly cool
    this.scene.add(new THREE.AmbientLight(0x0d0d18, 1));

    // Torch: warm orange point light on the camera
    this.torch = new THREE.PointLight(0xff7722, 2.2, 9, 2);
    this.camera.add(this.torch);
    this.scene.add(this.camera);

    // Secondary cold light deep in corridor (static, dim)
    const coldLight = new THREE.PointLight(0x3355aa, 0.4, 15, 2);
    coldLight.position.set(0, WALL_H * 0.5, -20);
    this.scene.add(coldLight);
  }

  buildDungeon(grid) {
    this.dungeonGroup.clear();

    const wallMat = new THREE.MeshLambertMaterial({ color: 0x3a2b1e });
    const floorMat = new THREE.MeshLambertMaterial({ color: 0x191410 });
    const ceilMat = new THREE.MeshLambertMaterial({ color: 0x0c0b09 });

    const wallGeo = new THREE.BoxGeometry(TILE, WALL_H, TILE);
    const planeGeo = new THREE.PlaneGeometry(TILE, TILE);

    for (let z = 0; z < grid.length; z++) {
      for (let x = 0; x < grid[z].length; x++) {
        const wx = x * TILE;
        const wz = z * TILE;

        if (grid[z][x] === 1) {
          const wall = new THREE.Mesh(wallGeo, wallMat);
          wall.position.set(wx, WALL_H / 2, wz);
          this.dungeonGroup.add(wall);
        } else {
          const floor = new THREE.Mesh(planeGeo, floorMat);
          floor.rotation.x = -Math.PI / 2;
          floor.position.set(wx, 0, wz);
          this.dungeonGroup.add(floor);

          const ceil = new THREE.Mesh(planeGeo, ceilMat);
          ceil.rotation.x = Math.PI / 2;
          ceil.position.set(wx, WALL_H, wz);
          this.dungeonGroup.add(ceil);
        }
      }
    }
  }

  buildEnemyMarkers(enemies) {
    this.enemyGroup.clear();

    const eyeGeo = new THREE.SphereGeometry(0.07, 6, 6);
    const eyeMat = new THREE.MeshBasicMaterial({ color: 0xff2200 });

    enemies.forEach(enemy => {
      const marker = new THREE.Group();
      // Two glowing eyes
      [-0.15, 0.15].forEach(ox => {
        const eye = new THREE.Mesh(eyeGeo, eyeMat);
        eye.position.set(ox, 0, 0);
        marker.add(eye);
      });
      const glow = new THREE.PointLight(0xff1100, 0.8, 3, 2);
      marker.add(glow);

      marker.position.set(enemy.x * TILE, EYE_Y, enemy.z * TILE);
      marker.userData.enemy = enemy;
      this.enemyGroup.add(marker);
    });
  }

  updateEnemyMarkers() {
    this.enemyGroup.children.forEach(marker => {
      marker.visible = marker.userData.enemy.alive;
    });
  }

  setPlayer(x, z, dir) {
    this.camera.position.set(x * TILE, EYE_Y, z * TILE);
    this.camera.rotation.set(0, DIR_ANGLE[dir], 0);
  }

  resize(w, h) {
    this.renderer.setSize(w, h);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  render(dt) {
    this.torchTime += dt;
    this.torch.intensity =
      2.0 + Math.sin(this.torchTime * 6.3) * 0.12 + Math.sin(this.torchTime * 11.7) * 0.06;

    this.renderer.render(this.scene, this.camera);
  }
}
