import { useState, useEffect } from 'react'
import { getDashboardSummary, getPollutionIndex, getHotspotSummary, getReportsSummary, getDistricts } from '../services/queries'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import { Shield, AlertTriangle, Activity, Factory, Users, TrendingUp, Map, Zap, FileText } from 'lucide-react'

const RISK_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MODERATE: '#f59e0b',
  LOW: '#22c55e',
}

export default function AdminPage() {
  const [dashboard, setDashboard] = useState<any>(null)
  const [pollutionIndex, setPollutionIndex] = useState<any>(null)
  const [hotspotSummary, setHotspotSummary] = useState<any>(null)
  const [reportsSummary, setReportsSummary] = useState<any>(null)
  const [districts, setDistricts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getDashboardSummary(),
      getPollutionIndex(),
      getHotspotSummary(),
      getReportsSummary(),
      getDistricts(),
    ]).then(([d, p, h, r, dist]) => {
      setDashboard(d)
      setPollutionIndex(p)
      setHotspotSummary(h)
      setReportsSummary(r)
      setDistricts(dist)
    }).catch(console.error).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading"><div className="loading-spinner" />Loading admin data…</div>

  const riskPieData = Object.entries(dashboard?.risk_distribution || {})
    .map(([name, value]) => ({ name, value }))

  const sevPieData = Object.entries(dashboard?.violations_by_severity || {})
    .map(([name, value]) => ({ name, value }))

  const topDistricts = [...(districts || [])].sort((a, b) => (b.overall_score || 0) - (a.overall_score || 0)).slice(0, 8)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <h1 className="page-heading">Admin Dashboard</h1>
        <p className="page-sub">Platform-wide analytics and operational overview — <span className="data-status">DEMO / SIMULATED</span></p>
      </div>

      {/* Top KPIs */}
      <div className="kpi-grid">
        {[
          { label: 'Pollution Index', value: pollutionIndex?.overall_score?.toFixed(1) || '—', unit: '/100', colorClass: 'kpi-high', icon: Shield },
          { label: 'Active Violations', value: dashboard?.active_violations || 0, colorClass: 'kpi-critical', icon: AlertTriangle },
          { label: 'Critical Violations', value: dashboard?.critical_violations || 0, colorClass: 'kpi-critical', icon: AlertTriangle },
          { label: 'Open Anomalies', value: dashboard?.open_anomalies || 0, colorClass: 'kpi-medium', icon: Activity },
          { label: 'Pending Alerts', value: dashboard?.pending_alerts || 0, colorClass: 'kpi-high', icon: Zap },
          { label: 'Open Incidents', value: dashboard?.open_incidents || 0, colorClass: 'kpi-high', icon: Shield },
          { label: 'Monitored Facilities', value: dashboard?.total_factories || 0, colorClass: 'kpi-info', icon: Factory },
          { label: 'Active Hotspots', value: hotspotSummary?.total_active || 0, colorClass: 'kpi-high', icon: Map },
          { label: 'Citizen Reports', value: reportsSummary?.total || 0, colorClass: 'kpi-info', icon: FileText },
        ].map(({ label, value, unit, colorClass, icon: Icon }) => (
          <div key={label} className="kpi-card">
            <div className="kpi-label">{label}</div>
            <div className={`kpi-value ${colorClass}`}>{value}{unit || ''}</div>
          </div>
        ))}
      </div>

      <div className="grid-2">
        {/* Risk Distribution */}
        <div className="card">
          <div className="card-title">Industrial Risk Distribution</div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={riskPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={3}>
                  {riskPieData.map((entry, i) => (
                    <Cell key={i} fill={RISK_COLORS[entry.name] || '#6b8f78'} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap', marginTop: 8 }}>
            {riskPieData.map(d => (
              <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: RISK_COLORS[d.name] || '#6b8f78' }} />
                <span style={{ fontSize: 11, color: 'var(--muted)' }}>{d.name}: {d.value as number}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Violation Severity */}
        <div className="card">
          <div className="card-title">Violations by Severity</div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sevPieData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--muted)' }} />
                <YAxis tick={{ fontSize: 10, fill: 'var(--muted)' }} />
                <Tooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8 }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {sevPieData.map((entry, i) => (
                    <Cell key={i} fill={RISK_COLORS[entry.name] || '#6b8f78'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* District pollution ranking */}
      <div className="card">
        <div className="card-title">Top Districts by Pollution Score</div>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={topDistricts} layout="vertical" margin={{ top: 0, right: 30, left: 60, bottom: 0 }}>
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: 'var(--muted)' }} />
              <YAxis type="category" dataKey="district_name" tick={{ fontSize: 11, fill: 'var(--muted)' }} width={80} />
              <Tooltip
                contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
                formatter={(v: any) => [v?.toFixed(1), 'Pollution Score']}
              />
              <Bar dataKey="overall_score" radius={[0, 4, 4, 0]}>
                {topDistricts.map((d, i) => (
                  <Cell key={i} fill={RISK_COLORS[d.risk_level] || '#6b8f78'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Citizen reports & hotspot stats */}
      <div className="grid-2">
        <div className="card">
          <div className="card-title">Citizen Reports by Status</div>
          {reportsSummary?.by_status ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {Object.entries(reportsSummary.by_status).map(([status, count]) => (
                <div key={status} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 13 }}>{status.replace('_', ' ')}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 80, height: 6, background: 'var(--surface2)', borderRadius: 3 }}>
                      <div style={{
                        height: '100%', borderRadius: 3,
                        background: status === 'resolved' ? 'var(--green)' : status === 'submitted' ? 'var(--orange)' : 'var(--yellow)',
                        width: `${Math.min(100, (count as number / (reportsSummary.total || 1)) * 100)}%`,
                      }} />
                    </div>
                    <span style={{ fontSize: 13, fontWeight: 700 }}>{count as number}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : <div className="empty-state"><p>No report data</p></div>}
        </div>

        <div className="card">
          <div className="card-title">Hotspot Distribution</div>
          {hotspotSummary?.by_type ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {Object.entries(hotspotSummary.by_type).map(([type, count]) => (
                <div key={type} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 13 }}>
                    {type === 'industrial' ? '🏭' : type === 'air' ? '💨' : type === 'water' ? '💧' : type === 'noise' ? '🔊' : '🗑️'} {type}
                  </span>
                  <span style={{ fontSize: 16, fontWeight: 700 }}>{count as number}</span>
                </div>
              ))}
              <div className="section-divider" />
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 13, color: 'var(--muted)' }}>Critical Hotspots</span>
                <span style={{ fontSize: 16, fontWeight: 800, color: 'var(--red)' }}>{hotspotSummary.critical_count}</span>
              </div>
            </div>
          ) : <div className="empty-state"><p>No hotspot data</p></div>}
        </div>
      </div>
    </div>
  )
}
