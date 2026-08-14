from fastapi import APIRouter, Depends, HTTPException
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


@router.get("/me/sessions/{session_id}/reps")
def get_session_reps(
    session_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Scope by user_id too, not just session_id, so one user can't read another's reps.
    session = (
        db.query(models.WorkoutSession)
        .filter(models.WorkoutSession.id == session_id, models.WorkoutSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return [
        {
            "rep": r.rep_num,
            "depth_angle": r.depth_angle,
            "top_angle": r.top_angle,
            "rom": r.rom,
            "lean": r.lean,
            "drift": r.drift,
            "symmetry": r.symmetry,
            "flare": r.flare,
            "duration_s": r.duration_s,
            "faults": r.faults.split(";") if r.faults else [],
            "score": r.score,
            "short_vs_best": r.short_vs_best,
        }
        for r in session.rep_details
    ]
