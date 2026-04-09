# This script extracts normalized hand landmarks from all ASL alphabet images
# and engineers robust features (distances + angles) for classification.
#
# Features are INVARIANT to:
#   - Hand position in frame (translation invariant via wrist centering)
#   - Hand distance from camera (scale invariant via reference distance)
#   - Partial rotation (angle/distance features)

import os
import cv2
import math
import mediapipe as mp
import numpy as np
import pandas as pd
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# ─── MediaPipe Setup ──────────────────────────────────────────────────────────
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=True, max_num_hands=1, min_detection_confidence=0.5)

# ─── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR = '/Users/aramishf/Desktop/group-project-the-team/ASL Alphabet/asl_alphabet_train'
OUTPUT_FILE = 'data/hand_landmarks_normalized.csv'

# ─── Landmark Indices ──────────────────────────────────────────────────────────
# MediaPipe hand landmark indices for reference:
#   0: WRIST
#   4: THUMB_TIP, 8: INDEX_TIP, 12: MIDDLE_TIP, 16: RING_TIP, 20: PINKY_TIP
#   5: INDEX_MCP, 9: MIDDLE_MCP, 13: RING_MCP, 17: PINKY_MCP
WRIST = 0
MIDDLE_MCP = 9
FINGERTIPS = [4, 8, 12, 16, 20]
MCPS = [5, 9, 13, 17]
PIPS = [6, 10, 14, 18]
DIPS = [7, 11, 15, 19]


def compute_distance(p1, p2):
    """Euclidean distance between two 3D points."""
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)


def compute_angle(a, b, c):
    """Angle at point b formed by points a-b-c, in radians."""
    ba = [a[i] - b[i] for i in range(3)]
    bc = [c[i] - b[i] for i in range(3)]
    dot = sum(ba[i]*bc[i] for i in range(3))
    mag_ba = math.sqrt(sum(x**2 for x in ba)) + 1e-8
    mag_bc = math.sqrt(sum(x**2 for x in bc)) + 1e-8
    cos_angle = max(-1, min(1, dot / (mag_ba * mag_bc)))
    return math.acos(cos_angle)


def normalize_landmarks(landmarks):
    """
    Takes 21 MediaPipe hand landmarks and returns a robust feature vector.
    
    Returns a list of features:
      - 60 normalized relative coordinates (20 landmarks × 3, wrist excluded)
      - 10 fingertip-to-wrist distances
      - 10 fingertip-to-fingertip distances
      - 15 joint angles (3 per finger: MCP, PIP, DIP angles)
    
    Total: ~95 features
    """
    pts = [(lm.x, lm.y, lm.z) for lm in landmarks]
    
    # ── Step 1: Center on wrist ──
    wrist = pts[WRIST]
    centered = [(p[0]-wrist[0], p[1]-wrist[1], p[2]-wrist[2]) for p in pts]
    
    # ── Step 2: Scale normalize ──
    # Use wrist-to-middle-finger-MCP as the reference distance
    ref_dist = compute_distance(centered[WRIST], centered[MIDDLE_MCP])
    if ref_dist < 1e-6:
        ref_dist = 1e-6  # avoid division by zero
    
    normalized = [(p[0]/ref_dist, p[1]/ref_dist, p[2]/ref_dist) for p in centered]
    
    # ── Step 3: Flatten normalized coordinates (skip wrist, it's always 0,0,0) ──
    coord_features = []
    for i in range(1, 21):
        coord_features.extend([normalized[i][0], normalized[i][1], normalized[i][2]])
    
    # ── Step 4: Distance features ──
    distance_features = []
    
    # Fingertip to wrist distances (5 values)
    for tip in FINGERTIPS:
        distance_features.append(compute_distance(normalized[tip], normalized[WRIST]))
    
    # Fingertip to palm center (5 values) - palm center approximated by MCP average
    palm_center = [
        np.mean([normalized[m][0] for m in MCPS]),
        np.mean([normalized[m][1] for m in MCPS]),
        np.mean([normalized[m][2] for m in MCPS])
    ]
    for tip in FINGERTIPS:
        distance_features.append(compute_distance(normalized[tip], palm_center))
    
    # Inter-fingertip distances: all pairs (10 values)
    for i in range(len(FINGERTIPS)):
        for j in range(i+1, len(FINGERTIPS)):
            distance_features.append(
                compute_distance(normalized[FINGERTIPS[i]], normalized[FINGERTIPS[j]])
            )
    
    # ── Step 5: Angle features ──
    angle_features = []
    
    # For each finger, compute 3 joint angles:
    # Thumb: landmarks 1-2-3, 2-3-4
    thumb_chain = [1, 2, 3, 4]
    for i in range(len(thumb_chain) - 2):
        angle_features.append(compute_angle(
            normalized[thumb_chain[i]],
            normalized[thumb_chain[i+1]],
            normalized[thumb_chain[i+2]]
        ))
    
    # Index through Pinky: landmarks [MCP-1, MCP, PIP, DIP, TIP]
    finger_chains = [
        [0, 5, 6, 7, 8],    # Index
        [0, 9, 10, 11, 12],  # Middle
        [0, 13, 14, 15, 16], # Ring
        [0, 17, 18, 19, 20], # Pinky
    ]
    for chain in finger_chains:
        for i in range(len(chain) - 2):
            angle_features.append(compute_angle(
                normalized[chain[i]],
                normalized[chain[i+1]],
                normalized[chain[i+2]]
            ))
    
    # Combine all features
    return coord_features + distance_features + angle_features


# ── Build Column Names ─────────────────────────────────────────────────────────
columns = []

# Normalized coordinates (landmarks 1-20, x/y/z)
for i in range(1, 21):
    columns.extend([f'nx{i}', f'ny{i}', f'nz{i}'])

# Fingertip-to-wrist distances
for i, tip in enumerate(FINGERTIPS):
    columns.append(f'dist_tip{tip}_wrist')

# Fingertip-to-palm distances
for i, tip in enumerate(FINGERTIPS):
    columns.append(f'dist_tip{tip}_palm')

# Inter-fingertip distances
for i in range(len(FINGERTIPS)):
    for j in range(i+1, len(FINGERTIPS)):
        columns.append(f'dist_tip{FINGERTIPS[i]}_tip{FINGERTIPS[j]}')

# Angles
thumb_angles = ['angle_thumb_1_2_3', 'angle_thumb_2_3_4']
columns.extend(thumb_angles)

finger_names = ['index', 'middle', 'ring', 'pinky']
for fname in finger_names:
    for k in range(3):
        columns.append(f'angle_{fname}_{k}')

columns.append('label')

print(f"Feature vector size: {len(columns) - 1} features per sample")

# ── Process Images ─────────────────────────────────────────────────────────────
data_list = []
labels = sorted(os.listdir(DATA_DIR))

print(f"Starting normalized extraction for {len(labels)} classes...")

for label in labels:
    label_path = os.path.join(DATA_DIR, label)
    if not os.path.isdir(label_path):
        continue
    
    print(f"Processing Class: {label}")
    for img_name in tqdm(os.listdir(label_path)):
        img_path = os.path.join(label_path, img_name)
        img = cv2.imread(img_path)
        if img is None:
            continue
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                try:
                    features = normalize_landmarks(hand_landmarks.landmark)
                    features.append(label)
                    data_list.append(features)
                except Exception:
                    continue  # skip malformed detections

# ── Save ───────────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
df = pd.DataFrame(data_list, columns=columns)
df.to_csv(OUTPUT_FILE, index=False)
print(f"\nDone! Saved {len(data_list)} samples with {len(columns)-1} features to {OUTPUT_FILE}")