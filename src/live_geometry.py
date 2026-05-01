import cv2
import mediapipe as mp
from hand_geometry import HandGeometry

# Initialize
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
engine = HandGeometry()

cap = cv2.VideoCapture(0)

print("\n--- Geometric ASL Research Tool ---")
print("Recognizing: A, B, I, L, V, F")
print("Press 'q' to quit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success: break
    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape
    
    # Process
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    detected_letter = "Scanning..."
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # 1. Get Spatial Features
            f = engine.get_spatial_features(hand_landmarks.landmark)
            letter = engine.classify_letter(hand_landmarks.landmark)
            
            if letter:
                detected_letter = f"LETTER: {letter}"
            
            # 2. Visual Debugging (Draw spatial status)
            cv2.putText(frame, f"I-M DIST: {f['d_im']:.3f}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"CROSSED: {f['crossed']}", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"INDEX UP: {f['up'][0]}", (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"MIDDLE UP: {f['up'][1]}", (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Main HUD
    cv2.rectangle(frame, (0, 0), (w, 70), (40, 40, 40), -1)
    cv2.putText(frame, detected_letter, (w//2 - 100, 50), 
                cv2.FONT_HERSHEY_DUPLEX, 1.5, (0, 255, 255), 2)
    
    cv2.imshow('Geometric ASL Research', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
