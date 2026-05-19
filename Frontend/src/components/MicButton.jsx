import Waveform from "./Waveform";

export default function MicButton({ isRecording, status, onClick, disabled }) {
  const listening = isRecording || status === "listening";
  return (
    <button
      type="button"
      className={`mic-btn ${listening ? "mic-btn-active" : ""}`}
      onClick={onClick}
      disabled={disabled}
      aria-label={listening ? "Stop recording" : "Start recording"}
    >
      <span className="mic-ring mic-ring-1" />
      <span className="mic-ring mic-ring-2" />
      <span className="mic-icon">{listening ? "■" : "🎤"}</span>
      <Waveform active={listening} />
    </button>
  );
}
