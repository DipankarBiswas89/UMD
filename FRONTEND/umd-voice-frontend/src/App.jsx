import React, { useState, useRef } from 'react';
import axios from 'axios';

function App() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [audioUrl, setAudioUrl] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const audioRef = useRef(null);

  const askAndSpeak = async () => {
    setLoading(true);
    setAnswer('');
    setAudioUrl(null);
    setError('');
    try {
      const response = await axios.get('/api/ask-and-speak', {
        params: { question },
      });
      setAnswer(response.data.answer);

      // Convert base64 audio back to Blob and play
      if (response.data.audio_base64) {
        const audioBlob = b64toBlob(response.data.audio_base64, 'audio/mpeg');
        const audioURL = URL.createObjectURL(audioBlob);
        setAudioUrl(audioURL);
        setTimeout(() => {
          if (audioRef.current) audioRef.current.play();
        }, 100);
      }
    } catch (err) {
      setError('Failed to get response from backend.');
    }
    setLoading(false);
  };

  // Helper: Convert base64 to Blob
  function b64toBlob(b64Data, contentType = '', sliceSize = 512) {
    const byteCharacters = atob(b64Data);
    const byteArrays = [];
    for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
      const slice = byteCharacters.slice(offset, offset + sliceSize);
      const byteNumbers = new Array(slice.length);
      for (let i = 0; i < slice.length; i++) {
        byteNumbers[i] = slice.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      byteArrays.push(byteArray);
    }
    return new Blob(byteArrays, { type: contentType });
  }

  return (
    <div style={{
      minHeight: '100vh',
      width: '100vw',
      background: 'linear-gradient(135deg, #1a2980 0%, #26d0ce 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <div style={{
        background: '#181f27',
        padding: '36px 28px',
        borderRadius: 36,
        minWidth: 350,
        maxWidth: 440,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center'
      }}>
        <h1 style={{
          fontSize: '2.5rem', fontWeight: 800, letterSpacing: 2,
          marginBottom: 18, color: 'white'
        }}>
          UMD Voice Assistant
        </h1>
        <input
          type="text"
          value={question}
          onChange={e => setQuestion(e.target.value)}
          placeholder="Type your message…"
          style={{
            width: '100%',
            padding: '13px 16px',
            borderRadius: 22,
            border: 'none',
            marginBottom: 16,
            fontSize: '1.15rem',
            outline: 'none',
            background: '#222732',
            color: 'white'
          }}
        />
        <button
          onClick={askAndSpeak}
          disabled={loading || question.trim() === ''}
          style={{
            width: '100%',
            padding: '15px 0',
            borderRadius: 28,
            border: 'none',
            background: loading
              ? '#43cea270'
              : 'linear-gradient(90deg,#43cea2,#185a9d)',
            color: 'white',
            fontWeight: 600,
            fontSize: '1.25rem',
            cursor: loading ? 'wait' : 'pointer',
            marginBottom: 14
          }}
        >
          {loading ? 'Processing...' : 'Ask & Speak'}
        </button>
        {error && (
          <div style={{ color: 'salmon', marginTop: 9, fontSize: '1rem' }}>
            {error}
          </div>
        )}
        {answer && (
          <div style={{
            width: '100%',
            background: '#242a36',
            color: '#f2f7fa',
            fontSize: '1.09rem',
            marginTop: 22,
            padding: '15px 19px',
            borderRadius: 16,
            boxShadow: '0 1.5px 7px #23252625',
            wordBreak: 'break-word'
          }}>
            {answer}
          </div>
        )}
        {audioUrl && (
          <audio
            ref={audioRef}
            controls
            src={audioUrl}
            autoPlay
            style={{
              width: '100%',
              marginTop: 16,
              background: '#1a2980'
            }}
          />
        )}
      </div>
    </div>
  );
}

export default App;
