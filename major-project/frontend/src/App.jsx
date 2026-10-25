import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Upload from './pages/Upload'
import PaperAnalysis from './pages/PaperAnalysis'
import CrossPaper from './pages/CrossPaper'
import RecurringIssues from './pages/RecurringIssues'
import GapResults from './pages/GapResults'
import Evidence from './pages/Evidence'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/upload" element={<Upload />} />
      <Route path="/analysis" element={<PaperAnalysis />} />
      <Route path="/compare" element={<CrossPaper />} />
      <Route path="/issues" element={<RecurringIssues />} />
      <Route path="/gaps" element={<GapResults />} />
      <Route path="/evidence" element={<Evidence />} />
    </Routes>
  )
}
