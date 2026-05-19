"""
AI Voice Assistant API — production entrypoint for Render (Python 3.11.9 via runtime.txt).
"""
from __future__ import annotations

import logging
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("main")

from fastapi import FastAPI, HTTPException, Query, Depends, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db, init_db, Message, AsyncSessionLocal, check_db_connection
from pathlib import Path
import httpx
import shutil
from pydantic import BaseModel
import hashlib
import asyncio
import time
import json
# Load .env keys robustly (relative to this file), so it works regardless of CWD
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

# Defer reading secrets until request time to avoid stale values
def get_env(name: str, default: str | None = None) -> str | None:
	return os.getenv(name, default)


def create_groq_http_client(timeout_seconds: float = 15.0) -> httpx.AsyncClient:
	"""Create a Groq HTTP client with HTTP/2 when available, else fallback."""
	try:
		return httpx.AsyncClient(
			timeout=httpx.Timeout(timeout_seconds),
			limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
			http2=True,
		)
	except ImportError:
		print("⚠️ 'h2' not installed; using HTTP/1.1 client for Groq.")
		return httpx.AsyncClient(
			timeout=httpx.Timeout(timeout_seconds),
			limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
		)


async def save_message_async(text: str, sender: str) -> None:
	try:
		async with AsyncSessionLocal() as session:
			session.add(Message(text=text, sender=sender))
			await session.commit()
	except Exception as e:
		print(f"⚠️ Async save failed for {sender}: {e}")


async def load_conversation_history(db: AsyncSession, limit: int = 12) -> list[dict[str, str]]:
	conversation_history: list[dict[str, str]] = []
	result = await db.execute(
		select(Message.sender, Message.text).order_by(Message.created_at.desc()).limit(limit)
	)
	recent_messages = list(reversed(result.all()))
	for sender, text in recent_messages:
		role = "user" if sender == "user" else "assistant"
		conversation_history.append({"role": role, "content": text})
	return conversation_history


def build_prompt_messages(question: str, conversation_history: list[dict[str, str]]) -> list[dict[str, str]]:
	messages = [
		{
			"role": "system",
			"content": "You are a helpful assistant. Use the conversation history to provide context-aware responses.",
		}
	]
	messages.extend(conversation_history)
	messages.append({"role": "user", "content": question})
	return messages

# Import TTS service after environment is loaded
from tts_service import get_tts_service, VOICE_DIR, is_valid_voice_sample_name
from api.routes.voice_assistant import router as voice_router
from utils.paths import GENERATED_AUDIO_DIR
from utils.whisper_service import warmup_whisper

# Setup FastAPI
app = FastAPI(title="Real-Time AI Voice Assistant")
groq_http_client: httpx.AsyncClient | None = None
_audio_generation_locks: dict[str, asyncio.Lock] = {}

def _cors_origins() -> list[str]:
	origins: list[str] = [
		"http://localhost:5173",
		"http://127.0.0.1:5173",
	]
	for key in ("FRONTEND_URL", "VERCEL_URL"):
		val = os.getenv(key, "").strip().rstrip("/")
		if val:
			if not val.startswith("http"):
				val = f"https://{val}"
			origins.append(val)
	extra = os.getenv("CORS_ORIGINS", "")
	if extra:
		origins.extend(o.strip().rstrip("/") for o in extra.split(",") if o.strip())
	return list(dict.fromkeys(origins))


