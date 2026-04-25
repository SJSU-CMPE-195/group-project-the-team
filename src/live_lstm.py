import os
import cv2
import torch
import torch.nn as nn
import numpy as np
import mediapipe as mp
import pickle
from collections import deque
import warnings

warnings.filterwarnings('ignore')

# --- 1. Model Configuration ---
MODELS_DIR = 'models'
MODEL_PATH = os.path.join(MODELS_DIR, 'wlasl10_lstm.pth')
ENCODER_PATH = os.path.join(MODELS_DIR, 'label_encoder.pkl')
CONFIDENCE_THRESHOLD = 0.70  # 70% confidence

# We must use exactly the same architecture class as in training to successfully load the weights
class SignLanguageLSTM(nn.Module):
    def __init__(self, input_size=126, hidden1_size=64, hidden2_size=128, fc_size=64, num_classes=10):
        super(SignLanguageLSTM, self).__init__()
        self.lstm1 = nn.LSTM(input_size, hidden1_size, batch_first=True)
        self.lstm2 = nn.LSTM(hidden1_size, hidden2_size, batch_first=True)
        self.fc1 = nn.Linear(hidden2_size, fc_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(fc_size, num_classes)

    def forward(self, x):
        out, _ = self.lstm1(x)
        out, _ = self.lstm2(out)
        out = out[:, -1, :]
        out = self.fc1(out)
        out = self.relu(out)
        out = self.fc2(out)
        return out

# --- 2. Load Weights and Classes ---
print("Loading Model and Label Encoder...")
with open(ENCODER_PATH, 'rb') as f:
    label_encoder = pickle.load(f)

# Initialize device and model
device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
print(f"Using device for inference: {device}")

model = SignLanguageLSTM(num_classes=len(label_encoder.classes_)).to(device)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()  # Set model to evaluation mode

# --- 3. Setup MediaPipe ---
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False, 
    max_num_hands=2, 
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# --- 4. Setup Video Capture and CLAHE ---
cap = cv2.VideoCapture(0)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

# Rolling window queue of exactly 30 frames
sequence_queue = deque(maxlen=30)
current_word = "..."
current_confidence = 0.0
top_3_text = "..."
mirror_view = True

def preprocess_frame(frame):
    """Lighting normalization."""
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

print("\nStarting Real-Time Inference. Press 'q' to quit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    if mirror_view:
        frame = cv2.flip(frame, 1)  # Mirror frame
    
    processed_frame = preprocess_frame(frame)
    rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
    
    results = hands.process(rgb_frame)
    
    # Initialize both hands as zeros
    right_hand_coords = [0] * 63
    left_hand_coords = [0] * 63
    
    if results.multi_hand_landmarks and results.multi_handedness:
        for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
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
        
        # Append combined vector: Right + Left
        sequence_queue.append(right_hand_coords + left_hand_coords)
    else:
        # If hand leaves frame, clear the queue
        if len(sequence_queue) > 0:
            sequence_queue.clear()
            current_word = "Hand Lost"
            current_confidence = 0.0

    # Execute Model only if queue is full
    if len(sequence_queue) == 30:
        input_data = np.array(sequence_queue, dtype=np.float32)
        input_tensor = torch.tensor(input_data).unsqueeze(0).to(device)
        
        with torch.no_grad():
            outputs = model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
            
            # Get Top 3 predictions for debugging
            topk_probs, topk_indices = torch.topk(probabilities, 3)
            
            # Best prediction
            conf_val = topk_probs[0].item()
            predicted_idx = topk_indices[0].item()
            
            if conf_val >= CONFIDENCE_THRESHOLD:
                current_word = label_encoder.inverse_transform([predicted_idx])[0]
                current_confidence = conf_val
            else:
                current_word = f"Low Conf ({conf_val*100:.0f}%)"
                current_confidence = conf_val
                
            # Prepare debug text for Top 3
            debug_info = []
            for i in range(3):
                p = topk_probs[i].item()
                idx = topk_indices[i].item()
                label = label_encoder.inverse_transform([idx])[0]
                debug_info.append(f"{label}: {p*100:.0f}%")
            top_3_text = " | ".join(debug_info)

    # --- 5. Output Graphics to HUD ---
    h, w, _ = frame.shape
    cv2.rectangle(frame, (0, 0), (w, 90), (30, 30, 30), -1)
    
    # Draw word
    color = (0, 255, 0) if current_confidence >= CONFIDENCE_THRESHOLD else (0, 165, 255)
    cv2.putText(frame, f"Sign: {current_word.upper()}", (20, 40), cv2.FONT_HERSHEY_DUPLEX, 1.0, color, 2)
    
    # Draw Top 3 Debug
    cv2.putText(frame, f"Top 3: {top_3_text if 'top_3_text' in locals() else '...'}", (20, 75), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    
    # Draw confidence bar
    bar_x = w - 220
    bar_w, bar_h, bar_y = 200, 20, 25
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (60, 60, 60), -1)
    fill_w = int(bar_w * current_confidence)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), color, -1)
    cv2.putText(frame, f"Conf: {current_confidence * 100:.0f}%", (bar_x, bar_y - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    cv2.putText(frame, f"Mirror: {'ON' if mirror_view else 'OFF'} (Press 'm' to toggle)", (w-220, 80), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

    cv2.imshow('Live WLASL-10 Inference', frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('m'):
        mirror_view = not mirror_view

cap.release()
cv2.destroyAllWindows()
