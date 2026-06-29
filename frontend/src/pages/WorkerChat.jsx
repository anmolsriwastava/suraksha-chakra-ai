import React, { useState, useRef, useEffect, useCallback } from 'react';
import { sendChatMessage } from '../utils/api';

// ── Helpers ────────────────────────────────────────────────────────────

function formatTime(date) {
  return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
}

// Parse **bold** markers in bot replies
function parseBold(text) {
  const parts = text.split(/(\*[^*]+\*)/g);
  return parts.map((part, i) =>
    part.startsWith('*') && part.endsWith('*')
      ? <strong key={i}>{part.slice(1, -1)}</strong>
      : part
  );
}

// Generate random waveform bars for voice note decoration
function randomBars(count = 20) {
  return Array.from({ length: count }, () => Math.random() * 18 + 6);
}

// ── Sub-components ─────────────────────────────────────────────────────

function TypingBubble() {
  return (
    <div className="bubble-row incoming">
      <div className="bubble incoming">
        <div className="typing-indicator">
          <div className="typing-dot" />
          <div className="typing-dot" />
          <div className="typing-dot" />
        </div>
      </div>
    </div>
  );
}

function VoiceBubble({ direction, durationSec = 3, audioUrl }) {
  const bars = useRef(randomBars());
  const handlePlay = () => {
    if (audioUrl) {
      const audio = new Audio(audioUrl);
      audio.play().catch(e => console.error("Error playing audio:", e));
    }
  };
  
  return (
    <div className="voice-bubble">
      <button className="voice-play-btn" onClick={handlePlay}>▶</button>
      <div className="voice-waveform">
        {bars.current.map((h, i) => (
          <div key={i} className="voice-bar" style={{ height: `${h}px` }} />
        ))}
      </div>
      <span style={{ fontSize: 12, opacity: 0.7, minWidth: 28 }}>
        0:{String(durationSec).padStart(2, '0')}
      </span>
    </div>
  );
}

function MessageBubble({ msg }) {
  const direction = msg.from === 'user' ? 'outgoing' : 'incoming';

  return (
    <div className={`bubble-row ${direction}`}>
      <div className={`bubble ${direction}`}>
        {msg.type === 'voice' ? (
          <VoiceBubble direction={direction} durationSec={msg.duration} audioUrl={msg.audioUrl} />
        ) : (
          <p className="bubble-text">{parseBold(msg.text)}</p>
        )}
        {msg.reportId && (
          <a
            href={`http://localhost:8000/api/reports/legal-notice/${msg.reportId}`}
            target="_blank"
            rel="noreferrer"
            style={{
              display: 'inline-block',
              marginTop: '8px',
              padding: '6px 12px',
              background: '#ef4444',
              color: 'white',
              borderRadius: '6px',
              textDecoration: 'none',
              fontSize: '13px',
              fontWeight: 500
            }}
          >
            📄 Download Legal Notice (PDF)
          </a>
        )}
        <div className="bubble-meta">{formatTime(msg.timestamp)}</div>
      </div>
    </div>
  );
}

function QuickReplies({ chips, onSelect }) {
  if (!chips || chips.length === 0) return null;
  return (
    <div className="quick-replies">
      {chips.map((chip) => (
        <button
          key={chip}
          className="quick-reply-chip"
          onClick={() => onSelect(chip)}
        >
          {chip}
        </button>
      ))}
    </div>
  );
}

// ── Initial greeting from the bot ──────────────────────────────────────

const WELCOME_MESSAGE = {
  id: 0,
  from: 'bot',
  type: 'text',
  timestamp: new Date(),
  text: `Namaste! 🙏 Main *Suraksha Chakra* hoon.

Main aapki in chezon mein madad kar sakta hoon:

1️⃣  Fair wage jaanne ke liye — apna kaam aur shehar batayein
2️⃣  Contractor check karne ke liye — unka naam batayein
3️⃣  Wage report karne ke liye — aapko kitna mila, batayein

Aap *Hindi ya Hinglish* mein likh sakte hain.
Voice message bhi bhej sakte hain! 🎤`,
};

const DEFAULT_QUICK_REPLIES = [
  'Delhi mein mason ka kaam mila',
  'Mumbai mein electrician hoon',
  'Contractor check karna hai',
];

// ── Main WorkerChat component ──────────────────────────────────────────

