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


def build_rows(manifest: list) -> tuple:
    """Returns (rows, skipped, missing).

    skipped = bench sessions, excluded on purpose: bench is parked/uncalibrated AND
    its rep_details carry a different schema (symmetry/flare instead of lean/drift),
    so folding it in would mean half-empty columns and rows the ML shouldn't train on.

    missing = manifest rows whose .npz is gone. This is reachable, not paranoia:
    tag_session.py deliberately lets you tag a session before/without its landmark
    file, and cleanup_session.py deletes .npz files without touching subjects.csv.
    Reported rather than raised, so one stale row can't block the whole table.

    mismatched = sessions where the .npz's exercise disagrees with subjects.csv.
    The analyzer follows the .npz (that's what was actually filmed) while the table
    records the CSV's exercise, so a disagreement would silently mislabel real
    features -- the same class of fault as the mis-tagged session 90-93 batch.
    """
    rows = []
    skipped = []
    missing = []
    mismatched = []
    for s in manifest:
        path = os.path.join(LANDMARK_DIR, f"{s['session_id']}.npz")
        if not os.path.exists(path):
            missing.append(s["session_id"])
            continue
        data = np.load(path, allow_pickle=True)
        exercise = str(data["exercise"])
        if exercise.strip().lower() != s["exercise"].strip().lower():
            mismatched.append((s["session_id"], exercise, s["exercise"]))
            continue
        if "bench" in exercise.lower():
            skipped.append(s["session_id"])
            continue
        result = analyze_exercise(exercise, data["landmarks"], data["timestamps"])
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
    return rows, skipped, missing, mismatched


def write_features(rows: list):
    with open(FEATURES_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def find_disagreements(manifest: list, rows: list) -> list:
    """Cross-check the two label sources. A 'good' session where the rule engine
    flags reps is a possible false positive (regression in the thresholds); a
    fault-labeled session where NO rep gets flagged is a miss. Both are known to
    exist today (under-exaggerated demos) -- see test_engine_regression.py, which
    pins the current set so a NEW one shows up as a test failure, not a surprise.

    Returns a list of {session_id, person, exercise, label, kind, detail} dicts,
    one per disagreeing session (kind is "false_positive" or "missed_fault").
    """
    by_session = {}
    for r in rows:
        by_session.setdefault(r["session_id"], []).append(r)

    disagreements = []
    for s in manifest:
        sid = s["session_id"]
        reps = by_session.get(sid, [])
        flagged = [r for r in reps if r["rule_faults"]]
        if s["label"] == "good" and flagged:
            faults = Counter(f for r in flagged for f in r["rule_faults"].split(";"))
            disagreements.append({
                "session_id": sid, "person": s["person"], "exercise": s["exercise"],
                "label": s["label"], "kind": "false_positive",
                "detail": f"{len(flagged)}/{len(reps)} reps flagged {dict(faults)}",
            })
        elif s["label"] != "good" and reps and not flagged:
            disagreements.append({
                "session_id": sid, "person": s["person"], "exercise": s["exercise"],
                "label": s["label"], "kind": "missed_fault",
                "detail": f"0/{len(reps)} reps flagged",
            })
    return disagreements


def sanity_report(manifest: list, rows: list, skipped: list = (), missing: list = (),
                  mismatched: list = ()):
    analyzed_ids = {r["session_id"] for r in rows}
    print(f"\n=== Feature table: {len(rows)} reps from {len(analyzed_ids)} sessions -> {FEATURES_CSV}")
    if skipped:
        print(f"    skipped {len(skipped)} bench session(s) (parked, different schema): {skipped}")
    if missing:
        print(f"    !! {len(missing)} tagged session(s) have no .npz file: {missing}")
    for sid, npz_ex, csv_ex in mismatched:
        print(f"    !! session {sid} EXERCISE MISMATCH: .npz says '{npz_ex}', "
              f"subjects.csv says '{csv_ex}' -- excluded; re-tag before trusting it")

    by_person = Counter()
    by_exercise = Counter()
    by_label = Counter()
    # Count only sessions that actually produced rows, so session and rep counts agree.
    sessions_per_person = Counter()
    for s in manifest:
        if s["session_id"] in analyzed_ids:
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

    mismatched_ids = {sid for sid, _, _ in mismatched}
    zero_rep = [s["session_id"] for s in manifest
                if s["session_id"] not in analyzed_ids
                and s["session_id"] not in skipped
                and s["session_id"] not in missing
                and s["session_id"] not in mismatched_ids]
    if zero_rep:
        print(f"\n    !! sessions with ZERO reps segmented: {zero_rep}")

    print("\n    label vs rule-engine disagreements:")
    disagreements = find_disagreements(manifest, rows)
    if not disagreements:
        print("      none")
    for d in disagreements:
        tag = "possible false positive" if d["kind"] == "false_positive" else "fault missed"
        print(f"      session {d['session_id']} ({d['person']}, {d['exercise']}, "
              f"{d['label']}): {d['detail']}  <- {tag}")


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
    rows, skipped, missing, mismatched = build_rows(manifest)
    write_features(rows)
    sanity_report(manifest, rows, skipped, missing, mismatched)
    if "--smoke" in sys.argv:
        smoke_test(rows)


if __name__ == "__main__":
    main()
