"""Pose feature pipeline: video -> normalized landmark time series.

This is the shared substrate the rest of the analysis (rep segmentation, form
scoring, and future ML models) is built on. It turns a recorded clip into a
clean, body-size/position-invariant sequence of poses that can be segmented,
scored, and persisted as training data.
"""
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

# MediaPipe Pose landmark indices we care about.
NOSE = 0
L_SHOULDER, R_SHOULDER = 11, 12
L_ELBOW, R_ELBOW = 13, 14
L_WRIST, R_WRIST = 15, 16
L_HIP, R_HIP = 23, 24
L_KNEE, R_KNEE = 25, 26
L_ANKLE, R_ANKLE = 27, 28

NUM_LANDMARKS = 33


def _ensure_model():
    if not os.path.exists(MODEL_PATH):
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)


def extract_pose_sequence(video_bytes: bytes, sample_every: int = 2) -> dict:
    """Decode the clip and run pose estimation on every `sample_every`-th frame.

    Skipped frames are grabbed but not decoded/inferred, which is the main
    speedup over running the model on all ~1800 frames of a 60s clip.

    Returns:
        landmarks: float array (T, 33, 4) of [x, y, z, visibility] in [0, 1]
        timestamps: float array (T,) in seconds
        fps: source frames per second
    """
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

    frames: list[np.ndarray] = []
    timestamps: list[float] = []

    try:
        cap = cv2.VideoCapture(tmp_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_idx = 0

        with PoseLandmarker.create_from_options(options) as landmarker:
            while cap.isOpened():
                grabbed = cap.grab()  # advance without decoding
                if not grabbed:
                    break
                if frame_idx % sample_every == 0:
                    ret, frame = cap.retrieve()
                    if not ret:
                        break
                    t = frame_idx / fps
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                    result = landmarker.detect_for_video(mp_image, int(t * 1000))
                    if result.pose_landmarks:
                        lm = result.pose_landmarks[0]
                        frames.append(
                            [[p.x, p.y, p.z, p.visibility] for p in lm]
                        )
                        timestamps.append(t)
                frame_idx += 1

        cap.release()
    finally:
        os.unlink(tmp_path)

    landmarks = (
        np.array(frames, dtype=np.float32)
        if frames
        else np.empty((0, NUM_LANDMARKS, 4), dtype=np.float32)
    )
    return {
        "landmarks": landmarks,
        "timestamps": np.array(timestamps, dtype=np.float32),
        "fps": float(fps),
    }


def normalize_sequence(landmarks: np.ndarray) -> np.ndarray:
    """Make poses invariant to position and body size.

    Each frame is recentered on the hip midpoint and scaled by torso length
    (hip-mid to shoulder-mid). Returns normalized x,y as (T, 33, 2).
    """
    if landmarks.shape[0] == 0:
        return np.empty((0, NUM_LANDMARKS, 2), dtype=np.float32)

    xy = landmarks[:, :, :2]  # (T, 33, 2)
    hip_mid = (xy[:, L_HIP] + xy[:, R_HIP]) / 2.0          # (T, 2)
    shoulder_mid = (xy[:, L_SHOULDER] + xy[:, R_SHOULDER]) / 2.0
    torso = np.linalg.norm(shoulder_mid - hip_mid, axis=1, keepdims=True)  # (T, 1)
    torso = np.clip(torso, 1e-3, None)

    centered = xy - hip_mid[:, None, :]
    return (centered / torso[:, None, :]).astype(np.float32)


def joint_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Interior angle at vertex b (degrees) for 2D points a-b-c."""
    ba, bc = a - b, c - b
    cos = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))


def angle_series(landmarks: np.ndarray, i: int, j: int, k: int) -> np.ndarray:
    """Per-frame joint angle at landmark j, hinged between i and k."""
    xy = landmarks[:, :, :2]
    out = np.empty(xy.shape[0], dtype=np.float32)
    for t in range(xy.shape[0]):
        out[t] = joint_angle(xy[t, i], xy[t, j], xy[t, k])
    return out
