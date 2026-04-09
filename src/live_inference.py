import cv2
import mediapipe as mp
import pickle
import numpy as np
from collections import deque

# 1. Load the trained model
with open('models/asl_model.pkl', 'rb') as f:
    data = pickle.load(f)
    model = data['model']
    label_encoder = data['label_encoder']

# 2. Setup MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

# 3. Prediction Smoothing & Confidence Settings
SMOOTHING_WINDOW = 15          # Number of past frames to consider
CONFIDENCE_THRESHOLD = 0.60    # Minimum probability to accept a prediction
prediction_buffer = deque(maxlen=SMOOTHING_WINDOW)

# 4. CLAHE for lighting normalization
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

def preprocess_frame(frame):
    """Apply CLAHE to normalize lighting conditions."""
    # Convert to LAB color space (L = lightness)
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    # Apply CLAHE only to the lightness channel
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    # Convert back to BGR
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

def get_smoothed_prediction(buffer):
    """Return the most common prediction from the buffer (majority vote)."""
    if not buffer:
        return None
    from collections import Counter
    counts = Counter(buffer)
    return counts.most_common(1)[0][0]

# 5. Start Camera
cap = cv2.VideoCapture(0)
print("Press 'q' to quit...")

# Track the stable displayed label
displayed_label = "..."
frame_count = 0

while cap.isOpened():
    success, image = cap.read()
    if not success:
        break

    image = cv2.flip(image, 1)

    # Apply CLAHE preprocessing for better lighting robustness
    processed = preprocess_frame(image)

    # Convert to RGB for MediaPipe
    image_rgb = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)

    confidence = 0.0
    current_label = None

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw landmarks with nicer styling
            mp_drawing.draw_landmarks(
                image,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )

            # Extract coordinates for prediction
            coords = []
            for lm in hand_landmarks.landmark:
                coords.extend([lm.x, lm.y, lm.z])

            # Get prediction probabilities
            proba = model.predict_proba([coords])[0]
            max_idx = np.argmax(proba)
            confidence = proba[max_idx]

            # Only accept high-confidence predictions
            if confidence >= CONFIDENCE_THRESHOLD:
                raw_label = label_encoder.inverse_transform([max_idx])[0]
                prediction_buffer.append(raw_label)
            # else: don't add to buffer (ignore noisy frames)

            # Get the smoothed (majority vote) prediction
            current_label = get_smoothed_prediction(prediction_buffer)
    else:
        # No hand detected — clear the buffer gradually
        if len(prediction_buffer) > 0:
            prediction_buffer.popleft()
        current_label = None

    # Update the displayed label
    if current_label:
        displayed_label = current_label
    else:
        displayed_label = "..."

    # ── Draw the HUD ──────────────────────────────────────────────
    h, w, _ = image.shape

    # Semi-transparent overlay bar at the top
    overlay = image.copy()
    cv2.rectangle(overlay, (0, 0), (w, 90), (30, 30, 30), -1)
    image = cv2.addWeighted(overlay, 0.7, image, 0.3, 0)

    # Title
    cv2.putText(image, "Silent Voice Bridge", (15, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 200, 255), 2)

    # Predicted sign (large)
    sign_color = (0, 255, 100) if confidence >= CONFIDENCE_THRESHOLD else (0, 180, 255)
    cv2.putText(image, f"Sign: {displayed_label}", (15, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1.4, sign_color, 3)

    # Confidence bar
    bar_x = w - 220
    bar_w = 200
    bar_h = 18
    bar_y = 55
    # Background
    cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (60, 60, 60), -1)
    # Fill
    fill_w = int(bar_w * confidence)
    bar_color = (0, 255, 100) if confidence >= CONFIDENCE_THRESHOLD else (0, 140, 255)
    cv2.rectangle(image, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), bar_color, -1)
    # Label
    cv2.putText(image, f"Conf: {confidence * 100:.0f}%", (bar_x, bar_y - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    # Instructions at the bottom
    cv2.putText(image, "Press 'q' to quit", (15, h - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

    cv2.imshow('Silent Voice Bridge - Real Time', image)
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()