const LABELS = {
  idle: "Tap the mic to speak",
  listening: "Listening…",
  processing: "Processing…",
  speaking: "Speaking…",
};

export default function StatusIndicator({ status }) {
  return (
    <div className={`status-pill status-${status}`} role="status" aria-live="polite">
      <span className="status-dot" />
      <span>{LABELS[status] || status}</span>
    </div>
  );
}
