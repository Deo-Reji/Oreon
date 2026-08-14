"""Pose feature pipeline: video -> normalized landmark time series.

This is the shared substrate the rest of the analysis (rep segmentation, form
scoring, and future ML models) is built on. It turns a recorded clip into a
clean, body-size/position-invariant sequence of poses that can be segmented,
scored, and persisted as training data.
"""
import os
import tempfile
import threading
import urllib.request
import cv2
import numpy as np
import mediapipe as mp

MODEL_PATH = os.path.join(os.path.dirname(__file__), "pose_landmarker.task")

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
)


# We only alias the joints the analysis engine actually uses so the scoring
NOSE = 0                          # tip of the nose
L_SHOULDER, R_SHOULDER = 11, 12  
L_ELBOW,    R_ELBOW    = 13, 14  
L_WRIST,    R_WRIST    = 15, 16  
L_HIP,      R_HIP      = 23, 24  
L_KNEE,     R_KNEE     = 25, 26  
L_ANKLE,    R_ANKLE    = 27, 28  

NUM_LANDMARKS = 33

_model_lock = threading.Lock()


def _ensure_model():
    if os.path.exists(MODEL_PATH):
        return

    with _model_lock:
        if os.path.exists(MODEL_PATH):
            return

        tmp = MODEL_PATH + ".tmp"
        try:
            urllib.request.urlretrieve(MODEL_URL, tmp)

            os.replace(tmp, MODEL_PATH)
        except Exception:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise  


