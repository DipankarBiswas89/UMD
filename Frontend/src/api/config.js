/**
 * API base URL:
 * - Dev: empty → use Vite proxy at /api
 * - Production (Vercel): set VITE_API_URL=https://your-backend.onrender.com
 */
const raw = (import.meta.env.VITE_API_URL || "").trim().replace(/\/$/, "");

export const API_BASE = raw;

/** Prefix for REST calls (dev uses /api proxy). */
export const API_PREFIX = API_BASE || "/api";

export function apiUrl(path) {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${API_PREFIX}${p}`;
}

export function resolveMediaUrl(path) {
  if (!path) return null;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  if (API_BASE) return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
  return `${API_PREFIX}${path}`;
}

export function voiceWebSocketUrl() {
  if (API_BASE) {
    const u = new URL(API_BASE);
    const protocol = u.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${u.host}/ws/voice`;
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/api/ws/voice`;
}
