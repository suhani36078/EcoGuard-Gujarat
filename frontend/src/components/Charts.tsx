import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line, CartesianGrid,
} from 'recharts'

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH:     '#f97316',
  MEDIUM:   '#eab308',
  LOW:      '#22c55e',
}

const RISK_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH:     '#f97316',
  MEDIUM:   '#eab308',
  LOW:      '#22c55e',
}

// ── Violations by severity bar chart ──────────────────────────────────────

interface ViolationSeverityChartProps {
  data: Record<string, number>
}

export function ViolationSeverityChart({ data }: ViolationSeverityChartProps) {
  const chartData = Object.entries(data).map(([name, value]) => ({ name, value }))
  return (
    <div className="card">
      <div className="card-title">Violations by Severity</div>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="name" tick={{ fill: '#8892a4', fontSize: 12 }} />
            <YAxis tick={{ fill: '#8892a4', fontSize: 12 }} />
            <Tooltip
              contentStyle={{ background: '#1a1d2e', border: '1px solid #2e3148', borderRadius: 8 }}
              labelStyle={{ color: '#e2e8f0' }}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {chartData.map((entry) => (
                <Cell key={entry.name} fill={SEVERITY_COLORS[entry.name] ?? '#6366f1'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

// ── Risk distribution pie chart ───────────────────────────────────────────

interface RiskDistributionChartProps {
  data: Record<string, number>
}

export function RiskDistributionChart({ data }: RiskDistributionChartProps) {
  const chartData = Object.entries(data).map(([name, value]) => ({ name, value }))
  return (
    <div className="card">
      <div className="card-title">Risk Distribution</div>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={3}
              dataKey="value"
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              labelLine={false}
            >
              {chartData.map((entry) => (
                <Cell key={entry.name} fill={RISK_COLORS[entry.name] ?? '#6366f1'} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ background: '#1a1d2e', border: '1px solid #2e3148', borderRadius: 8 }}
            />
            <Legend wrapperStyle={{ color: '#8892a4', fontSize: 12 }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

// ── Sensor reading time-series ─────────────────────────────────────────────

interface ReadingsChartProps {
  readings: Array<{ timestamp: string; pm25?: number; so2?: number; no2?: number; co?: number }>
  title?: string
}

export function ReadingsChart({ readings, title = 'Sensor Readings (last 50)' }: ReadingsChartProps) {
  const data = readings.slice(0, 50).reverse().map((r) => ({
    time: new Date(r.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
    PM25: r.pm25,
    SO2:  r.so2,
    NO2:  r.no2,
    CO:   r.co,
  }))

  return (
    <div className="card">
      <div className="card-title">{title}</div>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="time" tick={{ fill: '#8892a4', fontSize: 11 }} interval="preserveStartEnd" />
            <YAxis tick={{ fill: '#8892a4', fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: '#1a1d2e', border: '1px solid #2e3148', borderRadius: 8 }}
              labelStyle={{ color: '#e2e8f0' }}
            />
            <Legend wrapperStyle={{ color: '#8892a4', fontSize: 12 }} />
            <Line type="monotone" dataKey="PM25" stroke="#6366f1" dot={false} strokeWidth={2} />
            <Line type="monotone" dataKey="SO2"  stroke="#f97316" dot={false} strokeWidth={2} />
            <Line type="monotone" dataKey="NO2"  stroke="#eab308" dot={false} strokeWidth={2} />
            <Line type="monotone" dataKey="CO"   stroke="#22c55e" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

// ── Forecast chart ────────────────────────────────────────────────────────

interface ForecastChartProps {
  forecasts: Array<{ forecast_time?: string; predicted_value?: number; parameter?: string; confidence?: number }>
  factoryId: string
}

export function ForecastChart({ forecasts, factoryId }: ForecastChartProps) {
  const params = [...new Set(forecasts.map((f) => f.parameter).filter(Boolean))]
  const firstParam = params[0] ?? 'so2'

  const data = forecasts
    .filter((f) => f.parameter === firstParam)
    .slice(0, 24)
    .map((f) => ({
      time: f.forecast_time
        ? new Date(f.forecast_time).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
        : '',
      value: f.predicted_value,
      confidence: f.confidence ? +(f.confidence * 100).toFixed(0) : undefined,
    }))

  return (
    <div className="card">
      <div className="card-title">24h Forecast — {factoryId} ({firstParam?.toUpperCase()})</div>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="time" tick={{ fill: '#8892a4', fontSize: 11 }} interval={3} />
            <YAxis tick={{ fill: '#8892a4', fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: '#1a1d2e', border: '1px solid #2e3148', borderRadius: 8 }}
            />
            <Legend wrapperStyle={{ color: '#8892a4', fontSize: 12 }} />
            <Line type="monotone" dataKey="value" stroke="#818cf8" dot={false} strokeWidth={2} name="Predicted" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

// ── Risk score bar chart ──────────────────────────────────────────────────

interface RiskBarChartProps {
  scores: Array<{ factory_id: string; overall_score?: number; risk_level?: string }>
}

export function RiskBarChart({ scores }: RiskBarChartProps) {
  const data = scores.map((s) => ({
    name: s.factory_id,
    score: s.overall_score,
    fill: RISK_COLORS[s.risk_level ?? 'LOW'] ?? '#6366f1',
  }))

  return (
    <div className="card">
      <div className="card-title">Factory Risk Scores</div>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="name" tick={{ fill: '#8892a4', fontSize: 12 }} />
            <YAxis domain={[0, 100]} tick={{ fill: '#8892a4', fontSize: 12 }} />
            <Tooltip
              contentStyle={{ background: '#1a1d2e', border: '1px solid #2e3148', borderRadius: 8 }}
            />
            <Bar dataKey="score" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={index} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
