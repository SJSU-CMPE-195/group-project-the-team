# Webcam Data Collection Tool for ASL Alphabet
# 
# This script lets you record your own hand landmark data from your webcam
# to supplement the studio training images with real-world data.
#
# Usage:
#   1. Run the script
#   2. Hold up an ASL letter sign
#   3. Press the corresponding key (a-z) to record samples
#   4. Each keypress captures multiple samples over ~2 seconds
#   5. Press 'q' to quit and save

import os
import cv2
import math
import mediapipe as mp
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# ─── Import normalization from create_dataset ──────────────────────────────────
# We duplicate the normalization logic here to keep scripts self-contained

WRIST = 0
MIDDLE_MCP = 9
FINGERTIPS = [4, 8, 12, 16, 20]
MCPS = [5, 9, 13, 17]


def compute_distance(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)


def compute_angle(a, b, c):
    ba = [a[i] - b[i] for i in range(3)]
    bc = [c[i] - b[i] for i in range(3)]
    dot = sum(ba[i]*bc[i] for i in range(3))
    mag_ba = math.sqrt(sum(x**2 for x in ba)) + 1e-8
    mag_bc = math.sqrt(sum(x**2 for x in bc)) + 1e-8
    cos_angle = max(-1, min(1, dot / (mag_ba * mag_bc)))
    return math.acos(cos_angle)


def normalize_landmarks(landmarks):
    """Same normalization as create_dataset.py — must stay in sync."""
    pts = [(lm.x, lm.y, lm.z) for lm in landmarks]
    
    wrist = pts[WRIST]
    centered = [(p[0]-wrist[0], p[1]-wrist[1], p[2]-wrist[2]) for p in pts]
    
    ref_dist = compute_distance(centered[WRIST], centered[MIDDLE_MCP])
    if ref_dist < 1e-6:
        ref_dist = 1e-6
    
    normalized = [(p[0]/ref_dist, p[1]/ref_dist, p[2]/ref_dist) for p in centered]
    
    # Coordinates (skip wrist)
    coord_features = []
    for i in range(1, 21):
        coord_features.extend([normalized[i][0], normalized[i][1], normalized[i][2]])
    
    # Distances
    distance_features = []
    for tip in FINGERTIPS:
        distance_features.append(compute_distance(normalized[tip], normalized[WRIST]))
    
    palm_center = [
        np.mean([normalized[m][0] for m in MCPS]),
        np.mean([normalized[m][1] for m in MCPS]),
        np.mean([normalized[m][2] for m in MCPS])
    ]
    for tip in FINGERTIPS:
        distance_features.append(compute_distance(normalized[tip], palm_center))
    
    for i in range(len(FINGERTIPS)):
        for j in range(i+1, len(FINGERTIPS)):
            distance_features.append(
                compute_distance(normalized[FINGERTIPS[i]], normalized[FINGERTIPS[j]])
            )
    
    # Angles
    angle_features = []
    thumb_chain = [1, 2, 3, 4]
    for i in range(len(thumb_chain) - 2):
        angle_features.append(compute_angle(
            normalized[thumb_chain[i]], normalized[thumb_chain[i+1]], normalized[thumb_chain[i+2]]
        ))
    
    finger_chains = [
        [0, 5, 6, 7, 8], [0, 9, 10, 11, 12],
        [0, 13, 14, 15, 16], [0, 17, 18, 19, 20],
    ]
    for chain in finger_chains:
        for i in range(len(chain) - 2):
            angle_features.append(compute_angle(
                normalized[chain[i]], normalized[chain[i+1]], normalized[chain[i+2]]
            ))
    
    return coord_features + distance_features + angle_features


# ─── Setup ─────────────────────────────────────────────────────────────────────
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(
    static_image_mode=False, max_num_hands=1,
    min_detection_confidence=0.7, min_tracking_confidence=0.5
)

OUTPUT_FILE = 'data/webcam_landmarks.csv'
SAMPLES_PER_BURST = 30  # How many frames to capture per keypress

# Valid labels
VALID_LABELS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
SPECIAL_KEYS = {',': 'del', '.': 'nothing', '/': 'space'}

collected_data = []
label_counts = {}

