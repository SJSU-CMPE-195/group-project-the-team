# Silent Voice Bridge — Workstream B / Milestone 2

**Continuation of the working Milestone 1 Three.js project, now with a dataset-ready 3D joint-position player.**

## What's new

- **Direct 3D positional skeleton**: independently updated left/right shoulders, elbows, wrists, and 21 indexed hand points per side.
- Browser import, playback, scrub, loop, and export of `svb.avatar.positions.v1` JSON clips.
- **Synthetic positional test** button demonstrates that the new mode works. It is intentionally NOT a real ASL sign.
- Strict validation and time-linear interpolation (no fake pauses at source frame boundaries).
- `tools/inspect_asl3dword.py`: safely inspect authorized dataset metadata without unpickling it.
- `tools/positions_npz_to_json.py`: validate and convert *already reconstructed and correctly mapped* 3D joint-position arrays to the browser format.
- Original `svb.avatar.pose.v1`/`svb.avatar.animation.v1` player and controls remain usable.

## Critical limitation

**This package does not contain ASL3DWord or SMPL-X assets and DOES NOT yet play a genuine ASL3DWord sign.** The dataset must be requested from the researchers, and conversion of its 3D rotation data to a correctly mapped positional skeleton requires the source files/official SMPL-X model. This cannot be validated in their absence.

Read `docs/ASL3DWORD_PIPELINE.md` for the data contract, geometry pitfalls, and next experiment.

## Windows quick start (same as before)

1. Extract project.
2. Open the folder with `package.json` in VS Code.
3. Install Node.js 22.12+ (if not already done).
4. PowerShell:

```powershell
npm install
npm run dev
```

5. Open http://127.0.0.1:5173/ in your browser.
6. Click **Play positional test (NOT ASL)**. The viewer switches from the old angle-driven rig to an automatically updated full 3D joint-position skeleton.
7. Pause, scrub, orbit, change speed, or export. Click **Demo wave** or a **Quick pose** to return to Milestone 1 angle controls.
8. Click **Import pose / motion JSON** to open a JSON file created by the conversion script.

## Python data tools (optional until dataset access)

Use Python 3.10+ and install NumPy into a Python virtual environment (separate from the Node project):

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install numpy
.venv\Scripts\python.exe tools\inspect_asl3dword.py "C:\datasets\ASL3DWord" --max-files 20
```

Once you have a valid **already reconstructed 3D joint-position NPZ** (not raw SMPL-X rotations):

```powershell
.venv\Scripts\python.exe tools\positions_npz_to_json.py "C:\datasets\reconstructed.npz" "examples\HELLO.json" --label HELLO --fps 30
```

Do NOT use 30 fps unless the source FPS has been verified. If `times_ms` is present in NPZ, `--fps` is ignored.

## Tests

```powershell
npm test
npm run build
.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```

Tests cover positional schema, linear interpolation, runtime clock, timestamp validation, wrist alignment, and the original pose/animation system. The browser needs `npm install` to run Three.js and Vite.

## Main files

```
src/main.js                  dual-mode UI
src/rig.js                   original angle-driven skeleton
src/pose.js                  original stable v1 pose/animation contract
src/positionRig.js           NEW position-driven 3D skeleton
src/positionClip.js          NEW position schema/player/sample motion
examples/synthetic-position-not-asl.json

tools/inspect_asl3dword.py   metadata inspection, safe by default
tools/positions_npz_to_json.py   validated positional data converter
docs/ASL3DWORD_PIPELINE.md  next steps, geometry, API, constraints
```

All synthetic examples remain explicitly marked unverified. Additional sign labels must not be claimed until ASL-fluent review.
