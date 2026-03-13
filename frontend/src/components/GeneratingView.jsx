import React from 'react'
import useIsMobile from '../hooks/useIsMobile'

export default function GeneratingView({ progress, sceneStatuses, scenePlan }) {
  const isMobile = useIsMobile()
  const totalScenes = scenePlan?.total_scenes || 0
  const currentStep = progress?.step || ''

  const stepLabels = {
    visual: 'animating scene with AI',
    voiceover: 'recording voiceover',
    clip: 'compositing clip',
    error: 'retrying...',
  }

  // Count completed scenes from per-scene tracking
  const completedScenes = Array.from({ length: totalScenes }, (_, i) => {
    const s = sceneStatuses?.[i + 1]
    return s && s.step === 'clip' && s.status === 'done'
  }).filter(Boolean).length

  const pct = currentStep === 'assembly' || currentStep === 'complete'
    ? 95
    : totalScenes > 0
    ? Math.round((completedScenes / totalScenes) * 90)
    : 0

  return (
    <div style={{
      ...styles.container,
      ...(isMobile ? { padding: '0 16px' } : {}),
    }}>
      <div style={styles.glowOrb1} />
      <div style={styles.glowOrb2} />

      <div style={{
        ...styles.header,
        ...(isMobile ? { paddingTop: 36, paddingBottom: 24 } : {}),
      }}>
        <div style={styles.filmStrip}>
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="url(#grad)" strokeWidth="1.5">
            <defs>
              <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#667eea" />
                <stop offset="100%" stopColor="#764ba2" />
              </linearGradient>
            </defs>
            <rect x="2" y="2" width="20" height="20" rx="2.18" />
            <line x1="7" y1="2" x2="7" y2="22" />
            <line x1="17" y1="2" x2="17" y2="22" />
            <line x1="2" y1="12" x2="22" y2="12" />
            <line x1="2" y1="7" x2="7" y2="7" />
            <line x1="2" y1="17" x2="7" y2="17" />
            <line x1="17" y1="7" x2="22" y2="7" />
            <line x1="17" y1="17" x2="22" y2="17" />
          </svg>
        </div>
        <h2 style={{
          ...styles.title,
          ...(isMobile ? { fontSize: 22 } : {}),
        }}>Creating your video</h2>
        <p style={styles.subtitle}>{scenePlan?.title || 'Processing...'}</p>
      </div>

      {/* Progress bar */}
      <div style={styles.progressWrap}>
        <div style={styles.progressTrack}>
          <div style={{
            ...styles.progressBar,
            width: currentStep === 'assembly' ? '90%' : `${pct}%`,
          }} />
        </div>
        <span style={styles.progressText}>
          {currentStep === 'assembly' ? 'Final assembly...' : `${pct}%`}
        </span>
      </div>

      {/* Scene list */}
      <div style={styles.sceneList}>
        {Array.from({ length: totalScenes }, (_, i) => {
          const num = i + 1
          const s = sceneStatuses?.[num]
          const isDone = s && s.step === 'clip' && s.status === 'done'
          const isActive = s && s.status === 'in_progress'
          const isError = s && s.status === 'error'

          return (
            <div key={num} style={{
              ...styles.scene(isDone, isActive),
              ...(isError ? { border: '1px solid rgba(231,76,60,0.2)', background: 'rgba(231,76,60,0.05)' } : {}),
              ...(isMobile ? { padding: '12px 14px', gap: 10 } : {}),
            }}>
              <div style={styles.sceneIcon(isDone, isActive)}>
                {isDone ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#27ae60" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : isError ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#e74c3c" strokeWidth="2.5">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" />
                  </svg>
                ) : isActive ? (
                  <span style={styles.spinner} />
                ) : (
                  <span style={styles.pendingDot} />
                )}
              </div>
              {isDone && s?.thumbnail && (
                <img src={`data:image/jpeg;base64,${s.thumbnail}`} style={styles.thumb} alt="" />
              )}
              <div style={styles.sceneInfo}>
                <span style={styles.sceneName(isDone, isActive)}>
                  Scene {num}
                  {scenePlan?.scenes?.[i]?.speaker && (
                    <span style={styles.speakerBadge}>
                      {scenePlan.scenes[i].speaker === 'narrator' ? 'narr.' : scenePlan.scenes[i].speaker.replace('character_', 'char ')}
                    </span>
                  )}
                </span>
                {scenePlan?.scenes?.[i]?.narration && (
                  <span style={styles.narrationPreview}>
                    {scenePlan.scenes[i].narration.slice(0, 80)}{scenePlan.scenes[i].narration.length > 80 ? '...' : ''}
                  </span>
                )}
                <span style={{
                  ...(styles.sceneStatus(isDone, isActive)),
                  ...(isError ? { color: '#e74c3c' } : {}),
                }}>
                  {isError
                    ? 'failed — skipping'
                    : isActive && s?.step
                    ? stepLabels[s.step] || s.step
                    : isDone
                    ? 'complete'
                    : 'waiting'}
                </span>
              </div>
              {isDone && <span style={styles.doneTime}>done</span>}
            </div>
          )
        })}
      </div>

      {currentStep === 'assembly' && (
        <div style={styles.assembly}>
          <span style={styles.spinner} />
          <span style={styles.assemblyText}>
            Adding music and assembling final video...
          </span>
        </div>
      )}

      <p style={styles.tip}>
        {totalScenes > 0
          ? `Estimated ${Math.ceil(totalScenes * 1.5)} - ${totalScenes * 3} min total (${totalScenes} scenes in parallel batches)`
          : 'AI animation takes 1-3 minutes per scene.'}
      </p>
    </div>
  )
}

