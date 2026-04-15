'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Chrome, Loader2 } from 'lucide-react'

function getSignInErrorMessage(error: unknown): string {
  if (typeof error === 'object' && error !== null) {
    if ('code' in error && error.code === 'auth/popup-closed-by-user') {
      return 'Google sign-in was cancelled before completion.'
    }

    if ('code' in error && error.code === 'auth/popup-blocked') {
      return 'The browser blocked the Google sign-in popup. Allow popups and try again.'
    }

    if (
      'response' in error &&
      error.response &&
      typeof error.response === 'object' &&
      'data' in error.response &&
      error.response.data &&
      typeof error.response.data === 'object' &&
      'detail' in error.response.data &&
      typeof error.response.data.detail === 'string'
    ) {
      return error.response.data.detail
    }

    if ('message' in error && typeof error.message === 'string' && error.message.trim()) {
      return error.message
    }
  }

  return 'Failed to sign in. Please try again.'
}

export default function LoginPage() {
  const { user, loading, login } = useAuth()
  const router = useRouter()
  const [isSigningIn, setIsSigningIn] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (user && !loading) {
      router.push('/dashboard')
    }
  }, [user, loading, router])

  const handleGoogleSignIn = async () => {
    try {
      setIsSigningIn(true)
      setError(null)

      // Sign in with Firebase
      const { signInWithGoogle } = await import('@/services/firebase')
      const { idToken } = await signInWithGoogle()

      // Login to backend
      await login(idToken)

      router.push('/dashboard')
    } catch (error) {
      console.error('Sign in error:', error)
      setError(getSignInErrorMessage(error))
    } finally {
      setIsSigningIn(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-white flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            AI Speech Coach
          </h1>
          <p className="text-gray-600">
            Sign in to start improving your public speaking skills
          </p>
        </div>

        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Welcome Back</CardTitle>
            <CardDescription>
              Sign in with your Google account to continue
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="bg-error-50 border border-error-200 text-error-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <Button
              onClick={handleGoogleSignIn}
              disabled={isSigningIn}
              className="w-full"
              size="lg"
            >
              {isSigningIn ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  <Chrome className="mr-2 h-4 w-4" />
                  Continue with Google
                </>
              )}
            </Button>

            <div className="text-center text-sm text-gray-600">
              By signing in, you agree to our Terms of Service and Privacy Policy
            </div>
          </CardContent>
        </Card>

        <div className="mt-8 text-center text-sm text-gray-600">
          <p>
            New to AI Speech Coach?{' '}
            <button className="text-primary-600 hover:text-primary-700 font-medium">
              Learn more
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}
