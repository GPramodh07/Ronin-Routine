import os
import json
from datetime import datetime

class Database:
    def __init__(self, db_path="db.json"):
        self.db_path = db_path
        self.data = {
            "tasks": [
                {
                    "id": "task_1",
                    "title": "Complete the Dojo UI implementation",
                    "completed": False,
                    "crossed": False,
                    "created_at": datetime.now().isoformat(),
                    "completed_at": None
                },
                {
                    "id": "task_2",
                    "title": "Sharpen the katana (Review PRs)",
                    "completed": True,
                    "crossed": False,
                    "created_at": datetime.now().isoformat(),
                    "completed_at": datetime.now().isoformat()
                },
                {
                    "id": "task_3",
                    "title": "Meditate on the architecture docs",
                    "completed": False,
                    "crossed": False,
                    "created_at": datetime.now().isoformat(),
                    "completed_at": None
                }
            ],
            "timer_presets": [
                {"name": "Short Rest", "duration_mins": 30, "focus_mins": 25, "break_mins": 5},
                {"name": "Long Rest", "duration_mins": 60, "focus_mins": 50, "break_mins": 10}
            ],
            "stats": {
                "level": 1,
                "title": "Novice Ronin",
                "xp": 100,
                "total_focus_mins": 0,
                "slashed_tasks": 0,
                "sessions_completed": 0
            },
            "quotes": [
                {"text": "The focused mind can pierce through stone.", "author": "Way of the Ronin"},
                {"text": "Flow like water, strike like lightning, rest like a mountain.", "author": "Bushido Wisdom"},
                {"text": "Simplicity is the ultimate sophistication of the warrior.", "author": "Miyamoto Musashi"},
                {"text": "Do nothing that is of no use.", "author": "Miyamoto Musashi"}
            ],
            "focus_sessions": []
        }
        self.load()

    def load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    # Merge loaded data with defaults to ensure schema consistency
                    modified = False
                    for key in self.data:
                        if key in loaded_data:
                            if isinstance(self.data[key], dict) and isinstance(loaded_data[key], dict):
                                self.data[key].update(loaded_data[key])
                            else:
                                self.data[key] = loaded_data[key]
                        else:
                            modified = True
                    if modified:
                        self.save()
            except Exception as e:
                print(f"Error loading database, resetting to defaults: {e}")
                self.save()
        else:
            self.save()

    def save(self):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving database: {e}")

    # --- Task Management ---
    def get_tasks(self):
        return self.data["tasks"]

    def add_task(self, title):
        if not title.strip():
            return None
        task_id = f"task_{int(datetime.now().timestamp() * 1000)}"
        new_task = {
            "id": task_id,
            "title": title.strip(),
            "completed": False,
            "crossed": False,
            "created_at": datetime.now().isoformat(),
            "completed_at": None
        }
        self.data["tasks"].insert(0, new_task)
        self.save()
        return new_task

    def toggle_task(self, task_id, completed, crossed=False):
        for task in self.data["tasks"]:
            if task["id"] == task_id:
                old_completed = task.get("completed", False)
                
                # Set new states
                task["completed"] = completed
                task["crossed"] = crossed
                task["completed_at"] = datetime.now().isoformat() if (completed or crossed) else None
                
                # Gamified XP calculation
                if completed and not old_completed:
                    self.data["stats"]["slashed_tasks"] += 1
                    self.add_xp(10)
                elif not completed and old_completed:
                    self.data["stats"]["slashed_tasks"] = max(0, self.data["stats"]["slashed_tasks"] - 1)
                    self.add_xp(-10)
                
                self.save()
                return task
        return None

    def update_task_title(self, task_id, new_title):
        for task in self.data["tasks"]:
            if task["id"] == task_id:
                task["title"] = new_title.strip()
                self.save()
                return task
        return None

    def delete_task(self, task_id):
        initial_len = len(self.data["tasks"])
        self.data["tasks"] = [t for t in self.data["tasks"] if t["id"] != task_id]
        if len(self.data["tasks"]) < initial_len:
            self.save()
            return True
        return False

    # --- XP / Stats Management ---
    def add_xp(self, amount):
        stats = self.data["stats"]
        stats["xp"] = max(0, stats["xp"] + amount)
        
        # Calculate level: 100 XP per level
        new_level = stats["xp"] // 100
        if new_level != stats["level"]:
            stats["level"] = new_level
            # Update Title based on Level
            if new_level < 5:
                stats["title"] = "Novice Ronin"
            elif new_level < 10:
                stats["title"] = "Focus Initiate"
            elif new_level < 15:
                stats["title"] = "Disciplined"
            elif new_level < 20:
                stats["title"] = "Katana Adept"
            else:
                stats["title"] = "Focus Shogun"
        self.save()

    def record_focus_session(self, mins):
        stats = self.data["stats"]
        stats["total_focus_mins"] += mins
        stats["sessions_completed"] += 1
        # Award 25 XP per focus session completed!
        self.add_xp(25)
        
        # Record session history
        if "focus_sessions" not in self.data:
            self.data["focus_sessions"] = []
        self.data["focus_sessions"].append({
            "mins": mins,
            "completed_at": datetime.now().isoformat()
        })
        self.save()

    def get_stats(self):
        stats = self.data["stats"].copy()
        stats["focus_sessions"] = self.data.get("focus_sessions", [])
        return stats

    # --- Timer Presets ---
    def get_presets(self):
        return self.data["timer_presets"]

    def add_preset(self, name, duration_mins, focus_mins, break_mins):
        preset = {
            "name": name,
            "duration_mins": duration_mins,
            "focus_mins": focus_mins,
            "break_mins": break_mins
        }
        self.data["timer_presets"].append(preset)
        self.save()
        return preset

    # --- Wisdom / Quotes ---
    def get_quotes(self):
        return self.data["quotes"]

    def add_quote(self, text, author="Unknown"):
        quote = {"text": text, "author": author}
        self.data["quotes"].append(quote)
        self.save()
        return quote
