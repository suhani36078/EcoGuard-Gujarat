// Utility helpers

export function severityColor(sev?: string | null): string {
  switch (sev?.toUpperCase()) {
    case 'CRITICAL': return 'var(--red)'
    case 'HIGH':     return 'var(--orange)'
    case 'MEDIUM':   return 'var(--yellow)'
    case 'LOW':      return 'var(--green)'
    default:         return 'var(--muted)'
  }
}

export function severityBadgeClass(sev?: string | null): string {
  switch (sev?.toUpperCase()) {
    case 'CRITICAL': return 'badge badge-critical'
    case 'HIGH':     return 'badge badge-high'
    case 'MEDIUM':   return 'badge badge-medium'
    case 'LOW':      return 'badge badge-low'
    default:         return 'badge badge-neutral'
  }
}

export function riskLevelBadgeClass(level?: string | null): string {
  switch (level?.toUpperCase()) {
    case 'CRITICAL': return 'badge badge-critical'
    case 'HIGH':     return 'badge badge-high'
    case 'MEDIUM':   return 'badge badge-medium'
    case 'LOW':      return 'badge badge-low'
    default:         return 'badge badge-neutral'
  }
}

export function statusDotClass(status?: string): string {
  switch (status?.toLowerCase()) {
    case 'active': case 'open': case 'pending': return 'dot dot-red'
    case 'resolved': case 'acknowledged': return 'dot dot-green'
    case 'investigating': return 'dot dot-yellow'
    case 'monitoring': return 'dot dot-yellow'
    default: return 'dot dot-gray'
  }
}

export function fmtDate(iso?: string): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })
}

export function fmtNum(n?: number, decimals = 1): string {
  if (n == null) return '—'
  return n.toFixed(decimals)
}

export function paramLabel(param?: string): string {
  const MAP: Record<string, string> = {
    pm25: 'PM₂.₅', pm10: 'PM₁₀', so2: 'SO₂', no2: 'NO₂',
    co: 'CO', ph: 'pH', turbidity: 'Turbidity', chemical_level: 'Chemical',
  }
  return param ? (MAP[param] ?? param.toUpperCase()) : '—'
}

export function paramUnit(param?: string): string {
  const MAP: Record<string, string> = {
    pm25: 'µg/m³', pm10: 'µg/m³', so2: 'µg/m³', no2: 'µg/m³',
    co: 'mg/m³', ph: 'pH', turbidity: 'NTU', chemical_level: 'mg/L',
  }
  return param ? (MAP[param] ?? '') : ''
}
