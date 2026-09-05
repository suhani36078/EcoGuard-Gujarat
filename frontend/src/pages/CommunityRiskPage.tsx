import { useQuery } from 'react-query'
import { getCommunityRisk } from '../services/queries'
import { riskLevelBadgeClass, fmtNum } from '../utils/helpers'

export default function CommunityRiskPage() {
  const { data, isLoading, error } = useQuery('community-risk', getCommunityRisk, {
    refetchInterval: 60000,
  })

  if (isLoading) return <div className="loading">Loading community risk…</div>
  if (error) return <div className="error-box">Failed to load community risk.</div>

  const critical = (data ?? []).filter((c) => c.risk_level === 'CRITICAL')
  const high     = (data ?? []).filter((c) => c.risk_level === 'HIGH')

  return (
    <div>
      <h1 className="page-heading">Community Risk</h1>
      <p className="page-sub">Environmental exposure risk for communities near industrial zones</p>

      {critical.length > 0 && (
        <div className="error-box" style={{ marginBottom: 20 }}>
          ⚠ {critical.length} factory/factories pose CRITICAL community risk — immediate intervention required
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(340px,1fr))', gap: 20, marginBottom: 24 }}>
        {(data ?? []).map((c) => (
          <div key={c.factory_id} className="card" style={{
            borderColor: c.risk_level === 'CRITICAL' ? 'rgba(239,68,68,0.4)'
                        : c.risk_level === 'HIGH'     ? 'rgba(249,115,22,0.3)'
                        : undefined,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 15 }}>{c.factory_name}</div>
                <div style={{ color: 'var(--muted)', fontSize: 12 }}>{c.location}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{
                  fontSize: 28, fontWeight: 700,
                  color: c.risk_level === 'CRITICAL' ? 'var(--red)'
                       : c.risk_level === 'HIGH'     ? 'var(--orange)'
                       : c.risk_level === 'MEDIUM'   ? 'var(--yellow)'
                       : 'var(--green)',
                }}>
                  {fmtNum(c.overall_score, 0)}
                </div>
                <span className={riskLevelBadgeClass(c.risk_level)}>{c.risk_level}</span>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 12 }}>
              {[
                { label: 'Wind Speed', val: c.wind_speed ? `${c.wind_speed.toFixed(1)} m/s` : '—' },
                { label: 'Wind Direction', val: c.wind_direction ? `${c.wind_direction.toFixed(0)}°` : '—' },
                { label: 'Nearby Population', val: c.nearby_population ?? '—' },
                { label: 'Affected Area', val: c.affected_area_km ? `${c.affected_area_km.toFixed(1)} km²` : '—' },
              ].map((item) => (
                <div key={item.label} style={{ background: 'var(--bg2)', borderRadius: 6, padding: '8px 10px' }}>
                  <div style={{ fontSize: 10, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    {item.label}
                  </div>
                  <div style={{ fontWeight: 600, marginTop: 2 }}>{item.val}</div>
                </div>
              ))}
            </div>

            {c.health_advisory && (
              <div className="insight-box" style={{ fontSize: 12 }}>
                <div className="insight-label">🏥 Health Advisory</div>
                {c.health_advisory}
              </div>
            )}
          </div>
        ))}
      </div>

      {high.length > 0 && (
        <div className="card">
          <div className="card-title">High Risk Factories Summary</div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Factory</th><th>Location</th><th>Score</th><th>Risk Level</th><th>Advisory</th></tr>
              </thead>
              <tbody>
                {[...critical, ...high].map((c) => (
                  <tr key={c.factory_id}>
                    <td><code style={{ color: 'var(--accent2)', fontSize: 12 }}>{c.factory_id}</code></td>
                    <td>{c.location}</td>
                    <td style={{ fontWeight: 700, color: 'var(--orange)' }}>{fmtNum(c.overall_score, 0)}</td>
                    <td><span className={riskLevelBadgeClass(c.risk_level)}>{c.risk_level}</span></td>
                    <td style={{ fontSize: 12, color: 'var(--muted)', maxWidth: 300 }} className="truncate">
                      {c.health_advisory ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
