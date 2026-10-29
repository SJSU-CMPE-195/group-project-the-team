import * as THREE from 'three';
import { FINGERS, SIDES, validatePose } from './pose.js';

const rad = (degrees) => degrees * Math.PI / 180;
const UNIT_Y = new THREE.Vector3(0, 1, 0);
const SEGMENTS = {
  thumb: [0.049, 0.040, 0.032], index: [0.063, 0.046, 0.034],
  middle: [0.071, 0.051, 0.039], ring: [0.066, 0.046, 0.035],
  pinky: [0.052, 0.035, 0.027],
};
const LABELS = ['wrist', 'thumb_cmc','thumb_mcp','thumb_ip','thumb_tip',
  'index_mcp','index_pip','index_dip','index_tip',
  'middle_mcp','middle_pip','middle_dip','middle_tip',
  'ring_mcp','ring_pip','ring_dip','ring_tip',
  'pinky_mcp','pinky_pip','pinky_dip','pinky_tip'];

function joint(group, r, color, landmarks, label) {
  const sphere = new THREE.Mesh(
    new THREE.SphereGeometry(r, 12, 8),
    new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.10, roughness: 0.4 }),
  );
  group.add(sphere);
  if (landmarks && label) landmarks[label] = { group, sphere };
  return sphere;
}
function connector(parent, pointA, pointB, radius, material) {
  const dir = new THREE.Vector3().subVectors(pointB, pointA);
  const length = dir.length();
  if (length < 0.00001) return;
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, length, 10), material);
  mesh.position.copy(pointA).add(pointB).multiplyScalar(0.5);
  mesh.quaternion.setFromUnitVectors(UNIT_Y, dir.normalize());
  parent.add(mesh);
  return mesh;
}
function downwardBone(group, length, radius, material) {
  return connector(group, new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, -length, 0), radius, material);
}
function childAt(parent, x, y, z) {
  const g = new THREE.Group();
  g.position.set(x, y, z);
  parent.add(g);
  return g;
}

export class AvatarRig {
  constructor(scene) {
    this.root = new THREE.Group();
    this.root.name = 'Silent Voice Bridge avatar skeleton';
    scene.add(this.root);
    this.arms = {};
    this.jointMeshes = [];
    this.allLandmarks = {};
    this.makeTorso();
    for (const side of SIDES) this.makeArm(side);
  }

