import Waveform from "./Waveform";

export default function AudioPlayerControls({
  isPlaying,
  isPaused,
  onPlay,
  onPause,
  onStop,
  visible,
}) {
  if (!visible) return null;

  return (
    <div className="audio-controls">
      <Waveform active={isPlaying} bars={7} />
      <div className="audio-buttons">
        {!isPlaying || isPaused ? (
          <button type="button" className="ctrl-btn" onClick={onPlay} aria-label="Play">
            Play
          </button>
        ) : (
          <button type="button" className="ctrl-btn" onClick={onPause} aria-label="Pause">
            Pause
          </button>
        )}
        <button type="button" className="ctrl-btn" onClick={onStop} aria-label="Stop">
          Stop
        </button>
      </div>
    </div>
  );
}
