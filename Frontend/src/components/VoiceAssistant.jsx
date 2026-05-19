import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchMessages,
  fetchVoiceStatus,
  generateResponse,
  generateVoice,
  resolveAudioUrl,
  uploadVoiceFile,
} from "../api/voiceApi";
import { useAudioPlayer } from "../hooks/useAudioPlayer";
import { useVoiceAssistant } from "../hooks/useVoiceAssistant";
import { useVoiceRecorder } from "../hooks/useVoiceRecorder";
import AudioPlayerControls from "./AudioPlayerControls";
import ChatBubble from "./ChatBubble";
import MicButton from "./MicButton";
import StatusIndicator from "./StatusIndicator";

export default function VoiceAssistant() {
  const [messages, setMessages] = useState([]);
  const [textInput, setTextInput] = useState("");
  const [voiceStatus, setVoiceStatus] = useState(null);
  const [isUploadingVoice, setIsUploadingVoice] = useState(false);
  const [lastAudioUrl, setLastAudioUrl] = useState(null);
  const chatEndRef = useRef(null);

  const audioPlayer = useAudioPlayer();

  const appendMessages = useCallback((newMsgs) => {
    setMessages((prev) => [...prev, ...newMsgs]);
  }, []);

  const assistant = useVoiceAssistant({
    audioPlayer,
    onMessagesUpdate: appendMessages,
    useFullTurn: true,
  });

  const handleRecordingBlob = useCallback(
    async (blob, mimeType) => {
      try {
        const turn = await assistant.runPipeline(blob, mimeType);
        if (turn?.audio_url) setLastAudioUrl(resolveAudioUrl(turn.audio_url));
      } catch {
        /* error in assistant.error */
      }
    },
    [assistant]
  );

  const { isRecording, toggleRecording } = useVoiceRecorder({
    onBlob: handleRecordingBlob,
  });

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    (async () => {
      const history = await fetchMessages();
      if (history.length) {
        setMessages(
          history.map((m) => ({
            text: m.text,
            sender: m.sender === "user" ? "user" : "bot",
          }))
        );
      }
      setVoiceStatus(await fetchVoiceStatus());
    })();
  }, []);

  const displayStatus = isRecording ? "listening" : assistant.status;

  const handleMicClick = () => {
    if (assistant.status === "speaking") {
      assistant.interrupt();
    }
    if (!isRecording) assistant.setListening();
    toggleRecording();
  };

  const handleTextSend = async () => {
    const text = textInput.trim();
    if (!text || assistant.status === "processing") return;
    setTextInput("");
    appendMessages([{ text, sender: "user" }]);
    assistant.setStatus("processing");
    try {
      const ai = await generateResponse(text);
      appendMessages([{ text: ai.response, sender: "bot" }]);
      assistant.setStatus("speaking");
      const voice = await generateVoice(ai.response);
      const url = resolveAudioUrl(voice.audio_url);
      setLastAudioUrl(url);
      await audioPlayer.play(url, {
        onEnded: () => assistant.setStatus("idle"),
      });
    } catch (err) {
      assistant.setError(err.message);
      assistant.setStatus("idle");
    }
  };

  const handleVoiceUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploadingVoice(true);
    try {
      await uploadVoiceFile(file);
      setVoiceStatus(await fetchVoiceStatus());
    } catch (err) {
      assistant.setError(err.message);
    } finally {
      setIsUploadingVoice(false);
      e.target.value = "";
    }
  };

  const busy = assistant.status === "processing" || assistant.status === "speaking";

  return (
    <div className="assistant-shell">
      <header className="assistant-header">
        <div className="header-glow">
          <h1>Voice Assistant</h1>
          <p className="subtitle">Speak naturally — cloned voice replies</p>
        </div>
        <StatusIndicator status={displayStatus} />
      </header>

      {assistant.error && <div className="error-banner">{assistant.error}</div>}

      <section className="voice-upload-bar">
        <label htmlFor="voice-upload" className="upload-chip">
          {isUploadingVoice ? "Uploading…" : "Upload speaker WAV"}
        </label>
        <input
          id="voice-upload"
          type="file"
          accept=".wav,.mp3,.flac,.pth,.onnx"
          onChange={handleVoiceUpload}
          hidden
        />
        {voiceStatus?.voice_sample && (
          <span className="voice-chip ok">
            Speaker: {voiceStatus.voice_sample.split(/[/\\]/).pop()}
          </span>
        )}
        {!voiceStatus?.voice_sample && (
          <span className="voice-chip warn">No speaker WAV — upload yours</span>
        )}
        {voiceStatus?.voice_sample && voiceStatus?.tts_microservice_healthy === false && (
          <span className="voice-chip warn">
            Cloning offline — start TTS service (:8001) or you get generic AI voice
          </span>
        )}
        {voiceStatus?.tts_microservice_healthy === true && (
          <span className="voice-chip ok">Cloned voice active</span>
        )}
      </section>

      <main className="chat-main">
        <div className="chat-scroll">
          {messages.length === 0 && (
            <p className="empty-hint">Press the microphone and ask anything.</p>
          )}
          {messages.map((msg, i) => (
            <ChatBubble key={`${i}-${msg.text.slice(0, 12)}`} message={msg} />
          ))}
          <div ref={chatEndRef} />
        </div>
      </main>

      <footer className="assistant-footer">
        <AudioPlayerControls
          visible={!!lastAudioUrl}
          isPlaying={audioPlayer.isPlaying}
          isPaused={audioPlayer.isPaused}
          onPlay={() => lastAudioUrl && audioPlayer.resume()}
          onPause={audioPlayer.pause}
          onStop={() => {
            audioPlayer.stop();
            assistant.interrupt();
          }}
        />

        <div className="text-row">
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleTextSend()}
            placeholder="Or type a message…"
            disabled={busy}
          />
          <button type="button" className="send-btn" onClick={handleTextSend} disabled={busy}>
            Send
          </button>
        </div>

        <div className="mic-row">
          <MicButton
            isRecording={isRecording}
            status={displayStatus}
            onClick={handleMicClick}
            disabled={assistant.status === "processing"}
          />
          {busy && (
            <button type="button" className="interrupt-btn" onClick={assistant.interrupt}>
              Interrupt
            </button>
          )}
        </div>
      </footer>
    </div>
  );
}
