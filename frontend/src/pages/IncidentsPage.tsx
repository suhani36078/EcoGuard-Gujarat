import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from 'react-query'
import { getIncidents, takeIncidentAction } from '../services/queries'
import { severityBadgeClass, fmtDate } from '../utils/helpers'
import type { Incident } from '../services/types'

function StatusBadge({ status }: { status?: string }) {
  const cls: Record<string, string> = {
    open: 'badge-critical',
    investigating: 'badge-high',
    escalated: 'badge-high',
    legal_action: 'badge-high',
    preventive: 'badge-medium',
    monitoring: 'badge-medium',
    resolved: 'badge-low',
  }
  return <span className={`badge ${cls[status ?? ''] ?? 'badge-neutral'}`}>{status}</span>
}

function IncidentModal({ incident, onClose }: { incident: Incident; onClose: () => void }) {
  const qc = useQueryClient()
  const [note, setNote] = useState('')
  const { mutate, isLoading } = useMutation(
    (action: string) => takeIncidentAction(incident.id, action, 'officer', note),
    { onSuccess: () => { qc.invalidateQueries('incidents'); onClose() } },
  )

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
    }}>
      <div className="card" style={{ width: '560px', maxHeight: '80vh', overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          <span style={{ fontWeight: 700, fontSize: 16 }}>{incident.title}</span>
          <button className="btn btn-outline btn-sm" onClick={onClose}>✕</button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
          {[
            { label: 'Factory', val: incident.factory_id },
            { label: 'Status', val: <StatusBadge status={incident.status} /> },
            { label: 'Severity', val: <span className={severityBadgeClass(incident.severity)}>{incident.severity}</span> },
            { label: 'Assigned To', val: incident.assigned_to ?? '—' },
            { label: 'Created', val: fmtDate(incident.created_at) },
            { label: 'Resolved', val: fmtDate(incident.resolved_at) },
          ].map((r) => (
            <div key={r.label}>
              <div className="kpi-label">{r.label}</div>
              <div style={{ marginTop: 4 }}>{r.val}</div>
            </div>
          ))}
        </div>

        <div style={{ marginBottom: 16 }}>
          <div className="card-title">Description</div>
          <p style={{ fontSize: 13, lineHeight: 1.7, color: 'var(--muted)' }}>{incident.description}</p>
        </div>

        <div style={{ marginBottom: 12 }}>
          <textarea
            placeholder="Add a note (optional)…"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            style={{ height: 72, resize: 'vertical' }}
          />
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-primary btn-sm" disabled={isLoading} onClick={() => mutate('resolve')}>
            ✓ Resolve
          </button>
          <button className="btn btn-outline btn-sm" disabled={isLoading} onClick={() => mutate('escalate')}>
            ↑ Escalate
          </button>
          <button className="btn btn-outline btn-sm" disabled={isLoading} onClick={() => mutate('assign')}>
            👤 Assign
          </button>
          <button className="btn btn-outline btn-sm" disabled={isLoading} onClick={() => mutate('add_note')}>
            📝 Add Note
          </button>
        </div>
      </div>
    </div>
  )
}

export default function IncidentsPage() {
  const [selected, setSelected] = useState<Incident | null>(null)
  const { data, isLoading, error } = useQuery('incidents', getIncidents, {
    refetchInterval: 30000,
  })

  if (isLoading) return <div className="loading">Loading incidents…</div>
  if (error) return <div className="error-box">Failed to load incidents.</div>

  return (
    <div>
      <h1 className="page-heading">Incidents</h1>
      <p className="page-sub">{data?.length ?? 0} incidents. Click a row to take action.</p>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Factory</th>
              <th>Title</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Assigned To</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {(data ?? []).length === 0 ? (
              <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--muted)' }}>No incidents</td></tr>
            ) : (data ?? []).map((inc) => (
              <tr key={inc.id} style={{ cursor: 'pointer' }} onClick={() => setSelected(inc)}>
                <td style={{ color: 'var(--muted)', fontSize: 12 }}>{inc.id}</td>
                <td><code style={{ color: 'var(--accent2)', fontSize: 12 }}>{inc.factory_id}</code></td>
                <td style={{ fontWeight: 600 }}>{inc.title}</td>
                <td><span className={severityBadgeClass(inc.severity)}>{inc.severity}</span></td>
                <td><StatusBadge status={inc.status} /></td>
                <td style={{ color: 'var(--muted)', fontSize: 12 }}>{inc.assigned_to ?? '—'}</td>
                <td style={{ color: 'var(--muted)', fontSize: 12 }}>{fmtDate(inc.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected && <IncidentModal incident={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}
