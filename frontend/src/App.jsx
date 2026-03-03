import { useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_URL || ''

function App() {
  const [resume, setResume] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [resumeFile, setResumeFile] = useState(null)
  const [jdFile, setJdFile] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showAnalysis, setShowAnalysis] = useState(false)

  const handleTailor = async () => {
    const hasResume = resume.trim() || resumeFile
    const hasJd = jobDescription.trim() || jdFile
    if (!hasResume || !hasJd) {
      setError('Please provide both resume and job description (paste text or upload DOCX).')
      return
    }
    setError('')
    setResult(null)
    setLoading(true)

    try {
      let res
      if (resumeFile || jdFile) {
        const fd = new FormData()
        fd.append('resume', resume.trim())
        fd.append('job_description', jobDescription.trim())
        fd.append('output_format', 'markdown')
        if (resumeFile) fd.append('resume_file', resumeFile)
        if (jdFile) fd.append('jd_file', jdFile)
        res = await fetch(`${API_BASE}/api/v1/tailor/upload`, { method: 'POST', body: fd })
      } else {
        res = await fetch(`${API_BASE}/api/v1/tailor`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            resume: resume.trim(),
            job_description: jobDescription.trim(),
            output_format: 'markdown',
          }),
        })
      }

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || data.message || 'Request failed')
      }

      setResult(data)
      setShowAnalysis(false)
    } catch (err) {
      setError(err.message || 'Something went wrong. Make sure the API is running on port 8000.')
    } finally {
      setLoading(false)
    }
  }

  const downloadMarkdown = () => {
    if (!result?.final_resume) return
    const blob = new Blob([result.final_resume], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'tailored_resume.md'
    a.click()
    URL.revokeObjectURL(url)
  }

  const renderMarkdown = (text) => {
    if (!text) return ''
    const escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
    return escaped
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/^- (.*)$/gim, '<li>$1</li>')
      .replace(/\n\n/g, '<br/><br/>')
      .replace(/\n/g, '<br/>')
  }

  return (
    <div className="app">
      <header className="header">
        <h1 className="title">RSMEcreator</h1>
        <p className="subtitle">Agentic AI Resume Tailoring — tailor your resume to any job description</p>
      </header>

      <main className="main">
        <div className="inputs">
          <div className="input-card">
            <label className="label">Your Resume</label>
            <textarea
              className="textarea"
              value={resume}
              onChange={(e) => setResume(e.target.value)}
              placeholder="Paste your resume..."
              rows={12}
              disabled={loading}
            />
            <p className="file-hint">— or upload DOCX —</p>
            <input
              type="file"
              accept=".docx,.doc,.txt,.md"
              onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
              disabled={loading}
            />
          </div>

          <div className="input-card">
            <label className="label">Job Description</label>
            <textarea
              className="textarea"
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job description..."
              rows={12}
              disabled={loading}
            />
            <p className="file-hint">— or upload DOCX —</p>
            <input
              type="file"
              accept=".docx,.doc,.txt,.md"
              onChange={(e) => setJdFile(e.target.files?.[0] || null)}
              disabled={loading}
            />
          </div>
        </div>

        <div className="actions">
          <button
            className="btn btn-primary"
            onClick={handleTailor}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner" />
                Tailoring...
              </>
            ) : (
              '✨ Tailor Resume'
            )}
          </button>
        </div>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        {result && (
          <div className="result">
            <div className="result-header">
              <h2>Tailored Resume</h2>
              <div className="result-actions">
                <button className="btn btn-secondary" onClick={downloadMarkdown}>
                  Download Markdown
                </button>
                <button
                  className="btn btn-outline"
                  onClick={() => setShowAnalysis(!showAnalysis)}
                >
                  {showAnalysis ? 'Hide' : 'Show'} Analysis
                </button>
              </div>
            </div>

            {result.ats_analytics && !result.ats_analytics.error && (
              <div className="ats-section">
                <div className={`ats-score grade-${result.ats_analytics?.grade || 'C'}`}>
                  <div className="ats-number">{result.ats_score}</div>
                  <div className="ats-label">ATS Score</div>
                </div>
                <div className="ats-score">
                  <div className="ats-number">{result.ats_analytics?.grade || '-'}</div>
                  <div className="ats-label">Grade</div>
                </div>
                {result.ats_analytics?.breakdown && (
                  <div className="ats-breakdown">
                    <h4>Score Breakdown</h4>
                    {Object.entries(result.ats_analytics.breakdown).map(([key, v]) =>
                      v?.score !== undefined && v?.max ? (
                        <div key={key} className="ats-item">
                          <span>{key.replace(/_/g, ' ')}:</span> {v.score}/{v.max}
                          <div className="ats-bar"><div className="ats-bar-fill" style={{ width: `${Math.round((v.score / v.max) * 100)}%` }} /></div>
                        </div>
                      ) : null
                    )}
                  </div>
                )}
                {result.ats_analytics?.suggestions?.length > 0 && (
                  <div className="analytics-suggestions">
                    <h4>Suggestions</h4>
                    <ul>{result.ats_analytics.suggestions.map((s, i) => <li key={i}>{s}</li>)}</ul>
                  </div>
                )}
              </div>
            )}

            <div
              className="resume-preview"
              dangerouslySetInnerHTML={{ __html: renderMarkdown(result.final_resume) }}
            />

            {showAnalysis && (
              <div className="analysis">
                <h3>Validation & Analysis</h3>
                <ul>
                  {result.validation_notes?.map((note, i) => (
                    <li key={i}>{note}</li>
                  ))}
                </ul>
                {result.gap_analysis && (
                  <>
                    <p><strong>Matched keywords:</strong> {result.gap_analysis.matched_keywords?.slice(0, 10).join(', ') || '—'}</p>
                    <p><strong>Suggestions:</strong></p>
                    <ul>
                      {result.gap_analysis.suggestions?.slice(0, 5).map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            )}
          </div>
        )}
      </main>

      <aside className="sidebar">
        <h3>About</h3>
        <p>RSMEcreator uses LangGraph to:</p>
        <ol>
          <li>Parse resume & JD</li>
          <li>Analyze requirements</li>
          <li>Identify gaps</li>
          <li>Plan tailoring</li>
          <li>Rewrite sections</li>
          <li>Validate & output</li>
        </ol>
        <p className="sidebar-note">Start the API: <code>uvicorn api.main:app --port 8000</code></p>
      </aside>
    </div>
  )
}

export default App
