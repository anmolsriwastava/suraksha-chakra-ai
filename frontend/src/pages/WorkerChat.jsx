import React, { useState, useRef, useEffect, useCallback } from 'react';
import { sendChatMessage } from '../utils/api';
import styles from './WorkerChat.module.css';

// ── Translations ───────────────────────────────────────────────────────
const TRANSLATIONS = {
  en: {
    title: "Suraksha Chakra AI",
    subtitle: "Online • Protecting Workers",
    placeholder: "Type a message",
    voiceBtn: "Voice Message",
    sendBtn: "Send",
    micError: "Microphone access denied. Please text or check browser permissions.",
    serverError: "Server connection failed. Please try again later.",
    voiceError: "Voice message received but couldn't be processed. Try text.",
    today: "Today",
    newChat: "New Chat",
    downloadNotice: "📄 Download Legal Notice (PDF)",
    qr_welcome_1: "I got work as a mason in Delhi",
    qr_welcome_2: "I am an electrician in Mumbai",
    qr_check_contractor: "Check contractor",
    qr_wage_400: "I receive ₹400",
    qr_wage_500: "I receive ₹500",
    qr_wage_600: "I receive ₹600",
    qr_check_another: "Check another contractor",
    qr_new_wage: "Check new wage",
    qr_check_wage: "Check fair wage",
    qr_plumber_chennai: "I work as a plumber in Chennai",
    qr_report_issue: "I want to report an issue",
    qr_need_help: "I need legal help"
  },
  hi: {
    title: "सुरक्षा चक्र एआई",
    subtitle: "ऑनलाइन • श्रमिकों की सुरक्षा",
    placeholder: "एक संदेश टाइप करें",
    voiceBtn: "वॉयस मैसेज",
    sendBtn: "भेजें",
    micError: "माइक्रोफोन एक्सेस नहीं मिला। कृपया टेक्स्ट में लिखें या ब्राउज़र परमिशन चेक करें।",
    serverError: "सर्वर से कनेक्ट नहीं हो रहा। थोड़ी देर बाद ट्राई करें।",
    voiceError: "वॉयस मैसेज मिला, पर प्रोसेस नहीं हो सका। टेक्स्ट में ट्राई करें।",
    today: "आज",
    newChat: "नयी चैट",
    downloadNotice: "📄 कानूनी नोटिस डाउनलोड करें (PDF)",
    qr_welcome_1: "दिल्ली में राज मिस्त्री का काम मिला",
    qr_welcome_2: "मुंबई में इलेक्ट्रीशियन हूँ",
    qr_check_contractor: "Contractor का नाम बताना है",
    qr_wage_400: "मुझे ₹400 मिल रहा है",
    qr_wage_500: "मुझे ₹500 मिल रहा है",
    qr_wage_600: "मुझे ₹600 मिल रहा है",
    qr_check_another: "दूसरा ठेकेदार चेक करना है",
    qr_new_wage: "नया वेतन चेक करना है",
    qr_check_wage: "उचित वेतन चेक करना है",
    qr_plumber_chennai: "मैं चेन्नई में प्लंबर हूँ",
    qr_report_issue: "मुझे शिकायत दर्ज करनी है",
    qr_need_help: "मुझे कानूनी मदद चाहिए"
  },
  ta: {
    title: "சுரக்‌ஷா சக்ரா AI",
    subtitle: "ஆன்லைன் • தொழிலாளர் பாதுகாப்பு",
    placeholder: "செய்தியை தட்டச்சு செய்யவும்",
    voiceBtn: "குரல் செய்தி",
    sendBtn: "அனுப்பு",
    micError: "மைக்ரோஃபோன் அணுகல் மறுக்கப்பட்டது. தட்டச்சு செய்யவும்.",
    serverError: "சர்வர் இணைப்பு தோல்வி. மீண்டும் முயற்சிக்கவும்.",
    voiceError: "குரல் செய்தி பெறப்பட்டது ஆனால் செயல்படுத்த முடியவில்லை. உரையை முயற்சிக்கவும்.",
    today: "இன்று",
    newChat: "புதிய அரட்டை",
    downloadNotice: "📄 சட்டபூர்வ அறிவிப்பை பதிவிறக்குக (PDF)",
    qr_welcome_1: "தில்லியில் கொத்தனாராக வேலை கிடைத்தது",
    qr_welcome_2: "மும்பையில் எலக்ட்ரீஷியன்",
    qr_check_contractor: "ஒப்பந்ததாரரின் பெயரை சொல்ல வேண்டும்",
    qr_wage_400: "எனக்கு ₹400 கிடைக்கிறது",
    qr_wage_500: "எனக்கு ₹500 கிடைக்கிறது",
    qr_wage_600: "எனக்கு ₹600 கிடைக்கிறது",
    qr_check_another: "மற்றொரு ஒப்பந்ததாரரை சரிபார்க்கவும்",
    qr_new_wage: "புதிய ஊதியத்தை சரிபார்க்கவும்",
    qr_check_wage: "சரியான ஊதியத்தை சரிபார்க்கவும்",
    qr_plumber_chennai: "நான் சென்னையில் பிளம்பராக வேலை செய்கிறேன்",
    qr_report_issue: "நான் ஒரு சிக்கலைப் புகாரளிக்க விரும்புகிறேன்",
    qr_need_help: "எனக்கு சட்ட உதவி தேவை"
  },
  bn: {
    title: "সুরক্ষা চক্র এআই",
    subtitle: "অনলাইন • শ্রমিকদের সুরক্ষা",
    placeholder: "একটি বার্তা টাইপ করুন",
    voiceBtn: "ভয়েস বার্তা",
    sendBtn: "পাঠান",
    micError: "মাইক্রোফোন অ্যাক্সেস অস্বীকার করা হয়েছে। টাইপ করুন।",
    serverError: "সার্ভার সংযোগ ব্যর্থ। আবার চেষ্টা করুন।",
    voiceError: "ভয়েস বার্তা পেয়েছি কিন্তু প্রক্রিয়া করতে পারিনি। পাঠ্য চেষ্টা করুন।",
    today: "আজ",
    newChat: "নতুন চ্যাট",
    downloadNotice: "📄 আইনি নোটিশ ডাউনলোড করুন (PDF)",
    qr_welcome_1: "দিল্লিতে রাজমিস্ত্রির কাজ পেয়েছি",
    qr_welcome_2: "মুম্বাইয়ে ইলেকট্রিশিয়ান",
    qr_check_contractor: "ঠিকাদারের নাম বলতে চাই",
    qr_wage_400: "আমি ₹৪০০ পাই",
    qr_wage_500: "আমি ₹৫০০ পাই",
    qr_wage_600: "আমি ₹৬০০ পাই",
    qr_check_another: "অন্য ঠিকাদার চেক করুন",
    qr_new_wage: "নতুন মজুরি চেক করুন",
    qr_check_wage: "সঠিক মজুরি চেক করুন",
    qr_plumber_chennai: "আমি চেন্নাইতে প্লাম্বার হিসেবে কাজ করি",
    qr_report_issue: "আমি একটি অভিযোগ জানাতে চাই",
    qr_need_help: "আমার আইনি সাহায্য প্রয়োজন"
  },
  mr: {
    title: "सुरक्षा चक्र एआय",
    subtitle: "ऑनलाइन • कामगारांचे संरक्षण",
    placeholder: "संदेश टाईप करा",
    voiceBtn: "व्हॉइस मेसेज",
    sendBtn: "पाठवा",
    micError: "मायक्रोफोन ऍक्सेस नाकारला. कृपया टाईप करा.",
    serverError: "सर्व्हर कनेक्शन अयशस्वी. कृपया पुन्हा प्रयत्न करा.",
    voiceError: "व्हॉइस मेसेज मिळाला पण प्रक्रिया करू शकलो नाही. मजकूर वापरून पहा.",
    today: "आज",
    newChat: "नवीन गप्पा",
    downloadNotice: "📄 कायदेशीर नोटीस डाउनलोड करा (PDF)",
    qr_welcome_1: "दिल्लीत गवंडी म्हणून काम मिळाले",
    qr_welcome_2: "मुंबईत इलेक्ट्रीशियन आहे",
    qr_check_contractor: "कंत्राटदाराचे नाव सांगायचे आहे",
    qr_wage_400: "मला ₹400 मिळतात",
    qr_wage_500: "मला ₹500 मिळतात",
    qr_wage_600: "मला ₹600 मिळतात",
    qr_check_another: "दुसरा कंत्राटदार तपासा",
    qr_new_wage: "नवीन वेतन तपासा",
    qr_check_wage: "योग्य वेतन तपासा",
    qr_plumber_chennai: "मी चेन्नईमध्ये प्लंबर म्हणून काम करतो",
    qr_report_issue: "मला तक्रार नोंदवायची आहे",
    qr_need_help: "मला कायदेशीर मदत हवी आहे"
  },
  hinglish: {
    title: "Suraksha Chakra AI",
    subtitle: "Online • Workers ki Suraksha",
    placeholder: "Message type karein",
    voiceBtn: "Voice Message",
    sendBtn: "Send",
    micError: "Microphone access denied. Please text type karein.",
    serverError: "Server se connect nahi ho pa raha. Baad mein try karein.",
    voiceError: "Voice message mila par process nahi ho saka. Text try karein.",
    today: "Aaj",
    newChat: "New Chat",
    downloadNotice: "📄 Legal Notice Download karein (PDF)",
    qr_welcome_1: "Delhi mein raj mistri ka kaam mila",
    qr_welcome_2: "Mumbai mein electrician hoon",
    qr_check_contractor: "Contractor ka naam batana hai",
    qr_wage_400: "Mujhe ₹400 mil raha hai",
    qr_wage_500: "Mujhe ₹500 mil raha hai",
    qr_wage_600: "Mujhe ₹600 mil raha hai",
    qr_check_another: "Dusra contractor check karna hai",
    qr_new_wage: "Naya wage check karna hai",
    qr_check_wage: "Sahi wage check karna hai",
    qr_plumber_chennai: "Main Chennai mein plumber hoon",
    qr_report_issue: "Mujhe complaint darj karni hai",
    qr_need_help: "Mujhe legal help chahiye"
  }
};

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'hinglish', label: 'Hinglish' },
  { code: 'ta', label: 'தமிழ்' },
  { code: 'bn', label: 'বাংলা' },
  { code: 'mr', label: 'मराठी' }
];

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
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const audioRef = useRef(null);

  useEffect(() => {
    if (audioUrl) {
      const audio = new Audio(audioUrl);
      audio.playbackRate = 1.25;
      audio.onplay = () => setIsPlaying(true);
      audio.onpause = () => setIsPlaying(false);
      audio.onended = () => {
        setIsPlaying(false);
        setProgress(0);
      };
      audio.ontimeupdate = () => {
        if (audio.duration) {
          setProgress(audio.currentTime / audio.duration);
        }
      };
      audioRef.current = audio;
    }
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [audioUrl]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch(e => console.error("Error playing audio:", e));
    }
  };
  
  return (
    <div className={styles.voiceBubble}>
      <button className={styles.voicePlayBtn} onClick={togglePlay}>
        {isPlaying ? '⏸' : '▶'}
      </button>
      <div className={styles.voiceWaveform}>
        {bars.current.map((h, i) => {
          const isPlayed = i / bars.current.length <= progress;
          return (
            <div 
              key={i} 
              className={styles.voiceBar} 
              style={{ 
                height: `${h}px`,
                backgroundColor: isPlayed ? (direction === 'outgoing' ? '#128C7E' : '#25D366') : '#9CA3AF'
              }} 
            />
          );
        })}
      </div>
      <span style={{ fontSize: 11, opacity: 0.7, minWidth: 28 }}>
        0:{String(durationSec).padStart(2, '0')}
      </span>
    </div>
  );
}

