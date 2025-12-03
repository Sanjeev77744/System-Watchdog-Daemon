#!/bin/bash

# Configuration
# Thresholds (Adjust these to test)
CPU_THRESHOLD=80        # Alert if CPU usage is above 80%
DISK_THRESHOLD=90       # Alert if Disk usage is above 90%
CHECK_INTERVAL=10       # Check every 10 seconds
LOG_FILE="/tmp/watchdog.log"
PID_FILE="/tmp/watchdog.pid"

# Functions

# 1. Logging Function
log_action() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# 2. Alert Function (Desktop Notification)
send_alert() {
    local title="$1"
    local message="$2"
    local urgency="$3"

    # Log it
    log_action "ALERT: $title - $message"

    # Send visual popup (if notify-send exists)
    if command -v notify-send >/dev/null; then
        notify-send -u "$urgency" "$title" "$message"
    else
        # Fallback for headless servers
        echo "Check log! $title: $message"
    fi
}

# 3. Cleanup Function (Runs when we stop the script)
cleanup() {
    log_action "Watchdog service stopping..."
    rm -f "$PID_FILE"
    exit 0
}

# Initialization

# Check if script is already running
if [ -f "$PID_FILE" ]; then
    echo "Error: Watchdog is already running (PID $(cat $PID_FILE))."
    exit 1
fi

# Write current Process ID (PID) to file
echo $$ > "$PID_FILE"

# Trap signals: If someone does 'kill' or Ctrl+C, run cleanup()
trap cleanup SIGINT SIGTERM

log_action "Watchdog service started. Monitoring..."

# The Daemon

while true; do
    # 1. Check Disk Usage (Root partition)
    # df output: Filesystem Size Used Avail Use% Mounted
    # awk gets the 5th column, tr removes the % sign
    DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | tr -d '%')

    if [ "$DISK_USAGE" -gt "$DISK_THRESHOLD" ]; then
        send_alert "Disk Critical" "Root partition is at ${DISK_USAGE}% capacity!" "critical"
    fi

    # 2. Check CPU Usage
    # We grep the Cpu(s) line from top, and calculate (100 - idle_time)
    CPU_IDLE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print int($1)}')
    CPU_USAGE=$(( 100 - CPU_IDLE ))

    if [ "$CPU_USAGE" -gt "$CPU_THRESHOLD" ]; then
        send_alert "High CPU Load" "CPU usage is at ${CPU_USAGE}%!" "normal"
    fi

    # Sleep before next check
    sleep "$CHECK_INTERVAL"
done
