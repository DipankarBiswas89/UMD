// src/App.jsx
import React, { useState, useEffect } from "react";
import SpeechRecognition, {
  useSpeechRecognition,
} from "react-speech-recognition";
import "./index.css";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const { transcript, listening, resetTranscript } = useSpeechRecognition();

  // 🎤 Handle start/stop of voice recognition
  const handleVoiceInput = () => {
    if (listening) {
      SpeechRecognition.stopListening();
      setInput(transcript);
      resetTranscript();
    } else {
      SpeechRecognition.startListening({ continuous: true });
    }
  };

  // 💬 Send message
  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { text: input, sender: "user" };
    setMessages((prev) => [...prev, userMessage]);

    // Call backend API
    try {
      const params = new URLSearchParams({ question: input });
      const res = await fetch(`/api/ask-and-speak?${params.toString()}`);
      if (!res.ok) {
        throw new Error(`Server responded ${res.status}`);
      }
      const data = await res.json();
      const botText = data?.answer || "Sorry, I couldn't get a response.";
      const botMessage = { text: botText, sender: "bot" };
      setMessages((prev) => [...prev, botMessage]);
      speak(botText);
    } catch (err) {
      const errorText = "There was an error contacting the server.";
      const botMessage = { text: errorText, sender: "bot" };
      setMessages((prev) => [...prev, botMessage]);
    }

    setInput("");
  };

  // Bot reply generation removed (now using backend)

  // 🗣️ Convert text to speech
  const speak = (text) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.pitch = 1;
    utterance.rate = 1;
    utterance.volume = 1;
    window.speechSynthesis.speak(utterance);
  };

  // ⌨️ Press Enter to send
  const handleKeyPress = (e) => {
    if (e.key === "Enter") handleSend();
  };

  return (
    <div className="chat-container">
      <h2>🎙️ UMD Voice Assistant</h2>

      <div className="chat-box">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`message ${msg.sender === "user" ? "user" : "bot"}`}
          >
            {msg.text}
          </div>
        ))}
      </div>

      <div className="controls">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="Type or use voice..."
        />
        <button onClick={handleSend}>Send</button>
        <button onClick={handleVoiceInput}>
          {listening ? "🎧 Stop" : "🎤 Speak"}
        </button>
      </div>
    </div>
  );
}
