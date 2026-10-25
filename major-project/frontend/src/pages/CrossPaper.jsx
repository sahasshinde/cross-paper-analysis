import { useEffect, useRef, useState } from 'react'
import { useLocation, Link } from 'react-router-dom'
import axios from 'axios'

// Each tab compares ONE aspect across papers (like with like).
const ASPECTS = [
  ['problem', 'Research Problem'],
  ['objective', 'Research Objective'],
  ['methodology', 'Methodology'],
  ['dataset', 'Dataset'],
  ['results', 'Results'],
  ['limitations', 'Limitations'],
  ['future_work', 'Future Work'],
]
const GAP = ['limitations', 'future_work']   // recurring issues matter most here
const FACT_LABELS = ['Source', 'Size', 'Split / validation', 'Class imbalance', 'Missing values']

function Statement({ s }) {
  return (
    <div className="flex-1 bg-slate-50 border rounded p-3">
      <p className="text-xs text-slate-500 mb-1">
        <span className="font-semibold text-slate-700">{s.paper}</span> · page {s.page}
      </p>
      <p className="text-sm text-slate-800">{s.text}</p>
    </div>
  )
}

function PairCard({ p, dashed }) {
  return (
    <div className={'bg-white border rounded-lg p-4 mb-3 ' + (dashed ? 'border-dashed' : '')}>
      <p className="text-sm font-semibold mb-2">Similarity {(p.similarity * 100).toFixed(0)}%</p>
      <div className="flex flex-col md:flex-row gap-3">
        <Statement s={p.a} />
        <Statement s={p.b} />
      </div>
    </div>
  )
}

