"""Build the Stage-2 ML feature table: one row per rep, features + both label sources.

Joins the landmark clips (data/landmarks/{id}.npz) with the subject manifest
(data/subjects.csv) by running each clip through the real analysis engine and
flattening its per-rep details. The rule engine's own fault verdicts are the
bootstrap training target; the human session label rides along as ground truth
for auditing and for later, real training.

Usage (from backend/, with the venv active):
    python build_feature_table.py            # writes data/features.csv + prints report
    python build_feature_table.py --smoke    # also runs the RandomForest smoke test
"""
import csv
import os
import sys
from collections import Counter

import numpy as np

from app.services.exercises import analyze_exercise

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
LANDMARK_DIR = os.path.join(DATA_DIR, "landmarks")
SUBJECTS_CSV = os.path.join(DATA_DIR, "subjects.csv")
FEATURES_CSV = os.path.join(DATA_DIR, "features.csv")

FIELDS = [
    "session_id", "person", "sex", "height_cm", "weight_kg", "exercise",
    "session_label", "rep_num", "depth_angle", "top_angle", "rom", "lean",
    "drift", "duration_s", "rule_faults", "rule_score", "short_vs_best",
]

# Numeric per-rep features the smoke-test model trains on.
NUMERIC_FEATURES = ["depth_angle", "top_angle", "rom", "lean", "drift", "duration_s"]


def load_manifest() -> list:
    with open(SUBJECTS_CSV, newline="") as f:
        return list(csv.DictReader(f))


def build_rows(manifest: list) -> list:
    rows = []
    for s in manifest:
        path = os.path.join(LANDMARK_DIR, f"{s['session_id']}.npz")
        data = np.load(path, allow_pickle=True)
        result = analyze_exercise(str(data["exercise"]), data["landmarks"], data["timestamps"])
        for r in result["rep_details"]:
            rows.append({
                "session_id": s["session_id"],
                "person": s["person"],
                "sex": s["sex"],
                "height_cm": s["height_cm"],
                "weight_kg": s["weight_kg"],
                "exercise": s["exercise"],
                "session_label": s["label"],
                "rep_num": r["rep"],
                "depth_angle": r["depth_angle"],
                "top_angle": r["top_angle"],
                "rom": r["rom"],
                "lean": r["lean"],
                "drift": r["drift"],
                "duration_s": r["duration_s"],
                "rule_faults": ";".join(r["faults"]),
                "rule_score": r["score"],
                "short_vs_best": r.get("short_vs_best", False),
            })
    return rows


def write_features(rows: list):
    with open(FEATURES_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def sanity_report(manifest: list, rows: list):
    print(f"\n=== Feature table: {len(rows)} reps from {len(manifest)} sessions -> {FEATURES_CSV}")

    by_person = Counter()
    by_exercise = Counter()
    by_label = Counter()
    sessions_per_person = Counter()
    for s in manifest:
        sessions_per_person[s["person"]] += 1
    for r in rows:
        by_person[r["person"]] += 1
        by_exercise[r["exercise"]] += 1
        by_label[r["session_label"]] += 1

    print("\n    reps per person:")
    for person, n in by_person.most_common():
        print(f"      {person:<8} {n:>3} reps  ({sessions_per_person[person]} sessions)")
    print("    reps per exercise:")
    for ex, n in by_exercise.most_common():
        print(f"      {ex:<12} {n:>3}")
    print("    reps per session label:")
    for label, n in by_label.most_common():
        print(f"      {label:<18} {n:>3}")

    zero_rep = [s["session_id"] for s in manifest
                if not any(r["session_id"] == s["session_id"] for r in rows)]
    if zero_rep:
        print(f"\n    !! sessions with ZERO reps segmented: {zero_rep}")

    # Cross-check the two label sources. A 'good' session where the rule engine
    # flags reps is a possible false positive (regression in the thresholds); a
    # fault-labeled session where NO rep gets flagged is a miss. Both are known
    # to exist (under-exaggerated demos) — this report just keeps them visible.
    print("\n    label vs rule-engine disagreements:")
    disagreements = 0
    by_session = {}
    for r in rows:
        by_session.setdefault(r["session_id"], []).append(r)
    for s in manifest:
        reps = by_session.get(s["session_id"], [])
        flagged = [r for r in reps if r["rule_faults"]]
        if s["label"] == "good" and flagged:
            faults = Counter(f for r in flagged for f in r["rule_faults"].split(";"))
            print(f"      session {s['session_id']} ({s['person']}, {s['exercise']}, GOOD): "
                  f"{len(flagged)}/{len(reps)} reps flagged {dict(faults)}  <- possible false positive")
            disagreements += 1
        elif s["label"] != "good" and reps and not flagged:
            print(f"      session {s['session_id']} ({s['person']}, {s['exercise']}, "
                  f"{s['label']}): 0/{len(reps)} reps flagged  <- fault missed")
            disagreements += 1
    if not disagreements:
        print("      none")


def smoke_test(rows: list):
    """Proves the Stage-2 train/eval harness runs end-to-end. The accuracy number
    itself is MEANINGLESS at n=7 people — do not read anything into it."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import GroupKFold, cross_val_score

    print("\n=== RandomForest smoke test (harness check ONLY -- accuracy is NOT "
          "meaningful at this data size)")
    for exercise in sorted({r["exercise"] for r in rows}):
        sub = [r for r in rows if r["exercise"] == exercise]
        X = np.array([[float(r[f]) for f in NUMERIC_FEATURES] for r in sub])
        y = np.array([bool(r["rule_faults"]) for r in sub])
        groups = np.array([r["person"] for r in sub])
        n_people = len(set(groups))
        if len(set(y)) < 2 or n_people < 2:
            print(f"    {exercise}: skipped (not enough class/person variety)")
            continue
        # Split BY PERSON: a rep must never share a lifter with its test fold,
        # or the model just memorizes bodies instead of form.
        cv = GroupKFold(n_splits=min(5, n_people))
        scores = cross_val_score(RandomForestClassifier(n_estimators=200, random_state=0),
                                 X, y, groups=groups, cv=cv)
        print(f"    {exercise:<12} {len(sub)} reps, {n_people} people, "
              f"fault rate {y.mean():.0%}: accuracy {scores.mean():.2f} "
              f"+/- {scores.std():.2f} (person-held-out)")


def main():
    manifest = load_manifest()
    rows = build_rows(manifest)
    write_features(rows)
    sanity_report(manifest, rows)
    if "--smoke" in sys.argv:
        smoke_test(rows)


if __name__ == "__main__":
    main()
