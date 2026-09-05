#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# setup.sh — One-shot local developer setup for the Pollution Intelligence Platform
# Usage: ./scripts/setup.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
RESET="\033[0m"

info()  { echo -e "${GREEN}[INFO]${RESET}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
step()  { echo -e "\n${BOLD}==> $*${RESET}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

step "Gujarat Pollution Intelligence Platform — Setup"
info "Root: $ROOT_DIR"

# ── Python backend ────────────────────────────────────────────────────────────
step "1. Installing Python dependencies"
cd "$ROOT_DIR/backend"

if [ ! -f ".env" ]; then
    cp .env.example .env
    warn "Created .env from .env.example — edit with real credentials"
fi

pip install -r requirements.txt
info "Python dependencies installed"

# ── Seed database ─────────────────────────────────────────────────────────────
step "2. Seeding database with demo data"
python start.py --seed
info "Database seeded"

# ── Node frontend ─────────────────────────────────────────────────────────────
step "3. Installing Node.js frontend dependencies"
cd "$ROOT_DIR/frontend"
npm install --legacy-peer-deps
info "Frontend dependencies installed"

step "4. Building frontend"
npm run build
info "Frontend built to frontend/dist/"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}✅ Setup complete!${RESET}"
echo ""
echo "  Backend API:  cd backend && python start.py"
echo "  Frontend dev: cd frontend && npm run dev"
echo "  Docker:       docker-compose up --build"
echo ""
echo "  API docs:     http://localhost:8000/docs"
echo "  Frontend:     http://localhost:3000"
echo ""
echo "  Demo login:   admin / admin123"
