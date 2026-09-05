import { useState, useEffect } from 'react'
import { getHotspots, getHotspotSummary } from '../services/queries'
import { AlertTriangle, MapPin, Filter, TrendingUp, TrendingDown, Minus, Info } from 'lucide-react'

const SEVERITY_ORDER = ['CRITICAL', 'HIGH', 'MODERATE', 'LOW']
const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MODERATE: '#f59e0b',
  LOW: '#22c55e',
}
const TYPE_ICONS: Record<string, string> = {
  industrial: '🏭',
  air: '💨',
  water: '💧',
  noise: '🔊',
  waste: '🗑️',
}

const DEMO_H = [
  {id:1,name:'Vapi Chemical Complex',district:'Vapi',latitude:20.3724,longitude:72.9027,pollution_type:'industrial',severity:'CRITICAL',severity_score:91.5,trend:'increasing',possible_source:'Chemical manufacturing & effluent discharge',affected_radius:8.5,population_affected:125000,explanation:'Historically the most polluted industrial zone in India. Unregulated chemical discharge into the Damanganga river and groundwater. Multiple textile dye units, pharmaceutical plants, and chlor-alkali factories with inadequate effluent treatment plants (ETPs). GPCB consistently records exceedances for heavy metals, COD, BOD, and VOCs.'},
  {id:2,name:'Ankleshwar GIDC',district:'Ankleshwar',latitude:21.6263,longitude:73.0049,pollution_type:'industrial',severity:'HIGH',severity_score:82.0,trend:'increasing',possible_source:'Textile dye & pharmaceutical manufacturing',affected_radius:7.0,population_affected:98000,explanation:'Dense pharmaceutical and agrochemical cluster. High load of organic pollutants, persistent organic pollutants (POPs), and heavy metals in Narmada tributaries. Non-compliant ETPs during peak production cycles. Night-time illegal discharge events have been documented.'},
  {id:3,name:'Vatva Industrial Area',district:'Ahmedabad',latitude:22.9682,longitude:72.6389,pollution_type:'air',severity:'HIGH',severity_score:76.5,trend:'stable',possible_source:'Pharmaceutical & chemical manufacturing',affected_radius:5.0,population_affected:350000,explanation:'One of Asia\'s largest chemical industrial estates. High PM2.5 from boiler stack emissions. SO2 and NOx from chemical processing. Urban sprawl has brought residential areas closer to the industrial perimeter, increasing population exposure.'},
  {id:4,name:'Jamnagar Refinery Belt',district:'Jamnagar',latitude:22.4707,longitude:70.0577,pollution_type:'air',severity:'HIGH',severity_score:74.0,trend:'increasing',possible_source:'Petroleum refining operations',affected_radius:15.0,population_affected:180000,explanation:'Home to one of the world\'s largest refinery complexes. SO2 flaring events, hydrogen sulfide odor complaints, and elevated benzene levels recorded near residential areas. Sea breeze patterns concentrate emissions inland during evening hours.'},
  {id:5,name:'Morbi Ceramic Cluster',district:'Morbi',latitude:22.8173,longitude:70.8377,pollution_type:'air',severity:'HIGH',severity_score:71.0,trend:'increasing',possible_source:'Ceramic kiln coal combustion',affected_radius:6.0,population_affected:89000,explanation:'Over 1000 ceramic tile manufacturing units using coal-fired kilns. Extremely high PM10 and PM2.5 from coal combustion. Fluoride contamination in groundwater from ceramic flux chemicals. Tunnel kiln conversions to gas are ongoing but incomplete.'},
  {id:6,name:'Alang Ship Breaking',district:'Bhavnagar',latitude:21.4000,longitude:72.1500,pollution_type:'water',severity:'HIGH',severity_score:72.0,trend:'stable',possible_source:'Ship dismantling & hazardous waste',affected_radius:12.0,population_affected:45000,explanation:'World\'s largest ship breaking yard. Intertidal zone heavily contaminated with heavy metals (lead, mercury, chromium), asbestos, and ship fuel residues. Marine biodiversity severely impacted. Occupational exposure risk for ~50,000 workers remains high.'},
  {id:7,name:'Bharuch Petrochemical Zone',district:'Bharuch',latitude:21.7051,longitude:73.0015,pollution_type:'industrial',severity:'HIGH',severity_score:78.0,trend:'increasing',possible_source:'Petrochemical & fertilizer plants',affected_radius:10.0,population_affected:145000,explanation:'Dense concentration of large-scale petrochemical, fertilizer, and chemical plants along the Narmada estuary. Ammonia emissions from fertilizer plants, along with effluent discharge affecting downstream water quality. Air quality inversions during winter increase ground-level pollutant concentration.'},
  {id:8,name:'Sabarmati River Belt',district:'Ahmedabad',latitude:23.0500,longitude:72.5800,pollution_type:'water',severity:'MODERATE',severity_score:58.0,trend:'stable',possible_source:'Industrial & urban sewage discharge',affected_radius:20.0,population_affected:500000,explanation:'Combination of untreated municipal sewage and industrial effluents entering the Sabarmati river. BOD levels frequently exceed permissible limits. Heavy metal contamination from upstream industrial clusters. Urban drain interception project is partially implemented.'},
]

