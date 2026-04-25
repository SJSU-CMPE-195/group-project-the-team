import os
import cv2
import pandas as pd
import numpy as np
import mediapipe as mp
from tqdm import tqdm
import warnings

# Configuration
TARGET_WORDS = ["MOVIE1", "EAT1", "NIGHT1", "FINE1", "DEAF1", "HOSPITAL1", "PARTY1", "CHRISTMAS1", "BASKETBALL1", "DOG1"]
FRAMES_PER_VIDEO = 30
FEATURES_PER_FRAME = 126

DATA_DIR = '/Volumes/2TB/ASL_Citizen/ASL_Citizen'
SPLITS_DIR = os.path.join(DATA_DIR, 'splits')
VIDEO_DIR = os.path.join(DATA_DIR, 'videos')
OUTPUT_DIR = 'data/processed'

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
    frames_array = np.array(frames_data)
    if len(frames_array) >= FRAMES_PER_VIDEO:
        return frames_array[:FRAMES_PER_VIDEO]
    else:
        padding = np.zeros((FRAMES_PER_VIDEO - len(frames_array), FEATURES_PER_FRAME))
        return np.vstack((frames_array, padding))

def process_dataset():
    all_metadata = []
    for csv_file in os.listdir(SPLITS_DIR):
        if csv_file.endswith('.csv'):
            df = pd.read_csv(os.path.join(SPLITS_DIR, csv_file))
            all_metadata.append(df)
    
    metadata = pd.concat(all_metadata)
    # Filter for target words
    subset = metadata[metadata['Gloss'].isin(TARGET_WORDS)]
    print(f"Found {len(subset)} videos for target words: {TARGET_WORDS}")
    
    X, y = [], []
    for _, row in tqdm(subset.iterrows(), total=len(subset)):
        video_filename = row['Video file']
        gloss = row['Gloss']
        video_path = os.path.join(VIDEO_DIR, video_filename)
        
        if not os.path.exists(video_path):
            continue
            
        features = extract_landmarks(video_path)
        if features is not None:
            X.append(features)
            y.append(gloss)
            
    X = np.array(X)
    y = np.array(y)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    np.save(os.path.join(OUTPUT_DIR, 'X_citizen10.npy'), X)
    np.save(os.path.join(OUTPUT_DIR, 'y_citizen10.npy'), y)
    print(f"\nSaved {len(X)} samples to {OUTPUT_DIR}")

if __name__ == "__main__":
    process_dataset()
