import json
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QTimer
from src.db import Database

class WebBridge(QObject):
    # Signals sent to JS
    taskAdded = pyqtSignal(str)      # JSON string
    taskToggled = pyqtSignal(str)    # JSON string
    taskDeleted = pyqtSignal(str)    # task_id string
    timerTicked = pyqtSignal(int, str) # remaining_seconds, mm:ss string
    timerCompleted = pyqtSignal(str, str) # type ("focus"/"break"), msg string
    statsUpdated = pyqtSignal(str)   # JSON string
    quotesUpdated = pyqtSignal(str)  # JSON string

    def __init__(self, db: Database, play_chime_callback=None, show_notification_callback=None):
        super().__init__()
        self.db = db
        self.play_chime = play_chime_callback
        self.show_notification = show_notification_callback

        # Timer state
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer_tick)
        self.timer_seconds_remaining = 0
        self.timer_total_seconds = 0
        self.timer_type = "focus"  # "focus" or "break"
        self.timer_active_name = ""

    # --- Database Sync Slots (Called from JS) ---
    @pyqtSlot(result=str)
    def getTasks(self):
        return json.dumps(self.db.get_tasks())

    @pyqtSlot(result=str)
    def getStats(self):
        return json.dumps(self.db.get_stats())

    @pyqtSlot(result=str)
    def getQuotes(self):
        return json.dumps(self.db.get_quotes())

    @pyqtSlot(result=str)
    def getSongs(self):
        """
        Scans the 'songs' directory and returns a JSON list of dictionaries
        containing: name, url, title, artist.
        """
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        songs_dir = os.path.join(base_dir, "songs")
        
        if not os.path.exists(songs_dir):
            return json.dumps([])
            
        supported_exts = ('.mp3', '.wav', '.ogg', '.m4a')
        song_list = []
        
        try:
            files = sorted(os.listdir(songs_dir), key=lambda s: s.lower())
            for f in files:
                if f.lower().endswith(supported_exts):
                    # Relative path from src/templates/index.html is ../../songs/<filename>
                    name_without_ext, _ = os.path.splitext(f)
                    title = name_without_ext
                    artist = "Way of the Ronin"
                    
                    if " - " in name_without_ext:
                        parts = name_without_ext.split(" - ", 1)
                        # Standard format is Title - Artist, but can be either.
                        # Let's keep it as is or trim it cleanly.
                        title = parts[0].strip()
                        artist = parts[1].strip()
                        
                    song_list.append({
                        "name": f,
                        "url": f"../../songs/{f}",
                        "title": title,
                        "artist": artist
                    })
        except Exception as e:
            print(f"Error scanning songs folder: {e}")
            
        return json.dumps(song_list)

    @pyqtSlot(str, result=str)
    def addTask(self, title):
        task = self.db.add_task(title)
        if task:
            task_json = json.dumps(task)
            self.taskAdded.emit(task_json)
            self.statsUpdated.emit(json.dumps(self.db.get_stats()))
            return task_json
        return ""

    @pyqtSlot(str, bool, bool, result=str)
    def toggleTask(self, task_id, completed, crossed):
        task = self.db.toggle_task(task_id, completed, crossed)
        if task:
            task_json = json.dumps(task)
            self.taskToggled.emit(task_json)
            self.statsUpdated.emit(json.dumps(self.db.get_stats()))
            return task_json
        return ""

    @pyqtSlot(str, result=bool)
    def deleteTask(self, task_id):
        success = self.db.delete_task(task_id)
        if success:
            self.taskDeleted.emit(task_id)
            self.statsUpdated.emit(json.dumps(self.db.get_stats()))
            return True
        return False

    @pyqtSlot(str, str, result=str)
    def addQuote(self, text, author):
        quote = self.db.add_quote(text, author)
        quotes_json = json.dumps(self.db.get_quotes())
        self.quotesUpdated.emit(quotes_json)
        return json.dumps(quote)

    # --- Timer Control Slots (Called from JS) ---
    @pyqtSlot(int, str, str)
    def startTimer(self, minutes, timer_type, name):
        """
        Starts a Zen Pomodoro Timer.
        timer_type: 'focus' or 'break'
        name: Name of the timer preset e.g. 'Short Rest', 'Long Rest'
        """
        self.timer.stop()
        self.timer_type = timer_type
        self.timer_active_name = name
        self.timer_total_seconds = minutes * 60
        self.timer_seconds_remaining = self.timer_total_seconds
        
        self._emit_timer_state()
        self.timer.start(1000) # Tick every second
        
        type_lbl = "Focus Session" if timer_type == "focus" else "Break Time"
        if self.show_notification:
            self.show_notification(f"Ritual Commenced", f"You have entered a {minutes}-minute {type_lbl}.")

    @pyqtSlot()
    def pauseTimer(self):
        if self.timer.isActive():
            self.timer.stop()
            if self.show_notification:
                self.show_notification("Ritual Paused", "Your focus interval has been paused.")

    @pyqtSlot()
    def resumeTimer(self):
        if not self.timer.isActive() and self.timer_seconds_remaining > 0:
            self.timer.start(1000)
            if self.show_notification:
                self.show_notification("Ritual Resumed", "Your focus interval has been resumed.")

    @pyqtSlot()
    def cancelTimer(self):
        self.timer.stop()
        self.timer_seconds_remaining = 0
        self._emit_timer_state()
        if self.show_notification:
            self.show_notification("Ritual Abandoned", "The timer has been reset.")

    # --- Internal Timer Tick ---
    def _on_timer_tick(self):
        if self.timer_seconds_remaining > 0:
            self.timer_seconds_remaining -= 1
            self._emit_timer_state()
            
            if self.timer_seconds_remaining == 0:
                self.timer.stop()
                self._on_timer_completed()

    def _emit_timer_state(self):
        mins = self.timer_seconds_remaining // 60
        secs = self.timer_seconds_remaining % 60
        time_str = f"{mins:02d}:{secs:02d}"
        self.timerTicked.emit(self.timer_seconds_remaining, time_str)

    def _on_timer_completed(self):
        # 1. Update DB stats
        if self.timer_type == "focus":
            focus_mins = self.timer_total_seconds // 60
            self.db.record_focus_session(focus_mins)
            self.statsUpdated.emit(json.dumps(self.db.get_stats()))
            msg = "Focus interval completed! You have accumulated honor and XP."
            title = "Focus Interval Complete"
        else:
            msg = "Break completed! Prepare your mind for the next strike."
            title = "Break Complete"

        # 2. Play Zen Sound Chime
        if self.play_chime:
            self.play_chime()

        # 3. Trigger Notification
        if self.show_notification:
            self.show_notification(title, msg)

        # 4. Emit Completed Signal to JS
        self.timerCompleted.emit(self.timer_type, msg)
