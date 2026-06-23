# Week 3: MediaPipe Hand Landmark Detection & Visualization

**Goal for this week:** Go from "MediaPipe is installed" to "I can pull out all 21 hand landmark coordinates from a live webcam feed, draw them on screen, and print at least 3 simple gestures in the terminal."

**Checkpoint (due end of Week 3):** Hand landmarks detected live and at least 3 gestures printing in the terminal.

By now (after Week 2) you can already open a webcam feed with OpenCV and draw basic things on it (text, circles, rectangles). This week we hand the frames to MediaPipe, get coordinates back, and start reasoning about what those coordinates mean.

---

## Part 1: How to think about hand landmarks

Before touching code, get the mental model clear. MediaPipe Hands gives you **21 landmarks per detected hand**. Each landmark is a point with an index (0 to 20) and a position spatial data coordinate.

* **Landmark 0** is the wrist.
* **The thumb** runs 1 to 2 to 3 to 4 (tip).
* **Index finger:** 5 to 6 to 7 to 8 (tip).
* **Middle finger:** 9 to 10 to 11 to 12 (tip).
* **Ring finger:** 13 to 14 to 15 to 16 (tip).
* **Pinky finger:** 17 to 18 to 19 to 20 (tip).

**The pattern:** Each finger has a base knuckle (MCP), two joints, and a tip. The fingertips are **4, 8, 12, 16, 20**. Memorize these, because almost every gesture you'll write in Week 4 is some geometric comparison involving fingertips.

> ⚠️ **The single most important thing to understand:** Each landmark comes back as a *normalized* coordinate. `x` and `y` are floats from `0.0` to `1.0` (fraction of frame width/height), **not** absolute pixel values. 

To draw on the frame, you must map them back to pixels:
* $\text{px} = \text{int}(x \times \text{frame\_width})$
* $\text{py} = \text{int}(y \times \text{frame\_height})$

There is also a `z` value representing relative depth (roughly relative to the wrist). You can mostly ignore `z` for this project, but know it exists.

