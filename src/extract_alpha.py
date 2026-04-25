import os
import cv2
import pandas as pd
import numpy as np
import mediapipe as mp
from tqdm import tqdm
import warnings

# Configuration
# All 26 letters of the alphabet
LETTERS = [
    'a', 'b', 'C', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'L', 'm', 
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'X', 'Y', 'Z'
]
FRAMES_PER_VIDEO = 30
FEATURES_PER_FRAME = 126

VIDEO_DIR = '/Volumes/2TB/Skeletal_ASL/videos/videos'
OUTPUT_DIR = 'data/processed'

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# MediaPipe Setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)

def extract_landmarks(video_path):
    cap = cv2.VideoCapture(video_path)
    frames_data = []
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success: break
            
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        
        right_hand = [0] * 63
        left_hand = [0] * 63
        
        if results.multi_hand_landmarks and results.multi_handedness:
            for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                label = results.multi_handedness[i].classification[0].label
                wrist = hand_landmarks.landmark[0]
                coords = []
                for lm in hand_landmarks.landmark:
                    coords.extend([lm.x - wrist.x, lm.y - wrist.y, lm.z - wrist.z])
                
                if label == 'Right': right_hand = coords
                else: left_hand = coords
        
        frames_data.append(right_hand + left_hand)
            
    cap.release()
    if not frames_data: return None
    
    # Standardize to 30 frames
    if len(frames_data) > FRAMES_PER_VIDEO:
        indices = np.linspace(0, len(frames_data)-1, FRAMES_PER_VIDEO, dtype=int)
        frames_data = [frames_data[i] for i in indices]
    else:
        while len(frames_data) < FRAMES_PER_VIDEO:
            frames_data.append(frames_data[-1] if frames_data else [0]*FEATURES_PER_FRAME)
            
    return np.array(frames_data)

def process_alphabet():
    X = []
    y = []
    
    print(f"Processing 26 alphabet videos from {VIDEO_DIR}...")
    
    for letter in tqdm(LETTERS):
        video_path = os.path.join(VIDEO_DIR, f"{letter}.mp4")
        if not os.path.exists(video_path):
            print(f"Warning: Video for {letter} not found at {video_path}")
            continue
            
        # We augment each letter a bit to have more training samples
        # (Since the dataset only has 1 video per letter)
        landmarks = extract_landmarks(video_path)
        if landmarks is not None:
            # Add 20 samples per letter with slight variations (jitter) to make it robust
            for _ in range(20):
                jitter = np.random.normal(0, 0.005, landmarks.shape)
                X.append(landmarks + jitter)
                y.append(letter.upper()) # Normalize labels to uppercase
    
    X = np.array(X)
    y = np.array(y)
    
    np.save(os.path.join(OUTPUT_DIR, 'X_alpha.npy'), X)
    np.save(os.path.join(OUTPUT_DIR, 'y_alpha.npy'), y)
    
    print(f"\nAlphabet extraction complete. Saved {len(X)} samples to {OUTPUT_DIR}")

if __name__ == "__main__":
    process_alphabet()
