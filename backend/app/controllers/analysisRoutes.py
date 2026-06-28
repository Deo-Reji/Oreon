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
    video_bytes = await video.read()

    # video -> normalized, rep-segmented landmark sequence -> per-rep analysis
    seq = extract_pose_sequence(video_bytes)
    result = analyze_exercise(exercise, seq["landmarks"], seq["timestamps"])

    session = models.WorkoutSession(
        user_id=current_user.id,
        exercise_type=exercise,
        reps=result["reps"],
        form_score=result["form_score"],
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Persist the landmark sequence as training data (keyed by session id).
    storage.save_landmarks(session.id, seq, exercise, current_user.id)

    return {
        "status": "success",
        "session_id": session.id,
        "reps": result["reps"],
        "form_score": result["form_score"],
        "grade": result["grade"],
        "improvements": result["improvements"],
        "rep_details": result["rep_details"],
    }
