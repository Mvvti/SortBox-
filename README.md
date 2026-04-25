# Folder Sorter

Folder Sorter is a Windows 11 desktop app that automatically organizes files from your `Downloads` folder into category subfolders (Images, Documents, Video, Music, Archives, Programs, Code, and more).

It includes:
- a modern GUI built with `customtkinter`
- background monitoring with `watchdog`
- a system tray icon (`pystray`)
- grouped native Windows toast notifications (PowerShell-based, no extra notification package needed)
- single-instance protection (Windows mutex)

## Features

- One-click manual sorting of current files in `Downloads`
- Real-time sorting of newly added files
- Pause/Resume monitoring from both GUI and tray menu
- Smart duplicate handling:
  - if the target filename already exists in category folder, the new file goes to `Downloads/Duplikaty`
- Temporary/incomplete download protection:
  - ignores `.crdownload`, `.part`, `.tmp`, `.download`, `.partial`
- Stability check before move (waits until file size is stable)

## Requirements

- Windows 10/11
- Python 3.11+ (tested on Python 3.12)

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

From the project directory:

```bash
python main.py
```

## Build EXE (PyInstaller)

The project already includes `build.spec` configured for:
- one-file executable
- no console window
- customtkinter data files
- tray hidden import for Windows

Build command:

```bash
pyinstaller --clean --noconfirm build.spec
```

Output:

```text
dist/folder-sorter.exe
```

## Project Structure

```text
folder-sorter/
├─ assets/
│  ├─ .gitkeep
│  └─ icon.ico
├─ build.spec
├─ config.py
├─ gui.py
├─ main.py
├─ notifier.py
├─ requirements.txt
├─ sorter.py
└─ tray.py
```

## Notes

- The app is designed for Windows behavior and APIs.
- Notifications are sent via PowerShell/Windows Runtime calls, so no external toast package is required.
- Only one app instance can run at a time.
