import { useState } from 'react'
import { useMutation, useQuery } from 'react-query'
import { getFactories, runAgentPipeline } from '../services/queries'
import { fmtNum } from '../utils/helpers'
import type { AgentContext } from '../services/types'
import {
  Cpu, CheckCircle, Activity, TrendingUp, Shield, Users, Search, Bell,
  Droplets, Wind, Zap, Eye, MessageSquare, BarChart2, Database,
} from 'lucide-react'

const PARAMETERS = ['pm25', 'pm10', 'so2', 'no2', 'co', 'ph', 'turbidity', 'chemical_level']
const LIMITS: Record<string, number> = {
  pm25: 60, pm10: 100, so2: 80, no2: 80, co: 10, ph: 8.5, turbidity: 10, chemical_level: 50,
}

// Full EcoGuard Gujarat agent catalog (14 agents)
const ALL_AGENTS = [
  {
    id: 'monitoring', name: 'Pollution Monitoring Agent', icon: Activity, color: '#10b981',
    category: 'Core Pipeline',
    desc: 'Threshold validation on live sensor readings. Classifies status as NORMAL / WARNING / CRITICAL based on configurable GPCB limits.',
    capabilities: ['Real-time threshold check', 'GPCB limit comparison', 'Status classification', 'Sensor health check'],
  },
  {
    id: 'anomaly', name: 'Anomaly Detection Agent', icon: Search, color: '#0ea5e9',
    category: 'Core Pipeline',
    desc: 'Z-score + Isolation Forest model detects statistically unusual pollution readings. Generates anomaly scores 0–100.',
    capabilities: ['Z-score analysis', 'Isolation Forest ML model', 'Anomaly score 0–100', 'Historical baseline comparison'],
  },
  {
    id: 'compliance', name: 'Industrial Compliance Agent', icon: CheckCircle, color: '#34d399',
    category: 'Core Pipeline',
    desc: 'Analyzes industrial emission exceedance percentages, classifies violation severity, and generates compliance status for GPCB reporting.',
    capabilities: ['Exceedance % calculation', 'Severity classification', 'Compliance status', 'Show cause notice trigger'],
  },
  {
    id: 'forecast', name: 'Prediction Agent', icon: TrendingUp, color: '#f59e0b',
    category: 'Intelligence',
    desc: 'Linear regression model forecasts pollution values for 1h, 2h, and 4h windows. Confidence score based on data quality.',
    capabilities: ['1h/2h/4h forecast', 'Linear regression model', 'Confidence scoring', 'Trend direction analysis'],
  },
  {
    id: 'effluent', name: 'Water Quality Agent', icon: Droplets, color: '#06b6d4',
    category: 'Intelligence',
    desc: 'Analyzes water effluent parameters (pH, turbidity, BOD, COD). Identifies river and groundwater contamination risk.',
    capabilities: ['pH/turbidity analysis', 'BOD/COD assessment', 'River contamination risk', 'ETP compliance check'],
  },
  {
    id: 'hotspot', name: 'Hotspot Detection Agent', icon: Eye, color: '#ef4444',
    category: 'Intelligence',
    desc: 'Geospatial clustering algorithm identifies high-pollution zones across districts. Generates ranked hotspot list with severity.',
    capabilities: ['Geospatial clustering', 'Severity ranking', 'Affected radius estimate', 'Historical hotspot comparison'],
  },
  {
    id: 'risk', name: 'Factory Risk Agent', icon: Shield, color: '#f97316',
    category: 'Core Pipeline',
    desc: 'Composite risk scoring (0–100) combining anomaly, compliance, and trend signals for each industrial unit.',
    capabilities: ['Composite risk score', 'Multi-signal fusion', 'Risk category assignment', 'Escalation trigger'],
  },
  {
    id: 'community', name: 'Community Health Agent', icon: Users, color: '#a855f7',
    category: 'Intelligence',
    desc: 'Assesses population exposure risk based on pollution levels, population density, and vulnerable group proximity.',
    capabilities: ['Population exposure model', 'Vulnerable group assessment', 'Health impact estimation', 'Evacuation advisory'],
  },
  {
    id: 'citizen', name: 'Citizen Assistant Agent', icon: MessageSquare, color: '#2dd4bf',
    category: 'Citizen',
    desc: 'Natural language interface for citizen pollution queries. Answers location-based questions using district and hotspot data.',
    capabilities: ['Natural language Q&A', 'Location-based answers', 'Health advisory generation', 'Complaint routing'],
  },
  {
    id: 'air', name: 'Air Quality Agent', icon: Wind, color: '#0ea5e9',
    category: 'Intelligence',
    desc: 'Specialized analysis of air pollutants (PM2.5, PM10, SO₂, NOₓ, CO). AQI calculation and health category mapping.',
    capabilities: ['AQI calculation', 'PM2.5/PM10 analysis', 'SOx/NOx monitoring', 'Health category mapping'],
  },
  {
    id: 'alert', name: 'Alert & Early Warning Agent', icon: Bell, color: '#ef4444',
    category: 'Core Pipeline',
    desc: 'Generates intelligent alerts with deduplication, escalation routing, and multi-channel notification. Severity: LOW → CRITICAL.',
    capabilities: ['Alert generation', 'Deduplication', 'Escalation routing', 'Multi-channel notification'],
  },
  {
    id: 'recommendation', name: 'Recommendation Agent', icon: Zap, color: '#f59e0b',
    category: 'Intelligence',
    desc: 'Context-aware recommendations for interventions: regulatory action, public health advisories, industrial compliance steps.',
    capabilities: ['Regulatory recommendations', 'Health advisories', 'Intervention prioritization', 'Action plan generation'],
  },
  {
    id: 'data_quality', name: 'Data Quality Agent', icon: Database, color: '#6ee7b7',
    category: 'Infrastructure',
    desc: 'Monitors data completeness, sensor uptime, anomalous reporting gaps, and confidence scoring for all monitored locations.',
    capabilities: ['Missing data detection', 'Sensor health monitoring', 'Confidence scoring', 'Data trust indicators'],
  },
  {
    id: 'investigation', name: 'Investigation Agent', icon: BarChart2, color: '#34d399',
    category: 'Intelligence',
    desc: 'Root cause analysis and historical pattern matching. Identifies likely sources of pollution spikes using available dataset signals.',
    capabilities: ['Root cause analysis', 'Historical pattern matching', 'Source identification', 'Factor contribution scoring'],
  },
]

