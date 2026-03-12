import { useState, useRef, useCallback, useEffect, useMemo } from 'react'

export default function useWebSocket() {
  const [messages, setMessages] = useState([])
  const [scenePlan, setScenePlan] = useState(null)
  const [previews, setPreviews] = useState([])
  const [progress, setProgress] = useState(null)
  const [videoUrl, setVideoUrl] = useState(null)
  const [error, setError] = useState(null)
  const [connected, setConnected] = useState(false)
  const [isThinking, setIsThinking] = useState(false)
  const wsRef = useRef(null)
  const retriesRef = useRef(0)
  const reconnectTimer = useRef(null)

  const connect = useCallback((demoKey = '') => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    // Pass demo key from URL param or explicit argument
    const key = demoKey || new URLSearchParams(window.location.search).get('key') || ''
    const wsUrl = `${protocol}//${host}/ws${key ? `?key=${encodeURIComponent(key)}` : ''}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      retriesRef.current = 0
    }
    ws.onclose = () => {
      setConnected(false)
      const attempt = (retriesRef.current || 0)
      retriesRef.current = attempt + 1
      const delay = Math.min(1000 * Math.pow(2, attempt), 30000)
      reconnectTimer.current = setTimeout(() => {
        if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
          connect(key)
        }
      }, delay)
    }

    ws.onmessage = (event) => {
      let data
      try {
        data = JSON.parse(event.data)
      } catch {
        console.warn('Malformed WebSocket message:', event.data)
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
          break
        case 'complete':
          setVideoUrl(data.video_url)
          setProgress(null)
          break
        case 'error':
          setError(data.message)
          setIsThinking(false)
          break
      }
    }
  }, [])

  const send = useCallback((msg) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    }
  }, [])

  const sendText = useCallback((text) => {
    // Optimistic: show user message immediately
    setMessages(prev => [...prev, { role: 'user', text }])
    setIsThinking(true)
    setError(null)
    send({ type: 'text', text })
  }, [send])

  const approve = useCallback(() => {
    setIsThinking(true)
    send({ type: 'approve' })
  }, [send])

  const updatePlan = useCallback((plan) => {
    send({ type: 'update_plan', plan })
  }, [send])

  useEffect(() => {
    return () => {
      clearTimeout(reconnectTimer.current)
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
    }
  }, [])

  return useMemo(() => ({
    messages, scenePlan, previews, progress, videoUrl, error,
    connected, isThinking, connect, sendText, approve, updatePlan
  }), [messages, scenePlan, previews, progress, videoUrl, error,
       connected, isThinking, connect, sendText, approve, updatePlan])
}
