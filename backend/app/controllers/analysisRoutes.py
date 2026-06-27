from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.services.poseEstimation import analyze_video
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
    result = analyze_video(video_bytes, exercise=exercise)

    session = models.WorkoutSession(
        user_id=current_user.id,
        exercise_type=exercise,
        reps=result["reps"],
        form_score=result["form_score"],
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {"status": "success", "session_id": session.id, **result}
