"""Delete saved sessions (landmark .npz + DB row) by id.

For removing bad / false recordings without hunting through the folder.
Usage (from backend/, venv active):
    python cleanup_session.py 34
    python cleanup_session.py 34 35 36
"""
import os
import sys

from app.database import SessionLocal
from app import models

LANDMARK_DIR = os.path.join(os.path.dirname(__file__), "data", "landmarks")  


def delete_session(session_id: int):
    path = os.path.join(LANDMARK_DIR, f"{session_id}.npz")  
    if os.path.exists(path):
        os.remove(path)                                    
        print(f"  removed landmark file: {path}")
    else:
        print(f"  no landmark file for session {session_id}")

    db = SessionLocal()  
    try:
        row = db.query(models.WorkoutSession).filter(
            models.WorkoutSession.id == session_id
        ).first()                                         
        if row:
            db.delete(row)                                 
            db.commit()                                    
            print(f"  removed DB session {session_id}")
        else:
            print(f"  no DB row for session {session_id}")
    finally:
        db.close()  # always release the connection


def main():
    if len(sys.argv) < 2:                                  
        print("usage: python cleanup_session.py <session_id> [more ids...]")
        return
    for sid in sys.argv[1:]:                               
        print(f"session {sid}:")
        delete_session(int(sid))


if __name__ == "__main__":
    main()
