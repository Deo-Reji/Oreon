"""Bench rep-segmentation tests on SYNTHETIC signals.

The real bench clips have no rep-count labels, so these build bar-height signals
with a known number of presses and assert the segmenter recovers it. That
separates "our maths is wrong" from "MediaPipe tracked the lifter badly" —
when a real clip miscounts, these still passing means the tracking is at fault.
"""
import sys
import os

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.exercises import (
    _segment_reps, _bench_working_range, _interp_short_gaps, BENCH_MIN_RANGE,
)


def make_press(n_reps: int, low: float = 0.1, high: float = 1.1,
               setup: float = -0.5, frames_per_rep: int = 40, setup_frames: int = 60):
    """A bar-height signal: flat un-rack well below the press, then n_reps cosine presses."""
    t = np.linspace(0, n_reps * 2 * np.pi, n_reps * frames_per_rep)
    mid, amp = (high + low) / 2, (high - low) / 2
    press = mid + amp * np.cos(t)  # starts at the top (lockout), dips to the chest
    return np.concatenate([np.full(setup_frames, setup), press]).astype(np.float32)


def test_working_range_excludes_the_unrack():
    bar = make_press(5)
    lo, hi = _bench_working_range(bar)
    # The -0.5 setup must not pull the low reference down with it.
    assert lo > 0.0, f"un-rack leaked into the working range (lo={lo})"
    assert 1.0 < hi < 1.2, f"top reference off (hi={hi})"


def test_counts_reps_with_a_deep_unrack_present():
    for n in (3, 5, 8):
        bar = make_press(n)
        lo, hi = _bench_working_range(bar)
        got = len(_segment_reps(bar, min_range=BENCH_MIN_RANGE, margin_frac=0.10, lo=lo, hi=hi))
        assert got == n, f"expected {n} reps, got {got}"


def test_whole_clip_percentiles_undercount_the_same_signal():
    """Pins the exact bug the working-range fix exists to solve.

    Modelled on real clip 64: the un-rack sits at -0.42 while the press oscillates
    entirely above 0.5, so the whole-clip bands land BELOW the press and the
    segmenter never sees a dip past its lower band. The press here (0.25-1.1) has
    ample travel; only the band placement is wrong.
    """
    bar = make_press(5, low=0.25, high=1.1, setup=-0.5)
    naive = len(_segment_reps(bar, min_range=BENCH_MIN_RANGE, margin_frac=0.10))
    lo, hi = _bench_working_range(bar)
    fixed = len(_segment_reps(bar, min_range=BENCH_MIN_RANGE, margin_frac=0.10, lo=lo, hi=hi))
    assert fixed == 5, f"working-range bands should recover all 5 reps, got {fixed}"
    assert naive < fixed, f"expected whole-clip bands to undercount, got {naive}"


def test_flat_signal_finds_no_reps():
    bar = np.full(200, 0.6, dtype=np.float32)
    lo, hi = _bench_working_range(bar)
    assert _segment_reps(bar, min_range=BENCH_MIN_RANGE, margin_frac=0.10, lo=lo, hi=hi) == []


def test_foreshortened_press_is_rejected_not_guessed():
    """A press whose travel is far too small to be real (camera angled down the body
    axis) must report nothing rather than invent reps from noise."""
    bar = make_press(5, low=0.50, high=0.68)
    lo, hi = _bench_working_range(bar)
    got = len(_segment_reps(bar, min_range=BENCH_MIN_RANGE, margin_frac=0.10, lo=lo, hi=hi))
    assert got == 0, f"expected 0 reps from a foreshortened clip, got {got}"


def test_short_gaps_bridged_long_gaps_left_alone():
    s = np.arange(20, dtype=np.float64)
    bad = np.zeros(20, bool)
    bad[5:7] = True    # 2-frame glitch -> repaired
    bad[10:17] = True  # 7-frame occlusion -> left raw
    corrupt = s.copy()
    corrupt[bad] = 99.0
    out = _interp_short_gaps(corrupt, bad, max_gap=3)
    assert np.allclose(out[5:7], s[5:7]), "short glitch should be repaired"
    assert np.allclose(out[10:17], 99.0), "long occlusion must not be invented"