###  Required Reading (Skim, max 30 min total):
1. **Official Model Page:** Look specifically at the hand landmark diagram showing the 21 numbered points: [Google AI Hand Landmarker Guide](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker)
2. **MediaPipe Hands Paper:** Revisit the landmark framework figures: [MediaPipe Hands Research Paper](https://arxiv.org/pdf/2006.10214)

*Keep the 21-point diagram open in a tab all week. You will refer to it constantly.*

---

##  Part 2: The API Situation (Read before writing code)

This trips everyone up, so it's worth being explicit. As noted in Week 2, there are **two** completely different MediaPipe APIs, and most older YouTube tutorials use the legacy version:

* **`mediapipe.solutions` (The OLD API):** What Murtaza Hassan and older tutorials use (`mp.solutions.hands.Hands(...)`). It is deprecated but simpler, and only works on **Python 3.11.x + mediapipe 0.10.9**.
* **`mediapipe.tasks` (The NEW API):** The current production ecosystem. It requires downloading an external `.task` model file and using a `HandLandmarker` object framework.

**Project Recommendation:** If you followed the Week 1 setup and installed Python 3.11 + mediapipe 0.10.9, just use the **old `solutions` API**. It's simpler, matches the tutorials perfectly, and is ideal for a learning project. The snippets below provide old-API code as the baseline. 

*Only switch to `mediapipe.tasks` if you are on a newer Python environment and intentionally do not want to downgrade.*

---

## Part 3: Tutorials to Work Through

You watched these in Week 2 for the basic intro—now re-watch them with a specific **landmark-extraction lens**. Don't just copy the code; pause and pinpoint exactly *where the raw coordinates are extracted*.

1. **Murtaza Hassan — "Hand Tracking 30 FPS using CPU":** [Watch Video](https://youtu.be/NZde8Xt78Iw)
   * This is the core tutorial for the week. Watch how he wraps tracking into a reusable `HandDetector` class with `findHands()` and `findPosition()`. You will essentially build your own version of this. **The `findPosition()` method, which returns a list of `[id, cx, cy]`, is the absolute heart of this week.**
2. **Nicholas Renotte — "AI Hand Pose Estimation":** [Watch Video](https://youtu.be/vQZ4IvB07ec)
   * A great second perspective on rendering landmarks and structural connections using default drawing utilities.

*Note: Skip the "Gesture Volume Control" video for now (that is Week 4 territory), but feel free to preview it if you are curious.*

---

## Part 4: Hands-On — Build It in 3 Steps

Build incrementally! Don't try to write the entire system at once. Make sure each step prints or displays something successfully before moving forward.

### Step 1: Detect a Hand and Draw the Skeleton
Feed webcam frames to MediaPipe, extract hand landmarks, and overlay them.

> 💡 **Key Gotcha:** OpenCV captures frames in **BGR** format, but MediaPipe expects **RGB**. You must convert the frame using `cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)` before passing it to the processing pipeline, or detection will fail.

```python
import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,                  # One hand is plenty for this project
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5,
)

cap = cv2.VideoCapture(0)

while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)                      # Mirror frame for natural interaction
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)    # BGR -> RGB for MediaPipe
    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
            )

    cv2.imshow("Hand Tracking Core", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
```

Run it. You should see the skeleton overlaid on your hand. If you see nothing: check the BGR to RGB conversion, check your webcam index (try ⁠ 1 ⁠ instead of ⁠ 0 ⁠), check lighting.

### Step 2: Extract the 21 coordinates into a usable list

The skeleton is pretty, but for gestures you need the numbers. Pull each landmark into a ⁠ `[id, cx, cy]` ⁠ list with pixel coordinates.

```python
def get_landmark_list(frame, hand_landmarks):
    h, w, _ = frame.shape
    lm_list = []
    for idx, lm in enumerate(hand_landmarks.landmark):
        cx, cy = int(lm.x * w), int(lm.y * h)   # normalized -> pixels
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
            print(lm_list[8])   # e.g. index fingertip [8, x, y]
```

Watch the printed numbers change as you move your index finger. *This is the moment to internalize that a gesture is just arithmetic on these numbers.*

### Step 3: Print at least 3 gestures (this clears Checkpoint 2)

Now the core idea behind every gesture you'll write: **a finger is "up" if its tip is higher on screen than its middle joint.** Remember y grows downward in image coordinates, so "higher up" means a smaller y.

For each finger, compare tip y vs the PIP joint y (tip index  2):
* ⁠Index tip = 8, its PIP joint = 6- finger is up if ⁠ `lm[8].y < lm[6].y`
* Middle: 12 vs 10, Ring: 16 vs 14, Pinky: 20 vs 18
* ⁠Thumb is special ; it bends sideways, so compare **x** not y (and the direction depends on left/right hand). For now, compare thumb tip x (4) vs thumb joint x (3).

```python
def fingers_up(lm_list):
    """Returns a list of 5 ints [thumb, index, middle, ring, pinky], 1 = up."""
    tips = [4, 8, 12, 16, 20]
    fingers = []

    # Thumb: compare x (sideways). Assumes a right hand, mirrored feed.
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
This is what we did to correctly classify gestures for both the hands. **Note that the logic for thumb is different for both the hands**. 

```python
if result.hand_landmarks:
            for hand_idx, hand in enumerate(result.hand_landmarks):  #enumerate gives us both the index (0 or 1) and the hand. hand_idx=0 is first hand, hand_idx=1 is second hand if present.

                # tip and pip landmark indices for each finger
                # tips:  thumb=4, index=8, middle=12, ring=16, pinky=20
                # pips:  thumb=3, index=6, middle=10, ring=14, pinky=18
                # PIP = proximal interphalangeal joint = middle knuckle
                # logic: fingertip y < pip y means finger is extended (higher on screen = smaller y)

                handedness_label = result.handedness[hand_idx][0].display_name     #result.handedness is a list of hands, we pick the hand at position hand_idx
                                                                                   #[0] picks the first (and most confident) prediction for that hand
                                                                                   #.display_name gives us the string "left" or "right"

                if (handedness_label == "Left"): 
                    handedness_label = "Right"
                else:
                    handedness_label = "Left"                                      #since the image is mirrored, left hand is detected as right and vice versa. This code ensures that the handedness is displayed correctly
    
                fingers_up = []                                      #True/False for each of the 5 fingers — True means that finger is extended up

                thumb_tip = hand[4]
                thumb_ip  = hand[3]
                # fingers_up.append(thumb_tip.x < thumb_ip.x)         #thumb extends sideways so we compare x not y. True = thumb extended to the left (works for right hand; for left hand this would be reversed but good enough for now)

                #Thumb check depends upon which hand it is
                if handedness_label == "Right":
                    fingers_up.append(thumb_tip.x < thumb_ip.x)     #right thumb extends left
                else:
                    fingers_up.append(thumb_tip.x > thumb_ip.x)     #left thumb extends to right
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
Make a fist, open your palm, point ; watch the terminal print ⁠ `FIST ⁠, ⁠ OPEN PALM ⁠, ⁠ POINTING` ⁠. **Three gestures printing = Checkpoint 2 cleared.** (Five gestures is even better and gets you ahead for Week 4.)

## Part 5: New-API (`mediapipe.tasks`) note

If you're forced onto the new API, the logic in Parts 4.2 and 4.3 is identical; you still get a list of 21 landmarks with normalized ⁠` .x ⁠/⁠ .y` ⁠. Only the setup differs:

1. Download the model file ⁠ `hand_landmarker.task` ⁠ from the official landmarker page (link in Part 1).
2. Create a ⁠ `HandLandmarker` ⁠ from ⁠ `mediapipe.tasks.python.vision` ⁠, with ⁠ `running_mode=VIDEO` ⁠ (use ⁠ `detect_for_video(mp_image, timestamp_ms)` ⁠).
3. ⁠Results come back as ⁠ `result.hand_landmarks` ⁠ (a list of hands, each a list of 21 landmarks). Feed those into the **same** ⁠ `get_landmark_list` ⁠ / ⁠ `fingers_up` ⁠ / ⁠ `classify_gesture` ⁠ functions.

The official page above has a copy-pasteable Python setup snippet for this.

## Checkpoint 2 submission

Submit **one Python script** that:
* Opens the webcam and shows the live feed with the hand skeleton drawn.
* Extracts the 21 landmark coordinates each frame.
* ⁠Prints **at least 3 distinct gestures** to the terminal as you make them (and ideally overlays the gesture name on the video).

A 10-15 second screen recording showing the terminal printing gestures as your hand changes is a great addition (and warm-up for the final demo video).

## Common problems & fixes

* **No skeleton appears:** you forgot the BGR to RGB conversion, or your webcam index is wrong (try ⁠ `cv2.VideoCapture(1)`⁠).
* **Detection is laggy/jittery:** set ⁠ `max_num_hands=1` ⁠, ensure decent lighting, lower ⁠ `min_tracking_confidence` slightly.
* **`⁠AttributeError: module 'mediapipe' has no attribute 'solutions'`⁠:** you're on a new mediapipe version that dropped the old API ; either downgrade to ⁠ `mediapipe==0.10.9` ⁠ on Python 3.11, or move to the ⁠ `tasks` ⁠ API (Part 5).
* **Gestures flicker between two labels:** detection noise. It's fine for this week; in Week 7 you'll smooth it with a calibration/confidence buffer.
* **Thumb logic is backwards:** the thumb x-comparison flips for left vs right hand and depends on whether you mirrored the frame. Don't over-engineer it now ; Week 4 handles handedness properly.

## Looking ahead to Week 4

This week you hardcoded a few ⁠ `if fingers == [...]` ⁠ checks. Next week you'll build this out into a *proper standalone gesture module* (⁠`gestures.py`⁠) with cleaner logic, distance-based gestures (e.g., pinch = thumb tip close to index tip via Euclidean distance), and handedness handling  the file that Week 6 will plug into the game. So keep your ⁠ `fingers_up` ⁠ / ⁠ `classify_gesture` ⁠ functions tidy; you'll be refactoring them, not throwing them away.






