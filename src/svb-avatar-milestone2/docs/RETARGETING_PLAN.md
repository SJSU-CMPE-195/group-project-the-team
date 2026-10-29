# Milestone 2 design — captured MediaPipe landmarks → avatar motion

This is the **next** engineering milestone, not functionality already implemented in this zip.

## Why simple copy/paste of landmarks does not work

MediaPipe Hands may output normalized image landmarks (x/y in image proportions, wrist-origin z) and hand-world landmarks (meters around the hand's geometric center). A body pose may have yet another origin/scale. These cannot be directly combined into a coherent Three.js body without registration.

Moreover, the team's `(30, 68)` classification tensor is palm-normalized to be invariant to camera orientation. Such invariance intentionally discards motion detail important for avatar reconstruction.

## Source capture contract (proposed)

At capture time, preserve a timestamped track with:

- for each hand: 21 XYZ points in a documented coordinate space; left/right identity and detection score; track missing points explicitly;
- for upper body: left/right shoulder, elbow and wrist XYZ plus confidence/visibility;
- camera information: original width/height, whether frames were mirrored, coordinate units, and if possible intrinsics/calibration;
- original frame timestamps (do not assume exactly 30fps from the webcam).

Do not synthesize missing unseen body/finger positions without flagging that they're estimates.

## Retarget algorithm outline

1. **Choose neutral calibration frame** with visible shoulders and hands, and estimate body scale (shoulder distance) and hand scale (index-MCP–pinky-MCP span).
2. **Reconcile camera coordinates** into a right-handed avatar-centered reference (+Y up, +Z avatar-forward). Correct webcam mirroring and handedness explicitly.
3. **Estimate shoulder→elbow and elbow→wrist direction vectors.** Orient avatar upper/forearm segments to these directions; enforce avatar bone lengths. Constrained IK is preferable to copying lengths every frame.
4. **Estimate palm frame** from wrist, index MCP, pinky MCP. Use cross products to define palm axes and disambiguate palm roll. Check degenerate frames.
5. **Map each digit's MCP/PIP/DIP flex angles** from successive 3D segment directions. Clamp to anatomically plausible limits. Thumb requires its own axis/convention, not just the index-finger formula.
6. **Solve wrist orientation** from palm frame and forearm rotation. Continuous orientations can be interpolated with quaternion SLERP; avoid blindly interpolating Euler angles across ±180 degrees.
7. **Filter noise and repair occlusions** with confidence-aware temporal filtering, bounded interpolation, or reject too-poor source recordings. Preserve sign holds, apex and timing.
8. **Save browser-facing animation** with `svb.avatar.animation.v1` and recorded `time_ms`. Use one actual sign to validate before collecting all signs.
9. **Validate with ASL-fluent reviewer** on two camera angles and signer with different arm proportions; no sign marked verified automatically.

## Future schema versioning decision

This milestone's v1 playback accepts *joint angles*, not direct xyz coordinates. If robust retargeting requires explicit root pose, fingertip inverse kinematics, separate flex for each finger joint, or per-bone quaternions, publish `svb.avatar.pose.v2` and a migration layer; **do not mutate the v1 meaning silently**.

## Why not cubic spline every frame?

Cubic splines are useful for smoothing trajectories but may overshoot and modify handshapes. Prototype playback uses smoothstep interpolation between authored keyframes; **captured-sign motion should be resampled with explicit temporal constraints** and evaluated by ASL-fluent reviewers before use.

## Integration contract vs README

Keep original:

- `library/signs/<gloss>.json` metadata (gloss, English, templates, reviewer flag).
- `library/tensors/*.npy` `(30,68)` recognition templates.

Add:

- `library/avatar_sources/<id>` landmark source capture with pose, time, handedness.
- `library/avatar_frames/<id>` retargeted rig animation, or conversion when requested.
- sign metadata's `avatar_frames_file` points to playback track; FastAPI endpoint serves JSON.

The exact filenames/storage format still need team sign-off. No change to the original `(30,68)` recognition contract is necessary.

## ASL3DWord pathway in the current Milestone 2 package

For the approved ASL3DWord dataset (SMPL-X pose rotations rather than MediaPipe landmark recordings), use `ASL3DWORD_PIPELINE.md` instead. Direct 3D positional playback is now implemented in `src/positionRig.js` and `src/positionClip.js`; this file remains as the MediaPipe alternative.
