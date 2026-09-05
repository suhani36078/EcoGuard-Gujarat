import type { DashboardSummary } from '../services/types'

interface KpiCardsProps {
  data: DashboardSummary
}

export default function KpiCards({ data }: KpiCardsProps) {
  const cards = [
    {
      label: 'Total Factories',
      value: data.total_factories,
      cls: 'kpi-info',
      sub: 'monitored',
    },
    {
      label: 'Active Violations',
      value: data.active_violations,
      cls: data.active_violations > 0 ? 'kpi-high' : 'kpi-normal',
      sub: `${data.critical_violations} critical`,
    },
    {
      label: 'Open Anomalies',
      value: data.open_anomalies,
      cls: data.open_anomalies > 0 ? 'kpi-medium' : 'kpi-normal',
      sub: 'unusual patterns',
    },
    {
      label: 'Pending Alerts',
      value: data.pending_alerts,
      cls: data.pending_alerts > 0 ? 'kpi-critical' : 'kpi-normal',
      sub: 'awaiting action',
    },
    {
      label: 'Open Incidents',
      value: data.open_incidents,
      cls: data.open_incidents > 0 ? 'kpi-high' : 'kpi-normal',
      sub: 'under investigation',
    },
    {
      label: 'Factories at Risk',
      value: data.factories_at_risk,
      cls: data.factories_at_risk > 0 ? 'kpi-high' : 'kpi-normal',
      sub: 'HIGH or CRITICAL',
    },
    {
      label: 'Sensor Readings',
      value: data.recent_readings_count.toLocaleString(),
      cls: 'kpi-info',
      sub: 'total on platform',
    },
  ]

  return (
    <div className="kpi-grid">
      {cards.map((c) => (
        <div key={c.label} className="kpi-card">
          <div className="kpi-label">{c.label}</div>
          <div className={`kpi-value ${c.cls}`}>{c.value}</div>
          <div className="kpi-sub">{c.sub}</div>
        </div>
      ))}
    </div>
  )
}
