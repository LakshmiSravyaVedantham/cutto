import React, { useState, useEffect } from 'react'
import useIsMobile from '../hooks/useIsMobile'

function Confetti() {
  const [particles] = useState(() =>
    Array.from({ length: 36 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      delay: Math.random() * 1.2,
      duration: 1.5 + Math.random() * 2,
      size: 3 + Math.random() * 5,
      color: ['#667eea', '#764ba2', '#34d399', '#2ecc71', '#e879f9', '#fbbf24', '#60a5fa', '#f472b6'][i % 8],
      isSquare: i % 5 === 0,
    }))
  )

  return (
    <div style={{ position: 'fixed', top: '35%', left: 0, right: 0, pointerEvents: 'none', zIndex: 50 }}>
      {particles.map(p => (
        <div
          key={p.id}
          style={{
            position: 'absolute',
            left: `${p.left}%`,
            width: p.size,
            height: p.size,
            borderRadius: p.isSquare ? 2 : '50%',
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
      {/* Floating particles */}
      {!isMobile && Array.from({ length: 14 }, (_, i) => (
        <div key={`sp-${i}`} aria-hidden="true" style={{
          position: 'fixed',
          width: i % 3 === 0 ? 3 : 2,
          height: i % 3 === 0 ? 3 : 2,
          borderRadius: '50%',
          background: i % 3 === 0 ? '#34d399' : i % 4 === 0 ? '#764ba2' : '#667eea',
          top: `${8 + (i * 6.3) % 84}%`,
          left: `${4 + (i * 7.9) % 92}%`,
          opacity: 0.12 + (i % 5) * 0.06,
          animation: `starTwinkle ${3 + (i % 4)}s ease-in-out ${(i * 0.8) % 4}s infinite, floatSlow ${14 + (i % 6)}s ease-in-out ${(i * 0.6) % 5}s infinite`,
          pointerEvents: 'none',
          zIndex: 0,
        }} />
      ))}
      <div style={styles.glowOrb1} aria-hidden="true" />
      <div style={styles.glowOrb2} aria-hidden="true" />
      <div style={styles.glowOrb3} aria-hidden="true" />

      <div style={{
        ...styles.header,
        ...(isMobile ? { paddingTop: 32, paddingBottom: 20 } : {}),
      }}>
        <div style={styles.successRing}>
          <div style={styles.successIcon}>
            <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#34d399" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          </div>
        </div>
        <h2 style={{
          ...styles.title,
          ...(isMobile ? { fontSize: 28 } : {}),
        }}>Your video is ready</h2>
        <p style={styles.subtitle}>Watch, download, or create another</p>
      </div>

      <div style={{
        ...styles.videoOuterWrap,
        ...(isMobile ? { maxWidth: '100%' } : {}),
      }}>
        <div style={styles.videoWrap}>
          {videoError ? (
            <div style={{ padding: 32, textAlign: 'center' }}>
              <p style={{ fontSize: 14, marginBottom: 4, color: '#ff8a8a' }}>Video couldn't load in this browser</p>
              <p style={{ fontSize: 12, marginBottom: 16, color: '#6b7cc7' }}>Try reloading or download the file directly</p>
              <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
                <button
                  style={{
                    padding: '12px 24px', borderRadius: 12,
                    background: 'linear-gradient(135deg, #667eea, #764ba2)',
                    color: '#fff', border: 'none', cursor: 'pointer',
                    fontSize: 13, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 6,
                    boxShadow: '0 4px 16px rgba(102,126,234,0.3)',
                  }}
                  onClick={() => { setRetrying(true); setVideoError(false); setTimeout(() => setRetrying(false), 500) }}
                >
                  {retrying ? 'Retrying...' : 'Retry Playback'}
                </button>
                <a href={videoUrl} download style={{
                  padding: '12px 24px', borderRadius: 12,
                  background: 'rgba(102,126,234,0.08)', color: '#8b9cf7',
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
        </div>
        <div style={styles.videoGlow} />
      </div>

      <div style={{
        ...styles.btnRow,
        ...(isMobile ? { flexDirection: 'column', width: '100%', gap: 10 } : {}),
      }}>
        <div style={{
          ...styles.downloadWrap,
          ...(isMobile ? { width: '100%' } : {}),
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
        </div>
        {onEditScenes && (
          <button style={{
            ...styles.editBtn,
            ...(isMobile ? { width: '100%', justifyContent: 'center', padding: '16px 20px', minHeight: 52 } : {}),
          }} onClick={onEditScenes}
            onMouseOver={e => {
              e.currentTarget.style.borderColor = 'rgba(102,126,234,0.35)'
              e.currentTarget.style.background = 'rgba(102,126,234,0.1)'
              e.currentTarget.style.transform = 'translateY(-2px)'
            }}
            onMouseOut={e => {
              e.currentTarget.style.borderColor = 'rgba(102,126,234,0.15)'
              e.currentTarget.style.background = 'rgba(12,12,24,0.8)'
              e.currentTarget.style.transform = 'translateY(0)'
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
            e.currentTarget.style.transform = 'translateY(-2px)'
          }}
          onMouseOut={e => {
            e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'
            e.currentTarget.style.background = 'rgba(12,12,24,0.8)'
            e.currentTarget.style.transform = 'translateY(0)'
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
    background: 'radial-gradient(circle, rgba(52,211,153,0.1) 0%, transparent 70%)',
    pointerEvents: 'none',
    animation: 'float 10s ease-in-out infinite',
  },
  glowOrb2: {
    position: 'fixed',
    bottom: -200,
    left: -200,
    width: 500,
    height: 500,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(102,126,234,0.08) 0%, transparent 70%)',
    pointerEvents: 'none',
    animation: 'float 14s ease-in-out 3s infinite',
  },
  glowOrb3: {
    position: 'fixed',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: 600,
    height: 600,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(118,75,162,0.05) 0%, transparent 60%)',
    pointerEvents: 'none',
  },
  header: {
    textAlign: 'center',
    paddingTop: 48,
    paddingBottom: 28,
    animation: 'fadeIn 0.6s ease-out',
  },
  successRing: {
    display: 'inline-flex',
    marginBottom: 20,
    padding: 3,
    borderRadius: '50%',
    background: 'linear-gradient(135deg, rgba(52,211,153,0.4), rgba(46,204,113,0.2), rgba(52,211,153,0.4))',
    backgroundSize: '200% 200%',
    animation: 'gradientFlow 4s ease-in-out infinite',
  },
  successIcon: {
    width: 80,
    height: 80,
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'rgba(12,12,24,0.9)',
    animation: 'glowPulse 2.5s ease-in-out infinite',
  },
  title: {
    fontSize: 40,
    fontWeight: 900,
    background: 'linear-gradient(135deg, #34d399, #2ecc71, #34d399)',
    backgroundSize: '200% auto',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    letterSpacing: -1,
    animation: 'shimmer 4s linear infinite',
    filter: 'drop-shadow(0 0 20px rgba(52,211,153,0.15))',
  },
  subtitle: {
    color: '#6b7cc7',
    fontSize: 15,
    marginTop: 8,
    fontWeight: 500,
  },
  videoOuterWrap: {
    position: 'relative',
    width: '100%',
    maxWidth: 720,
    marginBottom: 36,
    animation: 'fadeInScale 0.6s ease-out 0.2s both',
  },
  videoWrap: {
    borderRadius: 22,
    padding: 2,
    background: 'linear-gradient(135deg, rgba(102,126,234,0.3), rgba(118,75,162,0.2), rgba(52,211,153,0.2))',
    backgroundSize: '200% 200%',
    animation: 'gradientFlow 6s ease-in-out infinite',
    position: 'relative',
    zIndex: 1,
  },
  video: {
    width: '100%',
    borderRadius: 20,
    display: 'block',
    background: '#0c0c18',
    boxShadow: '0 16px 64px rgba(0,0,0,0.6)',
  },
  videoGlow: {
    position: 'absolute',
    bottom: -28,
    left: '6%',
    right: '6%',
    height: 100,
    background: 'radial-gradient(ellipse, rgba(102,126,234,0.25) 0%, transparent 70%)',
    filter: 'blur(28px)',
    pointerEvents: 'none',
  },
  btnRow: {
    display: 'flex',
    gap: 12,
    justifyContent: 'center',
    animation: 'fadeIn 0.6s ease-out 0.4s both',
  },
  downloadWrap: {
    display: 'inline-block',
    padding: 2,
    borderRadius: 18,
    background: 'linear-gradient(135deg, rgba(102,126,234,0.5), rgba(118,75,162,0.5), rgba(102,126,234,0.5))',
    backgroundSize: '200% 200%',
    animation: 'gradientFlow 4s ease-in-out infinite',
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
    backdropFilter: 'blur(12px)',
    color: '#8b9cf7',
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
    backdropFilter: 'blur(12px)',
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
    marginBottom: 32,
    color: '#4a5070',
    fontSize: 12,
    letterSpacing: 1.5,
    textTransform: 'uppercase',
    fontWeight: 500,
  },
}
