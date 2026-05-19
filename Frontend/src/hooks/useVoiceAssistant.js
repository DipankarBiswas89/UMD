import { useCallback, useRef, useState } from "react";
import {
  generateResponse,
  generateVoice,
  resolveAudioUrl,
  transcribeBlob,
  uploadRecording,
  voiceTurn,
} from "../api/voiceApi";

/** idle | listening | processing | speaking */
export function useVoiceAssistant({ onMessagesUpdate, audioPlayer, useFullTurn = true }) {
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState(null);
  const abortRef = useRef(false);

  const runPipeline = useCallback(
    async (blob, mimeType) => {
      abortRef.current = false;
      setError(null);
      setStatus("processing");

      try {
        const ext = mimeType?.includes("webm") ? ".webm" : ".webm";
        const filename = `recording${ext}`;

        if (useFullTurn) {
          const recorded = await uploadRecording(blob, filename);
          if (abortRef.current) return;
          const turn = await voiceTurn(recorded.recording_id);
          if (abortRef.current) return;

          onMessagesUpdate?.([
            { text: turn.transcript, sender: "user" },
            { text: turn.response, sender: "bot", audioUrl: turn.audio_url },
          ]);

          setStatus("speaking");
          const url = resolveAudioUrl(turn.audio_url);
          await audioPlayer.play(url, {
            onEnded: () => setStatus("idle"),
            onError: () => setStatus("idle"),
          });
          return turn;
        }

        const stt = await transcribeBlob(blob, filename);
        if (abortRef.current) return;
        onMessagesUpdate?.([{ text: stt.text, sender: "user" }]);

        const ai = await generateResponse(stt.text);
        if (abortRef.current) return;
        onMessagesUpdate?.([{ text: ai.response, sender: "bot" }]);

        setStatus("speaking");
        const voice = await generateVoice(ai.response);
        const url = resolveAudioUrl(voice.audio_url);
        await audioPlayer.play(url, {
          onEnded: () => setStatus("idle"),
          onError: () => setStatus("idle"),
        });
        return { transcript: stt.text, response: ai.response, audio_url: voice.audio_url };
      } catch (err) {
        setError(err.message || "Voice pipeline failed");
        setStatus("idle");
        throw err;
      }
    },
    [audioPlayer, onMessagesUpdate, useFullTurn]
  );

  const interrupt = useCallback(() => {
    abortRef.current = true;
    audioPlayer.interrupt();
    setStatus("idle");
  }, [audioPlayer]);

  const setListening = useCallback(() => setStatus("listening"), []);

  return {
    status,
    setStatus,
    error,
    setError,
    runPipeline,
    interrupt,
    setListening,
  };
}
