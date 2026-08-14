"""Persist landmark sequences per session.

These saved sequences are the project's ML training set: every analyzed clip
becomes a reusable, labeled-able sample. Videos are intentionally NOT stored
(privacy + size) — only the extracted pose landmarks.
"""
import os
import numpy as np


LANDMARK_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "landmarks") #path


def save_landmarks(session_id: int, seq: dict, exercise: str, user_id: int) -> str:
    """Write one session's raw landmark time series to a compressed .npz."""
    os.makedirs(LANDMARK_DIR, exist_ok=True)               # create data/landmarks on first save, no-op after
    path = os.path.join(LANDMARK_DIR, f"{session_id}.npz") # one file per session, named by its db id
    np.savez_compressed(                                   # gzip-compress all arrays into a single .npz
        path,
        landmarks=seq["landmarks"],      # (T, 33, 4)->(Time, Frames, 4 values) ->raw x,y,z,visibility- full pose data 
        timestamps=seq["timestamps"],    # (T,) array of timestamps- one timestamp per frame
        fps=seq["fps"],                  # original clip frame rate per second
        exercise=exercise,               
        user_id=user_id,                 
    )
    return path
