"""
Coqui XTTS v2 microservice (Python 3.11).
Railway: binds to $PORT; /health returns 200 immediately; model loads in background.
"""
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.logging_config import setup_logging
from app.routes import router

setup_logging()

app = FastAPI(
    title="TTS Voice Cloning Service",
    description="Isolated Coqui XTTS v2 microservice (Python 3.11)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
async def startup_event():
    from app.routes import startup_warmup

    await startup_warmup()


@app.get("/")
def root():
    return {
        "service": "tts-service-python311",
        "health": "/health",
        "ready": "/health/ready",
        "docs": "/docs",
    }