// Dataset facts table: papers can use completely different data, and the
// comparison should still show WHAT each one uses.
function FactsTable({ facts }) {
  return (
    <div className="bg-white border rounded-lg p-4 mb-4 overflow-x-auto">
      <p className="text-sm font-semibold mb-2">Dataset at a glance</p>
      <table className="text-sm min-w-full">
        <thead>
          <tr className="text-left text-slate-500">
            <th className="pr-4 py-1"></th>
            {facts.map(f => <th key={f.name} className="pr-4 py-1">{f.name}</th>)}
          </tr>
        </thead>
        <tbody>
          {FACT_LABELS.map(label => (
            <tr key={label} className="border-t align-top">
              <td className="pr-4 py-2 font-semibold text-slate-700 whitespace-nowrap">{label}</td>
              {facts.map(f => {
                const x = f.facts.find(y => y.label === label)
                return (
                  <td key={f.name} className="pr-4 py-2" title={x ? x.text : ''}>
                    {x ? <>{x.value} <span className="text-xs text-slate-400">[p.{x.page}]</span></>
                       : <span className="text-slate-400">not stated</span>}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-xs text-slate-400 mt-2">Hover a value to see the sentence it came from.</p>
    </div>
  )
}

function SideBySide({ names, statements }) {
  return (
    <div className="mb-4">
      <p className="text-sm font-semibold mb-2">What each paper says</p>
      <div className="flex gap-3 overflow-x-auto pb-2">
        {names.map(n => {
          const mine = statements.filter(s => s.paper === n)
          return (
            <div key={n} className="min-w-[260px] flex-1 bg-white border rounded-lg p-3">
              <p className="text-sm font-semibold text-indigo-700 mb-2">{n}</p>
              {mine.length === 0 && <p className="text-sm text-slate-400">Nothing confident found.</p>}
              {mine.map((s, i) => (
                <p key={i} className="text-sm text-slate-700 mb-2">
                  {s.text} <span className="text-xs text-slate-400">[p.{s.page}]</span>
                </p>
              ))}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function CrossPaper() {
  const names = useLocation().state?.names
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [custom, setCustom] = useState({})   // slider values the user changed, per aspect
  const [tab, setTab] = useState('dataset')
  const started = useRef(false)

  useEffect(() => {
    if (!names || started.current) return
    started.current = true
    axios.post('http://localhost:8000/analysis/compare', { filenames: names })
      .then(res => setData(res.data))
      .catch(e => setError(e.response?.data?.detail || 'Comparison failed. Check the backend terminal.'))
  }, [names])

  if (!names) return (
    <div className="p-6">No papers selected. <Link to="/upload" className="text-indigo-600 underline">Go to upload</Link></div>
  )

  // each aspect starts at its own suggested level (typical similarity + margin)
  const levelOf = key => custom[key] ?? data.aspects[key].default_threshold
  const current = data?.aspects[tab]
  const threshold = data ? levelOf(tab) : 0.5
  const shown = current ? current.pairs.filter(p => p.similarity >= threshold) : []
  const closest = current && shown.length === 0
    ? current.pairs.filter(p => p.similarity < threshold).slice(0, 2) : []
  const countAbove = key => data.aspects[key].pairs.filter(p => p.similarity >= levelOf(key)).length
  const isGap = GAP.includes(tab)
  const label = ASPECTS.find(a => a[0] === tab)[1]

  return (
    <div className="min-h-screen bg-slate-50 p-6 max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold mb-1">Cross-Paper Comparison</h2>
      <p className="text-sm text-slate-600 mb-4">
        Papers are compared <b>like with like</b>: datasets with datasets, limitations with
        limitations, and so on. Descriptive aspects are shown side by side; limitations and
        future work are matched to find issues repeated by <b>different</b> papers.
      </p>

      {!data && !error && <p className="text-slate-600">Comparing {names.length} papers aspect by aspect...</p>}
      {error && <p className="text-red-600">{error}</p>}

      {data && (
        <>
          <Link to="/issues" state={{ names }}
            className="inline-block bg-indigo-600 text-white px-5 py-2 rounded-lg mb-4">
            Find recurring issues →
          </Link>

          <div className="flex flex-wrap gap-2 mb-4">
            {ASPECTS.map(([key, lab]) => (
              <button key={key} onClick={() => setTab(key)}
                className={'px-3 py-1 rounded-full text-sm border ' +
                  (tab === key ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-slate-700')}>
                {lab}{GAP.includes(key) ? ` (${countAbove(key)} matches)` : ''}
              </button>
            ))}
          </div>

          {tab === 'dataset' && <FactsTable facts={data.dataset_facts} />}
          {!isGap && <SideBySide names={data.papers} statements={current.statements} />}

          <div className="bg-white border rounded-lg p-4 mb-4">
            <p className="text-sm font-semibold mb-1">
              {isGap ? `Recurring ${label.toLowerCase()} across papers` : 'Statements that say similar things'}
            </p>
            <label className="text-sm">Minimum similarity: {threshold.toFixed(2)}</label>
            <input type="range" min="0.3" max="0.9" step="0.01" value={threshold}
              onChange={e => setCustom({ ...custom, [tab]: Number(e.target.value) })} className="w-full" />
            <p className="text-sm text-slate-600">
              {shown.length} similar pair(s). Each statement appears at most once per pair of papers.
            </p>
            <p className="text-xs text-slate-500 mt-2">
              Statements compared per paper: {current.counts.map(c => `${c.name} (${c.n})`).join(' · ')}
            </p>
            {current.baseline !== null && (
              <p className="text-xs text-slate-500">
                Typical similarity between any two papers for this aspect: {current.baseline.toFixed(2)}.
                The slider starts at this value plus a margin.
              </p>
            )}
            <p className="text-xs text-slate-400 mt-1">Embedding model: {data.model}</p>
          </div>

          {shown.length === 0 && (
            <div className="mb-4">
              <p className="text-slate-600 mb-2">
                {isGap
                  ? `No pairs reach ${threshold.toFixed(2)}. The papers may simply not share a ${label.toLowerCase()} statement.`
                  : 'No strongly matching statements, so the papers describe this differently. See the comparison above.'}
              </p>
              {closest.length > 0 && (
                <>
                  <p className="text-sm font-semibold text-slate-700 mb-2">
                    Closest matches below your level (check them yourself):
                  </p>
                  {closest.map((p, i) => <PairCard key={i} p={p} dashed />)}
                </>
              )}
              {closest.length === 0 && (
                <p className="text-sm text-slate-500">No two statements reached even 0.30.</p>
              )}
            </div>
          )}

          {shown.map((p, i) => <PairCard key={i} p={p} />)}

          {isGap && (
            <details className="bg-white border rounded-lg p-3 mb-4">
              <summary className="text-sm font-semibold cursor-pointer">
                Show all {current.statements.length} statements compared for this aspect
              </summary>
              {current.statements.map((s, i) => (
                <p key={i} className="text-sm text-slate-700 mt-2">
                  <span className="text-xs text-slate-500">{s.paper} · p.{s.page}:</span> {s.text}
                </p>
              ))}
            </details>
          )}
        </>
      )}
    </div>
  )
}
