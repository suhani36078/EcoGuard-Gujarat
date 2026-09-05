// Central API types for the Pollution Intelligence Platform

export interface Factory {
  id: string
  name: string
  location: string
  latitude: number
  longitude: number
  type?: string
  status?: string
  created_at?: string
}

export interface SensorReading {
  id: number
  factory_id: string
  timestamp: string
  pm25?: number
  pm10?: number
  so2?: number
  no2?: number
  co?: number
  temperature?: number
  humidity?: number
  wind_speed?: number
  wind_direction?: number
  ph?: number
  turbidity?: number
  chemical_level?: number
  production_activity?: number
}

export interface Violation {
  id: number
  factory_id: string
  parameter: string
  value: number
  limit_value: number
  exceedance_percent?: number
  severity?: string
  status?: string
  detected_at?: string
  resolved_at?: string
}

export interface Anomaly {
  id: number
  factory_id: string
  parameter?: string
  anomaly_score?: number
  detected_at?: string
  description?: string
  status?: string
}

export interface Alert {
  id: number
  factory_id: string
  violation_id?: number
  severity?: string
  message?: string
  recipients?: string
  status?: string
  created_at?: string
  acknowledged_at?: string
  resolved_at?: string
}

export interface Incident {
  id: number
  factory_id: string
  title: string
  description?: string
  status?: string
  severity?: string
  created_at?: string
  resolved_at?: string
  assigned_to?: string
}

export interface Forecast {
  id: number
  factory_id: string
  parameter?: string
  predicted_value?: number
  forecast_time?: string
  confidence?: number
  model_used?: string
}

export interface RiskScore {
  id: number
  factory_id: string
  overall_score?: number
  risk_level?: string
  components?: Record<string, number>
  calculated_at?: string
}

export interface CommunityRisk {
  factory_id: string
  factory_name: string
  location: string
  risk_level: string
  overall_score: number
  wind_direction?: number
  wind_speed?: number
  nearby_population?: string
  health_advisory?: string
  affected_area_km?: number
}

export interface DashboardSummary {
  total_factories: number
  active_violations: number
  critical_violations: number
  open_anomalies: number
  pending_alerts: number
  open_incidents: number
  factories_at_risk: number
  recent_readings_count: number
  violations_by_severity: Record<string, number>
  top_violating_factories: Array<{ factory_id: string; violation_count: number }>
  risk_distribution: Record<string, number>
}

export interface AgentContext {
  event_id?: string
  factory_id: string
  timestamp?: string
  parameter?: string
  value?: number
  configured_limit?: number
  location?: string
  severity?: string
  current_status?: string
  anomaly_score?: number
  violation_status?: string
  predicted_value?: number
  risk_score?: number
  community_risk?: string
  evidence?: Record<string, unknown>
  combined_assessment?: string
  alert_level?: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  role: string
  username: string
}
