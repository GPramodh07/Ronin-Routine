from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal

class RoninTrayIcon(QSystemTrayIcon):
    open_window_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    quick_timer_requested = pyqtSignal(int, str, str) # mins, type, name
    pause_timer_requested = pyqtSignal()
    resume_timer_requested = pyqtSignal()

    def __init__(self, icon_path, parent=None):
        icon = QIcon(icon_path)
        super().__init__(icon, parent)
        self.setToolTip("Ronin Routine - Mindful Focus")
        
        self.setup_menu()
        self.activated.connect(self._on_activated)

    def setup_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #1d100e;
                color: #f8dcd8;
                border: 1px solid #aa8984;
                font-family: 'JetBrains Mono', 'Hanken Grotesk', sans-serif;
            }
            QMenu::item {
                padding: 8px 24px;
            }
            QMenu::item:selected {
                background-color: #8b0000;
                color: #ffffff;
            }
        """)

        # Main window actions
        open_action = QAction("Open Dojo", self)
        open_action.triggered.connect(self.open_window_requested.emit)
        menu.addAction(open_action)
        menu.addSeparator()

        # Quick timer controls
        short_rest = QAction("Short Rest (30m)", self)
        short_rest.triggered.connect(lambda: self.quick_timer_requested.emit(30, "focus", "Short Rest"))
        menu.addAction(short_rest)

        long_rest = QAction("Long Rest (1h)", self)
        long_rest.triggered.connect(lambda: self.quick_timer_requested.emit(60, "focus", "Long Rest"))
        menu.addAction(long_rest)
        
        menu.addSeparator()

        # Pause/Resume controls
        self.pause_action = QAction("Pause Focus", self)
        self.pause_action.triggered.connect(self.pause_timer_requested.emit)
        menu.addAction(self.pause_action)

        self.resume_action = QAction("Resume Focus", self)
        self.resume_action.triggered.connect(self.resume_timer_requested.emit)
        self.resume_action.setEnabled(False) # Enable when paused
        menu.addAction(self.resume_action)

        menu.addSeparator()

        # Exit action
        quit_action = QAction("Depart Dojo (Exit)", self)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

    def _on_activated(self, reason):
        # Trigger window toggle on click or double click
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.open_window_requested.emit()

    def update_timer_state(self, active, seconds_remaining):
        """Enable/disable context menu items based on whether timer is running."""
        if seconds_remaining > 0:
            self.pause_action.setEnabled(active)
            self.resume_action.setEnabled(not active)
        else:
            self.pause_action.setEnabled(False)
            self.resume_action.setEnabled(False)
