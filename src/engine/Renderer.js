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
    this.scene.fog = new THREE.Fog(0x000000, 4, 22);

    this.camera = new THREE.PerspectiveCamera(72, 1, 0.05, 60);

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: false });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    this._setupLights();

    this.dungeonGroup = new THREE.Group();
    this.enemyGroup = new THREE.Group();
    this.scene.add(this.dungeonGroup, this.enemyGroup);

    this.torchTime = 0;
  }

  _setupLights() {
    this.scene.add(new THREE.AmbientLight(0x9a8858, 2.2));
    this.torch = new THREE.PointLight(0xffbb66, 9, 20, 2);
    this.camera.add(this.torch);
    this.scene.add(this.camera);
  }

  _loadTex(path) {
    const t = new THREE.TextureLoader().load(path);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  }

  buildDungeon(grid) {
    this.dungeonGroup.clear();

    const wMats = [
      new THREE.MeshLambertMaterial({ map: this._loadTex('/textures/wall.jpg') }),
      new THREE.MeshLambertMaterial({ map: this._loadTex('/textures/wall_rune.jpg') }),
      new THREE.MeshLambertMaterial({ map: this._loadTex('/textures/wall_torch.jpg') }),
      new THREE.MeshLambertMaterial({ map: this._loadTex('/textures/wall_skull.jpg') }),
    ];
    const fMat = new THREE.MeshLambertMaterial({ map: this._loadTex('/textures/floor.jpg') });
    const cMat = new THREE.MeshLambertMaterial({ color: 0x0e0c0a });

    const wallGeo = new THREE.PlaneGeometry(TILE, TILE);
    const pGeo = new THREE.PlaneGeometry(TILE, TILE);

    // [neighborDx, neighborDz, rotY, posOffsetX, posOffsetZ]
    const FACES = [
      [ 0, -1,  Math.PI,       0,        -TILE / 2],
      [ 1,  0,  Math.PI / 2,   TILE / 2,  0       ],
      [ 0,  1,  0,             0,          TILE / 2],
      [-1,  0, -Math.PI / 2,  -TILE / 2,  0       ],
    ];

    for (let z = 0; z < grid.length; z++) {
      for (let x = 0; x < grid[z].length; x++) {
        const wx = x * TILE;
        const wz = z * TILE;

        if (grid[z][x] === 1) {
          FACES.forEach(([dx, dz, rotY, ox, oz]) => {
            const nx = x + dx, nz = z + dz;
            if (!grid[nz] || grid[nz][nx] !== 0) return;
            const r = Math.random();
            const mat = r < 0.60 ? wMats[0] : r < 0.80 ? wMats[1] : r < 0.92 ? wMats[2] : wMats[3];
            const face = new THREE.Mesh(wallGeo, mat);
            face.position.set(wx + ox, TILE / 2, wz + oz);
            face.rotation.y = rotY;
            this.dungeonGroup.add(face);
          });
        } else {
          const floor = new THREE.Mesh(pGeo, fMat);
          floor.rotation.x = -Math.PI / 2;
          floor.position.set(wx, 0, wz);
          this.dungeonGroup.add(floor);

          const ceil = new THREE.Mesh(pGeo, cMat);
          ceil.rotation.x = Math.PI / 2;
          ceil.position.set(wx, WALL_H, wz);
          this.dungeonGroup.add(ceil);
        }
      }
    }
  }

  buildEnemyMarkers(enemies) {
    this.enemyGroup.clear();
    const loader = new THREE.TextureLoader();

    enemies.forEach(enemy => {
      const group = new THREE.Group();
      const tex = loader.load(`/sprites/${enemy.sprite}.png`);
      tex.magFilter = THREE.NearestFilter;
      tex.minFilter = THREE.NearestFilter;
      const sz = TILE * (enemy.size || 1.0);
      const fy = enemy.floatY || 0;
      const cy = sz / 2 + fy;

      // color tint matches dungeon ambient so sprite looks lit by the scene
      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({
        map: tex, transparent: true, alphaTest: 0.1, depthWrite: false,
        color: 0x997744,
      }));
      sprite.scale.set(sz, sz, 1);
      sprite.position.y = cy;
      group.add(sprite);

      const light = new THREE.PointLight(0xff2200, 0.3, 2.5, 2);
      light.position.y = cy;
      group.add(light);

      group.position.set(enemy.x * TILE, 0, enemy.z * TILE);
      group.userData.enemy = enemy;
      this.enemyGroup.add(group);
    });
  }

  updateEnemyMarkers() {
    this.enemyGroup.children.forEach(group => {
      group.visible = group.userData.enemy.alive;
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
      7.5 + Math.sin(this.torchTime * 6.3) * 0.5 + Math.sin(this.torchTime * 11.7) * 0.25;

    this.renderer.render(this.scene, this.camera);
  }
}
