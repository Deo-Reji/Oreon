"""Regression test for the rule-based fault engine (exercises.py) against the
44 labeled research clips. Protects the threshold-tuning work already done:
if a future change to exercises.py silently breaks a subject/session that was
previously validated clean, this test fails instead of it going unnoticed.

Run from backend/ with the venv active: python -m pytest tests/
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from build_feature_table import load_manifest, build_rows, find_disagreements

# The disagreements the engine currently produces, as of the 2026-07-08 tuning
# pass (see backend's ADR/logic log). Each is a DATA problem (fault demo too
# mild) or an accepted trade-off (avani no-lockout vs tanav's good squat),
# not an engine bug -- see the corresponding session's note below. If a change
# to exercises.py makes one of these DISAPPEAR, that's an improvement, not a
# failure. If it produces a session_id NOT in this set, that's a regression.
KNOWN_DISAGREEMENTS = {
    71: "geo shallow-squat demo overlaps good depth",
    75: "nithin shallow-squat demo overlaps good depth",
    79: "nithin partial-curl demo under-exaggerated (inside good ROM)",
    83: "diya shallow-squat demo overlaps good depth",
    87: "diya partial-curl demo under-exaggerated (inside good ROM)",
    91: "avani shallow-squat demo overlaps good depth",
    93: "avani no-lockout demo overlaps tanav's good squat -- accepted trade",
    95: "avani partial-curl demo under-exaggerated (inside good ROM)",
    101: "raghu good curl set has 1 genuine swing rep (98/100 not 100/100)",
    103: "tanav shallow-squat demo overlaps good depth",
}


def test_no_new_engine_disagreements():
    manifest = load_manifest()
    rows, *_ = build_rows(manifest)
    disagreements = find_disagreements(manifest, rows)

    # session_id comes back as a str (CSV-sourced); KNOWN_DISAGREEMENTS keys are int.
    found_ids = {int(d["session_id"]) for d in disagreements}
    unexpected = found_ids - KNOWN_DISAGREEMENTS.keys()

    assert not unexpected, (
        f"Engine produced NEW label disagreements not in KNOWN_DISAGREEMENTS: "
        f"{[d for d in disagreements if int(d['session_id']) in unexpected]}. "
        f"If this is an intentional threshold change, update KNOWN_DISAGREEMENTS "
        f"with the reason; otherwise this is a regression."
    )


def test_all_good_sessions_score_100_or_have_a_known_reason():
    """Every session labeled 'good' should score 100 across all its reps unless
    its session_id is in KNOWN_DISAGREEMENTS (currently only 101, raghu)."""
    manifest = load_manifest()
    rows, *_ = build_rows(manifest)
    # session_id arrives from the CSV as a str; normalise to int on BOTH sides so
    # the lookup can't silently miss and make this test vacuous.
    by_session = {}
    for r in rows:
        by_session.setdefault(int(r["session_id"]), []).append(r)

    checked = 0
    bad = []
    for s in manifest:
        if s["label"] != "good":
            continue
        sid = int(s["session_id"])
        reps = by_session.get(sid, [])
        if not reps:
            continue
        checked += 1
        if any(r["rule_faults"] for r in reps) and sid not in KNOWN_DISAGREEMENTS:
            bad.append(sid)

    # Guard against the lookup silently matching nothing (how this test was broken
    # once already): if it examines no sessions it is not testing anything.
    assert checked >= 10, f"expected to examine the good sessions, only saw {checked}"
    assert not bad, f"Good sessions unexpectedly flagged with no known reason: {bad}"
