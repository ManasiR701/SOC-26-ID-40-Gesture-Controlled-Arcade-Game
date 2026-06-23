import cv2                                                          #handles webcam and display. OpenCV lets Python talk to your camera. a video is just images shown fast enough to look smooth — OpenCV gives you those images one by one.
import mediapipe as mp                                              #Google's library for real-time ML pipelines. has pre-trained models for hands, face, pose etc. the Hands model detects your hand and returns 21 landmark coordinates. you don't train anything — Google already did that.
import time                                                         #used to calculate FPS (frames per second). FPS = 1 / (time between two consecutive frames)
import urllib.request                                               #built-in Python library to download files from the internet. we need it to download the MediaPipe hand detection model file (.task) which is not bundled with the pip package anymore in newer versions.

# --- NEW MEDIAPIPE API SETUP ---
# older mediapipe used mp.solutions.hands (simple but deprecated)
# newer mediapipe (0.10+) uses a "tasks" API where you explicitly load a model file
# these lines are just giving shorter names to deeply nested classes so we don't have to type the full path every time

BaseOptions = mp.tasks.BaseOptions                                  #BaseOptions is a config object that tells mediapipe WHERE to find the model file. think of it as "here is the brain I want you to use"
HandLandmarker = mp.tasks.vision.HandLandmarker                    #HandLandmarker is the actual detector class. you give it a frame, it gives you back landmark coordinates.
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions      #HandLandmarkerOptions is a config object that bundles all your settings together — how many hands, running mode, confidence thresholds etc.
VisionRunningMode = mp.tasks.vision.RunningMode                    #RunningMode tells mediapipe how you're feeding it images. IMAGE = one photo at a time. VIDEO = continuous stream with timestamps. LIVE_STREAM = async callback mode. we use IMAGE here because it's simplest for a while loop.

# --- DOWNLOAD MODEL FILE ---
# mediapipe's new API requires a .task file (a packaged ML model)
# this downloads it from Google's servers the first time you run the script
# after that it's saved locally and this line is instant (urllib checks if it exists)
urllib.request.urlretrieve(
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
    "hand_landmarker.task"                                          #saves the file as hand_landmarker.task in the same folder as this script. float16 means the model weights are stored in 16-bit floating point — smaller file, fast enough, slightly less precise than float32 but unnoticeable for hand tracking
)

# --- CONFIGURE THE DETECTOR ---
options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="hand_landmarker.task"),  #tells mediapipe to load the model from the file we just downloaded
    running_mode=VisionRunningMode.IMAGE,                           #IMAGE mode = we manually call detect() on each frame ourselves inside the loop. simplest mode. VIDEO mode would require timestamps, LIVE_STREAM would require async callbacks — unnecessary complexity for now.
    num_hands=2                                                     #maximum number of hands to detect per frame. more hands = slightly more compute per frame.
)

cap = cv2.VideoCapture(0)                                           #opens your webcam. 0 = first/default camera. if you have multiple cameras, try 1 or 2. returns a VideoCapture object that you can read frames from.
prev_time = 0                                                       #stores timestamp of the previous frame. used to compute FPS. initialized to 0, gets updated every loop iteration.

# --- MAIN LOOP ---
# we wrap everything inside "with HandLandmarker.create_from_options(options) as landmarker"
# this is a context manager — it initializes the model when entering the block and automatically
# cleans up / releases model resources when exiting. equivalent to try/finally under the hood.

