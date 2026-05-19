export default function Waveform({ active, bars = 5 }) {
  return (
    <div className={`waveform ${active ? "waveform-active" : ""}`} aria-hidden>
      {Array.from({ length: bars }).map((_, i) => (
        <span key={i} className="wave-bar" style={{ animationDelay: `${i * 0.1}s` }} />
      ))}
    </div>
  );
}
