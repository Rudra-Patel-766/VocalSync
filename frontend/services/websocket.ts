export interface WebSocketMessage {
  type: string
  data?: any
  metrics?: any
  message?: string
  results?: any
}

export class WebSocketService {
  private ws: WebSocket | null = null
  private url: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private isConnecting = false
  private manualDisconnect = false

  constructor() {
    this.url = process.env.NEXT_PUBLIC_API_URL?.replace('http', 'ws') || 'ws://localhost:8000'
  }

  connect(sessionId: number, onMessage: (message: WebSocketMessage) => void): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isConnecting) {
        reject(new Error('Connection already in progress'))
        return
      }

      this.isConnecting = true
      this.manualDisconnect = false

      try {
        this.ws = new WebSocket(`${this.url}/api/v1/session/ws/${sessionId}`)

        this.ws.onopen = () => {
          console.log('WebSocket connected')
          this.isConnecting = false
          this.reconnectAttempts = 0
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            onMessage(message)
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason)
          this.isConnecting = false
          if (!this.manualDisconnect) {
            this.handleReconnect(sessionId, onMessage)
          }
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          this.isConnecting = false
          reject(error)
        }
      } catch (error) {
        this.isConnecting = false
        reject(error)
      }
    })
  }

  private handleReconnect(sessionId: number, onMessage: (message: WebSocketMessage) => void) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
      
      setTimeout(() => {
        this.connect(sessionId, onMessage).catch(error => {
          console.error('Reconnection failed:', error)
        })
      }, this.reconnectDelay * this.reconnectAttempts)
    } else {
      console.error('Max reconnection attempts reached')
    }
  }

  sendAudioChunk(audioData: Float32Array, goal: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      // Convert Float32Array to base64
      const base64Audio = this.arrayBufferToBase64(audioData.buffer)
      
      const message = {
        type: 'audio_chunk',
        audio_data: base64Audio,
        goal: goal
      }
      
      this.ws.send(JSON.stringify(message))
    } else {
      console.error('WebSocket not connected')
    }
  }

  sendSessionComplete(audioData: Float32Array, goal: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      // Keep final payload small; backend can analyze from streamed chunk buffer.
      const maxFinalPayloadBytes = 4 * 1024 * 1024
      const shouldSendAudio = audioData.byteLength <= maxFinalPayloadBytes

      const message: Record<string, any> = {
        type: 'session_complete',
        goal: goal,
      }

      if (shouldSendAudio) {
        message.audio_data = this.arrayBufferToBase64(audioData.buffer)
      }
      
      this.ws.send(JSON.stringify(message))
    } else {
      console.error('WebSocket not connected')
    }
  }

  sendPing() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'ping' }))
    }
  }

  disconnect() {
    if (this.ws) {
      this.manualDisconnect = true
      this.ws.close()
      this.ws = null
    }
    this.reconnectAttempts = 0
    this.isConnecting = false
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }

  private arrayBufferToBase64(buffer: ArrayBufferLike): string {
    const bytes = new Uint8Array(buffer)
    let binary = ''
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i])
    }
    return btoa(binary)
  }
}

export const wsService = new WebSocketService()
