# Silent Voice Bridge — Workstream B / Milestone 1

A **runnable standalone Three.js skeletal avatar** for the CMPE 195 Silent Voice Bridge project.

**Milestone 1 scope:** torso, shoulders, two upper arms, two elbows, forearms, wrists, **two hands with 21 MediaPipe-indexed joints each**, independent per-finger curl/spread controls, presets, 3D orbit/zoom, basic animation timeline, editable keyframes, JSON import/export, and an exported avatar-landmark snapshot.

**Not ASL recognition or translation.** The included wave/poses are **synthetic animation tests and not verified ASL signs**. Milestone 2 is actual MediaPipe capture, retargeting, and reviewer-verified playback. Microphone, text-to-gloss, live camera, FastAPI integration, and a real ASL sign library are intentionally not in this milestone.

## 1. Windows prerequisites

1. Install **Node.js 22.12+** from https://nodejs.org/ (current LTS is recommended). Node includes npm. Reopen PowerShell after installation.
2. Install **Visual Studio Code** (optional) and use Microsoft Edge or Chrome with hardware acceleration on.
3. Internet connection is needed **once** for installing JavaScript packages. The app can then run locally without fetching any remote data.

Check Node/npm in PowerShell:

```powershell
node --version
npm --version
```

There is no Python `.venv` for this milestone. This is a JavaScript project.

## 2. Run it on Windows

1. Extract `svb-avatar-milestone1.zip` somewhere such as `C:\Users\YourName\Projects\svb-avatar-milestone1`.
2. Open **PowerShell or the VS Code terminal inside the extracted folder** (the folder containing `package.json`).
3. Execute:

```powershell
npm install
npm run dev
```

4. Open **http://127.0.0.1:5173/** in Chrome or Edge. The development terminal must remain open while using the app.
5. Press `Ctrl+C` to stop the server.

**Shortcut:** Double-click `START_WINDOWS.bat` in that same folder. It verifies Node/npm, installs missing packages, then starts the server. PowerShell is recommended for seeing errors.

> If PowerShell says `npm.ps1 cannot be loaded because running scripts is disabled`, use **Command Prompt (`cmd`)** or call `npm.cmd install` and `npm.cmd run dev`. You do not need to change system execution policy.

## 3. What to test in the browser

1. The avatar is visible with a head, torso, and both arms/hands. Left arm is blue; right arm is purple.
2. The synthetic demo wave automatically animates a right-arm gesture. Press Pause and Play, then move the timeline slider and change playback speed.
3. Orbit with left drag, zoom with mouse wheel, pan with right drag.
4. Press **Both fists**, **Open hands**, or **Raise arms**. They should move both arms/hands. Presets are not ASL signs.
5. Select **Left arm**, change **Index curl**, then select **Right arm** and change **Pinky curl**. They should move independently.
6. Toggle **Show joints** and **Show grid**.
7. Press **Save pose** to export the current rig pose as JSON. Use **Import JSON** to reload it.
8. Press **New animation**, adjust a joint, set `Keyframe time = 500`, press **+ Add keyframe**. Make another change at `1000 ms`, add it, then Play. You have created your own 1-second test motion.
9. Press **Export animation**, reload via **Import JSON**, and play again.
10. **Export joints** outputs world positions of all 42 hand landmarks and 6 body joints. These are **rendered avatar positions, not camera detections**.

## 4. Code layout

```
svb-avatar-milestone1/
  index.html            # UI structure
  src/
    main.js             # Three.js scene, camera, user inputs and app
    rig.js              # procedural torso, two articulated arms, 21 joints/hand
    pose.js             # stable v1 pose/animation schemas and presets
    player.js           # seekable, frame-rate-independent animation player
    styles.css          # responsive visual interface
  tests/
    pose.test.js        # pose validation/interpolation/timeline unit tests
  examples/
    demo-wave-not-asl.json
  docs/
    TEAM_HANDOFF.md
    RETARGETING_PLAN.md
    ANIMATION_API.md
    TEST_PLAN.md
  START_WINDOWS.bat
  package.json
  .gitignore
```

## 5. Data formats

