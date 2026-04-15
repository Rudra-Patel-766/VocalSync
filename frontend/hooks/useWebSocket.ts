'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { wsService, WebSocketMessage } from '@/services/websocket'
import { RealtimeMetrics } from '@/services/api'

export interface WebSocketState {
  connected: boolean
  connecting: boolean
  error: string | null
  metrics: RealtimeMetrics
  analysisResults: any
}

export function useWebSocket(sessionId: number | null) {
  const [wsState, setWsState] = useState<WebSocketState>({
    connected: false,
    connecting: false,
    error: null,
    metrics: {},
    analysisResults: null,
  })

  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const sessionIdRef = useRef<number | null>(null)
  const connectedRef = useRef(false)
  const connectingRef = useRef(false)

  const startPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
    }

    pingIntervalRef.current = setInterval(() => {
      wsService.sendPing()
    }, 30000)
  }, [])

  const clearPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }
  }, [])

  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'realtime_feedback':
        setWsState((prev) => ({
          ...prev,
          metrics: message.metrics || {},
        }))
        break

      case 'analysis_complete':
        setWsState((prev) => ({
          ...prev,
          analysisResults: message.results,
        }))
        break

      case 'error':
        setWsState((prev) => ({
          ...prev,
          error: message.message || 'Unknown error occurred',
        }))
        break

      case 'pong':
        break

      default:
        console.log('Unknown message type:', message.type)
    }
  }, [])

  const connect = useCallback(async (id: number) => {
    if (connectingRef.current || connectedRef.current) {
      return
    }

    connectingRef.current = true

    setWsState((prev) => ({
      ...prev,
      connecting: true,
      error: null,
    }))

    try {
      await wsService.connect(id, handleMessage)
      sessionIdRef.current = id
      connectedRef.current = true
      connectingRef.current = false
      
      setWsState((prev) => ({
        ...prev,
        connected: true,
        connecting: false,
      }))

      // Start ping interval
      startPingInterval()
    } catch (error) {
      console.error('WebSocket connection failed:', error)
      connectedRef.current = false
      connectingRef.current = false
      setWsState((prev) => ({
        ...prev,
        connected: false,
        connecting: false,
        error: 'Failed to connect to server',
      }))
    }
  }, [handleMessage, startPingInterval])

  const disconnect = useCallback(() => {
    wsService.disconnect()
    clearPingInterval()
    connectedRef.current = false
    connectingRef.current = false
    sessionIdRef.current = null
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    setWsState((prev) => ({
      ...prev,
      connected: false,
      connecting: false,
      error: null,
    }))
  }, [clearPingInterval])

  const sendAudioChunk = useCallback((audioData: Float32Array, goal: string) => {
    wsService.sendAudioChunk(audioData, goal)
  }, [])

  const sendSessionComplete = useCallback((audioData: Float32Array, goal: string) => {
    wsService.sendSessionComplete(audioData, goal)
  }, [])

  const clearError = useCallback(() => {
    setWsState((prev) => ({ ...prev, error: null }))
  }, [])

  // Auto-connect when sessionId changes
  useEffect(() => {
    if (sessionId && sessionId !== sessionIdRef.current) {
      disconnect()
      connect(sessionId)
    }

    return () => {
      disconnect()
    }
  }, [sessionId, connect, disconnect])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return {
    wsState,
    connect,
    disconnect,
    sendAudioChunk,
    sendSessionComplete,
    clearError,
  }
}
