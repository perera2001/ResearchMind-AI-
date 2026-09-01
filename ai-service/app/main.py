from fastapi import FastAPI

from app.auth import models as auth_models
from app.auth.routes import router as auth_router
from app.database import Base, engine


auth_models.Base.metadata.create_all(
    bind=engine,
)

app = FastAPI(
    title="ResearchMind AI Service",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ResearchMind AI Service",
    }


app.include_router(auth_router)