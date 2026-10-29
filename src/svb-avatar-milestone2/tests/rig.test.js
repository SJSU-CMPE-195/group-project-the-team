import test from 'node:test';
import assert from 'node:assert/strict';
import { neutralPose, clonePose } from '../src/pose.js';

// These tests run after `npm install` has installed Three.js.
// Without dependencies installed, unit tests for the pure pose/player layer still run.
let THREE, AvatarRig, MEDIAPIPE_HAND_LABELS;
try {
  THREE = await import('three');
  ({ AvatarRig, MEDIAPIPE_HAND_LABELS } = await import('../src/rig.js'));
} catch (error) {
  if (error.code !== 'ERR_MODULE_NOT_FOUND') throw error;
}

test('rig has exactly 21 hand landmarks per side in expected indexing', {skip: !THREE}, () => {
  const scene = new THREE.Scene();
  const rig = new AvatarRig(scene);
  rig.applyPose(neutralPose());
  assert.equal(MEDIAPIPE_HAND_LABELS.length, 21);
  assert.equal(MEDIAPIPE_HAND_LABELS[0], 'wrist');
  assert.equal(MEDIAPIPE_HAND_LABELS[4], 'thumb_tip');
  assert.equal(MEDIAPIPE_HAND_LABELS[8], 'index_tip');
  assert.equal(MEDIAPIPE_HAND_LABELS[20], 'pinky_tip');
  const hands = rig.getLandmarkPositions();
  for(const side of ['left','right']) {
    assert.equal(hands[side].length,21);
    for(const point of hands[side]) {
      assert.equal(point.length,3);
      assert.ok(point.every(Number.isFinite));
    }
  }
});

test('only left index finger moves when its curl changes', {skip: !THREE}, () => {
  const rig = new AvatarRig(new THREE.Scene());
  const initial = neutralPose();
  rig.applyPose(initial);
  const before = rig.getLandmarkPositions();
  const moved = clonePose(initial);
  moved.arms.left.hand.index.curl = 0.95;
  rig.applyPose(moved);
  const after = rig.getLandmarkPositions();
  assert.notDeepEqual(after.left[8],before.left[8]);
  assert.deepEqual(after.right[8],before.right[8]);
  assert.deepEqual(after.left[12],before.left[12]);
});

test('separate arms have independent elbow transforms', {skip: !THREE}, () => {
  const rig = new AvatarRig(new THREE.Scene());
  const start=neutralPose();rig.applyPose(start);
  const before=rig.getJointSummary();
  const moved=clonePose(start);moved.arms.right.elbow.flex=100;
  rig.applyPose(moved);
  const after=rig.getJointSummary();
  assert.notDeepEqual(after.right.wrist,before.right.wrist);
  assert.deepEqual(after.left.wrist,before.left.wrist);
});
