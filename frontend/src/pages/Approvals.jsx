import { useEffect, useState } from 'react'
import { getPendingApprovals, approveCase, rejectCase } from '../api'

const fmt = (n) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)

function ApprovalCard({ c, onAction }) {
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(null)

  async function handle(fn, label) {
    setBusy(true)
    try {
      await fn(c.case_id)
      setDone(label)
      onAction()
    } catch (e) {
      console.error(e)
    } finally {
      setBusy(false)
    }
  }

  const isEscalated = c.status === 'escalated'
  const draft = isEscalated ? c.escalation_draft : c.email_draft

  return (
    <div className="approval-card">
      <div className="approval-header">
        <div style={{ flex: 1 }}>
          <div className="approval-client">{c.client_name}</div>
          <div className="approval-amount">{fmt(c.invoice_amount)}</div>
          <div className="approval-meta">
            {c.overdue_bucket} days overdue ·
            Tone: {c.tone} ·
            {isEscalated
              ? ` Escalation: ${c.escalation_action?.replace('_', ' ')}`
              : ` Attempt ${c.outreach_attempts + 1}`}
          </div>
        </div>
        <span className={`badge badge-${c.status}`}>{c.status.replace('_', ' ')}</span>
        {c.gap_linked && (
          <span style={{ fontSize: '0.72rem', color: '#EF4444', fontWeight: 600 }}>⚑ GAP-LINKED</span>
        )}
      </div>

      <div className="approval-draft">
        {draft || '(no draft available)'}
      </div>

      <div className="approval-actions">
        {done ? (
          <span style={{ fontSize: '0.85rem', color: done === 'approved' ? '#10B981' : '#64748B', fontWeight: 600 }}>
            {done === 'approved' ? '✓ Email sent' : '✗ Skipped'}
          </span>
        ) : (
          <>
            <button
              className="btn-approve"
              disabled={busy}
              onClick={() => handle(approveCase, 'approved')}
            >
              {isEscalated ? '✓ Approve & Execute' : '✓ Approve & Send'}
            </button>
            <button
              className="btn-reject"
              disabled={busy}
              onClick={() => handle(rejectCase, 'rejected')}
            >
              Skip
            </button>
            {isEscalated && c.escalation_reason && (
              <span style={{ fontSize: '0.75rem', color: '#64748B', marginLeft: '0.5rem' }}>
                AI: {c.escalation_reason}
              </span>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default function Approvals() {
  const [pending, setPending] = useState([])
  const [loading, setLoading] = useState(true)

  function load() {
    getPendingApprovals().then(r => setPending(r.data)).finally(() => setLoading(false))
  }

  useEffect(load, [])

  if (loading) return <div className="loading">Loading approvals…</div>

  if (!pending.length) return (
    <div className="empty">
      <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>✓</div>
      No pending approvals. Run the pipeline to generate email drafts.
    </div>
  )

  return (
    <>
      <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="card-title">{pending.length} pending approval{pending.length !== 1 ? 's' : ''}</div>
        <div style={{ fontSize: '0.8rem', color: '#64748B' }}>
          Review AI-drafted emails before sending. Approve to send via SendGrid.
        </div>
      </div>
      <div className="approvals-grid">
        {pending.map(c => (
          <ApprovalCard key={c.case_id} c={c} onAction={load} />
        ))}
      </div>
    </>
  )
}
