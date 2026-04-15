'use client'

import { useState, useEffect, useCallback } from 'react'
import { sessionAPI, Session, SessionCreate } from '@/services/api'

export interface SessionState {
  currentSession: Session | null
  sessions: Session[]
  loading: boolean
  error: string | null
}

export function useSession() {
  const [sessionState, setSessionState] = useState<SessionState>({
    currentSession: null,
    sessions: [],
    loading: false,
    error: null,
  })

  const startSession = useCallback(async (sessionData: SessionCreate) => {
    setSessionState((prev) => ({
      ...prev,
      loading: true,
      error: null,
    }))

    try {
      const newSession = await sessionAPI.startSession(sessionData)
      
      setSessionState((prev) => ({
        ...prev,
        currentSession: newSession,
        loading: false,
      }))

      return newSession
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to start session'
      setSessionState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }))
      throw error
    }
  }, [])

  const endSession = useCallback(async (sessionId: number) => {
    setSessionState((prev) => ({
      ...prev,
      loading: true,
      error: null,
    }))

    try {
      const updatedSession = await sessionAPI.endSession(sessionId)
      
      setSessionState((prev) => ({
        ...prev,
        currentSession: updatedSession,
        loading: false,
      }))

      return updatedSession
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to end session'
      setSessionState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }))
      throw error
    }
  }, [])

  const loadSessions = useCallback(async () => {
    setSessionState((prev) => ({
      ...prev,
      loading: true,
      error: null,
    }))

    try {
      const sessions = await sessionAPI.getSessions()
      
      setSessionState((prev) => ({
        ...prev,
        sessions,
        loading: false,
      }))
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load sessions'
      setSessionState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }))
    }
  }, [])

  const getSession = useCallback(async (sessionId: number) => {
    setSessionState((prev) => ({
      ...prev,
      loading: true,
      error: null,
    }))

    try {
      const session = await sessionAPI.getSession(sessionId)
      
      setSessionState((prev) => ({
        ...prev,
        currentSession: session,
        loading: false,
      }))

      return session
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to get session'
      setSessionState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }))
      throw error
    }
  }, [])

  const clearCurrentSession = useCallback(() => {
    setSessionState((prev) => ({
      ...prev,
      currentSession: null,
    }))
  }, [])

  const clearError = useCallback(() => {
    setSessionState((prev) => ({
      ...prev,
      error: null,
    }))
  }, [])

  // Load sessions on mount
  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  return {
    sessionState,
    startSession,
    endSession,
    loadSessions,
    getSession,
    clearCurrentSession,
    clearError,
  }
}
