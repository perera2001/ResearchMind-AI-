from fastapi import FastAPI

from app.auth.routes import router as auth_router
from app.database import Base, engine
from app.documents.routes import router as document_router
from app.memory.routes import router as chat_router

import app.auth.models
import app.documents.models
import app.memory.models


Base.metadata.create_all(
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
app.include_router(document_router)
app.include_router(chat_router)