/**
 * Stable browser-facing avatar motion contract: svb.avatar.pose.v1 and
 * svb.avatar.animation.v1. This is NOT a MediaPipe recognition tensor.
 * Units: degrees, seconds encoded as integer milliseconds, meters in renderer.
 */
export const POSE_SCHEMA = 'svb.avatar.pose.v1';
export const ANIMATION_SCHEMA = 'svb.avatar.animation.v1';
export const FINGERS = Object.freeze(['thumb', 'index', 'middle', 'ring', 'pinky']);
export const SIDES = Object.freeze(['left', 'right']);

const copy = (value) => JSON.parse(JSON.stringify(value));
export const clonePose = copy;
const hand = () => Object.fromEntries(FINGERS.map((name) => [name, { curl: 0.08, spread: 0 }]));

export function neutralPose() {
  return {
    schema: POSE_SCHEMA,
    arms: {
      left: {
        shoulder: { x: -12, y: 0, z: 19 },
        elbow: { flex: 12 },
        wrist: { x: 0, y: 0, z: 0 },
        hand: hand(),
      },
      right: {
        shoulder: { x: -12, y: 0, z: -19 },
        elbow: { flex: 12 },
        wrist: { x: 0, y: 0, z: 0 },
        hand: hand(),
      },
    },
  };
}

export function presetPose(name) {
  const pose = neutralPose();
  if (name === 'neutral') return pose;
  if (name === 'open') {
    for (const side of SIDES) for (const finger of FINGERS) pose.arms[side].hand[finger].curl = 0;
  } else if (name === 'fist') {
    for (const side of SIDES) for (const finger of FINGERS) pose.arms[side].hand[finger].curl = 0.98;
  } else if (name === 'point') {
    for (const side of SIDES) {
      for (const finger of FINGERS) pose.arms[side].hand[finger].curl = finger === 'index' ? 0 : 0.95;
      pose.arms[side].shoulder.x = -25;
      pose.arms[side].elbow.flex = 70;
    }
  } else if (name === 'raise') {
    pose.arms.left.shoulder.z = 120;
    pose.arms.right.shoulder.z = -120;
    pose.arms.left.elbow.flex = 16;
    pose.arms.right.elbow.flex = 16;
  } else {
    throw new Error(`Unknown preset: ${name}`);
  }
  return pose;
}

const EXPECTED_RANGES = Object.freeze({
  'shoulder.x': [-150, 150], 'shoulder.y': [-100, 100], 'shoulder.z': [-165, 165],
  'elbow.flex': [0, 155],
  'wrist.x': [-90, 90], 'wrist.y': [-90, 90], 'wrist.z': [-90, 90],
});

