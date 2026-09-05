import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import { getDistricts, getHotspots, getPollutionIndex } from '../services/queries'
import { Filter, Search, AlertTriangle } from 'lucide-react'
import 'leaflet/dist/leaflet.css'

type PollutionFilter = 'all' | 'air' | 'water' | 'industrial' | 'noise' | 'waste'

const RISK_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MODERATE: '#f59e0b',
  LOW: '#22c55e',
}

const POLLUTION_TYPE_COLORS: Record<string, string> = {
  air: '#0ea5e9',
  water: '#06b6d4',
  industrial: '#f97316',
  noise: '#a855f7',
  waste: '#f59e0b',
}

function getRiskColor(score: number): string {
  if (score >= 75) return '#ef4444'
  if (score >= 60) return '#f97316'
  if (score >= 40) return '#f59e0b'
  return '#22c55e'
}

function getRiskLevel(score: number): string {
  if (score >= 75) return 'CRITICAL'
  if (score >= 60) return 'HIGH'
  if (score >= 40) return 'MODERATE'
  return 'LOW'
}

const DEMO_D = [
  {id:1,district_name:'Ahmedabad',district_code:'AHM',latitude:23.0225,longitude:72.5714,overall_score:63.2,air_score:68,water_score:52,industrial_score:65,noise_score:62,waste_score:55,risk_level:'HIGH',main_pollutant:'PM2.5',main_source:'Vehicular + Industrial (Vatva)',trend:'stable',monitored_locations:12,high_risk_zones:3,active_alerts:4,population:8253000,data_confidence:0.78},
  {id:2,district_name:'Surat',district_code:'SRT',latitude:21.1702,longitude:72.8311,overall_score:58.5,air_score:58,water_score:61,industrial_score:60,noise_score:54,waste_score:50,risk_level:'MODERATE',main_pollutant:'NOx',main_source:'Textile + Diamond Industry',trend:'stable',monitored_locations:8,high_risk_zones:2,active_alerts:2,population:6081000,data_confidence:0.72},
  {id:3,district_name:'Vapi',district_code:'VPI',latitude:20.3724,longitude:72.9027,overall_score:83.5,air_score:82,water_score:88,industrial_score:91,noise_score:55,waste_score:72,risk_level:'CRITICAL',main_pollutant:'SO2 + Chemicals',main_source:'Chemical Manufacturing Zone',trend:'increasing',monitored_locations:6,high_risk_zones:4,active_alerts:7,population:200000,data_confidence:0.85},
  {id:4,district_name:'Ankleshwar',district_code:'ANK',latitude:21.6263,longitude:73.0049,overall_score:76.8,air_score:75,water_score:81,industrial_score:85,noise_score:48,waste_score:65,risk_level:'HIGH',main_pollutant:'Textile Dyes',main_source:'GIDC Industrial Estate',trend:'increasing',monitored_locations:5,high_risk_zones:3,active_alerts:5,population:180000,data_confidence:0.82},
  {id:5,district_name:'Vadodara',district_code:'VDR',latitude:22.3072,longitude:73.1812,overall_score:53.2,air_score:55,water_score:48,industrial_score:58,noise_score:50,waste_score:45,risk_level:'MODERATE',main_pollutant:'SO2',main_source:'Petrochemical + Fertilizer',trend:'stable',monitored_locations:7,high_risk_zones:2,active_alerts:2,population:2065000,data_confidence:0.70},
  {id:6,district_name:'Rajkot',district_code:'RJK',latitude:22.3039,longitude:70.8022,overall_score:47.2,air_score:48,water_score:42,industrial_score:50,noise_score:52,waste_score:40,risk_level:'MODERATE',main_pollutant:'PM10',main_source:'Engineering + Casting',trend:'stable',monitored_locations:5,high_risk_zones:1,active_alerts:1,population:1390000,data_confidence:0.65},
  {id:7,district_name:'Gandhinagar',district_code:'GDN',latitude:23.2156,longitude:72.6369,overall_score:36.5,air_score:38,water_score:32,industrial_score:40,noise_score:35,waste_score:30,risk_level:'LOW',main_pollutant:'PM2.5',main_source:'Urban Traffic',trend:'stable',monitored_locations:4,high_risk_zones:0,active_alerts:0,population:1387000,data_confidence:0.72},
  {id:8,district_name:'Jamnagar',district_code:'JAM',latitude:22.4707,longitude:70.0577,overall_score:61.5,air_score:62,water_score:55,industrial_score:72,noise_score:45,waste_score:48,risk_level:'HIGH',main_pollutant:'SO2',main_source:'Refinery Operations',trend:'increasing',monitored_locations:4,high_risk_zones:2,active_alerts:3,population:920000,data_confidence:0.74},
  {id:9,district_name:'Bhavnagar',district_code:'BHV',latitude:21.7645,longitude:72.1519,overall_score:46.8,air_score:45,water_score:50,industrial_score:52,noise_score:40,waste_score:42,risk_level:'MODERATE',main_pollutant:'Effluents',main_source:'Ship-breaking + Cement',trend:'stable',monitored_locations:3,high_risk_zones:1,active_alerts:1,population:977000,data_confidence:0.62},
  {id:10,district_name:'Bharuch',district_code:'BRC',latitude:21.7051,longitude:73.0015,overall_score:73.2,air_score:72,water_score:78,industrial_score:80,noise_score:48,waste_score:62,risk_level:'HIGH',main_pollutant:'Chemical Effluents',main_source:'Petrochemical + GIDC',trend:'increasing',monitored_locations:5,high_risk_zones:3,active_alerts:4,population:1551000,data_confidence:0.80},
  {id:11,district_name:'Morbi',district_code:'MRB',latitude:22.8173,longitude:70.8377,overall_score:63.5,air_score:65,water_score:58,industrial_score:68,noise_score:60,waste_score:55,risk_level:'HIGH',main_pollutant:'PM10 + SO2',main_source:'Ceramic Kiln Industry',trend:'increasing',monitored_locations:3,high_risk_zones:2,active_alerts:3,population:950000,data_confidence:0.68},
  {id:12,district_name:'Navsari',district_code:'NVS',latitude:20.9467,longitude:72.9520,overall_score:59.5,air_score:58,water_score:62,industrial_score:65,noise_score:45,waste_score:50,risk_level:'MODERATE',main_pollutant:'Effluents',main_source:'Sugar + Paper Industry',trend:'stable',monitored_locations:3,high_risk_zones:1,active_alerts:2,population:1334000,data_confidence:0.65},
  {id:13,district_name:'Kutch',district_code:'KCH',latitude:23.7337,longitude:69.8597,overall_score:36.8,air_score:35,water_score:38,industrial_score:42,noise_score:30,waste_score:32,risk_level:'LOW',main_pollutant:'Dust',main_source:'Mining + Construction',trend:'stable',monitored_locations:3,high_risk_zones:0,active_alerts:0,population:2092000,data_confidence:0.55},
  {id:14,district_name:'Mehsana',district_code:'MSN',latitude:23.5880,longitude:72.3693,overall_score:41.5,air_score:42,water_score:40,industrial_score:45,noise_score:38,waste_score:35,risk_level:'MODERATE',main_pollutant:'PM10',main_source:'Dairy + Engineering',trend:'stable',monitored_locations:3,high_risk_zones:1,active_alerts:1,population:2027000,data_confidence:0.58},
  {id:15,district_name:'Patan',district_code:'PTN',latitude:23.8500,longitude:72.1167,overall_score:31.5,air_score:32,water_score:35,industrial_score:30,noise_score:28,waste_score:28,risk_level:'LOW',main_pollutant:'Dust',main_source:'Agriculture + Cotton',trend:'stable',monitored_locations:2,high_risk_zones:0,active_alerts:0,population:1343000,data_confidence:0.50},
]
const DEMO_H = [
  {id:1,name:'Vapi Chemical Complex',district:'Vapi',latitude:20.3724,longitude:72.9027,pollution_type:'industrial',severity:'CRITICAL',severity_score:91.5,trend:'increasing',possible_source:'Chemical manufacturing & effluent discharge',affected_radius:8.5,population_affected:125000},
  {id:2,name:'Ankleshwar GIDC',district:'Ankleshwar',latitude:21.6263,longitude:73.0049,pollution_type:'industrial',severity:'HIGH',severity_score:82.0,trend:'increasing',possible_source:'Textile dye & pharmaceutical manufacturing',affected_radius:7.0,population_affected:98000},
  {id:3,name:'Vatva Industrial Area',district:'Ahmedabad',latitude:22.9682,longitude:72.6389,pollution_type:'air',severity:'HIGH',severity_score:76.5,trend:'stable',possible_source:'Pharmaceutical & chemical manufacturing',affected_radius:5.0,population_affected:350000},
  {id:4,name:'Jamnagar Refinery Belt',district:'Jamnagar',latitude:22.4707,longitude:70.0577,pollution_type:'air',severity:'HIGH',severity_score:74.0,trend:'increasing',possible_source:'Petroleum refining operations',affected_radius:15.0,population_affected:180000},
  {id:5,name:'Morbi Ceramic Cluster',district:'Morbi',latitude:22.8173,longitude:70.8377,pollution_type:'air',severity:'HIGH',severity_score:71.0,trend:'increasing',possible_source:'Ceramic kiln coal combustion',affected_radius:6.0,population_affected:89000},
  {id:6,name:'Alang Ship Breaking',district:'Bhavnagar',latitude:21.4000,longitude:72.1500,pollution_type:'water',severity:'HIGH',severity_score:72.0,trend:'stable',possible_source:'Ship dismantling & hazardous waste',affected_radius:12.0,population_affected:45000},
  {id:7,name:'Bharuch Petrochemical Zone',district:'Bharuch',latitude:21.7051,longitude:73.0015,pollution_type:'industrial',severity:'HIGH',severity_score:78.0,trend:'increasing',possible_source:'Petrochemical & fertilizer plants',affected_radius:10.0,population_affected:145000},
  {id:8,name:'Sabarmati River Belt',district:'Ahmedabad',latitude:23.0500,longitude:72.5800,pollution_type:'water',severity:'MODERATE',severity_score:58.0,trend:'stable',possible_source:'Industrial & urban sewage discharge',affected_radius:20.0,population_affected:500000},
]

