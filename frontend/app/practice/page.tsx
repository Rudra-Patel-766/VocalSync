'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { useSession } from '@/hooks/useSession'
import { useAudio } from '@/hooks/useAudio'
import { useWebSocket } from '@/hooks/useWebSocket'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Mic, MicOff, Video, VideoOff, Square, Play, Pause, AlertCircle } from 'lucide-react'

const PRACTICE_GOALS = [
  { value: 'reduce_fillers', label: 'Reduce Filler Words', description: 'Focus on eliminating um, uh, like, etc.' },
  { value: 'improve_fluency', label: 'Improve Fluency', description: 'Better flow and pacing' },
  { value: 'interview_practice', label: 'Interview Practice', description: 'Professional communication skills' },
  { value: 'presentation_practice', label: 'Presentation Practice', description: 'Public speaking skills' },
]

export default function PracticePage() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const { sessionState, startSession, endSession } = useSession()
  const { wsState, disconnect, sendAudioChunk } = useWebSocket(sessionState.currentSession?.id || null)
  const { audioState, startRecording, stopRecording, pauseRecording, resumeRecording } = useAudio((audioChunk) => {
    if (sessionState.currentSession) {
      sendAudioChunk(audioChunk, selectedGoal)
    }
  })

  const [selectedGoal, setSelectedGoal] = useState<string>('improve_fluency')
  const [isVideoEnabled, setIsVideoEnabled] = useState(false)
  const [sessionPhase, setSessionPhase] = useState<'setup' | 'recording' | 'analysis' | 'complete'>('setup')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (wsState.error) {
      setError(wsState.error)
    }
  }, [wsState.error])

  const handleStartSession = async () => {
    try {
      setError(null)
      await startSession({
        goal: selectedGoal,
        context: 'Practice session',
      })
      
      setSessionPhase('recording')
      await startRecording()
    } catch (error) {
      setError('Failed to start session. Please try again.')
    }
  }

  const handleStopSession = async () => {
    const sessionId = sessionState.currentSession?.id
    try {
      setError(null)
      setSessionPhase('analysis')
      
      await stopRecording()
      disconnect()
      
      if (sessionId) {
        try {
          await endSession(sessionId)
        } catch (endError) {
          console.error('Failed to mark session as ended before redirect:', endError)
        }

        router.push(`/dashboard?sessionId=${sessionId}&fromSession=1&t=${Date.now()}`)
        return
      }
    } catch (error) {
      if (sessionId) {
        router.push(`/dashboard?sessionId=${sessionId}&fromSession=1&t=${Date.now()}`)
        return
      }
      setError('Failed to end session. Please try again.')
    }
  }

  useEffect(() => {
    if (wsState.analysisResults && sessionState.currentSession?.id) {
      disconnect()
      router.push(`/dashboard?sessionId=${sessionState.currentSession.id}&fromSession=1&t=${Date.now()}`)
    }
  }, [disconnect, router, sessionState.currentSession?.id, wsState.analysisResults])

  const handlePauseResume = () => {
    if (audioState.isPaused) {
      resumeRecording()
    } else {
      pauseRecording()
    }
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!user) {
    return null // Will redirect to login
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Practice Session</h1>
          <p className="text-gray-600">Improve your speaking skills with real-time feedback</p>
        </div>

        {error && (
          <div className="mb-6 bg-error-50 border border-error-200 text-error-700 px-4 py-3 rounded-lg flex items-center">
            <AlertCircle className="h-5 w-5 mr-2" />
            {error}
          </div>
        )}

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Practice Area */}
          <div className="lg:col-span-2 space-y-6">
            {/* Video/Audio Preview */}
            <Card>
              <CardContent className="p-6">
                <div className="aspect-video bg-gray-900 rounded-lg flex items-center justify-center">
                  {isVideoEnabled ? (
                    <div className="text-white text-center">
                      <Video className="h-12 w-12 mx-auto mb-2" />
                      <p>Video feed will appear here</p>
                    </div>
                  ) : (
                    <div className="text-white text-center">
                      <Mic className="h-12 w-12 mx-auto mb-2" />
                      <p>Audio recording active</p>
                    </div>
                  )}
                </div>

                {/* Recording Controls */}
                <div className="flex items-center justify-center mt-6 space-x-4">
                  {sessionPhase === 'setup' && (
                    <Button
                      onClick={handleStartSession}
                      size="lg"
                      className="bg-success-600 hover:bg-success-700"
                    >
                      <Play className="h-5 w-5 mr-2" />
                      Start Practice
                    </Button>
                  )}

                  {sessionPhase === 'recording' && (
                    <>
                      <Button
                        onClick={handlePauseResume}
                        variant="outline"
                        size="lg"
                      >
                        {audioState.isPaused ? (
                          <Play className="h-5 w-5 mr-2" />
                        ) : (
                          <Pause className="h-5 w-5 mr-2" />
                        )}
                        {audioState.isPaused ? 'Resume' : 'Pause'}
                      </Button>

                      <Button
                        onClick={handleStopSession}
                        size="lg"
                        className="bg-red-600 hover:bg-red-700"
                      >
                        <Square className="h-5 w-5 mr-2" />
                        End Session
                      </Button>
                    </>
                  )}
                </div>

                {/* Session Timer */}
                {sessionPhase === 'recording' && (
                  <div className="text-center mt-4">
                    <div className="text-2xl font-mono text-gray-900">
                      {formatDuration(audioState.duration)}
                    </div>
                    <div className="text-sm text-gray-600">Recording duration</div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Real-time Metrics */}
            {sessionPhase === 'recording' && (
              <Card>
                <CardHeader>
                  <CardTitle>Real-time Feedback</CardTitle>
                  <CardDescription>Live analysis of your speech</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {wsState.metrics.pace_feedback && (
                      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="text-lg font-semibold text-blue-900">{wsState.metrics.pace_feedback}</p>
                      </div>
                    )}
                    {wsState.metrics.volume_feedback && (
                      <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                        <p className="text-lg font-semibold text-amber-900">{wsState.metrics.volume_feedback}</p>
                      </div>
                    )}
                    {wsState.metrics.filler_feedback && (
                      <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
                        <p className="text-lg font-semibold text-purple-900">{wsState.metrics.filler_feedback}</p>
                      </div>
                    )}
                    {wsState.metrics.silence_feedback && (
                      <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                        <p className="text-lg font-semibold text-green-900">{wsState.metrics.silence_feedback}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* AI Coach Feedback */}
            {sessionPhase === 'analysis' && wsState.analysisResults?.ai_recommendations && (
              <Card>
                <CardHeader>
                  <CardTitle>Your AI Coach Feedback</CardTitle>
                  <CardDescription>Personalized recommendations based on your session</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="whitespace-pre-line text-gray-700 text-sm leading-relaxed">
                    {wsState.analysisResults.ai_recommendations}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Goal Selection */}
            {sessionPhase === 'setup' && (
              <Card>
                <CardHeader>
                  <CardTitle>Practice Goal</CardTitle>
                  <CardDescription>Choose your focus area</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {PRACTICE_GOALS.map((goal) => (
                      <div
                        key={goal.value}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          selectedGoal === goal.value
                            ? 'border-primary-500 bg-primary-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => setSelectedGoal(goal.value)}
                      >
                        <div className="font-medium text-gray-900">{goal.label}</div>
                        <div className="text-sm text-gray-600">{goal.description}</div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Audio/Video Settings */}
            <Card>
              <CardHeader>
                <CardTitle>Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Microphone</span>
                  <div className="flex items-center">
                    <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse mr-2"></div>
                    <span className="text-sm text-gray-600">Active</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Video</span>
                  <button
                    onClick={() => setIsVideoEnabled(!isVideoEnabled)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      isVideoEnabled ? 'bg-primary-600' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        isVideoEnabled ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </CardContent>
            </Card>

            {/* Session Status */}
            {sessionPhase !== 'setup' && (
              <Card>
                <CardHeader>
                  <CardTitle>Session Status</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Connection</span>
                      <span className={`text-sm font-medium ${
                        wsState.connected ? 'text-success-600' : 'text-error-600'
                      }`}>
                        {wsState.connected ? 'Connected' : 'Disconnected'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Recording</span>
                      <span className={`text-sm font-medium ${
                        audioState.isRecording ? 'text-success-600' : 'text-gray-600'
                      }`}>
                        {audioState.isRecording ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Phase</span>
                      <span className="text-sm font-medium capitalize">{sessionPhase}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
