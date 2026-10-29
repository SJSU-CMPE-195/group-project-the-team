# Proposed backend ↔ avatar frontend API — draft for Reuben and Nathaniel

This is an **integration proposal**. It is not a live endpoint in milestone 1. The existing team README defines the high-level avatar input `{ "gloss_sequence": ["HELLO", "HOW", "YOU"], "fingerspell": [] }`; that input remains valid and should ultimately drive the library lookup.

## Example HTTP request

`GET /api/signs/HELLO/animation`

- `200` when available and retargeted.
- `404` when not present. UI should display `Unsupported sign: HELLO`, not silently insert a random pose.
- `422` when source exists but is unusable (missing landmarks, conversion failure).
- Respond with JSON and appropriate CORS settings for the frontend origin (only if cross-origin).

## Body: `svb.avatar.animation.v1`

```json
{
  "schema": "svb.avatar.animation.v1",
  "label": "HELLO",
  "angle_unit": "degrees",
  "coordinate_system": "rig_joint_angles",
  "verified_by_asl_reviewer": false,
  "keyframes": [
    { "time_ms": 0, "pose": "FULL_POSE_OBJECT_REQUIRED" },
    { "time_ms": 500, "pose": "FULL_POSE_OBJECT_REQUIRED" }
  ]
}
```

The `pose` values above are **placeholders**, not valid payloads. Use the exported demo file for a complete accepted example.

### Pose object shape

```text
schema: "svb.avatar.pose.v1"
arms:
  left:
    shoulder: {x: number, y: number, z: number}    # degrees
    elbow: {flex: number}                          # degrees
    wrist: {x: number, y: number, z: number}       # degrees
    hand:
      thumb:  {curl: number, spread: number}       # 0..1 and -1..1
      index:  {curl: number, spread: number}
      middle: {curl: number, spread: number}
      ring:   {curl: number, spread: number}
      pinky:  {curl: number, spread: number}
  right: (same as left)
```

The included `validatePose` and `validateClip` functions reject out-of-range/incomplete data.

## World and handedness conventions

- Three.js world is right-handed; +Y up, +Z toward viewer.
- Avatar anatomical left = +X on the stage; anatomical right = -X.
- Angle convention is **our avatar rig's local axes**, not raw MediaPipe angles. Shoulder and wrist are local XYZ Euler angles (degrees); elbow flex is a positive degree value that bends forearm forward; fingers use normalized curl/spread.
- Positive/negative MediaPipe `z` and image X/Y values **must not** be copied to Three.js directly; calibrate/retarget separately.
- Front-camera mirroring must be documented; left/right labeling cannot be inferred from screen X alone.
- Pose durations are in `time_ms`, monotonic, first sample at 0.

## Backend storage vs browser delivery

Existing sign metadata may still use `"avatar_frames_file": "hello_001_avatar.npy"`. If so, the FastAPI loader should read `.npy`, interpret its **explicitly documented axis/order and schema**, and convert it to the JSON shape before the browser sees it.

Do not push the team's `(30,68)` recognition tensors through the avatar API: those are not the rig-angle format.

## Future versioning

If the ML/IK adapter needs a root global transform, joint-by-joint flexion, bone quaternions or per-frame confidence flags, define a new version and update both loader and renderer explicitly. Do not change what `svb.avatar.animation.v1` means in place.
