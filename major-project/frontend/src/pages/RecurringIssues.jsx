import { useEffect, useRef, useState } from 'react'
import { useLocation, Link } from 'react-router-dom'
import axios from 'axios'

const KIND = { limitations: 'Limitation', future_work: 'Future work' }
const BADGE = {
  High: 'bg-green-100 text-green-800 border-green-300',
  Medium: 'bg-amber-100 text-amber-800 border-amber-300',
  Low: 'bg-slate-100 text-slate-700 border-slate-300',
}

function StatementList({ statements }) {
  return statements.map((s, i) => (
    <div key={i} className="bg-slate-50 border rounded p-3 mt-2">
      <p className="text-xs text-slate-500 mb-1">
        <span className="font-semibold text-slate-700">{s.paper}</span> · page {s.page} ·{' '}
        <span className="text-indigo-600">{KIND[s.kind]}</span>
      </p>
      <p className="text-sm text-slate-800">{s.text}</p>
    </div>
  ))
}

export default function RecurringIssues() {
  const names = useLocation().state?.names
  const [data, setData] = useState(null)
  const [value, setValue] = useState(null)      // slider position (applied on release)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const started = useRef(false)

  const load = (threshold) => {
    setLoading(true); setError('')
    axios.post('http://localhost:8000/analysis/clusters', { filenames: names, threshold })
      .then(res => { setData(res.data); setValue(res.data.threshold) })
      .catch(e => setError(e.response?.data?.detail || 'Grouping failed. Check the backend terminal.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!names || started.current) return
    started.current = true
    load(null)                                   // null = automatic strictness
  }, [names])

  if (!names) return (
    <div className="p-6">No papers selected. <Link to="/upload" className="text-indigo-600 underline">Go to upload</Link></div>
  )

  return (
    <div className="min-h-screen bg-slate-50 p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-1">Recurring Issues</h2>
      <p className="text-sm text-slate-600 mb-4">
        Limitation and future-work statements from all papers are grouped by meaning.
        A group supported by at least <b>2 different papers</b> is a recurring issue.
        Limitations and future work are pooled on purpose: what one paper lists as a
        limitation, another often lists as future work.
      </p>

      {!data && !error && <p className="text-slate-600">Grouping statements from {names.length} papers...</p>}
      {error && <p className="text-red-600">{error}</p>}

      {data && (
        <>
          <Link to="/gaps" state={{ names, threshold: value }}
            className="inline-block bg-indigo-600 text-white px-5 py-2 rounded-lg mb-4">
            Generate potential research gaps →
          </Link>

          <div className="bg-white border rounded-lg p-4 mb-4">
            <p className="text-sm text-slate-700">
              {data.num_statements} statements from {data.total_papers} papers →{' '}
              <b>{data.recurring.length}</b> recurring issue(s)
              {loading && <span className="text-slate-400"> (updating...)</span>}
            </p>
            <label className="text-sm font-semibold block mt-3">
              Grouping strictness: {value?.toFixed(2)}
            </label>
            <input type="range" min="0.3" max="0.9" step="0.01" value={value ?? 0.5}
              onChange={e => setValue(Number(e.target.value))}
              onPointerUp={() => load(value)}
              onKeyUp={() => load(value)}
              className="w-full" />
            <p className="text-xs text-slate-500">
              Higher = only near-identical statements are grouped. Lower = broader groups.
              Automatic level: {data.default_threshold}
              {data.baseline !== null && ` (typical similarity between papers: ${data.baseline})`}.
            </p>
            <p className="text-xs text-slate-400 mt-1">Embedding model: {data.model}</p>
          </div>

          {data.recurring.length === 0 && (
            <p className="text-slate-600 mb-4">
              No issue is shared by two or more papers at this strictness. Lower the slider,
              or add more papers on the same topic.
            </p>
          )}

          {data.recurring.map(c => (
            <div key={c.id} className="bg-white border rounded-lg p-4 mb-4">
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <h3 className="font-semibold">Recurring issue #{c.id}</h3>
                <span className={'text-xs border rounded-full px-2 py-0.5 ' + BADGE[c.strength]}>
                  Evidence: {c.strength}
                </span>
                <span className="text-xs text-slate-500">
                  {c.num_papers} of {data.total_papers} papers
                </span>
              </div>

              <div className="flex flex-wrap gap-1 mb-3">
                {c.key_terms.map(t => (
                  <span key={t} className="text-xs bg-indigo-50 text-indigo-700 rounded px-2 py-0.5">{t}</span>
                ))}
              </div>

              <p className="text-xs text-slate-500">Most representative statement</p>
              <blockquote className="border-l-4 border-indigo-300 pl-3 text-sm text-slate-800 mb-2">
                {c.representative.text}
                <span className="block text-xs text-slate-500 mt-1">
                  {c.representative.paper} · page {c.representative.page}
                </span>
              </blockquote>

              <p className="text-xs text-slate-500">Supported by: {c.papers.join(' · ')}</p>
              <details className="mt-2">
                <summary className="text-sm font-semibold cursor-pointer text-indigo-700">
                  View all {c.statements.length} statements
                </summary>
                <StatementList statements={c.statements} />
              </details>
            </div>
          ))}

          {data.single_paper.length > 0 && (
            <details className="bg-white border rounded-lg p-3 mb-4">
              <summary className="text-sm font-semibold cursor-pointer">
                Issues raised by only one paper ({data.single_paper.length})
              </summary>
              <StatementList statements={data.single_paper.flatMap(c => c.statements)} />
            </details>
          )}

          <p className="text-xs text-slate-400">
            These are candidates only. The next stage words each recurring issue as a
            potential research gap and links it to its evidence. Nothing here claims
            that an issue is novel.
          </p>
        </>
      )}
    </div>
  )
}
