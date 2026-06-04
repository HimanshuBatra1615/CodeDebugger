const STYLES = {
  CRITICAL: 'bg-critical/15 text-critical border-critical/40',
  ERROR:    'bg-error/15 text-error border-error/40',
  WARNING:  'bg-warning/15 text-warning border-warning/40',
  INFO:     'bg-info/15 text-info border-info/40',
}

const DOTS = {
  CRITICAL: 'bg-critical',
  ERROR:    'bg-error',
  WARNING:  'bg-warning',
  INFO:     'bg-info',
}

export default function SeverityBadge({ severity, pulse = false }) {
  const s = (severity || 'INFO').toUpperCase()
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md border text-xs font-mono font-500 ${STYLES[s] ?? STYLES.INFO}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${DOTS[s] ?? DOTS.INFO} ${pulse && s === 'CRITICAL' ? 'animate-pulse' : ''}`} />
      {s}
    </span>
  )
}