def extract_pose_sequence(video_bytes: bytes, sample_every: int = 2) -> dict:
    """Decode the clip and run pose estimation on every `sample_every`-th frame.

    Skipped frames are grabbed but not decoded/inferred, which is the main
    speedup over running the model on all ~1800 frames of a 60s clip.

    Returns:
        landmarks: float array (T, 33, 4) of [x, y, z, visibility] in [0, 1]
        timestamps: float array (T,) in seconds
        fps: source frames per second
    """

    if sample_every < 1:
        raise ValueError(f"sample_every must be >= 1, got {sample_every}")

    _ensure_model()

    # Local aliases to shorten the deeply-nested mediapipe namespace calls below.
    BaseOptions = mp.tasks.BaseOptions                          # configures model path + hardware delegate
    PoseLandmarker = mp.tasks.vision.PoseLandmarker            # the class that loads and runs the model
    PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions  # bundles all config into one object
    VisionRunningMode = mp.tasks.vision.RunningMode            # enum: IMAGE / VIDEO / LIVE_STREAM

    # Build the options object that controls how the landmarker runs.
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),  
        running_mode=VisionRunningMode.VIDEO,  
    )

    # Write the raw bytes to a named temp file so OpenCV can open it by path.
    # OpenCV's VideoCapture cannot decode from a bytes object directly.
    # delete=False is required on Windows: the OS won't allow a second open
    # while the file is still held open by the NamedTemporaryFile handle.
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(video_bytes)   
        tmp_path = f.name      

    frames: list[np.ndarray] = []   # one entry per sampled frame: list of [x,y,z,vis] per landmark
    timestamps: list[float] = []    # wall-clock time in seconds for each sampled frame

    # Declare cap before the try so the finally block can always reference it,
    # even if VideoCapture() itself throws before the assignment completes.
    cap = None
    try:
        # Open the temp file with OpenCV's built-in video decoder.
        cap = cv2.VideoCapture(tmp_path)

        # Read native frame rate from the video header.
        # Falls back to 30fps if the header is missing, zero, NaN or negative
        # (some phone recordings omit or corrupt the fps metadata field). The
        # non-finite cases matter: `nan or 30` keeps the nan (nan is truthy),
        # and the timestamp below would then raise on int(nan), while a negative
        # fps makes timestamps run BACKWARDS and detect_for_video rejects them —
        # either way the request would 500 instead of returning a result.
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or not np.isfinite(fps) or fps <= 0:
            fps = 30.0

        # Counts every frame — including ones we skip — so that t = frame_idx / fps
        # stays accurate even when sample_every > 1.
        frame_idx = 0

        # Load model weights into memory. The context manager unloads them on exit,
        # even if an exception is raised inside the loop.
        with PoseLandmarker.create_from_options(options) as landmarker:
            while cap.isOpened():  # isOpened() returns False if the file was unreadable or is exhausted
                # grab() advances the internal frame buffer WITHOUT decoding pixels.
                # Decoding (colour conversion, decompression) is deferred to retrieve().
                # This is ~10x cheaper than cap.read() for frames we're going to throw away.
                grabbed = cap.grab()

                # grab() returns False when the video stream has no more frames.
                if not grabbed:
                    break

                # Only decode and infer on every Nth frame (default: every other frame).
                # This halves inference cost for 30fps video with no meaningful loss of
                # temporal resolution for exercises which unfold over ~1 second per rep.
                if frame_idx % sample_every == 0:
                    # Decode the already-grabbed frame into a full BGR numpy array (H, W, 3).
                    ret, frame = cap.retrieve()

                    if not ret:
                        break

                    t = frame_idx / fps

                    # MediaPipe expects RGB channel order; OpenCV always returns BGR.
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # Wrap the numpy array in MediaPipe's image container with the correct
                    # colour-space tag so the model interprets channels correctly.
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

                    # Run inference. VIDEO mode requires the timestamp in milliseconds and
                    # it must strictly increase with every call — using frame_idx/fps*1000
                    # guarantees this as long as fps > 0 (guaranteed by the or-30 fallback).
                    result = landmarker.detect_for_video(mp_image, int(t * 1000))

                    # The model returns an empty list when no person is detected in the frame.
                    if result.pose_landmarks:
                        # When multiple people are detected, pick the one with the highest
                        # total landmark visibility score — that person is most fully in frame
                        # and is almost certainly the subject performing the exercise, not a
                        # bystander in the background who may be partially occluded.
                        lm = max(
                            result.pose_landmarks,
                            key=lambda p: sum(pt.visibility for pt in p),
                        )

                        # Flatten each NormalizedLandmark object to [x, y, z, visibility].
                        # All four values are in [0, 1] — x/y/z are image-relative coordinates.
                        frames.append([[p.x, p.y, p.z, p.visibility] for p in lm])

                        # Record this frame's timestamp so callers know the real time gap
                        # between consecutive samples (important for rep-timing calculations).
                        timestamps.append(t)

                # Increment for every frame — skipped or sampled — to keep t = frame_idx/fps correct.
                frame_idx += 1

    finally:
        # Use a nested try/finally so BOTH cleanup steps always run independently.
        # If cap.release() throws, os.unlink still executes; without this nesting,
        # an exception in cap.release() would skip os.unlink and orphan the temp file.
        try:
            if cap is not None:
                cap.release()  # free the decoder buffers and drop the file handle
        finally:
            os.unlink(tmp_path)  # delete the temp file whether or not cap.release() succeeded

    # Stack the accumulated per-frame lists into a single numpy tensor.
    # np.array on an empty list gives the wrong shape, so we branch on whether frames is non-empty.
    landmarks = (
        np.array(frames, dtype=np.float32)                          # (T, 33, 4) when frames exist
        if frames
        else np.empty((0, NUM_LANDMARKS, 4), dtype=np.float32)      # correctly-shaped empty array when no pose was detected at all
    )

    return {
        "landmarks": landmarks,                                      # (T, 33, 4) — raw x, y, z, visibility per landmark per frame
        "timestamps": np.array(timestamps, dtype=np.float32),       # (T,) — elapsed seconds for each sampled frame
        "fps": float(fps),                                           # source frame rate — needed by rep-segmentation to convert frame counts to real time
    }


