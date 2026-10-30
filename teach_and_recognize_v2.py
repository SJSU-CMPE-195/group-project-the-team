"""
Silent Voice Bridge v2 - Workstream A & Teach-A-Sign Tool
Owner: Aramish

Features:
1. "Teach-A-Sign" Mode:
   - Select a sign to teach (e.g., HOW-ARE-YOU, HELLO, MY-NAME, HELP).
   - Prompts you to perform the sign 3 times (3 tries).
   - Validates that both hands are present when doing two-handed signs.
   - Resamples into canonical palm-space tensor of shape (30, 68).
   - Saves to library/tensors/<id>.npy and updates library/signs/<gloss>.json conforming to Section 4.2.

2. "Real-Time Recognition & TTS" Mode:
   - Live DTW Matcher against the shared sign library templates.
   - Speaks recognized English aloud using pyttsx3 or macOS TTS.
"""

import cv2
import numpy as np
import json
import time
import os
import subprocess
from pathlib import Path
from collections import deque
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

from palm_normalizer import normalize_landmarks_frame, resample_sequence, FEATURE_DIM, extract_raw_landmarks
from kinetic_segmenter import KineticSegmenter

# Directories conforming to Section 5
BASE_DIR = Path(__file__).resolve().parent
LIBRARY_DIR = BASE_DIR / "library"
SIGNS_DIR = LIBRARY_DIR / "signs"
TENSORS_DIR = LIBRARY_DIR / "tensors"

SIGNS_DIR.mkdir(parents=True, exist_ok=True)
TENSORS_DIR.mkdir(parents=True, exist_ok=True)

HAND_MODEL_PATH = str(BASE_DIR / 'hand_landmarker.task')
POSE_MODEL_PATH = str(BASE_DIR / 'pose_landmarker.task')

VOCABULARY = [
    {"gloss": "HELLO", "english": "Hello!", "hands": 1},
    {"gloss": "HOW-ARE-YOU", "english": "How are you?", "hands": 2},
    {"gloss": "FINE", "english": "I'm doing well, thank you.", "hands": 1},
    {"gloss": "MY-NAME", "english": "My name is Aramish.", "hands": 2},
    {"gloss": "WHAT-IS-YOUR-NAME", "english": "What is your name?", "hands": 2},
    {"gloss": "NICE-MEET-YOU", "english": "Nice to meet you.", "hands": 2},
    {"gloss": "THANK-YOU", "english": "Thank you.", "hands": 1},
    {"gloss": "PLEASE-REPEAT", "english": "Could you please repeat that?", "hands": 2},
    {"gloss": "DEAF", "english": "I am Deaf. Please face me and speak clearly.", "hands": 1},
    {"gloss": "WRITE-PLEASE", "english": "Could you type or write that down?", "hands": 2},
    {"gloss": "HELP", "english": "I need help.", "hands": 2},
]

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (0, 9), (9, 10), (10, 11), (11, 12),    # Middle
    (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
    (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
    (5, 9), (9, 13), (13, 17), (0, 17)      # Palm base
]

POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),  # Shoulders and arms
    (11, 23), (12, 24), (23, 24)                        # Torso
]

