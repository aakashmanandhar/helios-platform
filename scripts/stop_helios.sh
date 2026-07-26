#!/bin/bash
# Stops everything started by start_helios.sh.

PID_DIR="/tmp/helios_pids"

echo "Stopping Helios..."

for name in backend frontend; do
  PIDFILE="$PID_DIR/$name.pid"
  if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
      kill "$PID" 2>/dev/null
      echo "Stopped $name (PID $PID)"
    else
      echo "$name PID file was stale (process not running)"
    fi
    rm -f "$PIDFILE"
  else
    echo "No PID file found for $name"
  fi
done

# Fallback in case PID files are missing or npm spawned a detached child process
pkill -f "manage.py runserver 8000" 2>/dev/null && echo "Killed a lingering backend process"
pkill -f "vite" 2>/dev/null && echo "Killed a lingering frontend process"

echo "Helios stopped."
