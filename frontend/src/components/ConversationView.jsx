import React, { useState, useRef, useEffect } from 'react'

const styles = {
  container: {
    maxWidth: 800,
    margin: '0 auto',
    padding: 20,
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
  },
  header: {
    textAlign: 'center',
    padding: '20px 0',
    borderBottom: '1px solid #1a1a2e',
  },
  title: {
    fontSize: 24,
    fontWeight: 700,
    background: 'linear-gradient(135deg, #667eea, #764ba2)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  messages: {
    flex: 1,
    overflowY: 'auto',
    padding: '20px 0',
  },
  msg: {
    marginBottom: 16,
    padding: '14px 18px',
    borderRadius: 16,
    maxWidth: '85%',
    lineHeight: 1.5,
    fontSize: 15,
    whiteSpace: 'pre-wrap',
  },
  user: {
    background: 'linear-gradient(135deg, #1a1a3e, #1a1a2e)',
    marginLeft: 'auto',
    textAlign: 'right',
    borderBottomRightRadius: 4,
  },
  agent: {
    background: '#16213e',
    borderBottomLeftRadius: 4,
  },
  preview: {
    maxWidth: '100%',
    borderRadius: 12,
    marginTop: 12,
    marginBottom: 12,
    boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
  },
  inputRow: {
    display: 'flex',
    gap: 10,
    padding: '16px 0',
  },
  input: {
    flex: 1,
    padding: '14px 18px',
    borderRadius: 14,
    border: '1px solid #333',
    background: '#111',
    color: '#fff',
    fontSize: 16,
    outline: 'none',
    transition: 'border-color 0.2s',
  },
  sendBtn: {
    padding: '14px 28px',
    borderRadius: 14,
    background: 'linear-gradient(135deg, #667eea, #764ba2)',
    color: '#fff',
    border: 'none',
    cursor: 'pointer',
    fontSize: 16,
    fontWeight: 600,
  },
  approveBtn: {
    padding: '16px 28px',
    borderRadius: 14,
    background: 'linear-gradient(135deg, #27ae60, #2ecc71)',
    color: '#fff',
    border: 'none',
    cursor: 'pointer',
    fontSize: 16,
    fontWeight: 600,
    width: '100%',
    marginTop: 8,
    boxShadow: '0 4px 20px rgba(39, 174, 96, 0.3)',
  },
}

export default function ConversationView({ ws }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [ws.messages, ws.previews])

  const handleSend = () => {
    if (!input.trim()) return
    ws.sendText(input.trim())
    setInput('')
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>CutTo</h1>
      </div>

      <div style={styles.messages}>
        {ws.messages.map((m, i) => (
          <div
            key={i}
            style={{
              ...styles.msg,
              ...(m.role === 'user' ? styles.user : styles.agent),
            }}
          >
            {m.text}
          </div>
        ))}
        {ws.previews.map((img, i) => (
          <img
            key={`img-${i}`}
            src={`data:image/png;base64,${img}`}
            alt={`Scene preview ${i + 1}`}
            style={styles.preview}
          />
        ))}
        <div ref={bottomRef} />
      </div>

      {ws.error && (
        <div style={{ color: '#e74c3c', padding: 12, textAlign: 'center' }}>
          {ws.error}
        </div>
      )}

      {ws.scenePlan && (
        <button style={styles.approveBtn} onClick={ws.approve}>
          Looks good — Make my video!
        </button>
      )}

      <div style={styles.inputRow}>
        <input
          style={styles.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Describe your video idea..."
          onFocus={(e) => (e.target.style.borderColor = '#667eea')}
          onBlur={(e) => (e.target.style.borderColor = '#333')}
        />
        <button style={styles.sendBtn} onClick={handleSend}>
          Send
        </button>
      </div>
    </div>
  )
}