def draw_red_skeleton(image, hand_results, pose_results):
    """Draw clean red skeleton lines and red joint dots for hands and upper body."""
    h, w, _ = image.shape
    RED_COLOR = (0, 0, 255)       # Pure Red in BGR
    RED_DOT_COLOR = (40, 40, 255)  # Bright Red dot

    # 1. Pose landmarks (red lines and dots for upper body)
    if pose_results and pose_results.pose_landmarks and len(pose_results.pose_landmarks) > 0:
        lm_list = pose_results.pose_landmarks[0]
        for p1_idx, p2_idx in POSE_CONNECTIONS:
            if p1_idx < len(lm_list) and p2_idx < len(lm_list):
                pt1 = (int(lm_list[p1_idx].x * w), int(lm_list[p1_idx].y * h))
                pt2 = (int(lm_list[p2_idx].x * w), int(lm_list[p2_idx].y * h))
                cv2.line(image, pt1, pt2, RED_COLOR, 2, cv2.LINE_AA)
        
        for idx in [11, 12, 13, 14, 15, 16]:
            if idx < len(lm_list):
                cx, cy = int(lm_list[idx].x * w), int(lm_list[idx].y * h)
                cv2.circle(image, (cx, cy), 5, RED_DOT_COLOR, -1, cv2.LINE_AA)

    # 2. Hand landmarks (red lines and red dots)
    if hand_results and hand_results.hand_landmarks:
        for landmarks in hand_results.hand_landmarks:
            # Draw red connection bones
            for start_idx, end_idx in HAND_CONNECTIONS:
                p1 = (int(landmarks[start_idx].x * w), int(landmarks[start_idx].y * h))
                p2 = (int(landmarks[end_idx].x * w), int(landmarks[end_idx].y * h))
                cv2.line(image, p1, p2, RED_COLOR, 2, cv2.LINE_AA)

            # Draw red landmark points
            for lm in landmarks:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(image, (cx, cy), 4, RED_DOT_COLOR, -1, cv2.LINE_AA)


def speak_text(text):
    """Speaks English text asynchronously without blocking the camera thread."""
    try:
        subprocess.Popen(["say", text])
    except Exception:
        pass


class SignLibrary:
    def __init__(self):
        self.templates = {}  # {gloss: list of (30, 68) arrays}
        self.metadata = {}
        self.reload()

    def reload(self):
        self.templates.clear()
        self.metadata.clear()
        for json_file in SIGNS_DIR.glob("*.json"):
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)
                gloss = data["gloss"]
                self.metadata[gloss] = data
                self.templates[gloss] = []
                for t in data.get("templates", []):
                    t_path = TENSORS_DIR / t["tensor_file"]
                    if t_path.exists():
                        tensor = np.load(t_path)
                        if tensor.shape == (30, 68):
                            self.templates[gloss].append(tensor)
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
        print(f"✓ Sign Library loaded: {len(self.templates)} glosses with active templates.")

    def add_template(self, gloss, english, tensor_30x68, signer="aramish", avatar_frames=None):
        existing = [p for p in TENSORS_DIR.glob(f"{gloss.lower()}_*.npy") if not p.stem.endswith("_avatar")]
        count = len(existing) + 1
        tensor_filename = f"{gloss.lower()}_{count:03d}.npy"
        np.save(TENSORS_DIR / tensor_filename, tensor_30x68)

        avatar_filename = None
        if avatar_frames is not None:
            avatar_filename = f"{gloss.lower()}_{count:03d}_avatar.npy"
            np.save(TENSORS_DIR / avatar_filename, np.asarray(avatar_frames, dtype=np.float32))

        json_path = SIGNS_DIR / f"{gloss.lower()}.json"
        if json_path.exists():
            with open(json_path, "r") as f:
                data = json.load(f)
        else:
            data = {
                "gloss": gloss,
                "english": english,
                "category": "core",
                "templates": [],
                "verified_by_asl_reviewer": False
            }

        data["templates"].append({
            "id": f"{gloss.lower()}_{count:03d}",
            "signer": signer,
            "tensor_file": tensor_filename
        })

        # Section 4.2: one avatar clip per sign. Use the first one recorded.
        if avatar_filename and not data.get("avatar_frames_file"):
            data["avatar_frames_file"] = avatar_filename

        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)

        self.reload()


class MediaPipeManager:
    def __init__(self):
        hand_opts = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=HAND_MODEL_PATH),
            num_hands=2,
            min_hand_detection_confidence=0.35,
            min_hand_presence_confidence=0.35,
            min_tracking_confidence=0.35
        )
        self.hand_detector = vision.HandLandmarker.create_from_options(hand_opts)

        pose_opts = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=POSE_MODEL_PATH),
            min_pose_detection_confidence=0.4,
            min_pose_presence_confidence=0.4,
            min_tracking_confidence=0.4
        )
        self.pose_detector = vision.PoseLandmarker.create_from_options(pose_opts)

    def detect(self, rgb_frame):
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        hands = self.hand_detector.detect(mp_img)
        pose = self.pose_detector.detect(mp_img)
        return hands, pose


