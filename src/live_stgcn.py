import os
import cv2
import torch
import torch.nn as nn
import numpy as np
import mediapipe as mp
import pickle
from collections import deque
import warnings
from stgcn_model import SignLanguageSTGCN

warnings.filterwarnings('ignore')

# --- 1. Model Configuration ---
MODELS_DIR = 'models'
MODEL_PATH = os.path.join(MODELS_DIR, 'wlasl10_stgcn.pth')
ENCODER_PATH = os.path.join(MODELS_DIR, 'label_encoder.pkl')
CONFIDENCE_THRESHOLD = 0.50  # Lowered slightly as ST-GCN is more conservative

# --- 2. Load Weights and Classes ---
print("Loading ST-GCN Model and Label Encoder...")
with open(ENCODER_PATH, 'rb') as f:
    label_encoder = pickle.load(f)

device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
print(f"Using device for inference: {device}")

model = SignLanguageSTGCN(num_classes=len(label_encoder.classes_)).to(device)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()

# --- 3. Setup MediaPipe ---
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)

# --- 4. Setup Video Capture ---
cap = cv2.VideoCapture(0)
sequence_queue = deque(maxlen=30)
current_word = "..."
current_confidence = 0.0
top_3_text = "..."
mirror_view = True

print("\nStarting ST-GCN Live Inference. Press 'q' to quit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success: break

    if mirror_view:
        frame = cv2.flip(frame, 1)
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    right_hand_coords = [0] * 63
    left_hand_coords = [0] * 63
    
    if results.multi_hand_landmarks and results.multi_handedness:
        for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            label = results.multi_handedness[i].classification[0].label
            wrist = hand_landmarks.landmark[0]
            coords = []
            for lm in hand_landmarks.landmark:
                coords.extend([lm.x - wrist.x, lm.y - wrist.y, lm.z - wrist.z])
            if label == 'Right': right_hand_coords = coords
            else: left_hand_coords = coords
        
        sequence_queue.append(right_hand_coords + left_hand_coords)
    else:
        if len(sequence_queue) > 0:
            sequence_queue.clear()
            current_word = "Hand Lost"
            current_confidence = 0.0

    if len(sequence_queue) == 30:
        input_data = np.array(sequence_queue, dtype=np.float32)
        input_tensor = torch.tensor(input_data).unsqueeze(0).to(device)
        
        with torch.no_grad():
            outputs = model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
            topk_probs, topk_indices = torch.topk(probabilities, 3)
            
            conf_val = topk_probs[0].item()
            predicted_idx = topk_indices[0].item()
            
            current_word = label_encoder.inverse_transform([predicted_idx])[0]
            current_confidence = conf_val
                
            debug_info = [f"{label_encoder.inverse_transform([topk_indices[i].item()])[0]}: {topk_probs[i].item()*100:.0f}%" for i in range(3)]
            top_3_text = " | ".join(debug_info)

    # --- HUD ---
    h, w, _ = frame.shape
    cv2.rectangle(frame, (0, 0), (w, 90), (30, 30, 30), -1)
    color = (0, 255, 0) if current_confidence >= CONFIDENCE_THRESHOLD else (0, 165, 255)
    cv2.putText(frame, f"ST-GCN: {current_word.upper()}", (20, 40), cv2.FONT_HERSHEY_DUPLEX, 1.0, color, 2)
    cv2.putText(frame, f"Top 3: {top_3_text}", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    
    # Confidence Bar
    bar_x, bar_y, bar_w, bar_h = w - 220, 25, 200, 20
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (60, 60, 60), -1)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + int(bar_w * current_confidence), bar_y + bar_h), color, -1)
    cv2.putText(frame, f"Mirror: {'ON' if mirror_view else 'OFF'} (Press 'm')", (w-220, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

    cv2.imshow('ST-GCN Live WLASL Inference', frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'): break
    elif key == ord('m'): mirror_view = not mirror_view

cap.release()
cv2.destroyAllWindows()
