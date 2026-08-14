from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
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
    sessions = relationship("WorkoutSession", back_populates="user")  # user.sessions lists all their workouts


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
