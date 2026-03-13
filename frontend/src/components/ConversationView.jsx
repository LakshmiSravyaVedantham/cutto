import React, { useState, useRef, useEffect } from 'react'
import ScenePlanEditor from './ScenePlanEditor'
import useIsMobile from '../hooks/useIsMobile'

const MAX_IMAGE_SIZE = 5 * 1024 * 1024 // 5 MB
const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']

export default function ConversationView({ ws }) {
  const isMobile = useIsMobile()
  const [input, setInput] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [hasMic, setHasMic] = useState(false)
  const [attachedImage, setAttachedImage] = useState(null) // { dataUrl, base64 }
  const bottomRef = useRef(null)
  const recognitionRef = useRef(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [ws.messages, ws.previews, ws.isThinking, ws.scenePlan])

  // Global keyboard shortcut: V to toggle voice input
  useEffect(() => {
    const handler = (e) => {
      // Don't trigger when typing in an input/textarea
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return
      if (e.key === 'v' || e.key === 'V') {
        if (recognitionRef.current) toggleMic()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [isListening]) // eslint-disable-line react-hooks/exhaustive-deps

  // Stable ref to ws.sendText so speech handler doesn't re-create
  const sendTextRef = useRef(ws.sendText)
  sendTextRef.current = ws.sendText

  // Setup Web Speech API — runs ONCE (no deps)
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return

    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onresult = (event) => {
      // Collect all results into a single transcript
      let final = ''
      let interim = ''
      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          final += result[0].transcript
        } else {
          interim += result[0].transcript
        }
      }
      // Show interim + final text in input while recording
      setInput(final + interim)
    }

    recognition.onerror = (e) => {
      // "no-speech" and "aborted" are not real errors — just silence
      if (e.error !== 'no-speech' && e.error !== 'aborted') {
        console.warn('Speech recognition error:', e.error)
      }
      setIsListening(false)
    }

    // Don't auto-stop — user controls when to stop
    recognition.onend = () => {
      // Only reset if we didn't manually stop (e.g., browser killed it)
      setIsListening(prev => {
        // If still marked as listening, restart (browser can kill after ~60s)
        if (prev && recognitionRef.current) {
          try { recognitionRef.current.start() } catch {}
        }
        return prev
      })
    }

    recognitionRef.current = recognition
    setHasMic(true)
  }, [])

  const toggleMic = () => {
    if (isListening) {
      // Stop recording and send whatever was captured
      recognitionRef.current?.stop()
      setIsListening(false)
      // Send accumulated input
      setInput(prev => {
        if (prev.trim()) {
          sendTextRef.current(prev.trim())
        }
        return ''
      })
    } else {
      setInput('')
      try {
        recognitionRef.current?.start()
        setIsListening(true)
      } catch (e) {
        console.warn('Could not start speech recognition:', e)
      }
    }
  }

  const handleImageSelect = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    // Reset so the same file can be re-selected
    e.target.value = ''

    if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
      return // silently ignore unsupported types
    }
    if (file.size > MAX_IMAGE_SIZE) {
      return // too large
    }

    const reader = new FileReader()
    reader.onload = () => {
      const dataUrl = reader.result
      // dataUrl is "data:<mime>;base64,<data>" — send the full string,
      // backend strips the prefix.
      setAttachedImage({ dataUrl, base64: dataUrl })
    }
    reader.readAsDataURL(file)
  }

  const removeAttachedImage = () => setAttachedImage(null)

  const handleSend = () => {
    if (!input.trim() || ws.isThinking || !ws.connected) return
    ws.sendText(input.trim(), attachedImage?.base64 || null)
    setInput('')
    setAttachedImage(null)
  }

  const handlePlanUpdate = (updatedPlan) => {
    ws.updatePlan(updatedPlan)
  }

  const handleAskRevision = (note) => {
    ws.sendText(`Please revise the scene plan: ${note}`)
  }

  return (
    <div style={{
      ...styles.container,
      ...(isMobile ? { padding: '0 12px' } : {}),
    }}>
      <div style={styles.glowOrb1} aria-hidden="true" />
      <div style={styles.glowOrb2} aria-hidden="true" />

      <header style={styles.header}>
        <div style={styles.logoWrap}>
          <span style={styles.logoIcon} aria-hidden="true">&#9655;</span>
          <h1 style={styles.title}>CutTo</h1>
        </div>
        <p style={styles.headerSub}>Your AI Video Director</p>
      </header>

      <div style={styles.messages} role="log" aria-label="Conversation" aria-live="polite">
        {ws.messages.map((m, i) => (
          <div key={i} style={styles.msgRow(m.role)} role="article" aria-label={`${m.role === 'user' ? 'You' : 'AI Director'} said`}>
            <div style={styles.avatar(m.role)} aria-hidden="true">
              {m.role === 'user' ? 'You' : 'AI'}
            </div>
            <div style={{
              ...styles.msg(m.role),
              ...(isMobile ? { maxWidth: '85%', padding: '12px 14px', fontSize: 13 } : {}),
            }}>
              {m.image && (
                <img
                  src={m.image}
                  alt="Attached reference"
                  style={styles.msgImage}
                />
              )}
              {m.text}
            </div>
          </div>
        ))}

        {/* Thinking indicator */}
        {ws.isThinking && !ws.scenePlan && (
          <div style={styles.msgRow('agent')}>
            <div style={styles.avatar('agent')}>AI</div>
            <div style={styles.thinkingBubble}>
              <span style={styles.dot1} />
              <span style={styles.dot2} />
              <span style={styles.dot3} />
            </div>
          </div>
        )}

        {/* Scene previews */}
        {ws.previews.map((img, i) => (
          <div key={`img-${i}`} style={{
            ...styles.previewWrap,
            ...(isMobile ? { margin: '12px 0' } : {}),
          }}>
            <img
              src={`data:image/png;base64,${img}`}
              alt={`Scene preview ${i + 1}`}
              style={styles.preview}
            />
            <div style={styles.previewLabel}>Scene Preview {i + 1}</div>
          </div>
        ))}

        {/* Scene Plan Editor */}
        {ws.scenePlan && (
          <div style={styles.planEditorWrap}>
            <ScenePlanEditor
              plan={ws.scenePlan}
              onApprove={ws.approve}
              onUpdate={handlePlanUpdate}
              onAskRevision={handleAskRevision}
            />
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {ws.connectionLost && (
        <div style={styles.connectionBanner}>
          <span style={styles.connectionDot} />
          Connection lost — reconnecting...
        </div>
      )}

      {ws.error && (
        <div style={styles.error}>
          <span style={{ flex: 1 }}>{ws.error}</span>
          <button
            style={styles.errorDismiss}
            onClick={ws.dismissError}
            title="Dismiss"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      )}

      {/* Mic listening overlay */}
      {isListening && (
        <div style={styles.listeningOverlay}>
          <div style={styles.listeningContent}>
            <div style={styles.micWave}>
              <span style={styles.wave1} />
              <span style={styles.wave2} />
              <span style={styles.wave3} />
              <span style={styles.wave4} />
              <span style={styles.wave5} />
            </div>
            <p style={styles.listeningText}>Listening...</p>
            <p style={styles.listeningHint}>{input || 'Speak your idea'}</p>
            <button style={styles.stopBtn} onClick={toggleMic}>
              Stop Recording
            </button>
          </div>
        </div>
      )}

      {/* Hidden file input for image upload */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        style={{ display: 'none' }}
        onChange={handleImageSelect}
      />

      <div style={{
        ...styles.inputArea,
        ...(isMobile ? { paddingBottom: 12 } : {}),
      }}>
        {/* Attached image thumbnail */}
        {attachedImage && (
          <div style={styles.thumbnailRow}>
            <div style={styles.thumbnailWrap}>
              <img src={attachedImage.dataUrl} alt="Attached" style={styles.thumbnail} />
              <button style={styles.thumbnailRemove} onClick={removeAttachedImage} title="Remove image">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <span style={styles.thumbnailLabel}>Reference image attached</span>
          </div>
        )}

        <div style={{
          ...styles.inputRow,
          ...(isMobile ? { padding: '4px 4px 4px 6px' } : {}),
        }}>
          {/* Image upload button */}
          <button
            style={{
              ...styles.uploadBtn,
              ...(isMobile ? { minWidth: 44, minHeight: 44 } : {}),
            }}
            onClick={() => fileInputRef.current?.click()}
            disabled={isListening || ws.isThinking || !ws.connected}
            title="Attach reference image"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
            </svg>
          </button>
          {hasMic && (
            <button
              style={{
                ...styles.micBtn(isListening),
                ...(isMobile && !isListening ? { padding: '0 10px', minWidth: 44, minHeight: 44 } : {}),
              }}
              onClick={toggleMic}
              title={isListening ? 'Stop listening' : 'Speak your idea'}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
              {!isListening && !isMobile && <span style={styles.micLabel}>Voice</span>}
            </button>
          )}
          <input
            style={{
              ...styles.input,
              ...(isMobile ? { padding: '10px 8px', fontSize: 14 } : {}),
            }}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleSend() } }}
            placeholder={isListening ? 'Listening...' : 'Describe your video idea...'}
            disabled={isListening || ws.isThinking || !ws.connected}
            aria-label="Video idea input"
            autoComplete="off"
          />
          <button
            style={{
              ...styles.sendBtn,
              ...(isMobile ? { minWidth: 44, minHeight: 44 } : {}),
            }}
            onClick={handleSend}
            disabled={!input.trim() || isListening || ws.isThinking || !ws.connected}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
        {!isMobile && (
          <div style={styles.shortcutHint}>
            <kbd style={styles.kbd}>Enter</kbd> to send
            {hasMic && <><span style={styles.hintDot} /><kbd style={styles.kbd}>V</kbd> for voice</>}
          </div>
        )}
      </div>
    </div>
  )
}

