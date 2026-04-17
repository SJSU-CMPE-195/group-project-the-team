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
TARGET_WORDS = ["hello", "help", "thank you", "yes", "no", "please", "sorry", "hurt", "eat", "water"]
FRAMES_PER_VIDEO = 30
FEATURES_PER_FRAME = 63 # 21 points * 3 (x,y,z)

DATA_DIR = 'data/WLASL'
JSON_PATH = os.path.join(DATA_DIR, 'WLASL_v0.3.json')
VIDEO_DIR = os.path.join(DATA_DIR, 'videos')

# 2. Setup MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.5)

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
        continue # Skip if video is missing from Kaggle dataset
        
    cap = cv2.VideoCapture(video_path)
    frames_data = []
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
            
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        
        # Extract landmarks if a hand is found
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # Normalize to wrist (point 0)
            wrist = hand_landmarks.landmark[0]
            frame_coords = []
            for lm in hand_landmarks.landmark:
                frame_coords.extend([lm.x - wrist.x, lm.y - wrist.y, lm.z - wrist.z])
            frames_data.append(frame_coords)
        else:
            # If no hand found in this frame, append zeros to keep sequence intact
            frames_data.append(np.zeros(FEATURES_PER_FRAME).tolist())
            
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
