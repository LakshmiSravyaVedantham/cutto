import React from 'react'
import useIsMobile from '../hooks/useIsMobile'

export default function GeneratingView({ progress, sceneStatuses, scenePlan, error, onDismissError }) {
  const isMobile = useIsMobile()
  const totalScenes = scenePlan?.total_scenes || 0
  const currentStep = progress?.step || ''

  const stepLabels = {
    visual: 'animating scene with AI',
    voiceover: 'recording voiceover',
    clip: 'compositing clip',
    error: 'retrying...',
  }

  const completedScenes = Array.from({ length: totalScenes }, (_, i) => {
    const s = sceneStatuses?.[i + 1]
    return s && s.step === 'clip' && s.status === 'done'
  }).filter(Boolean).length

  const pct = currentStep === 'complete'
    ? 100
    : currentStep === 'assembly'
    ? 95
    : totalScenes > 0
    ? Math.round((completedScenes / totalScenes) * 90)
    : 0

  return (
    <div style={{
      ...styles.container,
      ...(isMobile ? { padding: '0 16px' } : {}),
    }}>
      {/* Floating particles */}
      {!isMobile && Array.from({ length: 12 }, (_, i) => (
        <div key={`p-${i}`} aria-hidden="true" style={{
          position: 'fixed',
          width: i % 3 === 0 ? 3 : 2,
          height: i % 3 === 0 ? 3 : 2,
          borderRadius: '50%',
          background: i % 4 === 0 ? '#764ba2' : '#667eea',
          top: `${10 + (i * 7.3) % 80}%`,
          left: `${5 + (i * 8.1) % 90}%`,
          opacity: 0.12 + (i % 5) * 0.06,
          animation: `starTwinkle ${3 + (i % 4)}s ease-in-out ${(i * 0.7) % 4}s infinite, floatSlow ${12 + (i % 8)}s ease-in-out ${(i * 0.5) % 6}s infinite`,
          pointerEvents: 'none',
          zIndex: 0,
        }} />
      ))}
      <div style={styles.glowOrb1} aria-hidden="true" />
      <div style={styles.glowOrb2} aria-hidden="true" />

      <div style={{
        ...styles.header,
        ...(isMobile ? { paddingTop: 36, paddingBottom: 24 } : {}),
      }}>
        <div style={styles.iconWrap}>
          <div style={styles.filmStrip}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="url(#genGrad)" strokeWidth="1.5">
              <defs>
                <linearGradient id="genGrad" x1="0%" y1="0%" x2="100%" y2="100%">
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
        </div>
        <h2 style={{
          ...styles.title,
          ...(isMobile ? { fontSize: 28 } : {}),
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
              ...(isError ? { border: '1px solid rgba(231,76,60,0.25)', background: 'rgba(231,76,60,0.05)' } : {}),
              ...(isMobile ? { padding: '12px 14px', gap: 10 } : {}),
              animationDelay: `${0.3 + i * 0.06}s`,
            }}>
              <div style={styles.sceneIcon(isDone, isActive, isError)}>
                {isDone ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#34d399" strokeWidth="3">
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
          <div style={styles.assemblyGlow} aria-hidden="true" />
          <span style={styles.spinner} />
          <span style={styles.assemblyText}>
            Adding music and assembling final video...
          </span>
        </div>
      )}

      {error && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10,
          padding: '14px 18px', marginTop: 16, borderRadius: 14,
          background: 'rgba(255,107,107,0.06)', border: '1px solid rgba(255,107,107,0.15)',
          color: '#ff8a8a', fontSize: 13, animation: 'fadeIn 0.3s ease-out',
          backdropFilter: 'blur(10px)',
        }}>
          <span style={{ flex: 1 }}>{error}</span>
          {onDismissError && (
            <button
              onClick={onDismissError}
              style={{
                background: 'transparent', border: 'none', color: '#ff8a8a',
                cursor: 'pointer', padding: 4, flexShrink: 0, opacity: 0.6,
              }}
              aria-label="Dismiss error"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          )}
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
    background: 'radial-gradient(circle, rgba(102,126,234,0.12) 0%, transparent 70%)',
    pointerEvents: 'none',
    animation: 'float 8s ease-in-out infinite',
  },
  glowOrb2: {
    position: 'fixed',
    bottom: -200,
    left: -200,
    width: 500,
    height: 500,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(118,75,162,0.1) 0%, transparent 70%)',
    pointerEvents: 'none',
    animation: 'float 12s ease-in-out 2s infinite',
  },
  header: {
    textAlign: 'center',
    paddingTop: 56,
    paddingBottom: 32,
    animation: 'fadeIn 0.6s ease-out',
  },
  iconWrap: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: 80,
    height: 80,
    borderRadius: 24,
    background: 'linear-gradient(135deg, rgba(102,126,234,0.1), rgba(118,75,162,0.1))',
    border: '1px solid rgba(102,126,234,0.15)',
    marginBottom: 20,
    animation: 'glowPulse 3s ease-in-out infinite, float 3s ease-in-out infinite',
  },
  filmStrip: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 36,
    fontWeight: 900,
    background: 'linear-gradient(135deg, #667eea, #e879f9, #764ba2)',
    backgroundSize: '200% auto',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    letterSpacing: -1,
    animation: 'shimmer 4s linear infinite',
    filter: 'drop-shadow(0 0 20px rgba(102,126,234,0.15))',
  },
  subtitle: {
    color: '#6b7cc7',
    fontSize: 15,
    marginTop: 8,
    fontWeight: 500,
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
    height: 8,
    background: 'rgba(255,255,255,0.04)',
    borderRadius: 4,
    overflow: 'hidden',
    border: '1px solid rgba(255,255,255,0.03)',
  },
  progressBar: {
    height: '100%',
    background: 'linear-gradient(90deg, #667eea, #9b6dff, #e879f9, #764ba2)',
    backgroundSize: '300% 100%',
    borderRadius: 4,
    transition: 'width 0.8s ease-out',
    animation: 'gradientFlow 3s ease-in-out infinite',
    boxShadow: '0 0 12px rgba(102,126,234,0.4)',
  },
  progressText: {
    color: '#8b9cf7',
    fontSize: 14,
    fontWeight: 700,
    minWidth: 50,
    textAlign: 'right',
  },
  sceneList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    animation: 'fadeIn 0.6s ease-out 0.3s both',
  },
  scene: (isDone, isActive) => ({
    display: 'flex',
    alignItems: 'center',
    gap: 14,
    padding: '16px 20px',
    background: isActive
      ? 'rgba(102,126,234,0.06)'
      : isDone
      ? 'rgba(52,211,153,0.03)'
      : 'rgba(12,12,24,0.6)',
    backdropFilter: 'blur(12px)',
    borderRadius: 16,
    border: isActive
      ? '1px solid rgba(102,126,234,0.25)'
      : isDone
      ? '1px solid rgba(52,211,153,0.12)'
      : '1px solid rgba(255,255,255,0.04)',
    transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
    animation: 'fadeIn 0.4s ease-out both',
    ...(isActive ? { boxShadow: '0 4px 20px rgba(102,126,234,0.1)' } : {}),
  }),
  sceneIcon: (isDone, isActive, isError) => ({
    width: 36,
    height: 36,
    borderRadius: 12,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    background: isDone
      ? 'rgba(52,211,153,0.12)'
      : isError
      ? 'rgba(231,76,60,0.1)'
      : isActive
      ? 'rgba(102,126,234,0.15)'
      : 'rgba(255,255,255,0.04)',
    border: isDone
      ? '1px solid rgba(52,211,153,0.2)'
      : isActive
      ? '1px solid rgba(102,126,234,0.2)'
      : '1px solid transparent',
    transition: 'all 0.3s ease',
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
    background: '#3a4060',
    animation: 'pulse 2s ease-in-out infinite',
  },
  thumb: {
    width: 52,
    height: 40,
    borderRadius: 8,
    objectFit: 'cover',
    flexShrink: 0,
    border: '1px solid rgba(255,255,255,0.06)',
    boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
  },
  sceneInfo: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: 3,
  },
  sceneName: (isDone, isActive) => ({
    fontSize: 14,
    fontWeight: 600,
    color: isDone ? '#34d399' : isActive ? '#d0d5f0' : '#5a6080',
  }),
  sceneStatus: (isDone, isActive) => ({
    fontSize: 12,
    color: isDone ? 'rgba(52,211,153,0.7)' : isActive ? '#8b9cf7' : '#3a4060',
    textTransform: 'capitalize',
    fontWeight: isActive ? 500 : 400,
  }),
  speakerBadge: {
    marginLeft: 6,
    fontSize: 10,
    fontWeight: 600,
    padding: '2px 7px',
    borderRadius: 6,
    background: 'rgba(102,126,234,0.12)',
    color: '#8b9cf7',
    letterSpacing: 0.3,
    textTransform: 'uppercase',
    border: '1px solid rgba(102,126,234,0.1)',
  },
  narrationPreview: {
    fontSize: 11,
    color: '#5a6080',
    lineHeight: 1.4,
    fontStyle: 'italic',
  },
  doneTime: {
    fontSize: 11,
    color: '#34d399',
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  assembly: {
    marginTop: 24,
    padding: '22px 28px',
    display: 'flex',
    alignItems: 'center',
    gap: 16,
    background: 'linear-gradient(135deg, rgba(102,126,234,0.08), rgba(118,75,162,0.08))',
    backdropFilter: 'blur(12px)',
    borderRadius: 18,
    border: '1px solid rgba(102,126,234,0.2)',
    animation: 'fadeIn 0.4s ease-out, glowPulse 3s ease-in-out infinite',
    position: 'relative',
    overflow: 'hidden',
  },
  assemblyGlow: {
    position: 'absolute',
    top: 0, left: 0, right: 0, bottom: 0,
    background: 'linear-gradient(90deg, transparent, rgba(102,126,234,0.05), transparent)',
    backgroundSize: '200% 100%',
    animation: 'shimmer 2s linear infinite',
    pointerEvents: 'none',
  },
  assemblyText: {
    color: '#a0b0ff',
    fontWeight: 700,
    fontSize: 15,
  },
  tip: {
    textAlign: 'center',
    color: '#4a5070',
    fontSize: 12,
    marginTop: 32,
    letterSpacing: 0.3,
    paddingBottom: 32,
  },
}
