import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

export default function Upload() {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const addFiles = (e) => {
    const picked = [...e.target.files]
    setFiles(prev => {
      const names = new Set(prev.map(f => f.name))
      return [...prev, ...picked.filter(f => !names.has(f.name))]
    })
    e.target.value = ''  // lets you pick the same file again later
  }

  const removeFile = (name) => setFiles(prev => prev.filter(f => f.name !== name))

  const submit = async () => {
    const form = new FormData()
    files.forEach(f => form.append('files', f))
    setLoading(true); setError('')
    try {
      await axios.post('http://localhost:8000/papers/upload', form)
      navigate('/analysis', { state: { names: files.map(f => f.name) } })
    } catch (e) {
      setError(e.response?.data?.detail || 'Upload failed. Is the backend running?')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6 max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">Upload Papers</h2>

      {/* The real file input is hidden; this label acts as the button */}
      <label className="inline-block cursor-pointer bg-white border-2 border-dashed border-indigo-400 text-indigo-600 font-semibold px-6 py-3 rounded-lg hover:bg-indigo-50 mb-6">
        + Choose PDF files
        <input type="file" accept=".pdf" multiple onChange={addFiles} className="hidden" />
      </label>

      <p className="font-semibold mb-1">Uploaded Papers ({files.length})</p>
      <ul className="mb-4">
        {files.map(f => (
          <li key={f.name} className="flex justify-between border-b py-1">
            <span>✓ {f.name}</span>
            <button onClick={() => removeFile(f.name)} className="text-red-500 text-sm">Remove</button>
          </li>
        ))}
      </ul>

      <button onClick={submit} disabled={files.length < 2 || loading}
        className="bg-indigo-600 text-white px-5 py-2 rounded-lg disabled:opacity-40">
        {loading ? 'Uploading...' : 'Start Analysis'}
      </button>
      {files.length < 2 && <p className="text-sm text-slate-500 mt-2">Add at least 2 PDFs.</p>}
      {error && <p className="text-red-600 mt-2">{error}</p>}
    </div>
  )
}