const CATEGORY_COLORS: Record<string, string> = {
  'Core Pipeline': 'var(--emerald)',
  'Intelligence': 'var(--sky)',
  'Citizen': 'var(--teal2)',
  'Infrastructure': 'var(--muted)',
}

const PIPELINE_STEPS = [
  { name: 'MonitoringAgent',      icon: Activity,     desc: 'Threshold validation → NORMAL / WARNING / CRITICAL' },
  { name: 'AnomalyAgent',         icon: Search,       desc: 'Z-score + Isolation Forest → anomaly_score 0–100' },
  { name: 'ComplianceAgent',      icon: CheckCircle,  desc: 'Exceedance % + severity classification' },
  { name: 'ForecastingAgent',     icon: TrendingUp,   desc: 'Linear regression 1h/2h/4h prediction' },
  { name: 'EffluentAgent',        icon: Droplets,     desc: 'Water parameter analysis (pH / turbidity)' },
  { name: 'FactoryRiskAgent',     icon: Shield,       desc: 'Composite risk score 0–100' },
  { name: 'CommunityHealthAgent', icon: Users,        desc: 'Population exposure risk assessment' },
  { name: 'InvestigationAgent',   icon: BarChart2,    desc: 'Root cause and historical pattern analysis' },
  { name: 'AlertAgent',           icon: Bell,         desc: 'Alert generation + dedup + escalation routing' },
]

