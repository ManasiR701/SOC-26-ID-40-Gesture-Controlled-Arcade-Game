# Week 3: MediaPipe Hand Landmark Detection & Visualization

## Goal

Go from "MediaPipe is installed" to "I can pull out all 21 hand landmark coordinates from a live webcam feed, draw them on screen, and print at least 3 simple gestures in the terminal."

**Checkpoint (due end of Week 3):** Hand landmarks detected live and at least 3 gestures printing in the terminal.

By now (after Week 2) you can already open a webcam feed with OpenCV and draw basic things on it (text, circles, rectangles). This week we hand the *frames* to MediaPipe, get *coordinates* back, and start reasoning about what those coordinates mean.

---

## Part 1: How to Think About Hand Landmarks

Before touching code, get the mental model clear. MediaPipe Hands gives you **21 landmarks per detected hand**. Each landmark is a point with an index (0 to 20) and a position.

- **Landmark 0** is the wrist.
- The thumb runs 1 → 2 → 3 → 4 (tip).
- Index finger: 5 → 6 → 7 → 8 (tip).
- Middle: 9 → 10 → 11 → 12 (tip).
- Ring: 13 → 14 → 15 → 16 (tip).
- Pinky: 17 → 18 → 19 → 20 (tip).

The pattern: each finger has a base knuckle (MCP), two joints, and a tip. The **fingertips are 4, 8, 12, 16, 20** — memorize these, because almost every gesture you'll write in Week 4 involves some comparison with fingertips.

### The Single Most Important Thing to Understand

Each landmark comes back as a *normalized* coordinate. `x` and `y` are floats from 0 to 1 (fraction of frame width/height), **not** pixel values. So to draw on the frame you multiply back up:

```
px = int(x * frame_width)
py = int(y * frame_height)
```

There's also a `z` (relative depth, roughly relative to the wrist) — you can mostly ignore `z` for this project, but know it exists.

### Required Reading

Skim these — don't spend more than 30 minutes total:

