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
    # Vector pointing up the torso. Image y-axis is inverted (0 at top),
    # so a perfectly upright torso points in the (0, -1) direction.
    vec = shoulder_mid - hip_mid
    # arctan2(|horizontal|, -vertical) gives 0° when perfectly upright and grows
    # as the lifter leans forward or backward — we only care about magnitude here.
    ang = np.degrees(np.arctan2(np.abs(vec[:, 0]), -vec[:, 1]))
    return ang.astype(np.float32)


def _shoulder_drift(landmarks: np.ndarray) -> float:
    """Robust horizontal travel of the shoulder midpoint (proxy for swinging).

    Median-filtered then measured as the 5-95 percentile span (not raw max-min) so
    a single mis-tracked frame can't fake a swing. This is a RAW distance in image
    coords; the caller divides it by torso length to make it scale-invariant (see
    _torso_length — shoulder WIDTH can't be the ruler here because side-on the two
    shoulders overlap and that distance collapses toward zero)."""
    xy = landmarks[:, :, :2]
    if xy.shape[0] == 0:
        return 0.0
    sx = (xy[:, pp.L_SHOULDER, 0] + xy[:, pp.R_SHOULDER, 0]) / 2.0
    sx = _median_filter(sx)
    return float(np.percentile(sx, 95) - np.percentile(sx, 5))


def _torso_length(landmarks: np.ndarray) -> float:
    """Median shoulder-midpoint to hip-midpoint distance = the side-view scale ruler.

    Unlike shoulder WIDTH (which foreshortens to ~0 when filmed side-on, because one
    shoulder sits behind the other), the torso's vertical length stays fully visible
    and stable from the side. Used to normalize horizontal drift so 'swing' means the
    same thing regardless of camera distance or body size. One scalar per clip."""
    sh = (landmarks[:, pp.L_SHOULDER, :2] + landmarks[:, pp.R_SHOULDER, :2]) / 2.0
    hp = (landmarks[:, pp.L_HIP, :2] + landmarks[:, pp.R_HIP, :2]) / 2.0
    return float(np.clip(np.median(np.linalg.norm(sh - hp, axis=1)), 1e-3, None))


# --- Behind-view bench helpers -------------------------------------------------
# Bench is filmed from behind the head (both arms visible, no body occlusion).
# From that angle the elbow ANGLE is foreshortened and useless, so bench is driven
# by WRIST HEIGHT instead. Distances aren't scale-free like angles were, so every
# bench measurement is normalized by shoulder width (a stable, visible-from-behind
# ruler) to stay invariant to camera distance and body size.

def _shoulder_width(landmarks: np.ndarray) -> float:
    """Median shoulder-to-shoulder distance across the clip = the scale ruler.

    One scalar per clip (median, not per-frame) so the ruler stays fixed even if
    a few frames jitter. Clamped to a small positive value to avoid div-by-zero.
    """
    xy = landmarks[:, :, :2]
    w = np.linalg.norm(xy[:, pp.L_SHOULDER] - xy[:, pp.R_SHOULDER], axis=1)
    return float(np.clip(np.median(w), 1e-3, None))


def _bar_height_series(landmarks: np.ndarray, scale: float) -> np.ndarray:
    """Bar (wrist-midpoint) height above the shoulder line, in shoulder-widths.

    Image y grows downward, so (shoulder_y - wrist_y) is POSITIVE when the wrists
    are above the shoulders. ~0 at the chest, large when pressed out to lockout.
    Referencing to the shoulder line makes it invariant to where the body sits in
    the frame; dividing by shoulder width makes it invariant to camera distance.
    """
    xy = landmarks[:, :, :2]
    wrist_y = (xy[:, pp.L_WRIST, 1] + xy[:, pp.R_WRIST, 1]) / 2.0
    shoulder_y = (xy[:, pp.L_SHOULDER, 1] + xy[:, pp.R_SHOULDER, 1]) / 2.0
    return ((shoulder_y - wrist_y) / scale).astype(np.float32)


MIN_VIS = 0.5   # landmarks below this visibility are occluded/guessed -> ignore them