const styles = {
  container: {
    maxWidth: 640,
    margin: '0 auto',
    padding: '0 24px',
    display: 'flex',
    flexDirection: 'column',
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
    paddingTop: 60,
    paddingBottom: 32,
    animation: 'fadeIn 0.6s ease-out',
  },
  filmStrip: {
    marginBottom: 16,
    animation: 'float 3s ease-in-out infinite',
  },
  title: {
    fontSize: 28,
    fontWeight: 800,
    background: 'linear-gradient(135deg, #667eea, #764ba2)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    letterSpacing: -0.5,
  },
  subtitle: {
    color: '#777',
    fontSize: 14,
    marginTop: 6,
  },
  progressWrap: {
    display: 'flex',
    alignItems: 'center',
    gap: 14,
    marginBottom: 28,
    animation: 'fadeIn 0.6s ease-out 0.2s both',
  },
  progressTrack: {
    flex: 1,
    height: 6,
    background: 'rgba(255,255,255,0.06)',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    background: 'linear-gradient(90deg, #667eea, #764ba2)',
    borderRadius: 3,
    transition: 'width 0.8s ease-out',
  },
  progressText: {
    color: '#888',
    fontSize: 13,
    fontWeight: 600,
    minWidth: 50,
    textAlign: 'right',
  },
  sceneList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
    animation: 'fadeIn 0.6s ease-out 0.3s both',
  },
  scene: (isDone, isActive) => ({
    display: 'flex',
    alignItems: 'center',
    gap: 14,
    padding: '14px 18px',
    background: isActive
      ? 'rgba(102,126,234,0.08)'
      : 'rgba(17,17,17,0.6)',
    backdropFilter: 'blur(10px)',
    borderRadius: 14,
    border: isActive
      ? '1px solid rgba(102,126,234,0.2)'
      : '1px solid rgba(255,255,255,0.04)',
    transition: 'all 0.3s ease',
  }),
  sceneIcon: (isDone, isActive) => ({
    width: 32,
    height: 32,
    borderRadius: 10,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    background: isDone
      ? 'rgba(39,174,96,0.1)'
      : isActive
      ? 'rgba(102,126,234,0.15)'
      : 'rgba(255,255,255,0.04)',
  }),
  spinner: {
    display: 'inline-block',
    width: 16,
    height: 16,
    border: '2px solid #667eea',
    borderTop: '2px solid transparent',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  pendingDot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
    background: '#333',
  },
  thumb: {
    width: 48,
    height: 36,
    borderRadius: 6,
    objectFit: 'cover',
    flexShrink: 0,
  },
  sceneInfo: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: 2,
  },
  sceneName: (isDone, isActive) => ({
    fontSize: 14,
    fontWeight: 600,
    color: isDone ? '#27ae60' : isActive ? '#fff' : '#555',
  }),
  sceneStatus: (isDone, isActive) => ({
    fontSize: 12,
    color: isDone ? 'rgba(39,174,96,0.6)' : isActive ? '#667eea' : '#444',
    textTransform: 'capitalize',
  }),
  speakerBadge: {
    marginLeft: 6,
    fontSize: 10,
    fontWeight: 600,
    padding: '1px 6px',
    borderRadius: 4,
    background: 'rgba(102,126,234,0.12)',
    color: '#667eea',
    letterSpacing: 0.3,
    textTransform: 'uppercase',
  },
  narrationPreview: {
    fontSize: 11,
    color: '#555',
    lineHeight: 1.4,
    fontStyle: 'italic',
  },
  doneTime: {
    fontSize: 11,
    color: '#27ae60',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  assembly: {
    marginTop: 24,
    padding: '20px 24px',
    display: 'flex',
    alignItems: 'center',
    gap: 14,
    background: 'linear-gradient(135deg, rgba(102,126,234,0.08), rgba(118,75,162,0.08))',
    backdropFilter: 'blur(10px)',
    borderRadius: 16,
    border: '1px solid rgba(102,126,234,0.15)',
    animation: 'fadeIn 0.4s ease-out',
  },
  assemblyText: {
    color: '#667eea',
    fontWeight: 600,
    fontSize: 14,
  },
  tip: {
    textAlign: 'center',
    color: '#444',
    fontSize: 12,
    marginTop: 32,
    letterSpacing: 0.3,
  },
}
