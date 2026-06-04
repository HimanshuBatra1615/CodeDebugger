import { useState } from 'react'
import Header           from './components/Header'
import UploadZone       from './components/UploadZone'
import AnalysisProgress from './components/AnalysisProgress'
import ReportPanel      from './components/ReportPanel'

// Stage: 'upload' | 'analyzing' | 'results'

export default function App() {
  const [stage,      setStage]      = useState('upload')
  const [analysisId, setAnalysisId] = useState(null)
  const [result,     setResult]     = useState(null)

  const handleAnalysisStart = (id) => {
    setAnalysisId(id)
    setStage('analyzing')
  }

  const handleComplete = (data) => {
    setResult(data)
    setStage('results')
  }

  const handleReset = () => {
    setStage('upload')
    setAnalysisId(null)
    setResult(null)
  }

  return (
    <div className="min-h-screen flex flex-col bg-bg">
      <Header
        showReset={stage !== 'upload'}
        onReset={handleReset}
      />

      <main className="flex-1 overflow-y-auto">
        {stage === 'upload' && (
          <UploadZone onAnalysisStart={handleAnalysisStart} />
        )}

        {stage === 'analyzing' && (
          <AnalysisProgress
            analysisId={analysisId}
            onComplete={handleComplete}
          />
        )}

        {stage === 'results' && result && (
          <ReportPanel
            result={result}
            onReset={handleReset}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-border px-6 py-3 flex items-center justify-between">
        <span className="text-t3 text-xs font-mono">
          CodeDebugger v1.0 
        </span>
        <span className="text-t3 text-xs font-mono">
        </span>
      </footer>
    </div>
  )
}
