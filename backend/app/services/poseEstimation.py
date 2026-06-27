import os
import tempfile
import urllib.request
import cv2
import numpy as np
import mediapipe as mp

MODEL_PATH = os.path.join(os.path.dirname(__file__), "pose_landmarker.task")
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
)


def _ensure_model():
    if not os.path.exists(MODEL_PATH):
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)


def _angle(a, b, c) -> float:
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba, bc = a - b, c - b
    cos = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))


def _get_angle(landmarks, exercise: str) -> float | None:
    # landmark indices: 23=left_hip, 25=left_knee, 27=left_ankle
    #                   11=left_shoulder, 13=left_elbow, 15=left_wrist
    if exercise == "squat":
        hip   = [landmarks[23].x, landmarks[23].y]
        knee  = [landmarks[25].x, landmarks[25].y]
        ankle = [landmarks[27].x, landmarks[27].y]
        return _angle(hip, knee, ankle)
    elif exercise == "curl":
        shoulder = [landmarks[11].x, landmarks[11].y]
        elbow    = [landmarks[13].x, landmarks[13].y]
        wrist    = [landmarks[15].x, landmarks[15].y]
        return _angle(shoulder, elbow, wrist)
    return None


def _count_rep(angle: float, stage: str | None, exercise: str) -> tuple[int, str | None]:
    reps = 0
    if exercise == "squat":
        if stage is None and angle > 160:
            stage = "up"
        elif angle < 90 and stage == "up":
            stage = "down"
        elif angle > 160 and stage == "down":
            stage = "up"
            reps = 1
    elif exercise == "curl":
        if stage is None and angle > 150:
            stage = "down"
        elif angle < 30 and stage == "down":
            stage = "up"
        elif angle > 150 and stage == "up":
            stage = "down"
            reps = 1
    return reps, stage


def analyze_video(video_bytes: bytes, exercise: str = "squat") -> dict:
    _ensure_model()

    BaseOptions = mp.tasks.BaseOptions
    PoseLandmarker = mp.tasks.vision.PoseLandmarker
    PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=VisionRunningMode.VIDEO,
    )

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(video_bytes)
        tmp_path = f.name

    try:
        cap = cv2.VideoCapture(tmp_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        reps = 0
        stage = None
        angles = []
        frame_idx = 0

        with PoseLandmarker.create_from_options(options) as landmarker:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                timestamp_ms = int((frame_idx / fps) * 1000)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                result = landmarker.detect_for_video(mp_image, timestamp_ms)
                frame_idx += 1

                if not result.pose_landmarks:
                    continue

                angle = _get_angle(result.pose_landmarks[0], exercise)
                if angle is None:
                    continue

                angles.append(angle)
                delta, stage = _count_rep(angle, stage, exercise)
                reps += delta

        cap.release()
        form_score = int(np.mean(angles)) if angles else 0
        return {"reps": reps, "form_score": form_score, "frames_analyzed": len(angles)}
    finally:
        os.unlink(tmp_path)
