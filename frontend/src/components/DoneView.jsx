import React, { useState, useEffect } from 'react'
import useIsMobile from '../hooks/useIsMobile'

function Confetti() {
  const [particles] = useState(() =>
    Array.from({ length: 24 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      delay: Math.random() * 0.8,
      duration: 1.5 + Math.random() * 1.5,
      size: 4 + Math.random() * 4,
      color: ['#667eea', '#764ba2', '#27ae60', '#2ecc71', '#e879f9', '#34d399'][i % 6],
    }))
  )

  return (
    <div style={{ position: 'fixed', top: '40%', left: 0, right: 0, pointerEvents: 'none', zIndex: 50 }}>
      {particles.map(p => (
        <div
          key={p.id}
          style={{
            position: 'absolute',
            left: `${p.left}%`,
            width: p.size,
            height: p.size,
            borderRadius: '50%',
            background: p.color,
            animation: `confetti ${p.duration}s ease-out ${p.delay}s forwards`,
            opacity: 0,
          }}
        />
      ))}
    </div>
  )
}

export default function DoneView({ videoUrl, onReset, onEditScenes }) {
  const isMobile = useIsMobile()
  const [videoError, setVideoError] = useState(false)
  const [retrying, setRetrying] = useState(false)
  const [showConfetti, setShowConfetti] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => setShowConfetti(false), 3500)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div style={{
      ...styles.container,
      ...(isMobile ? { padding: '0 12px' } : {}),
    }}>
      {showConfetti && <Confetti />}
      <div style={styles.glowOrb1} aria-hidden="true" />
      <div style={styles.glowOrb2} aria-hidden="true" />
      <div style={styles.glowOrb3} aria-hidden="true" />

      <div style={{
        ...styles.header,
        ...(isMobile ? { paddingTop: 32, paddingBottom: 20 } : {}),
      }}>
        <div style={styles.successIcon}>
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#27ae60" strokeWidth="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
        </div>
        <h2 style={{
          ...styles.title,
          ...(isMobile ? { fontSize: 24 } : {}),
        }}>Your video is ready</h2>
        <p style={styles.subtitle}>Watch, download, or create another</p>
      </div>

      <div style={{
        ...styles.videoWrap,
        ...(isMobile ? { maxWidth: '100%' } : {}),
      }}>
        {videoError ? (
          <div style={{ padding: 32, textAlign: 'center' }}>
            <p style={{ fontSize: 14, marginBottom: 4, color: '#ff8a8a' }}>Video couldn't load in this browser</p>
            <p style={{ fontSize: 12, marginBottom: 16, color: '#5a6080' }}>Try reloading or download the file directly</p>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
              <button
                style={{
                  padding: '10px 20px', borderRadius: 10,
                  background: 'linear-gradient(135deg, #667eea, #764ba2)',
                  color: '#fff', border: 'none', cursor: 'pointer',
                  fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6,
                }}
                onClick={() => { setRetrying(true); setVideoError(false); setTimeout(() => setRetrying(false), 500) }}
              >
                {retrying ? 'Retrying...' : 'Retry Playback'}
              </button>
              <a href={videoUrl} download style={{
                padding: '10px 20px', borderRadius: 10,
                background: 'rgba(102,126,234,0.1)', color: '#667eea',
                border: '1px solid rgba(102,126,234,0.2)',
                textDecoration: 'none', fontSize: 13, fontWeight: 600,
              }}>
                Download Instead
              </a>
            </div>
          </div>
        ) : (
          <video style={{
            ...styles.video,
            ...(isMobile ? { borderRadius: 14 } : {}),
          }} src={videoUrl} controls autoPlay onError={() => setVideoError(true)} />
        )}
        <div style={styles.videoGlow} />
      </div>

      <div style={{
        ...styles.btnRow,
        ...(isMobile ? { flexDirection: 'column', width: '100%', gap: 10 } : {}),
      }}>
        <a style={{
          ...styles.downloadBtn,
          ...(isMobile ? { width: '100%', justifyContent: 'center', padding: '16px 20px', minHeight: 52 } : {}),
        }} href={videoUrl} download
          onMouseOver={e => {
            e.currentTarget.style.transform = 'translateY(-2px)'
            e.currentTarget.style.boxShadow = '0 12px 40px rgba(102,126,234,0.45)'
          }}
          onMouseOut={e => {
            e.currentTarget.style.transform = 'translateY(0)'
            e.currentTarget.style.boxShadow = '0 4px 24px rgba(102,126,234,0.3)'
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Download Video
        </a>
        {onEditScenes && (
          <button style={{
            ...styles.editBtn,
            ...(isMobile ? { width: '100%', justifyContent: 'center', padding: '16px 20px', minHeight: 52 } : {}),
          }} onClick={onEditScenes}
            onMouseOver={e => {
              e.currentTarget.style.borderColor = 'rgba(102,126,234,0.3)'
              e.currentTarget.style.background = 'rgba(102,126,234,0.1)'
            }}
            onMouseOut={e => {
              e.currentTarget.style.borderColor = 'rgba(102,126,234,0.15)'
              e.currentTarget.style.background = 'rgba(12,12,24,0.8)'
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
            Edit Scenes
          </button>
        )}
        <button style={{
          ...styles.resetBtn,
          ...(isMobile ? { width: '100%', justifyContent: 'center', padding: '16px 20px', minHeight: 52 } : {}),
        }} onClick={onReset}
          onMouseOver={e => {
            e.currentTarget.style.borderColor = 'rgba(255,255,255,0.15)'
            e.currentTarget.style.background = 'rgba(255,255,255,0.06)'
          }}
          onMouseOut={e => {
            e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'
            e.currentTarget.style.background = 'rgba(12,12,24,0.8)'
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
          Make Another
        </button>
      </div>

      <p style={styles.watermark}>Made with CutTo</p>
    </div>
  )
}

const styles = {
  container: {
    maxWidth: 800,
    margin: '0 auto',
    padding: '0 24px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    minHeight: '100vh',
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
    background: 'radial-gradient(circle, rgba(39,174,96,0.08) 0%, transparent 70%)',
    pointerEvents: 'none',
  },
  glowOrb2: {
    position: 'fixed',
    bottom: -200,
    left: -200,
    width: 500,
    height: 500,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(102,126,234,0.06) 0%, transparent 70%)',
    pointerEvents: 'none',
  },
  glowOrb3: {
    position: 'fixed',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: 600,
    height: 600,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(118,75,162,0.04) 0%, transparent 60%)',
    pointerEvents: 'none',
  },
  header: {
    textAlign: 'center',
    paddingTop: 48,
    paddingBottom: 28,
    animation: 'fadeIn 0.6s ease-out',
  },
  successIcon: {
    marginBottom: 16,
    animation: 'glowPulse 2s ease-in-out infinite',
    borderRadius: '50%',
    display: 'inline-flex',
    padding: 8,
  },
  title: {
    fontSize: 32,
    fontWeight: 800,
    background: 'linear-gradient(135deg, #27ae60, #2ecc71)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    letterSpacing: -0.5,
  },
  subtitle: {
    color: '#5a6080',
    fontSize: 14,
    marginTop: 6,
  },
  videoWrap: {
    position: 'relative',
    width: '100%',
    maxWidth: 720,
    marginBottom: 32,
    animation: 'fadeInScale 0.6s ease-out 0.2s both',
  },
  video: {
    width: '100%',
    borderRadius: 20,
    border: '1px solid rgba(255,255,255,0.06)',
    boxShadow: '0 16px 64px rgba(0,0,0,0.6)',
    position: 'relative',
    zIndex: 1,
  },
  videoGlow: {
    position: 'absolute',
    bottom: -24,
    left: '8%',
    right: '8%',
    height: 80,
    background: 'radial-gradient(ellipse, rgba(102,126,234,0.2) 0%, transparent 70%)',
    filter: 'blur(24px)',
    pointerEvents: 'none',
  },
  btnRow: {
    display: 'flex',
    gap: 12,
    justifyContent: 'center',
    animation: 'fadeIn 0.6s ease-out 0.4s both',
  },
  downloadBtn: {
    padding: '16px 32px',
    borderRadius: 16,
    background: 'linear-gradient(135deg, #667eea, #764ba2)',
    color: '#fff',
    border: 'none',
    cursor: 'pointer',
    fontSize: 15,
    fontWeight: 700,
    textDecoration: 'none',
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    boxShadow: '0 4px 24px rgba(102,126,234,0.3)',
  },
  editBtn: {
    padding: '16px 32px',
    borderRadius: 16,
    background: 'rgba(12,12,24,0.8)',
    backdropFilter: 'blur(10px)',
    color: '#667eea',
    border: '1px solid rgba(102,126,234,0.15)',
    cursor: 'pointer',
    fontSize: 15,
    fontWeight: 600,
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  resetBtn: {
    padding: '16px 32px',
    borderRadius: 16,
    background: 'rgba(12,12,24,0.8)',
    backdropFilter: 'blur(10px)',
    color: '#8b9cf7',
    border: '1px solid rgba(255,255,255,0.06)',
    cursor: 'pointer',
    fontSize: 15,
    fontWeight: 600,
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  watermark: {
    marginTop: 48,
    color: '#4a5070',
    fontSize: 12,
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
}
