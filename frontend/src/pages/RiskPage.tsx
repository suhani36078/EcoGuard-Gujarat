import { useQuery } from 'react-query'
import { getRiskScores, getFactories } from '../services/queries'
import { riskLevelBadgeClass, fmtDate, fmtNum } from '../utils/helpers'
import { RiskBarChart } from '../components/Charts'

export default function RiskPage() {
  const { data: scores, isLoading } = useQuery('risk-scores', getRiskScores, {
    refetchInterval: 60000,
  })
  const { data: factories } = useQuery('factories', getFactories)

  if (isLoading) return <div className="loading">Loading risk scores…</div>

  const factoryName = (id: string) => factories?.find((f) => f.id === id)?.name ?? id

  return (
    <div>
      <h1 className="page-heading">Factory Risk Scores</h1>
      <p className="page-sub">Composite risk assessment: air quality + water quality + violation history + community exposure</p>

      {scores && <RiskBarChart scores={scores} />}

      <div className="table-wrap" style={{ marginTop: 20 }}>
        <table>
          <thead>
            <tr>
              <th>Factory</th>
              <th>Name</th>
              <th>Overall Score</th>
              <th>Risk Level</th>
              <th>Air Quality</th>
              <th>Water Quality</th>
              <th>Violation History</th>
              <th>Community Exposure</th>
              <th>Calculated At</th>
            </tr>
          </thead>
          <tbody>
            {(scores ?? []).map((s) => (
              <tr key={s.id}>
                <td><code style={{ color: 'var(--accent2)', fontSize: 12 }}>{s.factory_id}</code></td>
                <td style={{ fontSize: 12, color: 'var(--muted)' }}>{factoryName(s.factory_id)}</td>
                <td>
                  <span style={{
                    fontWeight: 700, fontSize: 18,
                    color: (s.overall_score ?? 0) >= 75 ? 'var(--red)'
                         : (s.overall_score ?? 0) >= 50 ? 'var(--orange)'
                         : 'var(--green)',
                  }}>
                    {fmtNum(s.overall_score, 0)}
                  </span>
                  <span style={{ color: 'var(--muted)', fontSize: 12 }}>/100</span>
                </td>
                <td><span className={riskLevelBadgeClass(s.risk_level)}>{s.risk_level}</span></td>
                <td>{fmtNum(s.components?.air_quality, 1)}</td>
                <td>{fmtNum(s.components?.water_quality, 1)}</td>
                <td>{fmtNum(s.components?.violation_history, 1)}</td>
                <td>{fmtNum(s.components?.community_exposure, 1)}</td>
                <td style={{ color: 'var(--muted)', fontSize: 12 }}>{fmtDate(s.calculated_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