function MessageBubble({ msg, t }) {
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
            {t('downloadNotice')}
          </a>
        )}
        <div className={styles.bubbleMeta}>{formatTime(msg.timestamp)}</div>
      </div>
    </div>
  );
}

function QuickReplies({ chips, onSelect, t }) {
  if (!chips || chips.length === 0) return null;
  return (
    <div className={styles.quickReplies}>
      {chips.map((chip) => (
        <button
          key={chip}
          className={styles.quickReplyChip}
          onClick={() => onSelect(chip, t(chip))}
        >
          {t(chip)}
        </button>
      ))}
    </div>
  );
}

// ── Initial greeting from the bot ──────────────────────────────────────

const DEFAULT_QUICK_REPLIES = [
  'qr_welcome_1',
  'qr_welcome_2',
  'qr_check_contractor',
  'qr_plumber_chennai',
  'qr_report_issue',
  'qr_need_help',
];

// ── Main WorkerChat component ──────────────────────────────────────────

export default function WorkerChat() {
  const [lang, setLang] = useState(() => localStorage.getItem('workerLang') || 'en');
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);

  const t = useCallback((key) => {
    return TRANSLATIONS[lang]?.[key] || TRANSLATIONS['en'][key] || key;
  }, [lang]);

  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem('workerMessages');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.map(m => ({ ...m, timestamp: new Date(m.timestamp) }));
      } catch (e) { return []; }
    }
    return [];
  });
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [quickReplies, setQuickReplies] = useState(() => {
    const saved = localStorage.getItem('workerQuickReplies');
    return saved ? JSON.parse(saved) : DEFAULT_QUICK_REPLIES;
  });
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [sessionId, setSessionId] = useState(() => {
    const saved = localStorage.getItem('workerSessionId');
    if (saved) return saved;
    const newId = 'demo-user-' + Date.now();
    localStorage.setItem('workerSessionId', newId);
    return newId;
  });

  useEffect(() => {
    localStorage.setItem('workerMessages', JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    localStorage.setItem('workerQuickReplies', JSON.stringify(quickReplies));
  }, [quickReplies]);

  const langRef = useRef(lang);
  const fetchedRef = useRef(false);

  useEffect(() => {
    async function fetchWelcome() {
      setIsTyping(true);
      try {
        const response = await sendChatMessage('', sessionId, null, lang);
        setMessages([{
          id: 0,
          from: 'bot',
          type: 'text',
          text: response.reply,
          timestamp: new Date()
        }]);
        setQuickReplies(response.quick_replies || []);
      } catch (e) {
        console.error(e);
      } finally {
        setIsTyping(false);
      }
    }

    if (!fetchedRef.current && messages.length === 0) {
      fetchedRef.current = true;
      fetchWelcome();
    } else if (langRef.current !== lang) {
      langRef.current = lang;
      sendChatMessage('', sessionId, null, lang).then(response => {
        setMessages(prev => {
          if (prev.length === 0) return prev;
          const newMsgs = [...prev];
          newMsgs[0] = { ...newMsgs[0], text: response.reply };
          return newMsgs;
        });
      }).catch(console.error);
    }
  }, [lang, sessionId]);

  const handleLangChange = (code) => {
    setLang(code);
    localStorage.setItem('workerLang', code);
    setLangDropdownOpen(false);
  };

  const handleNewChat = () => {
    localStorage.removeItem('workerMessages');
    localStorage.removeItem('workerSessionId');
    localStorage.removeItem('workerQuickReplies');
    
    const newId = 'demo-user-' + Date.now();
    setSessionId(newId);
    setMessages([]);
    setQuickReplies(DEFAULT_QUICK_REPLIES);
    fetchedRef.current = false;
  };

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
  const sendText = useCallback(async (chipKey, displayLabel) => {
    const textToSend = displayLabel || chipKey;
    if (!textToSend.trim()) return;

    addMessage({ from: 'user', type: 'text', text: textToSend.trim(), timestamp: new Date() });
    setInputText('');
    setQuickReplies([]);
    setIsTyping(true);

    try {
      const response = await sendChatMessage(chipKey.trim(), sessionId, null, lang);
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
        text: t('serverError'),
        timestamp: new Date(),
      });
    }
  }, [addMessage, sessionId, t, lang]);

  const handleSend = () => sendText(inputText, inputText);

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
          const response = await sendChatMessage('', sessionId, audioBase64, lang);

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
            text: t('voiceError'),
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
        text: t('micError'),
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
        <div className={styles.avatar}>🛡</div>
        <div className={styles.topbarInfo}>
          <h2>{t('title')}</h2>
          <p><span className={styles.onlineDot}></span> {t('subtitle')}</p>
        </div>

        {/* Language Selector */}
        <div className={styles.langSelectorContainer}>
          <button 
            className={styles.newChatBtn} 
            onClick={handleNewChat}
            style={{ marginRight: '10px', padding: '6px 12px', background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '4px', color: '#fff', cursor: 'pointer', fontSize: '13px' }}
          >
            {t('newChat')}
          </button>

          <button 
            className={styles.langSelectorBtn} 
            onClick={() => setLangDropdownOpen(!langDropdownOpen)}
          >
            🌐 {LANGUAGES.find(l => l.code === lang)?.label || 'English'} ▾
          </button>
          
          {langDropdownOpen && (
            <div className={styles.langDropdown}>
              {LANGUAGES.map((l) => (
                <div 
                  key={l.code}
                  className={`${styles.langOption} ${lang === l.code ? styles.selected : ''}`}
                  onClick={() => handleLangChange(l.code)}
                >
                  {l.label}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Message list */}
      <div className={styles.messageList} ref={listRef}>
        <div className={styles.dateDivider}><span>{t('today')}</span></div>

        {messages.map((msg) => (
          <MessageBubble key={msg.id} msg={msg} t={t} />
        ))}

        {isTyping && <TypingBubble />}
      </div>

      {/* Input Section Wrapper */}
      <div className={styles.inputContainer}>
        {/* Quick replies above input bar */}
        <QuickReplies chips={quickReplies} onSelect={sendText} t={t} />

        {/* Input bar */}
        <div className={styles.inputBar}>
          <button className={styles.iconBtn} title="Attach">+</button>
          <button className={styles.iconBtn} title="Emoji">☺</button>
          
          <div className={styles.inputWrapper}>
            <textarea
              ref={inputRef}
              className={styles.inputField}
              rows={1}
              placeholder={t('placeholder')}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isRecording}
            />
          </div>

          <button className={styles.iconBtn} title="Camera">📷</button>

          {inputText.trim() ? (
            <button
              className={`${styles.actionBtn} ${styles.sendBtn}`}
              onClick={handleSend}
              disabled={isRecording}
              title={t('sendBtn')}
            >
              ➤
            </button>
          ) : (
            <button
              className={`${styles.actionBtn} ${styles.micBtn} ${isRecording ? styles.recording : ''}`}
              onClick={handleMicClick}
              title={isRecording ? `Recording... ${recordingSeconds}s` : t('voiceBtn')}
            >
              {isRecording ? '⏹' : '🎙'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
