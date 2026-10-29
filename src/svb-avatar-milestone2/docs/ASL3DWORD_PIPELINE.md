# Milestone 2 technical contract — ASL3DWord -> Three.js

## Status

**Implemented/tested:** Three.js world-position skeleton; time-accurate linear interpolation; schema validation; browser import/export; source-independent NPZ -> JSON converter; safe metadata inspector; synthetic test motion.

**Not completed or claimed:** Real ASL3DWord sign replay. No restricted dataset files or SMPL-X licensed model are bundled. We cannot know/validate final source array structure, joint mapping, frame rate, coordinate conventions, or individual sign quality until access has been granted and the source files inspected.

## Why joint positions rather than your Milestone-1 angle controls?

The existing v1 rig stores one curl and spread per finger, plus 1 elbow flex degree of freedom. That's too restrictive for full SMPL-X rotations. Direct positions preserve the reconstructed shoulder/elbow/wrist/finger trajectories without projecting them into an approximate curl model. This is a **second player mode**; it doesn't change v1.

ASL3DWord is described by authors as *3D joint rotation data* reconstructed from sign-word video. Replaying it requires an additional **forward kinematics / SMPL-X reconstruction** step. You cannot simply treat rotation vectors as xyz points, and you cannot assume the author's array axes, joint ordering, or fps before inspection.

## Stage A — obtain authorization and inspect source

- Request access from `ludong@buffalo.edu`; the official repository requests name, institution, purpose, resource (dataset / checkpoint / both) and research-use agreement.
- Obtain the official SMPL-X neutral model separately under its own license as needed. Do not copy the model into our public repository or ZIP.
- Use the **official author's code** and documentation as the source of truth for the specific ASL3DWord pose representation; sample data may be stored in a format other than plain `.npy` arrays.
- Place the granted files outside Git, for example `C:\datasets\ASL3DWord`.
- Run `python tools/inspect_asl3dword.py C:\datasets\ASL3DWord --max-files 20`.
- Report 1) sample extension, 2) array names/shapes and 3) label/fps mapping; do NOT guess.

## Stage B — reconstruct source into 3D positions

Run the authors' SMPL-X-compatible reconstruction/forward-kinematics workflow **using authorized local model files**. Determine the ordering and rest-pose calibration for the body and hands. Export these arrays to a **new** NPZ file:

- `body_points`: float32/float64 of shape `(T,6,3)`, anatomical `left_shoulder`, `left_elbow`, `left_wrist`, `right_shoulder`, `right_elbow`, `right_wrist`.
- `hand_points`: `(T,2,21,3)`, side 0 anatomical left, side 1 anatomical right, and **MediaPipe index order 0..20** for each hand (0=wrist; thumb 1..4; index 5..8; middle 9..12; ring 13..16; pinky 17..20).
- `times_ms` optional: `(T,)` increasing timestamps (the converter starts timeline at 0).

**Important:** SMPL-X uses a different hand joint ordering and typically doesn't natively contain all 21 MediaPipe-style wrist/base/tip landmarks. This intermediate 21-point mapping is a deliberate, source-specific step to develop after seeing the granted dataset and official SMPL-X joint/mesh outputs. Fingertips may need to be obtained from the mesh, and some MediaPipe MCP/CMC landmarks may need conventions. Do **not** fill unavailable points by silently copying other joints.

### Alignment conventions

- Three.js world meters, `+Y` up, `+Z` avatar forward and toward the camera, anatomical left has positive `X` when facing viewer (at front view).
- Place shoulders roughly around `Y=1.54m` for this prototype; align torso center `X=0`. Use one consistent rigid 3D transform + uniform scale for the whole track, **not** per-joint recentering.
- Do not swap left/right based on mirrored webcams without verifying anatomical sides.
- Check that hand landmark 0 and associated wrist position agree within 10 cm (hard error otherwise).
- Keep the native recording speed. Don't automatically resample to the recognition tensor's 30 steps.

## Stage C — export and play

```
python -m pip install numpy
python tools/positions_npz_to_json.py path/to/reconstructed.npz path/to/HELLO.json --label HELLO --fps 30
```

Use `--fps` only if the source lacks `times_ms` and you **verified** its sample rate. The tool performs strict shape, finiteness, timestamp and wrist checks. It does not silently map SMPL-X joints or infer coordinate frames.

In the app, click **Import pose / motion JSON** and choose `HELLO.json`. The position skeleton plays automatically. Use **Pause**, **timeline scrub**, and orbit camera to inspect finger motion. Compare handshapes and trajectories with the reference sign video. Never mark verified without ASL-fluent review.

## Browser JSON contract — `svb.avatar.positions.v1`

```json
{
  "schema": "svb.avatar.positions.v1",
  "label": "EXAMPLE_UNVERIFIED",
  "coordinate_system": "threejs_world_m",
  "units": "meters",
  "source": "external_reconstructed_skeleton",
  "verified_by_asl_reviewer": false,
  "frames": [
    {"time_ms": 0, "joints": {
      "left_shoulder": [0.305,1.54,0], "left_elbow": [0.4,1.2,0], "left_wrist": [0.4,0.9,0],
      "right_shoulder": [-0.305,1.54,0], "right_elbow": [-0.4,1.2,0], "right_wrist": [-0.4,0.9,0],
      "left_hand": "...must be array of 21 xyz vectors...",
      "right_hand": "...must be array of 21 xyz vectors..."
    }}
  ]
}
```

Note: hand placeholders above are explanatory, not valid JSON motion. For a complete valid clip see `examples/synthetic-position-not-asl.json`.

## Workstream contracts

- **Reuben**: preserve both original recognition `(30,68)` templates and distinct avatar position clips; no change to original DTW tensor contract. Agree upon `avatar_frames_file` or a backend endpoint returning the browser schema.
- **Nathaniel**: source importer, positional playback, reviewer comparison, integration into English-to-gloss lookup.
- **Ruby**: Learn Mode can reuse the browser player using an imported approved animation.
- **Aramish**: recognition can still use its own source-normalized template; do not feed these world positions to recognition without matching its feature definition.

## Acceptance test for one genuine sign

1. Source asset is demonstrably part of the licensed dataset and maps to a known gloss/recording ID.
2. Source's original FPS, units, coordinate frame and joint ordering are documented.
3. Full 3D position arrays are reconstructed (not fabricated from a plausible example).
4. JSON schema validates; playback doesn't jump or mirror the signer, and both hands stay attached to wrists.
5. Review the rendered motion side by side with original video and get ASL-fluent feedback.
6. Only then add it to the shared production library.

## Links / attribution

Official authors' repo: https://github.com/dongludeeplearning/SignAvatar
Paper/project: https://dongludeeplearning.github.io/SignAvatar.html
SMPL-X model licensing: https://smpl-x.is.tue.mpg.de/

The SignAvatar repository lists a CC BY-NC 4.0 license; respect dataset/resource-specific terms and do not redistribute restricted files.
