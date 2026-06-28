"""Persist landmark sequences per session.

These saved sequences are the project's ML training set: every analyzed clip
becomes a reusable, labeled-able sample. Videos are intentionally NOT stored
(privacy + size) — only the extracted pose landmarks.
"""
import os
import numpy as np

LANDMARK_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "landmarks")


def save_landmarks(session_id: int, seq: dict, exercise: str, user_id: int) -> str:
    """Write one session's raw landmark time series to a compressed .npz."""
    os.makedirs(LANDMARK_DIR, exist_ok=True)
    path = os.path.join(LANDMARK_DIR, f"{session_id}.npz")
    np.savez_compressed(
        path,
        landmarks=seq["landmarks"],      # (T, 33, 4) raw x,y,z,visibility
        timestamps=seq["timestamps"],    # (T,)
        fps=seq["fps"],
        exercise=exercise,
        user_id=user_id,
    )
    return path
