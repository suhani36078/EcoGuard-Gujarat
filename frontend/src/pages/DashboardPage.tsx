import { useQuery } from 'react-query'
import { getDashboardSummary, getViolations, getAlerts, getPollutionIndex, getHotspotSummary, getDistricts } from '../services/queries'
import KpiCards from '../components/KpiCards'
import { ViolationSeverityChart, RiskDistributionChart } from '../components/Charts'
import { severityBadgeClass, fmtDate, paramLabel } from '../utils/helpers'
import { Shield, Zap, AlertTriangle, Map, Activity, TrendingUp } from 'lucide-react'

const RISK_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MODERATE: '#f59e0b',
  POOR: '#f97316',
  'VERY POOR': '#ef4444',
  GOOD: '#22c55e',
}

export default function DashboardPage() {
  const { data: summary, isLoading, error } = useQuery('dashboard', getDashboardSummary, { refetchInterval: 30000 })
  const { data: violations } = useQuery('violations-all', () => getViolations(), { refetchInterval: 30000 })
  const { data: alerts } = useQuery('alerts-all', getAlerts, { refetchInterval: 30000 })
  const { data: pollutionIndex } = useQuery('pollution-index', getPollutionIndex, { refetchInterval: 60000 })
  const { data: hotspotSummary } = useQuery('hotspot-summary', getHotspotSummary)
  const { data: districts } = useQuery('districts', getDistricts)

  if (isLoading) return (
    <div className="loading"><div className="loading-spinner" />Loading platform data…</div>
  )
  if (error || !summary) return <div className="error-box">Failed to load dashboard data. Is the backend running?</div>

  const recentViolations = (violations ?? []).slice(0, 6)
  const pendingAlerts = (alerts ?? []).filter((a) => a.status === 'pending').slice(0, 5)
  const topDistricts = [...(districts || [])].sort((a: any, b: any) => (b.overall_score || 0) - (a.overall_score || 0)).slice(0, 5)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Hero: Gujarat Pollution Index */}
      {pollutionIndex && (
        <div className="card" style={{
          background: 'linear-gradient(135deg, var(--surface) 0%, var(--surface2) 100%)',
          borderColor: 'var(--border2)',
          position: 'relative',
          overflow: 'hidden',
        }}>
          {/* Background glow */}
          <div style={{
            position: 'absolute',
            top: -40, right: -40,
            width: 200, height: 200,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(37,99,235,0.08) 0%, transparent 70%)',
            pointerEvents: 'none',
          }} />

          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 32, flexWrap: 'wrap' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <div style={{
                  padding: '4px 10px',
                  background: 'rgba(37,99,235,0.1)',
                  border: '1px solid rgba(37,99,235,0.2)',
                  borderRadius: 20,
                  fontSize: 10,
                  fontWeight: 700,
                  color: 'var(--emerald2)',
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                }}>
                  Gujarat Pollution Intelligence Score
                </div>
                <span className="data-status">DEMO / SIMULATED</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
                <div style={{
                  fontSize: 56,
                  fontWeight: 900,
                  fontFamily: "'Space Grotesk', sans-serif",
                  color: RISK_COLORS[pollutionIndex.risk_category] || 'var(--orange)',
                  lineHeight: 1,
                }}>
                  {pollutionIndex.overall_score?.toFixed(1)}
                </div>
                <div>
                  <div style={{ fontSize: 14, color: 'var(--muted)' }}>/100</div>
                  <span className={`badge badge-${pollutionIndex.risk_category?.toLowerCase().replace(' ', '-') || 'moderate'}`}>
                    {pollutionIndex.risk_category || 'MODERATE'}
                  </span>
                </div>
              </div>

              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 8 }}>
                {pollutionIndex.health_interpretation}
              </div>
            </div>

            <div style={{ flex: 1, minWidth: 280 }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12 }}>
                {[
                  { label: 'Air', value: pollutionIndex.air_score, color: '#0ea5e9' },
                  { label: 'Water', value: pollutionIndex.water_score, color: '#06b6d4' },
                  { label: 'Industrial', value: pollutionIndex.industrial_score, color: '#f97316' },
                  { label: 'Noise', value: pollutionIndex.noise_score, color: '#a855f7' },
                  { label: 'Waste', value: pollutionIndex.waste_score, color: '#f59e0b' },
                ].map(({ label, value, color }) => (
                  <div key={label} style={{ textAlign: 'center' }}>
                    <div style={{
                      width: 48, height: 48,
                      borderRadius: '50%',
                      background: `conic-gradient(${color} ${(value || 0) * 3.6}deg, var(--surface2) 0deg)`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto 6px',
                    }}>
                      <div style={{
                        width: 36, height: 36,
                        borderRadius: '50%',
                        background: 'var(--surface)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 12,
                        fontWeight: 800,
                        color,
                        fontFamily: "'Space Grotesk', sans-serif",
                      }}>
                        {value?.toFixed(0)}
                      </div>
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--muted)' }}>{label}</div>
                  </div>
                ))}
              </div>

              <div style={{ display: 'flex', gap: 24, marginTop: 16, justifyContent: 'center' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--text)', fontFamily: "'Space Grotesk', sans-serif" }}>
                    {pollutionIndex.monitored_locations}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--muted)' }}>Monitored Locations</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--orange)', fontFamily: "'Space Grotesk', sans-serif" }}>
                    {pollutionIndex.high_risk_zones}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--muted)' }}>High Risk Zones</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--red)', fontFamily: "'Space Grotesk', sans-serif" }}>
                    {pollutionIndex.active_alerts}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--muted)' }}>Active Alerts</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--text)', fontFamily: "'Space Grotesk', sans-serif" }}>
                    {pollutionIndex.data_coverage_pct?.toFixed(0)}%
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--muted)' }}>Data Coverage</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      <KpiCards data={summary} />

      {/* Charts */}
      <div className="grid-2">
        <ViolationSeverityChart data={summary.violations_by_severity} />
        <RiskDistributionChart data={summary.risk_distribution} />
      </div>

      <div className="grid-2">
        {/* Recent Violations */}
        <div className="card">
          <div className="card-title"><AlertTriangle size={14} /> Recent Active Violations</div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Facility</th>
                  <th>Parameter</th>
                  <th>Value</th>
                  <th>Severity</th>
                  <th>Detected</th>
                </tr>
              </thead>
              <tbody>
                {recentViolations.length === 0 ? (
                  <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--muted)', padding: 24 }}>No active violations</td></tr>
                ) : recentViolations.map((v) => (
                  <tr key={v.id}>
                    <td><code style={{ color: 'var(--emerald2)', fontSize: 11 }}>{v.factory_id}</code></td>
                    <td>{paramLabel(v.parameter)}</td>
                    <td style={{ fontWeight: 700 }}>{v.value.toFixed(1)}</td>
                    <td><span className={severityBadgeClass(v.severity)}>{v.severity}</span></td>
                    <td style={{ color: 'var(--muted)', fontSize: 11 }}>{fmtDate(v.detected_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pending Alerts */}
        <div className="card">
          <div className="card-title"><Zap size={14} /> Pending Alerts</div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Facility</th>
                  <th>Severity</th>
                  <th>Message</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {pendingAlerts.length === 0 ? (
                  <tr><td colSpan={4} style={{ textAlign: 'center', color: 'var(--muted)', padding: 24 }}>No pending alerts</td></tr>
                ) : pendingAlerts.map((a) => (
                  <tr key={a.id}>
                    <td><code style={{ color: 'var(--emerald2)', fontSize: 11 }}>{a.factory_id}</code></td>
                    <td><span className={severityBadgeClass(a.severity)}>{a.severity}</span></td>
                    <td style={{ maxWidth: 200 }} className="truncate">{a.message}</td>
                    <td style={{ color: 'var(--muted)', fontSize: 11 }}>{fmtDate(a.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* District ranking + hotspot summary */}
      <div className="grid-2">
        {topDistricts.length > 0 && (
          <div className="card">
            <div className="card-title"><Map size={14} /> Top Polluted Districts</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {topDistricts.map((d: any, i: number) => (
                <div key={d.district_code} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{ width: 20, height: 20, borderRadius: '50%', background: 'var(--surface2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700, color: 'var(--muted)', flexShrink: 0 }}>
                    {i + 1}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                      <span style={{ fontSize: 13, fontWeight: 600 }}>{d.district_name}</span>
                      <span style={{ fontSize: 12, fontWeight: 700, color: RISK_COLORS[d.risk_level] || 'var(--text)' }}>
                        {d.overall_score?.toFixed(0)}
                      </span>
                    </div>
                    <div className="score-bar">
                      <div className="score-bar-fill" style={{
                        width: `${d.overall_score || 0}%`,
                        background: RISK_COLORS[d.risk_level] || 'var(--emerald)',
                      }} />
                    </div>
                  </div>
                  <span className={`badge badge-${d.risk_level?.toLowerCase()}`} style={{ flexShrink: 0 }}>
                    {d.risk_level}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {hotspotSummary && (
          <div className="card">
            <div className="card-title"><Activity size={14} /> Hotspot Overview</div>
            <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
              <div className="kpi-card" style={{ flex: 1 }}>
                <div className="kpi-label">Total Active</div>
                <div className="kpi-value kpi-high">{hotspotSummary.total_active}</div>
              </div>
              <div className="kpi-card" style={{ flex: 1 }}>
                <div className="kpi-label">Critical</div>
                <div className="kpi-value kpi-critical">{hotspotSummary.critical_count}</div>
              </div>
            </div>
            {hotspotSummary.critical_hotspots?.map((h: any) => (
              <div key={h.name} style={{
                padding: '10px 12px',
                background: 'rgba(239,68,68,0.05)',
                border: '1px solid rgba(239,68,68,0.15)',
                borderRadius: 8,
                marginBottom: 8,
              }}>
                <div style={{ fontWeight: 600, fontSize: 13 }}>{h.name}</div>
                <div style={{ fontSize: 11, color: 'var(--muted)' }}>{h.district} · {h.type}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
