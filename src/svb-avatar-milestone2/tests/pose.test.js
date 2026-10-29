import test from 'node:test';
import assert from 'node:assert/strict';
import {
  FINGERS, SIDES, clonePose, neutralPose, presetPose,
  validatePose, validateClip, interpolatePose, sampleClip,
  demonstrationWave, singlePoseClip, clipDurationMs,
} from '../src/pose.js';
import { AnimationPlayer } from '../src/player.js';

test('neutral pose has two arms and individually controlled finger joints', () => {
  const pose = validatePose(neutralPose());
  assert.equal(SIDES.length,2);
  assert.equal(FINGERS.length,5);
  for (const side of SIDES) assert.deepEqual(Object.keys(pose.arms[side].hand), FINGERS);
});

test('preset curls correctly apply to all 10 fingers',()=>{
  const fist = presetPose('fist'), open=presetPose('open');
  for(const side of SIDES)for(const finger of FINGERS){
    assert.equal(fist.arms[side].hand[finger].curl,.98);
    assert.equal(open.arms[side].hand[finger].curl,0);
  }
  assert.throws(()=>presetPose('fake'),/Unknown/);
});

test('invalid joint ranges and missing finger are rejected',()=>{
  const p=neutralPose();p.arms.left.elbow.flex=250;
  assert.throws(()=>validatePose(p),/between/);
  const q=neutralPose();delete q.arms.right.hand.thumb;
  assert.throws(()=>validatePose(q),/thumb/);
});

test('interpolation is deterministic and leaves inputs unchanged',()=>{
  const a=neutralPose(),b=clonePose(a);
  b.arms.left.wrist.z=60;b.arms.right.hand.index.curl=.8;
  const c=interpolatePose(a,b,.5);
  assert.equal(c.arms.left.wrist.z,30);
  assert.ok(Math.abs(c.arms.right.hand.index.curl-.44)<1e-12);
  assert.equal(a.arms.left.wrist.z,0);
  assert.equal(interpolatePose(a,b,-3).arms.left.wrist.z,0);
  assert.equal(interpolatePose(a,b,3).arms.left.wrist.z,60);
});

test('demo clip has strictly ascending time and meaningful motion',()=>{
  const clip=validateClip(demonstrationWave());
  assert.equal(clip.keyframes.length,8);
  assert.equal(clip.verified_by_asl_reviewer,false);
  assert.equal(clipDurationMs(clip),2770);
  assert.notEqual(sampleClip(clip,900).arms.right.wrist.z,sampleClip(clip,1200).arms.right.wrist.z);
  assert.deepEqual(sampleClip(clip,-3),clip.keyframes[0].pose);
  assert.deepEqual(sampleClip(clip,10000),clip.keyframes.at(-1).pose);
});

test('single-pose clip has zero duration, player stops safely',()=>{
  const clip=singlePoseClip(neutralPose());const player=new AnimationPlayer(clip);
  player.playing=true;player.tick(250);
  assert.equal(player.playing,false);assert.equal(player.playheadMs,0);
});

test('animation player advances, loops, seeks, and pauses',()=>{
  const player=new AnimationPlayer(demonstrationWave());
  player.playing=true;player.tick(500);
  assert.equal(player.playheadMs,500);
  player.tick(3000);
  assert.equal(player.playheadMs,730);
  player.seek(100000);assert.equal(player.playheadMs,2770);
  player.loop=false;player.playing=true;player.seek(2700);player.tick(100);
  assert.equal(player.playheadMs,2770);assert.equal(player.playing,false);
});

test('imported JSON round-trips and invalid timeline is rejected',()=>{
  const source=demonstrationWave(),clip=JSON.parse(JSON.stringify(source));
  assert.deepEqual(validateClip(clip),source);
  clip.keyframes[1].time_ms=0;
  assert.throws(()=>validateClip(clip),/strictly increasing/);
});