cap = cv2.VideoCapture(0)
print("\n" + "="*60)
print("  ASL Webcam Data Collector")
print("="*60)
print("  Hold up a sign and press the matching key (a-z)")
print("  Special: ',' = del | '.' = nothing | '/' = space")
print("  Press 'q' to save and quit")
print("="*60 + "\n")

recording = False
record_label = None
record_count = 0

while cap.isOpened():
    success, image = cap.read()
    if not success:
        break
    
    image = cv2.flip(image, 1)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)
    
    hand_detected = False
    
    if results.multi_hand_landmarks:
        hand_detected = True
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                image, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )
            
            # If we're in recording mode, capture samples
            if recording and record_count < SAMPLES_PER_BURST:
                try:
                    features = normalize_landmarks(hand_landmarks.landmark)
                    features.append(record_label)
                    collected_data.append(features)
                    record_count += 1
                except Exception:
                    pass
    
    # Check if burst is done
    if recording and record_count >= SAMPLES_PER_BURST:
        recording = False
        label_counts[record_label] = label_counts.get(record_label, 0) + record_count
        print(f"  ✓ Captured {record_count} samples for '{record_label}' (total: {label_counts[record_label]})")
    
    # ── Draw UI ──
    h, w, _ = image.shape
    overlay = image.copy()
    cv2.rectangle(overlay, (0, 0), (w, 80), (30, 30, 30), -1)
    image = cv2.addWeighted(overlay, 0.7, image, 0.3, 0)
    
    cv2.putText(image, "ASL Data Collector", (15, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 200, 255), 2)
    
    status = f"Total: {len(collected_data)} samples | Classes: {len(label_counts)}"
    cv2.putText(image, status, (15, 55),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    
    if recording:
        cv2.putText(image, f"RECORDING '{record_label}': {record_count}/{SAMPLES_PER_BURST}",
                    (15, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    elif not hand_detected:
        cv2.putText(image, "Show your hand to the camera", (15, h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 180, 255), 1)
    else:
        cv2.putText(image, "Press a letter key to record | 'q' to quit", (15, h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 100), 1)
    
    cv2.imshow('ASL Data Collector', image)
    
    key = cv2.waitKey(5) & 0xFF
    if key == ord('q'):
        break
    elif not recording and hand_detected:
        char = chr(key) if key < 128 else None
        if char:
            if char.upper() in VALID_LABELS:
                recording = True
                record_label = char.upper()
                record_count = 0
                print(f"  ● Recording '{record_label}'...")
            elif char in SPECIAL_KEYS:
                recording = True
                record_label = SPECIAL_KEYS[char]
                record_count = 0
                print(f"  ● Recording '{record_label}'...")

cap.release()
cv2.destroyAllWindows()

# ── Save collected data ────────────────────────────────────────────────────────
if collected_data:
    # Build columns (same as create_dataset.py)
    columns = []
    for i in range(1, 21):
        columns.extend([f'nx{i}', f'ny{i}', f'nz{i}'])
    for tip in FINGERTIPS:
        columns.append(f'dist_tip{tip}_wrist')
    for tip in FINGERTIPS:
        columns.append(f'dist_tip{tip}_palm')
    for i in range(len(FINGERTIPS)):
        for j in range(i+1, len(FINGERTIPS)):
            columns.append(f'dist_tip{FINGERTIPS[i]}_tip{FINGERTIPS[j]}')
    columns.extend(['angle_thumb_1_2_3', 'angle_thumb_2_3_4'])
    for fname in ['index', 'middle', 'ring', 'pinky']:
        for k in range(3):
            columns.append(f'angle_{fname}_{k}')
    columns.append('label')
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df = pd.DataFrame(collected_data, columns=columns)
    
    # Append if file already exists
    if os.path.exists(OUTPUT_FILE):
        existing = pd.read_csv(OUTPUT_FILE)
        df = pd.concat([existing, df], ignore_index=True)
    
    df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\n{'='*60}")
    print(f"  Saved {len(collected_data)} new samples to {OUTPUT_FILE}")
    print(f"  Per-class breakdown:")
    for label, count in sorted(label_counts.items()):
        print(f"    {label}: {count} samples")
    print(f"{'='*60}")
else:
    print("\nNo data collected. Exiting.")
