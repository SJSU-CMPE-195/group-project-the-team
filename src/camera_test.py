import cv2
import mediapipe as mp

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Configure for both hands and high confidence
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,  # Tracks both left and right
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(0)

print("Press 'q' to quit...")

while cap.isOpened():
    success, image = cap.read()
    if not success:
        break

    # Flip the image horizontally for a selfie-view display
    image = cv2.flip(image, 1)
    
    # MediaPipe requires RGB, but OpenCV uses BGR
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)

    # Draw the hand annotations on the image
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    cv2.imshow('Silent Voice Bridge - Vision Test', image)

    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()