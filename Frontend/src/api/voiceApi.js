const API = "/api";

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
  const res = await fetch(`${API}/record`, { method: "POST", body: form });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function transcribeRecording(recordingId, language) {
  const form = new FormData();
  form.append("recording_id", recordingId);
  if (language) form.append("language", language);
  const res = await fetch(`${API}/transcribe`, { method: "POST", body: form });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function transcribeBlob(blob, filename = "recording.webm", language) {
  const form = new FormData();
  form.append("file", blob, filename);
  if (language) form.append("language", language);
  const res = await fetch(`${API}/transcribe`, { method: "POST", body: form });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function generateResponse(text) {
  const res = await fetch(`${API}/generate-response`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function generateVoice(text, language = "en") {
  const res = await fetch(`${API}/generate-voice`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language }),
  });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function voiceTurn(recordingId, language) {
  const res = await fetch(`${API}/voice-turn`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ recording_id: recordingId, language }),
  });
  if (!res.ok) await parseError(res);
  return res.json();
}

export function resolveAudioUrl(audioUrl) {
  if (!audioUrl) return null;
  if (audioUrl.startsWith("http")) return audioUrl;
  return `${API}${audioUrl}`;
}

export async function fetchMessages() {
  const res = await fetch(`${API}/messages`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.messages || [];
}

export async function fetchVoiceStatus() {
  const res = await fetch(`${API}/voice-status`);
  if (!res.ok) return null;
  return res.json();
}

export async function uploadVoiceFile(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API}/upload-voice`, { method: "POST", body: form });
  if (!res.ok) await parseError(res);
  return res.json();
}

export function createVoiceWebSocket(onMessage) {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  const ws = new WebSocket(`${protocol}//${host}${API}/ws/voice`);
  ws.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data));
    } catch {
      /* ignore */
    }
  };
  return ws;
}
