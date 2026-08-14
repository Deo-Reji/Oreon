"""Tag a recorded session with subject metadata for the training manifest.

Recordings auto-upload keyed to whoever is logged in, so for multi-person data
collection you stay logged in as yourself and tag each session with who it was.
Writes/updates a row in data/subjects.csv (joinable to the .npz by session_id).
The exercise is read from the .npz automatically.

Usage (from backend/, venv active):
    python tag_session.py 53 --person alice --sex F --height 165 --weight 60 --label good
    python tag_session.py 54 --person alice --sex F --height 165 --weight 60 --label shallow
Re-running for the same id overwrites that row (so you can fix mistakes).
"""
import os
import csv
import argparse
import numpy as np

HERE = os.path.dirname(__file__)                          
LANDMARK_DIR = os.path.join(HERE, "data", "landmarks")    
MANIFEST = os.path.join(HERE, "data", "subjects.csv")     
FIELDS = ["session_id", "person", "sex", "height_cm", "weight_kg", "exercise", "label"]  


def _exercise_for(session_id: int):
    path = os.path.join(LANDMARK_DIR, f"{session_id}.npz") 
    if not os.path.exists(path):
        return None                                        
    return str(np.load(path, allow_pickle=True)["exercise"])  


def _load_rows():
    if not os.path.exists(MANIFEST):
        return []                                         
    with open(MANIFEST, newline="") as f:
        return list(csv.DictReader(f))                     


def _save_rows(rows):
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)  
    with open(MANIFEST, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()                                   
        w.writerows(rows)


def main():
    p = argparse.ArgumentParser(description="Tag a session with subject metadata.")
    p.add_argument("session_id", type=int)                                  
    p.add_argument("--person", default="", help="name/label for the subject")
    p.add_argument("--sex", default="", choices=["M", "F", ""])
    p.add_argument("--height", default="", help="height in cm")
    p.add_argument("--weight", default="", help="weight in kg")
    p.add_argument("--label", default="", help="good / shallow / forward-lean / etc.")
    args = p.parse_args()

    exercise = _exercise_for(args.session_id)              
    if exercise is None:
        print(f"WARNING: no landmark file for session {args.session_id} "
              f"(tagging anyway -- double-check the id).")
        exercise = ""                                      

    row = {                                               
        "session_id": str(args.session_id),
        "person": args.person,
        "sex": args.sex,
        "height_cm": args.height,
        "weight_kg": args.weight,
        "exercise": exercise,
        "label": args.label,
    }

    rows = [r for r in _load_rows() if r.get("session_id") != str(args.session_id)]  
    rows.append(row)                                       
    rows.sort(key=lambda r: int(r["session_id"]))          
    _save_rows(rows)

    print(f"tagged session {args.session_id}: {row}")
    print(f"manifest: {MANIFEST} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
