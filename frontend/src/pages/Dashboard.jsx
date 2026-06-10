import { useEffect, useState } from 'react'
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  PointElement, LineElement, Filler, Tooltip, Legend,
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import { getLatestForecast, getCases } from '../api'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

const fmt = (n) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)

function labelDate(iso) {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export default function Dashboard() {
  const [forecast, setForecast] = useState(null)
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getLatestForecast(), getCases()])
      .then(([f, c]) => { setForecast(f.data); setCases(c.data) })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Loading forecast…</div>
  if (!forecast || !forecast.daily_forecast) return <div className="empty">No forecast data. Run the pipeline first.</div>

  const days = forecast.daily_forecast.slice(0, 30)
  const labels = days.map(d => labelDate(d.date))
  const balances = days.map(d => d.projected_balance)
  const gapLinked = cases.filter(c => c.gap_linked)
  const totalOverdue = cases.reduce((s, c) => s + (c.invoice_amount || 0), 0)
  const firstGap = forecast.gap_dates?.[0]

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Projected Balance',
        data: balances,
        fill: true,
        tension: 0.3,
        pointRadius: (ctx) => (days[ctx.dataIndex]?.gap ? 4 : 2),
        segment: {
          borderColor: ctx => days[ctx.p1DataIndex]?.gap ? '#EF4444' : '#3B82F6',
          backgroundColor: ctx => days[ctx.p1DataIndex]?.gap ? 'rgba(239,68,68,0.08)' : 'rgba(59,130,246,0.08)',
        },
        borderWidth: 2,
      },
    ],
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: ctx => fmt(ctx.parsed.y),
          afterLabel: ctx => days[ctx.dataIndex]?.gap ? '⚠ GAP' : '',
        },
      },
    },
    scales: {
      x: {
        ticks: { maxTicksLimit: 10, font: { size: 11 } },
        grid: { display: false },
      },
      y: {
        ticks: { callback: v => fmt(v), font: { size: 11 } },
        grid: { color: '#F1F5F9' },
      },
    },
  }

  return (
    <>
      <div className="metrics-row">
        <div className="metric-card">
          <div className="metric-label">Current Balance</div>
          <div className="metric-value success">{fmt(forecast.current_balance)}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">First Gap Date</div>
          <div className="metric-value danger">{firstGap ? labelDate(firstGap) : '—'}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Gap Amount</div>
          <div className="metric-value danger">{fmt(forecast.gap_amount)}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Total Overdue</div>
          <div className="metric-value warning">{fmt(totalOverdue)}</div>
        </div>
      </div>

      {forecast.gap_dates?.length > 0 && (
        <div className="gap-alert">
          <span className="gap-alert-icon">🚨</span>
          <div>
            <div className="gap-alert-title">Cash shortfall detected — {labelDate(firstGap)}</div>
            <div className="gap-alert-body">
              Projected balance of {fmt(forecast.current_balance - 10 * 1000)} will be insufficient for payroll
              ({fmt(8000)}). CashGuard has prioritized {forecast.linked_invoices?.length ?? 0} invoices to close the
              {' '}{fmt(forecast.gap_amount)} gap.
            </div>
          </div>
        </div>
      )}

      <div className="chart-card">
        <div className="card-title">60-Day Cash Runway (showing 30 days)</div>
        <div style={{ height: 280 }}>
          <Line data={chartData} options={chartOptions} />
        </div>
        <div style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: '#64748B', display: 'flex', gap: '1.5rem' }}>
          <span><span style={{ color: '#3B82F6' }}>■</span> Safe zone</span>
          <span><span style={{ color: '#EF4444' }}>■</span> Gap zone (balance below $0)</span>
          <span>⚑ Jun 18 — Payroll $8,000</span>
          <span>⚑ Jun 25 — Rent $4,500</span>
        </div>
      </div>

      {gapLinked.length > 0 && (
        <>
          <div className="card-title" style={{ marginBottom: '0.75rem' }}>
            🎯 Priority Collections — these invoices close the gap
          </div>
          <div className="priority-grid">
            {gapLinked.map(c => (
              <div className="priority-card" key={c.case_id}>
                <div className="priority-card-client">{c.client_name}</div>
                <div className="priority-card-amount">{fmt(c.invoice_amount)}</div>
                <div className="priority-card-meta">
                  {c.overdue_bucket} days overdue · Tone: {c.tone} · {c.status}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </>
  )
}
