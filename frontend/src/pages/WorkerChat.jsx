import React, { useState, useRef, useEffect, useCallback } from 'react';
import { sendChatMessage } from '../utils/api';
import styles from './WorkerChat.module.css';

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
  return Array.from({ length: count }, () => Math.random() * 14 + 4);
}

// ── Sub-components ─────────────────────────────────────────────────────

function TypingBubble() {
  return (
    <div className={`${styles.bubbleRow} ${styles.incoming}`}>
      <div className={`${styles.bubble} ${styles.incoming}`}>
        <div className={styles.typingIndicator}>
          <div className={styles.typingDot} />
          <div className={styles.typingDot} />
          <div className={styles.typingDot} />
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
    <div className={styles.voiceBubble}>
      <button className={styles.voicePlayBtn} onClick={handlePlay}>▶</button>
      <div className={styles.voiceWaveform}>
        {bars.current.map((h, i) => (
          <div key={i} className={styles.voiceBar} style={{ height: `${h}px` }} />
        ))}
      </div>
      <span style={{ fontSize: 11, opacity: 0.7, minWidth: 28 }}>
        0:{String(durationSec).padStart(2, '0')}
      </span>
    </div>
  );
}

function MessageBubble({ msg }) {
  const direction = msg.from === 'user' ? 'outgoing' : 'incoming';

  return (
    <div className={`${styles.bubbleRow} ${styles[direction]}`}>
      <div className={`${styles.bubble} ${styles[direction]}`}>
        {msg.type === 'voice' ? (
          <VoiceBubble direction={direction} durationSec={msg.duration} audioUrl={msg.audioUrl} />
        ) : (
          <div className={styles.bubbleText}>{parseBold(msg.text)}</div>
        )}
        {msg.reportId && (
          <a
            href={`http://localhost:8000/api/reports/legal-notice/${msg.reportId}`}
            target="_blank"
            rel="noreferrer"
            className={styles.noticeBtn}
          >
            📄 Download Legal Notice (PDF)
          </a>
        )}
        <div className={styles.bubbleMeta}>{formatTime(msg.timestamp)}</div>
      </div>
    </div>
  );
}

function QuickReplies({ chips, onSelect }) {
  if (!chips || chips.length === 0) return null;
  return (
    <div className={styles.quickReplies}>
      {chips.map((chip) => (
        <button
          key={chip}
          className={styles.quickReplyChip}
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

  const listRef = useRef(null);
  const inputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recordingTimerRef = useRef(null);
  const recordingStartRef = useRef(null);
  const nextId = useRef(1);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const addMessage = useCallback((msg) => {
    setMessages((prev) => [...prev, { ...msg, id: nextId.current++ }]);
  }, []);

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
      if (response.audio_base64) {
        addMessage({
          from: 'bot',
          type: 'voice',
          audioUrl: `data:audio/mp3;base64,${response.audio_base64}`,
          duration: Math.max(1, Math.round(response.reply.length / 15)),
          timestamp: new Date(),
        });
      }
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

        const duration = recordingStartRef.current ? Math.max(1, Math.round((Date.now() - recordingStartRef.current) / 1000)) : recordingSeconds;
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
          if (response.audio_base64) {
            addMessage({
              from: 'bot',
              type: 'voice',
              audioUrl: `data:audio/mp3;base64,${response.audio_base64}`,
              duration: Math.max(1, Math.round(response.reply.length / 15)),
              timestamp: new Date(),
            });
          }
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
      recordingStartRef.current = Date.now();
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
    <div className={styles.chatScreen}>
      {/* Top bar */}
      <div className={styles.topbar}>
        <div className={styles.avatar}>🛡️</div>
        <div className={styles.topbarInfo}>
          <h2>Suraksha Chakra AI</h2>
          <p><span className={styles.onlineDot}></span> Online • Protecting Workers</p>
        </div>
      </div>

      {/* Message list */}
      <div className={styles.messageList} ref={listRef}>
        <div className={styles.dateDivider}><span>Today</span></div>

        {messages.map((msg) => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}

        {isTyping && <TypingBubble />}
      </div>

      {/* Quick replies */}
      <QuickReplies chips={quickReplies} onSelect={sendText} />

      {/* Input bar */}
      <div className={styles.inputBar}>
        <button className={styles.iconBtn} title="Attach" style={{ fontSize: '26px' }}>＋</button>
        <button className={styles.iconBtn} title="Emoji">😊</button>
        
        <div className={styles.inputWrapper}>
          <textarea
            ref={inputRef}
            className={styles.inputField}
            rows={1}
            placeholder="Type a message"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isRecording}
          />
        </div>

        {inputText.trim() ? (
          <button
            className={`${styles.actionBtn} ${styles.sendBtn}`}
            onClick={handleSend}
            disabled={isRecording}
            title="Send"
          >
            ➤
          </button>
        ) : (
          <button
            className={`${styles.actionBtn} ${styles.micBtn} ${isRecording ? styles.recording : ''}`}
            onClick={handleMicClick}
            title={isRecording ? `Recording... ${recordingSeconds}s` : 'Voice Message'}
          >
            {isRecording ? '⏹' : '🎤'}
          </button>
        )}
      </div>
    </div>
  );
}
