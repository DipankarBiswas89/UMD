"""
AI response generation via Groq (reuses conversation history from database).
"""
from __future__ import annotations

import os
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal, Message
from sqlalchemy import select


def get_groq_api_key() -> str | None:
    return os.getenv("GROQ_API_KEY")


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
            "content": (
                "You are a helpful real-time voice assistant. "
                "Keep answers concise and conversational (2-4 sentences unless asked for detail)."
            ),
        }
    ]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": question})
    return messages


async def save_message_async(text: str, sender: str) -> None:
    try:
        async with AsyncSessionLocal() as session:
            session.add(Message(text=text, sender=sender))
            await session.commit()
    except Exception as exc:
        print(f"⚠️ Async save failed for {sender}: {exc}")


async def generate_ai_response(
    question: str,
    db: AsyncSession,
    *,
    http_client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    api_key = get_groq_api_key()
    if not api_key:
        return {
            "response": "Backend is running but GROQ_API_KEY is not set.",
            "error": "missing_api_key",
        }

    try:
        history = await load_conversation_history(db, limit=12)
    except Exception:
        history = []

    messages = build_prompt_messages(question, history)
    client = http_client
    owns_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=httpx.Timeout(20.0))
        owns_client = True

    try:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
                "temperature": 0.6,
                "max_tokens": int(os.getenv("GROQ_MAX_TOKENS", "256")),
                "messages": messages,
            },
        )
        response.raise_for_status()
        result = response.json()
        answer = (
            result.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "I'm unable to retrieve a response right now.")
        )
        answer = answer.strip()
        import asyncio

        asyncio.create_task(save_message_async(question, "user"))
        asyncio.create_task(save_message_async(answer, "bot"))
        return {"response": answer}
    except httpx.HTTPStatusError as exc:
        return {
            "response": "The AI service returned an error. Please try again.",
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "response": "There was an error contacting the AI service.",
            "error": str(exc),
        }
    finally:
        if owns_client:
            await client.aclose()
