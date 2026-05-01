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
from hand_geometry import HandGeometry

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
geo_engine = HandGeometry()

# MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)

cap = cv2.VideoCapture(0)
sequence_queue = deque(maxlen=SEQUENCE_LENGTH)
raw_wrist_history = {} # Track raw wrist (x,y) for velocity
current_word = "..."
current_confidence = 0.0
full_sentence = ""

# Spelling Mode Variables
spell_mode = False
current_letter = None
locked_letter = None
letter_hold_frames = 0
spelled_word = ""

print("\nStarting PRO-LEVEL Translator.")
print("Press 'q' to quit, 'r' to reset sentence.")
print("Press 's' to toggle SPELLING MODE.")

while cap.isOpened():
    success, frame = cap.read()
    if not success: break
    frame = cv2.flip(frame, 1)
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    right_hand = [0.0] * 63
    left_hand = [0.0] * 63
    hand_count = 0
    hand_velocity = 0.0
    primary_lm = None
    
    if results.multi_hand_landmarks:
        hand_count = len(results.multi_hand_landmarks)
        for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            label = results.multi_handedness[i].classification[0].label
            wrist = hand_landmarks.landmark[0]
            
            if i == 0: primary_lm = hand_landmarks.landmark # For spelling
            
            # --- VELOCITY CALCULATION ---
            if label in raw_wrist_history:
                prev_x, prev_y = raw_wrist_history[label]
                dist = ((wrist.x - prev_x)**2 + (wrist.y - prev_y)**2)**0.5
                hand_velocity = max(hand_velocity, dist)
            
            raw_wrist_history[label] = (wrist.x, wrist.y)

            coords = []
            for lm in hand_landmarks.landmark:
                coords.extend([lm.x - wrist.x, lm.y - wrist.y, lm.z - wrist.z])
            if label == 'Right': right_hand = coords
            else: left_hand = coords
        
        sequence_queue.append(right_hand + left_hand)
        
        # --- SPELLING MODE LOGIC ---
        if spell_mode and primary_lm:
            letter = geo_engine.classify_letter(primary_lm)
            if letter:
                if letter == current_letter:
                    letter_hold_frames += 1
                else:
                    current_letter = letter
                    letter_hold_frames = 0
                    
                if letter_hold_frames > 15 and locked_letter != letter:
                    locked_letter = letter
                    spelled_word += letter
            else:
                current_letter = None
                letter_hold_frames = 0
    else:
        raw_wrist_history = {} # Clear history when hands drop
        if len(sequence_queue) > 0:
            sequence_queue.clear()
            current_word = "..."
            engine.process_prediction([], 0)
            
        # Commit spelled word to sentence when hands drop
        if spell_mode and len(spelled_word) > 0:
            engine.sentence.append(spelled_word)
            spelled_word = ""
            locked_letter = None

    # --- WORD MODE LOGIC ---
    if not spell_mode and len(sequence_queue) == SEQUENCE_LENGTH:
        input_tensor = torch.tensor(np.array(sequence_queue), dtype=torch.float32).unsqueeze(0).to(device)
        with torch.no_grad():
            outputs = model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
            topk_probs, topk_indices = torch.topk(probabilities, 3)
            
            preds = []
            for i in range(3):
                word = label_encoder.inverse_transform([topk_indices[i].item()])[0]
                preds.append((word, topk_probs[i].item()))
            
            # Update Sentence Engine with VELOCITY
            candidate, energy_ratio, committed = engine.process_prediction(preds, hand_count, velocity=hand_velocity)
            
            current_word = candidate if candidate else "..."
            current_confidence = energy_ratio
            
    # --- AUTO-SPELL TOGGLE ---
    # If the user just signed "NAME", automatically enter spell mode!
    if not spell_mode and len(engine.sentence) > 0 and engine.sentence[-1] == "NAME":
        spell_mode = True
        sequence_queue.clear()
        current_letter = None
        locked_letter = None
        
    full_sentence = engine.get_sentence_text()
    if spell_mode and len(spelled_word) > 0:
        full_sentence += " " + spelled_word

    # --- ADVANCED HUD ---
    h, w, _ = frame.shape
    is_moving = hand_velocity > 0.05
    
    # Bottom Bar (Sentence)
    cv2.rectangle(frame, (0, h-80), (w, h), (15, 15, 15), -1)
    cv2.putText(frame, f"TRANSLATION: {full_sentence}", (20, h-30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    cv2.putText(frame, "Click this window to use 's' (Spell) or 'r' (Reset)", (20, h-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 100), 1)
    
    # Top Bar (Mode Interface)
    if spell_mode:
        cv2.rectangle(frame, (0, 0), (w, 80), (50, 10, 50), -1) # Purple background
        cv2.putText(frame, "[AUTO SPELL MODE] active" if (len(engine.sentence)>0 and engine.sentence[-1]=="NAME") else "[SPELL MODE]", (w - 300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 255), 2)
        display_text = f"Letter: {current_letter}" if current_letter else "Spelling..."
        cv2.putText(frame, display_text, (20, 55), cv2.FONT_HERSHEY_DUPLEX, 1.3, (255, 150, 255), 2)
        
        # Spelling progress bar
        bar_width = 200
        cv2.rectangle(frame, (20, 65), (20 + bar_width, 65 + 8), (30, 30, 30), -1)
        fill_width = int(min(letter_hold_frames / 15.0, 1.0) * bar_width)
        cv2.rectangle(frame, (20, 65), (20 + fill_width, 65 + 8), (255, 100, 255), -1)
        
    else:
        cv2.rectangle(frame, (0, 0), (w, 80), (25, 25, 25), -1) # Dark background
        accent_color = (0, 255, 127) if current_confidence >= 1.0 else (0, 200, 255)
        if is_moving: accent_color = (100, 100, 255)
        
        display_name = current_word.replace('1', '')
        label_status = "STILL..." if not is_moving else "TRANSITIONING"
        if current_confidence >= 1.0: label_status = "LOCKED"
        
        cv2.putText(frame, f"{display_name.upper()}", (20, 55), cv2.FONT_HERSHEY_DUPLEX, 1.3, accent_color, 2)
        cv2.putText(frame, label_status, (w - 200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

        bar_width = 300
        bar_x, bar_y = 20, 65
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + 8), (50, 50, 50), -1)
        if not is_moving:
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + int(bar_width * current_confidence), bar_y + 8), accent_color, -1)
        else:
            cv2.putText(frame, "WAITING FOR HOLD...", (bar_x, bar_y+7), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (200, 200, 200), 1)
    
    cv2.imshow('Pro-Level ASL Translator', frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'): break
    elif key == ord('r'): 
        engine.reset()
        spelled_word = ""
        spell_mode = False
    elif key == ord('s'): 
        spell_mode = not spell_mode
        sequence_queue.clear()
        current_letter = None
        locked_letter = None

cap.release()
cv2.destroyAllWindows()
