# Workstream B — Team handoff / decisions to approve

## Decisions now adopted for Workstream B prototype

1. **Three.js procedural skeleton**: torso, shoulders, 2 arms, independently articulated fingers, exactly 21 indexed joint markers per hand.
2. **One shared library**: existing `library/signs/<gloss>.json` metadata remains the source of truth.
3. **Do not change recognition tensors**: `(30, 68)` canonical-palm-space remains Workstream A's contract.
4. **Add an avatar source track** captured from MediaPipe *before* aggressive palm normalization: timestamps, 21 hand landmarks on each side, left/right identity, upper-body shoulder/elbow/wrist tracks, visibility and whether the camera was mirrored.
5. **Add an avatar playback track** retargeted into `svb.avatar.animation.v1` angles/timestamps. The browser uses this file; recognition stays separate.
6. **Use one coordinate convention**: Three.js +Y up, +Z forward/toward viewer, avatar anatomical LEFT at positive X, angles in degrees, 3D lengths in meters. Capture-to-rig calibration is necessary.
7. **Short inter-sign transition**: start at 200ms and test with an ASL-fluent reviewer. Protect the internal sign's sequence/timing; no global spline reshaping.
8. **Gloss pipeline**: fixed reviewed phrase table for the first 10–15 signs. Don't claim unrestricted ASL translation. If unavailable, explicit unsupported response; later only fingerspell with verified A–Z assets.
9. **Review**: don't set `verified_by_asl_reviewer` true without fluent reviewer approval.
10. **Timeline**: milestone 1 rig; milestone 2 capture and retarget one real sign; milestone 3 text/gloss and sequences; milestone 4 speech/fingerspelling/polish.

## Responsibilities

**Nathaniel (B):** Three.js rig, pose schema, animation player, UI, pose editing, versioned browser playback contract; later English-to-gloss, controlled transitions, fingerspelling, STT.

**Reuben (D):** Record/store avatar source motion plus recognition tensor; define API endpoint `GET /api/signs/{gloss}/animation`; make source-to-rig adapter available (collaborate with Nathaniel); finalize `.npy` storage vs JSON delivery.

**Aramish (A):** Preserve normalized `(30, 68)` DTW path; ensure capture module exposes full hand/pose motion to shared library before data reduction.

**Ruby (C):** Reuse Nathaniel's avatar player for tutor demonstration, use same gloss identifiers and reviewer flags.

## API proposal (not implemented)

`GET /api/signs/HELLO/animation`

Returns a `svb.avatar.animation.v1` JSON object. 404 when absent. Backend may use `.npy` storage internally. Frontend must not have to parse recognition tensors as avatar motion.

## Questions requiring the team's explicit agreement

- Is the live MediaPipe source available **before** wrist/palm normalization for both hands and pose?
- Are source frames from one fixed camera and capture orientation, or mixed? Mirroring must be explicit.
- Who will implement or jointly validate captured-landmark-to-avatar-angle retargeting?
- Who is the ASL-fluent reviewer, and which phrases/signs make up v1?
- Where does the endpoint live in the existing FastAPI API and what is the HTTP error format?

## Acceptance criteria for milestone 1

- Both hands visible, each exposes 21 MediaPipe-style landmark markers (42 total).
- Both shoulders, elbows, wrists, and individual fingers visibly move.
- Pose and animation JSON serialize, validate, import/export, and replay.
- Browser interaction works on Windows Chrome/Edge, with FPS smooth enough to inspect signs (measure on target laptop).
- Test wave is explicitly identified as synthetic non-ASL motion.
- Unit tests for pose validity and keyframe sampling pass.
