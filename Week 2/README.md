
# Week 2: Introduction to MediaPipe with Hands-on Exercises

In this week, we bridge standard image processing with Machine Learning frameworks by diving into Google's MediaPipe ecosystem.

---

## Technical Documentation (Read First)

Skim through these documents to understand the engineering framework behind real-time on-device hand tracking:

1. **Research Paper:** [MediaPipe Hands: On-device Real-time Hand Tracking (Lugaresi et al.)](https://arxiv.org/pdf/2006.10214)
2. **Legacy Documentation:** [MediaPipe Hands Solutions Overview](https://mediapipe.readthedocs.io/en/latest/solutions/hands.html)
3. **Modern Framework:** [Official Google AI Hand Landmarker Guide](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker)

---

## Video Tutorials

Watch these implementation walkthroughs to get familiarized with MediaPipe and learn how to extract and use the 21 hand landmark coordinates:

* Murtaza Hassan: [Hand Tracking 30 FPS using CPU](https://youtu.be/NZde8Xt78Iw?si=hSKwAB6kCDmleMaa)
* Murtaza Hassan: [Gesture Volume Control Preview](https://youtu.be/9iEPzbG-xLE?si=Za0RBr1HKxr6RMQZ)
* Nicholas Renotte: [AI Hand Pose Estimation](https://youtu.be/vQZ4IvB07ec?si=thAOzSnDkbsBgMAu)
* Nicholas Renotte: [AI Body Pose Estimation](https://youtu.be/06TE_U21FK4?si=04tPaovyEsUEDFIU)

---

## Crucial Architectural Note: The API Shift

MediaPipe contains two completely different programmatic APIs. This causes confusion for beginners:

1. **`mediapipe.solutions` (The Legacy API):** Used by Murtaza Hassan and older tutorials. It is simpler but deprecated. It requires **Python 3.11.x + mediapipe 0.10.9**.
2. **`mediapipe.tasks` (The Modern API):** Requires explicit compilation of an external `.task` model file. 

*If you set up Python 3.11 in Week 1, you can safely use the legacy `solutions` API to make following video tutorials much simpler!*