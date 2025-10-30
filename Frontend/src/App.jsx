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
  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage = { text: input, sender: "user" };
    setMessages((prev) => [...prev, userMessage]);

    // Fake bot response (you can connect to backend later)
    setTimeout(() => {
      const botText = generateBotReply(input);
      const botMessage = { text: botText, sender: "bot" };
      setMessages((prev) => [...prev, botMessage]);
      speak(botText); // 🗣️ Speak bot reply aloud
    }, 1000);

    setInput("");
  };

  // 🧠 Simple bot logic (can be replaced by AI API)
  const generateBotReply = (text) => {
    const lower = text.toLowerCase();
    if (lower.includes("hello")) return "Hello there! How are you today?";
    if (lower.includes("time"))
      return `It's ${new Date().toLocaleTimeString()}`;
    if (lower.includes("your name")) return "I'm UMD, your voice assistant!";
    if (lower.includes("bye")) return "Goodbye! Have a great day!";
    return "I'm still learning to understand that. Try saying hello!";
  };

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
