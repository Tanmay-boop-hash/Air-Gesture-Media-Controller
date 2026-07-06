# Air-Gesture-Media-Controller
A real time hand-gesture recognition system that controls media playback and system volumes using air gestures detected via a webcam. No hardware required beyond a standard webcam.

Built with a layered architecture — MediaPipe landmark detection, geometric feature extraction, rule-based gesture classification, a debounce state machine, and a system-level action dispatcher — running at ~30 FPS on Apple Silicon.

![Demo](assets/demo.gif)

---

## Features

- Real-time hand gesture recognition via webcam at ~30 FPS
- 7 gesture controls: play/pause, next/previous track, volume up/down, mute
- Auto-detects active media target — Spotify desktop, YouTube Music, YouTube, or any browser tab
- Debounce state machine prevents accidental or repeated action triggers
- React config UI with live gesture monitor via Server-Sent Events
- macOS-native media control via AppleScript + System Events
- Fully modular pipeline — each layer independently testable

---

## Gesture Reference

| Gesture | Action |
|---|---|
| Open Palm | Play / Pause |
| Point Left | Previous Track |
| Point Right | Next Track |
| Thumbs Up | Volume Up |
| Pinch | Volume Down |
| Fist | Mute Toggle |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Gesture Detection | MediaPipe Hands 0.10.21 |
| Computer Vision | OpenCV |
| Feature Extraction | NumPy, custom geometric features |
| Backend / API | FastAPI, Uvicorn |
| Live Streaming | Server-Sent Events (SSE) |
| Config UI | React 18, Vite, Axios |
| System Control | AppleScript, pynput |
| Language | Python 3.11, JavaScript |

---

## Architecture
```
Webcam → HandTracker → FeatureExtractor → GestureClassifier → StateMachine → ActionDispatcher
↕
FastAPI (SSE)
↕
React Config UI
```
- **HandTracker** (`hand_tracker.py`) — wraps MediaPipe Hands, converts normalized landmarks to pixel coordinates. Single responsibility: give the rest of the pipeline 21 (x, y, z) tuples per frame.

- **FeatureExtractor** (`feature_extractor.py`) — computes scale-invariant geometric features from raw landmarks: finger extension states, normalized pinch distance, and index finger angle. Position and scale independent — works regardless of hand distance from camera.

- **GestureClassifier** (`gesture_classifier.py`) — rule-based classifier mapping feature combinations to named gesture labels. No ML training required.

- **StateMachine** (`state_machine.py`) — debounce layer requiring a gesture to be held for N consecutive frames before firing. Prevents accidental triggers and action spam. Transitions: IDLE → TRIGGERED → IDLE.

- **ActionDispatcher** (`action_dispatcher.py`) — translates confirmed gesture labels to system actions. Auto-detects whether Spotify desktop, Chrome, or Safari is active and uses the appropriate control method (AppleScript for native apps, System Events keyboard injection for browsers).

- **FastAPI Bridge** (`api/server.py`) — exposes REST endpoints for config read/write and an SSE endpoint streaming live gesture state to the React UI at up to 20 updates/second.

---

## Project Structure

```
gesture-controller/
├── main.py                 # Entry point — camera loop + API thread
├── hand_tracker.py         # MediaPipe wrapper
├── feature_extractor.py    # Landmark → geometric features
├── gesture_classifier.py   # Features → gesture label
├── state_machine.py        # Debounce + hold logic
├── action_dispatcher.py    # Gesture → system action (macOS)
├── config.json             # Gesture-action mappings + settings
├── api/
│   ├── init.py
│   └── server.py           # FastAPI config bridge + SSE stream
└── ui/                     # React config frontend (Vite)
├── src/
│   └── App.jsx
└── package.json
```
---

## Setup & Installation

### Prerequisites

- macOS (Apple Silicon or Intel)
- Python 3.11+
- Node.js 18+
- Conda or virtualenv
- Webcam

### 1. Clone the repository

```bash
git clone https://github.com/Tanmay-boop-hash/Air-Gesture-Media-Controller.git
cd gesture-controller
```

### 2. Create Python environment

```bash
conda create -n gesture-ctrl python=3.11
conda activate gesture-ctrl
```

