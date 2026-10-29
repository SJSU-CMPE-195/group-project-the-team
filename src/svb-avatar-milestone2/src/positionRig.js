import * as THREE from 'three';
import {BODY_KEYS,HAND_EDGES,validatePositionFrame} from './positionClip.js';
const Y=new THREE.Vector3(0,1,0), V=(p)=>new THREE.Vector3(...p);
const sphere=(r,color)=>new THREE.Mesh(new THREE.SphereGeometry(r,12,9),new THREE.MeshStandardMaterial({color,roughness:.4}));
export class PositionRig {
  constructor(scene){
    this.root=new THREE.Group();this.root.name='Direct 3D joint position skeleton';scene.add(this.root);this.root.visible=false;
    this.dots={};this.edges=[];
    const addDot=(name,r,color)=>{const x=sphere(r,color);x.name=name;this.root.add(x);this.dots[name]=x;};
    const addEdge=(a,b,r,color)=>{
      const mesh=new THREE.Mesh(new THREE.CylinderGeometry(r,r,1,9),new THREE.MeshStandardMaterial({color,roughness:.5}));this.root.add(mesh);
      this.edges.push({a,b,mesh});
    };
    for(const side of ['left','right']){
      const col=side==='left'?0x38bdf8:0xa78bfa;
      for(const key of ['shoulder','elbow','wrist'])addDot(`${side}_${key}`,.033,col);
      addEdge(`${side}_shoulder`,`${side}_elbow`,.027,col);
      addEdge(`${side}_elbow`,`${side}_wrist`,.023,col);
      for(let i=0;i<21;i++)addDot(`${side}_hand_${i}`,i===0?.018:.011,i%4===0?0xfbbf24:0xe1efff);
      for(const [a,b] of HAND_EDGES)addEdge(`${side}_hand_${a}`,`${side}_hand_${b}`,.007,col);
      // connect explicitly to wrist for continuity
      addEdge(`${side}_wrist`,`${side}_hand_0`,.010,col);
    }
    addEdge('left_shoulder','right_shoulder',.043,0x73869f);
    this.torso=new THREE.Mesh(new THREE.BoxGeometry(.5,.45,.21),new THREE.MeshStandardMaterial({color:0x253b57,roughness:.75}));this.root.add(this.torso);
    this.head=sphere(.13,0xc6d9ec);this.head.scale.set(.9,1.12,.8);this.root.add(this.head);
    this.markers=true;
  }
  show(visible){this.root.visible=visible;}
  setJointMarkersVisible(show){this.markers=show;for(const p of Object.values(this.dots))p.visible=show;}
  applyFrame(f){
    validatePositionFrame(f);
    for(const key of BODY_KEYS)this.dots[key].position.fromArray(f[key]);
    for(const side of ['left','right'])f[`${side}_hand`].forEach((p,i)=>this.dots[`${side}_hand_${i}`].position.fromArray(p));
    for(const {a,b,mesh} of this.edges){
      const av=this.dots[a].position,bv=this.dots[b].position,dir=new THREE.Vector3().subVectors(bv,av);
      mesh.position.copy(av).add(bv).multiplyScalar(.5);
      const len=dir.length();mesh.visible=len>0.0001;
      if(len>.0001){mesh.quaternion.setFromUnitVectors(Y,dir.normalize());mesh.scale.set(1,len,1);}
    }
    const l=this.dots.left_shoulder.position,r=this.dots.right_shoulder.position;
    this.torso.position.copy(l).add(r).multiplyScalar(.5).add(new THREE.Vector3(0,-.25,0));
    this.head.position.copy(l).add(r).multiplyScalar(.5).add(new THREE.Vector3(0,.28,0));
  }
}
