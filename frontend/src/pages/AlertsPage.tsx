import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from 'react-query'
import { getAlerts, acknowledgeAlert } from '../services/queries'
import { fmtDate } from '../utils/helpers'
import { Bell, CheckCircle, AlertTriangle, AlertCircle, Info, Clock, MapPin, Factory } from 'lucide-react'

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MODERATE: '#f59e0b',
  LOW: '#22c55e',
}
const SEVERITY_ICONS: Record<string, any> = {
  CRITICAL: AlertCircle,
  HIGH: AlertTriangle,
  MODERATE: AlertTriangle,
  LOW: Info,
}

const DEMO_ALERTS = [
  { id: 1, factory_id: 'VAPI-CHEM-01', severity: 'CRITICAL', status: 'pending', message: 'Chemical effluent discharge exceeds permissible limits by 340%. Damanganga tributary at risk. Immediate containment required.', location: 'Vapi, South Gujarat', pollution_type: 'industrial', created_at: new Date(Date.now() - 1000 * 60 * 20).toISOString(), recipients: 'GPCB, District Collector', acknowledged_at: null },
  { id: 2, factory_id: 'ANK-GIDC-03', severity: 'HIGH', status: 'pending', message: 'SO₂ emissions at 3× safe limit. Night-time discharge detected at Ankleshwar GIDC Unit-3. Inspection team dispatched.', location: 'Ankleshwar, Bharuch', pollution_type: 'air', created_at: new Date(Date.now() - 1000 * 60 * 85).toISOString(), recipients: 'GPCB, Municipal Corporation', acknowledged_at: null },
  { id: 3, factory_id: 'JAM-REF-01', severity: 'HIGH', status: 'pending', message: 'Elevated H₂S odor levels in residential zones adjacent to refinery. Wind direction NE at 12 km/h. Health risk to 35,000 residents.', location: 'Jamnagar Refinery Belt', pollution_type: 'air', created_at: new Date(Date.now() - 1000 * 60 * 140).toISOString(), recipients: 'District Health Officer, GPCB', acknowledged_at: null },
  { id: 4, factory_id: 'MRB-CERAMA-07', severity: 'MODERATE', status: 'acknowledged', message: 'PM10 levels at 1.8× limit near Morbi ceramic kiln cluster. Coal ash dispersion increasing during shift change.', location: 'Morbi District', pollution_type: 'air', created_at: new Date(Date.now() - 1000 * 60 * 220).toISOString(), recipients: 'Local Pollution Control Unit', acknowledged_at: new Date(Date.now() - 1000 * 60 * 180).toISOString() },
  { id: 5, factory_id: 'BRC-PETRO-02', severity: 'HIGH', status: 'pending', message: 'Narmada downstream BOD spike detected. Petroleum residue film observed on surface water. Water intake stations alerted.', location: 'Bharuch, Narmada Zone', pollution_type: 'water', created_at: new Date(Date.now() - 1000 * 60 * 310).toISOString(), recipients: 'GWSSB, GPCB', acknowledged_at: null },
  { id: 6, factory_id: 'AHM-VATVA-11', severity: 'MODERATE', status: 'acknowledged', message: 'Volatile organic compound (VOC) odor complaints from residents near Vatva Phase-2. Evening temperature inversion trapping emissions.', location: 'Vatva, Ahmedabad', pollution_type: 'air', created_at: new Date(Date.now() - 1000 * 60 * 400).toISOString(), recipients: 'AMC Environment Dept', acknowledged_at: new Date(Date.now() - 1000 * 60 * 350).toISOString() },
  { id: 7, factory_id: 'BHV-ALANG-01', severity: 'HIGH', status: 'acknowledged', message: 'Heavy metal contamination (chromium, lead) detected in Alang coastal sediment samples. Exceeds marine pollution threshold.', location: 'Alang, Bhavnagar Coast', pollution_type: 'water', created_at: new Date(Date.now() - 1000 * 60 * 600).toISOString(), recipients: 'Gujarat Maritime Board, CPCB', acknowledged_at: new Date(Date.now() - 1000 * 60 * 540).toISOString() },
  { id: 8, factory_id: 'SRT-TEX-04', severity: 'LOW', status: 'resolved', message: 'Textile dyeing effluent color in Tapi river returned to normal after ETP maintenance. Monitoring continues.', location: 'Surat, Tapi Riverbank', pollution_type: 'water', created_at: new Date(Date.now() - 1000 * 60 * 900).toISOString(), recipients: 'GPCB Regional Office', acknowledged_at: new Date(Date.now() - 1000 * 60 * 800).toISOString() },
]

function timeAgo(iso: string | null): string {
  if (!iso) return '—'
  const d = Math.floor((Date.now() - new Date(iso).getTime()) / 60000)
  if (d < 60) return `${d}m ago`
  if (d < 1440) return `${Math.floor(d / 60)}h ago`
  return `${Math.floor(d / 1440)}d ago`
}