def _wrist_symmetry_series(landmarks: np.ndarray, scale: float) -> np.ndarray:
    """|left wrist height - right wrist height| per frame, in shoulder-widths.

    Large = one hand pressing higher than the other (uneven press) — the fault
    only a behind view can see. y is down, so the raw vertical gap is |Ly - Ry|.

    Frames where either wrist is occluded (visibility < MIN_VIS) are set to NaN so
    a mis-tracked far arm can't fake asymmetry; the caller aggregates with a
    percentile (not max) so single glitch frames don't dominate.
    """
    xy = landmarks[:, :, :2]
    vis = landmarks[:, :, 3]
    gap = (np.abs(xy[:, pp.L_WRIST, 1] - xy[:, pp.R_WRIST, 1]) / scale).astype(np.float32)
    bad = (vis[:, pp.L_WRIST] < MIN_VIS) | (vis[:, pp.R_WRIST] < MIN_VIS)
    gap[bad] = np.nan
    return gap


def _elbow_flare_series(landmarks: np.ndarray, scale: float) -> np.ndarray:
    """Mean lateral distance of the elbows from the shoulder midline, in
    shoulder-widths. Large = elbows splayed wide out to the sides.

    From behind, elbow flare happens in the image plane (left/right), so it IS
    measurable here even though the elbow's bend angle is not. Occluded elbows
    (visibility < MIN_VIS) are NaN-masked, same as the symmetry series.
    """
    xy = landmarks[:, :, :2]
    vis = landmarks[:, :, 3]
    mid_x = (xy[:, pp.L_SHOULDER, 0] + xy[:, pp.R_SHOULDER, 0]) / 2.0
    left = np.abs(xy[:, pp.L_ELBOW, 0] - mid_x)
    right = np.abs(xy[:, pp.R_ELBOW, 0] - mid_x)
    flare = ((left + right) / 2.0 / scale).astype(np.float32)
    bad = (vis[:, pp.L_ELBOW] < MIN_VIS) | (vis[:, pp.R_ELBOW] < MIN_VIS)
    flare[bad] = np.nan
    return flare


def _robust_max(series: np.ndarray) -> float:
    """A glitch-resistant 'worst value' for a rep window: the 75th percentile of
    the valid (non-NaN) frames, not the raw max. Returns 0.0 if nothing valid."""
    vals = series[~np.isnan(series)]
    if vals.size == 0:
        return 0.0
    return float(np.percentile(vals, 75))


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
    """Moving-average smooth over k frames. Output length equals input length."""
    if a.shape[0] < k or k < 2:
        return a
    kernel = np.ones(k) / k
    return np.convolve(a, kernel, mode="same").astype(np.float32)


def _clean_signal(angle: np.ndarray) -> np.ndarray:
    """De-glitch then smooth the rep-driving angle signal."""
    return _smooth(_median_filter(angle))


