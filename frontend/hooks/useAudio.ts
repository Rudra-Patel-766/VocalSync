'use client'

import { useState, useRef, useCallback } from 'react'

type AudioChunkHandler = (chunk: Float32Array) => void

export interface AudioState {
  isRecording: boolean
  isPaused: boolean
  volume: number
  duration: number
  audioData: Float32Array | null
}

export function useAudio(onAudioChunk?: AudioChunkHandler) {
  const [audioState, setAudioState] = useState<AudioState>({
    isRecording: false,
    isPaused: false,
    volume: 0,
    duration: 0,
    audioData: null,
  })

  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)
  const silenceGainRef = useRef<GainNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const audioChunksRef = useRef<Float32Array[]>([])
  const animationFrameRef = useRef<number | null>(null)
  const startTimeRef = useRef<number>(0)
  const recordingRef = useRef(false)
  const pausedRef = useRef(false)
  const onAudioChunkRef = useRef<AudioChunkHandler | undefined>(onAudioChunk)

  onAudioChunkRef.current = onAudioChunk

  const startVolumeMonitoring = useCallback(() => {
    const updateVolume = () => {
      if (analyserRef.current && recordingRef.current) {
        const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
        analyserRef.current.getByteFrequencyData(dataArray)

        const average = dataArray.reduce((acc, val) => acc + val, 0) / dataArray.length
        const volume = average / 255
        const duration = (Date.now() - startTimeRef.current) / 1000

        setAudioState((prev) => ({
          ...prev,
          volume,
          duration,
        }))

        animationFrameRef.current = requestAnimationFrame(updateVolume)
      }
    }

    updateVolume()
  }, [])

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000,
        },
      })

      streamRef.current = stream
      audioContextRef.current = new AudioContext({ sampleRate: 16000 })
      analyserRef.current = audioContextRef.current.createAnalyser()
      analyserRef.current.fftSize = 2048

      sourceRef.current = audioContextRef.current.createMediaStreamSource(stream)
      processorRef.current = audioContextRef.current.createScriptProcessor(4096, 1, 1)
      silenceGainRef.current = audioContextRef.current.createGain()
      silenceGainRef.current.gain.value = 0

      sourceRef.current.connect(analyserRef.current)
      analyserRef.current.connect(processorRef.current)
      processorRef.current.connect(silenceGainRef.current)
      silenceGainRef.current.connect(audioContextRef.current.destination)

      audioChunksRef.current = []
      startTimeRef.current = Date.now()

      processorRef.current.onaudioprocess = (event) => {
        if (!recordingRef.current || pausedRef.current) {
          return
        }

        const inputData = event.inputBuffer.getChannelData(0)
        const chunk = new Float32Array(inputData)
        audioChunksRef.current.push(chunk)
        onAudioChunkRef.current?.(chunk)
      }

      recordingRef.current = true
      pausedRef.current = false

      setAudioState({
        isRecording: true,
        isPaused: false,
        volume: 0,
        duration: 0,
        audioData: null,
      })

      startVolumeMonitoring()
    } catch (error) {
      console.error('Error starting recording:', error)
      throw error
    }
  }, [startVolumeMonitoring])

  const stopRecording = useCallback(async () => {
    recordingRef.current = false
    pausedRef.current = false

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }

    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current.onaudioprocess = null
      processorRef.current = null
    }

    if (analyserRef.current) {
      analyserRef.current.disconnect()
    }

    if (sourceRef.current) {
      sourceRef.current.disconnect()
      sourceRef.current = null
    }

    if (silenceGainRef.current) {
      silenceGainRef.current.disconnect()
      silenceGainRef.current = null
    }

    if (audioContextRef.current) {
      await audioContextRef.current.close()
      audioContextRef.current = null
    }

    const totalLength = audioChunksRef.current.reduce(
      (acc, chunk) => acc + chunk.length,
      0
    )
    const combinedAudio = new Float32Array(totalLength)
    let offset = 0

    audioChunksRef.current.forEach((chunk) => {
      combinedAudio.set(chunk, offset)
      offset += chunk.length
    })

    setAudioState((prev) => ({
      ...prev,
      isRecording: false,
      isPaused: false,
      audioData: combinedAudio,
    }))

    return combinedAudio
  }, [])

  const pauseRecording = useCallback(() => {
    if (audioContextRef.current && recordingRef.current && !pausedRef.current) {
      pausedRef.current = true
      audioContextRef.current.suspend()
      setAudioState((prev) => ({ ...prev, isPaused: true }))
    }
  }, [])

  const resumeRecording = useCallback(() => {
    if (audioContextRef.current && recordingRef.current && pausedRef.current) {
      pausedRef.current = false
      audioContextRef.current.resume()
      setAudioState((prev) => ({ ...prev, isPaused: false }))
    }
  }, [])

  const getAudioData = useCallback(() => {
    return audioState.audioData
  }, [audioState.audioData])

  const clearAudioData = useCallback(() => {
    audioChunksRef.current = []
    setAudioState((prev) => ({ ...prev, audioData: null }))
  }, [])

  return {
    audioState,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    getAudioData,
    clearAudioData,
  }
}
