import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-900 text-white flex flex-col items-center justify-center px-6 text-center">
      <h1 className="text-4xl font-bold mb-4">Cross-Paper Analysis and Research Gap Discovery</h1>
      <p className="max-w-xl text-slate-300 mb-8">
        Upload several research papers on the same topic. The system finds
        limitations that recur across papers and surfaces potential research
        gaps, each backed by evidence from the original text.
      </p>
      <Link to="/upload" className="bg-indigo-500 hover:bg-indigo-400 px-6 py-3 rounded-lg font-semibold">
        Start Analysis
      </Link>
    </div>
  )
}
