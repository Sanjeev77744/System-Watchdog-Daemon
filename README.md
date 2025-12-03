# 🛡️ System Watchdog Daemon

A lightweight Bash script that runs as a background process (daemon) to monitor system health in real-time. It checks CPU usage and Disk space, sending desktop notifications when critical thresholds are exceeded.

## 🚀 Features

* **Background Execution:** Runs silently using an infinite loop and sleep timers.
* **Desktop Alerts:** Integrates with `libnotify` to send visual pop-ups (works on Gnome, Cinnamon, XFCE, etc.).
* **Resource Parsing:** Uses `awk`, `sed`, and `top` to parse raw system data.
* **Process Safety:** * Uses **PID files** to prevent multiple instances from running.
    * Uses **Signal Trapping** (`trap`) to clean up temporary files upon exit (SIGINT/SIGTERM).

## 📋 Prerequisites

You need `libnotify` installed to see the desktop pop-ups.

* **Arch Linux:** `sudo pacman -S libnotify`
* **Ubuntu/Debian:** `sudo apt install libnotify-bin`
* **Fedora:** `sudo dnf install libnotify`

## 🛠️ Usage

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/system-watchdog.git](https://github.com/YOUR_USERNAME/system-watchdog.git)
    cd system-watchdog
    ```

2.  **Make executable:**
    ```bash
    chmod +x watchdog.sh
    ```

3.  **Start the Daemon:**
    ```bash
    ./watchdog.sh &
    ```
    *(Note: The `&` runs it in the background. You can close your terminal after this.)*

4.  **Stop the Daemon:**
    Since the script runs in the background, use the generated PID file to kill it cleanly:
    ```bash
    kill $(cat /tmp/watchdog.pid)
    ```

## ⚙️ Configuration

Open `watchdog.sh` to adjust the thresholds:

```bash
CPU_THRESHOLD=80        # Alert if CPU > 80%
DISK_THRESHOLD=90       # Alert if Disk > 90%
CHECK_INTERVAL=10       # Check every 10 seconds
