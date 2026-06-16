<p align="center" style="display:flex; align-items:center; justify-content:center; gap:18px;">
  <img src="assets/app_icon.png" alt="Ronin Routine logo" width="96" />
  <span style="font-size:2.5rem; font-weight:700;">Ronin Routine</span>
</p>

<p align="center" style="margin-top: 0.5rem; font-size:1.1rem; color:#555;">
  A productivity-first Linux desktop companion for task focus, progress tracking, and calm workflows.
</p>

<p align="center">
  <img src="assets/bg_sumie.jpg" alt="Ronin background" width="520" />
</p>

---

## 🧘 Productivity First

Ronin Routine is designed to help you stay in the zone without distraction.
It combines lightweight system tray access, actionable reminders, and a focus-friendly audio experience to make productive time feel natural.

## ✅ What You Can Do

- **Create and edit tasks** with minimal friction, updated in real-time
- **Set monthly goals** to align daily work with bigger-picture objectives
- **Track daily progress** with automatic task refresh each day for clear momentum
- **Focus with timers** using built-in Pomodoro timers (30-min and 1-hour sessions) with pause/resume control
- **Focus with music** by listening to pleasant songs while you work
- **Receive smart reminders** through the system tray and earphone notifications
- **Meditate and find wisdom** with built-in guidance sections
- **View stats** to understand your productivity patterns
- **Customize your experience** with Dojo and Sumi-e visual themes
- **Keep your workspace clean** with a non-intrusive app that stays tucked away until needed

## 🎯 Productivity Benefits

- Maintain flow with a calm, distraction-reduced interface
- Make work visible through task and progress tracking
- Use desktop notifications as gentle nudges, not interruptions
- Build routines around focus blocks with supportive audio

---

## 🔧 Core Features

- **Multi-tab dashboard** with Tasks, Monthly Goals, Meditation, Wisdom, and Stats sections
- **Smart task management** with real-time editing, daily refresh, and progress tracking
- **Goal tracking** to break down monthly objectives into daily actionable tasks
- **Pomodoro timers** for focused work sessions (30-minute and 1-hour options with pause/resume)
- **System tray launcher** for quick access to controls and global timer status
- **Intelligent notifications** including earphone-aware reminders and system tray alerts
- **Multiple visual themes** (Dojo and Sumi-e) with dynamic background images
- **Embedded web bridge** for rich, modern responsive content
- **Linux desktop integration** with `.desktop` file for seamless app launching
- **Local `.venv` isolation** so runtime files stay separate from source

---

## ✨ Preview

<p align="center">
  <img src="assets/dashboard.png" alt="Ronin dashboard preview" width="840" />
</p>

---

## 🚀 Quick Start

```bash
./setup_env.sh
```

Then activate the environment and launch the app:

```bash
source .venv/bin/activate
python3 src/main.py
```

---

## 🧩 Requirements

- Python 3.8+
- `pip`
- `PySide6`
- `PySide6-Essentials`
- `PySide6-WebEngine`
- `requests`

Dependencies are defined in `requirements.txt`.

---

## 📁 Included Files

- `src/main.py` — application entry point
- `src/db.py` — database management for tasks, goals, and user data
- `src/tray.py` — system tray management
- `src/notification.py` — notification delivery and earphone detection
- `src/web_bridge.py` — web integration layer for frontend-backend communication
- `src/templates/index.html` — embedded UI dashboard with multiple tabs and themes
- `ronin-routine.desktop` — Linux desktop launcher file
- `assets/` — app icons and theme background images (Dojo and Sumi-e themes)

---

## 📌 Notes

- `.venv/` holds the local virtual environment.
- `db.json` and `error.txt` are runtime files and should not be committed.
- If Qt WebEngine fails on Debian/Ubuntu, install these dependencies:

```bash
sudo apt-get install -y libnss3 libasound2 libegl1 libxcomposite1 libxdamage1 libxrandr2 libxtst6 libxkbcommon0 libdbus-1-3 libxcb-xinerama0
```

---

## 🎯 Feature Guide

### Tasks Tab
- Create, edit, and mark tasks complete
- Tasks automatically refresh daily to keep your focus fresh
- Track individual task progress

### Monthly Goals
- Set high-level goals for the month
- Break goals into daily actionable steps
- Align daily tasks with long-term vision

### Timers
- Start 30-minute or 1-hour Pomodoro sessions
- Pause and resume sessions as needed
- See global timer status in the top bar

### Reminders
- System tray notifications for task reminders
- Earphone-aware notifications when headphones are detected
- Gentle nudges to keep you on track

### Themes
- **Dojo Theme** — traditional focused aesthetic
- **Sumi-e Theme** — calming ink-wash inspired design
- Switch themes on-the-fly without restarting

---

## 🛡️ Project Vision

Ronin Routine is built to help focused users manage tasks, track progress, and keep productive time feeling calm and intentional.
