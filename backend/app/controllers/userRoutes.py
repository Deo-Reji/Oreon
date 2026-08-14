from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app import models

router = APIRouter()


@router.get("/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at,
    }


@router.get("/me/sessions")
def get_sessions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = (
        db.query(models.WorkoutSession)
        .filter(models.WorkoutSession.user_id == current_user.id)  
        .order_by(models.WorkoutSession.created_at.desc())         
        .all()
    )
    return [
        {
            "id": s.id,
            "exercise_type": s.exercise_type,
            "reps": s.reps,
            "form_score": s.form_score,
            "created_at": s.created_at,
        }
        for s in sessions
    ]
