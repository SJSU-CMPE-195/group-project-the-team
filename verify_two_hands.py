"""
Silent Voice Bridge v2 - Two-Hand & Pose Landmark Verification Tool
Tests webcam feed and verifies concurrent detection of Left Hand, Right Hand, and Pose.
"""

import cv2
import numpy as np
import time
import os
from pathlib import Path
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

HAND_MODEL_PATH = 'hand_landmarker.task'
POSE_MODEL_PATH = 'pose_landmarker.task'

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

class TwoHandTracker:
    def __init__(self):
        if not Path(HAND_MODEL_PATH).exists():
            raise FileNotFoundError(f"Model file {HAND_MODEL_PATH} not found.")
        if not Path(POSE_MODEL_PATH).exists():
            raise FileNotFoundError(f"Model file {POSE_MODEL_PATH} not found.")

        # Hands: set num_hands=2 with robust confidence thresholds
        hand_base_options = python.BaseOptions(model_asset_path=HAND_MODEL_PATH)
        hand_options = vision.HandLandmarkerOptions(
            base_options=hand_base_options,
            num_hands=2,
            min_hand_detection_confidence=0.35,
            min_hand_presence_confidence=0.35,
            min_tracking_confidence=0.35
        )
        self.hand_detector = vision.HandLandmarker.create_from_options(hand_options)

        # Pose
        pose_base_options = python.BaseOptions(model_asset_path=POSE_MODEL_PATH)
        pose_options = vision.PoseLandmarkerOptions(
            base_options=pose_base_options,
            min_pose_detection_confidence=0.4,
            min_pose_presence_confidence=0.4,
            min_tracking_confidence=0.4
        )
        self.pose_detector = vision.PoseLandmarker.create_from_options(pose_options)

    def detect(self, rgb_frame):
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        hand_results = self.hand_detector.detect(mp_image)
        pose_results = self.pose_detector.detect(mp_image)
        return hand_results, pose_results


def draw_landmarks(image, hand_results, pose_results):
    h, w, _ = image.shape
    
    # 1. Draw Pose (Cyan/Blue)
    if pose_results.pose_landmarks and len(pose_results.pose_landmarks) > 0:
        lm_list = pose_results.pose_landmarks[0]
        for start_idx, end_idx in POSE_CONNECTIONS:
            if start_idx < len(lm_list) and end_idx < len(lm_list):
                p1 = (int(lm_list[start_idx].x * w), int(lm_list[start_idx].y * h))
                p2 = (int(lm_list[end_idx].x * w), int(lm_list[end_idx].y * h))
                cv2.line(image, p1, p2, (255, 200, 0), 2)
        
        for idx in [11, 12, 13, 14, 15, 16]:  # Shoulders, elbows, wrists
            if idx < len(lm_list):
                cx, cy = int(lm_list[idx].x * w), int(lm_list[idx].y * h)
                cv2.circle(image, (cx, cy), 5, (255, 255, 0), -1)

    # 2. Draw Hands (Left = Green, Right = Magenta)
    detected_hands = []
    if hand_results.hand_landmarks:
        for idx, landmarks in enumerate(hand_results.hand_landmarks):
            label = "Unknown"
            score = 0.0
            if idx < len(hand_results.handedness):
                cat = hand_results.handedness[idx][0]
                label = cat.category_name
                score = cat.score

            color = (0, 255, 0) if label == "Left" else (255, 0, 255)
            detected_hands.append((label, score, landmarks[0]))

            # Connections
            for start_idx, end_idx in HAND_CONNECTIONS:
                p1 = (int(landmarks[start_idx].x * w), int(landmarks[start_idx].y * h))
                p2 = (int(landmarks[end_idx].x * w), int(landmarks[end_idx].y * h))
                cv2.line(image, p1, p2, color, 2)

            # Landmarks
            for lm in landmarks:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(image, (cx, cy), 4, color, -1)
                
            # Wrist text label
            wrist_x, wrist_y = int(landmarks[0].x * w), int(landmarks[0].y * h)
            cv2.putText(
                image, f"{label} ({score:.2f})",
                (wrist_x - 30, wrist_y - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2
            )

    return detected_hands


def main():
    print("\n" + "=" * 60)
    print("🚀 Silent Voice Bridge v2 - Dual Hand & Pose Verifier")
    print("=" * 60)
    print("Initializing MediaPipe detectors...")
    
    tracker = TwoHandTracker()
    print("✓ MediaPipe loaded successfully.")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Error: Cannot access webcam (device 0).")
        return

    # Request smooth frame rate & resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("\nInstructions:")
    print("• Bring BOTH hands up to your chest / camera view (as in HOW-ARE-YOU).")
    print("• Check HUD at top: Hand Count should say '2 HANDS DETECTED'.")
    print("• Press 'Q' or Esc to exit.\n")

    fps_history = []

    while True:
        t0 = time.time()
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab webcam frame.")
            break

        # Mirror horizontally for natural sign-language mirror view
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect
        hand_results, pose_results = tracker.detect(rgb_frame)

        # Draw
        detected_hands = draw_landmarks(frame, hand_results, pose_results)

        # Calculate FPS
        dt = time.time() - t0
        fps = 1.0 / dt if dt > 0 else 0
        fps_history.append(fps)
        if len(fps_history) > 30:
            fps_history.pop(0)
        avg_fps = sum(fps_history) / len(fps_history)

        # Draw HUD Panel
        hand_count = len(detected_hands)
        status_color = (0, 255, 0) if hand_count == 2 else ((0, 255, 255) if hand_count == 1 else (0, 0, 255))
        status_text = "✓ 2 HANDS DETECTED" if hand_count == 2 else (f"⚠️ 1 HAND ({detected_hands[0][0]})" if hand_count == 1 else "❌ NO HANDS")

        # Top overlay bar
        cv2.rectangle(frame, (0, 0), (w, 80), (20, 20, 20), -1)
        cv2.putText(frame, "SILENT VOICE BRIDGE v2 - LANDMARK VERIFIER", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        cv2.putText(frame, f"STATUS: {status_text}", (20, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.85, status_color, 2)
        cv2.putText(frame, f"FPS: {avg_fps:.1f}", (w - 140, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "Press 'Q' to quit", (w - 180, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

        cv2.imshow("Silent Voice Bridge v2 - Landmark Check", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("\n✓ Camera released and verifier stopped successfully.")


if __name__ == "__main__":
    main()
