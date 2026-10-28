# Silent Voice Bridge

**SJSU CMPE 195 Senior Design** · Advisor: Dr. Kaikai Liu

An assistive communication and sign-learning web app built on hand landmarks, not raw video.

> **Honest framing:** this is an assistive communication and learning tool for a limited vocabulary, not a full ASL interpreter. ASL has its own grammar and relies on facial expressions and head movement, which this version does not capture.

## Team

| Name | GitHub | Workstream |
| :--- | :--- | :--- |
| Aramish Farooq | [@aramishf](https://github.com/aramishf) | A: Sign to English to speech |
| Nathaniel Ortega | [@NateDawgg99](https://github.com/NateDawgg99) | B: English to avatar |
| Pwint Thu Thu San (Ruby) | [@PwintThuThuSan](https://github.com/PwintThuThuSan) | C: Learn mode |
| Reuben George | [@reubstahh](https://github.com/reubstahh) | D: Sign library, integration, testing |

## Project Description

Deaf signers and hearing people who don't know ASL struggle to hold even a short conversation, and beginners have few ways to practice signs with feedback. Silent Voice Bridge is a browser app with a two-way bridge: the hearing person speaks or types and an avatar signs it, and the signer signs at the webcam and the app shows and speaks the English. A Learn mode demonstrates a sign and coaches the learner's attempt, and Teach-A-Sign lets the team add a new sign by recording it three times.

## Prototype Scope

**Works end to end now**
- **English to Sign:** speech (Web Speech API) or typed text → English-to-gloss translation with ASL word order (for example "What is your name?" → `YOUR NAME WHAT`) and fingerspelling for unknown words → sign clips from the local lexicon blended with smooth transitions → avatar video in the browser.
- **Sign to English:** live webcam hand tracking with MediaPipe Hands, a skeleton overlay, and recognition of a core vocabulary (HELLO, HOW-ARE-YOU, NICE-MEET-YOU, MY-NAME, HELP, THANK-YOU, FINE, PLEASE, YES, plus the letters B, I, L, V, Y). Recognized signs go into the conversation transcript and are spoken aloud.
- **Learn mode:** Watch (avatar demo of any typed sentence) → Try it (webcam attempt) → coaching feedback (what was tracked, where learners commonly go wrong, and a tip).
- **Sign library and Teach-A-Sign:** 12 library signs with 36 templates in the shared `(30, 68)` palm-space format. Teach-A-Sign records a new sign 3 times, saves it to the library, and unlocks it for recognition in Bridge mode.
- **DTW template matching:** FastDTW over the library templates gives 94.4% leave-one-out accuracy (34/36). It runs in `benchmark_library.py` and in the desktop recognition tool `teach_and_recognize_v2.py`.

**Incomplete**
- Live recognition in the web app uses a rule-based hand-shape classifier with fixed confidence values. The DTW matcher is not yet wired into the browser path.
- Learn mode gives rule-based coaching text, not yet a numeric DTW score with per-joint feedback.
- All templates come from one signer, so accuracy on new signers has not been measured. No sign has been verified by an ASL-fluent reviewer yet.

**Left for the Expo:** see [What's Next](#whats-next).

## System Architecture

```
 Browser (served by unified_bridge_server.py, UI in ui_template.py)
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ Webcam → MediaPipe Hands → skeleton overlay → hand-shape classifier      │
 │          (CDN)                                + Teach-A-Sign signatures  │
 │                                                → transcript → TTS        │
 │ Mic (Web Speech STT) / text box ───────────────┐                         │
 │ Learn mode · Sign library · Teach-A-Sign       │                         │
 └────────────────────────────────────────────────┼─────────────────────────┘
                     HTTP (JSON)                  │
 ┌────────────────────────────────────────────────▼─────────────────────────┐
 │ unified_bridge_server.py (Python http.server, port 8090)                 │
 │   GET  /api/synthesize?text=…  → asl_engine: english_to_gloss            │
 │                                  → lexicon .pose clips → motion_blender  │
 │                                  → MP4 avatar video (/static/videos/…)   │
 │   GET  /api/signs              → sign library metadata                   │
 │   POST /api/custom_signs       → Teach-A-Sign: save 3 attempts as        │
 │                                  (30, 68) templates via palm_normalizer  │
 │   POST /api/score              → Learn-mode coaching                     │
 └──────────────────────────────────────────────────────────────────────────┘
 library/signs/*.json + library/tensors/*.npy   shared sign library (README Section 4.2 format)
 asl_engine/lexicon/*.pose                      avatar sign clips, A–Z fingerspelling
 palm_normalizer.py                             canonical palm-space features, shape (30, 68)
 kinetic_segmenter.py                           sign start/finish detection from hand velocity
 teach_and_recognize_v2.py                      desktop tool: Teach-A-Sign + live DTW recognition + TTS
 benchmark_library.py                           leave-one-out DTW accuracy over the library
 src/                                           195A pipeline (alphabet / word models, training)
```

Only landmarks and text leave the camera stage; no video is uploaded.

## Prerequisites

- **Python** 3.12 (the server and tests also run on 3.13). The desktop tools in `requirements.txt` need 3.12 because of `mediapipe==0.10.14`.
- **Google Chrome** (or Edge) for the web app. Speech-to-text uses the Web Speech API, which Safari and Firefox support only partially.
- **Webcam and microphone** for live use. They are not needed for the tests.
- **Internet access in the browser:** MediaPipe Hands is loaded from `cdn.jsdelivr.net`. English words with no local sign clip are fetched from the public sign.mt API; everything in the demo vocabulary is local.
- No accounts, API keys or environment variables are required.

## Installation

1. Clone the repository and check out the graded tag:
   ```bash
   git clone https://github.com/SJSU-CMPE-195/group-project-the-team.git
   cd group-project-the-team
   git checkout impl2-v1
   ```
2. Create and activate a virtual environment:
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```
3. Install the web app and test dependencies:
   ```bash
   pip install -r requirements-server.txt
   ```
4. Optional, for the desktop tools (`teach_and_recognize_v2.py`, `src/`): `pip install -r requirements.txt`

## Running the Prototype

```bash
source .venv/bin/activate
python unified_bridge_server.py        # optional port argument, default 8090
```

Open **http://localhost:8090** in Chrome and allow camera and microphone access.

- **Bridge:** sign at the camera to add English to the conversation, or type/speak in the box and press **Sign it** to see the avatar.
- **Learn:** type a sentence, watch the avatar, record your attempt, and read the coaching.
- **Sign library:** browse the signs, or **Teach a sign** to record a new one in 3 tries.

Desktop recognition with DTW (needs a webcam and `requirements.txt`): `python teach_and_recognize_v2.py`

## Testing

```bash
source .venv/bin/activate
python -m pytest tests -v          # 30 tests, about 5 seconds, no camera needed
python benchmark_library.py        # prints the per-template DTW report
```

| File | What it covers |
| :--- | :--- |
| `tests/test_palm_normalizer.py` | The `(30, 68)` feature contract: one and two hands, no hands, position invariance, resampling any length to 30 frames |
| `tests/test_english_to_gloss.py` | English to gloss: phrases, ASL question word order, stop words, fingerspelling fallback |
| `tests/test_sign_library.py` | Every library entry matches the Section 4.2 format with `(30, 68)` templates; leave-one-out DTW accuracy is at least 85% |
| `tests/test_server_api.py` | Starts the real server and checks the web page, the sign library API, English to avatar video end to end, and Learn-mode coaching |

## Demo

- **Video:** TODO: paste demo video link
- **Screenshots:** TODO

Sample output from `GET /api/synthesize?text=hello how are you`:
```json
{"english_text": "hello how are you", "glosses": ["HELLO", "HOW-ARE-YOU"], "total_frames": 299, "fps": 25.0, "duration_sec": 11.96, "video_url": "/static/videos/sign_cfb47e8702.mp4"}
```

## Technical Stack

- **Languages:** Python, JavaScript, HTML, CSS
- **Browser:** MediaPipe Hands, Web Speech API (speech-to-text and text-to-speech), Canvas
- **Server:** Python standard library `http.server`, NumPy, SciPy, FastDTW, OpenCV (video export), `pose-format`
- **Sign clips:** local `.pose` lexicon, with the public sign.mt API as a fallback
- **Desktop and training (195A):** MediaPipe, OpenCV, PyTorch (LSTM and ST-GCN models in `src/`)
- **Hardware:** any laptop with a webcam and microphone

## What's Next

Before the Project Expo on December 11:
1. Send live landmarks from the browser to the server and recognize with the DTW matcher, replacing the rule-based classifier, with a "not sure" state below a confidence threshold.
2. Numeric Learn-mode score (DTW distance to 0–100) with per-joint feedback.
3. Record templates from all four teammates and test on signers outside the team.
4. Move the server to FastAPI with a WebSocket for landmark streaming, and package it with Docker (`docker compose up`).
5. Serve MediaPipe locally so the app works fully offline.
6. Restructure the single-file UI into a component-based frontend (a React + Vite shell is in progress on the `reuben/frontend` branch).
7. Have an ASL-fluent reviewer verify each sign and set `verified_by_asl_reviewer`.
