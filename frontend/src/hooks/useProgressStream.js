import { useState, useEffect, useRef } from 'react'
import { openProgressStream } from '../api/client'

/**
 * Subscribe to a Server-Sent Events stream for a given analysis ID.
 * Returns { events, currentStep, isDone, error }.
 */
export function useProgressStream(analysisId, onComplete) {
  const [events, setEvents]       = useState([])
  const [currentStep, setStep]    = useState('connecting')
  const [isDone, setDone]         = useState(false)
  const [error, setError]         = useState(null)
  const esRef                     = useRef(null)

  useEffect(() => {
    if (!analysisId) return

    const es = openProgressStream(analysisId)
    esRef.current = es

    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.type === 'heartbeat') return

        if (data.type === 'progress') {
          setEvents(prev => [...prev, data])
          setStep(data.step)
        }

        if (data.type === 'complete') {
          setDone(true)
          onComplete?.(data.result)
          es.close()
        }

        if (data.type === 'error') {
          setError(data.message)
          setDone(true)
          es.close()
        }
      } catch (_) { /* ignore malformed events */ }
    }

    es.onerror = () => {
      setError('Connection to analysis stream lost.')
      setDone(true)
      es.close()
    }

    return () => es.close()
  }, [analysisId])  // eslint-disable-line react-hooks/exhaustive-deps

  return { events, currentStep, isDone, error }
}
