import os
import cv2
import json
import numpy as np
import mediapipe as mp
from tqdm import tqdm
import warnings

# Suppress annoying protobuf/mediapipe warnings in terminal
warnings.simplefilter('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# 1. Configuration
TARGET_WORDS = ["before", "thin", "cool", "drink", "go", "computer", "who", "cousin", "help", "candy"]
FRAMES_PER_VIDEO = 30
FEATURES_PER_FRAME = 126 # (21 points * 3) * 2 hands

DATA_DIR = 'data/WLASL'
JSON_PATH = os.path.join(DATA_DIR, 'WLASL_v0.3.json')
VIDEO_DIR = os.path.join(DATA_DIR, 'videos')

# 2. Setup MediaPipe
mp_hands = mp.solutions.hands
# Increased max_num_hands to 2
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)

# 3. Load the JSON map to find our videos
with open(JSON_PATH, 'r') as f:
    wlasl_data = json.load(f)

# Create a dictionary mapping video_id -> word
video_map = {}
for entry in wlasl_data:
    word = entry['gloss'].lower()
    if word in TARGET_WORDS:
        for instance in entry['instances']:
            video_id = instance['video_id']
            video_map[video_id] = word

print(f"Found {len(video_map)} videos for our {len(TARGET_WORDS)} target words.")

X, y = [], []

# 4. Process Videos
for video_id, word in tqdm(video_map.items()):
    video_path = os.path.join(VIDEO_DIR, f"{video_id}.mp4")
    
    if not os.path.exists(video_path):
        continue
        
    cap = cv2.VideoCapture(video_path)
    frames_data = []
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
            
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        
        # Initialize both hands as zeros
        right_hand_coords = [0] * 63
        left_hand_coords = [0] * 63
        
        if results.multi_hand_landmarks and results.multi_handedness:
            for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # Identify if this hand is Left or Right
                label = results.multi_handedness[i].classification[0].label # "Left" or "Right"
                
                # Normalize to wrist
                wrist = hand_landmarks.landmark[0]
                coords = []
                for lm in hand_landmarks.landmark:
                    coords.extend([lm.x - wrist.x, lm.y - wrist.y, lm.z - wrist.z])
                
                if label == 'Right':
                    right_hand_coords = coords
                else:
                    left_hand_coords = coords
        
        # Combine: Right (0-62) and Left (63-125)
        frames_data.append(right_hand_coords + left_hand_coords)
            
    cap.release()
    
    # 5. Frame Standardization (The strict 30-frame rule)
    if len(frames_data) == 0:
        continue # Skip empty videos
        
    frames_array = np.array(frames_data)
    
    # If video is too long, cut it to the first 30 frames
    if len(frames_array) >= FRAMES_PER_VIDEO:
        standardized_frames = frames_array[:FRAMES_PER_VIDEO]
    # If video is too short, pad with zeros at the end
    else:
        padding = np.zeros((FRAMES_PER_VIDEO - len(frames_array), FEATURES_PER_FRAME))
        standardized_frames = np.vstack((frames_array, padding))
        
    X.append(standardized_frames)
    y.append(word)

# 6. Save as NumPy Arrays
X = np.array(X)
y = np.array(y)

os.makedirs('data/processed', exist_ok=True)
np.save('data/processed/X_wlasl10.npy', X)
np.save('data/processed/y_wlasl10.npy', y)

print(f"\nExtraction Complete!")
print(f"Features Shape (X): {X.shape} -> (Videos, 30 Frames, 63 Coordinates)")
print(f"Labels Shape (y): {y.shape}")
