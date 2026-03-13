import React, { lazy, Suspense } from 'react'
import useWebSocket from './hooks/useWebSocket'
import useIsMobile from './hooks/useIsMobile'

const ConversationView = lazy(() => import('./components/ConversationView'))
const GeneratingView = lazy(() => import('./components/GeneratingView'))
const DoneView = lazy(() => import('./components/DoneView'))

export default function App() {
  const ws = useWebSocket()
  const isMobile = useIsMobile()

  const isGenerating = ws.progress && !ws.videoUrl
  const isDone = !!ws.videoUrl
  // Show active views even during brief disconnects so progress isn't lost
  const hasActiveSession = ws.connected || isDone || isGenerating || ws.messages.length > 0

  if (!hasActiveSession) {
    return (
      <div id="main-content" style={styles.container} role="main" aria-label="CutTo — AI Video Director">
        {/* Animated background elements */}
        <div style={styles.bgGrid} aria-hidden="true" />
        <div style={styles.glowOrb1} aria-hidden="true" />
        <div style={styles.glowOrb2} aria-hidden="true" />
        <div style={styles.glowOrb3} aria-hidden="true" />

        {/* Floating particles */}
        {!isMobile && Array.from({ length: 20 }, (_, i) => (
          <div key={`star-${i}`} aria-hidden="true" style={{
            position: 'fixed',
            width: i % 3 === 0 ? 3 : 2,
            height: i % 3 === 0 ? 3 : 2,
            borderRadius: '50%',
            background: i % 4 === 0 ? '#764ba2' : '#667eea',
            top: `${8 + (i * 4.7) % 85}%`,
            left: `${5 + (i * 7.3) % 90}%`,
            opacity: 0.15 + (i % 5) * 0.08,
            animation: `starTwinkle ${3 + (i % 4)}s ease-in-out ${(i * 0.7) % 4}s infinite, floatSlow ${12 + (i % 8)}s ease-in-out ${(i * 0.5) % 6}s infinite`,
            pointerEvents: 'none',
          }} />
        ))}

        {/* Hero */}
        <div style={styles.hero}>
          <div style={styles.badgeWrap}>
            <span style={styles.heroBadge} aria-label="Built with Google Gemini and Veo">
              <span style={styles.heroBadgeDot} aria-hidden="true" />
              Built with Google Gemini &amp; Veo
            </span>
          </div>

          <h1 style={{
            ...styles.title,
            ...(isMobile ? { fontSize: 52, letterSpacing: -2 } : {}),
          }}>
            <span style={styles.titleGradient}>CutTo</span>
          </h1>
          <p style={{
            ...styles.subtitle,
            ...(isMobile ? { fontSize: 17, maxWidth: 300 } : {}),
          }}>
            AI Video Director for Kids&apos; Education
          </p>
          <p style={styles.description}>
            Turn any lesson into an animated video. Describe your idea —
            CutTo writes the script, generates visuals, adds voiceover
            with lipsync, and delivers a finished video.
          </p>

          {/* CTA with animated gradient border */}
          <div style={styles.ctaWrap}>
            <button
              style={{
                ...styles.ctaBtn,
                ...(isMobile ? { padding: '18px 36px', fontSize: 16 } : {}),
                ...(ws.connecting ? { opacity: 0.7, pointerEvents: 'none' } : {}),
              }}
              onClick={ws.connect}
              disabled={ws.connecting}
              onMouseOver={e => {
                if (!ws.connecting) {
                  e.currentTarget.style.transform = 'translateY(-3px) scale(1.02)'
                  e.currentTarget.style.boxShadow = '0 16px 56px rgba(102,126,234,0.5), 0 0 120px rgba(118,75,162,0.15)'
                  e.currentTarget.parentElement.style.background = 'linear-gradient(135deg, #667eea, #e879f9, #764ba2, #667eea)'
                }
              }}
              onMouseOut={e => {
                e.currentTarget.style.transform = 'translateY(0) scale(1)'
                e.currentTarget.style.boxShadow = '0 8px 40px rgba(102,126,234,0.35)'
                e.currentTarget.parentElement.style.background = 'linear-gradient(135deg, rgba(102,126,234,0.5), rgba(118,75,162,0.5), rgba(102,126,234,0.5))'
              }}
            >
              {ws.connecting ? (
                <>
                  Connecting
                  <div style={{ width: 18, height: 18, border: '2px solid rgba(255,255,255,0.3)', borderTop: '2px solid #fff', borderRadius: '50%', animation: 'spin 0.8s linear infinite', marginLeft: 10 }} />
                </>
              ) : (
                <>
                  Start Creating
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ marginLeft: 8 }}>
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </>
              )}
            </button>
          </div>

          {/* Connection error */}
          {ws.error && (
            <div style={{
              marginTop: 16, padding: '12px 20px', borderRadius: 12,
              background: 'rgba(231,76,60,0.08)', border: '1px solid rgba(231,76,60,0.15)',
              color: '#e74c3c', fontSize: 13, display: 'flex', alignItems: 'center',
              gap: 10, animation: 'fadeIn 0.3s ease-out', maxWidth: 420, margin: '16px auto 0',
            }} role="alert">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              <span>{ws.error}</span>
              <button
                onClick={ws.dismissError}
                style={{
                  marginLeft: 'auto', background: 'none', border: 'none',
                  color: '#e74c3c', cursor: 'pointer', padding: 4, flexShrink: 0,
                }}
                aria-label="Dismiss error"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          )}
        </div>

        {/* Quick start templates */}
        <div style={{
          ...styles.quickStart,
          ...(isMobile ? { flexDirection: 'column' } : {}),
        }}>
          <p style={styles.quickLabel}>Quick start:</p>
          <div style={{
            ...styles.quickChips,
            ...(isMobile ? { flexDirection: 'column', alignItems: 'stretch' } : {}),
          }}>
            {[
              { emoji: '\u2764\uFE0F', label: 'How the heart pumps blood', prompt: 'Create a 90-second animated explainer for 8-year-olds about how the human heart pumps blood through its four chambers. Use colorful cartoon characters as red blood cells traveling through the body. Friendly narrator voice, upbeat music.', hint: '~90s video' },
              { emoji: '\uD83D\uDE80', label: 'Solar system adventure', prompt: 'Create an animated story for kids (ages 6-10) where a curious alien named Zip visits each planet in our solar system. Educational facts about each planet, Pixar-style animation, exciting and fun mood.', hint: '~90s video' },
              { emoji: '\uD83C\uDF0B', label: 'Why do volcanoes erupt?', prompt: 'Create a 60-second science explainer for elementary school students about why volcanoes erupt. Show the layers of the earth, magma chambers, and eruption in colorful animated diagrams. Keep it exciting but educational.', hint: '~60s video' },
            ].map((t) => (
              <button
                key={t.label}
                style={{
                  ...styles.quickChip,
                  ...(ws.connecting ? { opacity: 0.5, pointerEvents: 'none' } : {}),
                }}
                onClick={() => ws.connectWithPrompt(t.prompt)}
                disabled={ws.connecting}
                onMouseOver={e => {
                  if (!ws.connecting) {
                    e.currentTarget.style.borderColor = 'rgba(102,126,234,0.4)'
                    e.currentTarget.style.background = 'rgba(102,126,234,0.1)'
                    e.currentTarget.style.transform = 'translateY(-3px)'
                    e.currentTarget.style.boxShadow = '0 8px 24px rgba(102,126,234,0.15)'
                  }
                }}
                onMouseOut={e => {
                  e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'
                  e.currentTarget.style.background = 'rgba(15,15,25,0.6)'
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              title={t.hint}
              >
                <span style={{ marginRight: 6 }}>{t.emoji}</span>{t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Feature cards */}
        <div style={{
          ...styles.features,
          ...(isMobile ? { flexDirection: 'column', gap: 12 } : {}),
        }}>
          {[
            {
              icon: (
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="url(#feat1)" strokeWidth="1.5">
                  <defs><linearGradient id="feat1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="#667eea"/><stop offset="100%" stopColor="#e879f9"/></linearGradient></defs>
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
              ),
              label: '6 Video Types',
              desc: 'Stories, science explainers, tutorials, documentaries, marketing, motivational'
            },
            {
              icon: (
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="url(#feat2)" strokeWidth="1.5">
                  <defs><linearGradient id="feat2" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="#667eea"/><stop offset="100%" stopColor="#e879f9"/></linearGradient></defs>
                  <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>
                </svg>
              ),
              label: 'AI Visuals by Veo 2.0',
              desc: 'Animated scenes with consistent style, Imagen & Gemini fallback chain'
            },
            {
              icon: (
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="url(#feat3)" strokeWidth="1.5">
                  <defs><linearGradient id="feat3" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="#667eea"/><stop offset="100%" stopColor="#e879f9"/></linearGradient></defs>
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                </svg>
              ),
              label: 'Voice, Lipsync & Music',
              desc: '3 distinct characters, Wav2Lip mouth sync, mood-matched soundtrack'
            },
          ].map((f, i) => (
            <div
              key={f.label}
              style={{
                ...styles.featureCard,
                animationDelay: `${0.6 + i * 0.1}s`,
              }}
              onMouseOver={e => {
                e.currentTarget.style.borderColor = 'rgba(102,126,234,0.3)'
                e.currentTarget.style.transform = 'translateY(-6px) scale(1.02)'
                e.currentTarget.style.boxShadow = '0 20px 60px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05)'
                e.currentTarget.style.background = 'rgba(16,16,36,0.8)'
              }}
              onMouseOut={e => {
                e.currentTarget.style.borderColor = 'rgba(255,255,255,0.04)'
                e.currentTarget.style.transform = 'translateY(0) scale(1)'
                e.currentTarget.style.boxShadow = 'none'
                e.currentTarget.style.background = 'rgba(12,12,24,0.7)'
              }}
            >
              <div style={styles.featureIcon}>{f.icon}</div>
              <span style={styles.featureLabel}>{f.label}</span>
              <span style={styles.featureDesc}>{f.desc}</span>
            </div>
          ))}
        </div>

        {/* How it works */}
        <div style={styles.howSection}>
          <h3 style={styles.howTitle}>How it works</h3>
          <div style={{
            ...styles.howSteps,
            ...(isMobile ? { flexDirection: 'column', gap: 16 } : {}),
          }}>
            {[
              { num: '1', title: 'Describe', desc: 'Tell the AI director your video idea via text or voice', icon: '\uD83C\uDFA4' },
              { num: '2', title: 'Preview', desc: 'See AI-generated scene previews inline in the conversation', icon: '\uD83D\uDDBC\uFE0F' },
              { num: '3', title: 'Edit', desc: 'Refine scenes, reorder, change speakers, ask for revisions', icon: '\u270F\uFE0F' },
              { num: '4', title: 'Download', desc: 'Get your finished MP4 with visuals, voice, lipsync & music', icon: '\uD83C\uDFAC' },
            ].map((s, i) => (
              <div key={s.num} style={{
                ...styles.howStep,
                animationDelay: `${0.7 + i * 0.1}s`,
              }}
                onMouseOver={e => {
                  e.currentTarget.style.background = 'rgba(102,126,234,0.04)'
                  e.currentTarget.style.transform = 'translateY(-2px)'
                }}
                onMouseOut={e => {
                  e.currentTarget.style.background = 'transparent'
                  e.currentTarget.style.transform = 'translateY(0)'
                }}
              >
                <div style={styles.howNum}>{s.icon}</div>
                <span style={styles.howStepTitle}>{s.title}</span>
                <span style={styles.howStepDesc}>{s.desc}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Tech stack */}
        <div style={styles.techStack}>
          {['Gemini 2.5', 'Google ADK', 'Veo 2.0', 'Imagen 4.0', 'Cloud TTS', 'Wav2Lip', 'FFmpeg'].map((t, i) => (
            <span key={t} style={{
              ...styles.techBadge,
              animationDelay: `${0.8 + i * 0.05}s`,
            }}>{t}</span>
          ))}
        </div>
        <p style={styles.poweredBy}>
          Built with Google AI &amp; Google Cloud for the Gemini Live Agent Challenge
        </p>
      </div>
    )
  }

  const fallback = (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
      <div style={{ width: 24, height: 24, border: '2px solid #667eea', borderTop: '2px solid transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
      <span style={{ color: '#5a6080', fontSize: 13, fontWeight: 500 }}>Loading CutTo...</span>
    </div>
  )

  if (isDone) return (
    <Suspense fallback={fallback}>
      <DoneView
        videoUrl={ws.videoUrl}
        onReset={ws.reset}
        onEditScenes={ws.editScenes}
      />
    </Suspense>
  )
  if (isGenerating) return (
    <Suspense fallback={fallback}>
      <GeneratingView
        progress={ws.progress}
        sceneStatuses={ws.sceneStatuses}
        scenePlan={ws.scenePlan}
        error={ws.error}
        onDismissError={ws.dismissError}
      />
    </Suspense>
  )
  return (
    <Suspense fallback={fallback}>
      <ConversationView ws={ws} />
    </Suspense>
  )
}

const styles = {
  container: {
    maxWidth: 860,
    margin: '0 auto',
    padding: '0 24px 60px',
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    overflow: 'hidden',
  },
  bgGrid: {
    position: 'fixed',
    top: 0, left: 0, right: 0, bottom: 0,
    backgroundImage: `linear-gradient(rgba(102,126,234,0.03) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(102,126,234,0.03) 1px, transparent 1px)`,
    backgroundSize: '64px 64px',
    pointerEvents: 'none',
  },
  glowOrb1: {
    position: 'fixed',
    top: -300,
    right: -200,
    width: 700,
    height: 700,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(102,126,234,0.12) 0%, transparent 60%)',
    pointerEvents: 'none',
    animation: 'float 8s ease-in-out infinite',
  },
  glowOrb2: {
    position: 'fixed',
    bottom: -300,
    left: -200,
    width: 700,
    height: 700,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(118,75,162,0.1) 0%, transparent 60%)',
    pointerEvents: 'none',
    animation: 'float 10s ease-in-out 2s infinite',
  },
  glowOrb3: {
    position: 'fixed',
    top: '30%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: 900,
    height: 900,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(52,211,153,0.03) 0%, transparent 40%)',
    pointerEvents: 'none',
  },

  // Hero
  hero: {
    textAlign: 'center',
    animation: 'fadeIn 0.8s ease-out',
    marginBottom: 12,
  },
  badgeWrap: {
    marginBottom: 24,
  },
  heroBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    padding: '6px 16px',
    borderRadius: 20,
    background: 'rgba(102,126,234,0.08)',
    border: '1px solid rgba(102,126,234,0.15)',
    color: '#8b9cf7',
    fontSize: 12,
    fontWeight: 600,
    letterSpacing: 0.3,
    animation: 'borderGlow 3s ease-in-out infinite',
  },
  heroBadgeDot: {
    width: 6,
    height: 6,
    borderRadius: '50%',
    background: '#27ae60',
    animation: 'pulse 2s ease-in-out infinite',
  },
  title: {
    fontSize: 96,
    fontWeight: 900,
    letterSpacing: -5,
    lineHeight: 1,
    marginBottom: 16,
    filter: 'drop-shadow(0 0 60px rgba(102,126,234,0.2))',
  },
  titleGradient: {
    background: 'linear-gradient(135deg, #667eea 0%, #9b6dff 30%, #e879f9 60%, #764ba2 100%)',
    backgroundSize: '300% auto',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    animation: 'gradientFlow 6s ease-in-out infinite',
  },
  subtitle: {
    fontSize: 22,
    fontWeight: 600,
    color: '#b8c0e8',
    letterSpacing: 0.3,
    marginBottom: 12,
  },
  description: {
    color: '#5a6080',
    fontSize: 15,
    lineHeight: 1.7,
    maxWidth: 500,
    margin: '0 auto',
  },
  ctaWrap: {
    marginTop: 32,
    display: 'inline-block',
    padding: 2,
    borderRadius: 20,
    background: 'linear-gradient(135deg, rgba(102,126,234,0.5), rgba(118,75,162,0.5), rgba(102,126,234,0.5))',
    backgroundSize: '200% 200%',
    animation: 'fadeIn 0.8s ease-out 0.4s both, gradientFlow 4s ease-in-out infinite',
    transition: 'background 0.4s ease',
  },
  ctaBtn: {
    padding: '20px 56px',
    fontSize: 18,
    fontWeight: 700,
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: '#fff',
    border: 'none',
    borderRadius: 18,
    cursor: 'pointer',
    boxShadow: '0 8px 40px rgba(102,126,234,0.35)',
    display: 'inline-flex',
    alignItems: 'center',
    transition: 'all 0.3s ease',
  },

  // Quick start
  quickStart: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 12,
    marginTop: 24,
    animation: 'fadeIn 0.8s ease-out 0.5s both',
  },
  quickLabel: {
    fontSize: 12,
    color: '#4a5070',
    letterSpacing: 1,
    textTransform: 'uppercase',
    fontWeight: 600,
  },
  quickChips: {
    display: 'flex',
    gap: 8,
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  quickChip: {
    padding: '12px 20px',
    borderRadius: 14,
    background: 'rgba(15,15,25,0.6)',
    border: '1px solid rgba(255,255,255,0.06)',
    color: '#8b9cf7',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
    backdropFilter: 'blur(10px)',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    display: 'flex',
    alignItems: 'center',
  },

  // Features
  features: {
    display: 'flex',
    gap: 14,
    marginTop: 56,
    width: '100%',
    animation: 'fadeIn 0.8s ease-out 0.6s both',
  },
  featureCard: {
    flex: 1,
    padding: '32px 24px',
    background: 'rgba(12,12,24,0.7)',
    backdropFilter: 'blur(16px)',
    borderRadius: 20,
    border: '1px solid rgba(255,255,255,0.04)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 12,
    textAlign: 'center',
    transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
    animation: 'fadeIn 0.8s ease-out both',
  },
  featureIcon: {
    width: 56,
    height: 56,
    borderRadius: 16,
    background: 'linear-gradient(135deg, rgba(102,126,234,0.08), rgba(118,75,162,0.08))',
    border: '1px solid rgba(102,126,234,0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  featureLabel: {
    fontSize: 15,
    fontWeight: 700,
    color: '#d0d5f0',
    letterSpacing: 0.2,
  },
  featureDesc: {
    fontSize: 12,
    color: '#6a7090',
    lineHeight: 1.6,
  },

  // How it works
  howSection: {
    marginTop: 64,
    width: '100%',
    textAlign: 'center',
    animation: 'fadeIn 0.8s ease-out 0.7s both',
  },
  howTitle: {
    fontSize: 18,
    fontWeight: 700,
    color: '#667eea',
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 28,
  },
  howSteps: {
    display: 'flex',
    gap: 12,
    justifyContent: 'center',
  },
  howStep: {
    flex: 1,
    maxWidth: 180,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 8,
    padding: '20px 16px',
    borderRadius: 16,
    transition: 'all 0.3s ease',
    animation: 'fadeIn 0.8s ease-out both',
  },
  howNum: {
    width: 44,
    height: 44,
    borderRadius: 14,
    background: 'linear-gradient(135deg, rgba(102,126,234,0.12), rgba(118,75,162,0.12))',
    border: '1px solid rgba(102,126,234,0.15)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 20,
  },
  howStepTitle: {
    fontSize: 14,
    fontWeight: 700,
    color: '#c8d0f0',
  },
  howStepDesc: {
    fontSize: 12,
    color: '#5a6080',
    lineHeight: 1.5,
  },

  // Tech stack
  techStack: {
    display: 'flex',
    gap: 8,
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginTop: 48,
    animation: 'fadeIn 0.8s ease-out 0.8s both',
  },
  techBadge: {
    padding: '6px 16px',
    borderRadius: 10,
    background: 'rgba(102,126,234,0.06)',
    border: '1px solid rgba(102,126,234,0.1)',
    color: '#6b7cc7',
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: 0.3,
    animation: 'fadeIn 0.8s ease-out both',
    transition: 'all 0.2s ease',
  },
  poweredBy: {
    marginTop: 16,
    color: '#2a3050',
    fontSize: 11,
    letterSpacing: 1,
    textTransform: 'uppercase',
    animation: 'fadeIn 0.8s ease-out 0.9s both',
  },
}
