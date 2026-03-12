import { useState, useRef, useCallback, useEffect } from 'react'

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

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => {
      setConnected(false)
      setTimeout(() => {
        if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
          connect()
        }
      }, 2000)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

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
          setPreviews(prev => [...prev, data.image_data])
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
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
    }
  }, [])

  return {
    messages, scenePlan, previews, progress, videoUrl, error,
    connected, isThinking, connect, sendText, approve, updatePlan
  }
}
