import React from 'react'

const styles = {
  container: {
    maxWidth: 600,
    margin: '0 auto',
    padding: '80px 40px',
    textAlign: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 700,
    marginBottom: 12,
    background: 'linear-gradient(135deg, #667eea, #764ba2)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  subtitle: {
    color: '#888',
    marginBottom: 40,
  },
  scene: {
    display: 'flex',
    alignItems: 'center',
    gap: 14,
    padding: '14px 20px',
    marginBottom: 8,
    background: '#1a1a2e',
    borderRadius: 12,
    textAlign: 'left',
  },
  icon: {
    fontSize: 20,
    width: 30,
    textAlign: 'center',
  },
  done: { color: '#27ae60' },
  active: { color: '#667eea' },
  pending: { color: '#444' },
  spinner: {
    display: 'inline-block',
    width: 18,
    height: 18,
    border: '2px solid #667eea',
    borderTop: '2px solid transparent',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  assembly: {
    marginTop: 32,
    padding: '20px',
    background: 'linear-gradient(135deg, rgba(102,126,234,0.1), rgba(118,75,162,0.1))',
    borderRadius: 16,
    border: '1px solid rgba(102,126,234,0.2)',
  },
}

export default function GeneratingView({ progress, scenePlan }) {
  const totalScenes = scenePlan?.total_scenes || 0
  const currentScene = progress?.scene || 0
  const currentStep = progress?.step || ''

  const stepLabels = {
    visual: 'generating visuals',
    voiceover: 'creating voiceover',
    clip: 'assembling clip',
  }

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Creating your video</h2>
      <p style={styles.subtitle}>{scenePlan?.title || 'Processing...'}</p>

      {Array.from({ length: totalScenes }, (_, i) => {
        const num = i + 1
        const isDone =
          num < currentScene ||
          (num === currentScene && progress?.status === 'done' && currentStep === 'clip')
        const isActive =
          num === currentScene && progress?.status === 'in_progress'

        return (
          <div key={num} style={styles.scene}>
            <span style={styles.icon}>
              {isDone ? (
                <span style={styles.done}>&#10003;</span>
              ) : isActive ? (
                <span style={styles.spinner} />
              ) : (
                <span style={styles.pending}>&#9675;</span>
              )}
            </span>
            <span
              style={
                isDone
                  ? styles.done
                  : isActive
                  ? styles.active
                  : styles.pending
              }
            >
              Scene {num}
              {isActive && currentStep
                ? ` — ${stepLabels[currentStep] || currentStep}...`
                : isDone
                ? ' — done'
                : ''}
            </span>
          </div>
        )
      })}

      {currentStep === 'assembly' && (
        <div style={styles.assembly}>
          <span style={styles.spinner} />
          <span style={{ ...styles.active, marginLeft: 12 }}>
            Assembling final video with music...
          </span>
        </div>
      )}
    </div>
  )
}
