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


def _shoulder_drift(landmarks: np.ndarray) -> float:
    """Horizontal travel of the shoulder midpoint (proxy for swinging)."""
    xy = landmarks[:, :, :2]
    if xy.shape[0] == 0:
        return 0.0
    sx = (xy[:, pp.L_SHOULDER, 0] + xy[:, pp.R_SHOULDER, 0]) / 2.0
    return float(sx.max() - sx.min())


def _median_filter(a: np.ndarray, k: int = 5) -> np.ndarray:
    """Kill single-frame tracking glitches before smoothing."""
    if a.shape[0] < k or k < 2:
        return a
    pad = k // 2
    ap = np.pad(a, pad, mode="edge")
    out = np.empty_like(a)
    for i in range(a.shape[0]):
        out[i] = np.median(ap[i:i + k])
    return out


def _smooth(a: np.ndarray, k: int = 5) -> np.ndarray:
    if a.shape[0] < k or k < 2:
        return a
    kernel = np.ones(k) / k
    return np.convolve(a, kernel, mode="same").astype(np.float32)


def _clean_signal(angle: np.ndarray) -> np.ndarray:
    """De-glitch then smooth the rep-driving angle signal."""
    return _smooth(_median_filter(angle))


def _segment_reps(angle: np.ndarray, min_range: float = 25.0):
    """Adaptive rep segmentation: count an oscillation relative to THIS clip's
    own range, so partial/short reps still register (a fixed high/low threshold
    misses them entirely). A rep = cross above the upper band, dip below the
    lower band, return above the upper band.

    Returns (start, bottom, end) frame indices per rep.
    """
    n = angle.shape[0]
    if n < 5:
        return []

    lo = float(np.percentile(angle, 5))   # robust "bottom" reference
    hi = float(np.percentile(angle, 95))  # robust "top" reference
    rng = hi - lo
    if rng < min_range:                   # barely any movement -> no reps
        return []

    mid = (lo + hi) / 2.0
    margin = 0.15 * rng                   # hysteresis to avoid double-counts
    upper, lower = mid + margin, mid - margin

    reps = []
    state = "init"
    # Latest frame at/above the top band. A rep starts at the descent, not when
    # the lifter first reached the top -- this drops the walk-in / un-rack /
    # setup time that was corrupting rep 1 (long duration, inflated drift).
    top_idx = None
    min_val = np.inf
    min_idx = None
    for t, a in enumerate(angle):
        if state == "init":
            if a >= upper:
                state = "top"
                top_idx = t
        elif state == "top":
            if a >= upper:
                top_idx = t          # keep advancing until the descent begins
            elif a <= lower:
                state = "bottom"
                min_val = a
                min_idx = t
        elif state == "bottom":
            if a < min_val:
                min_val = a
                min_idx = t
            if a >= upper:
                reps.append((top_idx, min_idx, t))
                state = "top"
                top_idx = t
                min_val = np.inf
    return reps


# --- Form rule sets (take a per-rep metrics dict, return fault labels) ---

def _squat_faults(m):
    faults = []
    if m["depth"] > 100:
        faults.append("Not enough depth")
    if m["lean"] > 50:
        faults.append("Excessive forward lean")
    if m["top"] < 160:
        faults.append("Incomplete lockout")
    return faults


def _curl_faults(m):
    faults = []
    if m["top"] < 150:
        faults.append("Incomplete extension")
    if m["depth"] > 55:
        faults.append("Incomplete curl")
    if m["drift"] > 0.08:
        faults.append("Swinging / using momentum")
    return faults


def _bench_faults(m):
    # NOTE: bench is done lying down; pose-only fault detection is limited
    # (bar path / elbow flare need a clean side view or bar tracking).
    faults = []
    if m["top"] < 160:
        faults.append("Incomplete lockout")
    if m["depth"] > 100:
        faults.append("Partial range (bar not to chest)")
    return faults


