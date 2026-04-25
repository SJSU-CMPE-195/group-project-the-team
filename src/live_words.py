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

# --- Configuration ---
MODEL_PATH = 'models/citizen10_stgcn.pth'
ENCODER_PATH = 'models/label_encoder_citizen10.pkl'
CONFIDENCE_THRESHOLD = 0.45
SEQUENCE_LENGTH = 30

device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')

# Load Model
with open(ENCODER_PATH, 'rb') as f:
    label_encoder = pickle.load(f)
model = SignLanguageSTGCN(num_classes=len(label_encoder.classes_)).to(device)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()

# MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)

cap = cv2.VideoCapture(0)
sequence_queue = deque(maxlen=SEQUENCE_LENGTH)
current_word = "..."
current_confidence = 0.0

print("\nStarting DEDICATED WORD/GESTURE Inference. Press 'q' to quit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success: break
    frame = cv2.flip(frame, 1)
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    right_hand = [0] * 63
    left_hand = [0] * 63
    
    if results.multi_hand_landmarks:
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
        sequence_queue.clear()
        current_word = "..."

    if len(sequence_queue) == SEQUENCE_LENGTH:
        input_data = np.array(sequence_queue, dtype=np.float32)
        input_tensor = torch.tensor(input_data).unsqueeze(0).to(device)
        
        with torch.no_grad():
            outputs = model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
            conf, idx = torch.max(probabilities, 0)
            
            current_word = label_encoder.inverse_transform([idx.item()])[0]
            current_confidence = conf.item()

    # HUD
    cv2.rectangle(frame, (0, 0), (450, 60), (20, 50, 20), -1)
    color = (0, 255, 0) if current_confidence > CONFIDENCE_THRESHOLD else (150, 150, 150)
    display_name = current_word.replace('1', '')
    cv2.putText(frame, f"SIGN: {display_name.upper()}", (20, 40), cv2.FONT_HERSHEY_DUPLEX, 1.0, color, 2)
    
    cv2.imshow('ASL Signs ONLY', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()
