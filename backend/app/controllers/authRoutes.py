from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app import models
from app.services.authService import hash_password, verify_password, create_access_token

router = APIRouter()



class RegisterRequest(BaseModel):
    email: EmailStr  
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == body.email).first(): 
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(email=body.email, password_hash=hash_password(body.password))  
    db.add(user)     
    db.commit()      
    db.refresh(user) 
    return {"token": create_access_token(user.id)}  


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()  
    if not user or not verify_password(body.password, user.password_hash):  
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": create_access_token(user.id)} 