# joints: angle hinge triple (i, j, k) for the rep-driving angle.
EXERCISES = {
    "squat": {"joints": (pp.L_HIP, pp.L_KNEE, pp.L_ANKLE), "faults": _squat_faults},
    "curl": {"joints": (pp.L_SHOULDER, pp.L_ELBOW, pp.L_WRIST), "faults": _curl_faults},
    "bench": {"joints": (pp.L_SHOULDER, pp.L_ELBOW, pp.L_WRIST), "faults": _bench_faults},
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


# Population-default "full range" depth target per exercise (provisional; to be
# refined with multi-person data). Used only for the relative/self layer below.
FULL_ROM_TARGET = {"squat": 95.0, "curl": 60.0, "bench": 95.0}


def _self_calibration(key: str, rep_details: list) -> dict:
    """Relative layer ON TOP OF the absolute fault rules.

    Judges each rep against the lifter's OWN best rep this set (their demonstrated
    capacity), and separates 'can't' (a consistent range limit -> mobility/strength)
    from 'won't' (some reps cut short vs their best -> consistency/fatigue). The
    absolute rules still decide correctness; this only adds context.
    """
    depths = [r["depth_angle"] for r in rep_details]
    if not depths:
        return {}

    # Robust capacity: the deep END of the distribution (~20th percentile), NOT
    # the single deepest rep -- so one unusually deep rep or a tracking glitch
    # can't poison the baseline. Lower angle = deeper.
    capacity = float(np.percentile(depths, 20))
    target = FULL_ROM_TARGET.get(key, 95.0)
    margin = 22.0                          # shortfall vs your usual depth = "cut short"

    cut_short = 0
    for r in rep_details:
        r["short_vs_best"] = (r["depth_angle"] - capacity) > margin
        if r["short_vs_best"]:
            cut_short += 1

    if capacity <= target:
        cap = "full"
        if cut_short == 0:
            verdict = "Consistent full range."
        else:
            verdict = f"Capable of full range; {cut_short} rep(s) cut short vs your usual depth (consistency/fatigue)."
    else:
        cap = "limited"
        verdict = (f"Depth capped ~{round(capacity)}deg most reps (full ~{round(target)}deg) "
                   f"-> likely a mobility/strength limit, not carelessness.")

    return {"capacity_depth": round(capacity, 1), "capacity": cap, "cut_short_reps": cut_short, "verdict": verdict}


def analyze_exercise(exercise: str, landmarks: np.ndarray, timestamps: np.ndarray) -> dict:
    key = _resolve(exercise)
    cfg = EXERCISES[key]
    i, j, k = cfg["joints"]

    if landmarks.shape[0] < 5:
        return {"reps": 0, "form_score": 0, "grade": "F", "rep_details": [],
                "improvements": [], "self_calibration": {}}

    angle = _clean_signal(pp.angle_series(landmarks, i, j, k))
    segments = _segment_reps(angle)
    bottoms = [b for (_, b, _) in segments]
    n_frames = angle.shape[0]

    rep_details = []
    all_faults = []
    for n, (start, bottom, end) in enumerate(segments, 1):
        sl = slice(start, end + 1)
        window = angle[sl]
        # Lockout = the standing/extended peak the lifter ascends INTO after the
        # bottom. The rep window ends at the hysteresis band (below the true top),
        # so measure the peak out to the next rep's bottom (or clip end).
        next_bottom = bottoms[n] if n < len(bottoms) else n_frames
        top_seg = angle[bottom:next_bottom]
        top_val = float(top_seg.max()) if top_seg.size else float(window.max())
        m = {
            "depth": float(window.min()),
            "top": top_val,
            "lean": float(_trunk_lean_series(landmarks[sl]).max()),
            "drift": _shoulder_drift(landmarks[sl]),
        }
        faults = cfg["faults"](m)
        all_faults.extend(faults)
        rep_score = max(0, 100 - 20 * len(faults))
        rep_details.append({
            "rep": n,
            "rom": round(m["top"] - m["depth"], 1),
            "depth_angle": round(m["depth"], 1),
            "top_angle": round(m["top"], 1),
            "lean": round(m["lean"], 1),
            "drift": round(m["drift"], 3),
            "duration_s": round(float(timestamps[end] - timestamps[start]), 2),
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
        "self_calibration": _self_calibration(key, rep_details),
    }
