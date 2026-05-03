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

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
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
    t.magFilter = THREE.LinearFilter;
    t.minFilter = THREE.LinearMipmapLinearFilter;
    t.anisotropy = this.renderer.capabilities.getMaxAnisotropy();
    return t;
  }

  buildDungeon(grid) {
    this.dungeonGroup.clear();

    const wMats = [
      new THREE.MeshLambertMaterial({ map: this._loadTex('/textures/wall.png') }),
      new THREE.MeshLambertMaterial({ map: this._loadTex('/textures/wall_chain.png') }),
      new THREE.MeshLambertMaterial({ map: this._loadTex('/textures/wall_torch.png') }),
      new THREE.MeshLambertMaterial({ map: this._loadTex('/textures/wall_skull.png') }),
      new THREE.MeshLambertMaterial({ map: this._loadTex('/textures/wall_demon.png') }),
    ];
    const fMats = [
      new THREE.MeshLambertMaterial({ map: this._loadTex('/textures/floor.png') }),
      new THREE.MeshLambertMaterial({ map: this._loadTex('/textures/floor2.png') }),
      new THREE.MeshLambertMaterial({ map: this._loadTex('/textures/floor3.png') }),
      new THREE.MeshLambertMaterial({ map: this._loadTex('/textures/floor4.png') }),
      new THREE.MeshLambertMaterial({ map: this._loadTex('/textures/floor5.png') }),
    ];

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
            const mat = r < 0.55 ? wMats[0] : r < 0.72 ? wMats[1] : r < 0.84 ? wMats[2] : r < 0.93 ? wMats[3] : wMats[4];
            const face = new THREE.Mesh(wallGeo, mat);
            face.position.set(wx + ox, TILE / 2, wz + oz);
            face.rotation.y = rotY;
            this.dungeonGroup.add(face);
          });
        } else {
          const fr = Math.random();
          const fMat = fr < 0.60 ? fMats[0] : fr < 0.74 ? fMats[1] : fr < 0.84 ? fMats[2] : fr < 0.93 ? fMats[3] : fMats[4];
          const floor = new THREE.Mesh(pGeo, fMat);
          floor.rotation.x = -Math.PI / 2;
          floor.position.set(wx, 0, wz);
          this.dungeonGroup.add(floor);
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
      tex.colorSpace = THREE.SRGBColorSpace;
      tex.magFilter = THREE.LinearFilter;
      tex.minFilter = THREE.LinearFilter;
      const sz = TILE * (enemy.size || 1.0);
      const fy = enemy.floatY || 0;
      const cy = sz / 2 + fy;

      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({
        map: tex, transparent: true, alphaTest: 0.1, depthWrite: false,
        fog: true,
      }));
      sprite.scale.set(sz, sz, 1);
      sprite.position.y = cy;
      group.add(sprite);

      const light = new THREE.PointLight(0xffbb66, 1.5, 4, 2);
      light.position.y = cy;
      group.add(light);

      group.position.set(enemy.x * TILE, 0, enemy.z * TILE);
      group.userData.enemy = enemy;
      group.userData.sprite = sprite;
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

    this.enemyGroup.children.forEach(group => {
      if (!group.visible) return;
    });

    this.renderer.render(this.scene, this.camera);
  }
}
