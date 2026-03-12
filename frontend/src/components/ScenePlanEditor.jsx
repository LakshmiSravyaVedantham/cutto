import React, { useState } from 'react'
import useIsMobile from '../hooks/useIsMobile'

export default function ScenePlanEditor({ plan, onApprove, onUpdate, onAskRevision }) {
  const isMobile = useIsMobile()
  const [editingScene, setEditingScene] = useState(null)
  const [editNarration, setEditNarration] = useState('')
  const [editVisual, setEditVisual] = useState('')
  const [editSpeaker, setEditSpeaker] = useState('narrator')
  const [revisionNote, setRevisionNote] = useState('')

  const totalDuration = plan.scenes.reduce((sum, s) => sum + (s.target_duration || 0), 0)
  const durationLabel = totalDuration >= 60
    ? `~${Math.floor(totalDuration / 60)}m ${totalDuration % 60}s`
    : `~${totalDuration}s`

  const startEdit = (scene) => {
    setEditingScene(scene.scene_number)
    setEditNarration(scene.narration)
    setEditVisual(scene.visual_prompt)
    setEditSpeaker(scene.speaker || 'narrator')
  }

  const saveEdit = () => {
    const updated = {
      ...plan,
      scenes: plan.scenes.map(s =>
        s.scene_number === editingScene
          ? { ...s, narration: editNarration, visual_prompt: editVisual, speaker: editSpeaker }
          : s
      )
    }
    onUpdate(updated)
    setEditingScene(null)
  }

  const cancelEdit = () => {
    setEditingScene(null)
  }

  const handleRevision = () => {
    if (!revisionNote.trim()) return
    onAskRevision(revisionNote.trim())
    setRevisionNote('')
  }

  const addScene = () => {
    const lastScene = plan.scenes[plan.scenes.length - 1]
    const newScene = {
      scene_number: lastScene.scene_number + 1,
      speaker: 'narrator',
      narration: 'New scene narration — edit me!',
      visual_prompt: plan.visual_style_anchor + '. Describe the visual action here.',
      visual_type: 'video',
      target_duration: 6,
    }
    const updated = {
      ...plan,
      total_scenes: plan.total_scenes + 1,
      scenes: [...plan.scenes, newScene],
    }
    onUpdate(updated)
    // Auto-open edit for the new scene
    setEditingScene(newScene.scene_number)
    setEditNarration(newScene.narration)
    setEditVisual(newScene.visual_prompt)
  }

  const removeScene = (sceneNum) => {
    if (plan.scenes.length <= 1) return
    const filtered = plan.scenes
      .filter(s => s.scene_number !== sceneNum)
      .map((s, i) => ({ ...s, scene_number: i + 1 }))
    const updated = {
      ...plan,
      total_scenes: filtered.length,
      scenes: filtered,
    }
    onUpdate(updated)
    if (editingScene === sceneNum) setEditingScene(null)
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>{plan.title}</h3>
        <div style={{
          ...styles.meta,
          ...(isMobile ? { flexWrap: 'wrap' } : {}),
        }}>
          <span style={styles.badge}>{plan.scenes.length} scenes</span>
          <span style={styles.badge}>{durationLabel}</span>
          <span style={styles.badge}>{plan.mood}</span>
          <button
            style={{
              ...styles.badge,
              cursor: 'pointer',
              border: '1px solid',
              borderColor: plan.audio_driven ? '#e879f9' : 'rgba(102,126,234,0.3)',
              background: plan.audio_driven ? 'rgba(232,121,249,0.15)' : 'rgba(102,126,234,0.1)',
              color: plan.audio_driven ? '#e879f9' : '#667eea',
            }}
            onClick={() => onUpdate({ ...plan, audio_driven: !plan.audio_driven })}
            title={plan.audio_driven ? 'Audio drives video timing' : 'Video drives audio timing'}
          >
            {plan.audio_driven ? 'Audio-driven' : 'Video-driven'}
          </button>
        </div>
      </div>

      <div style={styles.sceneList}>
        {plan.scenes.map((scene) => (
          <div key={scene.scene_number} style={{
            ...styles.sceneCard,
            ...(isMobile ? { padding: '12px' } : {}),
          }}>
            <div style={{
              ...styles.sceneHeader,
              ...(isMobile ? { flexWrap: 'wrap', gap: 8 } : {}),
            }}>
              <span style={styles.sceneNum}>Scene {scene.scene_number}</span>
              <span style={{
                ...styles.speakerBadge,
                background: scene.speaker === 'narrator' ? 'rgba(102,126,234,0.15)' :
                  scene.speaker === 'character_1' ? 'rgba(232,121,249,0.15)' : 'rgba(52,211,153,0.15)',
                color: scene.speaker === 'narrator' ? '#667eea' :
                  scene.speaker === 'character_1' ? '#e879f9' : '#34d399',
              }}>{scene.speaker === 'narrator' ? 'Narrator' : scene.speaker === 'character_1' ? 'Char 1' : 'Char 2'}</span>
              <span style={styles.duration}>{scene.target_duration}s</span>
              {editingScene !== scene.scene_number && (
                <button style={{
                  ...styles.editBtn,
                  ...(isMobile ? { minHeight: 44, minWidth: 44, padding: '8px 16px' } : {}),
                }} onClick={() => startEdit(scene)}>
                  Edit
                </button>
              )}
              {plan.scenes.length > 1 && (
                <button style={{
                  ...styles.deleteBtn,
                  ...(isMobile ? { width: 44, height: 44, borderRadius: 10 } : {}),
                }} onClick={() => removeScene(scene.scene_number)} title="Remove scene">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              )}
            </div>

            {editingScene === scene.scene_number ? (
              <div style={styles.editArea}>
                <label style={styles.label}>Speaker</label>
                <select
                  style={styles.select}
                  value={editSpeaker}
                  onChange={e => setEditSpeaker(e.target.value)}
                >
                  <option value="narrator">Narrator (wide shots, no lipsync)</option>
                  <option value="character_1">Character 1 (close-up, lipsync)</option>
                  <option value="character_2">Character 2 (close-up, lipsync)</option>
                </select>
                <label style={styles.label}>Narration</label>
                <textarea
                  style={styles.textarea}
                  value={editNarration}
                  onChange={e => setEditNarration(e.target.value)}
                  rows={2}
                />
                <label style={styles.label}>Visual Description</label>
                <textarea
                  style={styles.textarea}
                  value={editVisual}
                  onChange={e => setEditVisual(e.target.value)}
                  rows={3}
                />
                <div style={styles.editBtnRow}>
                  <button style={{
                    ...styles.saveBtn,
                    ...(isMobile ? { minHeight: 44, padding: '10px 24px', fontSize: 14 } : {}),
                  }} onClick={saveEdit}>Save</button>
                  <button style={{
                    ...styles.cancelBtn,
                    ...(isMobile ? { minHeight: 44, padding: '10px 24px', fontSize: 14 } : {}),
                  }} onClick={cancelEdit}>Cancel</button>
                </div>
              </div>
            ) : (
              <div style={styles.sceneContent}>
                <div style={styles.field}>
                  <span style={styles.fieldIcon}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#667eea" strokeWidth="2">
                      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                    </svg>
                  </span>
                  <p style={styles.narration}>{scene.narration}</p>
                </div>
                <div style={styles.field}>
                  <span style={styles.fieldIcon}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#764ba2" strokeWidth="2">
                      <rect x="3" y="3" width="18" height="18" rx="2"/>
                      <circle cx="8.5" cy="8.5" r="1.5"/>
                      <polyline points="21 15 16 10 5 21"/>
                    </svg>
                  </span>
                  <p style={styles.visual}>{scene.visual_prompt.length > 120 ? scene.visual_prompt.slice(0, 120) + '...' : scene.visual_prompt}</p>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Add Scene button */}
      <button style={{
        ...styles.addSceneBtn,
        ...(isMobile ? { minHeight: 48, fontSize: 14 } : {}),
      }} onClick={addScene}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        Add Scene
      </button>

      {/* Revision input */}
      <div style={{
        ...styles.revisionArea,
        ...(isMobile ? { flexDirection: 'column', gap: 8 } : {}),
      }}>
        <input
          style={{
            ...styles.revisionInput,
            ...(isMobile ? { width: '100%', padding: '14px 14px', fontSize: 14 } : {}),
          }}
          value={revisionNote}
          onChange={e => setRevisionNote(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleRevision() } }}
          placeholder={isMobile ? "Ask AI to change something..." : "Ask AI to change something... (e.g. 'make it funnier' or 'add more action')"}
        />
        <button style={{
          ...styles.revisionBtn,
          ...(isMobile ? { width: '100%', minHeight: 44, fontSize: 14 } : {}),
        }} onClick={handleRevision}>
          Revise
        </button>
      </div>

      {/* Approve */}
      <button style={{
        ...styles.approveBtn,
        ...(isMobile ? { padding: '16px 20px', fontSize: 15, minHeight: 52 } : {}),
      }} onClick={onApprove}
        onMouseOver={e => {
          e.currentTarget.style.transform = 'translateY(-2px)'
          e.currentTarget.style.boxShadow = '0 8px 32px rgba(39,174,96,0.4)'
        }}
        onMouseOut={e => {
          e.currentTarget.style.transform = 'translateY(0)'
          e.currentTarget.style.boxShadow = '0 4px 24px rgba(39,174,96,0.3)'
        }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <polygon points="5 3 19 12 5 21 5 3"/>
        </svg>
        Looks great — Make my video!
      </button>
    </div>
  )
}

const styles = {
  container: {
    animation: 'fadeIn 0.5s ease-out',
  },
  header: {
    marginBottom: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: 800,
    background: 'linear-gradient(135deg, #667eea, #764ba2)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    marginBottom: 8,
  },
  meta: {
    display: 'flex',
    gap: 8,
  },
  badge: {
    padding: '4px 12px',
    borderRadius: 8,
    background: 'rgba(102,126,234,0.1)',
    color: '#667eea',
    fontSize: 12,
    fontWeight: 600,
    textTransform: 'capitalize',
  },
  sceneList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
  },
  sceneCard: {
    background: 'rgba(17,17,17,0.7)',
    backdropFilter: 'blur(10px)',
    borderRadius: 14,
    border: '1px solid rgba(255,255,255,0.05)',
    padding: '14px 16px',
    transition: 'border-color 0.2s',
  },
  sceneHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    marginBottom: 10,
  },
  sceneNum: {
    fontSize: 13,
    fontWeight: 700,
    color: '#667eea',
    flex: 1,
  },
  speakerBadge: {
    padding: '2px 10px',
    borderRadius: 6,
    fontSize: 10,
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  duration: {
    fontSize: 11,
    color: '#555',
    fontWeight: 600,
  },
  editBtn: {
    padding: '4px 14px',
    borderRadius: 8,
    background: 'rgba(255,255,255,0.06)',
    color: '#888',
    border: '1px solid rgba(255,255,255,0.08)',
    cursor: 'pointer',
    fontSize: 11,
    fontWeight: 600,
    transition: 'all 0.2s',
  },
  deleteBtn: {
    width: 28,
    height: 28,
    borderRadius: 8,
    background: 'transparent',
    color: '#555',
    border: '1px solid rgba(255,255,255,0.06)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s',
    flexShrink: 0,
  },
  addSceneBtn: {
    marginTop: 10,
    padding: '12px 20px',
    borderRadius: 12,
    background: 'rgba(102,126,234,0.08)',
    color: '#667eea',
    border: '1px dashed rgba(102,126,234,0.25)',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: 700,
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    transition: 'all 0.2s',
  },
  sceneContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
  },
  field: {
    display: 'flex',
    gap: 8,
    alignItems: 'flex-start',
  },
  fieldIcon: {
    flexShrink: 0,
    marginTop: 2,
  },
  narration: {
    fontSize: 13,
    color: '#ccc',
    lineHeight: 1.5,
    margin: 0,
  },
  visual: {
    fontSize: 12,
    color: '#666',
    lineHeight: 1.4,
    margin: 0,
    fontStyle: 'italic',
  },
  editArea: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
  },
  label: {
    fontSize: 11,
    color: '#667eea',
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  select: {
    width: '100%',
    padding: '10px 12px',
    borderRadius: 10,
    border: '1px solid rgba(102,126,234,0.2)',
    background: 'rgba(0,0,0,0.3)',
    color: '#fff',
    fontSize: 13,
    outline: 'none',
    fontFamily: 'inherit',
    cursor: 'pointer',
  },
  textarea: {
    width: '100%',
    padding: '10px 12px',
    borderRadius: 10,
    border: '1px solid rgba(102,126,234,0.2)',
    background: 'rgba(0,0,0,0.3)',
    color: '#fff',
    fontSize: 13,
    lineHeight: 1.5,
    outline: 'none',
    resize: 'vertical',
    fontFamily: 'inherit',
  },
  editBtnRow: {
    display: 'flex',
    gap: 8,
  },
  saveBtn: {
    padding: '6px 20px',
    borderRadius: 8,
    background: 'linear-gradient(135deg, #667eea, #764ba2)',
    color: '#fff',
    border: 'none',
    cursor: 'pointer',
    fontSize: 12,
    fontWeight: 700,
  },
  cancelBtn: {
    padding: '6px 20px',
    borderRadius: 8,
    background: 'transparent',
    color: '#888',
    border: '1px solid rgba(255,255,255,0.08)',
    cursor: 'pointer',
    fontSize: 12,
    fontWeight: 600,
  },
  revisionArea: {
    display: 'flex',
    gap: 8,
    marginTop: 16,
    marginBottom: 12,
  },
  revisionInput: {
    flex: 1,
    padding: '12px 16px',
    borderRadius: 12,
    border: '1px solid rgba(255,255,255,0.08)',
    background: 'rgba(17,17,17,0.8)',
    color: '#fff',
    fontSize: 13,
    outline: 'none',
  },
  revisionBtn: {
    padding: '12px 24px',
    borderRadius: 12,
    background: 'rgba(102,126,234,0.15)',
    color: '#667eea',
    border: '1px solid rgba(102,126,234,0.2)',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: 700,
    flexShrink: 0,
    transition: 'all 0.2s',
  },
  approveBtn: {
    padding: '18px 28px',
    borderRadius: 16,
    background: 'linear-gradient(135deg, #27ae60, #2ecc71)',
    color: '#fff',
    border: 'none',
    cursor: 'pointer',
    fontSize: 16,
    fontWeight: 700,
    width: '100%',
    boxShadow: '0 4px 24px rgba(39,174,96,0.3)',
    transition: 'all 0.2s',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
}
