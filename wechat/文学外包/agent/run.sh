#!/bin/bash
# Editor Agent launcher — run outside Claude Code to avoid CLAUDECODE env conflict
# Usage: ./run.sh [--dry-run]
#
# Supports auto-restart: if the agent writes .restart marker (self-intervention),
# the loop detects it and relaunches automatically.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/daemon.log"
PID_FILE="$SCRIPT_DIR/daemon.pid"
RESTART_MARKER="$SCRIPT_DIR/.restart"

mkdir -p "$LOG_DIR"

# Activate virtual env
source ~/venv/automation/bin/activate

# Critical: unset CLAUDECODE so claude -p works from Brain
unset CLAUDECODE

export PYTHONPATH="$PROJECT_ROOT"
cd "$PROJECT_ROOT"

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Editor Agent already running (PID $OLD_PID). Kill it first:"
        echo "  kill $OLD_PID && rm $PID_FILE"
        exit 1
    else
        rm "$PID_FILE"
    fi
fi

# Clean up stale restart marker
rm -f "$RESTART_MARKER"

echo "Starting Editor Agent..."
echo "  Log: $LOG_FILE"
echo "  Config: $SCRIPT_DIR/config.yaml"

# Main loop: run daemon, restart if .restart marker exists
while true; do
    nohup python -m wechat.文学外包.agent.daemon "$@" >> "$LOG_FILE" 2>&1 &
    DAEMON_PID=$!
    echo "$DAEMON_PID" > "$PID_FILE"

    echo "  PID: $DAEMON_PID"
    echo "  Tail: tail -f $LOG_FILE"

    # Wait for the daemon to exit
    wait $DAEMON_PID || true

    # Check if restart was requested
    if [ ! -f "$RESTART_MARKER" ]; then
        echo "Editor Agent exited (no restart marker). Done."
        rm -f "$PID_FILE"
        break
    fi

    rm -f "$RESTART_MARKER"
    rm -f "$PID_FILE"
    echo "[$(date)] Auto-restarting after self-intervention..." | tee -a "$LOG_FILE"
    sleep 2
done
