import cv2
import mediapipe as mp

class HandTracker:
    def __init__(self, max_hands=1, detection_confidence=0.7, tracking_confidence=0.5):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        
        self.hands = self.mp_hands.Hands(
            max_num_hands= max_hands,
            min_detection_confidence= detection_confidence,
            min_tracking_confidence= tracking_confidence
        )

    def get_landmarks(self, frame):
        """
        Takes a BGR frame from OpenCV.
        Returns a list of 21 (x, y, z) tuples in pixel coordinates,
        or None if no hand is detected.
        """
        h, w, _ = frame.shape

        # Mediapipe needs RGB, OpenCV gives BGR
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        if not results.multi_hand_landmarks:
            return None
        
        # Take the first detected hand only
        hand = results.multi_hand_landmarks[0]

        # Convert normalized coordinates to actual pixel coordinates
        landmarks = []
        for lm in hand.landmark:
            x, y = int(lm.x * w), int(lm.y * h)
            landmarks.append((x, y, lm.z))

        return landmarks  # list of 21 (x, y, z) tuples

    
    def draw_landmarks(self, frame, landmarks):
        """
        Draws the hand skeleton on the frame for debugging.
        Only used during development to get visual feedback.
        """
        if landmarks is None:
            return frame
        
        # Re-run to get the mediapipe object for drawing 
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame, 
                    hand_landmarks, 
                    self.mp_hands.HAND_CONNECTIONS
                )

        return frame