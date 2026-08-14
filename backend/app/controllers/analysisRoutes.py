from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.services.posePipeline import extract_pose_sequence
from app.services.exercises import analyze_exercise
from app.services import storage
from app import models

router = APIRouter()


@router.post("/analyze")
async def analyze(
    video: UploadFile = File(...),                              
    exercise: str = Form(default="squat"),                      
    current_user: models.User = Depends(get_current_user),     
    db: Session = Depends(get_db),                             
):
    #This loads the full video into memory as bytes
    video_bytes = await video.read()

    # We run the MediaPipe pose estimation frame-by-frame to build a (T, 33, 4) landmark array,
    # then segment that signal into reps and score each one with rule-based fault detection.
    seq = extract_pose_sequence(video_bytes)
    result = analyze_exercise(exercise, seq["landmarks"], seq["timestamps"])

    # This writes the high-level summaries (rep count + form score) to the DB.
    # Raw per-rep breakdowns are kept in `result` and returned to the client but not stored.
    session = models.WorkoutSession(
        user_id=current_user.id,
        exercise_type=exercise,
        reps=result["reps"],
        form_score=result["form_score"],
    )
    db.add(session)

    # flush assigns session.id (DB PK) without committing the transaction, so if
    # save_landmarks raises below the whole thing rolls back on session close.
    db.flush()
    db.refresh(session)

    # Save the raw landmark time series (not the video) to disk as a compressed .npz;
    storage.save_landmarks(session.id, seq, exercise, current_user.id)

    # Commit only after the landmark file is safely written — both succeed or neither does.
    db.commit()

    return {
        "status": "success",
        "session_id": session.id,
        "reps": result["reps"],
        "form_score": result["form_score"],
        "grade": result["grade"],
        "improvements": result["improvements"],
        "rep_details": result["rep_details"],
        "self_calibration": result["self_calibration"],
    }