function ResultPanel({ result }: { result: AgentContext }) {
  const level = result.alert_level ?? 'LOW'
  const borderColor = level === 'CRITICAL' ? 'rgba(239,68,68,0.4)'
    : level === 'HIGH' ? 'rgba(249,115,22,0.3)'
    : level === 'MEDIUM' ? 'rgba(234,179,8,0.3)'
    : 'rgba(34,197,94,0.2)'

  return (
    <div>
      <div className="card" style={{ borderColor, marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
          <span style={{ fontWeight: 700, fontSize: 16 }}>Pipeline Result — {result.event_id}</span>
          <span className={`badge badge-${level?.toLowerCase()}`}>ALERT: {result.alert_level}</span>
        </div>

        <div className="kpi-grid">
          {[
            { label: 'Status',         val: result.current_status    ?? '—', cls: result.current_status === 'CRITICAL' ? 'kpi-critical' : 'kpi-normal' },
            { label: 'Anomaly Score',  val: fmtNum(result.anomaly_score, 1),  cls: (result.anomaly_score ?? 0) > 70 ? 'kpi-high' : 'kpi-normal' },
            { label: 'Risk Score',     val: fmtNum(result.risk_score, 1),     cls: (result.risk_score ?? 0) > 65 ? 'kpi-high' : 'kpi-normal' },
            { label: 'Community Risk', val: result.community_risk    ?? '—',  cls: 'kpi-medium' },
            { label: 'Violation',      val: result.violation_status  ?? '—',  cls: result.violation_status === 'VIOLATION' ? 'kpi-critical' : 'kpi-normal' },
            { label: 'Predicted 1h',   val: fmtNum(result.predicted_value),   cls: 'kpi-info' },
          ].map((c: { label: string; val: string; cls: string }) => (
            <div key={c.label} className="kpi-card">
              <div className="kpi-label">{c.label}</div>
              <div className={`kpi-value ${c.cls}`} style={{ fontSize: 22 }}>{c.val}</div>
            </div>
          ))}
        </div>
      </div>

      {result.combined_assessment && (
        <div className="insight-box" style={{ marginBottom: 16 }}>
          <div className="insight-label">🤖 Combined Assessment</div>
          {result.combined_assessment}
        </div>
      )}

      {result.evidence && Object.keys(result.evidence).length > 0 && (
        <div className="card">
          <div className="card-title">Evidence</div>
          <pre style={{ fontSize: 12, color: 'var(--muted)', overflowX: 'auto', background: 'var(--bg)', padding: 12, borderRadius: 6 }}>
            {JSON.stringify(result.evidence, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

export default function AgentsPage() {
  const [activeTab, setActiveTab] = useState<'catalog' | 'pipeline'>('catalog')
  const [selectedAgent, setSelectedAgent] = useState<typeof ALL_AGENTS[0] | null>(null)
  const [categoryFilter, setCategoryFilter] = useState('All')
  const [form, setForm] = useState({ factory_id: 'F004', parameter: 'so2', value: 150, configured_limit: 80 })
  const [result, setResult] = useState<AgentContext | null>(null)

  const { data: factories } = useQuery('factories', getFactories)
  const { mutate, isLoading, error } = useMutation(runAgentPipeline, {
    onSuccess: (data) => setResult(data),
  })

  const categories = ['All', ...Array.from(new Set(ALL_AGENTS.map(a => a.category)))]
  const visibleAgents = categoryFilter === 'All' ? ALL_AGENTS : ALL_AGENTS.filter(a => a.category === categoryFilter)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <h1 className="page-heading">AI Multi-Agent System</h1>
        <p className="page-sub">EcoGuard Intelligence Engine — 14 specialized agents working in coordination</p>
      </div>

      {/* Stats bar */}
      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: '12px 20px' }}>
        {[
          { label: 'Total Agents', val: '14', color: 'var(--emerald2)' },
          { label: 'Core Pipeline', val: '5', color: 'var(--emerald)' },
          { label: 'Intelligence', val: '6', color: 'var(--sky)' },
          { label: 'Citizen', val: '1', color: 'var(--teal2)' },
          { label: 'Infrastructure', val: '2', color: 'var(--muted)' },
          { label: 'Pipeline Steps', val: '9', color: 'var(--orange)' },
        ].map(({ label, val, color }) => (
          <div key={label} style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 9, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 2 }}>{label}</div>
            <div style={{ fontSize: 22, fontWeight: 900, fontFamily: "'Space Grotesk', sans-serif", color }}>{val}</div>
          </div>
        ))}
      </div>

      {/* Tab selector */}
      <div className="tabs">
        <button className={`tab ${activeTab === 'catalog' ? 'active' : ''}`} onClick={() => setActiveTab('catalog')}>
          <Cpu size={14} style={{ marginRight: 6 }} />Agent Catalog
        </button>
        <button className={`tab ${activeTab === 'pipeline' ? 'active' : ''}`} onClick={() => setActiveTab('pipeline')}>
          <Activity size={14} style={{ marginRight: 6 }} />Run Pipeline
        </button>
      </div>

      {/* CATALOG TAB */}
      {activeTab === 'catalog' && (
        <div>
          {/* Category filter */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
            {categories.map(cat => (
              <button key={cat} className={`btn btn-sm ${categoryFilter === cat ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => setCategoryFilter(cat)}
                style={categoryFilter === cat && cat !== 'All' ? { borderColor: CATEGORY_COLORS[cat], color: CATEGORY_COLORS[cat], background: CATEGORY_COLORS[cat] + '15' } : {}}>
                {cat}
              </button>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: selectedAgent ? '1fr 420px' : 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
            {/* Agent cards */}
            <div style={{ display: 'grid', gridTemplateColumns: selectedAgent ? '1fr' : 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
              {visibleAgents.map(agent => {
                const Icon = agent.icon
                const isSelected = selectedAgent?.id === agent.id
                return (
                  <div key={agent.id}
                    className="card card-hover"
                    style={{ cursor: 'pointer', borderLeft: `3px solid ${agent.color}`, background: isSelected ? 'var(--surface2)' : 'var(--surface)' }}
                    onClick={() => setSelectedAgent(isSelected ? null : agent)}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                      <div style={{ width: 36, height: 36, borderRadius: 10, background: agent.color + '20', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                        <Icon size={18} color={agent.color} />
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                          <span style={{ fontWeight: 700, fontSize: 13 }}>{agent.name}</span>
                        </div>
                        <span style={{ fontSize: 10, padding: '2px 7px', borderRadius: 8, background: CATEGORY_COLORS[agent.category] + '15', color: CATEGORY_COLORS[agent.category], fontWeight: 600, letterSpacing: '0.04em' }}>{agent.category}</span>
                        <p style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.5, marginTop: 6 }}>{agent.desc.slice(0, 90)}…</p>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Agent detail panel */}
            {selectedAgent && (() => {
              const Icon = selectedAgent.icon
              return (
                <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div style={{ width: 44, height: 44, borderRadius: 12, background: selectedAgent.color + '20', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Icon size={22} color={selectedAgent.color} />
                      </div>
                      <div>
                        <div style={{ fontSize: 10, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 2 }}>{selectedAgent.category}</div>
                        <h3 style={{ fontSize: 15, fontWeight: 700 }}>{selectedAgent.name}</h3>
                      </div>
                    </div>
                    <button className="btn btn-sm btn-outline" onClick={() => setSelectedAgent(null)}>✕</button>
                  </div>

                  <div className="section-divider" />

                  <div className="insight-box" style={{ fontSize: 13 }}>
                    <div className="insight-label">Description</div>
                    {selectedAgent.desc}
                  </div>

                  <div>
                    <div className="card-title" style={{ marginBottom: 10 }}>Capabilities</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {selectedAgent.capabilities.map(cap => (
                        <div key={cap} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <CheckCircle size={13} color={selectedAgent.color} />
                          <span style={{ fontSize: 12 }}>{cap}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="insight-box" style={{ background: selectedAgent.color + '08', borderColor: selectedAgent.color + '30', fontSize: 12 }}>
                    <div className="insight-label" style={{ color: selectedAgent.color }}>Data Status</div>
                    This agent processes {selectedAgent.category === 'Core Pipeline' ? 'live sensor data routed through the main pipeline' : selectedAgent.category === 'Intelligence' ? 'historical + real-time combined signals' : selectedAgent.category === 'Citizen' ? 'user queries + platform knowledge base' : 'internal platform telemetry'}.
                    Currently operating in DEMO mode with simulated Gujarat data.
                  </div>
                </div>
              )
            })()}
          </div>
        </div>
      )}

      {/* PIPELINE TAB */}
      {activeTab === 'pipeline' && (
        <div>
          <div className="grid-2" style={{ marginBottom: 24 }}>
            {/* Pipeline Architecture */}
            <div className="card">
              <div className="card-title">Active Pipeline Architecture</div>
              {PIPELINE_STEPS.map(({ name, icon: Icon, desc }, i) => (
                <div key={name} className="pipeline-step">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1 }}>
                    <div style={{ width: 26, height: 26, borderRadius: 8, background: 'var(--emerald)20', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <Icon size={13} color="var(--emerald2)" />
                    </div>
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--emerald2)' }}>Step {i + 1}: {name}</div>
                      <div style={{ fontSize: 11, color: 'var(--muted)' }}>{desc}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Trigger form */}
            <div className="card">
              <div className="card-title">
                <Cpu size={14} style={{ display: 'inline', marginRight: 6 }} />
                Trigger Industrial Pipeline
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div>
                  <label style={{ display: 'block', marginBottom: 6, fontSize: 12, color: 'var(--muted)' }}>Factory</label>
                  <select value={form.factory_id} onChange={(e) => setForm({ ...form, factory_id: e.target.value })}>
                    {(factories ?? []).map((f) => (
                      <option key={f.id} value={f.id}>{f.id} — {f.name}</option>
                    ))}
                    {(!factories || factories.length === 0) && (
                      <>
                        <option value="F004">F004 — Vatva Chemical Complex</option>
                        <option value="F005">F005 — Vapi Industrial Unit</option>
                        <option value="F006">F006 — Ankleshwar GIDC</option>
                        <option value="F001">F001 — Gandhinagar Plant</option>
                      </>
                    )}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: 6, fontSize: 12, color: 'var(--muted)' }}>Parameter</label>
                  <select value={form.parameter} onChange={(e) => { const p = e.target.value; setForm({ ...form, parameter: p, configured_limit: LIMITS[p] ?? 80 }) }}>
                    {PARAMETERS.map((p) => <option key={p} value={p}>{p.toUpperCase()}</option>)}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: 6, fontSize: 12, color: 'var(--muted)' }}>
                    Measured Value <span style={{ color: 'var(--muted)' }}>(GPCB limit: {form.configured_limit})</span>
                  </label>
                  <input type="number" value={form.value} onChange={(e) => setForm({ ...form, value: parseFloat(e.target.value) || 0 })} />
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: 6, fontSize: 12, color: 'var(--muted)' }}>Configured Limit</label>
                  <input type="number" value={form.configured_limit} onChange={(e) => setForm({ ...form, configured_limit: parseFloat(e.target.value) || 80 })} />
                </div>

                {/* Demo presets */}
                <div>
                  <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 8 }}>Demo presets:</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {([
                      { label: 'SO₂ Spike',  factory: 'F004', param: 'so2',  val: 150 },
                      { label: 'High PM2.5', factory: 'F006', param: 'pm25', val: 110 },
                      { label: 'pH Problem', factory: 'F005', param: 'ph',   val: 9.8 },
                      { label: 'Normal',     factory: 'F001', param: 'pm25', val: 22  },
                    ] as Array<{ label: string; factory: string; param: string; val: number }>).map((preset) => (
                      <button key={preset.label} className="btn btn-outline btn-sm"
                        onClick={() => setForm({ factory_id: preset.factory, parameter: preset.param, value: preset.val, configured_limit: LIMITS[preset.param] ?? 80 })}>
                        {preset.label}
                      </button>
                    ))}
                  </div>
                </div>

                {!!error && <div className="error-box" style={{ fontSize: 12 }}>Pipeline failed. Is the backend running?</div>}

                <button className="btn btn-primary" onClick={() => mutate(form)} disabled={isLoading}>
                  {isLoading ? '⟳ Running pipeline…' : '▶ Run 9-Step Agent Pipeline'}
                </button>
              </div>
            </div>
          </div>

          {result && <ResultPanel result={result} />}
        </div>
      )}
    </div>
  )
}
