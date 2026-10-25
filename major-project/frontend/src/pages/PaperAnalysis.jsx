import { useEffect, useRef, useState } from 'react'
import { useLocation, Link } from 'react-router-dom'
import axios from 'axios'

const LABELS = {
  problem: 'Research Problem',
  objective: 'Research Objective',
  methodology: 'Methodology',
  dataset: 'Dataset',
  results: 'Results',
  limitations: 'Limitations',
  future_work: 'Future Work',
}

export default function PaperAnalysis() {
  const names = useLocation().state?.names
  const [papers, setPapers] = useState(null)
  const [error, setError] = useState('')
  const started = useRef(false)   // stops React dev mode from calling the API twice

  useEffect(() => {
    if (!names || started.current) return
    started.current = true
    axios.post('http://localhost:8000/analysis/aspects', { filenames: names })
      .then(res => setPapers(res.data.papers))
      .catch(e => setError(e.response?.data?.detail || 'Analysis failed. Check the backend terminal.'))
  }, [names])

  if (!names) return (
    <div className="p-6">No papers selected. <Link to="/upload" className="text-indigo-600 underline">Go to upload</Link></div>
  )

  return (
    <div className="min-h-screen bg-slate-50 p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Paper Analysis</h2>

      {papers && (
        <Link to="/compare" state={{ names }}
          className="inline-block bg-indigo-600 text-white px-5 py-2 rounded-lg mb-6">
          Compare across papers →
        </Link>
      )}

      {!papers && !error && (
        <p className="text-slate-600">
          Analyzing {names.length} papers... The first run downloads the language
          model (a few minutes). Please keep this tab open.
        </p>
      )}
      {error && <p className="text-red-600">{error}</p>}

      {papers?.map(p => (
        <div key={p.name} className="bg-white border rounded-lg p-5 mb-6">
          <h3 className="text-lg font-semibold">{p.name}</h3>
          <p className="text-xs text-slate-500 mb-3">
            {p.num_pages} pages · {p.num_sentences} sentences analysed
          </p>
          {p.warning && <p className="text-amber-600 text-sm mb-2">{p.warning}</p>}

          {Object.keys(LABELS).map(key => (
            <div key={key} className="mb-4">
              <h4 className="font-semibold text-indigo-700">
                {LABELS[key]} <span className="text-slate-400 font-normal">({p.aspects[key].length})</span>
              </h4>
              {p.aspects[key].length === 0 && <p className="text-sm text-slate-400">Nothing confident found.</p>}
              {p.aspects[key].map((s, i) => (
                <p key={i} className="text-sm text-slate-700 border-l-4 border-indigo-200 pl-3 my-1">
                  {s.text} <span className="text-xs text-slate-400">[p.{s.page} · score {s.score}]</span>
                </p>
              ))}
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}
