'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Mic, BarChart3, Target, Video } from 'lucide-react'

export default function HomePage() {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && user) {
      router.push('/dashboard')
    }
  }, [user, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (user) {
    return null // Will redirect to dashboard
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-white">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            AI Speech Coach
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Transform your public speaking skills with real-time AI-powered feedback. 
            Practice, analyze, and improve your communication confidence.
          </p>
          <div className="mt-8">
            <Button onClick={() => router.push('/login')} size="lg" className="mr-4">
              Get Started
            </Button>
            <Button variant="outline" size="lg">
              Learn More
            </Button>
          </div>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
          <Card className="text-center">
            <CardHeader>
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Mic className="w-6 h-6 text-primary-600" />
              </div>
              <CardTitle className="text-lg">Real-time Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Get instant feedback on your speaking rate, filler words, and voice clarity
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <div className="w-12 h-12 bg-success-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-6 h-6 text-success-600" />
              </div>
              <CardTitle className="text-lg">Progress Tracking</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Monitor your improvement with detailed analytics and trend analysis
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <div className="w-12 h-12 bg-warning-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Target className="w-6 h-6 text-warning-600" />
              </div>
              <CardTitle className="text-lg">Goal-Based Practice</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Focus on specific areas like reducing fillers or interview preparation
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Video className="w-6 h-6 text-secondary-600" />
              </div>
              <CardTitle className="text-lg">Video Recording</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Record yourself to review body language and presentation skills
              </CardDescription>
            </CardContent>
          </Card>
        </div>

        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-8">
            Ready to Transform Your Speaking Skills?
          </h2>
          <Button onClick={() => router.push('/login')} size="lg">
            Start Your Journey
          </Button>
        </div>
      </div>
    </div>
  )
}
