import { useEffect, useRef } from 'react'
import { useProgressStream } from '../hooks/useProgressStream'

const STEPS = [
  { key: 'parsing',     label: 'Parse log file',     desc: 'Extracting errors, stack traces, line numbers' },
  { key: 'indexing',    label: 'Index source code',  desc: 'Language detection, file structure' },
  { key: 'correlating', label: 'Correlate errors',   desc: 'Mapping log frames → source lines' },
  { key: 'analyzing',   label: 'AI analysis',        desc: 'Structured prompt → Gemini API' },
]

const STEP_ORDER = STEPS.map(s => s.key)

function stepStatus(stepKey, currentStep, events) {
  const currentIdx = STEP_ORDER.indexOf(currentStep)
  const stepIdx    = STEP_ORDER.indexOf(stepKey)
  if (stepIdx < 0) return 'pending'
  if (stepIdx < currentIdx) return 'done'
  if (stepIdx === currentIdx) return 'active'
  return 'pending'
}

function lastMessageFor(stepKey, events) {
  const matches = events.filter(e => e.step === stepKey)
  return matches.length ? matches[matches.length - 1].message : null
}

function StepIcon({ status }) {
  if (status === 'done')
    return <span className="text-success text-sm">✓</span>
  if (status === 'active')
    return (
      <span className="w-4 h-4 border-2 border-accent/30 border-t-accent rounded-full animate-spin block" />
    )
  return <span className="w-1.5 h-1.5 rounded-full bg-t3 block mx-auto" />
}

export default function AnalysisProgress({ analysisId, onComplete }) {
  const { events, currentStep, isDone, error } = useProgressStream(analysisId, onComplete)
  const logRef = useRef(null)

  // Auto-scroll terminal log
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [events])

  return (
    <div className="max-w-xl mx-auto px-6 py-12 animate-fade-in">

      {/* Header */}
      <div className="text-center mb-10">
        <div className="w-12 h-12 rounded-xl bg-accent/10 border border-accent/20 flex items-center justify-center mx-auto mb-4">
          <span className="text-accent text-xl font-mono animate-pulse-slow">⚙</span>
        </div>
        <h2 className="font-heading text-2xl font-700 text-t1 mb-1">Analysing…</h2>
        <p className="text-t3 text-xs font-mono">ID: {analysisId}</p>
      </div>

      {/* Pipeline steps */}
      <div className="bg-card border border-border rounded-xl overflow-hidden mb-4">
        {STEPS.map((step, i) => {
          const status  = stepStatus(step.key, currentStep, events)
          const msg     = lastMessageFor(step.key, events)
          const isLast  = i === STEPS.length - 1
          return (
            <div
              key={step.key}
              className={`flex items-start gap-4 px-4 py-3.5 ${!isLast ? 'border-b border-border' : ''} transition-colors duration-300 ${status === 'active' ? 'bg-accent/5' : ''}`}
            >
              {/* Icon column */}
              <div className="w-5 flex-shrink-0 flex items-center justify-center pt-0.5">
                <StepIcon status={status} />
              </div>

              {/* Text column */}
              <div className="flex-1 min-w-0">
                <div className={`text-sm font-medium transition-colors ${status === 'done' ? 'text-t2' : status === 'active' ? 'text-t1' : 'text-t3'}`}>
                  {step.label}
                </div>
                <div className="text-xs text-t3 font-mono mt-0.5">
                  {msg || step.desc}
                </div>
              </div>

              {/* Step number */}
              <div className="text-xs text-t3 font-mono flex-shrink-0 pt-0.5">
                {String(i + 1).padStart(2, '0')}
              </div>
            </div>
          )
        })}
      </div>

      {/* Terminal log */}
      {events.length > 0 && (
        <div
          ref={logRef}
          className="bg-bg border border-border rounded-xl p-3 h-36 overflow-y-auto font-mono text-xs space-y-1"
        >
          {events.map((e, i) => (
            <div key={i} className="flex gap-2 items-start">
              <span className="text-t3 flex-shrink-0">{'>'}</span>
              <span className={`${e.count !== undefined ? 'text-success' : 'text-t2'}`}>
                {e.message}
                {e.count !== undefined && (
                  <span className="text-accent ml-2">[{e.count}]</span>
                )}
              </span>
            </div>
          ))}
          {!isDone && (
            <div className="flex gap-2 items-center text-accent">
              <span>{'>'}</span>
              <span className="animate-pulse">_</span>
            </div>
          )}
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="mt-4 px-4 py-3 rounded-lg bg-critical/10 border border-critical/30 text-critical text-sm font-mono">
          ✕ {error}
        </div>
      )}
    </div>
  )
}
