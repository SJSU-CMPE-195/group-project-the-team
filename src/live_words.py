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
from sentence_engine import SentenceEngine

warnings.filterwarnings('ignore')

# --- 1. Configuration ---
MODEL_PATH = 'models/citizen20_stgcn.pth'
ENCODER_PATH = 'models/label_encoder_citizen20.pkl'
CONFIDENCE_THRESHOLD = 0.45
SEQUENCE_LENGTH = 30

device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')

# Load Model & Engine
with open(ENCODER_PATH, 'rb') as f:
    label_encoder = pickle.load(f)
model = SignLanguageSTGCN(num_classes=len(label_encoder.classes_)).to(device)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()

engine = SentenceEngine(confidence_threshold=0.5)

# MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)

cap = cv2.VideoCapture(0)
sequence_queue = deque(maxlen=SEQUENCE_LENGTH)
current_word = "..."
current_confidence = 0.0
full_sentence = ""

print("\nStarting SENTENCE-BUILDER Inference. Press 'q' to quit, 'r' to reset sentence.")

while cap.isOpened():
    success, frame = cap.read()
    if not success: break
    frame = cv2.flip(frame, 1)
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    right_hand = [0] * 63
    left_hand = [0] * 63
    hand_count = 0
    
    if results.multi_hand_landmarks:
        hand_count = len(results.multi_hand_landmarks)
        for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            label = results.multi_handedness[i].classification[0].label
            wrist = hand_landmarks.landmark[0]
            coords = []
            for lm in hand_landmarks.landmark:
                coords.extend([lm.x - wrist.x, lm.y - wrist.y, lm.z - wrist.z])
            if label == 'Right': right_hand = coords
            else: left_hand = coords
        
        sequence_queue.append(right_hand + left_hand)
    else:
        if len(sequence_queue) > 0:
            sequence_queue.clear()
            current_word = "..."
            # Inform engine hands are down
            engine.process_prediction([], 0)

    if len(sequence_queue) == SEQUENCE_LENGTH:
        input_data = np.array(sequence_queue, dtype=np.float32)
        input_tensor = torch.tensor(input_data).unsqueeze(0).to(device)
        
        with torch.no_grad():
            outputs = model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
            
            topk_probs, topk_indices = torch.topk(probabilities, 3)
            
            # Prepare predictions for the engine
            preds = []
            for i in range(3):
                word = label_encoder.inverse_transform([topk_indices[i].item()])[0]
                conf = topk_probs[i].item()
                preds.append((word, conf))
            
            # Update Sentence Engine (Now with Energy Logic)
            candidate, energy_ratio, committed = engine.process_prediction(preds, hand_count)
            
            current_word = candidate if candidate else "..."
            current_confidence = energy_ratio # Use energy for the bar
            full_sentence = engine.get_sentence_text()

    # --- ADVANCED HUD ---
    h, w, _ = frame.shape
    # Dynamic Colors
    accent_color = (0, 255, 127) if current_confidence >= 1.0 else (0, 200, 255)
    
    # Bottom Sentence Bar (Premium Dark Mode)
    cv2.rectangle(frame, (0, h-80), (w, h), (15, 15, 15), -1)
    cv2.putText(frame, f"TRANSLATION: {full_sentence}", (20, h-30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    
    # Top Status Bar
    cv2.rectangle(frame, (0, 0), (w, 80), (25, 25, 25), -1)
    display_name = current_word.replace('1', '')
    
    # Candidate Word (Yellow if charging, Green if locked)
    label_status = "HOLDING..." if current_confidence < 1.0 and current_word != "..." else "LOCKED"
    cv2.putText(frame, f"{display_name.upper()}", (20, 55), cv2.FONT_HERSHEY_DUPLEX, 1.3, accent_color, 2)
    cv2.putText(frame, label_status, (w - 180, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

    # ENERGY COMMITMENT BAR (Progress bar for the current sign)
    bar_width = 300
    bar_x, bar_y = 20, 65
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + 8), (50, 50, 50), -1)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + int(bar_width * current_confidence), bar_y + 8), accent_color, -1)
    
    cv2.imshow('Pro-Level ASL Translator', frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'): break
    elif key == ord('r'): engine.reset()

cap.release()
cv2.destroyAllWindows()

cap.release()
cv2.destroyAllWindows()
