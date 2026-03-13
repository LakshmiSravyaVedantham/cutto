import React from 'react'
import useWebSocket from './hooks/useWebSocket'
import useIsMobile from './hooks/useIsMobile'
import ConversationView from './components/ConversationView'
import GeneratingView from './components/GeneratingView'
import DoneView from './components/DoneView'

export default function App() {
  const ws = useWebSocket()
  const isMobile = useIsMobile()

  const isGenerating = ws.progress && !ws.videoUrl
  const isDone = !!ws.videoUrl

  if (!ws.connected) {
    return (
      <div style={styles.container}>
        <div style={styles.glowOrb1} />
        <div style={styles.glowOrb2} />
        <div style={styles.glowOrb3} />

        <div style={styles.header}>
          <div style={styles.logoWrap}>
            <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="url(#landingGrad)" strokeWidth="1.5" style={{ animation: 'float 3s ease-in-out infinite' }}>
              <defs>
                <linearGradient id="landingGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#667eea" />
                  <stop offset="100%" stopColor="#764ba2" />
                </linearGradient>
              </defs>
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
          </div>
          <h1 style={{
            ...styles.title,
            ...(isMobile ? { fontSize: 48, letterSpacing: -2 } : {}),
          }}>CutTo</h1>
          <p style={{
            ...styles.subtitle,
            ...(isMobile ? { fontSize: 16 } : {}),
          }}>Describe any video. We'll direct it.</p>
          <p style={styles.description}>
            Medical explainer, animated story, product demo, tutorial, documentary —
            just describe what you need. CutTo writes the script, generates visuals,
            adds voiceover with lipsync, and delivers a finished video.
          </p>
        </div>

        <div style={{
          ...styles.features,
          ...(isMobile ? { flexDirection: 'column', gap: 10, marginTop: 32 } : {}),
        }}>
          {[
            { icon: '🎬', label: 'Any Video Type', desc: 'Stories, explainers, tutorials, marketing, documentaries' },
            { icon: '🎨', label: 'AI-Generated Visuals', desc: 'Animated scenes, diagrams, cinematic footage via Veo' },
            { icon: '🎙️', label: 'Voice, Lipsync & Music', desc: 'Multi-character voices, lipsync, mood-matched soundtrack' },
          ].map((f, i) => (
            <div key={i} style={styles.featureCard}>
              <span style={styles.featureIcon}>{f.icon}</span>
              <span style={styles.featureLabel}>{f.label}</span>
              <span style={styles.featureDesc}>{f.desc}</span>
            </div>
          ))}
        </div>

        <button
          style={{
            ...styles.startBtn,
            ...(isMobile ? { padding: '18px 40px', fontSize: 16 } : {}),
          }}
          onClick={ws.connect}
          onMouseOver={e => {
            e.currentTarget.style.transform = 'translateY(-3px) scale(1.02)'
            e.currentTarget.style.boxShadow = '0 8px 40px rgba(102,126,234,0.45)'
          }}
          onMouseOut={e => {
            e.currentTarget.style.transform = 'translateY(0) scale(1)'
            e.currentTarget.style.boxShadow = '0 4px 24px rgba(102,126,234,0.3)'
          }}
        >
          Start Creating
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ marginLeft: 8 }}>
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" />
          </svg>
        </button>

        <div style={{
          ...styles.quickStart,
          ...(isMobile ? { flexDirection: 'column' } : {}),
        }}>
          <p style={styles.quickStartLabel}>Or try a quick start:</p>
          <div style={{
            ...styles.quickStartChips,
            ...(isMobile ? { flexDirection: 'column', alignItems: 'stretch' } : {}),
          }}>
            {[
              { label: 'How the heart works', prompt: 'Create a 90-second medical explainer on how the human heart pumps blood through its four chambers. Target audience: high school biology students. Style: clean 3D medical animation with labels.' },
              { label: 'Pixar-style story', prompt: 'Create an animated short story about a lonely robot in a junkyard who discovers a flower growing through the metal. Pixar style, warm and emotional, inspiring mood.' },
              { label: 'Product launch video', prompt: 'Create a sleek product launch video for a new AI-powered fitness watch called "PulseAI". Modern, clean, upbeat. Show features: heart rate, sleep tracking, AI coaching.' },
            ].map((t, i) => (
              <button
                key={i}
                style={styles.quickChip}
                onClick={() => ws.connectWithPrompt(t.prompt)}
                onMouseOver={e => {
                  e.currentTarget.style.borderColor = 'rgba(102,126,234,0.4)'
                  e.currentTarget.style.background = 'rgba(102,126,234,0.1)'
                }}
                onMouseOut={e => {
                  e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'
                  e.currentTarget.style.background = 'rgba(17,17,17,0.6)'
                }}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <div style={styles.techStack}>
          <span style={styles.techBadge}>Gemini 2.0</span>
          <span style={styles.techBadge}>Veo 2.0</span>
          <span style={styles.techBadge}>Imagen 4.0</span>
          <span style={styles.techBadge}>Cloud TTS</span>
          <span style={styles.techBadge}>Cloud Run</span>
        </div>
        <p style={styles.poweredBy}>
          Built with Google AI &amp; Google Cloud
        </p>
      </div>
    )
  }

  if (isDone) return (
    <DoneView
      videoUrl={ws.videoUrl}
      onReset={ws.reset}
    />
  )
  if (isGenerating) return (
    <GeneratingView
      progress={ws.progress}
      sceneStatuses={ws.sceneStatuses}
      scenePlan={ws.scenePlan}
    />
  )
  return <ConversationView ws={ws} />
}

const styles = {
  container: {
    maxWidth: 800,
    margin: '0 auto',
    padding: '0 24px',
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    overflow: 'hidden',
  },
  glowOrb1: {
    position: 'fixed',
    top: -250,
    right: -250,
    width: 600,
    height: 600,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(102,126,234,0.1) 0%, transparent 70%)',
    pointerEvents: 'none',
  },
  glowOrb2: {
    position: 'fixed',
    bottom: -250,
    left: -250,
    width: 600,
    height: 600,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(118,75,162,0.08) 0%, transparent 70%)',
    pointerEvents: 'none',
  },
  glowOrb3: {
    position: 'fixed',
    top: '40%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: 800,
    height: 800,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(102,126,234,0.03) 0%, transparent 50%)',
    pointerEvents: 'none',
  },
  header: {
    textAlign: 'center',
    animation: 'fadeIn 0.8s ease-out',
  },
  logoWrap: {
    marginBottom: 20,
  },
  title: {
    fontSize: 72,
    fontWeight: 900,
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    letterSpacing: -3,
    lineHeight: 1,
  },
  subtitle: {
    color: '#999',
    marginTop: 12,
    fontSize: 20,
    fontWeight: 500,
    letterSpacing: 0.5,
  },
  description: {
    color: '#555',
    marginTop: 16,
    fontSize: 14,
    lineHeight: 1.7,
    maxWidth: 480,
  },
  features: {
    display: 'flex',
    gap: 12,
    marginTop: 48,
    animation: 'fadeIn 0.8s ease-out 0.3s both',
  },
  featureCard: {
    flex: 1,
    padding: '24px 16px',
    background: 'rgba(17,17,17,0.6)',
    backdropFilter: 'blur(10px)',
    borderRadius: 18,
    border: '1px solid rgba(255,255,255,0.05)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 8,
    textAlign: 'center',
  },
  featureIcon: {
    fontSize: 28,
  },
  featureLabel: {
    fontSize: 13,
    fontWeight: 700,
    color: '#ddd',
    letterSpacing: 0.3,
  },
  featureDesc: {
    fontSize: 11,
    color: '#666',
    lineHeight: 1.5,
  },
  startBtn: {
    marginTop: 48,
    padding: '20px 56px',
    fontSize: 18,
    fontWeight: 700,
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: '#fff',
    border: 'none',
    borderRadius: 18,
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    boxShadow: '0 4px 24px rgba(102,126,234,0.3)',
    display: 'flex',
    alignItems: 'center',
    animation: 'fadeIn 0.8s ease-out 0.5s both',
  },
  techStack: {
    display: 'flex',
    gap: 8,
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginTop: 32,
    animation: 'fadeIn 0.8s ease-out 0.7s both',
  },
  techBadge: {
    padding: '4px 12px',
    borderRadius: 8,
    background: 'rgba(102,126,234,0.08)',
    border: '1px solid rgba(102,126,234,0.12)',
    color: '#667eea',
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: 0.3,
  },
  poweredBy: {
    marginTop: 12,
    color: '#333',
    fontSize: 11,
    letterSpacing: 1,
    textTransform: 'uppercase',
    animation: 'fadeIn 0.8s ease-out 0.8s both',
  },
  quickStart: {
    marginTop: 32,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 12,
    animation: 'fadeIn 0.8s ease-out 0.6s both',
  },
  quickStartLabel: {
    fontSize: 12,
    color: '#555',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  quickStartChips: {
    display: 'flex',
    gap: 8,
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  quickChip: {
    padding: '10px 18px',
    borderRadius: 12,
    background: 'rgba(17,17,17,0.6)',
    border: '1px solid rgba(255,255,255,0.08)',
    color: '#aaa',
    fontSize: 13,
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s',
    backdropFilter: 'blur(10px)',
  },
}
