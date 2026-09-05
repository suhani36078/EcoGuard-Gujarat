import { useState } from 'react'
import { createReport } from '../services/queries'
import { MapPin, Camera, AlertTriangle, CheckCircle, Clock, Loader } from 'lucide-react'

const CATEGORIES = [
  { value: 'smoke', label: '💨 Smoke / Emissions', desc: 'Factory or vehicle smoke' },
  { value: 'water', label: '💧 Water Contamination', desc: 'Discharge, discoloration' },
  { value: 'garbage', label: '🗑️ Garbage Dumping', desc: 'Illegal waste disposal' },
  { value: 'noise', label: '🔊 Excessive Noise', desc: 'Industrial or traffic noise' },
  { value: 'industrial', label: '🏭 Industrial Pollution', desc: 'Chemical/industrial emissions' },
  { value: 'burning', label: '🔥 Waste Burning', desc: 'Open burning of waste' },
]

const SEVERITIES = [
  { value: 'LOW', label: 'Low', color: 'var(--green)', desc: 'Minor, not immediately harmful' },
  { value: 'MODERATE', label: 'Moderate', color: 'var(--yellow)', desc: 'Concerning, needs attention' },
  { value: 'HIGH', label: 'High', color: 'var(--orange)', desc: 'Serious, urgent action needed' },
  { value: 'CRITICAL', label: 'Critical', color: 'var(--red)', desc: 'Emergency, immediate response required' },
]

const GUJARAT_DISTRICTS = [
  'Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Gandhinagar', 'Bhavnagar',
  'Jamnagar', 'Junagadh', 'Anand', 'Bharuch', 'Vapi / Valsad', 'Navsari',
  'Morbi', 'Mehsana', 'Patan', 'Banaskantha', 'Sabarkantha', 'Dahod',
  'Panchmahal', 'Kheda', 'Kutch', 'Surendranagar', 'Amreli', 'Botad',
  'Narmada', 'Tapi', 'Dang', 'Chhota Udaipur',
]

const STATUS_FLOW = [
  { key: 'submitted', label: 'Submitted', icon: '📋' },
  { key: 'under_review', label: 'Under Review', icon: '🔍' },
  { key: 'assigned', label: 'Assigned', icon: '👤' },
  { key: 'resolved', label: 'Resolved', icon: '✅' },
]

