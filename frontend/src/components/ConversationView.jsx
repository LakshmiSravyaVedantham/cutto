import React, { useState, useRef, useEffect } from 'react'
import ScenePlanEditor from './ScenePlanEditor'
import useIsMobile from '../hooks/useIsMobile'

export default function ConversationView({ ws }) {
  const isMobile = useIsMobile()
  const [input, setInput] = useState('')
  const [isListening, setIsListening] = useState(false)
  const bottomRef = useRef(null)
  const recognitionRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [ws.messages, ws.previews, ws.isThinking, ws.scenePlan])

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

  const handleSend = () => {
    if (!input.trim()) return
    ws.sendText(input.trim())
    setInput('')
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
      <div style={styles.glowOrb1} />
      <div style={styles.glowOrb2} />

      <div style={styles.header}>
        <div style={styles.logoWrap}>
          <span style={styles.logoIcon}>&#9655;</span>
          <h1 style={styles.title}>CutTo</h1>
        </div>
        <p style={styles.headerSub}>Your AI Video Director</p>
      </div>

      <div style={styles.messages}>
        {ws.messages.map((m, i) => (
          <div key={i} style={styles.msgRow(m.role)}>
            <div style={styles.avatar(m.role)}>
              {m.role === 'user' ? 'You' : 'AI'}
            </div>
            <div style={{
              ...styles.msg(m.role),
              ...(isMobile ? { maxWidth: '85%', padding: '12px 14px', fontSize: 13 } : {}),
            }}>
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

      {ws.error && (
        <div style={styles.error}>{ws.error}</div>
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

      <div style={{
        ...styles.inputArea,
        ...(isMobile ? { paddingBottom: 12 } : {}),
      }}>
        <div style={{
          ...styles.inputRow,
          ...(isMobile ? { padding: '4px 4px 4px 6px' } : {}),
        }}>
          {recognitionRef.current && (
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
            disabled={isListening}
          />
          <button
            style={{
              ...styles.sendBtn,
              ...(isMobile ? { minWidth: 44, minHeight: 44 } : {}),
            }}
            onClick={handleSend}
            disabled={!input.trim() || isListening}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
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
    background: 'radial-gradient(circle, rgba(102,126,234,0.08) 0%, transparent 70%)',
    pointerEvents: 'none',
  },
  glowOrb2: {
    position: 'fixed',
    bottom: -200,
    left: -200,
    width: 500,
    height: 500,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(118,75,162,0.06) 0%, transparent 70%)',
    pointerEvents: 'none',
  },
  header: {
    textAlign: 'center',
    padding: '24px 0 16px',
    borderBottom: '1px solid rgba(255,255,255,0.06)',
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
    color: '#555',
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
    lineHeight: 1.6,
    fontSize: 14,
    whiteSpace: 'pre-wrap',
    background: role === 'user'
      ? 'rgba(26, 26, 62, 0.6)'
      : 'rgba(22, 33, 62, 0.6)',
    backdropFilter: 'blur(10px)',
    border: role === 'user'
      ? '1px solid rgba(102,126,234,0.15)'
      : '1px solid rgba(255,255,255,0.04)',
    borderBottomRightRadius: role === 'user' ? 4 : 16,
    borderBottomLeftRadius: role === 'user' ? 16 : 4,
    color: role === 'user' ? '#c8d0ff' : '#ddd',
  }),
  thinkingBubble: {
    padding: '18px 24px',
    borderRadius: 16,
    background: 'rgba(22, 33, 62, 0.6)',
    backdropFilter: 'blur(10px)',
    border: '1px solid rgba(255,255,255,0.04)',
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
    background: 'rgba(10,10,30,0.6)',
    backdropFilter: 'blur(10px)',
    borderRadius: 20,
    border: '1px solid rgba(102,126,234,0.1)',
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
    color: '#ff6b6b',
    padding: '12px 16px',
    textAlign: 'center',
    background: 'rgba(255,107,107,0.08)',
    borderRadius: 12,
    border: '1px solid rgba(255,107,107,0.15)',
    marginBottom: 8,
    fontSize: 14,
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
    background: 'rgba(17, 17, 17, 0.8)',
    backdropFilter: 'blur(10px)',
    borderRadius: 18,
    border: '1px solid rgba(255,255,255,0.08)',
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
    transition: 'all 0.2s',
    background: active
      ? 'linear-gradient(135deg, #e74c3c, #c0392b)'
      : 'rgba(255,255,255,0.06)',
    color: active ? '#fff' : '#888',
    boxShadow: active ? '0 0 20px rgba(231,76,60,0.4)' : 'none',
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
}
