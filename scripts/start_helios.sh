#!/bin/bash
# Starts the Helios web app (Django backend + React frontend) and opens the browser.
# Safe to run multiple times — skips anything already running.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="/tmp/helios_pids"
mkdir -p "$PID_DIR"

echo "Starting Helios from $PROJECT_ROOT ..."

# Postgres check (Django, Feast, and pgvector all depend on it) — informational only,
# this script doesn't manage Postgres itself since it's a system-level service.
if ! pg_isready -q 2>/dev/null; then
  echo "WARNING: Postgres doesn't appear to be reachable. Start it before continuing if the app fails to load data."
fi

# --- Backend (Django, port 8000) ---
if [ -f "$PID_DIR/backend.pid" ] && kill -0 "$(cat "$PID_DIR/backend.pid")" 2>/dev/null; then
  echo "Backend already running (PID $(cat "$PID_DIR/backend.pid"))"
else
  cd "$PROJECT_ROOT/webapp/backend"
  source "$PROJECT_ROOT/.venv/bin/activate"
  nohup python manage.py runserver 8000 < /dev/null > /tmp/helios_backend.log 2>&1 &
  echo $! > "$PID_DIR/backend.pid"
  echo "Backend started (PID $!) — log: /tmp/helios_backend.log"
fi

# --- Frontend (Vite, port 5173) ---
if [ -f "$PID_DIR/frontend.pid" ] && kill -0 "$(cat "$PID_DIR/frontend.pid")" 2>/dev/null; then
  echo "Frontend already running (PID $(cat "$PID_DIR/frontend.pid"))"
else
  cd "$PROJECT_ROOT/webapp/frontend"
  nohup npm run dev < /dev/null > /tmp/helios_frontend.log 2>&1 &
  echo $! > "$PID_DIR/frontend.pid"
  echo "Frontend started (PID $!) — log: /tmp/helios_frontend.log"
fi

# Wait for the frontend to actually respond before opening the browser
echo "Waiting for the app to come up..."
for i in $(seq 1 30); do
  if curl -s http://localhost:5173 > /dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

open "http://localhost:5173"
echo "Helios is running — backend: http://localhost:8000  frontend: http://localhost:5173"
