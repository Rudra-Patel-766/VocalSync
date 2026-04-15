'use client'

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || '',
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || '',
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || '',
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || '',
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || '',
}

let firebaseApp: any = null
let firebaseAuth: any = null
let googleProvider: any = null

async function getFirebaseClient() {
  if (typeof window === 'undefined') {
    throw new Error('Firebase auth is only available in the browser')
  }

  const [{ getApp, getApps, initializeApp }, authModule] = await Promise.all([
    import('firebase/app'),
    import('firebase/auth'),
  ])

  if (!firebaseApp) {
    firebaseApp = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig)
  }

  if (!firebaseAuth) {
    firebaseAuth = authModule.getAuth(firebaseApp)
  }

  if (!googleProvider) {
    googleProvider = new authModule.GoogleAuthProvider()
    googleProvider.addScope('email')
    googleProvider.addScope('profile')
  }

  return {
    authModule,
    auth: firebaseAuth,
    googleProvider,
  }
}

export const signInWithGoogle = async () => {
  try {
    const { authModule, auth, googleProvider } = await getFirebaseClient()
    const result = await authModule.signInWithPopup(auth, googleProvider)
    const credential = authModule.GoogleAuthProvider.credentialFromResult(result)
    const token = credential?.accessToken
    const user = result.user
    
    // Get ID token for backend verification
    const idToken = await user.getIdToken()
    
    return {
      user: {
        uid: user.uid,
        email: user.email,
        displayName: user.displayName,
        photoURL: user.photoURL,
      },
      idToken,
      token,
    }
  } catch (error) {
    console.error('Google sign-in error:', error)
    throw error
  }
}

export const logoutFromFirebase = async () => {
  try {
    const { authModule, auth } = await getFirebaseClient()
    await authModule.signOut(auth)
  } catch (error) {
    console.error('Firebase logout error:', error)
    throw error
  }
}
