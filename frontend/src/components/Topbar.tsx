interface TopbarProps {
  title: string
  subtitle?: string
}

export default function Topbar({ title, subtitle }: TopbarProps) {
  const now = new Date()
  const timeStr = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
  const dateStr = now.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })

  return (
    <header className="topbar">
      <div>
        <div className="topbar-title">{title}</div>
        {subtitle && <div className="topbar-sub">{subtitle}</div>}
      </div>
      <div className="topbar-right">
        <span className="demo-tag">DEMO / SIMULATED</span>
        <span className="live-indicator">
          <span className="dot dot-green dot-pulse" />
          Platform Active
        </span>
        <span style={{ fontSize: 11, color: 'var(--muted)', display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
          <span>{timeStr}</span>
          <span style={{ fontSize: 10 }}>{dateStr}</span>
        </span>
      </div>
    </header>
  )
}