def normalize_sequence(landmarks: np.ndarray) -> np.ndarray:
    """Make poses invariant to position and body size.

    Each frame is recentered on the hip midpoint and scaled by torso length
    (hip-mid to shoulder-mid). Returns normalized x,y as (T, 33, 2).
    """
    # Validate shape before any indexing so callers get a clear ValueError
    # instead of a cryptic IndexError deep inside the slicing logic.
    # Valid input must be a 3-D array with exactly 33 landmarks and at least x+y channels.
    if landmarks.ndim != 3 or landmarks.shape[1] != NUM_LANDMARKS or landmarks.shape[2] < 2:
        raise ValueError(
            f"landmarks must be shape (T, {NUM_LANDMARKS}, >=2), got {landmarks.shape}"
        )

    # Short-circuit: return a correctly-shaped empty array so downstream code
    # can check shape[0] == 0 without any index-out-of-bounds errors.
    if landmarks.shape[0] == 0:
        return np.empty((0, NUM_LANDMARKS, 2), dtype=np.float32)

    # Drop z and visibility — normalization is 2D only (image-plane coordinates).
    xy = landmarks[:, :, :2]  # (T, 33, 2)

    # Compute the midpoint between the two hips for every frame simultaneously.
    # This point becomes the new origin (0, 0) for every landmark after centering.
    hip_mid = (xy[:, L_HIP] + xy[:, R_HIP]) / 2.0          # (T, 2)

    # Compute the midpoint between the two shoulders for every frame.
    # Combined with hip_mid, this defines the torso segment used as the scale reference.
    shoulder_mid = (xy[:, L_SHOULDER] + xy[:, R_SHOULDER]) / 2.0  # (T, 2)

    # Euclidean length of the hip-mid → shoulder-mid segment in image-space pixels (or [0,1] coords).
    # keepdims=True keeps shape (T, 1) so it can broadcast against (T, 33, 2) in the division below.
    torso = np.linalg.norm(shoulder_mid - hip_mid, axis=1, keepdims=True)  # (T, 1)

    # Clamp to a small positive value to prevent division-by-zero if both joints
    # collapse to the same pixel (can happen during severe model failures / heavy occlusion).
    # NOTE: when torso ≈ 1e-3 the normalised coordinates will be very large —
    # this is intentional; it signals a bad frame rather than silently producing zeros.
    torso = np.clip(torso, 1e-3, None)

    # Subtract hip midpoint from every landmark, broadcasting (T, 2) → (T, 1, 2)
    # via [:, None, :] so numpy aligns it against every landmark in the (T, 33, 2) array.
    centered = xy - hip_mid[:, None, :]

    # Divide by torso length so a tall and a short person doing the same movement
    # produce the same normalised coordinates. Cast back to float32 — numpy upcasts
    # to float64 during the division if the input was float32.
    return (centered / torso[:, None, :]).astype(np.float32)


def joint_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Interior angle at vertex b (degrees) for 2D points a-b-c."""
    # Vectors from the vertex b out to each of the two limb endpoints.
    # The angle between ba and bc is the interior joint angle we want.
    ba, bc = a - b, c - b

    # Cosine rule: cos θ = (ba · bc) / (|ba| * |bc|).
    # +1e-6 prevents division-by-zero when a limb has zero length (two landmarks
    # at the exact same pixel). In that degenerate case cos ≈ 0 and the function
    # returns 90° — a silent fallback, so callers should check landmark visibility
    # before trusting the result.
    cos = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)

    # arccos requires its argument in [-1, 1]. Floating-point arithmetic can push
    # the cosine slightly outside that range (e.g., 1.0000001), which would make
    # arccos return NaN. np.clip guards against that before the conversion.
    return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))


def angle_series(landmarks: np.ndarray, i: int, j: int, k: int) -> np.ndarray:
    """Per-frame joint angle at landmark j, hinged between i and k."""
    # Drop z and visibility — angles are computed in 2D image-plane coordinates only.
    xy = landmarks[:, :, :2]  # (T, 33, 2)

    # Extract the three landmark positions for all T frames at once.
    # Each is (T, 2) — x and y coordinates per frame.
    a, b, c = xy[:, i], xy[:, j], xy[:, k]

    # Vectors from the vertex b to each limb endpoint, across all T frames simultaneously.
    ba = a - b  # (T, 2)
    bc = c - b  # (T, 2)

    # Element-wise dot product per frame: sum over the 2 spatial dimensions, result is (T,).
    dot = (ba * bc).sum(axis=1)

    # Cosine of the interior angle for every frame.
    # +1e-6 prevents division-by-zero for zero-length limb segments (same degenerate
    # case as in joint_angle above — returns ≈ 90° silently).
    cos = dot / (np.linalg.norm(ba, axis=1) * np.linalg.norm(bc, axis=1) + 1e-6)  # (T,)

    # Clamp, take arccos, convert radians → degrees, cast to float32.
    # Fully vectorised — no Python loop over frames.
    return np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))).astype(np.float32)  # (T,)
