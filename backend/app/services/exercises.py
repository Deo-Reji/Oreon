"""Per-exercise rep segmentation, metrics, and rule-based form scoring.

Consumes the landmark time series from posePipeline and produces per-rep ROM,
tempo, detected faults, and a real 0-100 form score. The fault rules here are
the labeling target the ML fault detector will eventually learn to replace.
"""
import numpy as np
from collections import Counter
from app.services import posePipeline as pp


def _trunk_lean_series(landmarks: np.ndarray) -> np.ndarray:
    """Angle of the torso from vertical, in degrees, per frame."""
    xy = landmarks[:, :, :2]
    hip_mid = (xy[:, pp.L_HIP] + xy[:, pp.R_HIP]) / 2.0
    shoulder_mid = (xy[:, pp.L_SHOULDER] + xy[:, pp.R_SHOULDER]) / 2.0
    vec = shoulder_mid - hip_mid          # points up the torso (image y is down)
    # Angle from the vertical axis (0, -1).
    ang = np.degrees(np.arctan2(np.abs(vec[:, 0]), -vec[:, 1]))
    return ang.astype(np.float32)


def _smooth(a: np.ndarray, k: int = 5) -> np.ndarray:
    if a.shape[0] < k or k < 2:
        return a
    kernel = np.ones(k) / k
    return np.convolve(a, kernel, mode="same").astype(np.float32)


def _segment_reps(angle: np.ndarray, high: float, low: float):
    """Yield (start, bottom, end) frame indices for each full high->low->high cycle."""
    reps = []
    reached_top = False
    top_start = None
    min_val = np.inf
    min_idx = None
    for t, a in enumerate(angle):
        if not reached_top:
            if a >= high:
                reached_top = True
                top_start = t
                min_val = np.inf
            continue
        if a < min_val:
            min_val = a
            min_idx = t
        if min_val <= low and a >= high:
            reps.append((top_start, min_idx, t))
            top_start = t
            min_val = np.inf
    return reps


# --- Form rule sets (return a list of fault labels for one rep) ---

def _squat_faults(landmarks, sl, depth, top_angle):
    faults = []
    if depth > 100:
        faults.append("Not enough depth")
    lean = _trunk_lean_series(landmarks[sl])
    if lean.size and lean.max() > 50:
        faults.append("Excessive forward lean")
    if top_angle < 160:
        faults.append("Incomplete lockout")
    return faults


def _curl_faults(landmarks, sl, depth, top_angle):
    faults = []
    if top_angle < 150:
        faults.append("Incomplete extension")
    if depth > 55:
        faults.append("Incomplete curl")
    # Swing: how much the shoulder drifts horizontally during the rep.
    xy = landmarks[sl, :, :2]
    if xy.shape[0]:
        sx = (xy[:, pp.L_SHOULDER, 0] + xy[:, pp.R_SHOULDER, 0]) / 2.0
        if sx.max() - sx.min() > 0.08:
            faults.append("Swinging / using momentum")
    return faults


def _bench_faults(landmarks, sl, depth, top_angle):
    # NOTE: bench is done lying down; pose-only fault detection is limited
    # (bar path / elbow flare need a clean side view or bar tracking).
    faults = []
    if top_angle < 160:
        faults.append("Incomplete lockout")
    if depth > 100:
        faults.append("Partial range (bar not to chest)")
    return faults


# joints: angle hinge triple (i, j, k); high/low: rep thresholds on that angle.
EXERCISES = {
    "squat": {"joints": (pp.L_HIP, pp.L_KNEE, pp.L_ANKLE), "high": 160, "low": 100, "faults": _squat_faults},
    "curl": {"joints": (pp.L_SHOULDER, pp.L_ELBOW, pp.L_WRIST), "high": 150, "low": 60, "faults": _curl_faults},
    "bench": {"joints": (pp.L_SHOULDER, pp.L_ELBOW, pp.L_WRIST), "high": 160, "low": 95, "faults": _bench_faults},
}


def _resolve(exercise: str) -> str:
    """Map a free-form exercise name from the app to an analyzer key.

    e.g. "Bench Press" -> "bench", "Hammer Curl" -> "curl", "Squat" -> "squat".
    """
    name = (exercise or "").lower()
    if "bench" in name:
        return "bench"
    if "curl" in name:
        return "curl"
    if "squat" in name:
        return "squat"
    return "squat"


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def analyze_exercise(exercise: str, landmarks: np.ndarray, timestamps: np.ndarray) -> dict:
    cfg = EXERCISES[_resolve(exercise)]
    i, j, k = cfg["joints"]

    if landmarks.shape[0] < 3:
        return {"reps": 0, "form_score": 0, "grade": "F", "rep_details": [], "improvements": []}

    angle = _smooth(pp.angle_series(landmarks, i, j, k))
    segments = _segment_reps(angle, cfg["high"], cfg["low"])

    rep_details = []
    all_faults = []
    for n, (start, bottom, end) in enumerate(segments, 1):
        sl = slice(start, end + 1)
        window = angle[sl]
        depth = float(window.min())
        top_angle = float(window.max())
        rom = round(top_angle - depth, 1)
        duration = round(float(timestamps[end] - timestamps[start]), 2)
        faults = cfg["faults"](landmarks, sl, depth, top_angle)
        all_faults.extend(faults)
        rep_score = max(0, 100 - 20 * len(faults))
        rep_details.append({
            "rep": n,
            "rom": rom,
            "depth_angle": round(depth, 1),
            "top_angle": round(top_angle, 1),
            "duration_s": duration,
            "faults": faults,
            "score": rep_score,
        })

    reps = len(rep_details)
    form_score = int(round(np.mean([r["score"] for r in rep_details]))) if reps else 0

    # Most common faults become the "things to improve" list.
    counts = Counter(all_faults)
    improvements = [f"{label} ({n}/{reps})" for label, n in counts.most_common(3)]

    return {
        "reps": reps,
        "form_score": form_score,
        "grade": _grade(form_score),
        "rep_details": rep_details,
        "improvements": improvements,
    }
