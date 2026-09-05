import api from './api'
import type {
  Factory, SensorReading, Violation, Anomaly, Alert,
  Incident, Forecast, RiskScore, CommunityRisk, DashboardSummary,
  AgentContext, TokenResponse,
} from './types'

// ── Auth ───────────────────────────────────────────────────────────────────

export const login = async (username: string, password: string): Promise<TokenResponse> => {
  const { data } = await api.post<TokenResponse>('/auth/login', { username, password })
  return data
}

// ── Factories ─────────────────────────────────────────────────────────────

export const getFactories = async (): Promise<Factory[]> => {
  const { data } = await api.get<Factory[]>('/factories')
  return data
}

export const getFactory = async (id: string): Promise<Factory> => {
  const { data } = await api.get<Factory>(`/factories/${id}`)
  return data
}

// ── Readings ──────────────────────────────────────────────────────────────

export const getReadings = async (factoryId: string, limit = 100): Promise<SensorReading[]> => {
  const { data } = await api.get<SensorReading[]>(`/readings/${factoryId}`, {
    params: { limit },
  })
  return data
}

// ── Violations ────────────────────────────────────────────────────────────

export const getViolations = async (factoryId?: string): Promise<Violation[]> => {
  const url = factoryId ? `/violations/${factoryId}` : '/violations'
  const { data } = await api.get<Violation[]>(url)
  return data
}

// ── Anomalies ─────────────────────────────────────────────────────────────

export const getAnomalies = async (): Promise<Anomaly[]> => {
  const { data } = await api.get<Anomaly[]>('/anomalies')
  return data
}

// ── Alerts ────────────────────────────────────────────────────────────────

export const getAlerts = async (): Promise<Alert[]> => {
  const { data } = await api.get<Alert[]>('/alerts')
  return data
}

export const acknowledgeAlert = async (id: number): Promise<Alert> => {
  const { data } = await api.post<Alert>(`/alerts/${id}/acknowledge`)
  return data
}

// ── Incidents ─────────────────────────────────────────────────────────────

export const getIncidents = async (): Promise<Incident[]> => {
  const { data } = await api.get<Incident[]>('/incidents')
  return data
}

export const takeIncidentAction = async (
  id: number,
  action: string,
  performedBy: string,
  note?: string,
): Promise<Incident> => {
  const { data } = await api.post<Incident>(`/incidents/${id}/action`, {
    action,
    performed_by: performedBy,
    note,
  })
  return data
}

// ── Forecasts ─────────────────────────────────────────────────────────────

export const getForecasts = async (factoryId: string): Promise<Forecast[]> => {
  const { data } = await api.get<Forecast[]>(`/forecasts/${factoryId}`)
  return data
}

// ── Risk Scores ───────────────────────────────────────────────────────────

export const getRiskScores = async (): Promise<RiskScore[]> => {
  const { data } = await api.get<RiskScore[]>('/risk-scores')
  return data
}

export const getFactoryRiskScore = async (factoryId: string): Promise<RiskScore> => {
  const { data } = await api.get<RiskScore>(`/risk-scores/${factoryId}`)
  return data
}

// ── Community Risk ────────────────────────────────────────────────────────

export const getCommunityRisk = async (): Promise<CommunityRisk[]> => {
  const { data } = await api.get<CommunityRisk[]>('/community-risk')
  return data
}

// ── Dashboard ─────────────────────────────────────────────────────────────

export const getDashboardSummary = async (): Promise<DashboardSummary> => {
  const { data } = await api.get<DashboardSummary>('/dashboard/summary')
  return data
}

// ── Agents ────────────────────────────────────────────────────────────────

export const runAgentPipeline = async (params: {
  factory_id: string
  parameter?: string
  value?: number
  configured_limit?: number
}): Promise<AgentContext> => {
  const { data } = await api.post<AgentContext>('/agents/process', params)
  return data
}

// ── Districts ──────────────────────────────────────────────────────────────

export const getDistricts = async () => {
  const { data } = await api.get('/districts')
  return data
}

export const getDistrictSummary = async () => {
  const { data } = await api.get('/districts/summary/state')
  return data
}

export const getDistrict = async (code: string) => {
  const { data } = await api.get(`/districts/${code}`)
  return data
}

// ── Hotspots ──────────────────────────────────────────────────────────────

export const getHotspots = async (params?: { district?: string; pollution_type?: string; severity?: string }) => {
  const { data } = await api.get('/hotspots', { params })
  return data
}

export const getHotspotSummary = async () => {
  const { data } = await api.get('/hotspots/summary')
  return data
}

// ── Citizen Reports ───────────────────────────────────────────────────────

export const createReport = async (report: {
  category: string; location: string; district?: string;
  latitude?: number; longitude?: number; description?: string;
  severity?: string; image_url?: string;
}) => {
  const { data } = await api.post('/citizen-reports', report)
  return data
}

export const getReports = async (params?: { status?: string; category?: string }) => {
  const { data } = await api.get('/citizen-reports', { params })
  return data
}

export const getReportsSummary = async () => {
  const { data } = await api.get('/citizen-reports/summary')
  return data
}

export const updateReportStatus = async (id: number, status: string, assigned_to?: string, resolution_note?: string) => {
  const { data } = await api.patch(`/citizen-reports/${id}/status`, { status, assigned_to, resolution_note })
  return data
}

// ── Pollution Index ───────────────────────────────────────────────────────

export const getPollutionIndex = async () => {
  const { data } = await api.get('/pollution-index/current')
  return data
}

export const getPollutionIndexHistory = async () => {
  const { data } = await api.get('/pollution-index/history')
  return data
}

// ── Predictions ───────────────────────────────────────────────────────────

export const predictDistrict = async (district: string, days: number = 7) => {
  const { data } = await api.post('/predictions/district', { district, days_ahead: days })
  return data
}

export const getHotspotRisk = async () => {
  const { data } = await api.get('/predictions/hotspot-risk')
  return data
}

export const whatIfAnalysis = async (params: {
  district?: string;
  traffic_reduction_pct?: number;
  industrial_reduction_pct?: number;
  waste_reduction_pct?: number;
  green_cover_increase_pct?: number;
  public_transport_adoption_pct?: number;
}) => {
  const { data } = await api.post('/predictions/what-if', params)
  return data
}

// ── Chat ─────────────────────────────────────────────────────────────────

export const sendChatMessage = async (message: string, session_id?: string) => {
  const { data } = await api.post('/chat/message', { message, session_id })
  return data
}
