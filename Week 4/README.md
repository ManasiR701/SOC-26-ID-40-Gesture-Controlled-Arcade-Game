# Week 4: Gesture Logic & Building the Gesture Module

## Goal

Turn last week's hardcoded `if fingers == [...]` checks into a clean, standalone `gestures.py` module that classifies at least **5 gestures** using landmark coordinate geometry — the file Week 6 will import and wire into the game.

**Where this sits:** Week 3 got you landmarks live and 3 gestures printing. This week is the "real" gesture engineering: better logic, distance-based gestures, handedness handling, and packaging it as a reusable module. By the end of the week you should have 5 solid gestures. *(Checkpoint 3, end of Week 5, formally requires the 5-gesture file + HUD + game running; finishing the gesture file this week puts you exactly on track.)*

---

## Part 1: The Mental Shift — Gestures Are Geometry

Last week a gesture was a hardcoded list match. It breaks the moment a finger is halfway up or the hand tilts. This week you graduate to reasoning about coordinates so gestures are robust.

There are **three tools** you'll use for essentially every gesture:

| Tool | What it does |
|---|---|
| **Finger up/down** | Tip vs. joint comparison (you already have this from Week 3) |
| **Distance between two landmarks** | Euclidean distance — unlocks pinch, "OK" sign, and any "are these two points close?" gesture |
| **Relative position** | Is the thumb to the left/right of the index? Is the hand tilted? Used for direction gestures and handedness |

Master these three and you can express almost any static gesture.

---

## Part 2: Distance — The Key New Tool

The distance between two landmarks is just the Pythagorean theorem on their pixel coordinates:

```python
import math

def distance(lm_list, p1, p2):
    """Euclidean pixel distance between two landmark indices."""
    x1, y1 = lm_list[p1][1], lm_list[p1][2]
    x2, y2 = lm_list[p2][1], lm_list[p2][2]
    return math.hypot(x2 - x1, y2 - y1)
```

### ⚠️ Critical Gotcha: Normalize Your Distances

Raw pixel distance changes with how close your hand is to the camera. A pinch at arm's length might be 30px; the same pinch up close might be 90px. So a hardcoded threshold like `distance < 40` will behave differently depending on hand position.

**The fix is normalization:** divide by a reference length that scales the same way, so the ratio stays roughly constant regardless of hand distance. A good reference is the hand's overall size — wrist (0) to middle-finger MCP (9):

```python
def normalized_distance(lm_list, p1, p2):
    """Distance between p1 and p2 as a ratio of hand size (camera-distance invariant)."""
    ref = distance(lm_list, 0, 9)   # wrist to middle knuckle = hand scale
    if ref == 0:
        return 0
    return distance(lm_list, p1, p2) / ref
```

Now `"pinch"` is `normalized_distance(lm, 4, 8) < 0.3` and it works whether your hand is near or far.

> **This single idea — normalize by hand size — is the most important concept of the whole week.**

