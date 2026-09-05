import { useState } from 'react'
import { useQuery } from 'react-query'
import { getAnomalies } from '../services/queries'
import { fmtDate, paramLabel } from '../utils/helpers'

function AnomalyScoreBadge({ score }: { score?: number }) {
  const s = score ?? 0
  let cls = 'badge-low'
  if (s >= 80) cls = 'badge-critical'
  else if (s >= 60) cls = 'badge-high'
  else if (s >= 40) cls = 'badge-medium'
  return <span className={`badge ${cls}`}>{s.toFixed(0)}</span>
}

export default function AnomaliesPage() {
  const [factoryFilter, setFactoryFilter] = useState('')

  const { data, isLoading, error } = useQuery('anomalies', getAnomalies, {
    refetchInterval: 30000,
  })

  if (isLoading) return <div className="loading">Loading anomalies…</div>
  if (error) return <div className="error-box">Failed to load anomalies.</div>

  const factories = [...new Set((data ?? []).map((a) => a.factory_id))].sort()
  const rows = (data ?? []).filter((a) => !factoryFilter || a.factory_id === factoryFilter)

  return (
    <div>
      <h1 className="page-heading">Anomalies</h1>
      <p className="page-sub">
        Statistical outliers detected by Z-score and Isolation Forest. {data?.length ?? 0} total.
      </p>

      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <select value={factoryFilter} onChange={(e) => setFactoryFilter(e.target.value)} style={{ maxWidth: 200 }}>
          <option value="">All Factories</option>
          {factories.map((f) => <option key={f} value={f}>{f}</option>)}
        </select>
        <span style={{ alignSelf: 'center', color: 'var(--muted)', fontSize: 13 }}>
          {rows.length} results
        </span>
      </div>

      {/* Score distribution */}
      <div className="kpi-grid" style={{ marginBottom: 20 }}>
        {[
          { label: 'Total Anomalies', val: data?.length ?? 0, cls: 'kpi-info' },
          { label: 'Critical (≥80)', val: (data ?? []).filter((a) => (a.anomaly_score ?? 0) >= 80).length, cls: 'kpi-critical' },
          { label: 'High (60-79)', val: (data ?? []).filter((a) => { const s = a.anomaly_score ?? 0; return s >= 60 && s < 80 }).length, cls: 'kpi-high' },
          { label: 'Medium (40-59)', val: (data ?? []).filter((a) => { const s = a.anomaly_score ?? 0; return s >= 40 && s < 60 }).length, cls: 'kpi-medium' },
          { label: 'Open Status', val: (data ?? []).filter((a) => a.status === 'open').length, cls: 'kpi-high' },
        ].map((c) => (
          <div key={c.label} className="kpi-card">
            <div className="kpi-label">{c.label}</div>
            <div className={`kpi-value ${c.cls}`}>{c.val}</div>
          </div>
        ))}
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Factory</th>
              <th>Parameter</th>
              <th>Score</th>
              <th>Status</th>
              <th>Description</th>
              <th>Detected At</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((a) => (
              <tr key={a.id}>
                <td style={{ color: 'var(--muted)', fontSize: 12 }}>{a.id}</td>
                <td><code style={{ color: 'var(--accent2)', fontSize: 12 }}>{a.factory_id}</code></td>
                <td>{paramLabel(a.parameter)}</td>
                <td><AnomalyScoreBadge score={a.anomaly_score} /></td>
                <td>
                  <span className={`badge ${a.status === 'open' ? 'badge-high' : 'badge-neutral'}`}>
                    {a.status}
                  </span>
                </td>
                <td style={{ maxWidth: 300, fontSize: 12, color: 'var(--muted)' }} className="truncate">
                  {a.description ?? '—'}
                </td>
                <td style={{ color: 'var(--muted)', fontSize: 12 }}>{fmtDate(a.detected_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
