import React from 'react'

const styles = {
  container: {
    maxWidth: 800,
    margin: '0 auto',
    padding: '60px 40px',
    textAlign: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: 700,
    marginBottom: 8,
    background: 'linear-gradient(135deg, #27ae60, #2ecc71)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  subtitle: {
    color: '#888',
    marginBottom: 32,
  },
  video: {
    width: '100%',
    maxWidth: 720,
    borderRadius: 16,
    marginBottom: 32,
    boxShadow: '0 8px 40px rgba(0,0,0,0.4)',
  },
  btnRow: {
    display: 'flex',
    gap: 16,
    justifyContent: 'center',
  },
  downloadBtn: {
    padding: '16px 36px',
    borderRadius: 14,
    background: 'linear-gradient(135deg, #667eea, #764ba2)',
    color: '#fff',
    border: 'none',
    cursor: 'pointer',
    fontSize: 16,
    fontWeight: 600,
    textDecoration: 'none',
    display: 'inline-block',
  },
  resetBtn: {
    padding: '16px 36px',
    borderRadius: 14,
    background: '#222',
    color: '#fff',
    border: '1px solid #333',
    cursor: 'pointer',
    fontSize: 16,
    fontWeight: 600,
  },
}

export default function DoneView({ videoUrl, onReset }) {
  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Your video is ready!</h2>
      <p style={styles.subtitle}>Download it or create another one</p>
      <video style={styles.video} src={videoUrl} controls autoPlay />
      <div style={styles.btnRow}>
        <a style={styles.downloadBtn} href={videoUrl} download>
          Download
        </a>
        <button style={styles.resetBtn} onClick={onReset}>
          Make Another
        </button>
      </div>
    </div>
  )
}
