# Manual QA checklist — milestone 1

## Test setup

Windows 10/11, Chrome or Edge, Node.js 22.12+, `npm install`, `npm run dev`. Open `http://127.0.0.1:5173/`.

- [ ] Browser shows a torso, head, blue anatomical left arm and purple anatomical right arm.
- [ ] Both hands contain 21 points in the expected MediaPipe ordering (0 wrist, thumb 1–4, index 5–8, middle 9–12, ring 13–16, pinky 17–20).
- [ ] Orbit, zoom, and pan operate; page does not scroll unexpectedly while dragging canvas.
- [ ] Synthetic wave auto-plays, Pause and Play stop/start, timeline scrubbing visibly changes right arm.
- [ ] Loop toggle stops playback at end when unchecked; speed 2x plays faster than 0.5x.
- [ ] Neutral/Open/Fist/Point/Raise presets animate both hands/arms.
- [ ] Left-arm index curl can change without moving right-arm index curl; repeat right hand pinky.
- [ ] Left and right shoulder x/y/z, elbow flex, wrist x/y/z each produce visible changes.
- [ ] Finger curl and spread controls operate for all fingers on both hands.
- [ ] Export pose then Import JSON restores that pose.
- [ ] Create animation from pose; add keyframes at 500 and 1000 ms; Play shows transition; export/reimport reproduces it.
- [ ] Import invalid JSON displays an error instead of crashing the entire page.
- [ ] Export joints contains 21 XYZ arrays per hand, 6 shoulder/elbow/wrist XYZ arrays; `schema` warns synthetic.
- [ ] Resize browser window/mobile width: inspector stays reachable, canvas scales.
- [ ] Reload, inspect Console (F12): no uncaught errors.
- [ ] Run `npm test` and `npm run build` successfully in terminal.

## Important correctness checks for later real ASL playback

- [ ] Two ASL-fluent reviewers can distinguish the target sign without English labels.
- [ ] Wrist relative to shoulder remains consistent for different arm spans.
- [ ] Finger configuration remains correct during held shapes and inter-sign transitions.
- [ ] Captured camera handedness/mirroring matches rendered hand assignments.
- [ ] Clip duration and timing match recorded sign within an agreed tolerance.

## Current non-goals

Voice recognition, phrase translation, automatic MediaPipe retargeting, ASL grammaticality, and facial grammar are **not** part of milestone 1.
