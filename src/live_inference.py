import cv2
import mediapipe as mp
import pickle
import math
import numpy as np
from collections import deque, Counter
import warnings
warnings.filterwarnings('ignore')

# ─── Landmark Constants ────────────────────────────────────────────────────────
WRIST = 0
MIDDLE_MCP = 9
FINGERTIPS = [4, 8, 12, 16, 20]
MCPS = [5, 9, 13, 17]


def compute_distance(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)


def compute_angle(a, b, c):
    ba = [a[i] - b[i] for i in range(3)]
    bc = [c[i] - b[i] for i in range(3)]
    dot = sum(ba[i]*bc[i] for i in range(3))
    mag_ba = math.sqrt(sum(x**2 for x in ba)) + 1e-8
    mag_bc = math.sqrt(sum(x**2 for x in bc)) + 1e-8
    cos_angle = max(-1, min(1, dot / (mag_ba * mag_bc)))
    return math.acos(cos_angle)


def normalize_landmarks(landmarks):
    """Same normalization as create_dataset.py — must stay in sync."""
    pts = [(lm.x, lm.y, lm.z) for lm in landmarks]
    
    wrist = pts[WRIST]
    centered = [(p[0]-wrist[0], p[1]-wrist[1], p[2]-wrist[2]) for p in pts]
    
    ref_dist = compute_distance(centered[WRIST], centered[MIDDLE_MCP])
    if ref_dist < 1e-6:
        ref_dist = 1e-6
    
    normalized = [(p[0]/ref_dist, p[1]/ref_dist, p[2]/ref_dist) for p in centered]
    
    coord_features = []
    for i in range(1, 21):
        coord_features.extend([normalized[i][0], normalized[i][1], normalized[i][2]])
    
    distance_features = []
    for tip in FINGERTIPS:
        distance_features.append(compute_distance(normalized[tip], normalized[WRIST]))
    
    palm_center = [
        np.mean([normalized[m][0] for m in MCPS]),
        np.mean([normalized[m][1] for m in MCPS]),
        np.mean([normalized[m][2] for m in MCPS])
    ]
    for tip in FINGERTIPS:
        distance_features.append(compute_distance(normalized[tip], palm_center))
    
    for i in range(len(FINGERTIPS)):
        for j in range(i+1, len(FINGERTIPS)):
            distance_features.append(
                compute_distance(normalized[FINGERTIPS[i]], normalized[FINGERTIPS[j]])
            )
    
    angle_features = []
    thumb_chain = [1, 2, 3, 4]
    for i in range(len(thumb_chain) - 2):
        angle_features.append(compute_angle(
            normalized[thumb_chain[i]], normalized[thumb_chain[i+1]], normalized[thumb_chain[i+2]]
        ))
    
    finger_chains = [
        [0, 5, 6, 7, 8], [0, 9, 10, 11, 12],
        [0, 13, 14, 15, 16], [0, 17, 18, 19, 20],
    ]
    for chain in finger_chains:
        for i in range(len(chain) - 2):
            angle_features.append(compute_angle(
                normalized[chain[i]], normalized[chain[i+1]], normalized[chain[i+2]]
            ))
    
    return coord_features + distance_features + angle_features


# ─── 1. Load Model ────────────────────────────────────────────────────────────
print("Loading model...")
with open('models/asl_model.pkl', 'rb') as f:
    data = pickle.load(f)
    model = data['model']
    label_encoder = data['label_encoder']
    scaler = data.get('scaler', None)
    model_type = data.get('model_type', 'random_forest')

print(f"  Model type: {model_type}")
print(f"  Classes: {len(label_encoder.classes_)}")

# ─── 2. Setup MediaPipe ───────────────────────────────────────────────────────
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

# ─── 3. Smoothing & Confidence ────────────────────────────────────────────────
SMOOTHING_WINDOW = 15
CONFIDENCE_THRESHOLD = 0.60
prediction_buffer = deque(maxlen=SMOOTHING_WINDOW)

# ─── 4. CLAHE ─────────────────────────────────────────────────────────────────
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

def preprocess_frame(frame):
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

# ─── 5. Camera Loop ───────────────────────────────────────────────────────────
cap = cv2.VideoCapture(0)
print("Press 'q' to quit...")

displayed_label = "..."

while cap.isOpened():
    success, image = cap.read()
    if not success:
        break

    image = cv2.flip(image, 1)
    processed = preprocess_frame(image)
    image_rgb = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)

    confidence = 0.0

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                image, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )

            try:
                # Extract NORMALIZED features
                features = normalize_landmarks(hand_landmarks.landmark)
                features_array = np.array(features).reshape(1, -1)
                
                # Apply scaler if available (MLP model)
                if scaler is not None:
                    features_array = scaler.transform(features_array)
                
                # Predict with probabilities
                proba = model.predict_proba(features_array)[0]
                max_idx = np.argmax(proba)
                confidence = proba[max_idx]
                
                if confidence >= CONFIDENCE_THRESHOLD:
                    raw_label = label_encoder.inverse_transform([max_idx])[0]
                    prediction_buffer.append(raw_label)
            except Exception:
                pass
        
        # Majority vote
        if prediction_buffer:
            displayed_label = Counter(prediction_buffer).most_common(1)[0][0]
    else:
        if len(prediction_buffer) > 0:
            prediction_buffer.popleft()
        if not prediction_buffer:
            displayed_label = "..."

    # ── HUD ────────────────────────────────────────────────────────────────
    h, w, _ = image.shape
    
    overlay = image.copy()
    cv2.rectangle(overlay, (0, 0), (w, 90), (30, 30, 30), -1)
    image = cv2.addWeighted(overlay, 0.7, image, 0.3, 0)

    cv2.putText(image, "Silent Voice Bridge", (15, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 200, 255), 2)

    sign_color = (0, 255, 100) if confidence >= CONFIDENCE_THRESHOLD else (0, 180, 255)
    cv2.putText(image, f"Sign: {displayed_label}", (15, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1.4, sign_color, 3)

    # Confidence bar
    bar_x = w - 220
    bar_w, bar_h, bar_y = 200, 18, 55
    cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (60, 60, 60), -1)
    fill_w = int(bar_w * confidence)
    bar_color = (0, 255, 100) if confidence >= CONFIDENCE_THRESHOLD else (0, 140, 255)
    cv2.rectangle(image, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), bar_color, -1)
    cv2.putText(image, f"Conf: {confidence * 100:.0f}%", (bar_x, bar_y - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    cv2.putText(image, "Press 'q' to quit", (15, h - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

    cv2.imshow('Silent Voice Bridge - Real Time', image)
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()