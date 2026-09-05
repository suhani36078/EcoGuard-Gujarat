import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Factory, AlertTriangle, Activity,
  ShieldAlert, TrendingUp, Users, Cpu, LogOut, BarChart2,
  Map, MessageSquare, Zap, FileText, FlaskConical, Bell,
  Target, Settings,
} from 'lucide-react'

interface SidebarProps {
  username?: string
  role?: string
  onLogout: () => void
}

const NAV_MONITOR = [
  { to: '/',          label: 'Overview',       icon: LayoutDashboard },
  { to: '/map',       label: 'Gujarat Map',    icon: Map },
  { to: '/districts', label: 'Districts',      icon: BarChart2 },
  { to: '/hotspots',  label: 'Hotspots',       icon: Target },
]

const NAV_POLLUTION = [
  { to: '/factories',   label: 'Industrial Zones', icon: Factory },
  { to: '/alerts',      label: 'Alerts',           icon: Bell },
  { to: '/violations',  label: 'Violations',       icon: AlertTriangle },
  { to: '/anomalies',   label: 'Anomalies',        icon: Activity },
  { to: '/incidents',   label: 'Incidents',        icon: ShieldAlert },
]

const NAV_INTELLIGENCE = [
  { to: '/predictions', label: 'Predictions',      icon: TrendingUp },
  { to: '/simulator',   label: 'What-If?',         icon: FlaskConical },
  { to: '/forecasts',   label: 'Forecasts',        icon: Zap },
  { to: '/risk',        label: 'Risk Scores',      icon: BarChart2 },
  { to: '/community',   label: 'Community Risk',   icon: Users },
  { to: '/agents',      label: 'AI Agents',        icon: Cpu },
]

const NAV_CITIZEN = [
  { to: '/report',    label: 'Report Pollution',  icon: FileText },
  { to: '/chat',      label: 'Ask EcoGuard',       icon: MessageSquare },
]

export default function Sidebar({ username, role, onLogout }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">🌐</div>
          <div>
            <div className="sidebar-brand-title">ECOGUARD</div>
          </div>
        </div>
        <div className="sidebar-brand-sub">EcoGuard Gujarat</div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-label">Monitoring</div>
        {NAV_MONITOR.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          >
            <Icon size={15} />
            <span>{label}</span>
          </NavLink>
        ))}

        <div className="nav-section-label">Pollution Data</div>
        {NAV_POLLUTION.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          >
            <Icon size={15} />
            <span>{label}</span>
          </NavLink>
        ))}

        <div className="nav-section-label">Intelligence</div>
        {NAV_INTELLIGENCE.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          >
            <Icon size={15} />
            <span>{label}</span>
          </NavLink>
        ))}

        <div className="nav-section-label">Citizen</div>
        {NAV_CITIZEN.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          >
            <Icon size={15} />
            <span>{label}</span>
          </NavLink>
        ))}

        {(role === 'admin' || role === 'regulator') && (
          <>
            <div className="nav-section-label">Admin</div>
            <NavLink
              to="/admin"
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            >
              <Settings size={15} />
              <span>Admin Panel</span>
            </NavLink>
          </>
        )}
      </nav>

      <div style={{ padding: '12px 8px', borderTop: '1px solid var(--border)' }}>
        {username && (
          <div style={{
            padding: '8px 10px', marginBottom: '4px',
            background: 'var(--surface2)', borderRadius: 'var(--radius)',
            fontSize: '11px', color: 'var(--muted)',
          }}>
            <div style={{ fontWeight: 600, color: 'var(--text2)', fontSize: '12px' }}>{username}</div>
            <div style={{ textTransform: 'uppercase', letterSpacing: '0.06em', fontSize: '9px' }}>{role || 'viewer'}</div>
          </div>
        )}
        <button
          className="nav-link"
          style={{ width: '100%', background: 'none', border: 'none', color: 'var(--muted)' }}
          onClick={onLogout}
        >
          <LogOut size={15} />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  )
}
