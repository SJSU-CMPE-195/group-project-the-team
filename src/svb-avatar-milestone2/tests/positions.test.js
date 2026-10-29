import test from 'node:test';
import assert from 'node:assert/strict';
import { demoPositionClip, validatePositionClip, positionDurationMs, samplePositionClip, PositionPlayer, HAND_EDGES } from '../src/positionClip.js';

test('synthetic position clip matches v1 data contract',()=>{
  const c=demoPositionClip();assert.equal(c.schema,'svb.avatar.positions.v1');
  assert.equal(c.frames.length,49);assert.equal(positionDurationMs(c),2400);
  assert.equal(c.frames[0].joints.left_hand.length,21);
  assert.equal(c.frames[0].joints.right_hand.length,21);
});
test('all fingers have connected edges',()=>{
  for (const tip of [4,8,12,16,20]) assert.ok(HAND_EDGES.some(edge=>edge.includes(tip)));
});
test('position clips interpolate linearly between frames',()=>{
  const c=demoPositionClip();
  const a=samplePositionClip(c,0),b=samplePositionClip(c,50),middle=samplePositionClip(c,25);
  for (const k of ['left_elbow','right_wrist'])for(let i=0;i<3;i++)assert.ok(Math.abs(middle[k][i]-(a[k][i]+b[k][i])/2)<1e-9);
});
test('reject missing or misordered fingers',()=>{
  const c=demoPositionClip();c.frames[0].joints.left_hand=[];
  assert.throws(()=>validatePositionClip(c),/21 points/);
});
test('reject detached wrist',()=>{
  const c=demoPositionClip();c.frames[0].joints.right_hand[0][0]+=1;
  assert.throws(()=>validatePositionClip(c),/wrist/);
});
test('position player seek, play, stop',()=>{
  const p=new PositionPlayer(demoPositionClip());p.loop=false;p.playing=true;
  const a=p.tick(500);assert.equal(p.playheadMs,500);assert.equal(a.left_hand.length,21);
  p.tick(3000);assert.equal(p.playheadMs,2400);assert.equal(p.playing,false);
  p.seek(0);assert.equal(p.playheadMs,0);
});
