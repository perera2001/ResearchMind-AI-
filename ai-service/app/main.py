from fastapi import FastAPI

from app.internal.routes import router as internal_router


app = FastAPI(
    title="ResearchMind AI Service",
    version="2.0.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ResearchMind AI Service",
    }


app.include_router(internal_router)
