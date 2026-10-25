import { useLocation, Link } from 'react-router-dom'

const KIND = { limitations: 'Limitation', future_work: 'Future work' }

export default function Evidence() {
  const { state } = useLocation()
  const g = state?.gap
  if (!g) return (
    <div className="p-6">
      No gap selected. <Link to="/upload" className="text-indigo-600 underline">Start again</Link>
    </div>
  )
  const v = g.verification

  return (
    <div className="min-h-screen bg-slate-50 p-6 max-w-4xl mx-auto">
      <Link to="/gaps" state={{ names: state.names }} className="text-indigo-600 underline text-sm">
        ← Back to gaps
      </Link>

      <p className="text-xs font-bold tracking-wide text-indigo-700 mt-3">
        POTENTIAL RESEARCH GAP #{g.id} · EVIDENCE
      </p>
      <h2 className="text-xl font-bold mb-3">{g.title}</h2>

      <div className="bg-white border rounded-lg p-4 mb-4 text-sm text-slate-700">
        <p className="font-semibold mb-2">How this gap was checked</p>
        <ul className="list-disc ml-5 space-y-1">
          <li>
            Quotes found on the cited PDF page: <b>{v.quotes_verified} of {v.quotes_total}</b>
          </li>
          <li>
            Similarity between the gap wording and its evidence: average{' '}
            <b>{v.support_mean}</b>, lowest <b>{v.support_min}</b>
          </li>
          <li>Supported by <b>{g.num_papers}</b> of {g.total_papers} papers ({g.strength} evidence strength)</li>
          <li>Wording method: {g.wording}</li>
        </ul>
        <p className="text-xs text-slate-500 mt-3">
          A potential gap is not a claim of novelty. It shows an unresolved issue that several
          papers mention; whether it is still open must be checked in the wider literature.
        </p>
      </div>

      {g.evidence.map((e, i) => (
        <div key={i} className="bg-white border rounded-lg p-4 mb-3">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm mb-2">
            <p><span className="text-slate-500">Paper: </span><b>{e.paper}</b></p>
            <p><span className="text-slate-500">Page: </span><b>{e.page}</b></p>
            <p><span className="text-slate-500">Type: </span><b>{KIND[e.kind]}</b></p>
          </div>
          <p className="text-xs text-slate-500 mb-1">Original passage</p>
          <blockquote className="border-l-4 border-indigo-300 pl-3 text-sm text-slate-800">
            {e.text}
          </blockquote>
          <p className={'text-xs mt-2 ' + (e.verified ? 'text-green-700' : 'text-red-600')}>
            {e.verified ? `✓ Found on page ${e.page} of ${e.paper}` : '! Could not be matched to the PDF page text'}
          </p>
        </div>
      ))}
    </div>
  )
}
