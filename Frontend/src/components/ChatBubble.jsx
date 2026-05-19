export default function ChatBubble({ message }) {
  const isUser = message.sender === "user";
  return (
    <div className={`bubble-row ${isUser ? "bubble-row-user" : "bubble-row-bot"}`}>
      <div className={`bubble ${isUser ? "bubble-user" : "bubble-bot"}`}>
        <p>{message.text}</p>
        {message.audioUrl && !isUser && (
          <span className="bubble-audio-hint">Voice response ready</span>
        )}
      </div>
    </div>
  );
}