def _segment_reps(angle: np.ndarray, min_range: float = 25.0, margin_frac: float = 0.15):
    """Adaptive rep segmentation: count an oscillation relative to THIS clip's
    own range, so partial/short reps still register (a fixed high/low threshold
    misses them entirely). A rep = cross above the upper band, dip below the
    lower band, return above the upper band.

    margin_frac sets the hysteresis band width as a fraction of the clip's range.
    Bigger = more noise rejection but misses small reps; smaller = catches small
    reps but risks double-counting jitter. Bench uses a tighter band than the
    squat/curl default because its wrist-height swing is smaller.

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
    margin = margin_frac * rng            # hysteresis band to avoid double-counts on noise near the threshold
    upper, lower = mid + margin, mid - margin

    reps = []
    state = "init"
    # Latest frame at/above the top band. A rep starts at the descent, not when
    # the lifter first reached the top — this drops the walk-in / un-rack /
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
                top_idx = t          # keep advancing so top_idx is the last frame at the top band before descent
            elif a <= lower:
                state = "bottom"
                min_val = a
                min_idx = t
        elif state == "bottom":
            if a < min_val:          # track the deepest frame during the descent
                min_val = a
                min_idx = t
            if a >= upper:           # ascent complete: one full rep
                reps.append((top_idx, min_idx, t))
                state = "top"
                top_idx = t
                min_val = np.inf
    return reps


# --- Form rule sets (take a per-rep metrics dict, return fault labels) ---
# "depth" = minimum angle in the window (most-bent position).
# "top"   = maximum angle measured from the bottom up to the next rep's bottom
#            (not just within the rep window — see top_val logic in analyze_exercise).
# "lean"  = max trunk lean in degrees over the rep window.
# "drift" = horizontal shoulder travel over the rep window (normalised coords).

def _squat_faults(m):
    faults = []
    # Knee angle at bottom > 100° means the lifter didn't squat deep enough.
    if m["depth"] > 100:
        faults.append("Not enough depth")
    # Knee angle at lockout below SQUAT_LOCKOUT_MIN means legs never fully extended.
    # This one stays a flat cutoff (not a per-person percentage like the curl ROM
    # faults) because self-calibration provably fails here: a tall lifter's OWN good
    # squat lockout can swing ~133-175° within a single good set (validated on tanav,
    # n=7), so there's no stable "their 100%" to take a percentage of — any relative
    # rule flags their own low-but-good reps. The lowered floor (was 160) is set just
    # under the lowest good-squat lockout seen across the roster.
    if m["top"] < SQUAT_LOCKOUT_MIN:
        faults.append("Incomplete lockout")
    # NOTE: "Excessive forward lean" is NOT decided here. A flat per-rep cutoff
    # false-flagged every good squat (lean is body-type dependent), so it's added
    # afterwards by _apply_lean_calibration, which needs the whole set to judge a
    # rep against the lifter's own baseline.
    return faults


def _curl_faults(m):
    faults = []
    # Only swing is a flat per-rep rule here. "Incomplete curl" and "Incomplete
    # extension" USED to be flat angle cutoffs (depth>80, top<150) but those
    # false-flagged good form on bigger/taller lifters: raghu's GOOD hammer curl
    # bottoms at 77-91° (a big-armed neutral-grip curl legitimately doesn't flex as
    # far) and overlapped geo's deliberate partial-curl demo (80-97°) — no flat
    # cutoff can pass one and catch the other. They're now judged against each
    # lifter's OWN range in _apply_curl_calibration (needs the whole set).
    #
    # Shoulder midpoint translating horizontally > 0.28 TORSO-LENGTHS during a rep
    # indicates body english (rocking the torso to heave the weight). Calibrated
    # from labeled good-vs-swing hammer-curl sets across 4 subjects: good reps
    # topped out ~0.24 torso-lengths of drift, deliberate-swing reps ran 0.33-0.75.
    # (m["drift"] is already torso-length-normalized by analyze_exercise; the old
    # raw-pixel version was scale-dependent and missed swings filmed farther away.)
    if m["drift"] > 0.28:
        faults.append("Swinging / using momentum")
    return faults


# --- Behind-view bench thresholds ---------------------------------------------
# PROVISIONAL, in SHOULDER-WIDTH units (not degrees). Bar height = (shoulder_y -
# wrist_y) / shoulder_width: ~0 at the chest, larger when pressed toward lockout.
# These are first-pass guesses to be tuned from behind-camera data, exactly like
# the squat/curl angle thresholds were tuned from side-view clips.
BENCH_MIN_RANGE = 0.5       # min bar travel (shoulder-widths) for a rep to count
BENCH_LOCKOUT_MIN = 1.2     # top bar height below this -> didn't fully lock out
BENCH_CHEST_MAX = 0.55      # bottom bar height above this -> bar didn't reach chest
BENCH_SYMMETRY_MAX = 0.40   # L/R wrist-height gap above this -> uneven press
BENCH_FLARE_MAX = 1.30      # elbow lateral spread above this -> flared elbows


def _bench_faults(m):
    """Behind-view bench, driven by wrist height (not elbow angle).

    m["top"]  = peak bar height (lockout), m["depth"] = lowest bar height (chest),
    m["symmetry"] = worst L/R wrist-height gap, m["flare"] = worst elbow spread.
    All in shoulder-width units.
    """
    faults = []
    # Bar never rose to full lockout height.
    if m["top"] < BENCH_LOCKOUT_MIN:
        faults.append("Incomplete lockout")
    # Bar never descended to chest level (partial range).
    if m["depth"] > BENCH_CHEST_MAX:
        faults.append("Partial range (bar not to chest)")
    # One arm pressed noticeably higher than the other.
    if m["symmetry"] > BENCH_SYMMETRY_MAX:
        faults.append("Uneven press (one arm higher)")
    # Elbows splayed out wide instead of tracking under the bar.
    if m["flare"] > BENCH_FLARE_MAX:
        faults.append("Elbow flare")
    return faults


# joints_l / joints_r: the angle hinge triple (i, j, k) for each body side — the
# angle is measured at landmark j. We keep BOTH sides so the analyzer can use
# whichever one the camera actually saw (see _pick_side), instead of assuming the
# lifter filmed their left side. Bench is NOT here: it uses a wrist-height pipeline
# (_analyze_bench), not a joint angle, so it's routed separately in analyze_exercise().
EXERCISES = {
    "squat": {"joints_l": (pp.L_HIP, pp.L_KNEE, pp.L_ANKLE),
              "joints_r": (pp.R_HIP, pp.R_KNEE, pp.R_ANKLE),
              "faults": _squat_faults},
    "curl":  {"joints_l": (pp.L_SHOULDER, pp.L_ELBOW, pp.L_WRIST),
              "joints_r": (pp.R_SHOULDER, pp.R_ELBOW, pp.R_WRIST),
              "faults": _curl_faults},
}


def _pick_side(landmarks: np.ndarray, left: tuple, right: tuple) -> tuple:
    """Return whichever joint triple (left or right) the camera tracked better.

    A side-on squat/curl film shows one side of the body clearly and leaves the
    far side occluded (MediaPipe still guesses it, but with low visibility). We
    compare the mean visibility of each side's three joints across the whole clip
    and drive the analysis off the well-seen side — so it doesn't matter which way
    the lifter faces the camera. Ties go to left (arbitrary, stable).
    """
    vis = landmarks[:, :, 3]
    vis_left = float(vis[:, list(left)].mean())
    vis_right = float(vis[:, list(right)].mean())
    return right if vis_right > vis_left else left


def _resolve(exercise: str) -> str:
    """Map a free-form exercise name from the app to an analyzer key.

    e.g. "Bench Press" -> "bench", "Hammer Curl" -> "curl", "Squat" -> "squat".
    Falls back to "squat" silently for any unrecognised name — callers should
    validate the exercise name before reaching here to avoid surprising results.
    """
    name = (exercise or "").lower()
    if "bench" in name:
        return "bench"
    if "curl" in name:
        return "curl"
    if "squat" in name:
        return "squat"
    # Unknown exercise: default to squat rather than raising, so the pipeline
    # never crashes on an unexpected name. The squat joint triple (knee angle)
    # is the most generic proxy available.
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
# squat/curl are in DEGREES (min joint angle at full range); bench is in
# SHOULDER-WIDTHS (lowest bar height that counts as reaching the chest).
FULL_ROM_TARGET = {"squat": 95.0, "curl": 75.0, "bench": 0.30}

# "Cut short vs your usual best" margin, in the same unit as the exercise's depth.
CUT_SHORT_MARGIN = {"squat": 22.0, "curl": 22.0, "bench": 0.40}

# Unit label per exercise, for the human-readable verdict string.
DEPTH_UNIT = {"squat": "deg", "curl": "deg", "bench": "sw"}


def _fmt_depth(v: float, unit: str) -> str:
    """Format a depth value for the verdict: whole degrees, or 2dp shoulder-widths."""
    return f"{v:.2f}{unit}" if unit == "sw" else f"{round(v)}{unit}"


def _self_calibration(key: str, rep_details: list) -> dict:
    """Relative layer ON TOP OF the absolute fault rules.

    Judges each rep against the lifter's OWN best rep this set (their demonstrated
    capacity), and separates 'can't' (a consistent range limit -> mobility/strength)
    from 'won't' (some reps cut short vs their best -> consistency/fatigue). The
    absolute rules still decide correctness; this only adds context.

    NOTE: this function mutates each dict in rep_details in-place, adding a
    'short_vs_best' boolean key. The caller's rep_details list (and the API
    response that includes it) will therefore contain this extra field.
    """
    depths = [r["depth_angle"] for r in rep_details]
    if not depths:
        return {}

    # Robust capacity: the deep END of the distribution (~20th percentile), NOT
    # the single deepest rep — so one unusually deep rep or a tracking glitch
    # can't poison the baseline. Lower angle = deeper for all supported exercises.
    capacity = float(np.percentile(depths, 20))
    target = FULL_ROM_TARGET.get(key, 95.0)
    margin = CUT_SHORT_MARGIN.get(key, 22.0)  # shortfall vs usual depth = "cut short"
    unit = DEPTH_UNIT.get(key, "deg")

    cut_short = 0
    for r in rep_details:
        # A rep is "cut short" if it is more than `margin` degrees shallower than
        # the lifter's own typical depth (capacity), not against the population target.
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
        verdict = (f"Depth capped ~{_fmt_depth(capacity, unit)} most reps "
                   f"(full ~{_fmt_depth(target, unit)}) "
                   f"-> likely a mobility/strength limit, not carelessness.")

    return {"capacity_depth": round(capacity, 1), "capacity": cap, "cut_short_reps": cut_short, "verdict": verdict}


# --- Squat forward-lean: self-calibrated, NOT a flat cutoff -------------------
# A flat "lean > 50°" rule false-flagged EVERY good squat across 4 subjects
# (long-femur lifters naturally sit at ~50-59° of trunk lean). Static trunk lean
# is heavily body-type dependent, and within a single set a deliberate uniform
# lean is indistinguishable from a naturally leany build (no internal variation to
# key off). So we judge lean two ways together:
#   - RELATIVE: a rep that leans LEAN_DELTA past THIS lifter's own median lean —
#     i.e. their form degraded / they fatigued on that rep.
#   - ABSOLUTE: LEAN_HARD as an egregious safety net, the only thing that can catch
#     a set that is uniformly over-leaned (the relative test is blind to that).
# PROVISIONAL (n=4): good squats topped out ~59°, deliberate-lean sets ran 62-72°.
# Revisit as more bodies come in — expect to lower LEAN_HARD if uprighter subjects
# never approach it, or lean on the relative term more once fatigue data exists.
LEAN_DELTA = 12.0   # degrees past your own median lean = this rep degraded
LEAN_HARD = 62.0    # degrees absolute = excessive for almost any build


# --- Curl ROM faults: percentage of the lifter's OWN range, not a flat cutoff ---
# Same lesson as lean, hit again on the curl: "good" ROM is body-dependent (raghu's
# big-armed hammer curl bottoms at ~87° and is genuinely full for him; a smaller
# lifter reaches ~55°), so a flat angle cutoff false-flags the outliers. Each rep is
# judged as a PERCENTAGE of THIS lifter's own best rep this set (relative term),
# with a loose absolute net for a set that is uniformly short (where the relative
# term has no good rep to key off — the same blind spot lean's LEAN_HARD covers).
# Elbow is treated as straight at ~180°; flexion/extension are measured from there.
ELBOW_STRAIGHT = 180.0
CURL_FLEX_KEEP = 0.82    # a rep must reach >=82% of the lifter's own best flexion (curl height)
CURL_DEPTH_HARD = 95.0   # abs net: elbow never flexed past ~95° => barely curled at all
EXT_HARD = 130.0         # abs net: elbow never straightened past 130° => clearly short
EXT_DEFICIT_MULT = 2.5   # rep sat >2.5x further from straight than the lifter's own best


def _apply_curl_calibration(rep_details: list) -> None:
    """Add the curl ROM faults ('Incomplete curl', 'Incomplete extension') relative
    to the lifter's OWN demonstrated range, then rescore each rep. Mutates in place.
    Runs after all reps are measured because it needs the whole set to know the
    lifter's capacity — a big-armed or tall lifter is judged against themselves, not
    a stranger's angles."""
    if not rep_details:
        return
    depths = [r["depth_angle"] for r in rep_details]  # min elbow angle = curl height
    tops = [r["top_angle"] for r in rep_details]       # max elbow angle = extension
    # Curl-up capacity: the deepest flexion the lifter showed (robust ~20th pct, not
    # the single best rep, so one unusually high curl can't poison the baseline).
    cap_depth = float(np.percentile(depths, 20))
    best_flex = ELBOW_STRAIGHT - cap_depth
    # Extension capacity: the straightest the lifter got (robust ~80th pct).
    cap_top = float(np.percentile(tops, 80))
    best_ext_deficit = ELBOW_STRAIGHT - cap_top
    for r in rep_details:
        # Incomplete curl: this rep reached < CURL_FLEX_KEEP of the lifter's own best
        # flexion, OR barely flexed at all (absolute net for a uniformly-short set).
        rep_flex = ELBOW_STRAIGHT - r["depth_angle"]
        if (rep_flex < CURL_FLEX_KEEP * best_flex or r["depth_angle"] > CURL_DEPTH_HARD) \
                and "Incomplete curl" not in r["faults"]:
            r["faults"].append("Incomplete curl")
        # Incomplete extension: this rep sat EXT_DEFICIT_MULT× further from a straight
        # arm than the lifter's own best, OR never straightened past EXT_HARD (net).
        rep_ext_deficit = ELBOW_STRAIGHT - r["top_angle"]
        if (r["top_angle"] < EXT_HARD or rep_ext_deficit > EXT_DEFICIT_MULT * best_ext_deficit) \
                and "Incomplete extension" not in r["faults"]:
            r["faults"].append("Incomplete extension")
        r["score"] = max(0, 100 - 20 * len(r["faults"]))


