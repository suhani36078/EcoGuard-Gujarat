import { useState } from 'react'
import { login } from '../services/queries'
import { Shield, Activity, Map, TrendingUp, MessageSquare, Eye, EyeOff } from 'lucide-react'

interface LoginPageProps {
  onLogin: (token: string, username: string, role: string) => void
}

const DEMO_CREDS = [
  { username: 'admin',     password: 'admin123',     role: 'Administrator' },
  { username: 'regulator', password: 'regulator123', role: 'Analyst' },
  { username: 'officer',   password: 'officer123',   role: 'Officer' },
  { username: 'viewer',    password: 'viewer123',    role: 'Citizen' },
]

const BRAND = 'ECOGUARD GUJARAT'

const FEATURES = [
  { icon: Map, title: 'Interactive Gujarat Map', desc: 'Real-time pollution heatmaps across 26 districts' },
  { icon: Activity, title: 'Multi-Pollutant Monitoring', desc: 'Air, water, noise, industrial & waste tracking' },
  { icon: TrendingUp, title: 'AI Predictions', desc: 'ML-powered pollution risk forecasting' },
  { icon: Shield, title: 'Smart Alerts', desc: 'Intelligent early warning for critical pollution events' },
  { icon: MessageSquare, title: 'Citizen Assistant', desc: 'IBM Granite-powered pollution Q&A' },
]

export default function LoginPage({ onLogin }: LoginPageProps) {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    // Client-side demo bypass — works without backend
    const demo = DEMO_CREDS.find(d => d.username === username && d.password === password)
    if (demo) {
      const fakeToken = `demo-${demo.username}-${Date.now()}`
      localStorage.setItem('token', fakeToken)
      setLoading(false)
      onLogin(fakeToken, demo.username, demo.role)
      return
    }

    try {
      const resp = await login(username, password)
      localStorage.setItem('token', resp.access_token)
      onLogin(resp.access_token, resp.username, resp.role)
    } catch {
      setError('Invalid credentials. Use a demo account below.')
    } finally {
      setLoading(false)
    }
  }

  const fillCred = (u: string, p: string) => {
    setUsername(u)
    setPassword(p)
    setError('')
  }

  return (
    <div className="login-page">
      {/* Left panel */}
      <div className="login-left">
        <div style={{ maxWidth: 520, textAlign: 'center' }}>
          {/* Logo */}
          <div style={{
            width: 72, height: 72,
            background: 'linear-gradient(135deg, var(--emerald), var(--teal))',
            borderRadius: 18,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 36, margin: '0 auto 24px',
            boxShadow: '0 16px 48px rgba(37,99,235,0.25)',
          }}>
            🌐
          </div>

          <div style={{
            fontFamily: "'Space Grotesk', 'Inter', sans-serif",
            fontSize: 36, fontWeight: 800,
            letterSpacing: '-0.02em',
            background: 'linear-gradient(135deg, var(--text) 0%, var(--emerald3) 60%, var(--teal2) 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            marginBottom: 8,
          }}>
            {BRAND}
          </div>

          <div style={{ fontSize: 16, color: 'var(--text2)', marginBottom: 6, fontWeight: 500 }}>
            Gujarat Pollution Intelligence Platform
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 48 }}>
            Monitor · Understand · Predict · Act
          </div>

          {/* Features list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16, textAlign: 'left' }}>
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                <div style={{
                  width: 38, height: 38, borderRadius: 10, flexShrink: 0,
                  background: 'rgba(37,99,235,0.1)',
                  border: '1px solid rgba(37,99,235,0.2)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: 'var(--emerald2)',
                }}>
                  <Icon size={18} />
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 2 }}>{title}</div>
                  <div style={{ fontSize: 11, color: 'var(--muted)' }}>{desc}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Data disclaimer */}
          <div style={{
            marginTop: 40, padding: '12px 16px',
            background: 'rgba(168,85,247,0.08)',
            border: '1px solid rgba(168,85,247,0.2)',
            borderRadius: 8, fontSize: 11, color: 'var(--muted)',
            textAlign: 'left',
          }}>
            <span style={{ color: 'var(--purple)', fontWeight: 700 }}>DEMO PLATFORM</span>
            {' '}— This platform uses simulated/estimated data. Not real-time official government measurements.
            Architecture is ready for live sensor integration.
          </div>
        </div>
      </div>

      {/* Right panel — Login form */}
      <div className="login-right">
        <div className="login-card">
          {/* Mobile logo */}
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <div style={{
              width: 52, height: 52,
              background: 'linear-gradient(135deg, var(--emerald), var(--teal))',
              borderRadius: 14, display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 26, margin: '0 auto 16px',
              boxShadow: '0 8px 24px rgba(37,99,235,0.25)',
            }}>
              🌐
            </div>
            <h1 style={{
              fontFamily: "'Space Grotesk', 'Inter', sans-serif",
              fontSize: 24, fontWeight: 800, marginBottom: 4,
              background: 'linear-gradient(135deg, var(--text), var(--emerald3))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              Sign In
            </h1>
            <p style={{ color: 'var(--muted)', fontSize: 12 }}>
              EcoGuard Gujarat — Pollution Intelligence
            </p>
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <label>Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                autoFocus
              />
            </div>

            <div>
              <label>Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  style={{ paddingRight: 40 }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--muted)', padding: 0,
                  }}
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="error-box" style={{ fontSize: 12, padding: '10px 14px' }}>
                {error}
              </div>
            )}

            <button
              className="btn btn-primary"
              type="submit"
              disabled={loading}
              style={{ width: '100%', justifyContent: 'center', padding: '11px' }}
            >
              {loading ? (
                <><span className="loading-spinner" style={{ width: 16, height: 16 }} />Signing in…</>
              ) : (
                'Sign In to Platform'
              )}
            </button>
          </form>

          {/* Demo credentials */}
          <div style={{ marginTop: 24 }}>
            <div style={{
              fontSize: 10, color: 'var(--muted)',
              textTransform: 'uppercase', letterSpacing: '0.08em',
              marginBottom: 10, fontWeight: 700,
            }}>
              Demo Accounts
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
              {DEMO_CREDS.map(({ username: u, password: p, role }) => (
                <button
                  key={u}
                  type="button"
                  onClick={() => fillCred(u, p)}
                  style={{
                    background: 'var(--surface2)',
                    border: '1px solid var(--border2)',
                    borderRadius: 8,
                    padding: '8px 10px',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.15s',
                  }}
                  onMouseOver={(e) => (e.currentTarget.style.borderColor = 'var(--emerald)')}
                  onMouseOut={(e) => (e.currentTarget.style.borderColor = 'var(--border2)')}
                >
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text2)' }}>{u}</div>
                  <div style={{ fontSize: 10, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{role}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
