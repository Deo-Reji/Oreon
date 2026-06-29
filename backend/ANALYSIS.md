# Oreon Analysis Engine — Logic Map & Audit Notes

A guide for reviewing what the form analysis actually does, where it's solid, and
where it's fragile. Read top to bottom; the "Audit checklist" at the end is the
list to work through.

## The pipeline (the flow)

```
video bytes
  -> posePipeline.extract_pose_sequence()   # MediaPipe, every 2nd frame -> (T,33,4)
  -> exercises.analyze_exercise()
       -> _clean_signal()                   # median de-glitch + moving-average smooth
       -> angle_series()                    # the rep-driving joint angle, per frame
       -> _segment_reps()                   # split the angle signal into reps
       -> per rep: depth / top / lean / drift / duration
       -> cfg["faults"](metrics)            # ABSOLUTE rule checks -> fault labels
       -> _self_calibration()               # RELATIVE layer (capacity, cut-short)
  -> reps, form_score, grade, improvements, rep_details, self_calibration
storage.save_landmarks()                    # raw (T,33,4) .npz = ML training data
```

Two layers of judgment, kept separate on purpose:
- **Absolute rules** decide *correctness* (is this a proper rep?). Fixed thresholds.
- **Self-calibration** adds *context* (vs your own capacity; can't vs won't). Relative.

## File-by-file

### posePipeline.py — turns video into a clean angle signal
- `extract_pose_sequence(sample_every=2)` — runs MediaPipe on every 2nd frame.
  Skipped frames are grabbed but not decoded (the speedup).
- `normalize_sequence()` — centers on hips, scales by torso. Removes body SIZE +
  position. (Currently NOT used by the rule engine — angles are already size-
  invariant — but it's there for ML features.)
- `angle_series(i,j,k)` — the per-frame joint angle that drives everything.

### exercises.py — segmentation, metrics, faults, self-cal
- `_clean_signal()` = `_median_filter()` (kills single-frame glitches) then
  `_smooth()` (5-wide moving average).
- `_segment_reps(min_range=25)` — ADAPTIVE. Uses this clip's own 5th/95th
  percentile to set an upper/lower band (hysteresis margin = 15% of range). A rep
  = cross upper -> dip below lower -> back above upper. Counts partial reps that a
  fixed threshold would miss. Rep START = the descent (last frame at top), so
  walk-in/un-rack time is excluded.
- Per-rep metrics:
  - `depth` = min angle in the rep window (the bottom). Lower = deeper.
  - `top`  = max angle from the bottom out to the NEXT rep's bottom (the lockout
    the lifter ascends into — measured here because the rep window ends at the
    hysteresis band, below the true peak).
  - `lean` = max torso angle from vertical during the rep (squat only meaning).
  - `drift` = horizontal travel of the shoulder midpoint (swing proxy).

## The numbers that drive everything (every threshold is here)

| Where | Param | Value | Meaning |
|---|---|---|---|
| `_segment_reps` | min_range | 25 | below this much motion -> 0 reps |
| `_segment_reps` | margin | 0.15*range | hysteresis band |
| squat | depth > | 100 | "Not enough depth" |
| squat | lean > | 50 | "Excessive forward lean" |
| squat | top < | 160 | "Incomplete lockout" |
| curl | top < | 150 | "Incomplete extension" |
| curl | depth > | 55 | "Incomplete curl" |
| curl | drift > | 0.08 | "Swinging / using momentum" |
| bench | top < | 160 | "Incomplete lockout" |
| bench | depth > | 100 | "Partial range (bar not to chest)" |
| self-cal | FULL_ROM_TARGET | squat 95 / curl 60 / bench 95 | "full range" depth |
| self-cal | capacity | 20th pct of depths | robust "your usual best" |
| self-cal | margin | 22 | shortfall vs capacity = "cut short" |
| score | per fault | -20 | rep score = 100 - 20*faults |
| grade | A/B/C/D | 90/80/70/60 | letter from score |

**Every one of these is fit to Deo's body + side-view camera. They are the thing
that will NOT generalize — that's the multi-person job, not a bug.**

## Known weak spots (with evidence from your clips)

1. **Bench tracking glitches.** Files 44/46 have depth=11.7°, 5.9°, 23.6° — your
   elbow didn't bend that far; MediaPipe lost your arm (lying-down occlusion,
   mostly first/last rep). Median filter doesn't catch multi-frame dropouts.
   -> Candidate fix: reject physically-implausible depths (e.g. bench elbow <30°)
   or trim the first/last rep on bench. Bench is the weakest of the three.

2. **`cut_short` is still noisy.** Bench 44 flags 6 "cut short" on a clean 100/A
   set, because capacity (49°) sits between the two deep early reps and the normal
   ~73° reps. This feature is inherently shaky from a SINGLE set — it's the part
   that most needs cross-session baselines. Low stakes (informational), but don't
   trust it yet.

3. **Lean threshold (50) is the textbook overfitting case.** It cleanly separates
   YOUR good squats (lean 26-42) from your intentional-lean clips (52-72). But a
   long-femur lifter *must* lean more to stay balanced — 50 would false-flag them.
   This is exactly why absolute lean must eventually become relative/ML.

4. **Bench `lean` displays 88-180°** (you're horizontal, so torso-from-vertical is
   ~90°+). It's meaningless for bench and unused by bench rules, but it's confusing
   in the output. -> Candidate: don't compute/show lean for bench.

5. **Curl "Incomplete curl" (depth>55) is borderline.** Your good hammer curls
   bottom out at 53-63°, so good reps at 56-63 sometimes get flagged. A hammer curl
   legitimately may not get the elbow below ~55-60. -> maybe loosen to ~65.

## Audit checklist (work through this tomorrow)

For each .npz, you KNOW what you did. Compare against the output:

1. **Rep count** — is `reps` right on every clip? (Bench 44 reports 11 for 8 —
   glitch reps. Curl 49 reports 4 for ~8 — partials still merging?)
2. **Each fault** — do you AGREE with every time it fires? Note false positives
   (fires when form was fine) and false negatives (misses a real fault).
3. **Thresholds** — for each fault, find the gap between your known-good and
   known-bad reps. Is the threshold in that gap? Write the better number.
4. **Self-cal verdict** — does "limited" vs "capable but cut short" match reality?
5. **Score/grade** — does -20/fault and the A-F cutoffs feel right, or too harsh?
6. **Generalization gut-check** — for each threshold, ask "would this still be
   right for someone twice my size / half my mobility?" Flag the ones that won't.

## What "ready for ML" means (the bar to clear before multi-person)

- Rep counting is reliable on clean clips (it is; bench glitches aside).
- Faults fire sensibly and the thresholds are in roughly the right place for one
  person (close — needs your audit pass).
- The landmark .npz capture is trustworthy (it is — that's the training data).
- You're confident the FEATURES (depth/top/lean/drift/ROM/tempo) are the right
  signals, even if the THRESHOLDS need diverse data. (They are.)

Once the audit confirms the above, the thresholds become a multi-person tuning job
(or ML's job), and the engine is "ready" to start collecting from other people.
