import os
import cv2
import torch
import torch.nn as nn
import numpy as np
import mediapipe as mp
import pickle
from collections import deque
import warnings
from stgcn_model import SignLanguageSTGCN, SingleHandSTGCN

warnings.filterwarnings('ignore')

# --- 1. Model Configuration ---
MODELS_DIR = 'models'

# Master Model (2 Hands)
MASTER_PATH = os.path.join(MODELS_DIR, 'master_stgcn.pth')
MASTER_ENCODER_PATH = os.path.join(MODELS_DIR, 'label_encoder_master.pkl')

# Solo Model (1 Hand)
SOLO_PATH = os.path.join(MODELS_DIR, 'alpha_solo_stgcn.pth')
SOLO_ENCODER_PATH = os.path.join(MODELS_DIR, 'label_encoder_alpha_solo.pkl')

CONFIDENCE_THRESHOLD = 0.40
SEQUENCE_LENGTH = 30

# --- 2. Load Weights and Encoders ---
device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
print(f"Loading Models on: {device}...")

# Load Master
with open(MASTER_ENCODER_PATH, 'rb') as f:
    master_encoder = pickle.load(f)
master_model = SignLanguageSTGCN(num_classes=len(master_encoder.classes_)).to(device)
master_model.load_state_dict(torch.load(MASTER_PATH, map_location=device))
master_model.eval()

# Load Solo
with open(SOLO_ENCODER_PATH, 'rb') as f:
    solo_encoder = pickle.load(f)
solo_model = SingleHandSTGCN(num_classes=len(solo_encoder.classes_)).to(device)
solo_model.load_state_dict(torch.load(SOLO_PATH, map_location=device))
solo_model.eval()

# --- 3. Setup MediaPipe ---
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)

# --- 4. Setup Video Capture ---
cap = cv2.VideoCapture(0)
sequence_queue = deque(maxlen=SEQUENCE_LENGTH)
current_word = "..."
current_confidence = 0.0
top_3_text = "..."
mode_text = "WAITING"

print("\nStarting Dual-Hand Live Inference. Press 'q' to quit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success: break
    frame = cv2.flip(frame, 1)
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    right_hand_coords = [0] * 63
    left_hand_coords = [0] * 63
    hand_count = 0
    
    if results.multi_hand_landmarks and results.multi_handedness:
        hand_count = len(results.multi_hand_landmarks)
        for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            label = results.multi_handedness[i].classification[0].label
            wrist = hand_landmarks.landmark[0]
            coords = []
            for lm in hand_landmarks.landmark:
                coords.extend([lm.x - wrist.x, lm.y - wrist.y, lm.z - wrist.z])
            if label == 'Right': right_hand_coords = coords
            else: left_hand_coords = coords
        
        # Add to sequence
        sequence_queue.append(right_hand_coords + left_hand_coords)
    else:
        if len(sequence_queue) > 0:
            sequence_queue.clear()
            current_word = "..."
            mode_text = "WAITING"

    if len(sequence_queue) == SEQUENCE_LENGTH:
        input_data = np.array(sequence_queue, dtype=np.float32)
        
        with torch.no_grad():
            if hand_count == 2:
                # USE MASTER MODEL (126 features)
                mode_text = "SIGN MODE (2 HANDS)"
                input_tensor = torch.tensor(input_data).unsqueeze(0).to(device)
                outputs = master_model(input_tensor)
                encoder = master_encoder
            else:
                # USE SOLO MODEL (63 features - pick the active hand)
                mode_text = "LETTER MODE (1 HAND)"
                # Pick active hand from input_data
                rh = input_data[:, :63]
                lh = input_data[:, 63:]
                solo_input = rh if np.sum(np.abs(rh)) >= np.sum(np.abs(lh)) else lh
                input_tensor = torch.tensor(solo_input).unsqueeze(0).to(device)
                outputs = solo_model(input_tensor)
                encoder = solo_encoder
            
            probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
            topk_probs, topk_indices = torch.topk(probabilities, 3)
            
            current_word = encoder.inverse_transform([topk_indices[0].item()])[0]
            current_confidence = topk_probs[0].item()
            
            debug_info = [f"{encoder.inverse_transform([topk_indices[i].item()])[0]}: {topk_probs[i].item()*100:.0f}%" for i in range(3)]
            top_3_text = " | ".join(debug_info)

    # --- HUD ---
    h, w, _ = frame.shape
    hud_color = (0, 255, 0) if hand_count == 2 else (255, 165, 0) if hand_count == 1 else (100, 100, 100)
    
    cv2.rectangle(frame, (0, 0), (w, 90), (30, 30, 30), -1)
    cv2.putText(frame, mode_text, (20, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    display_word = current_word.replace('1', '') # Clean up gloss names
    cv2.putText(frame, f"{display_word.upper()}", (20, 65), cv2.FONT_HERSHEY_DUPLEX, 1.2, hud_color, 2)
    cv2.putText(frame, f"Top 3: {top_3_text}", (w - 400, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    
    # Confidence Bar
    cv2.rectangle(frame, (w - 220, 20), (w - 20, 40), (60, 60, 60), -1)
    cv2.rectangle(frame, (w - 220, 20), (w - 220 + int(200 * current_confidence), 40), hud_color, -1)

    cv2.imshow('Dual-Hand ASL Recognition', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()
