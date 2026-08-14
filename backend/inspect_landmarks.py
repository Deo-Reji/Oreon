"""Dump per-rep analysis numbers from saved landmark clips, for tuning thresholds.

Usage (from backend/, with the venv active):
    python inspect_landmarks.py            # all saved sessions
    python inspect_landmarks.py 12         # just session 12

For each clip it prints the rep count and, per rep, the key angles the fault
rules depend on (depth_angle, top_angle, rom) plus detected faults. Compare the
numbers on a clip you KNOW was good vs one you KNOW was faulty to see where each
threshold in exercises.py should sit.
"""
import os
import sys
import glob
import numpy as np

from app.services.exercises import analyze_exercise

LANDMARK_DIR = os.path.join(os.path.dirname(__file__), "data", "landmarks")  


def inspect(path: str):
    data = np.load(path, allow_pickle=True)  
    exercise = str(data["exercise"])         
    landmarks = data["landmarks"]            
    timestamps = data["timestamps"]         

    result = analyze_exercise(exercise, landmarks, timestamps)  

    name = os.path.basename(path)           
    print(f"\n=== {name}  |  exercise='{exercise}'  |  frames={landmarks.shape[0]}")
    print(f"    reps={result['reps']}  form_score={result['form_score']}  grade={result['grade']}")
    if result["improvements"]:               
        print(f"    improvements: {result['improvements']}")
    sc = result.get("self_calibration") or {} 
    if sc:
        print(f"    self-cal: capacity={sc['capacity']}  capacity_depth={sc['capacity_depth']}  "
              f"cut_short={sc['cut_short_reps']}")
        print(f"              {sc['verdict']}")
    for r in result["rep_details"]:
        mark = " <cut-short>" if r.get("short_vs_best") else ""
        if "symmetry" in r:
            # Behind-view bench: bar heights + symmetry/flare, all in shoulder-widths.
            print(
                f"    rep {r['rep']:>2}: chest={r['depth_angle']:>5.2f}  "
                f"lockout={r['top_angle']:>5.2f}  rom={r['rom']:>5.2f}  "
                f"sym={r['symmetry']:>4.2f}  flare={r['flare']:>4.2f}  "
                f"dur={r['duration_s']:>4.1f}s  score={r['score']:>3}  faults={r['faults']}{mark}"
            )
        else:
            print(
                f"    rep {r['rep']:>2}: depth={r['depth_angle']:>6.1f}  "
                f"top={r['top_angle']:>6.1f}  rom={r['rom']:>6.1f}  "
                f"lean={r['lean']:>5.1f}  drift={r['drift']:>5.3f}  "
                f"dur={r['duration_s']:>4.1f}s  score={r['score']:>3}  faults={r['faults']}{mark}"
            )


def main():
    if len(sys.argv) > 1:                     
        paths = [os.path.join(LANDMARK_DIR, f"{sys.argv[1]}.npz")]
    else:                                     
        paths = sorted(glob.glob(os.path.join(LANDMARK_DIR, "*.npz")))

    if not paths:
        print(f"No landmark files found in {LANDMARK_DIR}")
        return

    for p in paths:
        if os.path.exists(p):                 
            inspect(p)
        else:
            print(f"Not found: {p}")


if __name__ == "__main__":
    main()
