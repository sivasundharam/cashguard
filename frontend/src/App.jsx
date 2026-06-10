import { useState } from 'react'
import Dashboard from './pages/Dashboard'
import Collections from './pages/Collections'
import Approvals from './pages/Approvals'
import { runPipeline } from './api'

export default function App() {
  const [tab, setTab] = useState('dashboard')
  const [running, setRunning] = useState(false)
  const [pipelineResult, setPipelineResult] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)

  async function handleRun() {
    setRunning(true)
    setPipelineResult(null)
    try {
      const { data } = await runPipeline()
      setPipelineResult(data)
      setRefreshKey(k => k + 1)
    } catch (e) {
      console.error('Pipeline error', e)
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="app">
      <nav className="navbar">
        <div className="nav-brand">
          <span className="shield">🛡</span>
          <span>CashGuard</span>
          <span className="brand-sub">Maria's Catering</span>
        </div>
        <div className="nav-tabs">
          {['dashboard', 'collections', 'approvals'].map(t => (
            <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
        <button className={`run-btn ${running ? 'running' : ''}`} onClick={handleRun} disabled={running}>
          {running ? '⟳ Running agents...' : '▶ Run Pipeline'}
        </button>
      </nav>

      <main className="main">
        {pipelineResult && (
          <div className="pipeline-banner">
            ✓ Pipeline complete — {pipelineResult.cases_created?.length ?? 0} new cases,&nbsp;
            {pipelineResult.drafts_created?.length ?? 0} drafts generated,&nbsp;
            gap detected: <strong>{pipelineResult.gap_detected ? 'Yes' : 'No'}</strong>
            {pipelineResult.errors?.length > 0 && (
              <span style={{ color: '#B45309', marginLeft: '1rem' }}>
                ⚠ {pipelineResult.errors.length} warning(s)
              </span>
            )}
          </div>
        )}
        {tab === 'dashboard'   && <Dashboard key={refreshKey} />}
        {tab === 'collections' && <Collections key={refreshKey} />}
        {tab === 'approvals'   && <Approvals key={refreshKey} />}
      </main>
    </div>
  )
}