### 3. Install Python dependencies

```bash
pip install mediapipe==0.10.21 opencv-python pyautogui fastapi uvicorn pynput pyobjc-framework-Quartz
```

If you get an OpenCV conflict:

```bash
pip uninstall opencv-python opencv-contrib-python
pip install opencv-python
```

### 4. Install React dependencies

```bash
cd ui
npm install
cd ..
```

### 5. macOS Permissions

The app requires two macOS permissions. You will be prompted automatically on first run, or grant them manually:

- **System Settings → Privacy & Security → Camera** — allow Terminal (or your IDE)
- **System Settings → Privacy & Security → Accessibility** — allow Terminal (or your IDE)

Accessibility permission is required for System Events to send keystrokes to browser processes.

---

## Running the App

### Start the gesture engine

```bash
conda activate gesture-ctrl
python main.py
```

This opens the webcam window and starts the FastAPI server on `http://localhost:8000`.

### Start the config UI (optional)

In a separate terminal:

```bash
cd ui
npm run dev
```

Open `http://localhost:5173` in your browser.

### Usage

1. Open Spotify desktop or YouTube Music in Safari/Chrome
2. Run `python main.py`
3. Hold your hand in front of the webcam
4. Hold a gesture steady for ~0.3 seconds until the progress bar fills
5. The corresponding action fires once — return hand to neutral position to trigger again

---

## Configuration

`config.json` controls gesture mappings and sensitivity settings:

```json
{
    "gestures": {
        "OPEN_PALM": "play_pause",
        "FIST": "mute",
        "POINT_LEFT": "previous_track",
        "POINT_RIGHT": "next_track",
        "THUMBS_UP": "volume_up",
        "PINCH": "volume_down",
        "PEACE": "like_song"
    },
    "settings": {
        "hold_frames": 8,
        "pinch_threshold": 0.28
    }
}
```

`hold_frames` — number of consecutive frames a gesture must be held before firing. Lower = more responsive, higher = fewer accidental triggers. Default: 8 (~0.27s at 30fps).

`pinch_threshold` — normalized distance ratio below which a pinch is detected. Lower = tighter pinch required. Default: 0.28.

---

## Limitations

- **macOS only** — the action dispatcher uses AppleScript and macOS System Events for system-level control. The gesture recognition pipeline itself (all layers up to the dispatcher) is fully cross-platform. Porting to Windows requires replacing `action_dispatcher.py` only.
- **Single hand** — only the first detected hand is tracked. Two-hand gestures are not supported.
- **PEACE gesture** — "like song" has no universal keyboard shortcut across media apps. The gesture fires but the action is a no-op by default; can be remapped via config.json.
- **Lighting sensitive** — MediaPipe Hands performs best in well-lit environments. Poor lighting reduces landmark detection confidence and increases misclassification.
- **Right hand optimised** — the thumb extension heuristic and pointing direction logic are calibrated for a right hand facing the camera. Left hand users may need to adjust thresholds in `gesture_classifier.py`.
- **Browser focus** — next/previous track controls in browser targets (YouTube Music, YouTube) require System Events keyboard injection, which depends on Accessibility permissions being granted.
- **Spotify Web Player** — not supported as a target. Use Spotify desktop app or YouTube Music instead.
- **Browser media targets** — play/pause and track controls require the browser tab to be in focus when using YouTube Music or YouTube. 
  Volume controls work system-wide regardless of focus. Spotify desktop is unaffected — AppleScript controls it directly without focus dependency.

---

## How It Works — The Debounce State Machine

The state machine is the layer that makes the system usable rather than just functional. MediaPipe produces a gesture label every frame (~30/sec). Without debouncing, a one-second gesture would fire its action 30 times.

The state machine solves this with two rules:
1. A gesture must be held for `hold_frames` consecutive frames before it fires (eliminates flickers and accidental triggers)
2. Once fired, the system waits for the hand to return to a neutral `NONE` state before accepting a new gesture (eliminates action spam from holding a gesture)
```
IDLE ──(held N frames)──► TRIGGERED ──(hand resets to NONE)──► IDLE
```

---
