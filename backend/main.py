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
    allow_origins=["*"],      # any origin for now -- fine in dev, lock down before prod
    allow_credentials=True,
    allow_methods=["*"],      # allow every HTTP verb
    allow_headers=["*"],      # allow every header (we need Authorization)
)

app.include_router(auth_router, prefix="/api/auth")      # /api/auth/register, /api/auth/login
app.include_router(user_router, prefix="/api/users")     # /api/users/me, /api/users/me/sessions
app.include_router(analysis_router, prefix="/api")       # /api/analyze


@app.get("/")
def health():
    return {"status": "ok"}  # simple ping so you can confirm the server is up