export default function CitizenReportPage() {
  const [step, setStep] = useState<'form' | 'success'>('form')
  const [submittedReport, setSubmittedReport] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [form, setForm] = useState({
    category: '',
    location: '',
    district: '',
    description: '',
    severity: 'MODERATE',
    latitude: '',
    longitude: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.category || !form.location) {
      setError('Please select a category and provide a location.')
      return
    }
    setError('')
    setLoading(true)
    try {
      const report = await createReport({
        category: form.category,
        location: form.location,
        district: form.district || undefined,
        description: form.description || undefined,
        severity: form.severity,
        latitude: form.latitude ? parseFloat(form.latitude) : undefined,
        longitude: form.longitude ? parseFloat(form.longitude) : undefined,
      })
      setSubmittedReport(report)
      setStep('success')
    } catch (err) {
      setError('Failed to submit report. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setStep('form')
    setSubmittedReport(null)
    setForm({ category: '', location: '', district: '', description: '', severity: 'MODERATE', latitude: '', longitude: '' })
  }

  if (step === 'success' && submittedReport) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 600, margin: '0 auto' }}>
        <div>
          <h1 className="page-heading">Report Submitted!</h1>
          <p className="page-sub">Thank you for helping protect Gujarat's environment.</p>
        </div>

        <div className="card" style={{ textAlign: 'center', padding: '40px 20px' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
          <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Report #{submittedReport.id} Submitted</h2>
          <p style={{ color: 'var(--muted)', marginBottom: 24 }}>
            Your report has been received and will be reviewed by the environmental monitoring team.
          </p>

          {/* Status tracker */}
          <div style={{ display: 'flex', gap: 0, justifyContent: 'center', marginBottom: 32, flexWrap: 'wrap' }}>
            {STATUS_FLOW.map((s, i) => (
              <div key={s.key} style={{ display: 'flex', alignItems: 'center' }}>
                <div style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
                  opacity: s.key === 'submitted' ? 1 : 0.4,
                }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: '50%',
                    background: s.key === 'submitted' ? 'var(--emerald)' : 'var(--surface2)',
                    border: `2px solid ${s.key === 'submitted' ? 'var(--emerald)' : 'var(--border2)'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 18,
                  }}>
                    {s.icon}
                  </div>
                  <span style={{ fontSize: 10, color: 'var(--muted)', whiteSpace: 'nowrap' }}>{s.label}</span>
                </div>
                {i < STATUS_FLOW.length - 1 && (
                  <div style={{ width: 40, height: 2, background: 'var(--border)', margin: '0 4px', marginBottom: 16 }} />
                )}
              </div>
            ))}
          </div>

          <div style={{ background: 'var(--surface2)', borderRadius: 12, padding: 20, textAlign: 'left', marginBottom: 24 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div>
                <div style={{ fontSize: 10, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Category</div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{submittedReport.category}</div>
              </div>
              <div>
                <div style={{ fontSize: 10, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Severity</div>
                <span className={`badge badge-${submittedReport.severity?.toLowerCase()}`}>{submittedReport.severity}</span>
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <div style={{ fontSize: 10, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Location</div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{submittedReport.location}</div>
              </div>
            </div>
          </div>

          <button className="btn btn-primary btn-lg" onClick={reset} style={{ width: '100%', justifyContent: 'center' }}>
            Submit Another Report
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 700, margin: '0 auto' }}>
      <div>
        <h1 className="page-heading">Report Pollution</h1>
        <p className="page-sub">Help protect Gujarat's environment by reporting pollution incidents.</p>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {/* Category Selection */}
        <div className="card">
          <div className="card-title">Pollution Category *</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 10 }}>
            {CATEGORIES.map(cat => (
              <div
                key={cat.value}
                onClick={() => setForm(f => ({ ...f, category: cat.value }))}
                style={{
                  padding: '12px 16px',
                  borderRadius: 10,
                  border: `2px solid ${form.category === cat.value ? 'var(--emerald)' : 'var(--border2)'}`,
                  background: form.category === cat.value ? 'rgba(37,99,235,0.08)' : 'var(--surface2)',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 3 }}>{cat.label}</div>
                <div style={{ fontSize: 11, color: 'var(--muted)' }}>{cat.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Location */}
        <div className="card">
          <div className="card-title"><MapPin size={14} /> Location Details *</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="form-group" style={{ gridColumn: '1 / -1' }}>
              <label>Specific Location / Address *</label>
              <input
                placeholder="E.g., Near Vatva GIDC Gate 2, Ahmedabad"
                value={form.location}
                onChange={e => setForm(f => ({ ...f, location: e.target.value }))}
                required
              />
            </div>
            <div className="form-group">
              <label>District</label>
              <select value={form.district} onChange={e => setForm(f => ({ ...f, district: e.target.value }))}>
                <option value="">Select District</option>
                {GUJARAT_DISTRICTS.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Coordinates (optional)</label>
              <div style={{ display: 'flex', gap: 8 }}>
                <input
                  placeholder="Latitude"
                  type="number"
                  step="any"
                  value={form.latitude}
                  onChange={e => setForm(f => ({ ...f, latitude: e.target.value }))}
                />
                <input
                  placeholder="Longitude"
                  type="number"
                  step="any"
                  value={form.longitude}
                  onChange={e => setForm(f => ({ ...f, longitude: e.target.value }))}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Description & Severity */}
        <div className="card">
          <div className="card-title">Incident Details</div>
          <div className="form-group">
            <label>Description</label>
            <textarea
              placeholder="Describe what you observed: smell, color, visibility, duration, any immediate effects on people/animals…"
              value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              rows={4}
            />
          </div>

          <div>
            <label style={{ marginBottom: 10, display: 'block' }}>Severity Level *</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
              {SEVERITIES.map(sev => (
                <div
                  key={sev.value}
                  onClick={() => setForm(f => ({ ...f, severity: sev.value }))}
                  style={{
                    padding: '10px',
                    borderRadius: 8,
                    border: `2px solid ${form.severity === sev.value ? sev.color : 'var(--border2)'}`,
                    background: form.severity === sev.value ? sev.color + '15' : 'var(--surface2)',
                    cursor: 'pointer',
                    textAlign: 'center',
                    transition: 'all 0.15s',
                  }}
                >
                  <div style={{ fontSize: 12, fontWeight: 700, color: sev.color }}>{sev.label}</div>
                  <div style={{ fontSize: 10, color: 'var(--muted)', marginTop: 2 }}>{sev.desc}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {error && <div className="error-box">{error}</div>}

        <button
          className="btn btn-primary btn-lg"
          type="submit"
          disabled={loading || !form.category || !form.location}
          style={{ justifyContent: 'center' }}
        >
          {loading ? (
            <><Loader size={15} style={{ animation: 'spin 1s linear infinite' }} />Submitting…</>
          ) : (
            'Submit Pollution Report'
          )}
        </button>

        <div style={{ fontSize: 11, color: 'var(--muted)', textAlign: 'center' }}>
          Reports are reviewed by GPCB-affiliated environmental officers. Data is anonymized.
        </div>
      </form>
    </div>
  )
}
