import { useState, useMemo } from 'react'
import SuggestionCard from './SuggestionCard'
import SeverityBadge  from './SeverityBadge'

// ── Stat pill ─────────────────────────────────────────────────────────────────

function Stat({ label, value, color }) {
  return (
    <div className="flex flex-col items-center gap-0.5">
      <span className={`text-2xl font-heading font-700 ${color}`}>{value}</span>
      <span className="text-xs text-t3 font-mono">{label}</span>
    </div>
  )
}

// ── Filter pill ───────────────────────────────────────────────────────────────

function FilterPill({ label, active, count, severity, onClick }) {
  const activeStyles = {
    ALL:      'border-accent/50 bg-accent/10 text-accent',
    CRITICAL: 'border-critical/50 bg-critical/10 text-critical',
    ERROR:    'border-error/50 bg-error/10 text-error',
    WARNING:  'border-warning/50 bg-warning/10 text-warning',
  }
  const key = severity || 'ALL'
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-lg border text-xs font-mono flex items-center gap-1.5 transition-all ${
        active ? (activeStyles[key] || activeStyles.ALL) : 'border-border text-t3 hover:border-t3 hover:text-t2'
      }`}
    >
      {label}
      <span className="opacity-70">({count})</span>
    </button>
  )
}

// ── Export utility ────────────────────────────────────────────────────────────

function exportJSON(result) {
  const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = `codedebugger-${result.analysis_id}.json`
  a.click()
  URL.revokeObjectURL(url)
}

// ── Main panel ────────────────────────────────────────────────────────────────

export default function ReportPanel({ result, onReset }) {
  const [filter, setFilter] = useState('ALL')
  const [sort,   setSort]   = useState('severity')  // 'severity' | 'confidence' | 'file'

  const suggestions = result.suggestions || []

  // Counts per severity
  const counts = useMemo(() => {
    const c = { ALL: suggestions.length, CRITICAL: 0, ERROR: 0, WARNING: 0 }
    for (const s of suggestions) c[s.severity] = (c[s.severity] || 0) + 1
    return c
  }, [suggestions])

  // Filtered + sorted list
  const displayed = useMemo(() => {
    const filtered = filter === 'ALL'
      ? [...suggestions]
      : suggestions.filter(s => s.severity === filter)

    const SEV = { CRITICAL: 0, ERROR: 1, WARNING: 2, INFO: 3 }
    if (sort === 'severity')
      return filtered.sort((a, b) => (SEV[a.severity] ?? 9) - (SEV[b.severity] ?? 9) || b.confidence - a.confidence)
    if (sort === 'confidence')
      return filtered.sort((a, b) => b.confidence - a.confidence)
    if (sort === 'file')
      return filtered.sort((a, b) => a.source_file.localeCompare(b.source_file) || a.line - b.line)
    return filtered
  }, [suggestions, filter, sort])

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 animate-fade-in">

      {/* ── Summary bar ── */}
      <div className="bg-card border border-border rounded-xl px-6 py-5 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="font-heading text-xl font-700 text-t1">Analysis complete</h2>
            <div className="text-xs text-t3 font-mono mt-0.5">
              {result.language} · {result.files_analyzed?.length ?? 0} files · ID: {result.analysis_id}
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => exportJSON(result)}
              className="px-3 py-1.5 rounded-lg border border-border text-xs font-mono text-t2 hover:text-t1 hover:border-t3 transition-colors"
            >
              ↓ export JSON
            </button>
            <button
              onClick={onReset}
              className="px-3 py-1.5 rounded-lg border border-accent/30 bg-accent/10 text-accent text-xs font-mono hover:bg-accent/20 transition-colors"
            >
              + new analysis
            </button>
          </div>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-4 divide-x divide-border">
          <Stat label="log errors"   value={result.total_log_errors} color="text-t1" />
          <Stat label="correlated"   value={result.correlated}       color="text-info" />
          <Stat label="suggestions"  value={suggestions.length}      color="text-accent" />
          <div className="flex items-center justify-center gap-3 pl-4">
            {counts.CRITICAL > 0 && <span className="text-sm font-mono text-critical">{counts.CRITICAL} critical</span>}
            {counts.ERROR    > 0 && <span className="text-sm font-mono text-error">{counts.ERROR} error</span>}
            {counts.WARNING  > 0 && <span className="text-sm font-mono text-warning">{counts.WARNING} warn</span>}
            {suggestions.length === 0 && <span className="text-sm font-mono text-success">✓ all clear</span>}
          </div>
        </div>
      </div>

      {/* ── Filter + sort bar ── */}
      {suggestions.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
          {/* Filter pills */}
          <div className="flex flex-wrap gap-2">
            <FilterPill label="All"      active={filter === 'ALL'}      count={counts.ALL}      onClick={() => setFilter('ALL')} />
            {counts.CRITICAL > 0 && <FilterPill label="Critical" active={filter === 'CRITICAL'} count={counts.CRITICAL} severity="CRITICAL" onClick={() => setFilter('CRITICAL')} />}
            {counts.ERROR    > 0 && <FilterPill label="Error"    active={filter === 'ERROR'}    count={counts.ERROR}    severity="ERROR"    onClick={() => setFilter('ERROR')} />}
            {counts.WARNING  > 0 && <FilterPill label="Warning"  active={filter === 'WARNING'}  count={counts.WARNING}  severity="WARNING"  onClick={() => setFilter('WARNING')} />}
          </div>

          {/* Sort */}
          <div className="flex items-center gap-2">
            <span className="text-t3 text-xs font-mono">sort:</span>
            {['severity', 'confidence', 'file'].map(s => (
              <button
                key={s}
                onClick={() => setSort(s)}
                className={`text-xs font-mono px-2 py-1 rounded transition-colors ${
                  sort === s ? 'text-accent' : 'text-t3 hover:text-t2'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Suggestions list ── */}
      {displayed.length === 0 ? (
        <div className="text-center py-16 text-t3 font-mono text-sm">
          {suggestions.length === 0
            ? '✓ No issues found in the uploaded files.'
            : 'No suggestions match the current filter.'}
        </div>
      ) : (
        <div className="space-y-4">
          {displayed.map((s, i) => (
            <SuggestionCard key={s.id} suggestion={s} index={i} />
          ))}
        </div>
      )}
    </div>
  )
}
