"""
Coqui XTTS v2 microservice entrypoint (Python 3.11).
Run: uvicorn main:app --host 0.0.0.0 --port 8001
"""
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

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
    return {"service": "tts-service-python311", "docs": "/docs"}
