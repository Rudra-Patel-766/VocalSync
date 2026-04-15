'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useSearchParams } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { dashboardAPI, sessionAPI } from '@/services/api'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { BarChart3, TrendingUp, Clock, Award, Mic, Play, ArrowRight, Sparkles } from 'lucide-react'

const CHART_WIDTH = 720
const CHART_HEIGHT = 240
const CHART_PADDING = 24

export default function DashboardPage() {
  const { user, loading, logout } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const [analytics, setAnalytics] = useState<any>(null)
  const [insights, setInsights] = useState<any>(null)
  const [latestRecommendation, setLatestRecommendation] = useState<any>(null)
  const [loadingData, setLoadingData] = useState(true)
  const lastLoadKeyRef = useRef<string | null>(null)

  const sessionIdParam = searchParams.get('sessionId')
  const fromSessionParam = searchParams.get('fromSession') === '1'
  const navToken = searchParams.get('t')

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user) {
      const targetSessionId = sessionIdParam ? Number(sessionIdParam) : null
      const loadKey = `${user.id}-${targetSessionId ?? 'none'}-${fromSessionParam ? '1' : '0'}-${navToken ?? 'none'}`

      if (lastLoadKeyRef.current === loadKey) {
        return
      }
      lastLoadKeyRef.current = loadKey
      loadDashboardData(targetSessionId, fromSessionParam)
    }
  }, [user, sessionIdParam, fromSessionParam, navToken])

  const loadDashboardData = async (targetSessionId: number | null, fromSession: boolean) => {
    try {
      setLoadingData(true)

      // Load analytics first so dashboard becomes usable quickly.
      const analyticsData = await dashboardAPI.getAnalytics()
      setAnalytics(analyticsData)
      setLoadingData(false)

      const latestSessionId = analyticsData?.last_15_sessions?.length
        ? analyticsData.last_15_sessions[analyticsData.last_15_sessions.length - 1]?.session_id
        : null

      if (latestSessionId) {
        const loadLatestRecommendation = async () => {
          const maxPollAttempts = fromSession && targetSessionId === latestSessionId ? 6 : 2
          const pollDelayMs = 1200

          for (let attempt = 0; attempt < maxPollAttempts; attempt++) {
            try {
              const recommendationData = await sessionAPI.getRecommendations(latestSessionId)
              if (recommendationData.status === 'ready' || recommendationData.status === 'failed') {
                setLatestRecommendation(recommendationData)
                return
              }

              if (attempt < maxPollAttempts - 1) {
                await new Promise((resolve) => setTimeout(resolve, pollDelayMs))
              }
            } catch (error) {
              console.error('Failed to load latest recommendation:', error)
              return
            }
          }
        }

        loadLatestRecommendation()
      }

      // Single delayed refresh for newly finished sessions.
      if (fromSession && targetSessionId) {
        const hasSession = analyticsData?.last_15_sessions?.some((s: any) => s.session_id === targetSessionId)
        if (!hasSession) {
          const maxRefreshAttempts = 5
          const refreshDelayMs = 1500

          for (let attempt = 0; attempt < maxRefreshAttempts; attempt++) {
            await new Promise((resolve) => setTimeout(resolve, refreshDelayMs))

            try {
              const refreshedAnalytics = await dashboardAPI.getAnalytics()
              setAnalytics(refreshedAnalytics)

              const sessionNowPresent = refreshedAnalytics?.last_15_sessions?.some(
                (s: any) => s.session_id === targetSessionId
              )

              if (sessionNowPresent) {
                break
              }
            } catch (refreshError) {
              console.error('Failed to refresh dashboard analytics:', refreshError)
              break
            }
          }
        }
      }

      // Load insights without blocking first paint.
      dashboardAPI
        .getInsights()
        .then((insightsData) => setInsights(insightsData))
        .catch((error) => {
          console.error('Failed to load dashboard insights:', error)
        })
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      setLoadingData(false)
    } finally {
      // no-op: loading is finalized in try/catch to avoid waiting for deferred requests
    }
  }

  const handleLogout = async () => {
    await logout()
    router.push('/')
  }

  const formatPercentage = (value: number) => {
    const sign = value >= 0 ? '+' : ''
    return `${sign}${value.toFixed(1)}%`
  }

  const buildLinePath = (values: number[], maxValue: number) => {
    if (!values.length || maxValue <= 0) return ''

    const innerWidth = CHART_WIDTH - CHART_PADDING * 2
    const innerHeight = CHART_HEIGHT - CHART_PADDING * 2

    return values
      .map((value, index) => {
        const x = CHART_PADDING + (values.length === 1 ? innerWidth / 2 : (index / (values.length - 1)) * innerWidth)
        const normalized = Math.max(0, Math.min(1, value / maxValue))
        const y = CHART_PADDING + (1 - normalized) * innerHeight
        return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
      })
      .join(' ')
  }

  const trendSessions = analytics?.last_15_sessions || []
  const wpmSeries = trendSessions.map((s: any) => s.wpm || 0)
  const confidenceSeries = trendSessions.map((s: any) => (s.confidence_score || 0) * 200)
  const fillerSeries = trendSessions.map((s: any) => (s.filler_ratio || 0) * 200)
  const chartMax = Math.max(1, ...wpmSeries, ...confidenceSeries, ...fillerSeries)
  const wpmPath = buildLinePath(wpmSeries, chartMax)
  const confidencePath = buildLinePath(confidenceSeries, chartMax)
  const fillerPath = buildLinePath(fillerSeries, chartMax)

  const latestSession = trendSessions.length > 0 ? trendSessions[trendSessions.length - 1] : null
  const previousSession = trendSessions.length > 1 ? trendSessions[trendSessions.length - 2] : null
  const wpmDelta = latestSession && previousSession ? latestSession.wpm - previousSession.wpm : null
  const fillerDelta = latestSession && previousSession ? (latestSession.filler_ratio - previousSession.filler_ratio) * 100 : null
  const confidenceDelta = latestSession && previousSession ? (latestSession.confidence_score - previousSession.confidence_score) * 100 : null

  const recentSessions = [...trendSessions].slice(-5).reverse()

  if (loading || loadingData) {
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
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
              <p className="text-gray-600">Welcome back, {user.email}</p>
            </div>
            <div className="flex items-center space-x-4">
              <Button onClick={() => router.push('/practice')}>
                <Play className="h-4 w-4 mr-2" />
                New Session
              </Button>
              <Button variant="outline" onClick={handleLogout}>
                Logout
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Quick Stats */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Sessions</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {analytics?.last_15_sessions?.length || 0}
                  </p>
                </div>
                <div className="p-3 bg-primary-100 rounded-lg">
                  <Mic className="h-6 w-6 text-primary-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">WPM Growth</p>
                  <p className="text-2xl font-bold text-green-600">
                    {formatPercentage(analytics?.wpm_growth || 0)}
                  </p>
                </div>
                <div className="p-3 bg-success-100 rounded-lg">
                  <TrendingUp className="h-6 w-6 text-success-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Filler Reduction</p>
                  <p className="text-2xl font-bold text-green-600">
                    {formatPercentage(analytics?.filler_reduction || 0)}
                  </p>
                </div>
                <div className="p-3 bg-warning-100 rounded-lg">
                  <BarChart3 className="h-6 w-6 text-warning-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Practice Hours</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {((analytics?.last_15_sessions?.length || 0) * 0.5).toFixed(1)}
                  </p>
                </div>
                <div className="p-3 bg-secondary-100 rounded-lg">
                  <Clock className="h-6 w-6 text-secondary-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Performance Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Performance Trends</CardTitle>
                <CardDescription>Your speaking progress over time</CardDescription>
              </CardHeader>
              <CardContent>
                {trendSessions.length > 0 ? (
                  <div className="bg-gray-100 rounded-lg p-4">
                    <svg viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`} className="w-full h-64">
                      <rect x="0" y="0" width={CHART_WIDTH} height={CHART_HEIGHT} fill="transparent" />
                      <line
                        x1={CHART_PADDING}
                        y1={CHART_HEIGHT - CHART_PADDING}
                        x2={CHART_WIDTH - CHART_PADDING}
                        y2={CHART_HEIGHT - CHART_PADDING}
                        stroke="#94a3b8"
                        strokeWidth="1"
                      />
                      <line
                        x1={CHART_PADDING}
                        y1={CHART_PADDING}
                        x2={CHART_PADDING}
                        y2={CHART_HEIGHT - CHART_PADDING}
                        stroke="#94a3b8"
                        strokeWidth="1"
                      />
                      {wpmPath && (
                        <path d={wpmPath} fill="none" stroke="#2563eb" strokeWidth="3" strokeLinecap="round" />
                      )}
                      {confidencePath && (
                        <path d={confidencePath} fill="none" stroke="#16a34a" strokeWidth="3" strokeLinecap="round" />
                      )}
                      {fillerPath && (
                        <path d={fillerPath} fill="none" stroke="#f97316" strokeWidth="3" strokeLinecap="round" />
                      )}
                    </svg>
                    <div className="mt-3 flex items-center gap-6 text-sm text-gray-700">
                      <div className="flex items-center gap-2">
                        <span className="inline-block h-2.5 w-2.5 rounded-full bg-blue-600" />
                        WPM
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="inline-block h-2.5 w-2.5 rounded-full bg-green-600" />
                        Confidence (scaled)
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="inline-block h-2.5 w-2.5 rounded-full bg-orange-500" />
                        Filler ratio (scaled)
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
                    <div className="text-center text-gray-500">
                      <BarChart3 className="h-12 w-12 mx-auto mb-2" />
                      <p>No trend data yet</p>
                      <p className="text-sm">Complete sessions with analysis to populate the chart</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Recent Sessions */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Sessions</CardTitle>
                <CardDescription>Your latest practice sessions</CardDescription>
              </CardHeader>
              <CardContent>
                {recentSessions.map((session: any) => (
                  <div key={session.session_id} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
                    <div>
                      <p className="font-medium text-gray-900">Session {session.session_id}</p>
                      <p className="text-sm text-gray-600">
                        {new Date(session.date).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">{session.wpm.toFixed(0)} WPM</p>
                      <p className="text-sm text-gray-600">
                        Confidence: {(session.confidence_score * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                ))}
                {recentSessions.length > 0 && (
                  <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-4">
                    <div className="flex items-center gap-2 text-emerald-900 font-semibold mb-2">
                      <Sparkles className="h-4 w-4" />
                      Latest session context
                    </div>
                    <p className="text-sm text-emerald-900">
                      {wpmDelta !== null && fillerDelta !== null && confidenceDelta !== null ? (
                        <>
                          Your latest session changed by {wpmDelta >= 0 ? '+' : ''}{wpmDelta.toFixed(0)} WPM, filler ratio {fillerDelta >= 0 ? '+' : ''}{fillerDelta.toFixed(1)} points, and confidence {confidenceDelta >= 0 ? '+' : ''}{confidenceDelta.toFixed(1)} points versus the previous session.
                        </>
                      ) : (
                        <>Not enough history yet to calculate a session-to-session comparison.</>
                      )}
                    </p>
                  </div>
                )}
                
                {(!analytics?.last_15_sessions || analytics.last_15_sessions.length === 0) && (
                  <div className="text-center py-8 text-gray-500">
                    <Mic className="h-12 w-12 mx-auto mb-2" />
                    <p>No sessions yet</p>
                    <p className="text-sm">Start your first practice session to see data</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Latest Recommendation */}
            <Card>
              <CardHeader>
                <CardTitle>Latest Recommendation</CardTitle>
                <CardDescription>Personalized from your most recent analyzed session</CardDescription>
              </CardHeader>
              <CardContent>
                {latestRecommendation?.status === 'ready' && latestRecommendation?.recommendations ? (
                  <div className="whitespace-pre-line text-sm leading-relaxed text-gray-700">
                    {latestRecommendation.recommendations}
                  </div>
                ) : latestRecommendation?.status === 'failed' ? (
                  <p className="text-sm text-red-600">{latestRecommendation.error || 'Recommendation generation failed.'}</p>
                ) : (
                  <p className="text-sm text-gray-500">Waiting for your latest recommendation to finish generating.</p>
                )}
              </CardContent>
            </Card>

            {/* Insights */}
            <Card>
              <CardHeader>
                <CardTitle>Insights</CardTitle>
                <CardDescription>AI-powered recommendations</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {insights?.insights?.slice(0, 3).map((insight: string, index: number) => (
                    <div key={index} className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <p className="text-sm text-blue-800">{insight}</p>
                    </div>
                  ))}
                  
                  {(!insights?.insights || insights.insights.length === 0) && (
                    <p className="text-sm text-gray-500">Complete more sessions to get insights</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Recommendations */}
            <Card>
              <CardHeader>
                <CardTitle>Recommendations</CardTitle>
                <CardDescription>Ways to improve</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {insights?.recommendations?.slice(0, 3).map((recommendation: string, index: number) => (
                    <div key={index} className="flex items-start space-x-2">
                      <Award className="h-4 w-4 text-warning-500 mt-0.5 flex-shrink-0" />
                      <p className="text-sm text-gray-700">{recommendation}</p>
                    </div>
                  ))}
                  
                  {(!insights?.recommendations || insights.recommendations.length === 0) && (
                    <p className="text-sm text-gray-500">Practice more to get personalized recommendations</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button 
                  onClick={() => router.push('/practice')}
                  className="w-full"
                >
                  <Play className="h-4 w-4 mr-2" />
                  Start New Session
                </Button>
                
                <Button 
                  variant="outline"
                  onClick={() => router.push('/practice')}
                  className="w-full"
                >
                  View Session History
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