# --- Squat lockout floor (see _squat_faults for why this is a flat cutoff) --------
SQUAT_LOCKOUT_MIN = 130.0   # lowered from 160: lowest good-squat lockout on the roster (~133, tanav)


def _apply_lean_calibration(rep_details: list) -> None:
    """Add the squat 'Excessive forward lean' fault relative to the lifter's own
    baseline, then rescore each rep. Mutates rep_details in place. Runs after all
    reps are measured because it needs the whole set to know the lifter's norm."""
    leans = [r["lean"] for r in rep_details]
    if not leans:
        return
    baseline = float(np.median(leans))
    for r in rep_details:
        excessive = (r["lean"] > baseline + LEAN_DELTA) or (r["lean"] > LEAN_HARD)
        if excessive and "Excessive forward lean" not in r["faults"]:
            r["faults"].append("Excessive forward lean")
        r["score"] = max(0, 100 - 20 * len(r["faults"]))


def _analyze_bench(landmarks: np.ndarray, timestamps: np.ndarray) -> dict:
    """Behind-view bench analysis, driven by wrist height instead of joint angle.

    The bar-height signal (high at lockout, ~0 at chest) is segmented into reps
    the same way the squat/curl angle is; depth/lockout come from that signal and
    symmetry/flare are measured per rep. Everything is in shoulder-width units.
    """
    scale = _shoulder_width(landmarks)
    # The wrist-height signal is jitterier than a joint angle, so smooth it harder
    # (9-wide vs the default 5) before segmenting — otherwise small wiggles get
    # counted as reps. Tighter hysteresis band (0.10) because the swing is smaller.
    bar = _smooth(_median_filter(_bar_height_series(landmarks, scale)), k=9)
    sym = _wrist_symmetry_series(landmarks, scale)
    flare = _elbow_flare_series(landmarks, scale)

    segments = _segment_reps(bar, min_range=BENCH_MIN_RANGE, margin_frac=0.10)
    bottoms = [b for (_, b, _) in segments]
    n_frames = bar.shape[0]

    rep_details = []
    all_faults = []
    for rep_num, (start, bottom, end) in enumerate(segments, 1):
        sl = slice(start, end + 1)
        window = bar[sl]

        # Peak (lockout) is measured from this rep's bottom to the next rep's
        # bottom — same look-ahead trick as the angle path, because the rep
        # window ends at the hysteresis band, below the true top.
        next_bottom = bottoms[rep_num] if rep_num < len(bottoms) else n_frames
        top_seg = bar[bottom:next_bottom]
        top_val = float(top_seg.max()) if top_seg.size else float(window.max())

        m = {
            "depth": float(window.min()),          # lowest bar height = closest to chest
            "top": top_val,                        # highest bar height = lockout
            "symmetry": _robust_max(sym[sl]),      # worst L/R wrist-height gap (glitch-resistant)
            "flare": _robust_max(flare[sl]),       # worst elbow spread (glitch-resistant)
        }
        faults = _bench_faults(m)
        all_faults.extend(faults)
        rep_score = max(0, 100 - 20 * len(faults))
        rep_details.append({
            "rep": rep_num,
            "rom": round(m["top"] - m["depth"], 2),
            "depth_angle": round(m["depth"], 2),   # chest bar height (name kept for schema parity)
            "top_angle": round(m["top"], 2),       # lockout bar height
            "symmetry": round(m["symmetry"], 2),
            "flare": round(m["flare"], 2),
            "duration_s": round(float(timestamps[end] - timestamps[start]), 2),
            "faults": faults,
            "score": rep_score,
        })

    reps = len(rep_details)
    form_score = int(round(np.mean([r["score"] for r in rep_details]))) if reps else 0
    counts = Counter(all_faults)
    improvements = [f"{label} ({cnt}/{reps})" for label, cnt in counts.most_common(3)]

    return {
        "reps": reps,
        "form_score": form_score,
        "grade": _grade(form_score),
        "rep_details": rep_details,
        "improvements": improvements,
        "self_calibration": _self_calibration("bench", rep_details),
    }


