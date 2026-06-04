import { useState, useRef } from 'react'
import { startAnalysis } from '../api/client'

function DropZone({ label, accept, multiple, files, onFiles, icon, hint }) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef(null)

  const handle = (incoming) => {
    const arr = Array.from(incoming).filter(f =>
      accept ? accept.some(ext => f.name.endsWith(ext)) : true
    )
    if (arr.length) onFiles(multiple ? arr : [arr[0]])
  }

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={e => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={e => { e.preventDefault(); setDragging(false); handle(e.dataTransfer.files) }}
      className={`
        relative cursor-pointer rounded-xl border-2 border-dashed p-6 transition-all duration-200
        flex flex-col items-center gap-3 text-center min-h-[160px] justify-center
        ${dragging
          ? 'border-accent bg-accent/5 scale-[1.01]'
          : files.length
            ? 'border-success/50 bg-success/5'
            : 'border-border bg-surface hover:border-t3 hover:bg-surface/80'
        }
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept?.join(',')}
        multiple={multiple}
        className="hidden"
        onChange={e => handle(e.target.files)}
      />

      <div className={`text-2xl transition-transform ${dragging ? 'scale-125' : ''}`}>{icon}</div>

      {files.length === 0 ? (
        <>
          <div className="text-t1 font-medium text-sm">{label}</div>
          <div className="text-t3 text-xs font-mono">{hint}</div>
        </>
      ) : (
        <div className="w-full space-y-1.5">
          {files.map((f, i) => (
            <div key={i} className="flex items-center gap-2 text-xs">
              <span className="text-success">✓</span>
              <span className="font-mono text-t2 truncate max-w-[200px]">{f.name}</span>
              <span className="text-t3 ml-auto">{(f.size / 1024).toFixed(0)}KB</span>
            </div>
          ))}
          <button
            onClick={e => { e.stopPropagation(); onFiles([]) }}
            className="text-t3 hover:text-error text-xs mt-1 font-mono transition-colors"
          >
            clear
          </button>
        </div>
      )}
    </div>
  )
}

export default function UploadZone({ onAnalysisStart }) {
  const [codeFiles, setCodeFiles]   = useState([])
  const [logFile,   setLogFile]     = useState([])
  const [loading,   setLoading]     = useState(false)
  const [error,     setError]       = useState(null)

  const canSubmit = codeFiles.length > 0 && logFile.length > 0 && !loading

  const handleSubmit = async () => {
    if (!canSubmit) return
    setLoading(true)
    setError(null)
    try {
      const { analysis_id } = await startAnalysis(codeFiles, logFile[0])
      onAnalysisStart(analysis_id)
    } catch (e) {
      setError(e.message)
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-12 animate-fade-in">

      {/* Hero */}
      <div className="mb-10 text-center">
        <div className="inline-flex items-center gap-2 bg-accent/10 border border-accent/20 rounded-full px-3 py-1 mb-4">
          <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
          <span className="text-accent text-xs font-mono">AI-powered</span>
        </div>
        <h2 className="font-heading text-3xl font-700 text-t1 mb-2">
          Upload code &amp; logs
        </h2>
        <p className="text-t2 text-sm max-w-sm mx-auto">
          Drop your source files and error log. The pipeline parses stack traces,
          correlates them to your code, then generates precise fixes.
        </p>
      </div>

      {/* Drop zones */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <DropZone
          label="Source code"
          hint=".java .py .js .ts .go or a .zip"
          accept={['.java', '.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.cs', '.cpp', '.rs', '.kt', '.zip']}
          multiple
          files={codeFiles}
          onFiles={setCodeFiles}
          icon="📁"
        />
        <DropZone
          label="Log file"
          hint=".log or .txt"
          accept={['.log', '.txt', '.out']}
          multiple={false}
          files={logFile}
          onFiles={setLogFile}
          icon="📋"
        />
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 px-4 py-3 rounded-lg bg-critical/10 border border-critical/30 text-critical text-sm font-mono">
          ✕ {error}
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={!canSubmit}
        className={`
          w-full py-3.5 rounded-xl font-heading font-700 text-sm tracking-wide transition-all duration-200
          ${canSubmit
            ? 'bg-accent text-bg hover:bg-accent/90 hover:scale-[1.01] shadow-lg shadow-accent/20'
            : 'bg-surface text-t3 cursor-not-allowed border border-border'
          }
        `}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="w-4 h-4 border-2 border-bg/30 border-t-bg rounded-full animate-spin" />
            Starting analysis…
          </span>
        ) : (
          'Analyse →'
        )}
      </button>

      {/* Info strip */}
      <div className="mt-6 flex flex-wrap justify-center gap-4 text-xs text-t3 font-mono">
        {['Java', 'Python', 'Node.js', 'Go', 'C#', 'Kotlin'].map(lang => (
          <span key={lang} className="flex items-center gap-1">
            <span className="text-accent/60">▸</span>{lang}
          </span>
        ))}
      </div>
    </div>
  )
}
