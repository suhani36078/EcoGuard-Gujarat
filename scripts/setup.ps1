# ─────────────────────────────────────────────────────────────────────────────
# setup.ps1 — One-shot local developer setup (Windows PowerShell)
# Usage: .\scripts\setup.ps1
# ─────────────────────────────────────────────────────────────────────────────
param([switch]$SkipFrontend)

$Root = Split-Path $PSScriptRoot -Parent
$ErrorActionPreference = "Stop"

function Write-Step { Write-Host "`n==> $args" -ForegroundColor Cyan }
function Write-Ok   { Write-Host "[OK] $args"  -ForegroundColor Green }
function Write-Warn { Write-Host "[WARN] $args" -ForegroundColor Yellow }

Write-Step "Gujarat Pollution Intelligence Platform — Setup"

# ── Python backend ────────────────────────────────────────────────────────────
Write-Step "1. Installing Python dependencies"
Set-Location "$Root\backend"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Warn "Created .env from .env.example - edit with real credentials"
}

pip install -r requirements.txt
Write-Ok "Python dependencies installed"

# ── Seed database ─────────────────────────────────────────────────────────────
Write-Step "2. Seeding database"
python start.py --seed
Write-Ok "Database seeded with 7 factories and demo data"

# ── Node frontend ─────────────────────────────────────────────────────────────
if (-not $SkipFrontend) {
    Write-Step "3. Installing Node.js frontend dependencies"
    Set-Location "$Root\frontend"
    npm install --legacy-peer-deps
    Write-Ok "Frontend dependencies installed"

    Write-Step "4. Building frontend"
    npm run build
    Write-Ok "Frontend built to frontend\dist\"
}

# ── Done ──────────────────────────────────────────────────────────────────────
Set-Location $Root
Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  Start backend:  cd backend; python start.py" -ForegroundColor White
Write-Host "  Dev frontend:   cd frontend; npm run dev"    -ForegroundColor White
Write-Host "  Docker:         docker-compose up --build"  -ForegroundColor White
Write-Host ""
Write-Host "  API docs:       http://localhost:8000/docs"  -ForegroundColor Cyan
Write-Host "  Frontend:       http://localhost:3000"       -ForegroundColor Cyan
Write-Host ""
Write-Host "  Demo login:     admin / admin123"            -ForegroundColor Yellow
