import { useState } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import FactoriesPage from './pages/FactoriesPage'
import ViolationsPage from './pages/ViolationsPage'
import AlertsPage from './pages/AlertsPage'
import AnomaliesPage from './pages/AnomaliesPage'
import IncidentsPage from './pages/IncidentsPage'
import ForecastsPage from './pages/ForecastsPage'
import RiskPage from './pages/RiskPage'
import CommunityRiskPage from './pages/CommunityRiskPage'
import AgentsPage from './pages/AgentsPage'
import MapPage from './pages/MapPage'
import DistrictsPage from './pages/DistrictsPage'
import HotspotsPage from './pages/HotspotsPage'
import CitizenReportPage from './pages/CitizenReportPage'
import ChatPage from './pages/ChatPage'
import SimulatorPage from './pages/SimulatorPage'
import AdminPage from './pages/AdminPage'

const PAGE_TITLES: Record<string, { title: string; subtitle?: string }> = {
  '/':            { title: 'Overview Dashboard',    subtitle: 'Gujarat pollution intelligence summary' },
  '/map':         { title: 'Gujarat Pollution Map', subtitle: 'Interactive district-level visualization' },
  '/districts':   { title: 'District Intelligence', subtitle: 'City and district pollution profiles' },
  '/hotspots':    { title: 'Pollution Hotspots',    subtitle: 'High-risk zones requiring intervention' },
  '/factories':   { title: 'Industrial Zones',      subtitle: 'Factory and facility monitoring' },
  '/alerts':      { title: 'Alerts',                subtitle: 'Active notifications and warnings' },
  '/violations':  { title: 'Violations',            subtitle: 'Regulatory limit breaches' },
  '/anomalies':   { title: 'Anomalies',             subtitle: 'Statistical outliers and unusual patterns' },
  '/incidents':   { title: 'Incidents',             subtitle: 'Escalation management' },
  '/predictions': { title: 'Predictions & Forecast',subtitle: 'AI-powered pollution risk forecast' },
  '/simulator':   { title: 'What-If Simulator',     subtitle: 'Intervention impact analysis' },
  '/forecasts':   { title: 'ML Forecasts',          subtitle: '24h sensor-level predictions' },
  '/risk':        { title: 'Risk Scores',           subtitle: 'Composite facility risk analysis' },
  '/community':   { title: 'Community Risk',        subtitle: 'Population exposure assessment' },
  '/agents':      { title: 'AI Agent Pipeline',     subtitle: 'Multi-agent intelligence system' },
  '/report':      { title: 'Report Pollution',      subtitle: 'Citizen pollution reporting' },
  '/chat':        { title: 'Ask EcoGuard',           subtitle: 'AI pollution intelligence assistant' },
  '/admin':       { title: 'Admin Dashboard',       subtitle: 'Platform administration and analytics' },
}

function AppShell({ username, role, onLogout }: { username: string; role: string; onLogout: () => void }) {
  const location = useLocation()
  const pageInfo = PAGE_TITLES[location.pathname] ?? { title: 'EcoGuard Gujarat', subtitle: 'Gujarat Pollution Intelligence' }

  return (
    <div className="app-shell">
      <Sidebar username={username} role={role} onLogout={onLogout} />
      <div className="main-area">
        <Topbar title={pageInfo.title} subtitle={pageInfo.subtitle} />
        <div className="page-content">
          <Routes>
            <Route path="/"            element={<DashboardPage />} />
            <Route path="/map"         element={<MapPage />} />
            <Route path="/districts"   element={<DistrictsPage />} />
            <Route path="/hotspots"    element={<HotspotsPage />} />
            <Route path="/factories"   element={<FactoriesPage />} />
            <Route path="/violations"  element={<ViolationsPage />} />
            <Route path="/alerts"      element={<AlertsPage />} />
            <Route path="/anomalies"   element={<AnomaliesPage />} />
            <Route path="/incidents"   element={<IncidentsPage />} />
            <Route path="/predictions" element={<SimulatorPage />} />
            <Route path="/simulator"   element={<SimulatorPage />} />
            <Route path="/forecasts"   element={<ForecastsPage />} />
            <Route path="/risk"        element={<RiskPage />} />
            <Route path="/community"   element={<CommunityRiskPage />} />
            <Route path="/agents"      element={<AgentsPage />} />
            <Route path="/report"      element={<CitizenReportPage />} />
            <Route path="/chat"        element={<ChatPage />} />
            <Route path="/admin"       element={<AdminPage />} />
            <Route path="*"            element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [username, setUsername] = useState(() => localStorage.getItem('eco_username') || '')
  const [role, setRole] = useState(() => localStorage.getItem('eco_role') || '')

  const handleLogin = (t: string, u: string, r: string) => {
    localStorage.setItem('token', t)
    localStorage.setItem('eco_username', u)
    localStorage.setItem('eco_role', r)
    setToken(t)
    setUsername(u)
    setRole(r)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('eco_username')
    localStorage.removeItem('eco_role')
    setToken(null)
    setUsername('')
    setRole('')
  }

  if (!token) {
    return <LoginPage onLogin={handleLogin} />
  }

  return <AppShell username={username} role={role} onLogout={handleLogout} />
}