export default function AlertsPage() {
  const qc = useQueryClient()
  const [severityFilter, setSeverityFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [selected, setSelected] = useState<any>(null)

  const { data: liveAlerts } = useQuery('alerts-all', getAlerts, {
    refetchInterval: 15000,
    onError: () => {},
  })

  const { mutate: ack } = useMutation(acknowledgeAlert, {
    onSuccess: () => qc.invalidateQueries('alerts-all'),
  })

  const alerts = (liveAlerts && liveAlerts.length > 0) ? liveAlerts : DEMO_ALERTS

  const filtered = alerts.filter((a: any) => {
    if (severityFilter !== 'all' && a.severity?.toUpperCase() !== severityFilter) return false
    if (statusFilter !== 'all' && a.status !== statusFilter) return false
    return true
  })

  const pending = alerts.filter((a: any) => a.status === 'pending')
  const critical = alerts.filter((a: any) => a.severity === 'CRITICAL')
  const high = alerts.filter((a: any) => a.severity === 'HIGH')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 className="page-heading">Pollution Alerts</h1>
          <p className="page-sub">Real-time intelligence alerts for Gujarat — <span className="data-status">DEMO / SIMULATED</span></p>
        </div>
        {pending.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 10, padding: '8px 14px' }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#ef4444', animation: 'pulse 1.5s infinite' }} />
            <span style={{ fontSize: 13, fontWeight: 700, color: '#ef4444' }}>{pending.length} Active Alert{pending.length !== 1 ? 's' : ''}</span>
          </div>
        )}
      </div>

      {/* KPIs */}
      <div className="kpi-grid">
        {[
          { label: 'Total Alerts', val: alerts.length, cls: 'kpi-info', icon: Bell },
          { label: 'Pending Action', val: pending.length, cls: pending.length > 0 ? 'kpi-critical' : 'kpi-normal', icon: Clock },
          { label: 'Critical', val: critical.length, cls: critical.length > 0 ? 'kpi-critical' : 'kpi-normal', icon: AlertCircle },
          { label: 'High Severity', val: high.length, cls: high.length > 0 ? 'kpi-high' : 'kpi-normal', icon: AlertTriangle },
          { label: 'Resolved', val: alerts.filter((a: any) => a.status === 'resolved').length, cls: 'kpi-normal', icon: CheckCircle },
        ].map(({ label, val, cls, icon: Icon }) => (
          <div key={label} className="kpi-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <Icon size={15} color="var(--muted)" />
              <div className="kpi-label">{label}</div>
            </div>
            <div className={`kpi-value ${cls}`}>{val}</div>
          </div>
        ))}
      </div>

      {/* Filter bar */}
      <div className="card" style={{ padding: '12px 16px' }}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginRight: 4 }}>Severity:</span>
          {['all', 'CRITICAL', 'HIGH', 'MODERATE', 'LOW'].map(s => (
            <button key={s} className={`btn btn-sm ${severityFilter === s ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setSeverityFilter(s)}
              style={s !== 'all' && severityFilter === s ? { borderColor: SEVERITY_COLORS[s], background: SEVERITY_COLORS[s] + '22', color: SEVERITY_COLORS[s] } : {}}>
              {s === 'all' ? 'All' : s}
            </button>
          ))}
          <div style={{ width: 1, height: 18, background: 'var(--border)', margin: '0 8px' }} />
          <span style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginRight: 4 }}>Status:</span>
          {['all', 'pending', 'acknowledged', 'resolved'].map(s => (
            <button key={s} className={`btn btn-sm ${statusFilter === s ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setStatusFilter(s)}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Alert list + detail panel */}
      <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 400px' : '1fr', gap: 20 }}>
        {/* Alert list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {filtered.length === 0 ? (
            <div className="empty-state">
              <CheckCircle size={32} color="var(--green)" />
              <p>No alerts for current filter.</p>
            </div>
          ) : filtered.map((a: any) => {
            const SvIcon = SEVERITY_ICONS[a.severity?.toUpperCase()] || Info
            const sc = SEVERITY_COLORS[a.severity?.toUpperCase()] || 'var(--muted)'
            const isPending = a.status === 'pending'
            return (
              <div key={a.id}
                className="card card-hover"
                style={{ cursor: 'pointer', borderLeft: `3px solid ${sc}`, background: selected?.id === a.id ? 'var(--surface2)' : 'var(--surface)' }}
                onClick={() => setSelected(selected?.id === a.id ? null : a)}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      <SvIcon size={15} color={sc} />
                      <span className={`badge badge-${a.severity?.toLowerCase()}`}>{a.severity}</span>
                      <span className={`badge ${a.status === 'pending' ? 'badge-critical' : a.status === 'resolved' ? 'badge-low' : 'badge-moderate'}`}
                        style={{ fontSize: 10, opacity: 0.85 }}>{a.status}</span>
                      {a.pollution_type && (
                        <span className={`pollution-type-badge type-${a.pollution_type}`} style={{ fontSize: 10 }}>{a.pollution_type}</span>
                      )}
                    </div>
                    <p style={{ fontSize: 13, lineHeight: 1.5, marginBottom: 8 }}>{a.message}</p>
                    <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
                      {a.location && (
                        <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'var(--muted)' }}>
                          <MapPin size={11} /> {a.location}
                        </span>
                      )}
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'var(--muted)' }}>
                        <Factory size={11} /> {a.factory_id}
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'var(--muted)' }}>
                        <Clock size={11} /> {timeAgo(a.created_at)}
                      </span>
                    </div>
                  </div>
                  {isPending && (
                    <button className="btn btn-sm btn-outline"
                      style={{ borderColor: 'var(--emerald)', color: 'var(--emerald2)', whiteSpace: 'nowrap' }}
                      onClick={e => { e.stopPropagation(); ack(a.id) }}>
                      ✓ Ack
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Detail panel */}
        {selected && (() => {
          const SvIcon = SEVERITY_ICONS[selected.severity?.toUpperCase()] || Info
          const sc = SEVERITY_COLORS[selected.severity?.toUpperCase()] || 'var(--muted)'
          return (
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16, position: 'sticky', top: 80, maxHeight: '80vh', overflowY: 'auto' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ fontSize: 10, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>Alert Detail</div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <SvIcon size={18} color={sc} />
                    <span style={{ fontSize: 16, fontWeight: 700, color: sc }}>{selected.severity}</span>
                  </div>
                </div>
                <button className="btn btn-sm btn-outline" onClick={() => setSelected(null)}>✕</button>
              </div>

              <div className="section-divider" />

              {/* Status badges */}
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <span className={`badge badge-${selected.status === 'pending' ? 'critical' : selected.status === 'resolved' ? 'low' : 'moderate'}`}>
                  {selected.status}
                </span>
                {selected.pollution_type && (
                  <span className={`pollution-type-badge type-${selected.pollution_type}`}>{selected.pollution_type}</span>
                )}
              </div>

              {/* Message */}
              <div className="insight-box" style={{ fontSize: 13 }}>
                <div className="insight-label">Alert Message</div>
                {selected.message}
              </div>

              {/* Details */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {[
                  { label: 'Alert ID', value: `#${selected.id}` },
                  { label: 'Source Unit', value: selected.factory_id },
                  { label: 'Location', value: selected.location },
                  { label: 'Recipients', value: selected.recipients },
                  { label: 'Raised', value: selected.created_at ? `${timeAgo(selected.created_at)} — ${fmtDate(selected.created_at)}` : '—' },
                  { label: 'Acknowledged', value: selected.acknowledged_at ? `${timeAgo(selected.acknowledged_at)} — ${fmtDate(selected.acknowledged_at)}` : 'Not yet acknowledged' },
                ].map(({ label, value }) => (
                  <div key={label} style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                    <span style={{ fontSize: 12, color: 'var(--muted)', whiteSpace: 'nowrap' }}>{label}</span>
                    <span style={{ fontSize: 12, fontWeight: 600, textAlign: 'right', wordBreak: 'break-word' }}>{value || '—'}</span>
                  </div>
                ))}
              </div>

              <div className="section-divider" />

              {/* Recommended action */}
              <div className="insight-box" style={{ background: 'rgba(249,115,22,0.05)', borderColor: 'rgba(249,115,22,0.2)', fontSize: 12 }}>
                <div className="insight-label" style={{ color: 'var(--orange)' }}>Recommended Action</div>
                {selected.severity === 'CRITICAL'
                  ? '① Issue Show Cause Notice immediately. ② Deploy GPCB inspection team within 24h. ③ Activate public health advisory. ④ Coordinate with District Collector for emergency response. ⑤ Consider temporary production halt.'
                  : selected.severity === 'HIGH'
                  ? '① Schedule GPCB inspection within 72h. ② Issue formal notice requiring corrective action plan. ③ Increase monitoring frequency to hourly. ④ Notify local health authorities.'
                  : '① Log for routine inspection cycle. ② Monitor trend — escalate if persists >48h. ③ Verify compliance status with unit operator. ④ Issue advisory if required.'}
              </div>

              {selected.status === 'pending' && (
                <button className="btn btn-primary" onClick={() => ack(selected.id)}>
                  <CheckCircle size={14} style={{ marginRight: 6 }} />
                  Acknowledge Alert
                </button>
              )}

              <div className="data-status" style={{ justifyContent: 'center' }}>DEMO / SIMULATED DATA</div>
            </div>
          )
        })()}
      </div>
    </div>
  )
}
