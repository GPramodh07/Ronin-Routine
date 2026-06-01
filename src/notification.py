import subprocess
import os

class NotificationHelper:
    def __init__(self, app_icon_path=None):
        self.app_icon_path = app_icon_path or ""
        # Check if notify-send is available on system
        self.has_notify_send = self._check_command("notify-send")
        self.has_kdialog = self._check_command("kdialog")

    def _check_command(self, cmd):
        try:
            subprocess.run([cmd, "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            return False

    def send(self, title, message, tray_icon=None):
        """
        Sends a native Linux KDE notification.
        If a tray_icon is provided and supports showMessage, use it.
        Otherwise, fall back to native notify-send or kdialog.
        """
        print(f"Notification triggered: {title} - {message}")

        # 1. Try QSystemTrayIcon if active
        if tray_icon:
            try:
                # QSystemTrayIcon.MessageIcon.Information
                tray_icon.showMessage(title, message, tray_icon.icon(), 10000)
                return
            except Exception as e:
                print(f"Tray notification failed, trying fallback: {e}")

        # 2. Try notify-send (highly integrated with KDE Plasma notification center)
        if self.has_notify_send:
            try:
                cmd = ["notify-send", "-a", "Ronin Routine", title, message]
                if self.app_icon_path and os.path.exists(self.app_icon_path):
                    cmd.extend(["-i", self.app_icon_path])
                subprocess.Popen(cmd)
                return
            except Exception as e:
                print(f"notify-send failed: {e}")

        # 3. Try kdialog (KDE specific backup)
        if self.has_kdialog:
            try:
                subprocess.Popen(["kdialog", "--title", "Ronin Routine", "--passivepopup", f"{title}\n{message}", "10"])
                return
            except Exception as e:
                print(f"kdialog failed: {e}")
