import React from 'react'
import useWebSocket from './hooks/useWebSocket'
import ConversationView from './components/ConversationView'
import GeneratingView from './components/GeneratingView'
import DoneView from './components/DoneView'

const styles = {
  container: {
    maxWidth: 800,
    margin: '0 auto',
    padding: 20,
    minHeight: '100vh',
  },
  header: {
    textAlign: 'center',
    padding: '80px 0 40px',
  },
  title: {
    fontSize: 64,
    fontWeight: 800,
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    letterSpacing: -2,
  },
  subtitle: {
    color: '#888',
    marginTop: 12,
    fontSize: 18,
  },
  startBtn: {
    display: 'block',
    margin: '60px auto',
    padding: '18px 56px',
    fontSize: 18,
    fontWeight: 600,
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: '#fff',
    border: 'none',
    borderRadius: 14,
    cursor: 'pointer',
    transition: 'transform 0.2s, box-shadow 0.2s',
    boxShadow: '0 4px 20px rgba(102, 126, 234, 0.3)',
  },
}

export default function App() {
  const ws = useWebSocket()

  const isGenerating = ws.progress && !ws.videoUrl
  const isDone = !!ws.videoUrl

  if (!ws.connected) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <h1 style={styles.title}>CutTo</h1>
          <p style={styles.subtitle}>Describe a video. We'll make it.</p>
        </div>
        <button
          style={styles.startBtn}
          onClick={ws.connect}
          onMouseOver={e => { e.target.style.transform = 'scale(1.05)'; e.target.style.boxShadow = '0 6px 30px rgba(102, 126, 234, 0.5)' }}
          onMouseOut={e => { e.target.style.transform = 'scale(1)'; e.target.style.boxShadow = '0 4px 20px rgba(102, 126, 234, 0.3)' }}
        >
          Start Creating
        </button>
      </div>
    )
  }

  if (isDone) return <DoneView videoUrl={ws.videoUrl} onReset={() => window.location.reload()} />
  if (isGenerating) return <GeneratingView progress={ws.progress} scenePlan={ws.scenePlan} />
  return <ConversationView ws={ws} />
}