This is also exactly what Murtaza's "Gesture Volume Control" video demonstrates (thumb-to-index distance controlling volume) — worth rewatching now that it's directly relevant: [https://youtu.be/9iEPzbG-xLE](https://youtu.be/9iEPzbG-xLE)

---

## Part 3: Handedness — Getting the Thumb Right

Last week the thumb logic was a hack that assumed a right hand. Now do it properly. The old solutions API gives you handedness for free:

```python
results = hands.process(rgb)
if results.multi_handedness:
    label = results.multi_handedness[0].classification[0].label  # "Left" or "Right"
```

> **Watch out:** Because you flipped the frame (`cv2.flip`) for a mirror effect, MediaPipe's "Left"/"Right" is reported relative to the unflipped image — so it will feel reversed to the user. Decide on one convention and stick to it.

For the thumb, the up-check flips based on handedness:

```python
def thumb_up(lm_list, hand_label):
    if hand_label == "Right":
        return lm_list[4][1] > lm_list[3][1]   # tip x to the right of joint
    else:
        return lm_list[4][1] < lm_list[3][1]
```

For a learning project it's fine to lock to one hand (tell users "use your right hand") and skip this — but knowing *why* it flips matters.

---

## Part 4: Build `gestures.py` — The Actual Module

This is the deliverable. Structure it as a self-contained file that exposes one clean function: give it a landmark list, get back a gesture name. Week 6 will call exactly this.

```python
# gestures.py
import math


def _distance(lm_list, p1, p2):
    x1, y1 = lm_list[p1][1], lm_list[p1][2]
    x2, y2 = lm_list[p2][1], lm_list[p2][2]
    return math.hypot(x2 - x1, y2 - y1)


def _hand_scale(lm_list):
    ref = _distance(lm_list, 0, 9)
    return ref if ref != 0 else 1


def fingers_up(lm_list, hand_label="Right"):
    """Returns [thumb, index, middle, ring, pinky], 1 = up."""
    fingers = []

    # Thumb compares x; direction depends on handedness
    if hand_label == "Right":
        fingers.append(1 if lm_list[4][1] > lm_list[3][1] else 0)
    else:
        fingers.append(1 if lm_list[4][1] < lm_list[3][1] else 0)

    # Other four compare y (tip above PIP joint = up)
    for tip in [8, 12, 16, 20]:
        fingers.append(1 if lm_list[tip][2] < lm_list[tip - 2][2] else 0)

    return fingers


def classify(lm_list, hand_label="Right"):
    """Main entry point. Returns a gesture name string."""
    if not lm_list or len(lm_list) < 21:
        return "NONE"

    fingers = fingers_up(lm_list, hand_label)
    scale = _hand_scale(lm_list)

    # Distance-based gestures take priority (more specific)
    pinch = _distance(lm_list, 4, 8) / scale       # thumb tip to index tip
    if pinch < 0.3 and fingers[2] and fingers[3] and fingers[4]:
        return "OK"                                 # thumb+index circle, others up

    # Finger-count gestures
    if fingers == [0, 0, 0, 0, 0]:
        return "FIST"
    if fingers == [1, 1, 1, 1, 1]:
        return "OPEN_PALM"
    if fingers == [0, 1, 0, 0, 0]:
        return "POINT"
    if fingers == [0, 1, 1, 0, 0]:
        return "PEACE"
    if fingers == [1, 0, 0, 0, 0]:
        return "THUMB"

    return "UNKNOWN"
```

### Design Choices

- **One public function, `classify()`** — clean interface for Week 6. Everything else is a `_helper`.
- **Distance gestures checked first**, because they're more specific than finger-counts (an "OK" sign would otherwise be misread as some finger combo).
- **Guards (`len(lm_list) < 21`)** so it never crashes when no hand is present; returns `"NONE"`.
- **Gesture names are `UPPER_SNAKE` strings**, easy to map to game commands later.

---

## Part 5: Test the Module Standalone

Write a small `test_gestures.py` that imports your module and runs it on the webcam. This is how you verify correctness before integration:

```python
import cv2
import mediapipe as mp
import gestures   # your module

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

cap = cv2.VideoCapture(0)

while True:
    ok, frame = cap.read()
    if not ok:
        break
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    gesture = "NONE"
    if results.multi_hand_landmarks:
        hand = results.multi_hand_landmarks[0]
        label = "Right"
        if results.multi_handedness:
            label = results.multi_handedness[0].classification[0].label

        h, w, _ = frame.shape
        lm_list = [[i, int(lm.x * w), int(lm.y * h)]
                   for i, lm in enumerate(hand.landmark)]

        gesture = gestures.classify(lm_list, label)
        mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

    cv2.putText(frame, gesture, (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 2)
    cv2.imshow("Gesture Test", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
```

Run through all 5 gestures and confirm each reads correctly and stably. The clean split — `gestures.py` (logic) vs `test_gestures.py` (the webcam loop) — is exactly the separation you need for Week 6, where the game replaces the test loop but imports the same `gestures.py` unchanged.

---

## Part 6: Tuning Your Thresholds

The `0.3` pinch threshold and the up/down comparisons are starting points, not gospel. Spend time tuning:

- Print the raw normalized distances while making gestures, and pick thresholds in the gap between "clearly pinched" and "clearly open."
- If a gesture is too eager (fires when it shouldn't), tighten the threshold. Too reluctant — loosen it.
- Test under the lighting and background you'll actually demo in.
- Note which gestures get confused with each other (e.g. `POINT` vs `PEACE` when the middle finger is lazy). Your eventual game commands should use gestures that are visually distinct so misclassification is rare — keep this in mind when you choose which gesture maps to which game action in Week 6.

---

## End-of-Week Deliverable

| File | Description |
|---|---|
| `gestures.py` | Standalone module exposing `classify(lm_list, hand_label)`, recognizing at least 5 distinct gestures, using normalized distances so it works at varying hand-to-camera distances |
| `test_gestures.py` | A webcam harness proving all 5 gestures work live |

Thresholds should be tuned and gestures reliably distinguishable.

> This is the engine of the whole project. Get it solid and stable now — Weeks 5–7 (game code, integration, HUD, polish) all assume `gestures.py` "just works" and import it without changes.

---

## Common Problems & Fixes

| Problem | Fix |
|---|---|
| Pinch threshold works up close but not far away (or vice versa) | You're using raw pixel distance — switch to `normalized_distance` / divide by hand scale. This is the #1 issue this week. |
| Thumb reads wrong | Handedness flip (Part 3), made worse by the mirror flip. Lock to one hand if you're stuck. |
| Two gestures keep getting confused | Check ordering in `classify()` (specific/distance gestures must be checked before generic finger-counts), and consider whether the two gestures are just too visually similar. |
| Gesture flickers rapidly between frames | Detection noise; fine for now. Week 7's smoothing pass adds a "hold for N frames" buffer to stabilize it. Don't solve it here. |
| `gestures.py` crashes when hand leaves frame | Missing the `len(lm_list) < 21` guard — always return `"NONE"` on no/partial hand. |

---

## Looking Ahead to Week 5

Next week you switch context entirely: read and understand the provided Pygame game code — its main loop, how it reads input (keyboard events), and where a command enters the game. You'll be hunting for the exact spot where Week 6 swaps "keypress" for "gesture from `classify()`."

As you finish this week, jot down what 5 commands the game will need (e.g. up/down/left/right/pause) — that tells you which 5 gestures actually matter for mapping.