import React from 'react'
import useIsMobile from '../hooks/useIsMobile'

export default function DoneView({ videoUrl, onReset }) {
  const isMobile = useIsMobile()
  return (
    <div style={{
      ...styles.container,
      ...(isMobile ? { padding: '0 12px' } : {}),
    }}>
      <div style={styles.glowOrb1} />
      <div style={styles.glowOrb2} />
      <div style={styles.glowOrb3} />

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
        <video style={{
          ...styles.video,
          ...(isMobile ? { borderRadius: 14 } : {}),
        }} src={videoUrl} controls autoPlay />
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
            e.currentTarget.style.boxShadow = '0 8px 32px rgba(102,126,234,0.4)'
          }}
          onMouseOut={e => {
            e.currentTarget.style.transform = 'translateY(0)'
            e.currentTarget.style.boxShadow = '0 4px 20px rgba(102,126,234,0.25)'
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Download Video
        </a>
        <button style={{
          ...styles.resetBtn,
          ...(isMobile ? { width: '100%', justifyContent: 'center', padding: '16px 20px', minHeight: 52 } : {}),
        }} onClick={onReset}
          onMouseOver={e => {
            e.currentTarget.style.borderColor = 'rgba(255,255,255,0.15)'
            e.currentTarget.style.background = 'rgba(255,255,255,0.06)'
          }}
          onMouseOut={e => {
            e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'
            e.currentTarget.style.background = 'rgba(17,17,17,0.8)'
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
    background: 'radial-gradient(circle, rgba(39,174,96,0.06) 0%, transparent 70%)',
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
    animation: 'float 3s ease-in-out infinite',
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
    color: '#666',
    fontSize: 14,
    marginTop: 6,
  },
  videoWrap: {
    position: 'relative',
    width: '100%',
    maxWidth: 720,
    marginBottom: 32,
    animation: 'fadeIn 0.6s ease-out 0.2s both',
  },
  video: {
    width: '100%',
    borderRadius: 20,
    border: '1px solid rgba(255,255,255,0.06)',
    boxShadow: '0 12px 48px rgba(0,0,0,0.5)',
    position: 'relative',
    zIndex: 1,
  },
  videoGlow: {
    position: 'absolute',
    bottom: -20,
    left: '10%',
    right: '10%',
    height: 60,
    background: 'radial-gradient(ellipse, rgba(102,126,234,0.15) 0%, transparent 70%)',
    filter: 'blur(20px)',
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
    boxShadow: '0 4px 20px rgba(102,126,234,0.25)',
    transition: 'transform 0.2s, box-shadow 0.2s',
  },
  resetBtn: {
    padding: '16px 32px',
    borderRadius: 16,
    background: 'rgba(17,17,17,0.8)',
    backdropFilter: 'blur(10px)',
    color: '#aaa',
    border: '1px solid rgba(255,255,255,0.08)',
    cursor: 'pointer',
    fontSize: 15,
    fontWeight: 600,
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    transition: 'all 0.2s',
  },
  watermark: {
    marginTop: 48,
    color: '#333',
    fontSize: 12,
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
}
