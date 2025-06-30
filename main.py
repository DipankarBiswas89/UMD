from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
import os
import httpx

# Load .env keys
load_dotenv("secret.env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TTS_API_KEY = os.getenv("TTS_API_KEY")
AGENT_ID = os.getenv("AGENT_ID")

# Setup FastAPI
app = FastAPI()

@app.get("/")
def home():
    return {"message": "Groq + ElevenLabs Voice Assistant is active 🎙️"}

@app.get("/ask-and-speak")
async def ask_and_speak(question: str):
    if not GROQ_API_KEY or not TTS_API_KEY or not AGENT_ID:
        raise HTTPException(status_code=500, detail="Missing keys")

    print("❓ Question:", question)

    # 1️⃣ Ask Groq API
    try:
        async with httpx.AsyncClient() as client:
            groq_response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama3-8b-8192",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": question}
                    ]
                }
            )
            groq_response.raise_for_status()
            result = groq_response.json()
            answer = result["choices"][0]["message"]["content"]
            print("🤖 Answer:", answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GROQ API error: {str(e)}")

    # ✂️ Optional: truncate answer for TTS
    if len(answer) > 600:
        answer = answer[:600] + "..."

    # 2️⃣ Generate voice using ElevenLabs
    try:
        client = ElevenLabs(api_key=TTS_API_KEY)
        audio_stream = client.generate(
            text=answer,
            voice=AGENT_ID,
            model="eleven_monolingual_v1"
        )
        with open("output.wav", "wb") as f:
             for chunk in audio_stream:
                 f.write(chunk)
        print("✅ Voice generated")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ElevenLabs error: {str(e)}")

    return FileResponse("output.wav", media_type="audio/wav")
