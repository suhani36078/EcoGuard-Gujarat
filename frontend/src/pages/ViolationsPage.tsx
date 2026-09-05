import { useState } from 'react'
import { useQuery } from 'react-query'
import { getViolations } from '../services/queries'
import { severityBadgeClass, fmtDate, paramLabel, paramUnit, fmtNum } from '../utils/helpers'

export default function ViolationsPage() {
  const [factoryFilter, setFactoryFilter] = useState('')
  const [sevFilter, setSevFilter] = useState('')

  const { data, isLoading, error } = useQuery('violations-all', () => getViolations(), {
    refetchInterval: 30000,
  })

  if (isLoading) return <div className="loading">Loading violations…</div>
  if (error) return <div className="error-box">Failed to load violations.</div>

  const rows = (data ?? []).filter((v) => {
    if (factoryFilter && v.factory_id !== factoryFilter) return false
    if (sevFilter && v.severity !== sevFilter) return false
    return true
  })

  const factories = [...new Set((data ?? []).map((v) => v.factory_id))].sort()

  return (
    <div>
      <h1 className="page-heading">Violations</h1>
      <p className="page-sub">All detected regulatory limit exceedances. {data?.length ?? 0} total.</p>

      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <select value={factoryFilter} onChange={(e) => setFactoryFilter(e.target.value)} style={{ maxWidth: 200 }}>
          <option value="">All Factories</option>
          {factories.map((f) => <option key={f} value={f}>{f}</option>)}
        </select>
        <select value={sevFilter} onChange={(e) => setSevFilter(e.target.value)} style={{ maxWidth: 160 }}>
          <option value="">All Severities</option>
          {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <span style={{ alignSelf: 'center', color: 'var(--muted)', fontSize: 13 }}>
          {rows.length} results
        </span>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Factory</th>
              <th>Parameter</th>
              <th>Measured</th>
              <th>Limit</th>
              <th>Exceedance</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Detected At</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr><td colSpan={9} style={{ textAlign: 'center', color: 'var(--muted)' }}>No violations match filter</td></tr>
            ) : rows.map((v) => (
              <tr key={v.id}>
                <td style={{ color: 'var(--muted)', fontSize: 12 }}>{v.id}</td>
                <td><code style={{ color: 'var(--accent2)', fontSize: 12 }}>{v.factory_id}</code></td>
                <td>
                  <span style={{ fontWeight: 600 }}>{paramLabel(v.parameter)}</span>
                  <span style={{ color: 'var(--muted)', fontSize: 11, marginLeft: 4 }}>{paramUnit(v.parameter)}</span>
                </td>
                <td style={{ fontWeight: 600, color: 'var(--orange)' }}>{fmtNum(v.value)}</td>
                <td style={{ color: 'var(--muted)' }}>{fmtNum(v.limit_value)}</td>
                <td>
                  <span style={{
                    color: (v.exceedance_percent ?? 0) > 50 ? 'var(--red)' : 'var(--orange)',
                    fontWeight: 600,
                  }}>
                    +{fmtNum(v.exceedance_percent)}%
                  </span>
                </td>
                <td><span className={severityBadgeClass(v.severity)}>{v.severity}</span></td>
                <td>
                  <span className={`badge ${v.status === 'active' ? 'badge-critical' : 'badge-low'}`}>
                    {v.status}
                  </span>
                </td>
                <td style={{ color: 'var(--muted)', fontSize: 12, whiteSpace: 'nowrap' }}>{fmtDate(v.detected_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
