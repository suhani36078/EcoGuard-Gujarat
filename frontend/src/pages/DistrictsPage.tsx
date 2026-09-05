import { useState, useEffect } from 'react'
import { getDistricts, getDistrictSummary } from '../services/queries'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { TrendingUp, TrendingDown, Minus, Search, MapPin } from 'lucide-react'

const RISK_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MODERATE: '#f59e0b',
  LOW: '#22c55e',
}

const DEMO_D = [
  {id:1,district_name:'Ahmedabad',district_code:'AHM',latitude:23.0225,longitude:72.5714,overall_score:63.2,air_score:68,water_score:52,industrial_score:65,noise_score:62,waste_score:55,risk_level:'HIGH',main_pollutant:'PM2.5',main_source:'Vehicular + Industrial (Vatva)',trend:'stable',monitored_locations:12,high_risk_zones:3,active_alerts:4,population:8253000,data_confidence:0.78},
  {id:2,district_name:'Surat',district_code:'SRT',latitude:21.1702,longitude:72.8311,overall_score:58.5,air_score:58,water_score:61,industrial_score:60,noise_score:54,waste_score:50,risk_level:'MODERATE',main_pollutant:'NOx',main_source:'Textile + Diamond Industry',trend:'stable',monitored_locations:8,high_risk_zones:2,active_alerts:2,population:6081000,data_confidence:0.72},
  {id:3,district_name:'Vapi',district_code:'VPI',latitude:20.3724,longitude:72.9027,overall_score:83.5,air_score:82,water_score:88,industrial_score:91,noise_score:55,waste_score:72,risk_level:'CRITICAL',main_pollutant:'SO2 + Chemicals',main_source:'Chemical Manufacturing Zone',trend:'increasing',monitored_locations:6,high_risk_zones:4,active_alerts:7,population:200000,data_confidence:0.85},
  {id:4,district_name:'Ankleshwar',district_code:'ANK',latitude:21.6263,longitude:73.0049,overall_score:76.8,air_score:75,water_score:81,industrial_score:85,noise_score:48,waste_score:65,risk_level:'HIGH',main_pollutant:'Textile Dyes',main_source:'GIDC Industrial Estate',trend:'increasing',monitored_locations:5,high_risk_zones:3,active_alerts:5,population:180000,data_confidence:0.82},
  {id:5,district_name:'Vadodara',district_code:'VDR',latitude:22.3072,longitude:73.1812,overall_score:53.2,air_score:55,water_score:48,industrial_score:58,noise_score:50,waste_score:45,risk_level:'MODERATE',main_pollutant:'SO2',main_source:'Petrochemical + Fertilizer',trend:'stable',monitored_locations:7,high_risk_zones:2,active_alerts:2,population:2065000,data_confidence:0.70},
  {id:6,district_name:'Rajkot',district_code:'RJK',latitude:22.3039,longitude:70.8022,overall_score:47.2,air_score:48,water_score:42,industrial_score:50,noise_score:52,waste_score:40,risk_level:'MODERATE',main_pollutant:'PM10',main_source:'Engineering + Casting',trend:'stable',monitored_locations:5,high_risk_zones:1,active_alerts:1,population:1390000,data_confidence:0.65},
  {id:7,district_name:'Gandhinagar',district_code:'GDN',latitude:23.2156,longitude:72.6369,overall_score:36.5,air_score:38,water_score:32,industrial_score:40,noise_score:35,waste_score:30,risk_level:'LOW',main_pollutant:'PM2.5',main_source:'Urban Traffic',trend:'stable',monitored_locations:4,high_risk_zones:0,active_alerts:0,population:1387000,data_confidence:0.72},
  {id:8,district_name:'Jamnagar',district_code:'JAM',latitude:22.4707,longitude:70.0577,overall_score:61.5,air_score:62,water_score:55,industrial_score:72,noise_score:45,waste_score:48,risk_level:'HIGH',main_pollutant:'SO2',main_source:'Refinery Operations',trend:'increasing',monitored_locations:4,high_risk_zones:2,active_alerts:3,population:920000,data_confidence:0.74},
  {id:9,district_name:'Bhavnagar',district_code:'BHV',latitude:21.7645,longitude:72.1519,overall_score:46.8,air_score:45,water_score:50,industrial_score:52,noise_score:40,waste_score:42,risk_level:'MODERATE',main_pollutant:'Effluents',main_source:'Ship-breaking + Cement',trend:'stable',monitored_locations:3,high_risk_zones:1,active_alerts:1,population:977000,data_confidence:0.62},
  {id:10,district_name:'Bharuch',district_code:'BRC',latitude:21.7051,longitude:73.0015,overall_score:73.2,air_score:72,water_score:78,industrial_score:80,noise_score:48,waste_score:62,risk_level:'HIGH',main_pollutant:'Chemical Effluents',main_source:'Petrochemical + GIDC',trend:'increasing',monitored_locations:5,high_risk_zones:3,active_alerts:4,population:1551000,data_confidence:0.80},
  {id:11,district_name:'Morbi',district_code:'MRB',latitude:22.8173,longitude:70.8377,overall_score:63.5,air_score:65,water_score:58,industrial_score:68,noise_score:60,waste_score:55,risk_level:'HIGH',main_pollutant:'PM10 + SO2',main_source:'Ceramic Kiln Industry',trend:'increasing',monitored_locations:3,high_risk_zones:2,active_alerts:3,population:950000,data_confidence:0.68},
  {id:12,district_name:'Navsari',district_code:'NVS',latitude:20.9467,longitude:72.9520,overall_score:59.5,air_score:58,water_score:62,industrial_score:65,noise_score:45,waste_score:50,risk_level:'MODERATE',main_pollutant:'Effluents',main_source:'Sugar + Paper Industry',trend:'stable',monitored_locations:3,high_risk_zones:1,active_alerts:2,population:1334000,data_confidence:0.65},
  {id:13,district_name:'Kutch',district_code:'KCH',latitude:23.7337,longitude:69.8597,overall_score:36.8,air_score:35,water_score:38,industrial_score:42,noise_score:30,waste_score:32,risk_level:'LOW',main_pollutant:'Dust',main_source:'Mining + Construction',trend:'stable',monitored_locations:3,high_risk_zones:0,active_alerts:0,population:2092000,data_confidence:0.55},
  {id:14,district_name:'Mehsana',district_code:'MSN',latitude:23.5880,longitude:72.3693,overall_score:41.5,air_score:42,water_score:40,industrial_score:45,noise_score:38,waste_score:35,risk_level:'MODERATE',main_pollutant:'PM10',main_source:'Dairy + Engineering',trend:'stable',monitored_locations:3,high_risk_zones:1,active_alerts:1,population:2027000,data_confidence:0.58},
  {id:15,district_name:'Patan',district_code:'PTN',latitude:23.8500,longitude:72.1167,overall_score:31.5,air_score:32,water_score:35,industrial_score:30,noise_score:28,waste_score:28,risk_level:'LOW',main_pollutant:'Dust',main_source:'Agriculture + Cotton',trend:'stable',monitored_locations:2,high_risk_zones:0,active_alerts:0,population:1343000,data_confidence:0.50},
]

