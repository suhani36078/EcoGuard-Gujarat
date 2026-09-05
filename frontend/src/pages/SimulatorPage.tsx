import { useState, useEffect } from 'react'
import { whatIfAnalysis, predictDistrict, getHotspotRisk } from '../services/queries'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { FlaskConical, AlertTriangle, TrendingDown, Info } from 'lucide-react'

const GUJARAT_DISTRICTS = [
  'Gujarat', 'Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Vapi', 'Ankleshwar', 'Bharuch',
  'Gandhinagar', 'Jamnagar', 'Bhavnagar', 'Morbi', 'Mehsana', 'Navsari',
]

const getRiskColor = (score: number) => {
  if (score >= 75) return 'var(--red)'
  if (score >= 60) return 'var(--orange)'
  if (score >= 40) return 'var(--yellow)'
  return 'var(--green)'
}

export default function SimulatorPage() {
  const [district, setDistrict] = useState('Gujarat')
  const [trafficReduction, setTrafficReduction] = useState(0)
  const [industrialReduction, setIndustrialReduction] = useState(0)
  const [wasteReduction, setWasteReduction] = useState(0)
  const [greenCover, setGreenCover] = useState(0)
  const [publicTransport, setPublicTransport] = useState(0)
  const [result, setResult] = useState<any>(null)
  const [predResult, setPredResult] = useState<any>(null)
  const [atRisk, setAtRisk] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [predLoading, setPredLoading] = useState(false)

  useEffect(() => {
    getHotspotRisk().then(setAtRisk).catch(console.error)
  }, [])

  const runSimulation = async () => {
    setLoading(true)
    try {
      const res = await whatIfAnalysis({
        district,
        traffic_reduction_pct: trafficReduction,
        industrial_reduction_pct: industrialReduction,
        waste_reduction_pct: wasteReduction,
        green_cover_increase_pct: greenCover,
        public_transport_adoption_pct: publicTransport,
      })
      setResult(res)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const runPrediction = async () => {
    setPredLoading(true)
    try {
      const res = await predictDistrict(district, 7)
      setPredResult(res)
    } catch (err) {
      console.error(err)
    } finally {
      setPredLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <h1 className="page-heading">Prediction & What-If Analysis</h1>
        <p className="page-sub">Forecast pollution trends and simulate intervention impact — <span className="data-status">MODEL-BASED / DEMO</span></p>
      </div>

      {/* Disclaimer */}
      <div className="alert-banner alert-banner-moderate">
        <Info size={16} color="var(--yellow)" style={{ flexShrink: 0 }} />
        <span>
          <strong>Simulation Disclaimer:</strong> Results are model-based estimates for demonstration purposes only.
          Not a guarantee or official policy recommendation. Actual impact depends on implementation, enforcement, and environmental conditions.
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>

        {/* What-If Simulator */}
        <div className="card">
          <div className="card-title"><FlaskConical size={14} /> What-If Simulator</div>

          <div className="form-group">
            <label>District / Region</label>
            <select value={district} onChange={e => setDistrict(e.target.value)}>
              {GUJARAT_DISTRICTS.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>

          <div className="section-divider" />

          {[
            { label: '🚗 Traffic Reduction', value: trafficReduction, setter: setTrafficReduction, desc: 'Reduce vehicle traffic volume' },
            { label: '🏭 Industrial Emissions', value: industrialReduction, setter: setIndustrialReduction, desc: 'Cut industrial pollutant output' },
            { label: '🗑️ Waste Reduction', value: wasteReduction, setter: setWasteReduction, desc: 'Improve waste management' },
            { label: '🌳 Green Cover Increase', value: greenCover, setter: setGreenCover, desc: 'Expand tree cover & parks' },
            { label: '🚌 Public Transport', value: publicTransport, setter: setPublicTransport, desc: 'Shift commuters to public transport' },
          ].map(({ label, value, setter, desc }) => (
            <div key={label} className="slider-group">
              <div className="slider-label">
                <span>{label}</span>
                <span style={{ color: 'var(--emerald2)', fontWeight: 700 }}>{value}%</span>
              </div>
              <div style={{ fontSize: 10, color: 'var(--muted)', marginBottom: 4 }}>{desc}</div>
              <input
                type="range"
                min="0"
                max="80"
                step="5"
                value={value}
                onChange={e => setter(parseInt(e.target.value))}
              />
            </div>
          ))}

          <button
            className="btn btn-primary"
            style={{ width: '100%', justifyContent: 'center', marginTop: 8 }}
            onClick={runSimulation}
            disabled={loading}
          >
            {loading ? 'Simulating…' : '▶ Run Simulation'}
          </button>
        </div>

        {/* Simulation Results */}
        <div>
          {result ? (
            <div className="card">
              <div className="card-title">Simulation Results — {result.district}</div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
                {/* Baseline */}
                <div style={{ padding: 16, background: 'var(--surface2)', borderRadius: 10, border: '1px solid var(--border2)' }}>
                  <div style={{ fontSize: 10, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>Current / Baseline</div>
                  <div style={{ fontSize: 28, fontWeight: 800, color: getRiskColor(result.baseline.overall_score), fontFamily: "'Space Grotesk', sans-serif" }}>
                    {result.baseline.overall_score}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--muted)' }}>{result.baseline.risk_level}</div>
                </div>
                {/* Projected */}
                <div style={{ padding: 16, background: 'rgba(37,99,235,0.05)', borderRadius: 10, border: '1px solid rgba(37,99,235,0.2)' }}>
                  <div style={{ fontSize: 10, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>Projected</div>
                  <div style={{ fontSize: 28, fontWeight: 800, color: getRiskColor(result.projected.overall_score), fontFamily: "'Space Grotesk', sans-serif" }}>
                    {result.projected.overall_score}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--green)' }}>
                    {result.projected.risk_level} · ↓{result.reduction_percent}% reduction
                  </div>
                </div>
              </div>

              {/* Category breakdown */}
              {[
                { label: 'Air', b: result.baseline.air_score, p: result.projected.air_score, color: '#0ea5e9' },
                { label: 'Water', b: result.baseline.water_score, p: result.projected.water_score, color: '#06b6d4' },
                { label: 'Industrial', b: result.baseline.industrial_score, p: result.projected.industrial_score, color: '#f97316' },
                { label: 'Noise', b: result.baseline.noise_score, p: result.projected.noise_score, color: '#a855f7' },
                { label: 'Waste', b: result.baseline.waste_score, p: result.projected.waste_score, color: '#f59e0b' },
              ].map(({ label, b, p, color }) => (
                <div key={label} style={{ marginBottom: 10 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                    <span style={{ fontSize: 11, color: 'var(--muted)' }}>{label}</span>
                    <span style={{ fontSize: 11 }}>
                      <span style={{ color: 'var(--muted)' }}>{b?.toFixed(0)}</span>
                      <span style={{ color: 'var(--muted)', margin: '0 4px' }}>→</span>
                      <span style={{ color: 'var(--green)', fontWeight: 700 }}>{p?.toFixed(0)}</span>
                    </span>
                  </div>
                  <div className="score-bar">
                    <div className="score-bar-fill" style={{ width: `${b}%`, background: color, opacity: 0.3 }} />
                  </div>
                  <div className="score-bar" style={{ marginTop: 2 }}>
                    <div className="score-bar-fill" style={{ width: `${p}%`, background: color }} />
                  </div>
                </div>
              ))}

              {result.intervention_factors?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <div className="card-title">Active Interventions</div>
                  {result.intervention_factors.map((f: string, i: number) => (
                    <div key={i} style={{ fontSize: 12, color: 'var(--text2)', marginBottom: 4, display: 'flex', gap: 6 }}>
                      <TrendingDown size={12} color="var(--green)" style={{ flexShrink: 0, marginTop: 2 }} />
                      {f}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: 300, gap: 16 }}>
              <FlaskConical size={40} color="var(--muted)" />
              <div style={{ fontSize: 14, color: 'var(--muted)', textAlign: 'center' }}>
                Adjust the intervention sliders and click<br /><strong style={{ color: 'var(--text2)' }}>Run Simulation</strong> to see projected impact.
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Prediction section */}
      <div className="card">
        <div className="card-title"><TrendingDown size={14} /> Pollution Risk Prediction — 7 Days</div>
        <div style={{ display: 'flex', gap: 12, marginBottom: 16, alignItems: 'center' }}>
          <select value={district} onChange={e => setDistrict(e.target.value)} style={{ width: 'auto', minWidth: 180 }}>
            {GUJARAT_DISTRICTS.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
          <button className="btn btn-primary btn-sm" onClick={runPrediction} disabled={predLoading}>
            {predLoading ? 'Predicting…' : '▶ Predict'}
          </button>
        </div>

        {predResult ? (
          <div>
            <div style={{ display: 'flex', gap: 16, marginBottom: 20, flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: 11, color: 'var(--muted)' }}>Base Score</div>
                <div style={{ fontSize: 24, fontWeight: 700, fontFamily: "'Space Grotesk', sans-serif", color: getRiskColor(predResult.base_score) }}>
                  {predResult.base_score?.toFixed(1)}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--muted)' }}>Trend</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: predResult.current_trend === 'increasing' ? 'var(--red)' : predResult.current_trend === 'decreasing' ? 'var(--green)' : 'var(--muted)' }}>
                  {predResult.current_trend === 'increasing' ? '📈 Rising' : predResult.current_trend === 'decreasing' ? '📉 Falling' : '➡️ Stable'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--muted)' }}>Model</div>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text2)' }}>{predResult.model}</div>
              </div>
            </div>

            <div className="chart-container-sm">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={predResult.predictions} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--muted)' }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: 'var(--muted)' }} />
                  <Tooltip
                    contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
                    formatter={(value: any, name: string) => [value?.toFixed(1), 'Pollution Score']}
                  />
                  <ReferenceLine y={50} stroke="var(--yellow)" strokeDasharray="4 2" label={{ value: 'MODERATE', fill: 'var(--yellow)', fontSize: 10 }} />
                  <ReferenceLine y={65} stroke="var(--orange)" strokeDasharray="4 2" />
                  <Line
                    type="monotone"
                    dataKey="predicted_score"
                    stroke="var(--emerald)"
                    strokeWidth={2}
                    dot={(props: any) => {
                      const { cx, cy, payload } = props
                      const color = getRiskColor(payload.predicted_score)
                      return <circle key={payload.date} cx={cx} cy={cy} r={4} fill={color} stroke="none" />
                    }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 8 }}>
              {predResult.confidence_note}
            </div>
          </div>
        ) : (
          <div className="empty-state">
            <AlertTriangle size={28} />
            <p>Select a district and click Predict to see the 7-day forecast.</p>
          </div>
        )}
      </div>

      {/* At-risk districts */}
      {atRisk && atRisk.at_risk_districts?.length > 0 && (
        <div className="card">
          <div className="card-title"><AlertTriangle size={14} /> Districts at Risk of New Hotspot Formation</div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>District</th>
                  <th>Current Score</th>
                  <th>Hotspot Probability</th>
                  <th>Primary Threat</th>
                  <th>Risk Level</th>
                </tr>
              </thead>
              <tbody>
                {atRisk.at_risk_districts.map((r: any) => (
                  <tr key={r.district}>
                    <td><strong>{r.district}</strong></td>
                    <td style={{ color: getRiskColor(r.current_score), fontWeight: 700 }}>{r.current_score?.toFixed(1)}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ flex: 1, height: 6, background: 'var(--surface2)', borderRadius: 3, maxWidth: 80 }}>
                          <div style={{ height: '100%', background: 'var(--orange)', borderRadius: 3, width: `${r.hotspot_probability * 100}%` }} />
                        </div>
                        <span style={{ fontSize: 12, fontWeight: 700 }}>{(r.hotspot_probability * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td>{r.primary_threat}</td>
                    <td><span className={`badge badge-${r.risk_level?.toLowerCase()}`}>{r.risk_level}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ marginTop: 10, fontSize: 11, color: 'var(--muted)' }}>{atRisk.data_note}</div>
        </div>
      )}
    </div>
  )
}
