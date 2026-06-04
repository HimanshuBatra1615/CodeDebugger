export default function Header({ onReset, showReset }) {
  return (
    <header className="border-b border-border px-6 py-4 flex items-center justify-between">
      <div className="flex items-center gap-3">
        {/* Logo mark */}
        <div className="w-8 h-8 rounded-lg bg-accent/10 border border-accent/30 flex items-center justify-center">
          <span className="text-accent font-mono text-xs font-semibold">CD</span>
        </div>
        <div>
          <h1 className="font-heading text-lg font-700 text-t1 leading-none">CodeDebugger</h1>
          <p className="text-t3 text-xs font-mono mt-0.5">AI-powered error analysis</p>
        </div>
      </div>

      {showReset && (
        <button
          onClick={onReset}
          className="text-xs text-t2 hover:text-t1 border border-border hover:border-t3 rounded-lg px-3 py-1.5 transition-colors font-mono"
        >
          ← new analysis
        </button>
      )}
    </header>
  )
}
