import { useState } from 'react'
import { useQuery } from 'react-query'
import { getFactories, getForecasts } from '../services/queries'
import { ForecastChart } from '../components/Charts'
import { fmtDate, fmtNum, paramLabel, paramUnit } from '../utils/helpers'

export default function ForecastsPage() {
  const [selectedFactory, setSelectedFactory] = useState('F007')

  const { data: factories } = useQuery('factories', getFactories)
  const { data: forecasts, isLoading } = useQuery(
    ['forecasts', selectedFactory],
    () => getForecasts(selectedFactory),
    { enabled: !!selectedFactory },
  )

  return (
    <div>
      <h1 className="page-heading">Forecasts</h1>
      <p className="page-sub">24h pollution predictions using ML models (LSTM + Linear Regression)</p>

      <div style={{ marginBottom: 20 }}>
        <select
          value={selectedFactory}
          onChange={(e) => setSelectedFactory(e.target.value)}
          style={{ maxWidth: 300 }}
        >
          {(factories ?? []).map((f) => (
            <option key={f.id} value={f.id}>{f.id} — {f.name}</option>
          ))}
        </select>
      </div>

      {isLoading && <div className="loading">Loading forecasts…</div>}

      {forecasts && forecasts.length > 0 && (
        <>
          <ForecastChart forecasts={forecasts} factoryId={selectedFactory} />

          <div style={{ marginTop: 20 }} className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Parameter</th>
                  <th>Forecast Time</th>
                  <th>Predicted Value</th>
                  <th>Confidence</th>
                  <th>Model</th>
                </tr>
              </thead>
              <tbody>
                {forecasts.slice(0, 48).map((f) => (
                  <tr key={f.id}>
                    <td style={{ color: 'var(--muted)', fontSize: 12 }}>{f.id}</td>
                    <td>
                      <span style={{ fontWeight: 600 }}>{paramLabel(f.parameter)}</span>
                      <span style={{ color: 'var(--muted)', fontSize: 11, marginLeft: 4 }}>{paramUnit(f.parameter)}</span>
                    </td>
                    <td style={{ color: 'var(--muted)', fontSize: 12 }}>{fmtDate(f.forecast_time)}</td>
                    <td style={{ fontWeight: 600, color: 'var(--accent2)' }}>{fmtNum(f.predicted_value)}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{
                          width: 60, height: 6, background: 'var(--border)', borderRadius: 3, overflow: 'hidden',
                        }}>
                          <div style={{
                            width: `${(f.confidence ?? 0) * 100}%`, height: '100%',
                            background: (f.confidence ?? 0) > 0.7 ? 'var(--green)' : 'var(--yellow)',
                          }} />
                        </div>
                        <span style={{ fontSize: 12 }}>{fmtNum((f.confidence ?? 0) * 100, 0)}%</span>
                      </div>
                    </td>
                    <td style={{ color: 'var(--muted)', fontSize: 12 }}>{f.model_used}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {forecasts && forecasts.length === 0 && (
        <div className="card" style={{ textAlign: 'center', color: 'var(--muted)' }}>
          No forecasts available for {selectedFactory}
        </div>
      )}
    </div>
  )
}