app.add_middleware(
	CORSMiddleware,
	allow_origins=_cors_origins(),
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Create voices directory if it doesn't exist (already created in tts_service, but ensure it exists)
VOICE_DIR.mkdir(exist_ok=True)
GENERATED_AUDIO_DIR.mkdir(exist_ok=True)

# Voice assistant REST + WebSocket (register before static mounts)
app.include_router(voice_router)

# Legacy cached XTTS outputs in voices/
app.mount("/legacy-audio", StaticFiles(directory=str(VOICE_DIR)), name="legacy-audio")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
	"""Production startup: DB, tables, XTTS, Whisper."""
	global groq_http_client
	logger.info("Starting AI Voice Assistant API (Python %s)", sys.version.split()[0])

	if not await check_db_connection():
		logger.error("Database connection failed — check DATABASE_URL")
		if os.getenv("RENDER"):
			raise RuntimeError("Database connection failed on startup")
		return
	logger.info("Database connected successfully")

	try:
		await init_db()
		logger.info("Database tables initialized successfully")
	except Exception as e:
		logger.error("Database table init failed: %s", e)

	try:
		tts_service = get_tts_service()
		warmup_start = time.perf_counter()
		await tts_service.warmup_coqui()
		if tts_service._local_coqui_ready:
			logger.info("XTTS ready (local in-process — dev only)")
		elif tts_service._tts_service_available:
			await tts_service.sync_speaker_to_microservice()
			logger.info("TTS microservice connected (Railway / local :8001)")
		else:
			logger.warning(
				"Voice cloning unavailable — set TTS_SERVICE_URL to Railway; else Edge TTS fallback"
			)
		logger.info("TTS warmup finished in %.1fs", time.perf_counter() - warmup_start)
	except Exception as e:
		logger.error("TTS initialization warning: %s", e)

	if os.getenv("SKIP_WHISPER_WARMUP", "").lower() not in ("1", "true", "yes"):
		try:
			whisper_start = time.perf_counter()
			await warmup_whisper()
			logger.info("Whisper warmup complete in %.1fs", time.perf_counter() - whisper_start)
		except Exception as whisper_error:
			logger.warning("Whisper warmup skipped: %s", whisper_error)
	else:
		logger.info("Whisper warmup skipped (SKIP_WHISPER_WARMUP)")

	try:
		groq_http_client = create_groq_http_client(timeout_seconds=15.0)
		logger.info("Groq HTTP client ready")
	except Exception as e:
		logger.warning("Groq HTTP client failed: %s", e)

	logger.info("FastAPI server ready")


@app.on_event("shutdown")
async def shutdown_event():
	"""Close shared clients on shutdown."""
	global groq_http_client
	if groq_http_client is not None:
		await groq_http_client.aclose()
		groq_http_client = None

@app.get("/")
def home():
	return {"message": "Groq + Custom Voice Assistant is active 🎙️"}

@app.get("/health")
async def health():
	from utils.coqui_local import is_coqui_installed

	tts = get_tts_service()
	micro_ok = await tts.check_tts_service()
	return {
		"ok": True,
		"python": sys.version.split()[0],
		"database": await check_db_connection(),
		"coqui_installed": is_coqui_installed(),
		"xtts_local": bool(tts._local_coqui_ready),
		"tts_microservice_healthy": micro_ok,
		"tts_service_url": os.getenv("TTS_SERVICE_URL", ""),
		"tts_backend": os.getenv("TTS_BACKEND") or ("microservice" if os.getenv("RENDER") else "auto"),
	}

@app.get("/home")
def res():
	return {"Hello": "Welcome to the Groq + Custom Voice Assistant API!"}

@app.get("/ask-and-speak")
async def ask_and_speak(
	question: str = Query(..., description="The user's question"),
	db: AsyncSession = Depends(get_db)
):
	global groq_http_client
	request_start = time.perf_counter()
	groq_api_key = get_env("GROQ_API_KEY")
	# If no API key is configured, respond gracefully so the frontend doesn't break
	if not groq_api_key:
		fallback = "Backend is running but GROQ_API_KEY is not set."
		return JSONResponse(content={"answer": fallback})
	
	print("❓ Question:", question)

	# 📚 Retrieve conversation history from database BEFORE saving current question
	# This ensures we get the full context without including the current question
	try:
		history_start = time.perf_counter()
		conversation_history = await load_conversation_history(db, limit=12)
		print(f"📚 Loaded {len(conversation_history)} previous messages for context")
		print(f"⏱️ History fetch took {(time.perf_counter() - history_start) * 1000:.0f} ms")
	except Exception as e:
		print(f"⚠️ Error loading conversation history: {e}")
		conversation_history = []
		# Continue without history if there's an error
	
	# 1️⃣ Ask Groq API with conversation history
	answer = None
	try:
		groq_start = time.perf_counter()
		messages = build_prompt_messages(question, conversation_history)
		
		if groq_http_client is None:
			groq_http_client = create_groq_http_client(timeout_seconds=15.0)

		groq_response = await groq_http_client.post(
			"https://api.groq.com/openai/v1/chat/completions",
			headers={
				"Authorization": f"Bearer {groq_api_key}",
				"Content-Type": "application/json",
				"Accept": "application/json",
			},
			json={
				"model": "llama-3.1-8b-instant",
				"temperature": 0.6,
				"max_tokens": 192,
				"stream": False,
				"messages": messages
			}
		)
		groq_response.raise_for_status()
		result = groq_response.json()
		answer = (
			result.get("choices", [{}])[0]
			.get("message", {})
			.get("content", "I'm unable to retrieve a response right now.")
		)
		print("🤖 Answer:", answer.strip())
		print(f"⏱️ Groq call took {(time.perf_counter() - groq_start) * 1000:.0f} ms")
	except httpx.HTTPStatusError as e:
		# Surface upstream status code in logs, but keep UI-friendly message
		status = getattr(e.response, "status_code", None)
		body = None
		try:
			body = e.response.text
		except Exception:
			body = "<no body>"
		print("GROQ API HTTP error:", status, str(e))
		print("GROQ API response body:", body)
		answer = "The AI service returned an error. Please try again."
	except Exception as e:
		print("GROQ API unexpected error:", str(e))
		answer = "There was an error contacting the AI service."
	
	# Save messages asynchronously so user gets response immediately.
	try:
		if question:
			asyncio.create_task(save_message_async(question, "user"))
		if answer:
			asyncio.create_task(save_message_async(answer.strip(), "bot"))
	except Exception as e:
		print(f"⚠️ Failed to schedule async message persistence: {e}")
	
	# Return the answer immediately (don't wait for TTS here).
	# Frontend will request audio separately, so the UI feels fast.
	total_ms = (time.perf_counter() - request_start) * 1000
	print(f"⏱️ /ask-and-speak total time: {total_ms:.0f} ms")
	return JSONResponse(content={
		"answer": answer.strip() if answer else "No response generated",
		"audio_url": None
	})


@app.get("/ask-and-stream")
async def ask_and_stream(
	question: str = Query(..., description="The user's question"),
	db: AsyncSession = Depends(get_db)
):
	global groq_http_client
	groq_api_key = get_env("GROQ_API_KEY")
	if not groq_api_key:
		async def fallback_stream():
			yield json.dumps({"type": "delta", "text": "Backend is running but GROQ_API_KEY is not set."}) + "\n"
			yield json.dumps({"type": "done"}) + "\n"
		return StreamingResponse(fallback_stream(), media_type="application/x-ndjson")

	if groq_http_client is None:
		groq_http_client = create_groq_http_client(timeout_seconds=30.0)

	try:
		conversation_history = await load_conversation_history(db, limit=12)
	except Exception:
		conversation_history = []

	messages = build_prompt_messages(question, conversation_history)
	print(f"❓ [stream] Question: {question}")

	async def stream_generator():
		full_text = ""
		try:
			async with groq_http_client.stream(
				"POST",
				"https://api.groq.com/openai/v1/chat/completions",
				headers={
					"Authorization": f"Bearer {groq_api_key}",
					"Content-Type": "application/json",
					"Accept": "text/event-stream",
				},
				json={
					"model": "llama-3.1-8b-instant",
					"temperature": 0.6,
					"max_tokens": 192,
					"stream": True,
					"messages": messages,
				},
			) as response:
				response.raise_for_status()
				async for line in response.aiter_lines():
					if not line.startswith("data: "):
						continue
					payload = line[6:].strip()
					if payload == "[DONE]":
						break
					try:
						chunk = json.loads(payload)
						delta = (
							chunk.get("choices", [{}])[0]
							.get("delta", {})
							.get("content", "")
						)
						if delta:
							full_text += delta
							yield json.dumps({"type": "delta", "text": delta}) + "\n"
					except Exception:
						continue

			final_text = full_text.strip() or "No response generated"
			asyncio.create_task(save_message_async(question, "user"))
			asyncio.create_task(save_message_async(final_text, "bot"))
			yield json.dumps({"type": "done", "answer": final_text}) + "\n"
		except Exception as e:
			print(f"⚠️ Stream endpoint error: {e}")
			yield json.dumps({"type": "error", "message": "Streaming failed. Please retry."}) + "\n"

	return StreamingResponse(stream_generator(), media_type="application/x-ndjson")

class GenerateAudioRequest(BaseModel):
	text: str

@app.post("/generate-audio")
async def generate_audio(req: GenerateAudioRequest):
	"""
	Generate custom-voice audio for a given text.
	This is separated from /ask-and-speak so chat responses return fast.
	"""
	text = (req.text or "").strip()
	if not text:
		raise HTTPException(status_code=400, detail="Missing text")
	print(f"🔊 /generate-audio request received (len={len(text)})")
	request_start = time.perf_counter()

	tts_service = get_tts_service()
	voice_sample = tts_service.voice_sample_path
	voice_tag = ""
	try:
		if voice_sample and voice_sample.exists():
			st = voice_sample.stat()
			voice_tag = f"{voice_sample.name}:{int(st.st_mtime)}:{st.st_size}"
	except Exception:
		voice_tag = voice_sample.name if voice_sample else ""

	# Cache key includes voice identity + text, so changing voice invalidates cache.
	key = hashlib.sha1((voice_tag + "\n" + text).encode("utf-8", errors="ignore")).hexdigest()
	out_path = VOICE_DIR / f"output_{key}.wav"

	# If cached file exists, return immediately.
	if out_path.exists():
		print(f"⚡ Returning cached audio: {out_path.name}")
		return JSONResponse(content={"audio_url": f"/legacy-audio/{out_path.name}", "cached": True})

	try:
		lock = _audio_generation_locks.setdefault(key, asyncio.Lock())
		async with lock:
			# Another request may have generated this file while we were waiting.
			if out_path.exists():
				print(f"⚡ Returning freshly cached audio: {out_path.name}")
				return JSONResponse(content={"audio_url": f"/legacy-audio/{out_path.name}", "cached": True})
			audio_path = await tts_service.generate_speech(text, output_path=out_path)
		_audio_generation_locks.pop(key, None)
		print(f"✅ Generated new audio: {audio_path.name}")
		total_ms = (time.perf_counter() - request_start) * 1000
		print(f"⏱️ /generate-audio total time: {total_ms:.0f} ms")
		return JSONResponse(content={"audio_url": f"/legacy-audio/{audio_path.name}", "cached": False})
	except asyncio.CancelledError:
		# Happens when server is interrupted (e.g., Ctrl+C) during long TTS generation.
		# Return a clean response instead of noisy traceback logs.
		print("⚠️ Audio generation cancelled (server shutdown or request cancelled).")
		raise HTTPException(status_code=503, detail="Audio generation was cancelled. Please retry.")
	except Exception as e:
		_audio_generation_locks.pop(key, None)
		print(f"❌ ERROR generating audio: {e}")
		raise HTTPException(status_code=500, detail=f"Audio generation failed: {e}")


@app.get("/messages")
async def get_messages(
	limit: int = Query(100, description="Maximum number of messages to retrieve"),
	db: AsyncSession = Depends(get_db)
):
	"""Retrieve stored messages from the database."""
	try:
		# Query messages ordered by creation time (most recent first)
		result = await db.execute(
			select(Message).order_by(Message.created_at.desc()).limit(limit)
		)
		messages = result.scalars().all()
		
		# Convert to list of dictionaries and reverse to show oldest first
		messages_list = [
			{
				"id": msg.id,
				"text": msg.text,
				"sender": msg.sender,
				"created_at": msg.created_at.isoformat() if msg.created_at else None
			}
			for msg in reversed(messages)
		]
		
		return JSONResponse(content={"messages": messages_list})
	except Exception as e:
		print(f"⚠️ Error retrieving messages: {e}")
		return JSONResponse(
			status_code=500,
			content={"error": "Failed to retrieve messages", "messages": []}
		)

@app.post("/upload-voice")
async def upload_voice(file: UploadFile = File(...)):
	"""
	Upload a voice sample or model file.
	
	Supported formats:
	- Voice samples: .wav, .mp3, .flac (for voice cloning)
	- Voice models: .pth (Coqui TTS), .onnx (Piper TTS)
	"""
	try:
		# Validate file extension
		file_ext = Path(file.filename).suffix.lower()
		allowed_extensions = [".wav", ".mp3", ".flac", ".pth", ".onnx"]
		
		if file_ext not in allowed_extensions:
			raise HTTPException(
				status_code=400,
				detail=f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
			)

		if file_ext in [".wav", ".mp3", ".flac"] and not is_valid_voice_sample_name(file.filename):
			raise HTTPException(
				status_code=400,
				detail=(
					f"'{file.filename}' looks like generated audio. "
					"Upload a clean speaker reference (e.g. speaker.wav), not an AI output file."
				),
			)
		
		# Save file to voices directory
		file_path = VOICE_DIR / file.filename
		
		with open(file_path, "wb") as buffer:
			shutil.copyfileobj(file.file, buffer)
		
		# Update TTS service with the new voice
		tts_service = get_tts_service()
		if file_ext in [".wav", ".mp3", ".flac"]:
			tts_service.set_voice_sample(file_path)
			try:
				await tts_service.sync_speaker_to_microservice()
			except Exception as sync_error:
				print(f"⚠️ TTS microservice speaker sync failed: {sync_error}")
			message = f"Voice sample uploaded successfully: {file.filename}"
		else:
			tts_service.set_voice_model(file_path)
			message = f"Voice model uploaded successfully: {file.filename}"
		
		print(f"✅ {message}")
		
		return JSONResponse(content={
			"message": message,
			"filename": file.filename,
			"file_type": "sample" if file_ext in [".wav", ".mp3", ".flac"] else "model"
		})
	except HTTPException:
		raise
	except Exception as e:
		print(f"⚠️ Error uploading voice file: {e}")
		raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/voice-status")
async def get_voice_status():
	"""Get the status of the current voice configuration"""
	try:
		from utils.coqui_local import is_coqui_installed

		tts_service = get_tts_service()
		micro_ok = await tts_service.check_tts_service()
		cloning_ready = bool(tts_service._local_coqui_ready or micro_ok)
		return JSONResponse(content={
			"voice_model": str(tts_service.voice_model_path) if tts_service.voice_model_path else None,
			"voice_sample": str(tts_service.voice_sample_path) if tts_service.voice_sample_path else None,
			"tts_backend": os.getenv("TTS_BACKEND") or ("microservice" if os.getenv("RENDER") else "auto"),
			"coqui_installed": is_coqui_installed(),
			"xtts_local": bool(tts_service._local_coqui_ready),
			"tts_microservice_healthy": micro_ok,
			"tts_service_url": os.getenv("TTS_SERVICE_URL", ""),
			"voice_cloning_ready": cloning_ready,
			"voices_directory": str(VOICE_DIR),
		})
	except Exception as e:
		return JSONResponse(
			status_code=500,
			content={"error": f"Error getting voice status: {str(e)}"}
		)