export default function MapPage() {
  const [districts, setDistricts] = useState<any[]>(DEMO_D)
  const [hotspots, setHotspots] = useState<any[]>(DEMO_H)
  const [pollutionIndex, setPollutionIndex] = useState<any>({ overall_score: 56.4, risk_category: 'POOR' })
  const [filter, setFilter] = useState<PollutionFilter>('all')
  const [selectedDistrict, setSelectedDistrict] = useState<any>(null)
  const [selectedHotspot, setSelectedHotspot] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [showHotspots, setShowHotspots] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    setLoading(true)
    Promise.all([getDistricts(), getHotspots(), getPollutionIndex()])
      .then(([d, h, p]) => {
        if (d?.length > 0) setDistricts(d)
        if (h?.length > 0) setHotspots(h)
        if (p?.overall_score) setPollutionIndex(p)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const getDistrictScore = (d: any): number => {
    switch (filter) {
      case 'air': return d.air_score || 0
      case 'water': return d.water_score || 0
      case 'industrial': return d.industrial_score || 0
      case 'noise': return d.noise_score || 0
      case 'waste': return d.waste_score || 0
      default: return d.overall_score || 0
    }
  }

  const filteredHotspots = filter === 'all' ? hotspots : hotspots.filter(h => h.pollution_type === filter)
  const displayDistricts = search ? districts.filter(d => d.district_name.toLowerCase().includes(search.toLowerCase())) : districts

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 className="page-heading">Gujarat Pollution Map</h1>
          <p className="page-sub">District-level pollution intelligence — <span className="data-status">DEMO / SIMULATED</span></p>
        </div>
        <div style={{ display:'flex', gap:20, background:'var(--surface)', border:'1px solid var(--border)', borderRadius:12, padding:'12px 20px' }}>
          {[
            {label:'State Score', val:(pollutionIndex?.overall_score||56.4).toFixed(1), color:getRiskColor(pollutionIndex?.overall_score||56)},
            {label:'Districts', val:String(districts.length), color:'var(--emerald2)'},
            {label:'Hotspots', val:String(hotspots.length), color:'var(--orange)'},
            {label:'Critical', val:String(hotspots.filter((h:any)=>h.severity==='CRITICAL').length), color:'var(--red)'},
          ].map(({label,val,color}) => (
            <div key={label} style={{textAlign:'center'}}>
              <div style={{fontSize:9,color:'var(--muted)',textTransform:'uppercase',letterSpacing:'0.08em',marginBottom:2}}>{label}</div>
              <div style={{fontSize:22,fontWeight:900,fontFamily:"'Space Grotesk',sans-serif",color}}>{val}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Filter bar */}
      <div className="card" style={{ padding: '12px 16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <Filter size={13} color="var(--muted)" />
          {([['all','🌐 All'],['air','💨 Air'],['water','💧 Water'],['industrial','🏭 Industrial'],['noise','🔊 Noise'],['waste','🗑️ Waste']] as [PollutionFilter,string][]).map(([f,label]) => (
            <button key={f} className={`btn btn-sm ${filter===f?'btn-primary':'btn-outline'}`} onClick={() => setFilter(f)}>{label}</button>
          ))}
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ position:'relative' }}>
              <Search size={12} style={{ position:'absolute', left:9, top:'50%', transform:'translateY(-50%)', color:'var(--muted)', pointerEvents:'none' }} />
              <input placeholder="Search district..." value={search} onChange={e => setSearch(e.target.value)} style={{ width:170, paddingLeft:28, height:30, fontSize:12 }} />
            </div>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', margin: 0, fontSize: 12, color: 'var(--text2)', whiteSpace:'nowrap' }}>
              <input type="checkbox" checked={showHotspots} onChange={e => setShowHotspots(e.target.checked)} style={{ width: 14, height: 14 }} />
              Hotspots
            </label>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: selectedDistrict ? '1fr 340px' : '1fr', gap: 20 }}>
        {/* Map */}
        <div className="map-container" style={{ position:'relative' }}>
          <MapContainer center={[22.2587, 71.1924]} zoom={7} style={{ height: '100%', width: '100%', background:'#0a0f0d' }}>
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' />
            {/* District markers */}
            {displayDistricts.map(d => {
              if (!d.latitude || !d.longitude) return null
              const score = getDistrictScore(d)
              const color = getRiskColor(score)
              const radius = Math.max(10, Math.min(28, score / 3.5))
              return (
                <CircleMarker key={d.district_code} center={[d.latitude, d.longitude]} radius={radius}
                  pathOptions={{ fillColor:color, color:'#111', fillOpacity:0.75, weight:1 }}
                  eventHandlers={{ click: () => setSelectedDistrict(d) }}>
                  <Popup>
                    <div style={{ minWidth:185, fontFamily:'Inter,sans-serif' }}>
                      <div style={{ fontWeight:700, fontSize:14, marginBottom:5, color:'#1f2328' }}>{d.district_name}</div>
                      <div style={{ display:'flex', justifyContent:'space-between', marginBottom:3 }}>
                        <span style={{ fontSize:12, color:'#57606a' }}>Score</span>
                        <span style={{ fontWeight:700, color, fontSize:13 }}>{score?.toFixed(0)}/100</span>
                      </div>
                      <div style={{ display:'flex', justifyContent:'space-between', marginBottom:3 }}>
                        <span style={{ fontSize:12, color:'#57606a' }}>Risk</span>
                        <span style={{ fontSize:12, fontWeight:600, color }}>{getRiskLevel(score)}</span>
                      </div>
                      <div style={{ fontSize:11, color:'#57606a', marginTop:4 }}>📍 {d.main_source}</div>
                      <div style={{ fontSize:10, color:'#a0aec0', marginTop:2 }}>Click panel for details</div>
                    </div>
                  </Popup>
                </CircleMarker>
              )
            })}
            {/* Hotspot markers */}
            {showHotspots && filteredHotspots.map(h => {
              const hc = POLLUTION_TYPE_COLORS[h.pollution_type] || '#f97316'
              return (
                <CircleMarker key={`h${h.id}`} center={[h.latitude, h.longitude]}
                  radius={h.severity==='CRITICAL'?9:6}
                  pathOptions={{ fillColor:hc, color:h.severity==='CRITICAL'?'#ef4444':hc, fillOpacity:0.9, weight:h.severity==='CRITICAL'?2.5:1.5 }}>
                  <Popup>
                    <div style={{ minWidth:205, fontFamily:'Inter,sans-serif' }}>
                      <div style={{ fontWeight:700, fontSize:13, marginBottom:3, color:'#1f2328' }}>⚠️ {h.name}</div>
                      <div style={{ fontSize:11, color:'#57606a', marginBottom:5 }}>📍 {h.district}</div>
                      <div style={{ display:'flex', gap:5, marginBottom:5 }}>
                        <span style={{ fontSize:10, padding:'2px 7px', borderRadius:10, background:RISK_COLORS[h.severity]+'22', color:RISK_COLORS[h.severity], fontWeight:700 }}>{h.severity}</span>
                        <span style={{ fontSize:10, padding:'2px 7px', borderRadius:10, background:hc+'22', color:hc, fontWeight:600 }}>{h.pollution_type}</span>
                      </div>
                      <div style={{ fontSize:11, color:'#57606a', lineHeight:1.5 }}>{h.possible_source}</div>
                    </div>
                  </Popup>
                </CircleMarker>
              )
            })}
          </MapContainer>
          {loading && (
            <div style={{ position:'absolute', top:10, left:'50%', transform:'translateX(-50%)', background:'rgba(19,30,23,0.92)', padding:'5px 14px', borderRadius:20, fontSize:12, color:'var(--emerald2)', display:'flex', gap:6, alignItems:'center', zIndex:1000, border:'1px solid var(--border2)' }}>
              <div className="loading-spinner" style={{ width:11, height:11 }} /> Syncing live data...
            </div>
          )}
        </div>

        {/* District detail panel */}
        {selectedDistrict && (
          <div className="card" style={{ overflow:'auto', display:'flex', flexDirection:'column', gap:14 }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start' }}>
              <div>
                <div style={{ fontSize:10, color:'var(--muted)', textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:3 }}>District Profile</div>
                <h3 style={{ fontSize:16, fontWeight:700 }}>{selectedDistrict.district_name}</h3>
              </div>
              <button className="btn btn-sm btn-outline" onClick={() => setSelectedDistrict(null)}>✕</button>
            </div>
            <div style={{ display:'flex', gap:10 }}>
              <div style={{ flex:1, background:'var(--surface2)', borderRadius:10, padding:10, textAlign:'center' }}>
                <div style={{ fontSize:9, color:'var(--muted)', marginBottom:2 }}>SCORE</div>
                <div style={{ fontSize:28, fontWeight:900, color:getRiskColor(selectedDistrict.overall_score), fontFamily:"'Space Grotesk',sans-serif" }}>{selectedDistrict.overall_score?.toFixed(1)}</div>
              </div>
              <div style={{ flex:1, background:'var(--surface2)', borderRadius:10, padding:10, textAlign:'center', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center' }}>
                <div style={{ fontSize:9, color:'var(--muted)', marginBottom:5 }}>RISK LEVEL</div>
                <span className={`badge badge-${selectedDistrict.risk_level?.toLowerCase()}`}>{selectedDistrict.risk_level}</span>
              </div>
            </div>
            {[{l:'Air',v:selectedDistrict.air_score,c:'#0ea5e9'},{l:'Water',v:selectedDistrict.water_score,c:'#06b6d4'},{l:'Industrial',v:selectedDistrict.industrial_score,c:'#f97316'},{l:'Noise',v:selectedDistrict.noise_score,c:'#a855f7'},{l:'Waste',v:selectedDistrict.waste_score,c:'#f59e0b'}].map(({l,v,c}) => (
              <div key={l}>
                <div style={{ display:'flex', justifyContent:'space-between', marginBottom:3 }}>
                  <span style={{ fontSize:11, color:'var(--muted)' }}>{l}</span>
                  <span style={{ fontSize:11, fontWeight:700, color:c }}>{v?.toFixed(0)}/100</span>
                </div>
                <div className="score-bar"><div className="score-bar-fill" style={{ width:`${v||0}%`, background:c }} /></div>
              </div>
            ))}
            <div className="section-divider" style={{ margin:'2px 0' }} />
            {[
              {k:'Main Pollutant', v:selectedDistrict.main_pollutant},
              {k:'Main Source', v:selectedDistrict.main_source},
              {k:'Trend', v:selectedDistrict.trend==='increasing'?'📈 Rising':selectedDistrict.trend==='decreasing'?'📉 Improving':'→ Stable'},
              {k:'Monitored Locations', v:selectedDistrict.monitored_locations},
              {k:'High Risk Zones', v:selectedDistrict.high_risk_zones, warn:true},
              {k:'Active Alerts', v:selectedDistrict.active_alerts, err:true},
              {k:'Population', v:selectedDistrict.population?.toLocaleString()},
            ].map(({k,v,warn,err}:any) => (
              <div key={k} style={{ display:'flex', justifyContent:'space-between' }}>
                <span style={{ fontSize:12, color:'var(--muted)' }}>{k}</span>
                <span style={{ fontSize:12, fontWeight:600, color: err&&v>0?'var(--red)':warn&&v>0?'var(--orange)':'var(--text2)', textAlign:'right', maxWidth:'56%' }}>{v ?? '—'}</span>
              </div>
            ))}
            <div className="insight-box" style={{ fontSize:12 }}>
              <div className="insight-label">Health Advisory</div>
              {selectedDistrict.overall_score>70 ? 'Significant industrial pollution. Wear N95 masks near industrial zones. Sensitive groups should avoid outdoor exposure.' : selectedDistrict.overall_score>50 ? 'Moderate pollution. Sensitive groups should limit outdoor activity near industrial areas.' : 'Relatively safe. Standard precautions apply.'}
            </div>
            <div className="data-status" style={{ justifyContent:'center' }}>DEMO — Confidence: {((selectedDistrict.data_confidence||0.75)*100).toFixed(0)}%</div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="card" style={{ padding: '12px 20px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 20, alignItems: 'center' }}>
          <span style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Legend:</span>
          {Object.entries(RISK_COLORS).map(([level, color]) => (
            <div key={level} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 12, height: 12, borderRadius: '50%', background: color }} />
              <span style={{ fontSize: 11, color: 'var(--text2)' }}>{level}</span>
            </div>
          ))}
          <div style={{ width: 1, height: 16, background: 'var(--border)', margin: '0 4px' }} />
          <span style={{ fontSize: 11, color: 'var(--muted)' }}>● Districts (size = pollution score)</span>
          {showHotspots && <span style={{ fontSize: 11, color: 'var(--muted)' }}>● Hotspots (by type)</span>}
        </div>
      </div>
    </div>
  )
}
