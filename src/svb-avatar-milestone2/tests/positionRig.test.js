import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { PositionRig } from '../src/positionRig.js';
import { demoPositionClip, samplePositionClip } from '../src/positionClip.js';

test('position rig creates every recorded point and bone link',()=>{
  const scene=new THREE.Scene();const rig=new PositionRig(scene);
  assert.equal(rig.root.visible,false);
  for(const side of ['left','right']){
    for(let i=0;i<21;i++)assert.ok(rig.dots[`${side}_hand_${i}`]);
    for(const joint of ['shoulder','elbow','wrist'])assert.ok(rig.dots[`${side}_${joint}`]);
  }
  const clip=demoPositionClip();
  const a=samplePositionClip(clip,0),b=samplePositionClip(clip,1200);
  rig.applyFrame(a);const first=rig.dots.left_wrist.position.y;
  rig.show(true);rig.applyFrame(b);
  assert.equal(rig.root.visible,true);
  assert.notEqual(rig.dots.left_wrist.position.y,first);
  assert.equal(rig.dots.right_hand_0.position.x,b.right_hand[0][0]);
  rig.setJointMarkersVisible(false);
  assert.equal(rig.dots.right_hand_20.visible,false);
});
