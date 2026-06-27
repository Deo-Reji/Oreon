from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app import models
from app.controllers.analysisRoutes import router as analysis_router
from app.controllers.authRoutes import router as auth_router
from app.controllers.userRoutes import router as user_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Allow the React Native app (Expo/dev) to call the API.
# Tighten this to specific origins before production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth")
app.include_router(user_router, prefix="/api/users")
app.include_router(analysis_router, prefix="/api")


@app.get("/")
def health():
    return {"status": "ok"}
