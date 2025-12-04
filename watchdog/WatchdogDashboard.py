import sys
import os
import signal
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QTextEdit, QFrame, QMessageBox)
from PyQt6.QtCore import QTimer, Qt, QProcess
from PyQt6.QtGui import QFont, QColor, QPalette

# Configuration Paths
SCRIPT_PATH = "./watchdog_v2.sh"
CONFIG_FILE = "watchdog.conf"
LOG_FILE = "/tmp/watchdog.log"
PID_FILE = "/tmp/watchdog.pid"

class WatchdogDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("System Watchdog Control Center")
        self.setGeometry(100, 100, 800, 600)
        
        # Main Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout = QVBoxLayout(main_widget)
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(20, 20, 20, 20)

        # 1. Header Section (Status)
        self.setup_header()

        # 2. Controls & Config Section
        self.setup_controls()

        # 3. Log Viewer Section
        self.setup_log_viewer()

        # Timers
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_status)
        self.status_timer.start(2000)  # Check status every 2 seconds

        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.update_logs)
        self.log_timer.start(1000)  # Update logs every 1 second
        
        self.last_file_pos = 0
        self.load_config()

    def setup_header(self):
        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(header_frame)

        title = QLabel("🛡️ Daemon Status:")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        
        self.status_indicator = QLabel("STOPPED")
        self.status_indicator.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.status_indicator.setStyleSheet("color: red;")

        layout.addWidget(title)
        layout.addWidget(self.status_indicator)
        layout.addStretch()
        self.layout.addWidget(header_frame)

    def setup_controls(self):
        control_frame = QFrame()
        layout = QHBoxLayout(control_frame)

        # Left: Buttons
        btn_layout = QVBoxLayout()
        self.btn_start = QPushButton("▶ Start Daemon")
        self.btn_start.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        self.btn_start.clicked.connect(self.start_daemon)

        self.btn_stop = QPushButton("⏹ Stop Daemon")
        self.btn_stop.setStyleSheet("background-color: #f44336; color: white; padding: 10px;")
        self.btn_stop.clicked.connect(self.stop_daemon)
        
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)

        # Right: Config Inputs
        config_layout = QVBoxLayout()
        
        # CPU Input
        cpu_layout = QHBoxLayout()
        cpu_layout.addWidget(QLabel("CPU Threshold (%):"))
        self.input_cpu = QLineEdit()
        cpu_layout.addWidget(self.input_cpu)
        
        # Disk Input
        disk_layout = QHBoxLayout()
        disk_layout.addWidget(QLabel("Disk Threshold (%):"))
        self.input_disk = QLineEdit()
        disk_layout.addWidget(self.input_disk)

        # Save Button
        self.btn_save = QPushButton("💾 Save Config")
        self.btn_save.clicked.connect(self.save_config)

        config_layout.addLayout(cpu_layout)
        config_layout.addLayout(disk_layout)
        config_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout, 1)
        layout.addLayout(config_layout, 2)
        self.layout.addWidget(control_frame)

    def setup_log_viewer(self):
        lbl = QLabel("Live System Logs:")
        lbl.setFont(QFont("Arial", 12))
        self.layout.addWidget(lbl)

        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        self.layout.addWidget(self.log_viewer)

    # Logic

    def load_config(self):
        """Reads watchdog.conf into inputs."""
        if not os.path.exists(CONFIG_FILE):
            return
        
        try:
            with open(CONFIG_FILE, 'r') as f:
                for line in f:
                    if "CPU_THRESHOLD=" in line:
                        self.input_cpu.setText(line.split('=')[1].strip())
                    elif "DISK_THRESHOLD=" in line:
                        self.input_disk.setText(line.split('=')[1].strip())
        except Exception as e:
            self.log_viewer.append(f"Config Load Error: {e}")

    def save_config(self):
        """Writes inputs to watchdog.conf."""
        cpu = self.input_cpu.text()
        disk = self.input_disk.text()
        
        if not cpu.isdigit() or not disk.isdigit():
            QMessageBox.warning(self, "Error", "Thresholds must be numbers.")
            return

        config_content = f"CPU_THRESHOLD={cpu}\nDISK_THRESHOLD={disk}\n"
        
        try:
            with open(CONFIG_FILE, 'w') as f:
                f.write(config_content)
            self.log_viewer.append(f"--- Configuration saved: CPU={cpu}%, Disk={disk}% ---")
            
            # If running, restart to apply changes? 
            # Ideally the script reloads, but for now we warn the user.
            if self.is_running():
                QMessageBox.information(self, "Saved", "Configuration saved. Restart the daemon to apply changes.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def check_status(self):
        """Checks if PID file exists and process is alive."""
        running = self.is_running()
        if running:
            self.status_indicator.setText("RUNNING")
            self.status_indicator.setStyleSheet("color: green;")
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
        else:
            self.status_indicator.setText("STOPPED")
            self.status_indicator.setStyleSheet("color: red;")
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)

    def is_running(self):
        if not os.path.exists(PID_FILE):
            return False
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            # Check if process exists (signal 0 does not kill, just checks access)
            os.kill(pid, 0)
            return True
        except (OSError, ValueError):
            return False

    def start_daemon(self):
        if not os.path.exists(SCRIPT_PATH):
            QMessageBox.critical(self, "Error", f"Script not found at {SCRIPT_PATH}")
            return
            
        # Make executable just in case
        os.chmod(SCRIPT_PATH, 0o755)
        
        try:
            subprocess.Popen([SCRIPT_PATH], cwd=os.getcwd())
            self.log_viewer.append("--- Starting Daemon... ---")
            QTimer.singleShot(500, self.check_status)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start: {e}")

    def stop_daemon(self):
        if not os.path.exists(PID_FILE):
            return
        
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            self.log_viewer.append("--- Stopping Daemon... ---")
            QTimer.singleShot(500, self.check_status)
        except Exception as e:
            self.log_viewer.append(f"Error stopping: {e}")

    def update_logs(self):
        """Reads new lines from log file."""
        if not os.path.exists(LOG_FILE):
            return

        try:
            with open(LOG_FILE, 'r') as f:
                f.seek(self.last_file_pos)
                new_data = f.read()
                self.last_file_pos = f.tell()
                
                if new_data:
                    self.log_viewer.insertPlainText(new_data)
                    self.log_viewer.verticalScrollBar().setValue(
                        self.log_viewer.verticalScrollBar().maximum()
                    )
        except Exception:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set Dark Mode style
    app.setStyle("Fusion")
    
    window = WatchdogDashboard()
    window.show()
    sys.exit(app.exec())