const styles = {
  container: {
    maxWidth: 860,
    margin: '0 auto',
    padding: '0 24px',
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    position: 'relative',
    overflow: 'hidden',
  },
  glowOrb1: {
    position: 'fixed',
    top: -200,
    right: -200,
    width: 500,
    height: 500,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(102,126,234,0.1) 0%, transparent 70%)',
    pointerEvents: 'none',
    animation: 'float 8s ease-in-out infinite',
  },
  glowOrb2: {
    position: 'fixed',
    bottom: -200,
    left: -200,
    width: 500,
    height: 500,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(118,75,162,0.08) 0%, transparent 70%)',
    pointerEvents: 'none',
  },
  header: {
    textAlign: 'center',
    padding: '24px 0 16px',
    borderBottom: '1px solid rgba(255,255,255,0.04)',
  },
  logoWrap: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  logoIcon: {
    fontSize: 28,
    background: 'linear-gradient(135deg, #667eea, #764ba2)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  title: {
    fontSize: 28,
    fontWeight: 800,
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    letterSpacing: -1,
  },
  headerSub: {
    color: '#4a5070',
    fontSize: 13,
    marginTop: 4,
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  messages: {
    flex: 1,
    overflowY: 'auto',
    padding: '24px 0',
    scrollbarWidth: 'thin',
    scrollbarColor: '#333 transparent',
  },
  msgRow: (role) => ({
    display: 'flex',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 20,
    flexDirection: role === 'user' ? 'row-reverse' : 'row',
    animation: 'fadeIn 0.3s ease-out',
  }),
  avatar: (role) => ({
    width: 36,
    height: 36,
    borderRadius: 10,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: 0.5,
    flexShrink: 0,
    background: role === 'user'
      ? 'linear-gradient(135deg, #1a1a3e, #2a2a5e)'
      : 'linear-gradient(135deg, #667eea, #764ba2)',
    color: '#fff',
  }),
  msg: (role) => ({
    padding: '14px 18px',
    borderRadius: 16,
    maxWidth: '75%',
    lineHeight: 1.7,
    fontSize: 14,
    whiteSpace: 'pre-wrap',
    background: role === 'user'
      ? 'rgba(20, 20, 50, 0.7)'
      : 'rgba(12, 16, 32, 0.7)',
    backdropFilter: 'blur(16px)',
    border: role === 'user'
      ? '1px solid rgba(102,126,234,0.12)'
      : '1px solid rgba(255,255,255,0.03)',
    borderBottomRightRadius: role === 'user' ? 4 : 16,
    borderBottomLeftRadius: role === 'user' ? 16 : 4,
    color: role === 'user' ? '#b8c0e8' : '#c8cee8',
  }),
  thinkingBubble: {
    padding: '18px 24px',
    borderRadius: 16,
    background: 'rgba(12, 16, 32, 0.7)',
    backdropFilter: 'blur(16px)',
    border: '1px solid rgba(255,255,255,0.03)',
    borderBottomLeftRadius: 4,
    display: 'flex',
    gap: 6,
    alignItems: 'center',
  },
  dot1: {
    width: 8, height: 8, borderRadius: '50%', background: '#667eea',
    animation: 'pulse 1.4s ease-in-out infinite',
  },
  dot2: {
    width: 8, height: 8, borderRadius: '50%', background: '#667eea',
    animation: 'pulse 1.4s ease-in-out 0.2s infinite',
  },
  dot3: {
    width: 8, height: 8, borderRadius: '50%', background: '#667eea',
    animation: 'pulse 1.4s ease-in-out 0.4s infinite',
  },
  planEditorWrap: {
    margin: '16px 0',
    padding: 20,
    background: 'rgba(8,8,20,0.7)',
    backdropFilter: 'blur(16px)',
    borderRadius: 20,
    border: '1px solid rgba(102,126,234,0.08)',
    animation: 'fadeInScale 0.4s ease-out',
  },
  previewWrap: {
    margin: '16px 0 16px 48px',
    position: 'relative',
  },
  preview: {
    maxWidth: '100%',
    borderRadius: 16,
    boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
    border: '1px solid rgba(255,255,255,0.06)',
  },
  previewLabel: {
    position: 'absolute',
    bottom: 12,
    left: 12,
    background: 'rgba(0,0,0,0.7)',
    backdropFilter: 'blur(8px)',
    padding: '6px 14px',
    borderRadius: 8,
    fontSize: 12,
    color: '#aaa',
    fontWeight: 600,
  },
  error: {
    color: '#ff8a8a',
    padding: '12px 16px',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    background: 'rgba(255,107,107,0.06)',
    borderRadius: 12,
    border: '1px solid rgba(255,107,107,0.12)',
    marginBottom: 8,
    fontSize: 13,
    animation: 'fadeIn 0.3s ease-out',
  },
  errorDismiss: {
    background: 'transparent',
    border: 'none',
    color: '#ff8a8a',
    cursor: 'pointer',
    padding: 4,
    borderRadius: 6,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    opacity: 0.6,
  },
  connectionBanner: {
    padding: '10px 16px',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    background: 'rgba(245,158,11,0.06)',
    borderRadius: 12,
    border: '1px solid rgba(245,158,11,0.12)',
    marginBottom: 8,
    fontSize: 13,
    color: '#f59e0b',
    fontWeight: 500,
    animation: 'fadeIn 0.3s ease-out',
  },
  connectionDot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
    background: '#f59e0b',
    animation: 'pulse 1.5s ease-in-out infinite',
    flexShrink: 0,
  },
  // Listening overlay — full screen, unmistakable
  listeningOverlay: {
    position: 'fixed',
    top: 0, left: 0, right: 0, bottom: 0,
    background: 'rgba(0,0,0,0.85)',
    backdropFilter: 'blur(20px)',
    zIndex: 100,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    animation: 'fadeIn 0.2s ease-out',
  },
  listeningContent: {
    textAlign: 'center',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 16,
  },
  micWave: {
    display: 'flex',
    alignItems: 'center',
    gap: 4,
    height: 60,
  },
  wave1: { width: 4, height: 20, borderRadius: 2, background: '#e74c3c', animation: 'waveBar 1s ease-in-out 0.0s infinite' },
  wave2: { width: 4, height: 36, borderRadius: 2, background: '#e74c3c', animation: 'waveBar 1s ease-in-out 0.1s infinite' },
  wave3: { width: 4, height: 50, borderRadius: 2, background: '#e74c3c', animation: 'waveBar 1s ease-in-out 0.2s infinite' },
  wave4: { width: 4, height: 36, borderRadius: 2, background: '#e74c3c', animation: 'waveBar 1s ease-in-out 0.3s infinite' },
  wave5: { width: 4, height: 20, borderRadius: 2, background: '#e74c3c', animation: 'waveBar 1s ease-in-out 0.4s infinite' },
  listeningText: {
    fontSize: 24,
    fontWeight: 800,
    color: '#e74c3c',
    letterSpacing: 1,
  },
  listeningHint: {
    fontSize: 16,
    color: '#aaa',
    maxWidth: 400,
    minHeight: 24,
  },
  stopBtn: {
    marginTop: 12,
    padding: '14px 40px',
    borderRadius: 14,
    background: 'linear-gradient(135deg, #e74c3c, #c0392b)',
    color: '#fff',
    border: 'none',
    cursor: 'pointer',
    fontSize: 16,
    fontWeight: 700,
    boxShadow: '0 4px 24px rgba(231,76,60,0.4)',
  },
  inputArea: {
    paddingBottom: 20,
  },
  inputRow: {
    display: 'flex',
    gap: 8,
    alignItems: 'center',
    background: 'rgba(10, 10, 20, 0.8)',
    backdropFilter: 'blur(16px)',
    borderRadius: 18,
    border: '1px solid rgba(255,255,255,0.06)',
    padding: '6px 6px 6px 8px',
    transition: 'border-color 0.3s',
  },
  micBtn: (active) => ({
    minWidth: active ? 44 : 'auto',
    height: 44,
    borderRadius: 14,
    border: 'none',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    flexShrink: 0,
    padding: active ? 0 : '0 14px',
    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
    background: active
      ? 'linear-gradient(135deg, #e74c3c, #c0392b)'
      : 'rgba(255,255,255,0.04)',
    color: active ? '#fff' : '#6b7cc7',
    boxShadow: active ? '0 0 24px rgba(231,76,60,0.4)' : 'none',
  }),
  micLabel: {
    fontSize: 12,
    fontWeight: 600,
  },
  input: {
    flex: 1,
    padding: '12px 14px',
    borderRadius: 12,
    border: 'none',
    background: 'transparent',
    color: '#fff',
    fontSize: 15,
    outline: 'none',
  },
  sendBtn: {
    width: 44,
    height: 44,
    borderRadius: 14,
    background: 'linear-gradient(135deg, #667eea, #764ba2)',
    color: '#fff',
    border: 'none',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    transition: 'transform 0.2s',
  },
  uploadBtn: {
    height: 44,
    minWidth: 44,
    borderRadius: 14,
    border: 'none',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    background: 'rgba(255,255,255,0.04)',
    color: '#6b7cc7',
    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
  },
  thumbnailRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '8px 12px 0',
  },
  thumbnailWrap: {
    position: 'relative',
    width: 48,
    height: 48,
    flexShrink: 0,
  },
  thumbnail: {
    width: 48,
    height: 48,
    borderRadius: 10,
    objectFit: 'cover',
    border: '1px solid rgba(102,126,234,0.3)',
  },
  thumbnailRemove: {
    position: 'absolute',
    top: -6,
    right: -6,
    width: 20,
    height: 20,
    borderRadius: '50%',
    background: 'rgba(255,80,80,0.9)',
    color: '#fff',
    border: 'none',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 0,
  },
  thumbnailLabel: {
    fontSize: 12,
    color: '#888',
    fontWeight: 500,
  },
  msgImage: {
    maxWidth: '100%',
    maxHeight: 120,
    borderRadius: 10,
    marginBottom: 8,
    objectFit: 'cover',
    border: '1px solid rgba(255,255,255,0.08)',
    display: 'block',
  },
  shortcutHint: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    padding: '6px 0 0',
    fontSize: 11,
    color: '#3a4060',
  },
  kbd: {
    padding: '1px 6px',
    borderRadius: 4,
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.06)',
    fontFamily: 'inherit',
    fontSize: 10,
    fontWeight: 600,
    color: '#5a6080',
  },
  hintDot: {
    width: 3,
    height: 3,
    borderRadius: '50%',
    background: '#3a4060',
  },
}
