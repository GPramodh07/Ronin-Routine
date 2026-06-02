import json
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QTimer
from src.db import Database

class WebBridge(QObject):
    # Signals sent to JS
    taskAdded = pyqtSignal(str)      # JSON string
    taskToggled = pyqtSignal(str)    # JSON string
    taskDeleted = pyqtSignal(str)    # task_id string
    taskUpdated = pyqtSignal(str)    # JSON string
    timerTicked = pyqtSignal(int, str, str) # remaining_seconds, mm:ss string, timer_type
    timerCompleted = pyqtSignal(str, str) # type ("focus"/"break"), msg string
    timerPaused = pyqtSignal()
    timerResumed = pyqtSignal()
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
    def editTask(self, task_id, new_title):
        task = self.db.update_task_title(task_id, new_title)
        if task:
            task_json = json.dumps(task)
            self.taskUpdated.emit(task_json)
            return task_json
        return ""

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
        
        # Override initial focus durations for split presets
        if name == "Short Rest" and timer_type == "focus":
            minutes = 25
        elif name == "Long Rest" and timer_type == "focus":
            minutes = 50
            
        self.timer_total_seconds = minutes * 60
        self.timer_seconds_remaining = self.timer_total_seconds
        
        self._emit_timer_state()
        self.timer.start(1000) # Tick every second

    @pyqtSlot()
    def pauseTimer(self):
        if self.timer.isActive():
            self.timer.stop()
            self.timerPaused.emit()

    @pyqtSlot()
    def resumeTimer(self):
        if not self.timer.isActive() and self.timer_seconds_remaining > 0:
            self.timer.start(1000)
            self.timerResumed.emit()

    @pyqtSlot()
    def cancelTimer(self):
        self.timer.stop()
        self.timer_seconds_remaining = self.timer_total_seconds
        self._emit_timer_state()
        self.timerPaused.emit()

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
        self.timerTicked.emit(self.timer_seconds_remaining, time_str, self.timer_type)

    def _on_timer_completed(self):
        # 1. Check if it's a transition from focus to break for split presets
        if self.timer_type == "focus":
            if self.timer_active_name == "Short Rest":
                # Record 25 mins focus in DB
                self.db.record_focus_session(25)
                self.statsUpdated.emit(json.dumps(self.db.get_stats()))
                
                # Notify & Chime
                if self.play_chime:
                    self.play_chime()
                if self.show_notification:
                    self.show_notification("Time to Break", "Focus interval completed! Time to take a 5-minute break.")
                
                # Auto transition to break timer
                self.startTimer(5, "break", "Short Rest")
                return
                
            elif self.timer_active_name == "Long Rest":
                # Record 50 mins focus in DB
                self.db.record_focus_session(50)
                self.statsUpdated.emit(json.dumps(self.db.get_stats()))
                
                # Notify & Chime
                if self.play_chime:
                    self.play_chime()
                if self.show_notification:
                    self.show_notification("Time to Break", "Focus interval completed! Time to take a 10-minute break.")
                
                # Auto transition to break timer
                self.startTimer(10, "break", "Long Rest")
                return

        # 2. Normal completion (non-split custom/artisan timers or break timers)
        if self.timer_type == "focus":
            focus_mins = self.timer_total_seconds // 60
            self.db.record_focus_session(focus_mins)
            self.statsUpdated.emit(json.dumps(self.db.get_stats()))
            msg = "Focus interval completed! You have accumulated honor and XP."
            title = "Focus Interval Complete"
        else:
            msg = "Break completed! Prepare your mind for the next strike."
            title = "Break Complete"

        # Play Zen Sound Chime
        if self.play_chime:
            self.play_chime()

        # Trigger Notification
        if self.show_notification:
            self.show_notification(title, msg)

        # Emit Completed Signal to JS
        self.timerCompleted.emit(self.timer_type, msg)
