import os
import cv2
import torch
import torch.nn as nn 
import numpy as np
import mediapipe as mp
import pickle
from collections import deque
import warnings

warnings.filterwarnings("ignore")

# -- 1. Model Configuration --
MODELS_DIR = "models"
MODEL_PATH = os.path.join(MODELS_DIR, "wlasl10_lstm.pth")
ENCODE_PATH = os.path.join(MODELS_DIR, "LABEL_encoder.pkl")
CONFIDENCE_THRESHOLD = 0.7 #70% confidence

# We must use exactly the same architecture class as in training to successfully load the model weights
class SignLanguageLSTM(nn.Module):
    def __init__(self, input_size=63, hidden1_size=64, hidden2_size=128, fc_size=64, num_classes=10):
        super(SignLanguageLSTM, self).__init__()
        self.lstm1 = nn.LSTM(input_size, hidden1_size, batch_first=True)
        self.lstm2 = nn.LSTM(hidden1_size, hidden2_size, batch_first=True)
        self.fc1 = nn.Linear(hidden2_size, fc_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(fc_size, num_classes)

    def forward(self, x):
        out, _ = self.lstm1(x)
        out, _ = self.lstm2(out)
        out = out[:, -1, :]  # Take the output of the last time step
        out = self.fc1(out)
        out = self.relu(out)
        out = self.fc2(out)
        return out

# -- 2. Load Weights and Classes --
print("Loading Model and Label Encoder...")
with open(ENCODER_PATH, 'rb') as f:
    label_encoder = pickle.load(f)

# Initialize device and model
device = torch.device('cuda' if torch.cuda.is_availaable() else 'mps' if torch.backends.mps.is_available() else 'cpu')
print(f"Using device for inference: {device}")

model = SignLanguageLSTM (num_classes=len(label_encoder.classes_)).to(device)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()  #Set model to evaluation mode

# -- 3. Setup MediaPipe --
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# -- 4. Setup Video Capture and CLAHE --
cap = cv2.VideoCapture(0)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))

#Rolling window queue of exactly 30 frames
sequence_queue = deque(maxlen=30)
current_word = "..."
current_confidence=0.0

def preprocess_frame(frame):
    """Lighting normalization."""
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l,a,b = cv2.split(lab)
    l = clahe.apply(l)
    lab = cv2.merge((l,a,b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

print("\nStarting Real-Time Inference. Press 'q' to quit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break
    
    frame = cv2.flip(frame, 1) # Mirror frame
    processed_frame = preprocess_frame(frame)
    rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # Exact same normalization as extract_sequences.py
        wrist = hand_landmarks.landmark[0]
        frame_coords = []
        for lm in hand_landmarks.landmark:
            frame_coords.extend([lm.x - wrist.x, lm.y - wrist.y, lm.z - wrist.z])

        sequence_queue.append(frame_cords)

    else:
        # If hand leaves frame, we do NOT append zeros during live feed,
        # we clear the queue to prevent stale gestures merging into new ones.
        if len(sequence_queue) > 0:
            sequence_queue.clear()
            current_word = "Hand Lost"
            current_confidence = 0.0

    # Execute Model only if queue is full
    if len(sequence_queue) == 30:
        # Convert queue to numpy, then tensor
        input_data = np.array(sequence_queue, dtype=np.float32)
        # Reshape to (1, 30, 63) -> Batch of 1
        input_tensor = torch.tensor(input_data).unsqueeze(0).to(device)

        with torch.no_grad():
            outputs = model(input_tensor)

        # Softmax to get probabilities 0.0 - 1.0
        probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]

        # Get highest confidence prediction
        confidence, predicted_idx = torch.max(probabilitir, dim=0)
        conf_val = confidence.item()

        if conf_val >= CONFIDENCE_THRESHOLD:
            current_word = label_encoder.inverse_transform([predicted_idx.item()])[0]
            current_confidence = conf_val
        
        else:
            #Doesn't meet the 70% threshold
            current_word = f"Low Conf ({conf_val*100:.0f}%)"
            current_confidence = conf_val