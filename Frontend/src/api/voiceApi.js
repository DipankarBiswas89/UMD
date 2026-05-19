import { API_PREFIX, apiUrl, resolveMediaUrl, voiceWebSocketUrl } from "./config.js";

async function parseError(res) {
  let detail = `Request failed (${res.status})`;
  try {
    const data = await res.json();
    if (data.detail) detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
  } catch {
    /* ignore */
  }
  throw new Error(detail);
}

export async function uploadRecording(blob, filename = "recording.webm") {
  const form = new FormData();
  form.append("file", blob, filename);
  const res = await fetch(apiUrl("/record"), { method: "POST", body: form });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function transcribeRecording(recordingId, language) {
  const form = new FormData();
  form.append("recording_id", recordingId);
  if (language) form.append("language", language);
  const res = await fetch(apiUrl("/transcribe"), { method: "POST", body: form });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function transcribeBlob(blob, filename = "recording.webm", language) {
  const form = new FormData();
  form.append("file", blob, filename);
  if (language) form.append("language", language);
  const res = await fetch(apiUrl("/transcribe"), { method: "POST", body: form });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function generateResponse(text) {
  const res = await fetch(apiUrl("/generate-response"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function generateVoice(text, language = "en") {
  const res = await fetch(apiUrl("/generate-voice"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language }),
  });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function voiceTurn(recordingId, language) {
  const res = await fetch(apiUrl("/voice-turn"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ recording_id: recordingId, language }),
  });
  if (!res.ok) await parseError(res);
  return res.json();
}

export function resolveAudioUrl(audioUrl) {
  return resolveMediaUrl(audioUrl);
}

export async function fetchMessages() {
  const res = await fetch(apiUrl("/messages"));
  if (!res.ok) return [];
  const data = await res.json();
  return data.messages || [];
}

export async function fetchVoiceStatus() {
  const res = await fetch(apiUrl("/voice-status"));
  if (!res.ok) return null;
  return res.json();
}

export async function uploadVoiceFile(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(apiUrl("/upload-voice"), { method: "POST", body: form });
  if (!res.ok) await parseError(res);
  return res.json();
}

export function createVoiceWebSocket(onMessage) {
  const ws = new WebSocket(voiceWebSocketUrl());
  ws.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data));
    } catch {
      /* ignore */
    }
  };
  return ws;
}

// Re-export for components that need the prefix
export { API_PREFIX };