with HandLandmarker.create_from_options(options) as landmarker:
    while True:                                                     #infinite loop — each iteration processes exactly one frame from the webcam
        success, frame = cap.read()                                 #reads one frame. success = True/False depending on whether the camera is working. frame = the image as a NumPy array of shape (height, width, 3) where 3 = BGR channels (Blue, Green, Red — OpenCV's default order)
        if not success:                                             #if the camera failed or disconnected, stop the loop
            print("Camera not found")
            break

        frame = cv2.flip(frame, 1)                                  #flips the frame horizontally. 1 = horizontal flip. without this, the feed is mirrored — moving your right hand moves the on-screen hand left. flipping makes it feel like a mirror, which is intuitive.
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)          #converts BGR → RGB. OpenCV reads images in BGR by default. MediaPipe expects RGB. same visual image, just different channel order in memory. if you skip this, colors get misinterpreted and detection breaks.

        # wrap the numpy array in a mediapipe Image object
        # mediapipe's new API doesn't accept raw numpy arrays — it needs its own Image wrapper
        # mp.ImageFormat.SRGB tells it "this is a standard RGB image" (as opposed to grayscale, float, etc.)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        result = landmarker.detect(mp_image)                        #runs the hand detection model on this frame. returns a HandLandmarkerResult object containing: result.hand_landmarks (list of hands, each hand is a list of 21 landmarks), result.handedness (left/right classification), result.hand_world_landmarks (3D coordinates in meters)

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

                for tip_id, pip_id in [(8,6), (12,10), (16,14), (20,18)]:
                    fingers_up.append(hand[tip_id].y < hand[pip_id].y) #for each finger: True if tip is above its middle knuckle = finger is up

                count = sum(fingers_up)                              #number of fingers up. True=1 False=0 so sum = count of extended fingers

                if count == 0:
                    gesture = "FIST"
                elif count == 5:
                    gesture = "OPEN PALM"
                elif fingers_up == [False, True, False, False, False]:
                    gesture = "POINTING"
                elif fingers_up == [False, True, True, False, False]:
                    gesture = "PEACE"
                else:
                    gesture = f"{count} FINGERS"

                # position the text differently for each hand so they don't overlap
                # hand_idx=0 → y=70, hand_idx=1 → y=120
                text_y = 70 + hand_idx * 50                         #50px gap between hand labels. first hand at y=70, second hand at y=120.

                
                
                
                cv2.putText(frame, f"{handedness_label}: {gesture}", (10, text_y),  #"Hand left: PEACE" or "Hand right: FIST" etc. 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        # --- DRAW LANDMARKS ---
        if result.hand_landmarks:                                   #result.hand_landmarks is a list. if no hand is detected it's empty [] which is falsy. if at least one hand is found, this is truthy and we enter the block.
            for hand in result.hand_landmarks:                      #loop over each detected hand. if two hands are visible, this runs twice. each "hand" is a list of 21 NormalizedLandmark objects.
                for lm in hand:                                     #loop over all 21 landmarks of this hand. lm.x and lm.y are normalized (0 to 1, relative to frame width/height). lm.z is depth (negative = closer to camera) but we ignore it for 2D drawing.
                    h, w, _ = frame.shape                           #frame.shape returns (height, width, channels). we unpack height and width. the _ discards channels (3) since we don't need it here.
                    cx, cy = int(lm.x * w), int(lm.y * h)           #convert normalized coordinates to pixel coordinates. lm.x=0.5 on a 640px wide frame → cx=320. int() because pixel indices must be whole numbers.
                    cv2.circle(frame, (cx, cy), 7, (0, 255, 0), -1) #draws a filled circle at each landmark. arguments: image, center (x,y), radius=5px, color=(0,255,0) which is green in BGR, thickness=-1 means filled (positive thickness = just the outline)

                #----Connecting the green landmarks with lines----#
                HAND_CONNECTIONS = [
                    (0, 1), (1, 2), (2, 3), (3, 4),                 # Thumb
                    (0, 5), (5, 6), (6, 7), (7, 8),                 # Index Finger
                    (0, 9), (9, 10), (10, 11), (11, 12),            # Middle Finger
                    (0, 13), (13, 14), (14, 15), (15, 16),          # Ring Finger
                    (0, 17), (17, 18), (18, 19), (19, 20),          # Pinky
                    (5, 9), (9, 13), (13, 17)                       # Palm connections
                ]

                h, w, _ = frame.shape
                for start, end in HAND_CONNECTIONS:
                    x1, y1 = int(hand[start].x * w), int(hand[start].y * h)   # pixel coordinates of landmark 0 (0 means the first landmark in (a, b))
                    x2, y2 = int(hand[end].x * w), int(hand[end].y * h)       # pixel coordinates of landmark 1 (here landmark 1 is b)
                    cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)   # drawing a line between (x1, y1) and (x2, y2)
        # --- FPS CALCULATION ---
        curr_time = time.time()                                     #current timestamp in seconds (float). e.g. 1716123456.789
        fps = 1 / (curr_time - prev_time)                           #time between frames = curr - prev. FPS = 1 / that. if a frame takes 0.033 seconds, FPS = ~30.
        prev_time = curr_time                                       #update prev_time for the next iteration

        cv2.putText(frame, f"FPS: {int(fps)}", (10, 30),            #draws text on the frame. arguments: image, text string, position (x=10 y=30 from top-left), font, font scale, color (green), thickness
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Hand Tracking", frame)                          #opens a window named "Hand Tracking" and displays the current frame. without this line you'd process frames but never see anything. this must be called every loop iteration to refresh the display.

        if cv2.waitKey(1) & 0xFF == ord('q'):                       #waitKey(1) waits 1ms for a keypress — required for OpenCV to actually render the window. returns the key code. & 0xFF masks to last 8 bits for cross-platform compatibility. ord('q') = ASCII code 113. if you press q, break the loop.
            break

cap.release()                                                       #releases the webcam so other programs can use it. without this the camera stays locked even after the script ends.
cv2.destroyAllWindows()                                             #closes all OpenCV windows. without this the window might hang open after the script exits.