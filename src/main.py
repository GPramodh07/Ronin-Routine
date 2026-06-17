import sys
import os
import argparse
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import QUrl, pyqtSlot
from PyQt6.QtWebChannel import QWebChannel

# Add current dir to path to avoid import errors
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.db import Database
from src.web_bridge import WebBridge
from src.tray import RoninTrayIcon
from src.notification import NotificationHelper

class MainWindow(QMainWindow):
    def __init__(self, db: Database, dev_mode=False):
        super().__init__()
        self.db = db
        self.dev_mode = dev_mode
        self.is_quitting = False

        self.setWindowTitle("Ronin Routine")
        self.resize(1366, 768)

        # Paths setup
        self.app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.icon_path = os.path.join(self.app_dir, "assets", "app_icon.png")
        self.chime_path = os.path.join(self.app_dir, "assets", "zen_chime.wav")

        # Create assets folder if missing
        os.makedirs(os.path.join(self.app_dir, "assets"), exist_ok=True)

        # 1. Setup Notification Helper
        self.notifier = NotificationHelper(app_icon_path=self.icon_path)

        # 2. Setup Web Bridge
        self.bridge = WebBridge(
            self.db,
            play_chime_callback=self.play_chime,
            show_notification_callback=self.show_notification
        )

        # 4. Setup System Tray Icon
        self.tray_icon = RoninTrayIcon(self.icon_path, self)
        self.tray_icon.open_window_requested.connect(self.reveal_window)
        self.tray_icon.quit_requested.connect(self.depart_dojo)
        self.tray_icon.quick_timer_requested.connect(self.bridge.startTimer)
        self.tray_icon.pause_timer_requested.connect(self.bridge.pauseTimer)
        self.tray_icon.resume_timer_requested.connect(self.bridge.resumeTimer)
        
        # Connect bridge timer ticks to update tray enablement states
        self.bridge.timerTicked.connect(self.update_tray_timer_state)
        
        self.tray_icon.show()

        # 5. Setup UI Layout
        self.setup_ui()

    def setup_ui(self):
        # Create WebEngine view
        self.web_view = QWebEngineView()
        
        # Enable developer settings
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        
        if self.dev_mode:
            settings.setAttribute(QWebEngineSettings.WebAttribute.DeveloperExtrasEnabled, True)

        # Setup Web Channel for Python-JS communication
        self.channel = QWebChannel()
        self.channel.registerObject("pyBridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        # Load main HTML template
        template_path = os.path.join(self.app_dir, "src", "templates", "index.html")
        if not os.path.exists(template_path):
            print(f"Template path missing, will create it shortly: {template_path}")
        
        self.web_view.setUrl(QUrl.fromLocalFile(template_path))

        # Set central widget
        self.setCentralWidget(self.web_view)

    def play_chime(self):
        """Plays a zen meditation chime sound. Uses a background thread to attempt playing via CLI sound servers (pw-play, paplay, aplay) sequentially with verify-and-fallback logic, ensuring audio routes properly when earphones are plugged in."""
        import threading
        import subprocess
        import shutil

        # Trigger HTML5 audio chime in the webview
        try:
            self.bridge.chimeTriggered.emit()
        except Exception as e:
            print(f"Error emitting chimeTriggered signal: {e}")

        def _play_thread():
            if not os.path.exists(self.chime_path):
                print(f"Chime audio file not found at: {self.chime_path}")
                return

            players = [
                ["pw-play", self.chime_path],
                ["paplay", self.chime_path],
                ["aplay", self.chime_path]
            ]

            played_successfully = False
            for cmd in players:
                try:
                    if shutil.which(cmd[0]):
                        print(f"Attempting to play zen chime via {cmd[0]}...")
                        # Execute and wait for return code
                        res = subprocess.run(cmd, capture_output=True, text=True)
                        if res.returncode == 0:
                            print(f"Zen chime played successfully via {cmd[0]}")
                            played_successfully = True
                            break
                        else:
                            print(f"{cmd[0]} failed with return code {res.returncode}: {res.stderr.strip()}")
                except Exception as e:
                    print(f"Playback error via {cmd[0]}: {e}")

            if not played_successfully:
                print("All CLI sound servers failed. Triggering motherboard beep fallback...")
                try:
                    QApplication.beep()
                except Exception as e:
                    print(f"Fallback motherboard beep failed: {e}")

        threading.Thread(target=_play_thread, daemon=True).start()

    def show_notification(self, title, message, urgency="normal"):
        """Triggers system notification via notifier."""
        self.notifier.send(title, message, tray_icon=self.tray_icon, urgency=urgency)

    def update_tray_timer_state(self, seconds_remaining, time_str, timer_type=None):
        """Update System Tray Tooltip and pause/resume enablement actions."""
        active = self.bridge.timer.isActive()
        if seconds_remaining > 0:
            status = "Focusing" if self.bridge.timer_type == "focus" else "Resting"
            self.tray_icon.setToolTip(f"Ronin Routine: {status} ({time_str})")
        else:
            self.tray_icon.setToolTip("Ronin Routine - Mindful Focus")
        
        self.tray_icon.update_timer_state(active, seconds_remaining)

    def reveal_window(self):
        """Show window, restore it if minimized, and raise it to focus."""
        self.show()
        if self.isMinimized():
            self.showNormal()
        self.activateWindow()

    def closeEvent(self, event):
        """Intercept main window close events. Minimize to system tray instead of exiting."""
        if self.is_quitting:
            event.accept()
        else:
            event.ignore()
            self.hide()
            self.show_notification(
                "Dojo Minimized", 
                "Ronin Routine is still guarding your focus in the system tray."
            )

    def depart_dojo(self):
        """Clean quit trigger called from system tray or global quit."""
        self.is_quitting = True
        self.tray_icon.hide()
        QApplication.quit()

def main():
    parser = argparse.ArgumentParser(description="Ronin Routine Desktop Focus Application")
    parser.add_argument("--dev", action="store_true", help="Launch with Qt Developer tools enabled")
    args = parser.parse_args()

    # Create app
    app = QApplication(sys.argv)
    app.setApplicationName("Ronin Routine")
    
    # Establish local database
    db_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db.json")
    db = Database(db_file)

    # Initialize main window
    window = MainWindow(db, dev_mode=args.dev)
    
    # Check if a custom icon exists to set on the main window
    if os.path.exists(window.icon_path):
        from PyQt6.QtGui import QIcon
        app.setWindowIcon(QIcon(window.icon_path))
        window.setWindowIcon(QIcon(window.icon_path))

    window.reveal_window()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