function requireObject(value, path) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${path} must be an object`);
  }
}
function requireNumber(value, path, min, max) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < min || value > max) {
    throw new Error(`${path} must be finite and between ${min} and ${max}`);
  }
}

export function validatePose(pose) {
  requireObject(pose, 'pose');
  if (pose.schema !== POSE_SCHEMA) throw new Error(`Expected pose schema ${POSE_SCHEMA}`);
  requireObject(pose.arms, 'pose.arms');
  for (const side of SIDES) {
    const arm = pose.arms[side];
    requireObject(arm, `arms.${side}`);
    for (const part of ['shoulder', 'elbow', 'wrist', 'hand']) requireObject(arm[part], `arms.${side}.${part}`);
    for (const [key, [min, max]] of Object.entries(EXPECTED_RANGES)) {
      const [part, field] = key.split('.');
      requireNumber(arm[part][field], `arms.${side}.${key}`, min, max);
    }
    for (const finger of FINGERS) {
      const joint = arm.hand[finger];
      requireObject(joint, `arms.${side}.hand.${finger}`);
      requireNumber(joint.curl, `arms.${side}.hand.${finger}.curl`, 0, 1);
      requireNumber(joint.spread, `arms.${side}.hand.${finger}.spread`, -1, 1);
    }
  }
  return pose;
}

export function interpolatePose(a, b, t) {
  validatePose(a); validatePose(b);
  if (!Number.isFinite(t)) throw new Error('Interpolation fraction must be finite');
  t = Math.max(0, Math.min(1, t));
  const result = clonePose(a);
  const mix = (u, v) => u + (v - u) * t;
  for (const side of SIDES) {
    for (const key of ['x', 'y', 'z']) {
      result.arms[side].shoulder[key] = mix(a.arms[side].shoulder[key], b.arms[side].shoulder[key]);
      result.arms[side].wrist[key] = mix(a.arms[side].wrist[key], b.arms[side].wrist[key]);
    }
    result.arms[side].elbow.flex = mix(a.arms[side].elbow.flex, b.arms[side].elbow.flex);
    for (const finger of FINGERS) {
      for (const prop of ['curl', 'spread']) {
        result.arms[side].hand[finger][prop] = mix(a.arms[side].hand[finger][prop], b.arms[side].hand[finger][prop]);
      }
    }
  }
  return result;
}

export function validateClip(clip) {
  requireObject(clip, 'clip');
  if (clip.schema !== ANIMATION_SCHEMA) throw new Error(`Expected animation schema ${ANIMATION_SCHEMA}`);
  if (typeof clip.label !== 'string' || !clip.label.trim() || clip.label.length > 100) throw new Error('Invalid clip label');
  if (clip.angle_unit !== 'degrees') throw new Error('angle_unit must be degrees');
  if (clip.coordinate_system !== 'rig_joint_angles') throw new Error('coordinate_system must be rig_joint_angles');
  if (!Array.isArray(clip.keyframes) || clip.keyframes.length < 1 || clip.keyframes.length > 10000) {
    throw new Error('Clip needs 1-10000 keyframes');
  }
  let lastTime = -1;
  for (let i = 0; i < clip.keyframes.length; i++) {
    const kf = clip.keyframes[i];
    requireObject(kf, `keyframes[${i}]`);
    requireNumber(kf.time_ms, `keyframes[${i}].time_ms`, 0, 600000);
    if (kf.time_ms <= lastTime) throw new Error('Keyframe times must be strictly increasing');
    lastTime = kf.time_ms;
    validatePose(kf.pose);
  }
  if (clip.keyframes[0].time_ms !== 0) throw new Error('First keyframe must start at 0 ms');
  return clip;
}

export const clipDurationMs = (clip) => clip.keyframes[clip.keyframes.length - 1].time_ms;

export function sampleClip(clip, timeMs) {
  // Validating on load is sufficient; the player calls this every frame.
  const kfs = clip.keyframes;
  if (kfs.length === 1 || timeMs <= kfs[0].time_ms) return clonePose(kfs[0].pose);
  if (timeMs >= clipDurationMs(clip)) return clonePose(kfs[kfs.length - 1].pose);
  let lo = 0, hi = kfs.length - 1;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (kfs[mid].time_ms <= timeMs) lo = mid; else hi = mid;
  }
  const a = kfs[lo], b = kfs[hi];
  const linearT = (timeMs - a.time_ms) / (b.time_ms - a.time_ms);
  // smoothstep has zero velocity at keyframe boundaries: fine for a prototype,
  // but do not treat it as linguistically validated ASL motion.
  const smoothT = linearT * linearT * (3 - 2 * linearT);
  return interpolatePose(a.pose, b.pose, smoothT);
}

export function singlePoseClip(pose, label = 'CUSTOM_POSE') {
  validatePose(pose);
  const clip = {
    schema: ANIMATION_SCHEMA, label, angle_unit: 'degrees', coordinate_system: 'rig_joint_angles',
    verified_by_asl_reviewer: false,
    keyframes: [{ time_ms: 0, pose: clonePose(pose) }],
  };
  return validateClip(clip);
}

export function demonstrationWave() {
  const rest = neutralPose();
  const raised = clonePose(rest);
  raised.arms.right.shoulder.x = -45;
  raised.arms.right.shoulder.z = -40;
  raised.arms.right.elbow.flex = 110;
  raised.arms.right.wrist.x = -18;
  for (const finger of FINGERS) raised.arms.right.hand[finger].curl = 0;
  const waveLeft = clonePose(raised), waveRight = clonePose(raised);
  waveLeft.arms.right.wrist.z = -29;
  waveRight.arms.right.wrist.z = 29;
  const k = (t, pose) => ({time_ms: t, pose});
  return validateClip({
    schema: ANIMATION_SCHEMA, label: 'DEMO_WAVE_NOT_ASL', angle_unit: 'degrees',
    coordinate_system: 'rig_joint_angles', verified_by_asl_reviewer: false,
    keyframes: [k(0, rest), k(520, raised), k(820, waveLeft), k(1150, waveRight),
      k(1480, waveLeft), k(1810, waveRight), k(2220, raised), k(2770, rest)],
  });
}
