import { useEffect, useState } from 'react'
import { getCases } from '../api'

const fmt = (n) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)

function StatusBadge({ s }) {
  return <span className={`badge badge-${s}`}>{s.replace('_', ' ')}</span>
}

function UrgencyBadge({ u }) {
  return <span className={`badge badge-${u}`}>{u}</span>
}

function ToneBadge({ t }) {
  return <span className={`badge badge-${t}`}>{t}</span>
}

function CaseRow({ c }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <tr className={c.gap_linked ? 'gap-linked-row' : ''}>
        <td>
          <span style={{ fontWeight: 600 }}>{c.client_name}</span>
          {c.gap_linked && <span style={{ marginLeft: '0.4rem', fontSize: '0.7rem', color: '#EF4444' }}>⚑ GAP</span>}
        </td>
        <td>{fmt(c.invoice_amount)}</td>
        <td>{c.overdue_bucket} days</td>
        <td><ToneBadge t={c.tone || 'firm'} /></td>
        <td><UrgencyBadge u={c.urgency} /></td>
        <td><StatusBadge s={c.status} /></td>
        <td>
          {c.email_draft && (
            <button className="expand-btn" onClick={() => setOpen(o => !o)}>
              {open ? '▲ Hide' : '▼ Draft'}
            </button>
          )}
        </td>
      </tr>
      {open && c.email_draft && (
        <tr className="draft-row">
          <td colSpan={7}>
            <div className="draft-box">{c.email_draft}</div>
          </td>
        </tr>
      )}
    </>
  )
}

export default function Collections() {
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getCases().then(r => setCases(r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Loading cases…</div>
  if (!cases.length) return <div className="empty">No collections cases. Run the pipeline to create cases.</div>

  // Sort: gap-linked first, then by urgency weight
  const urgencyOrder = { critical: 0, high: 1, medium: 2, low: 3 }
  const sorted = [...cases].sort((a, b) => {
    if (a.gap_linked !== b.gap_linked) return a.gap_linked ? -1 : 1
    return (urgencyOrder[a.urgency] ?? 9) - (urgencyOrder[b.urgency] ?? 9)
  })

  const totalAmount = cases.reduce((s, c) => s + (c.invoice_amount || 0), 0)

  return (
    <div className="table-card">
      <div className="table-header">
        <div className="card-title" style={{ marginBottom: 0 }}>
          Collections Pipeline — {cases.length} active cases
        </div>
        <div style={{ fontSize: '0.82rem', color: '#64748B' }}>
          Total outstanding: <strong>{fmt(totalAmount)}</strong>
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Client</th>
            <th>Amount</th>
            <th>Overdue</th>
            <th>Tone</th>
            <th>Urgency</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {sorted.map(c => <CaseRow key={c.case_id} c={c} />)}
        </tbody>
      </table>
    </div>
  )
}
