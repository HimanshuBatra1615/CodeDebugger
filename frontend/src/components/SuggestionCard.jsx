import { useState } from 'react'
import SeverityBadge from './SeverityBadge'

// ── Code renderers ────────────────────────────────────────────────────────────

function ContextBlock({ context }) {
  const lines = (context || '').split('\n')
  return (
    <div className="font-mono text-xs overflow-x-auto rounded-lg bg-bg border border-border">
      {lines.map((line, i) => {
        const isError = /^\s*\d+\s+→/.test(line)
        return (
          <div
            key={i}
            className={`px-3 py-0.5 whitespace-pre leading-5 ${
              isError
                ? 'bg-critical/10 border-l-2 border-critical text-red-200'
                : 'text-t2 hover:bg-white/[0.02]'
            }`}
          >
            {line}
          </div>
        )
      })}
    </div>
  )
}

function FixedBlock({ code }) {
  if (!code) return (
    <div className="font-mono text-xs text-t3 italic px-3 py-2">
      No fix snippet provided.
    </div>
  )
  const lines = code.split('\n')
  return (
    <div className="font-mono text-xs overflow-x-auto rounded-lg bg-bg border border-success/30">
      {lines.map((line, i) => (
        <div
          key={i}
          className="px-3 py-0.5 whitespace-pre leading-5 text-green-300 bg-green-950/20 border-l-2 border-success"
        >
          {line}
        </div>
      ))}
    </div>
  )
}

// ── Confidence bar ────────────────────────────────────────────────────────────

function ConfidenceBar({ value }) {
  const pct = Math.round((value || 0) * 100)
  const color = pct >= 80 ? 'bg-success' : pct >= 55 ? 'bg-warning' : 'bg-error'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 bg-border rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-t3 w-8 text-right">{pct}%</span>
    </div>
  )
}

// ── Copy button ───────────────────────────────────────────────────────────────

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1800)
  }
  return (
    <button
      onClick={copy}
      className="text-xs font-mono px-2 py-1 rounded border border-border text-t3 hover:text-t1 hover:border-t2 transition-colors"
    >
      {copied ? '✓ copied' : 'copy fix'}
    </button>
  )
}

// ── Main card ─────────────────────────────────────────────────────────────────

export default function SuggestionCard({ suggestion, index }) {
  const [expanded, setExpanded] = useState(false)
  const [diffTab, setDiffTab]   = useState('context')   // 'context' | 'fix'

  const {
    severity, error_type, source_file, line, method,
    root_cause, suggestion: sugText, fixed_code,
    confidence, original_context,
  } = suggestion

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden animate-slide-up"
         style={{ animationDelay: `${index * 60}ms`, animationFillMode: 'backwards' }}>

      {/* ── Header row ── */}
      <div className="px-4 py-3 flex items-start gap-3 flex-wrap">
        <SeverityBadge severity={severity} pulse />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-t1 text-sm font-medium">{error_type}</span>
            {method && (
              <span className="text-t3 font-mono text-xs">{method}()</span>
            )}
          </div>
          <div className="flex items-center gap-1 mt-0.5 font-mono text-xs text-t3">
            <span>{source_file}</span>
            <span className="text-border">:</span>
            <span className="text-accent">{line}</span>
          </div>
        </div>

        {/* Confidence */}
        <div className="w-28 flex-shrink-0 flex flex-col gap-1 justify-center">
          <span className="text-xs text-t3 font-mono">confidence</span>
          <ConfidenceBar value={confidence} />
        </div>
      </div>

      {/* ── Root cause ── */}
      <div className="px-4 pb-3 border-t border-border/50 pt-3">
        <p className="text-xs text-t3 uppercase font-mono tracking-wider mb-1">Root cause</p>
        <p className="text-sm text-t1">{root_cause}</p>
      </div>

      {/* ── Suggestion ── */}
      <div className="px-4 pb-3">
        <p className="text-xs text-t3 uppercase font-mono tracking-wider mb-1">Fix</p>
        <p className="text-sm text-t2">{sugText}</p>
      </div>

      {/* ── Expand toggle ── */}
      <div className="border-t border-border">
        <button
          onClick={() => setExpanded(e => !e)}
          className="w-full flex items-center justify-between px-4 py-2.5 text-xs font-mono text-t3 hover:text-t2 hover:bg-white/[0.02] transition-colors"
        >
          <span>{expanded ? '▲ hide code' : '▼ show code diff'}</span>
          {fixed_code && <CopyButton text={fixed_code} />}
        </button>
      </div>

      {/* ── Code diff ── */}
      {expanded && (
        <div className="px-4 pb-4 animate-fade-in">
          {/* Tabs */}
          <div className="flex gap-1 mb-3">
            {[
              { id: 'context', label: '⚠ original context' },
              { id: 'fix',     label: '✓ suggested fix' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setDiffTab(tab.id)}
                className={`px-3 py-1 rounded-lg text-xs font-mono transition-colors ${
                  diffTab === tab.id
                    ? tab.id === 'fix'
                      ? 'bg-success/15 text-success border border-success/30'
                      : 'bg-critical/15 text-critical border border-critical/30'
                    : 'text-t3 border border-border hover:border-t3'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {diffTab === 'context'
            ? <ContextBlock context={original_context} />
            : <FixedBlock   code={fixed_code} />
          }
        </div>
      )}
    </div>
  )
}