export default function WorkerChat() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [quickReplies, setQuickReplies] = useState(DEFAULT_QUICK_REPLIES);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [sessionId] = useState('demo-user-' + Date.now());
  const [ttsEnabled, setTtsEnabled] = useState(false);

  const listRef = useRef(null);
  const inputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recordingTimerRef = useRef(null);
  const nextId = useRef(1);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const speakText = useCallback((text) => {
    if (!ttsEnabled || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'hi-IN';
    window.speechSynthesis.speak(utterance);
  }, [ttsEnabled]);

  const addMessage = useCallback((msg) => {
    setMessages((prev) => [...prev, { ...msg, id: nextId.current++ }]);
    if (msg.from === 'bot' && msg.type === 'text') {
      speakText(msg.text);
    }
  }, [speakText]);

  // Send text message → hit backend → show reply
  const sendText = useCallback(async (text) => {
    if (!text.trim()) return;

    addMessage({ from: 'user', type: 'text', text: text.trim(), timestamp: new Date() });
    setInputText('');
    setQuickReplies([]);
    setIsTyping(true);

    try {
      const response = await sendChatMessage(text.trim(), sessionId);
      setIsTyping(false);
      addMessage({ 
        from: 'bot', 
        type: 'text', 
        text: response.reply, 
        timestamp: new Date(),
        reportId: response.extracted?.report_id 
      });
      // Use server-provided quick replies if available, otherwise use defaults
      setQuickReplies(
        response.quick_replies && response.quick_replies.length > 0
          ? response.quick_replies
          : []
      );
    } catch (err) {
      setIsTyping(false);
      addMessage({
        from: 'bot',
        type: 'text',
        text: 'Sorry, server se connect nahi ho raha. Thodi der baad try karein. 🙏',
        timestamp: new Date(),
      });
    }
  }, [addMessage, sessionId]);

  const handleSend = () => sendText(inputText);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Voice recording — sends actual audio as base64 to backend
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());

        const duration = recordingSeconds;
        const blob = new Blob(audioChunksRef.current, { type: 'audio/ogg; codecs=opus' });
        const audioUrl = URL.createObjectURL(blob);
        
        addMessage({ from: 'user', type: 'voice', duration, audioUrl, timestamp: new Date() });
        setIsTyping(true);
        setRecordingSeconds(0);

        try {
          const reader = new FileReader();
          const base64Promise = new Promise((resolve, reject) => {
            reader.onloadend = () => {
              const base64 = reader.result.split(',')[1];
              resolve(base64);
            };
            reader.onerror = reject;
          });
          reader.readAsDataURL(blob);

          const audioBase64 = await base64Promise;
          const response = await sendChatMessage('', sessionId, audioBase64);

          setIsTyping(false);
          addMessage({ 
            from: 'bot', 
            type: 'text', 
            text: response.reply, 
            timestamp: new Date(),
            reportId: response.extracted?.report_id 
          });
          setQuickReplies(
            response.quick_replies && response.quick_replies.length > 0
              ? response.quick_replies
              : []
          );
        } catch (err) {
          setIsTyping(false);
          addMessage({
            from: 'bot',
            type: 'text',
            text: 'Voice message mila, par process nahi ho saka. Text mein try karein. 🙏',
            timestamp: new Date(),
          });
        }
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);

      // Count seconds
      recordingTimerRef.current = setInterval(() => {
        setRecordingSeconds((s) => s + 1);
      }, 1000);
    } catch (err) {
      // Mic access denied — show helper message
      addMessage({
        from: 'bot',
        type: 'text',
        text: 'Microphone access nahi mila. Please text mein likhen ya browser permissions check karein.',
        timestamp: new Date(),
      });
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
    clearInterval(recordingTimerRef.current);
    setIsRecording(false);
  };

  const handleMicClick = () => {
    if (isRecording) stopRecording();
    else startRecording();
  };

  return (
    <div className="chat-screen">
      {/* Top bar */}
      <div className="chat-topbar">
        <div className="chat-topbar-avatar">🛡️</div>
        <div className="chat-topbar-info" style={{ flex: 1 }}>
          <h2>Suraksha Chakra</h2>
          <p>● Online — Aapka haq, aapki awaaz</p>
        </div>
        <button 
          onClick={() => {
            setTtsEnabled(!ttsEnabled);
            if (!ttsEnabled) {
              const lastBotMsg = [...messages].reverse().find(m => m.from === 'bot');
              if (lastBotMsg && lastBotMsg.text && window.speechSynthesis) {
                window.speechSynthesis.cancel();
                const u = new SpeechSynthesisUtterance(lastBotMsg.text);
                u.lang = 'hi-IN';
                window.speechSynthesis.speak(u);
              }
            } else {
              window.speechSynthesis?.cancel();
            }
          }}
          style={{ background: 'transparent', border: 'none', fontSize: '24px', cursor: 'pointer', opacity: ttsEnabled ? 1 : 0.4 }}
          title={ttsEnabled ? "Speaker On" : "Speaker Off"}
        >
          {ttsEnabled ? '🔊' : '🔈'}
        </button>
      </div>

      {/* Message list */}
      <div className="message-list" ref={listRef}>
        <div className="date-divider"><span>Aaj</span></div>

        {messages.map((msg) => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}

        {isTyping && <TypingBubble />}
      </div>

      {/* Quick replies */}
      <QuickReplies chips={quickReplies} onSelect={sendText} />

      {/* Input bar */}
      <div className="input-bar">
        <button
          className={`input-icon-btn mic-btn ${isRecording ? 'recording' : ''}`}
          onClick={handleMicClick}
          title={isRecording ? `Recording… ${recordingSeconds}s (tap to stop)` : 'Voice message'}
        >
          {isRecording ? '⏹' : '🎤'}
        </button>

        <textarea
          ref={inputRef}
          className="input-field"
          rows={1}
          placeholder="Yahan likhen… (Hindi ya Hinglish)"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isRecording}
        />

        <button
          className="input-icon-btn send-btn"
          onClick={handleSend}
          disabled={!inputText.trim() || isRecording}
          title="Bhejein"
        >
          ➤
        </button>
      </div>
    </div>
  );
}