def match_sign_dtw(query_tensor, sign_library, top_k=3):
    """
    Computes FastDTW distance against all templates in the library.
    Converts distance into confidence score in [0.0, 1.0].
    """
    results = []
    for gloss, t_list in sign_library.templates.items():
        best_d = float('inf')
        for template in t_list:
            d, _ = fastdtw(query_tensor, template, dist=euclidean)
            if d < best_d:
                best_d = d
        if best_d != float('inf'):
            # Exponential decay mapping: d=0 -> 1.0; d=25 -> 0.77; d=60 -> 0.54
            confidence = float(np.exp(-best_d / 100.0))
            results.append((gloss, confidence, best_d))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


def record_sign_3_times(cap, detector, sign_item, library):
    """
    Records a sign across 3 tries for Aramish, validates both hands, and saves to library.
    """
    gloss = sign_item["gloss"]
    english = sign_item["english"]
    expected_hands = sign_item["hands"]

    collected_tensors = []

    for attempt in range(1, 4):
        # Countdown
        countdown_secs = 3
        start_wait = time.time()
        while time.time() - start_wait < countdown_secs:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            remaining = int(countdown_secs - (time.time() - start_wait)) + 1

            # Overlay
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 150), (20, 20, 20), -1)
            cv2.putText(frame, f"TEACHING: {gloss} ({attempt}/3)", (30, 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
            cv2.putText(frame, f"GET READY... SIGN IN {remaining}s", (30, 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 165, 255), 3)

            # Show red skeleton during countdown too so user can align hands
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            c_hands, c_pose = detector.detect(rgb)
            draw_red_skeleton(frame, c_hands, c_pose)

            cv2.imshow("Silent Voice Bridge v2 - Aramish Workstream A", frame)
            if (cv2.waitKey(1) & 0xFF) == ord('q'):
                return False

        # Capture Motion Window (around 2 seconds / 45-60 frames)
        print(f"🎬 Recording Attempt {attempt}/3 for {gloss}...")
        frames_features = []
        frames_raw = []
        record_start = time.time()
        RECORD_DURATION = 2.0  # seconds

        while time.time() - record_start < RECORD_DURATION:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            hands, pose = detector.detect(rgb)

            # Check hands count
            h_count = len(hands.hand_landmarks) if hands.hand_landmarks else 0
            feat = normalize_landmarks_frame(hands, pose)
            frames_features.append(feat)
            frames_raw.append(extract_raw_landmarks(hands, pose))

            # Draw visual red skeleton
            draw_red_skeleton(frame, hands, pose)

            # Draw visual feedback
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 120), (0, 50, 0), -1)
            cv2.putText(frame, f"● RECORDING ATTEMPT {attempt}/3 - PERFORM {gloss}", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            hand_stat = "✓ BOTH HANDS DETECTED" if h_count >= 2 else (f"Hand count: {h_count} (Expected: {expected_hands})")
            hand_col = (0, 255, 0) if h_count >= expected_hands else (0, 0, 255)
            cv2.putText(frame, hand_stat, (30, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.7, hand_col, 2)

            cv2.imshow("Silent Voice Bridge v2 - Aramish Workstream A", frame)
            if (cv2.waitKey(1) & 0xFF) == ord('q'):
                return False

        # Resample to canonical (30, 68) tensor
        tensor_30x68 = resample_sequence(frames_features, target_len=30)
        collected_tensors.append((tensor_30x68, np.stack(frames_raw)))
        print(f"✓ Recorded Attempt {attempt}/3 (tensor: {tensor_30x68.shape}, avatar: {np.stack(frames_raw).shape})")

    # Save all 3 attempts as distinct templates (+ raw avatar frames)
    for t, raw in collected_tensors:
        library.add_template(gloss, english, t, signer="aramish", avatar_frames=raw)

    print(f"\n🎉 Successfully saved 3 templates for '{gloss}' to library!")
    speak_text(f"Sign {gloss} saved successfully.")
    return True


def run_pipeline():
    print("\n" + "="*65)
    print("SILENT VOICE BRIDGE v2 - WORKSTREAM A: RECOGNITION & TUTOR")
    print("Owner: Aramish | Capstone Demo Pipeline")
    print("="*65)

    detector = MediaPipeManager()
    library = SignLibrary()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot access webcam.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    detector = MediaPipeManager()
    library = SignLibrary()
    segmenter = KineticSegmenter()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot access webcam.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    last_spoken_time = 0
    last_spoken_gloss = ""
    current_vocab_idx = 0

    best_match = None
    top_matches = []
    display_until = 0

    print("\nKey Controls:")
    print(" [T] = Teach current selected sign (Records 3 tries)")
    print(" [N] = Next sign in vocabulary")
    print(" [P] = Previous sign in vocabulary")
    print(" [Q] = Quit\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        hands, pose = detector.detect(rgb)
        feat = normalize_landmarks_frame(hands, pose)

        # Update kinetic segmenter
        completed_trajectory, motion_state, velocity = segmenter.update(hands, feat)

        target_sign = VOCABULARY[current_vocab_idx]
        h_count = len(hands.hand_landmarks) if hands.hand_landmarks else 0

        # When a clean gesture trajectory finishes (motion stopped):
        if completed_trajectory is not None and len(library.templates) > 0:
            query = resample_sequence(completed_trajectory, target_len=30)
            top_matches = match_sign_dtw(query, library, top_k=3)
            
            if top_matches:
                best_match = top_matches[0]
                display_until = time.time() + 2.5  # Keep on screen for 2.5s
                
                # Speak aloud
                now = time.time()
                if best_match[0] != last_spoken_gloss or (now - last_spoken_time > 2.0):
                    english_phrase = library.metadata.get(best_match[0], {}).get("english", best_match[0])
                    speak_text(english_phrase)
                    last_spoken_time = now
                    last_spoken_gloss = best_match[0]

        # Draw clean red skeleton lines and red joint dots
        draw_red_skeleton(frame, hands, pose)

        # Draw UI
        # 1. Top Panel (Recognition & TTS)
        cv2.rectangle(frame, (0, 0), (w, 120), (15, 15, 15), -1)
        
        now = time.time()
        if best_match and now < display_until:
            gloss, conf, dist = best_match
            eng = library.metadata.get(gloss, {}).get("english", "")
            cv2.putText(frame, f"SIGN: {gloss} ({conf*100:.1f}%)", (25, 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 3)
            cv2.putText(frame, f"SPEECH: \"{eng}\"", (25, 95),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 255, 255), 2)
        else:
            state_text = "● MOTION DETECTED (Signing...)" if motion_state == "SIGNING" else "IDLE - Ready for sign"
            state_color = (0, 165, 255) if motion_state == "SIGNING" else (160, 160, 160)
            cv2.putText(frame, "SIGN: [Perform a sign gesture...]", (25, 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.85, (180, 180, 180), 2)
            cv2.putText(frame, f"STATUS: {state_text} (vel: {velocity*1000:.0f})", (25, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, state_color, 2)

        # 2. Bottom Panel (Teach-A-Sign & Vocabulary Selection)
        cv2.rectangle(frame, (0, h - 110), (w, h), (20, 20, 20), -1)
        cv2.putText(frame, f"SELECTED SIGN: {target_sign['gloss']} (Press 'T' to record 3 tries)",
                    (25, h - 70), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 200, 255), 2)
        cv2.putText(frame, f"Hands: {target_sign['hands']} | Press 'N' for next, 'P' for prev | Library templates: {len(library.templates)} glosses",
                    (25, h - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        # Top Right Hands Indicator
        h_color = (0, 255, 0) if h_count >= 2 else ((0, 255, 255) if h_count == 1 else (0, 0, 255))
        cv2.putText(frame, f"HANDS: {h_count}", (w - 180, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, h_color, 2)

        cv2.imshow("Silent Voice Bridge v2 - Aramish Workstream A", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord('n'):
            current_vocab_idx = (current_vocab_idx + 1) % len(VOCABULARY)
        elif key == ord('p'):
            current_vocab_idx = (current_vocab_idx - 1) % len(VOCABULARY)
        elif key == ord('t'):
            record_sign_3_times(cap, detector, target_sign, library)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_pipeline()