  makeTorso() {
    const cloth = new THREE.MeshStandardMaterial({color: 0x253b57, roughness: 0.68, metalness: 0.12});
    const trim = new THREE.MeshStandardMaterial({color: 0x577b9f, roughness: 0.45});
    const body = new THREE.Mesh(new THREE.BoxGeometry(0.50, 0.48, 0.25), cloth);
    body.position.y = 1.30;
    this.root.add(body);
    const pelvis = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.15, 0.22), cloth);
    pelvis.position.y = 1.01;
    this.root.add(pelvis);
    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.065, 0.075, 0.13, 16), trim);
    neck.position.y = 1.61;
    this.root.add(neck);
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.145, 26, 18), new THREE.MeshStandardMaterial({color: 0xc6d9ec, roughness: .75}));
    head.scale.set(0.86, 1.09, 0.81);
    head.position.set(0, 1.82, 0.01);
    this.root.add(head);
    const face = new THREE.Mesh(new THREE.SphereGeometry(0.025, 12, 8), new THREE.MeshBasicMaterial({color: 0x334155}));
    for (const x of [-0.053,0.053]) {
      const eye=face.clone();eye.position.set(x,1.84,0.124);this.root.add(eye);
    }
    const spine = new THREE.Mesh(new THREE.CylinderGeometry(0.013,0.013,0.40,10), trim);
    spine.position.set(0,1.29,0.142);this.root.add(spine);
  }

  makeArm(side) {
    const isLeft = side === 'left';
    const anatomicalSign = isLeft ? 1 : -1;
    const color = isLeft ? 0x38bdf8 : 0xa78bfa;
    const material = new THREE.MeshStandardMaterial({color, roughness: 0.34, metalness: 0.14});
    const handMaterial = new THREE.MeshStandardMaterial({color: isLeft ? 0x7dd3fc : 0xc4b5fd, roughness: .4});
    const shoulder = childAt(this.root, anatomicalSign * 0.305, 1.54, 0);
    this.jointMeshes.push(joint(shoulder, .053, color, null, null));
    downwardBone(shoulder, 0.33, .037, material);
    const elbow = childAt(shoulder, 0, -0.33, 0);
    this.jointMeshes.push(joint(elbow, .046, color, null, null));
    downwardBone(elbow, 0.29, .030, material);
    const wrist = childAt(elbow, 0, -0.29, 0);
    this.jointMeshes.push(joint(wrist, .030, color, null, null));
    const handRoot = childAt(wrist, 0, 0, 0);
    const landmarks = {};
    const visibleWrist = joint(handRoot, .014, 0xf8fafc, landmarks, 'wrist');
    this.jointMeshes.push(visibleWrist);

    const slotValues = {index:-0.047, middle:-0.015, ring:0.019, pinky:0.050};
    const roots = {};
    const palmBases = [];
    for (const finger of FINGERS) {
      const isThumb = finger === 'thumb';
      const x = isThumb ? -0.080 * anatomicalSign : slotValues[finger] * anatomicalSign;
      const y = isThumb ? -0.052 : -0.134;
      const fingerRoot = childAt(handRoot, x, y, 0);
      const baseName = isThumb ? 'thumb_cmc' : `${finger}_mcp`;
      const baseSphere = joint(fingerRoot, .014, 0xf8fafc, landmarks, baseName);
      this.jointMeshes.push(baseSphere);
      connector(handRoot, new THREE.Vector3(0,0,0), new THREE.Vector3(x,y,0), .011, handMaterial);
      if (!isThumb) palmBases.push([x,y]);
      const [l1,l2,l3] = SEGMENTS[finger];
      const r = isThumb ? .010 : .008;
      downwardBone(fingerRoot, l1, r, handMaterial);
      const second = childAt(fingerRoot, 0, -l1, 0);
      const secondName = isThumb ? 'thumb_mcp' : `${finger}_pip`;
      this.jointMeshes.push(joint(second, .012, 0xf8fafc, landmarks, secondName));
      downwardBone(second, l2, r*.88, handMaterial);
      const third = childAt(second, 0, -l2, 0);
      const thirdName = isThumb ? 'thumb_ip' : `${finger}_dip`;
      this.jointMeshes.push(joint(third, .010, 0xf8fafc, landmarks, thirdName));
      downwardBone(third, l3, r*.73, handMaterial);
      const tip = childAt(third, 0, -l3, 0);
      this.jointMeshes.push(joint(tip, .010, 0xfbbf24, landmarks, `${finger}_tip`));
      roots[finger] = {base: fingerRoot, middle: second, distal: third};
    }
    palmBases.sort((a,b)=>a[0]-b[0]);
    for (let i=0;i<palmBases.length-1;i++) {
      connector(handRoot, new THREE.Vector3(...palmBases[i],0), new THREE.Vector3(...palmBases[i+1],0), .009, handMaterial);
    }
    this.allLandmarks[side] = landmarks;
    this.arms[side] = {shoulder,elbow,wrist,handRoot,roots,anatomicalSign};
  }

  applyPose(pose) {
    validatePose(pose);
    for (const side of SIDES) {
      const arm = this.arms[side];
      const data = pose.arms[side];
      arm.shoulder.rotation.set(rad(data.shoulder.x),rad(data.shoulder.y),rad(data.shoulder.z),'XYZ');
      arm.elbow.rotation.x = -rad(data.elbow.flex);
      arm.wrist.rotation.set(rad(data.wrist.x),rad(data.wrist.y),rad(data.wrist.z),'XYZ');
      for (const finger of FINGERS) {
        const {base,middle,distal} = arm.roots[finger];
        const {curl,spread} = data.hand[finger];
        if (finger === 'thumb') {
          base.rotation.set(-0.20-curl*0.50,0,-0.88*arm.anatomicalSign+spread*0.4,'XYZ');
          middle.rotation.x = -curl*0.92;
          distal.rotation.x = -curl*0.76;
        } else {
          base.rotation.set(-curl*0.90,0,spread*0.30*arm.anatomicalSign,'XYZ');
          middle.rotation.x = -curl*1.30;
          distal.rotation.x = -curl*0.90;
        }
      }
    }
    this.root.updateMatrixWorld(true);
  }

  setJointMarkersVisible(visible) {
    for (const sphere of this.jointMeshes) sphere.visible = visible;
  }

  getLandmarkPositions() {
    this.root.updateMatrixWorld(true);
    const result = {};
    for (const side of SIDES) {
      result[side] = LABELS.map((name) => {
        const item = this.allLandmarks[side][name];
        if (!item) throw new Error(`Missing landmark ${side}.${name}`);
        return item.group.getWorldPosition(new THREE.Vector3()).toArray();
      });
    }
    return result;
  }

  getJointSummary() {
    this.root.updateMatrixWorld(true);
    return Object.fromEntries(SIDES.map((side)=>[side, {
      shoulder: this.arms[side].shoulder.getWorldPosition(new THREE.Vector3()).toArray(),
      elbow: this.arms[side].elbow.getWorldPosition(new THREE.Vector3()).toArray(),
      wrist: this.arms[side].wrist.getWorldPosition(new THREE.Vector3()).toArray(),
    }]));
  }
}

export const MEDIAPIPE_HAND_LABELS = Object.freeze([...LABELS]);
