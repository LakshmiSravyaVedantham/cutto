import { useState, useRef, useCallback, useEffect, useMemo } from 'react'

function friendlyError(message) {
  if (!message) return 'Something went wrong. Please try again.'
  const lower = message.toLowerCase()
  if (lower.includes('quota') || lower.includes('rate limit') || lower.includes('429'))
    return 'API rate limit reached. Please wait a minute and try again.'
  if (lower.includes('api key') || lower.includes('api_key') || lower.includes('invalid key'))
    return 'API key issue. The server may need a valid Google API key configured.'
  if (lower.includes('veo') && (lower.includes('fail') || lower.includes('error')))
    return 'Video generation failed. The AI will retry with a fallback method.'
  if (lower.includes('timeout'))
    return 'Request timed out. The server may be busy — try again in a moment.'
  if (lower.includes('model') && lower.includes('not found'))
    return 'AI model unavailable. Please try again later.'
  return message
}

export default function useWebSocket() {
  const [messages, setMessages] = useState([])
  const [scenePlan, setScenePlan] = useState(null)
  const [previews, setPreviews] = useState([])
  const [progress, setProgress] = useState(null)
  const [sceneStatuses, setSceneStatuses] = useState({})
  const [videoUrl, setVideoUrl] = useState(null)
  const [error, setError] = useState(null)
  const [connected, setConnected] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [isThinking, setIsThinking] = useState(false)
  const [connectionLost, setConnectionLost] = useState(false)
  const wsRef = useRef(null)
  const retriesRef = useRef(0)
  const reconnectTimer = useRef(null)
  const isThinkingRef = useRef(false)
  const lastSentRef = useRef({ text: '', at: 0 })
  const pendingPromptRef = useRef(null)
  const errorTimerRef = useRef(null)

  useEffect(() => {
    isThinkingRef.current = isThinking
  }, [isThinking])

  const connect = useCallback((demoKey = '') => {
    const explicitKey = typeof demoKey === 'string' ? demoKey : ''
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    // Pass demo key from URL param or explicit argument
    const key =
      explicitKey || new URLSearchParams(window.location.search).get('key') || ''
    const wsUrl = `${protocol}//${host}/ws${key ? `?key=${encodeURIComponent(key)}` : ''}`

    setConnecting(true)
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setConnecting(false)
      setConnected(true)
      setConnectionLost(false)
      retriesRef.current = 0
    }
    ws.onclose = () => {
      setConnecting(false)
      // Use functional setState to read current value — avoids stale closure
      // (connect has [] deps so the outer 'connected' is always false)
      setConnected(prev => {
        if (prev) {
          setConnectionLost(true)
        } else if (retriesRef.current === 0) {
          // First failed attempt — show error so user isn't left guessing
          setError('Can\u2019t reach the server. Make sure the backend is running.')
        }
        return false
      })
      const attempt = (retriesRef.current || 0)
      retriesRef.current = attempt + 1
      const delay = Math.min(1000 * Math.pow(2, attempt), 30000)
      reconnectTimer.current = setTimeout(() => {
        if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
          connect(key)
        }
      }, delay)
    }
    ws.onerror = () => {
      // onerror fires before onclose; don't duplicate state changes
    }

    ws.onmessage = (event) => {
      let data
      try {
        data = JSON.parse(event.data)
      } catch {
        console.warn('Malformed WebSocket message:', event.data)
        setIsThinking(false)
        return
      }

      switch (data.type) {
        case 'transcript':
          if (data.role === 'agent') {
            setIsThinking(false)
          }
          // Only add agent messages — user messages are added optimistically in sendText
          if (data.role === 'agent') {
            setMessages(prev => [...prev, { role: data.role, text: data.text }])
            // Auto-send queued prompt after welcome message
            if (pendingPromptRef.current) {
              const prompt = pendingPromptRef.current
              pendingPromptRef.current = null
              setTimeout(() => {
                setMessages(prev => [...prev, { role: 'user', text: prompt }])
                setIsThinking(true)
                setError(null)
                lastSentRef.current = { text: prompt, at: Date.now() }
                if (wsRef.current?.readyState === WebSocket.OPEN) {
                  wsRef.current.send(JSON.stringify({ type: 'text', text: prompt }))
                }
              }, 500)
            }
          }
          break
        case 'scene_preview':
          setPreviews(prev => [...prev.slice(-9), data.image_data])
          break
        case 'scene_plan':
          setScenePlan(data.plan)
          setIsThinking(false)
          break
        case 'pipeline_progress':
          setProgress(data)
          // Track per-scene status so parallel batches don't overwrite each other
          if (data.scene > 0) {
            setSceneStatuses(prev => ({
              ...prev,
              [data.scene]: { step: data.step, status: data.status, thumbnail: data.thumbnail || prev[data.scene]?.thumbnail }
            }))
          }
          break
        case 'complete':
          setVideoUrl(data.video_url)
          setProgress(null)
          setSceneStatuses({})
          break
        case 'error':
          setError(friendlyError(data.message))
          setIsThinking(false)
          // Only clear progress for fatal errors, not scene-level ones
          if (!data.scene) setProgress(null)
          // Auto-dismiss non-critical errors after 15s
          clearTimeout(errorTimerRef.current)
          errorTimerRef.current = setTimeout(() => setError(null), 15000)
          break
      }
    }
  }, [])

  const send = useCallback((msg) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    }
  }, [])

  const sendText = useCallback((text, image = null) => {
    const normalized = text.trim()
    if (!normalized) return

    // Ignore accidental double-submits while the agent is already working.
    if (isThinkingRef.current) return

    const now = Date.now()
    if (
      lastSentRef.current.text === normalized &&
      now - lastSentRef.current.at < 2000
    ) {
      return
    }
    lastSentRef.current = { text: normalized, at: now }

    // Optimistic: show user message immediately
    setMessages(prev => [...prev, { role: 'user', text: normalized, image }])
    setIsThinking(true)
    setError(null)
    const msg = { type: 'text', text: normalized }
    if (image) msg.image = image
    send(msg)
  }, [send])

  const approve = useCallback(() => {
    setIsThinking(true)
    send({ type: 'approve' })
  }, [send])

  const updatePlan = useCallback((plan) => {
    send({ type: 'update_plan', plan })
  }, [send])

  const dismissError = useCallback(() => {
    setError(null)
    clearTimeout(errorTimerRef.current)
  }, [])

  useEffect(() => {
    return () => {
      clearTimeout(reconnectTimer.current)
      clearTimeout(errorTimerRef.current)
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
    }
  }, [])

  const reset = useCallback(() => {
    setMessages([])
    setScenePlan(null)
    setPreviews([])
    setProgress(null)
    setSceneStatuses({})
    setVideoUrl(null)
    setError(null)
  }, [])

  const editScenes = useCallback(() => {
    setVideoUrl(null)
    setProgress(null)
    setSceneStatuses({})
  }, [])

  const connectWithPrompt = useCallback((prompt, demoKey = '') => {
    pendingPromptRef.current = prompt
    connect(demoKey)
  }, [connect])

  return useMemo(() => ({
    messages, scenePlan, previews, progress, sceneStatuses, videoUrl, error,
    connected, connecting, connectionLost, isThinking, connect, connectWithPrompt,
    sendText, approve, updatePlan, reset, editScenes, dismissError
  }), [messages, scenePlan, previews, progress, sceneStatuses, videoUrl, error,
       connected, connecting, connectionLost, isThinking, connect, connectWithPrompt,
       sendText, approve, updatePlan, reset, editScenes, dismissError])
}
