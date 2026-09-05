import { useState } from 'react'
import { useQuery } from 'react-query'
import { getFactories, getReadings } from '../services/queries'
import { ReadingsChart } from '../components/Charts'
import type { Factory } from '../services/types'

function FactoryRow({ factory, onSelect, selected }: {
  factory: Factory
  onSelect: (f: Factory) => void
  selected: boolean
}) {
  return (
    <tr
      style={{ cursor: 'pointer', background: selected ? 'rgba(99,102,241,0.08)' : undefined }}
      onClick={() => onSelect(factory)}
    >
      <td><code style={{ color: 'var(--accent2)', fontSize: 12 }}>{factory.id}</code></td>
      <td style={{ fontWeight: 600 }}>{factory.name}</td>
      <td>{factory.location}</td>
      <td>{factory.type ?? '—'}</td>
      <td>
        <span className={`badge ${factory.status === 'active' ? 'badge-low' : 'badge-neutral'}`}>
          {factory.status}
        </span>
      </td>
      <td style={{ color: 'var(--muted)', fontSize: 12 }}>
        {factory.latitude.toFixed(4)}, {factory.longitude.toFixed(4)}
      </td>
    </tr>
  )
}

export default function FactoriesPage() {
  const [selected, setSelected] = useState<Factory | null>(null)

  const { data: factories, isLoading } = useQuery('factories', getFactories)
  const { data: readings } = useQuery(
    ['readings', selected?.id],
    () => getReadings(selected!.id, 100),
    { enabled: !!selected },
  )

  if (isLoading) return <div className="loading">Loading factories…</div>

  return (
    <div>
      <h1 className="page-heading">Factories</h1>
      <p className="page-sub">Click a factory to see its sensor readings.</p>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Location</th>
              <th>Type</th>
              <th>Status</th>
              <th>Coordinates</th>
            </tr>
          </thead>
          <tbody>
            {(factories ?? []).map((f) => (
              <FactoryRow
                key={f.id}
                factory={f}
                onSelect={setSelected}
                selected={selected?.id === f.id}
              />
            ))}
          </tbody>
        </table>
      </div>

      {selected && (
        <div style={{ marginTop: 24 }}>
          <div style={{ marginBottom: 16 }}>
            <span className="page-heading" style={{ fontSize: 18 }}>{selected.name}</span>
            <span style={{ marginLeft: 12, color: 'var(--muted)', fontSize: 13 }}>
              {selected.location} · {selected.type}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 16, marginBottom: 20 }}>
            {[
              { label: 'Location', val: selected.location },
              { label: 'Type', val: selected.type ?? '—' },
              { label: 'Status', val: selected.status?.toUpperCase() ?? '—' },
              { label: 'Latitude', val: selected.latitude.toFixed(4) },
              { label: 'Longitude', val: selected.longitude.toFixed(4) },
              { label: 'Factory ID', val: selected.id },
            ].map((item) => (
              <div key={item.label} className="card" style={{ padding: '14px 18px' }}>
                <div className="kpi-label">{item.label}</div>
                <div style={{ fontWeight: 600, marginTop: 4 }}>{item.val}</div>
              </div>
            ))}
          </div>

          {readings && readings.length > 0 && (
            <ReadingsChart readings={readings} title={`Sensor Readings — ${selected.id}`} />
          )}

          {readings && readings.length > 0 && (
            <div className="table-wrap" style={{ marginTop: 20 }}>
              <table>
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>PM₂.₅</th>
                    <th>PM₁₀</th>
                    <th>SO₂</th>
                    <th>NO₂</th>
                    <th>CO</th>
                    <th>pH</th>
                    <th>Turbidity</th>
                    <th>Wind</th>
                  </tr>
                </thead>
                <tbody>
                  {readings.slice(0, 20).map((r) => (
                    <tr key={r.id}>
                      <td style={{ fontSize: 11, color: 'var(--muted)', whiteSpace: 'nowrap' }}>
                        {new Date(r.timestamp).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' })}
                      </td>
                      <td>{r.pm25?.toFixed(1) ?? '—'}</td>
                      <td>{r.pm10?.toFixed(1) ?? '—'}</td>
                      <td>{r.so2?.toFixed(1) ?? '—'}</td>
                      <td>{r.no2?.toFixed(1) ?? '—'}</td>
                      <td>{r.co?.toFixed(2) ?? '—'}</td>
                      <td>{r.ph?.toFixed(2) ?? '—'}</td>
                      <td>{r.turbidity?.toFixed(1) ?? '—'}</td>
                      <td style={{ fontSize: 12, color: 'var(--muted)' }}>
                        {r.wind_speed?.toFixed(1)} m/s {r.wind_direction?.toFixed(0)}°
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
