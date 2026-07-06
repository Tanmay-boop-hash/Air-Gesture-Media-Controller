import cv2
import threading
import uvicorn
from hand_tracker import HandTracker
from feature_extractor import FeatureExtractor
from gesture_classifier import GestureClassifier
from state_machine import StateMachine
from action_dispatcher import ActionDispatcher
from api.server import app, current_state

tracker = HandTracker()
extractor = FeatureExtractor()
classifier = GestureClassifier()
state_machine = StateMachine()
dispatcher = ActionDispatcher()

# Run FastAPI in a background thread so it doesn't block camera loop
def run_api():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

api_thread = threading.Thread(target=run_api, daemon=True)
api_thread.start()
print("API running on http://localhost:8000")


cap = cv2.VideoCapture(0)
print("Gesture Media Controller Starting... press Q to quit")


while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Flip horzontally - mirror mode feels natural
    frame = cv2.flip(frame, 1)
    landmarks = tracker.get_landmarks(frame)
    frame = tracker.draw_landmarks(frame, landmarks)

    features = extractor.extract(landmarks)
    raw_gesture = classifier.classify(features)
    confirmed_gesture = state_machine.update(raw_gesture)
    debug = state_machine.get_debug_info()

    # Update shared state - SSE picks this up and streams to React
    current_state["raw_gesture"] = raw_gesture
    current_state["confirmed_gesture"] = confirmed_gesture
    current_state["hold_progress"] = round(
        min(debug['hold'] / debug['hold_needed'], 1.0), 2
    )
    current_state["state_machine"] = debug['state']

    dispatcher.dispatch(confirmed_gesture)

    if features:
        # Finger states
        fingers = ['thumb', 'index', 'middle', 'ring', 'pinky']
        states = [features['thumb_up'], features['index_up'], features['middle_up'], features['ring_up'], features['pinky_up']]

        status = ' '.join(f"{'UP' if s else '--'}" for s in states)
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Raw gesture - what classifier sees (still flickery)
    cv2.putText(frame, f"Raw: {raw_gesture}", (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (150, 150, 2), 2)

    # Hold progress bar - fills up as we hold a gesture
    hold_pct = min(debug['hold']/debug['hold_needed'], 1.0)
    bar_width = int(hold_pct * 300)
    cv2.rectangle(frame, (10, 82), (310, 98), (40, 40, 40), -1)
    cv2.rectangle(frame, (10, 82), (10 + bar_width, 98), (0, 220, 100), -1)

    # Confirmed gesture display
    display_gesture = confirmed_gesture or debug['current']
    color = (0, 255, 255) if confirmed_gesture else (180, 180, 180)
    cv2.putText(frame, display_gesture, (10, 135), cv2.FONT_HERSHEY_SIMPLEX, 1.1, color, 3) 
        
    # state indicator 
    state_color = (0, 200, 100) if debug['state'] == 'IDLE' else (0, 120, 255)
    cv2.putText(frame, debug['state'], (10, 168), cv2.FONT_HERSHEY_SIMPLEX, 0.6, state_color, 2)

    # Gesture legend bottom-left
    legend = [
        "OPEN_PALM = play/pause",
        "POINT_LEFT/RIGHT = prev/next",
        "THUMBS_UP/PINCH = vol +/-",
        "FIST = mute  |  PEACE = like",
    ]
    for i, line in enumerate(legend):
        cv2.putText(frame, line, (10, frame.shape[0] - 80 + i*20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

    cv2.imshow("Gesture Media Controller", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break   

cap.release()
cv2.destroyAllWindows()