const DEMO_SUMMARY = {
  total_active: 8,
  critical_count: 1,
  by_type: { industrial: 3, air: 3, water: 2 },
  avg_severity: 75.4,
  total_population_affected: 1532000,
}

export default function HotspotsPage() {
  const [hotspots, setHotspots] = useState<any[]>(DEMO_H)
  const [summary, setSummary] = useState<any>(DEMO_SUMMARY)
  const [filter, setFilter] = useState('all')
  const [selected, setSelected] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    Promise.all([getHotspots(), getHotspotSummary()])
      .then(([h, s]) => {
        if (h?.length > 0) setHotspots(h)
        if (s?.total_active) setSummary(s)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const filtered = filter === 'all'
    ? hotspots
    : hotspots.filter(h => filter === 'critical' ? h.severity === 'CRITICAL' : h.pollution_type === filter)

  const sorted = [...filtered].sort((a, b) =>
    SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity)
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <h1 className="page-heading">Pollution Hotspots</h1>
        <p className="page-sub">High-risk pollution zones requiring intervention — <span className="data-status">DEMO / SIMULATED</span></p>
      </div>

      {/* Summary KPIs */}
      {summary && (
        <div className="kpi-grid">
          <div className="kpi-card">
            <div className="kpi-label">Total Active</div>
            <div className="kpi-value kpi-high">{summary.total_active}</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">Critical</div>
            <div className="kpi-value kpi-critical">{summary.critical_count}</div>
          </div>
          {Object.entries((summary.by_type || {})).map(([type, count]) => (
            <div key={type} className="kpi-card">
              <div className="kpi-label">{TYPE_ICONS[type] || '●'} {type}</div>
              <div className="kpi-value kpi-info">{count as number}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filter */}
      <div className="card" style={{ padding: '12px 16px' }}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <Filter size={14} color="var(--muted)" />
          {['all', 'critical', 'industrial', 'air', 'water', 'noise', 'waste'].map(f => (
            <button
              key={f}
              className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setFilter(f)}
            >
              {f === 'all' ? 'All' :
               f === 'critical' ? '🔴 Critical' :
               f === 'industrial' ? '🏭 Industrial' :
               f === 'air' ? '💨 Air' :
               f === 'water' ? '💧 Water' :
               f === 'noise' ? '🔊 Noise' : '🗑️ Waste'}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 420px' : '1fr', gap: 20 }}>
        {/* Hotspot list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {loading ? (
            <div className="loading"><div className="loading-spinner" />Loading hotspots…</div>
          ) : sorted.length === 0 ? (
            <div className="empty-state">
              <AlertTriangle size={32} />
              <p>No hotspots found for the current filter.</p>
            </div>
          ) : (
            sorted.map(h => (
              <div
                key={h.id}
                className="card card-hover"
                style={{
                  cursor: 'pointer',
                  borderLeft: `3px solid ${SEVERITY_COLORS[h.severity] || 'var(--border)'}`,
                  background: selected?.id === h.id ? 'var(--surface2)' : 'var(--surface)',
                }}
                onClick={() => setSelected(selected?.id === h.id ? null : h)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      <span style={{ fontSize: 18 }}>{TYPE_ICONS[h.pollution_type] || '⚠️'}</span>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 14 }}>{h.name}</div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
                          <MapPin size={11} color="var(--muted)" />
                          <span style={{ fontSize: 11, color: 'var(--muted)' }}>{h.district}</span>
                        </div>
                      </div>
                    </div>

                    <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 8 }}>
                      {h.possible_source}
                    </div>

                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      <span className={`badge badge-${h.severity?.toLowerCase()}`}>{h.severity}</span>
                      <span className={`pollution-type-badge type-${h.pollution_type}`}>
                        {h.pollution_type}
                      </span>
                      {h.trend === 'increasing' && (
                        <span style={{ display: 'flex', alignItems: 'center', gap: 3, fontSize: 11, color: 'var(--red)' }}>
                          <TrendingUp size={12} /> Rising
                        </span>
                      )}
                      {h.trend === 'decreasing' && (
                        <span style={{ display: 'flex', alignItems: 'center', gap: 3, fontSize: 11, color: 'var(--green)' }}>
                          <TrendingDown size={12} /> Improving
                        </span>
                      )}
                    </div>
                  </div>

                  <div style={{ textAlign: 'right', marginLeft: 16 }}>
                    <div style={{ fontSize: 28, fontWeight: 800, color: SEVERITY_COLORS[h.severity], fontFamily: "'Space Grotesk', sans-serif" }}>
                      {h.severity_score?.toFixed(0)}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--muted)' }}>/ 100</div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Detail panel */}
        {selected && (
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontSize: 22 }}>{TYPE_ICONS[selected.pollution_type] || '⚠️'}</div>
                <h3 style={{ fontSize: 16, fontWeight: 700, marginTop: 4 }}>{selected.name}</h3>
              </div>
              <button className="btn btn-sm btn-outline" onClick={() => setSelected(null)}>✕</button>
            </div>

            <div style={{ display: 'flex', gap: 12 }}>
              <span className={`badge badge-${selected.severity?.toLowerCase()}`}>{selected.severity}</span>
              <span className={`pollution-type-badge type-${selected.pollution_type}`}>{selected.pollution_type}</span>
              <span style={{
                fontSize: 11, display: 'flex', alignItems: 'center', gap: 3,
                color: selected.trend === 'increasing' ? 'var(--red)' : selected.trend === 'decreasing' ? 'var(--green)' : 'var(--muted)',
              }}>
                {selected.trend === 'increasing' ? <TrendingUp size={12} /> : selected.trend === 'decreasing' ? <TrendingDown size={12} /> : <Minus size={12} />}
                {selected.trend}
              </span>
            </div>

            {/* Severity score */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: 12, color: 'var(--muted)' }}>Severity Score</span>
                <span style={{ fontSize: 12, fontWeight: 700, color: SEVERITY_COLORS[selected.severity] }}>{selected.severity_score?.toFixed(1)}/100</span>
              </div>
              <div className="score-bar">
                <div
                  className="score-bar-fill"
                  style={{
                    width: `${selected.severity_score || 0}%`,
                    background: SEVERITY_COLORS[selected.severity],
                  }}
                />
              </div>
            </div>

            <div className="section-divider" />

            {/* Stats */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { label: 'District', value: selected.district },
                { label: 'Pollution Type', value: selected.pollution_type },
                { label: 'Affected Radius', value: `${selected.affected_radius} km` },
                { label: 'Population Affected', value: selected.population_affected?.toLocaleString() },
                { label: 'Detected', value: selected.detected_at ? new Date(selected.detected_at).toLocaleDateString('en-IN') : '—' },
              ].map(({ label, value }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 12, color: 'var(--muted)' }}>{label}</span>
                  <span style={{ fontSize: 12, fontWeight: 600, textAlign: 'right', maxWidth: '60%' }}>{value || '—'}</span>
                </div>
              ))}
            </div>

            <div className="section-divider" />

            {/* Why is this hotspot high? */}
            <div>
              <div className="card-title" style={{ marginBottom: 10 }}>
                <Info size={14} /> Why is this hotspot high?
              </div>
              <div className="insight-box" style={{ fontSize: 12 }}>
                <div className="insight-label">AI Explanation</div>
                {selected.explanation || 'No explanation available for this hotspot.'}
              </div>
            </div>

            {/* Recommended intervention */}
            <div className="insight-box" style={{ background: 'rgba(249,115,22,0.05)', borderColor: 'rgba(249,115,22,0.2)' }}>
              <div className="insight-label" style={{ color: 'var(--orange)' }}>Recommended Intervention</div>
              <div style={{ fontSize: 12 }}>
                {selected.severity === 'CRITICAL'
                  ? '1) Immediate regulatory action required. 2) Issue Show Cause Notice. 3) Deploy inspection team. 4) Public health advisory. 5) Consider temporary operational suspension.'
                  : selected.severity === 'HIGH'
                  ? '1) Initiate GPCB inspection within 7 days. 2) Require corrective action plan. 3) Increase monitoring frequency. 4) Community notification.'
                  : '1) Schedule routine inspection. 2) Review compliance status. 3) Monitor trend direction. 4) Issue advisory if trend continues.'}
              </div>
            </div>

            <div className="data-status" style={{ justifyContent: 'center' }}>DEMO / SIMULATED DATA</div>
          </div>
        )}
      </div>
    </div>
  )
}