def analyze_exercise(exercise: str, landmarks: np.ndarray, timestamps: np.ndarray) -> dict:
    key = _resolve(exercise)

    if landmarks.shape[0] < 5:
        return {"reps": 0, "form_score": 0, "grade": "F", "rep_details": [],
                "improvements": [], "self_calibration": {}}

    # Bench uses its own wrist-height pipeline (elbow angle is useless from behind).
    if key == "bench":
        return _analyze_bench(landmarks, timestamps)

    cfg = EXERCISES[key]
    # Use whichever body side the camera actually saw, not a hardcoded left side.
    i, j, k = _pick_side(landmarks, cfg["joints_l"], cfg["joints_r"])
    # Side-view scale ruler for the drift/swing metric (see _torso_length).
    tscale = _torso_length(landmarks)

    # Compute the joint angle time series, then de-glitch and smooth it.
    # This is the single signal used for rep segmentation for this exercise.
    angle = _clean_signal(pp.angle_series(landmarks, i, j, k))
    segments = _segment_reps(angle)

    # Pre-extract all rep bottom indices so we can look up the NEXT rep's bottom
    # when measuring the top/lockout angle (see top_val logic below).
    bottoms = [b for (_, b, _) in segments]
    n_frames = angle.shape[0]   # == timestamps.shape[0]; used as the end sentinel for the last rep

    rep_details = []
    for rep_num, (start, bottom, end) in enumerate(segments, 1):
        sl = slice(start, end + 1)
        window = angle[sl]

        # The rep window ends at the hysteresis band crossing (below the true top),
        # NOT at the actual lockout peak. To capture the real top angle we look ahead
        # from this rep's bottom to the next rep's bottom (or the clip end).
        #
        # INDEXING NOTE: rep_num is 1-indexed (enumerate starts at 1), and bottoms
        # is 0-indexed. bottoms[rep_num] is therefore the (rep_num+1)-th element,
        # i.e. exactly the NEXT rep's bottom. This is intentional — don't change
        # the enumerate start without updating this line.
        next_bottom = bottoms[rep_num] if rep_num < len(bottoms) else n_frames
        top_seg = angle[bottom:next_bottom]
        top_val = float(top_seg.max()) if top_seg.size else float(window.max())

        m = {
            # Minimum angle in the rep window = the deepest/most-bent position.
            "depth": float(window.min()),
            # Maximum angle from bottom to next rep's bottom = the lockout/extended peak.
            "top": top_val,
            # Worst-case trunk lean across the rep window (degrees from vertical).
            "lean": float(_trunk_lean_series(landmarks[sl]).max()),
            # Horizontal shoulder travel across the rep window, in torso-lengths
            # (scale-invariant swing proxy — see _shoulder_drift / _torso_length).
            "drift": _shoulder_drift(landmarks[sl]) / tscale,
        }
        faults = cfg["faults"](m)
        # Each fault deducts 20 points; floor at 0. (Squat lean may add another
        # fault below in _apply_lean_calibration, which rescores those reps.)
        rep_score = max(0, 100 - 20 * len(faults))
        rep_details.append({
            "rep": rep_num,
            "rom": round(m["top"] - m["depth"], 1),
            "depth_angle": round(m["depth"], 1),
            "top_angle": round(m["top"], 1),
            "lean": round(m["lean"], 1),
            "drift": round(m["drift"], 3),
            "duration_s": round(float(timestamps[end] - timestamps[start]), 2),
            "faults": faults,
            "score": rep_score,
        })

    # Squat forward-lean is decided against the lifter's own baseline, so it runs
    # here (after every rep's lean is known) rather than in the per-rep fault rule.
    # Mutates rep_details: may append the lean fault and rescore affected reps.
    if key == "squat":
        _apply_lean_calibration(rep_details)
    elif key == "curl":
        _apply_curl_calibration(rep_details)

    reps = len(rep_details)
    form_score = int(round(np.mean([r["score"] for r in rep_details]))) if reps else 0

    # Most common faults across all reps become the "things to improve" list.
    # Counted from the final rep_details so post-pass faults (lean) are included.
    all_faults = [f for r in rep_details for f in r["faults"]]
    counts = Counter(all_faults)
    improvements = [f"{label} ({cnt}/{reps})" for label, cnt in counts.most_common(3)]

    return {
        "reps": reps,
        "form_score": form_score,
        "grade": _grade(form_score),
        "rep_details": rep_details,   # dicts are further enriched by _self_calibration below
        "improvements": improvements,
        "self_calibration": _self_calibration(key, rep_details),
    }
