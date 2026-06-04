const BASE = '/api'

export async function startAnalysis(codeFiles, logFile) {
  const fd = new FormData()
  for (const f of codeFiles) fd.append('code_files', f)
  fd.append('log_file', logFile)

  const res = await fetch(`${BASE}/analyze`, { method: 'POST', body: fd })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }))
    throw new Error(err.detail || 'Upload failed')
  }
  return res.json()  // { analysis_id, status }
}

export async function getAnalysis(id) {
  const res = await fetch(`${BASE}/analyze/${id}`)
  if (!res.ok) throw new Error('Analysis not found')
  return res.json()
}

export function openProgressStream(id) {
  return new EventSource(`${BASE}/analyze/${id}/progress`)
}
