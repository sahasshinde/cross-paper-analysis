import { useEffect, useRef, useState } from 'react'
import { useLocation, Link } from 'react-router-dom'
import axios from 'axios'

const BADGE = {
  High: 'bg-green-100 text-green-800 border-green-300',
  Medium: 'bg-amber-100 text-amber-800 border-amber-300',
  Low: 'bg-slate-100 text-slate-700 border-slate-300',
}

export default function GapResults() {
  const state = useLocation().state
  const names = state?.names
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const started = useRef(false)

  useEffect(() => {
    if (!names || started.current) return
    started.current = true
    axios.post('http://localhost:8000/analysis/gaps',
      { filenames: names, threshold: state?.threshold ?? null })
      .then(res => setData(res.data))
      .catch(e => setError(e.response?.data?.detail || 'Could not build gaps. Check the backend terminal.'))
  }, [names])

  if (!names) return (
    <div className="p-6">No papers selected. <Link to="/upload" className="text-indigo-600 underline">Go to upload</Link></div>
  )

  return (
    <div className="min-h-screen bg-slate-50 p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-1">Potential Research Gaps</h2>
      <p className="text-sm text-slate-600 mb-4">
        Each gap is a recurring issue found in several papers, worded only from the
        statements that support it. Gaps are <b>candidates</b>: the system has not checked
        whether the issue is already solved elsewhere in the literature.
      </p>

      {!data && !error && <p className="text-slate-600">Building gaps and verifying evidence...</p>}
      {error && <p className="text-red-600">{error}</p>}

      {data && (
        <>
          <p className="text-xs text-slate-500 mb-4">
            {data.num_statements} statements from {data.total_papers} papers · grouping strictness{' '}
            {data.threshold} · wording: {data.wording} · model: {data.model}
          </p>

          {data.gaps.length === 0 && (
            <div className="bg-white border rounded-lg p-4">
              <p className="text-slate-700">
                No issue is shared by two or more papers at this strictness, so no potential
                gap can be supported. Lower the grouping strictness on the Recurring Issues
                page, or upload more papers on the same topic.
              </p>
              <Link to="/issues" state={{ names }} className="text-indigo-600 underline text-sm">
                Back to Recurring Issues
              </Link>
            </div>
          )}

          {data.gaps.map(g => (
            <div key={g.id} className="bg-white border rounded-lg p-5 mb-4">
              <p className="text-xs font-bold tracking-wide text-indigo-700 mb-1">
                POTENTIAL RESEARCH GAP #{g.id}
              </p>
              <h3 className="text-lg font-semibold mb-3">{g.title}</h3>

              <div className="flex flex-wrap gap-2 mb-3">
                <span className={'text-xs border rounded-full px-2 py-0.5 ' + BADGE[g.strength]}>
                  Evidence strength: {g.strength}
                </span>
                <span className="text-xs border rounded-full px-2 py-0.5 bg-slate-50">
                  Supporting papers: {g.num_papers} of {g.total_papers}
                </span>
                <span className={'text-xs border rounded-full px-2 py-0.5 ' +
                  (g.verification.status === 'Verified'
                    ? 'bg-green-50 text-green-800 border-green-300'
                    : 'bg-red-50 text-red-700 border-red-300')}>
                  {g.verification.status === 'Verified' ? '✓ ' : '! '}
                  {g.verification.status} ({g.verification.quotes_verified}/{g.verification.quotes_total} quotes found in PDFs)
                </span>
              </div>

              <p className="text-sm text-slate-700 mb-2">{g.explanation}</p>
              <p className="text-xs text-slate-500 mb-3">
                Supported by: {g.papers.join(' · ')} · wording: {g.wording}
              </p>

              <Link to="/evidence" state={{ gap: g, names }}
                className="inline-block bg-indigo-600 text-white text-sm px-4 py-2 rounded-lg">
                View Evidence
              </Link>
            </div>
          ))}

          <Link to="/issues" state={{ names }} className="text-indigo-600 underline text-sm">
            ← Back to Recurring Issues
          </Link>
        </>
      )}
    </div>
  )
}