1. **Official landmark model page** — look specifically at the hand landmark diagram showing the 21 numbered points: [https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker)
2. **MediaPipe Hands paper** — just the sections on the landmark model (you read this in Week 2; revisit the landmark figure): [https://arxiv.org/pdf/2006.10214](https://arxiv.org/pdf/2006.10214)

> Keep the 21-point diagram open in a tab all week. You will refer to it constantly.

---

## Part 2: The API Situation (Read This Before You Write Any Code)

This trips everyone up, so it's worth being explicit. As your Week 2 doc noted, there are **two** MediaPipe APIs and most YouTube tutorials use the old one:

| API | Description |
|---|---|
| **`mediapipe.solutions` (OLD)** | What Murtaza Hassan and most tutorials use — `mp.solutions.hands.Hands(...)`. Deprecated. Only works on **Python 3.11.x + mediapipe 0.10.9**. |
| **`mediapipe.tasks` (NEW)** | Current API. Uses a downloaded `.task` model file and a `HandLandmarker` object. |

**Recommendation for this project:** If you already followed the Week 1 setup and installed Python 3.11 + mediapipe 0.10.9, just use the **old `solutions` API**. It's simpler, every tutorial matches it, and it's perfectly fine for a learning project. The code below uses the old API as the default and notes the new-API equivalent where relevant.

Only switch to `mediapipe.tasks` if you're on a newer Python/mediapipe version and don't want to downgrade.

---

## Part 3: Tutorials to Work Through

You watched these in Week 2 for the intro — now re-watch with a **landmark-extraction lens**. Don't just copy; pause and identify *where the coordinates come from*.

1. **Murtaza Hassan — "Hand Tracking 30 FPS using CPU":** [https://youtu.be/NZde8Xt78Iw](https://youtu.be/NZde8Xt78Iw)
   - This is the core tutorial for the week. Watch how he wraps detection into a reusable `HandDetector` class with `findHands()` and `findPosition()`. You will essentially build your own version of this. **The `findPosition()` method — which returns a list of `[id, cx, cy]` — is the heart of this week.**

2. **Nicholas Renotte — "AI Hand Pose Estimation":** [https://youtu.be/vQZ4IvB07ec](https://youtu.be/vQZ4IvB07ec)
   - A good second perspective on drawing landmarks and connections. Watch how he uses the drawing utilities to render the skeleton.

Skip the "Gesture Volume Control" video for now (that's Week 4 territory — it covers actual gesture-to-action logic), but it's a great preview if you're curious.

---

## Part 4: Hands-On — Build It in Three Steps

Build incrementally. Don't try to write the whole thing at once. Get each step printing or showing something before moving on.

### Step 1: Detect a Hand and Draw the Skeleton

Feed webcam frames to MediaPipe, get hand landmarks, and draw them.

> **Key gotcha:** OpenCV gives you frames in **BGR**, but MediaPipe expects **RGB**. You must convert with `cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)` before passing to MediaPipe, or detection will fail or behave oddly.

```python
import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,             # one hand is plenty for this project
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5,
)

cap = cv2.VideoCapture(0)

while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)                       # mirror, feels natural
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)     # BGR → RGB for MediaPipe
    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
            )

    cv2.imshow("Hand Tracking", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
```

Run it. You should see the skeleton overlaid on your hand.

If you see nothing: check the BGR → RGB conversion, check your webcam index (try `1` instead of `0`), and check your lighting.

### Step 2: Extract the 21 Coordinates into a Usable List

The skeleton is pretty, but for gestures you need the *numbers*. Pull each landmark into a `[id, cx, cy]` list with pixel coordinates.

```python
def get_landmark_list(frame, hand_landmarks):
    h, w, _ = frame.shape
    lm_list = []
    for idx, lm in enumerate(hand_landmarks.landmark):
        cx, cy = int(lm.x * w), int(lm.y * h)   # normalized → pixels
        lm_list.append([idx, cx, cy])
    return lm_list
```

Inside your loop, after detection:

```python
if results.multi_hand_landmarks:
    for hand_landmarks in results.multi_hand_landmarks:
        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        lm_list = get_landmark_list(frame, hand_landmarks)
        if lm_list:
            print(lm_list[8])   # e.g. index fingertip → [8, x, y]
```

Watch the printed numbers change as you move your index finger. **This is the moment to internalize that a gesture is just arithmetic on these numbers.**

### Step 3: Print at Least 3 Gestures (This Clears the Checkpoint)

Now for the core idea behind every gesture you'll write: **a finger is "up" if its tip is higher on screen than its middle joint.** Remember that `y` grows *downward* in image coordinates, so "higher up" means a *smaller* `y`.

For each finger, compare the tip `y` vs the PIP joint `y` (tip index − 2):

| Finger | Tip | PIP Joint | Up condition |
|---|---|---|---|
| Index | 8 | 6 | `lm[8].y < lm[6].y` |
| Middle | 12 | 10 | `lm[12].y < lm[10].y` |
| Ring | 16 | 14 | `lm[16].y < lm[14].y` |
| Pinky | 20 | 18 | `lm[20].y < lm[18].y` |

The thumb is special — it bends sideways, so compare **x** not `y` (and the direction depends on left/right hand). For now, compare thumb tip x (landmark 4) vs thumb joint x (landmark 3).

```python
def fingers_up(lm_list):
    """Returns a list of 5 ints [thumb, index, middle, ring, pinky], 1 = up."""
    tips = [4, 8, 12, 16, 20]
    fingers = []

    # Thumb: compare x (sideways). Assumes a right hand on a mirrored feed.
    fingers.append(1 if lm_list[4][1] > lm_list[3][1] else 0)

    # Other four fingers: compare y (tip above PIP joint = up)
    for tip in tips[1:]:
        fingers.append(1 if lm_list[tip][2] < lm_list[tip - 2][2] else 0)

    return fingers


def classify_gesture(fingers):
    if fingers == [0, 0, 0, 0, 0]:
        return "FIST"
    if fingers == [1, 1, 1, 1, 1]:
        return "OPEN PALM"
    if fingers == [0, 1, 0, 0, 0]:
        return "POINTING"
    if fingers == [0, 1, 1, 0, 0]:
        return "PEACE"
    if fingers == [1, 0, 0, 0, 0]:
        return "THUMBS UP"
    return "UNKNOWN"
```

Wire it into the loop:

```python
if lm_list:
    fingers = fingers_up(lm_list)
    gesture = classify_gesture(fingers)
    print(fingers, gesture)
    cv2.putText(frame, gesture, (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
```

Make a fist, open your palm, point — watch the terminal print `FIST`, `OPEN PALM`, `POINTING`. **Three gestures printing = Checkpoint cleared.** (Five gestures is even better and gets you ahead for Week 4.)

---

## Part 5: New-API (`mediapipe.tasks`) Note

If you're forced onto the new API, the *logic* in Steps 2 and 3 above is identical — you still get a list of 21 landmarks with normalized `.x`/`.y`. Only the setup differs:

1. Download the model file `hand_landmarker.task` from the official landmarker page (link in Part 1).
2. Create a `HandLandmarker` from `mediapipe.tasks.python.vision`, with `running_mode=VIDEO` (use `detect_for_video(mp_image, timestamp_ms)`).
3. Results come back as `result.hand_landmarks` (a list of hands, each a list of 21 landmarks). Feed those into the **same** `get_landmark_list` / `fingers_up` / `classify_gesture` functions.

The official page linked in Part 1 has a copy-pasteable Python setup snippet for this.

---

## Checkpoint Submission

Submit **one Python script** that:

- Opens the webcam and shows the live feed with the hand skeleton drawn.
- Extracts the 21 landmark coordinates each frame.
- Prints **at least 3 distinct gestures** to the terminal as you make them (and ideally overlays the gesture name on the video).

A 10–15 second screen recording showing the terminal printing gestures as your hand changes shape is a great addition — and a warm-up for the final demo video.

---

## Common Problems & Fixes

| Problem | Fix |
|---|---|
| No skeleton appears | You forgot the BGR → RGB conversion, or your webcam index is wrong (try `cv2.VideoCapture(1)`). |
| Detection is laggy/jittery | Set `max_num_hands=1`, ensure decent lighting, and try lowering `min_tracking_confidence` slightly. |
| `AttributeError: module 'mediapipe' has no attribute 'solutions'` | You're on a newer mediapipe version that dropped the old API — either downgrade to `mediapipe==0.10.9` on Python 3.11, or move to the `tasks` API (Part 5). |
| Gestures flicker between two labels | Detection noise. It's fine for this week; in Week 7 you'll smooth it with a calibration/confidence buffer. |
| Thumb logic is backwards | The thumb x-comparison flips for left vs. right hand and depends on whether you mirrored the frame. Don't over-engineer it now — Week 4 handles handedness properly. |

---

## Looking Ahead to Week 4

This week you hardcoded a few `if fingers == [...]` checks. Next week you'll build this out into a **proper standalone gesture module** (`gestures.py`) with cleaner logic, distance-based gestures (e.g., pinch = thumb tip close to index tip via Euclidean distance), and handedness handling — the file that Week 6 will plug directly into the game.

Keep your `fingers_up` / `classify_gesture` functions tidy; you'll be refactoring them, not throwing them away.