**Pose:** `svb.avatar.pose.v1` = degrees, `arms.left` and `arms.right`, each with shoulder `x/y/z`, elbow `flex`, wrist `x/y/z`, fingers (`thumb/index/middle/ring/pinky`) each with `curl` (0..1), `spread` (-1..1).

**Animation:** `svb.avatar.animation.v1` = timestamps and pose keyframes. See `examples/demo-wave-not-asl.json`.

```json
{
  "schema": "svb.avatar.animation.v1",
  "label": "TEST_ONLY",
  "angle_unit": "degrees",
  "coordinate_system": "rig_joint_angles",
  "verified_by_asl_reviewer": false,
  "keyframes": [
    { "time_ms": 0, "pose": { "schema": "svb.avatar.pose.v1", "arms": { "left": {}, "right": {} } } }
  ]
}
```

The above abbreviated pose is **not valid JSON input for the application**: all joint fields are required. Use the exported pose/animation or complete example file to see the actual data.

**Important:** The team's original `(30, 68)` recognition tensor is **unchanged**. This is a separate avatar-specific representation. Conversion from captured MediaPipe landmark positions to joint angles is **not part of this milestone**. `docs/RETARGETING_PLAN.md` describes how to build it next.

## 6. Integrate into team repository

Suggested placement under the existing project:

```
silent-voice-bridge/
  frontend/
    avatar-prototype/  # copy these files here initially
  library/
    signs/
    tensors/
```

Do **not** replace the team's existing frontend configuration or overwrite its package.json. First confirm whether the shared frontend uses Vite and Three.js; then move `src/rig.js`, `src/pose.js`, and `src/player.js` into its component folder and adapt `src/main.js` to its app lifecycle.

The target API is `GET /api/signs/{gloss}/animation`, returning a validated `svb.avatar.animation.v1` object. Reuben may store `.npy` files on the backend; the backend should convert them to a browser-friendly format. This API is a **proposal, not already implemented**.

## 7. Tests

```powershell
npm test
npm run build
```

`npm test` checks data structures and playback without requiring a browser. `npm run build` requires dependencies installed. Manual WebGL checks are listed in `docs/TEST_PLAN.md`.

## 8. Troubleshooting

- **Blank screen:** Open browser developer tools (`F12`) and inspect Console. Verify Chrome/Edge WebGL hardware acceleration is enabled. Try `npm run dev` again.
- **`npm` not found:** Reinstall Node.js and reopen terminal.
- **PowerShell policy error:** Use `npm.cmd` or Command Prompt instead of changing system policy.
- **Can't load page:** Look for the actual localhost port in terminal; port 5173 could be in use.
- **`vite` not found:** You skipped `npm install` or ran terminal from a different folder.
- **Pose import rejected:** File must contain all required fields, with the correct versioned `schema` and legal ranges.
- **Animation import rejected:** Clip keyframes must start at 0ms and have strictly increasing timestamps.
- **Hands don't form a recognizable ASL sign:** Correct: test poses are only intended to validate articulation, not teach ASL.

## 9. Current limitations

- Hands have visible joint-and-bone geometry, but not skin, realistic deformation, or facial grammar.
- Finger controls are simplified: one curl parameter drives MCP/PIP/DIP with distinct ratios. Per-joint angle control can be added after capture validation.
- Elbow uses a single flex axis. Shoulder and wrist have 3 Euler controls. This is a controlled prototype, not a complete anatomical/biomechanical model.
- The saved demo keyframes are synthetic and must **not** be labeled verified ASL.
- Transitions use simple smoothstep between keyframes (zero end velocity), not tested ASL coarticulation.
- The browser doesn't capture MediaPipe landmarks yet. It exports its **own** generated joint positions for inspection.
- Facial expression, body shift, and non-manual ASL markers are out of scope for the initial avatar.
- No offline Docker packaging or Jetson port included yet.

## References

- Three.js documentation: https://threejs.org/docs/ and https://threejs.org/manual/#en/installation
- MediaPipe Hand Landmarker: https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/web_js
- Original team README, Section 4 shared contracts (unchanged).
