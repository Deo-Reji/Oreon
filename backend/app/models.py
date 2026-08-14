from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

#This is how the tables for the data I am storing in sql are made

#This is the simple user table and everything builds off of this
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)               # unique row id, auto-incremented
    email = Column(String, unique=True, index=True, nullable=False)  # login handle, no duplicates allowed
    password_hash = Column(String, nullable=False)                   # bcrypt hash, never the raw password
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # stamped once when the row is first inserted

    # relationship between user and workoutSession tables
    # cascade: deleting a user deletes their sessions (and, in turn, those sessions'
    # rep rows) instead of trying to orphan them -- user_id is NOT NULL, so without
    # this SQLAlchemy's default "set the FK to NULL" raises IntegrityError.
    sessions = relationship("WorkoutSession", back_populates="user",
                            cascade="all, delete-orphan")  # user.sessions lists all their workouts


#This is a table of exercises a user has completed
class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id = Column(Integer, primary_key=True, index=True)                 # unique session id
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # which user this session belongs to
    exercise_type = Column(String)                                     # e.g. "squat" / "bench press"
    reps = Column(Integer)                                             # how many reps were counted
    form_score = Column(Integer)                                       # 0-100 form grade for the set
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # when the session was analyzed

    # reverse of above
    user = relationship("User", back_populates="sessions")  # session.user gets back to the owner
    # cascade is REQUIRED here, not cosmetic: cleanup_session.py deletes WorkoutSession
    # rows directly, and rep_details.session_id is NOT NULL. Without the cascade,
    # SQLAlchemy tries to NULL the child FK on delete and raises IntegrityError.
    # order_by is not cosmetic: without it row order is whatever the DB returns, so
    # the API could hand the client rep 4 before rep 1.
    rep_details = relationship("RepDetail", back_populates="session",
                               cascade="all, delete-orphan",
                               order_by="RepDetail.rep_num")  # session.rep_details lists every rep


# One row per rep within a session -- the per-rep numbers analyze_exercise()
# computes (angles, fault verdicts, self-cal flag) were previously returned to
# the client only and discarded server-side. Persisting them is what turns real
# user sessions into future training data, the same way the research .npz
# clips are, instead of only the aggregate reps/form_score surviving.
class RepDetail(Base):
    __tablename__ = "rep_details"

    id = Column(Integer, primary_key=True, index=True)
    # ondelete CASCADE is the DB-level twin of the relationship cascade above -- it
    # covers raw SQL deletes that never go through the ORM.
    session_id = Column(Integer, ForeignKey("workout_sessions.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    rep_num = Column(Integer, nullable=False)
    depth_angle = Column(Float)
    top_angle = Column(Float)
    rom = Column(Float)
    lean = Column(Float, nullable=True)      # squat only
    drift = Column(Float, nullable=True)     # squat/curl swing metric
    symmetry = Column(Float, nullable=True)  # bench only
    flare = Column(Float, nullable=True)     # bench only
    duration_s = Column(Float)
    faults = Column(String)  # semicolon-joined fault labels, e.g. "Excessive forward lean"
    score = Column(Integer)
    short_vs_best = Column(Boolean, default=False)  # self-cal flag: cut short vs the lifter's own best rep

    session = relationship("WorkoutSession", back_populates="rep_details")