const DEMO_SUMMARY = {
  overall_score: 56.4,
  total_districts: 15,
  high_risk_districts: 6,
  monitored_locations: 73,
  active_alerts: 33,
  most_affected_district: 'Vapi',
}

export default function DistrictsPage() {
  const [districts, setDistricts] = useState<any[]>(DEMO_D)
  const [summary, setSummary] = useState<any>(DEMO_SUMMARY)
  const [search, setSearch] = useState('')
  const [selectedDistrict, setSelectedDistrict] = useState<any>(null)
  const [sortBy, setSortBy] = useState<'overall_score' | 'air_score' | 'water_score' | 'industrial_score'>('overall_score')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    Promise.all([getDistricts(), getDistrictSummary()])
      .then(([d, s]) => {
        if (d?.length > 0) setDistricts(d)
        if (s?.total_districts) setSummary(s)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const filtered = districts
    .filter(d => d.district_name.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => (b[sortBy] || 0) - (a[sortBy] || 0))

  const TrendIcon = ({ trend }: { trend: string }) => {
    if (trend === 'increasing') return <TrendingUp size={13} color="var(--red)" />
    if (trend === 'decreasing') return <TrendingDown size={13} color="var(--green)" />
    return <Minus size={13} color="var(--muted)" />
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <h1 className="page-heading">District Intelligence</h1>
        <p className="page-sub">City and district-wise pollution profiles across Gujarat — <span className="data-status">DEMO / SIMULATED</span></p>
      </div>

      {/* State summary */}
      {summary && (
        <div className="kpi-grid">
          {[
            { label: 'Overall Score', value: summary.overall_score?.toFixed(1), unit: '/100', color: 'kpi-high' },
            { label: 'Districts', value: summary.total_districts, color: 'kpi-info' },
            { label: 'High Risk', value: summary.high_risk_districts, color: 'kpi-critical' },
            { label: 'Monitored Locations', value: summary.monitored_locations, color: 'kpi-normal' },
            { label: 'Active Alerts', value: summary.active_alerts, color: 'kpi-high' },
            { label: 'Most Affected', value: summary.most_affected_district, color: 'kpi-critical', small: true },
          ].map(({ label, value, unit, color, small }) => (
            <div key={label} className="kpi-card">
              <div className="kpi-label">{label}</div>
              <div className={`kpi-value ${color}`} style={small ? { fontSize: 18 } : {}}>
                {value}{unit || ''}
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: selectedDistrict ? '1fr 380px' : '1fr', gap: 20 }}>
        {/* District list */}
        <div>
          {/* Controls */}
          <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 200, position: 'relative' }}>
              <Search size={14} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--muted)' }} />
              <input
                placeholder="Search district..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                style={{ paddingLeft: 36 }}
              />
            </div>
            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value as any)}
              style={{ width: 'auto', minWidth: 180 }}
            >
              <option value="overall_score">Sort: Overall Score</option>
              <option value="air_score">Sort: Air Score</option>
              <option value="water_score">Sort: Water Score</option>
              <option value="industrial_score">Sort: Industrial Score</option>
            </select>
          </div>

          {loading ? (
            <div className="loading"><div className="loading-spinner" />Loading districts…</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>District</th>
                    <th>Overall</th>
                    <th>Air</th>
                    <th>Water</th>
                    <th>Industrial</th>
                    <th>Risk Level</th>
                    <th>Trend</th>
                    <th>Alerts</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(d => (
                    <tr
                      key={d.district_code}
                      style={{ cursor: 'pointer' }}
                      onClick={() => setSelectedDistrict(d)}
                    >
                      <td>
                        <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                          <MapPin size={12} color="var(--muted)" />
                          {d.district_name}
                        </div>
                      </td>
                      <td>
                        <span style={{ fontWeight: 700, color: RISK_COLORS[d.risk_level] || 'var(--text)' }}>
                          {d.overall_score?.toFixed(1)}
                        </span>
                      </td>
                      <td>{d.air_score?.toFixed(0)}</td>
                      <td>{d.water_score?.toFixed(0)}</td>
                      <td>{d.industrial_score?.toFixed(0)}</td>
                      <td><span className={`badge badge-${d.risk_level?.toLowerCase()}`}>{d.risk_level}</span></td>
                      <td><TrendIcon trend={d.trend} /></td>
                      <td>
                        {d.active_alerts > 0
                          ? <span style={{ color: 'var(--red)', fontWeight: 700 }}>{d.active_alerts}</span>
                          : <span style={{ color: 'var(--muted)' }}>0</span>
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* District detail */}
        {selectedDistrict && (
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>{selectedDistrict.district_name}</h3>
                <span className={`badge badge-${selectedDistrict.risk_level?.toLowerCase()}`}>{selectedDistrict.risk_level}</span>
              </div>
              <button className="btn btn-sm btn-outline" onClick={() => setSelectedDistrict(null)}>✕</button>
            </div>

            <div style={{ display: 'flex', gap: 16 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 11, color: 'var(--muted)' }}>Overall Score</div>
                <div style={{ fontSize: 32, fontWeight: 800, color: RISK_COLORS[selectedDistrict.risk_level] || 'var(--text)', fontFamily: "'Space Grotesk', sans-serif" }}>
                  {selectedDistrict.overall_score?.toFixed(1)}<span style={{ fontSize: 14, color: 'var(--muted)' }}>/100</span>
                </div>
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 11, color: 'var(--muted)' }}>Population</div>
                <div style={{ fontSize: 20, fontWeight: 700, fontFamily: "'Space Grotesk', sans-serif" }}>
                  {selectedDistrict.population ? (selectedDistrict.population / 1000000).toFixed(1) + 'M' : '—'}
                </div>
              </div>
            </div>

            {/* Pollution breakdown chart */}
            <div>
              <div className="card-title">Pollution Breakdown</div>
              <div style={{ height: 180 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={[
                      { name: 'Air', value: selectedDistrict.air_score, fill: '#0ea5e9' },
                      { name: 'Water', value: selectedDistrict.water_score, fill: '#06b6d4' },
                      { name: 'Industrial', value: selectedDistrict.industrial_score, fill: '#f97316' },
                      { name: 'Noise', value: selectedDistrict.noise_score, fill: '#a855f7' },
                      { name: 'Waste', value: selectedDistrict.waste_score, fill: '#f59e0b' },
                    ]}
                    margin={{ top: 0, right: 0, left: -20, bottom: 0 }}
                  >
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--muted)' }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: 'var(--muted)' }} />
                    <Tooltip
                      contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
                    />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                      {[
                        { fill: '#0ea5e9' }, { fill: '#06b6d4' }, { fill: '#f97316' }, { fill: '#a855f7' }, { fill: '#f59e0b' }
                      ].map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="section-divider" />

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[
                { label: 'Main Pollutant', value: selectedDistrict.main_pollutant },
                { label: 'Main Source', value: selectedDistrict.main_source },
                { label: 'Monitored Locations', value: selectedDistrict.monitored_locations },
                { label: 'High Risk Zones', value: selectedDistrict.high_risk_zones, warn: true },
                { label: 'Active Alerts', value: selectedDistrict.active_alerts, warn: true },
                { label: 'Trend', value: selectedDistrict.trend },
                { label: 'Data Confidence', value: `${((selectedDistrict.data_confidence || 0.75) * 100).toFixed(0)}%` },
              ].map(({ label, value, warn }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 12, color: 'var(--muted)' }}>{label}</span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: warn && value > 0 ? 'var(--orange)' : 'var(--text2)' }}>
                    {value ?? '—'}
                  </span>
                </div>
              ))}
            </div>

            <div className="insight-box">
              <div className="insight-label">Health Impact</div>
              {selectedDistrict.overall_score > 70
                ? 'Significant pollution levels. Residents, especially sensitive groups, should limit outdoor exposure. Industrial emissions are the primary concern.'
                : selectedDistrict.overall_score > 50
                ? 'Moderate pollution. Sensitive populations (children, elderly, respiratory patients) should take precautions during peak industrial activity.'
                : 'Relatively low pollution. Standard precautions apply. Continue monitoring industrial discharge.'}
            </div>

            <div className="data-status" style={{ textAlign: 'center', width: '100%', justifyContent: 'center' }}>
              {selectedDistrict.data_source || 'DEMO/SIMULATED'}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
