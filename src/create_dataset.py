# This script will loop through all 87,000 images, extract the coordinates,
#  and save them into one CSV file. Since 87,000 is a lot, 
# I’ve added a progress bar so you don't think the computer has frozen.

import os
import cv2
import mediapipe as mp
import pandas as pd
from tqdm import tqdm # Install this: pip install tqdm

# 1. Setup MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=True, max_num_hands=1, min_detection_confidence=0.5)

# 2. Define Paths
DATA_DIR = '/Users/aramishf/Desktop/group-project-the-team/ASL Alphabet/asl_alphabet_train'
OUTPUT_FILE = 'data/hand_landmarks.csv'

data_list = []

# 3. Process Folders
# Get all subfolders (A, B, Space, etc.)
labels = sorted(os.listdir(DATA_DIR))

print(f"Starting extraction for {len(labels)} classes...")

for label in labels:
    label_path = os.path.join(DATA_DIR, label)
    if not os.path.isdir(label_path):
        continue
    
    print(f"Processing Class: {label}")
    # Loop through each image in the folder
    for img_name in tqdm(os.listdir(label_path)):
        img_path = os.path.join(label_path, img_name)
        img = cv2.imread(img_path)
        if img is None:
            continue
            
        # Convert to RGB for MediaPipe
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                row = []
                # Extract 21 points (x, y, z)
                for lm in hand_landmarks.landmark:
                    row.extend([lm.x, lm.y, lm.z])
                
                # Add the label at the end
                row.append(label)
                data_list.append(row)

# 4. Save to CSV
# Create column names: x0, y0, z0, x1, y1, z1 ... label
columns = []
for i in range(21):
    columns.extend([f'x{i}', f'y{i}', f'z{i}'])
columns.append('label')

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
df = pd.DataFrame(data_list, columns=columns)
df.to_csv(OUTPUT_FILE, index=False)
print(f"Done! Saved {len(data_list)} samples to {OUTPUT_FILE}")