"""Punkt wejscia aplikacji Folder Sorter."""

from __future__ import annotations

import ctypes
import sys
import threading
from typing import Callable

from gui import MainWindow
from notifier import Notifier
from sorter import FolderSorter, sort_existing_files
from tray import TrayIcon

_MUTEX_NAME = "Global\\FolderSorterSingleInstanceMutex"
_ERROR_ALREADY_EXISTS = 183


def _acquire_single_instance_mutex() -> int | None:
    """Zwraca uchwyt mutexu albo None, gdy instancja juz dziala."""
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, _MUTEX_NAME)
    if not handle:
        return None

    if ctypes.windll.kernel32.GetLastError() == _ERROR_ALREADY_EXISTS:
        ctypes.windll.kernel32.CloseHandle(handle)
        return None

    return handle


def _release_single_instance_mutex(handle: int | None) -> None:
    if handle:
        ctypes.windll.kernel32.CloseHandle(handle)


class App:
    """Koordynuje GUI, tray i monitorowanie folderu."""

    def __init__(self) -> None:
        self._paused = False
        self._quitting = False
        self._state_lock = threading.Lock()
        self.notifier = Notifier()

        self.window = MainWindow(
            on_sort_now=self.on_sort_now,
            on_pause=self.on_pause,
            on_resume=self.on_resume,
            on_quit=self.on_quit,
        )
        self.tray = TrayIcon(
            on_show=self.on_show,
            on_pause=self.on_pause,
            on_resume=self.on_resume,
            on_quit=self.on_quit,
        )
        self.sorter = FolderSorter(on_event=self.on_event)

    def _log_threadsafe(self, message: str) -> None:
        try:
            self.window.root.after(0, lambda m=message: self.window.log(m))
        except Exception:  # noqa: BLE001
            pass

    def _sync_paused_state(self) -> None:
        paused = self._paused
        running = not paused
        self.window.root.after(0, lambda p=paused, r=running: self._apply_gui_state(p, r))
        self.tray.set_paused(self._paused)

    def _apply_gui_state(self, paused: bool, running: bool) -> None:
        self.window.set_paused(paused)
        self.window.set_status(running=running)

    def _run_sort_and_log(self, done_message: str | None = None) -> None:
        try:
            results = sort_existing_files()
            if results:
                for message in results:
                    self._log_threadsafe(message)
            else:
                self._log_threadsafe("Brak plikow do posortowania.")
            if done_message:
                self._log_threadsafe(done_message)
        except Exception as exc:  # noqa: BLE001
            self._log_threadsafe(f"Blad sortowania: {exc}")

    def _run_in_thread(self, target: Callable[[], None]) -> None:
        thread = threading.Thread(target=target, daemon=True)
        thread.start()

    def on_sort_now(self) -> None:
        self._run_in_thread(
            lambda: self._run_sort_and_log("Sortowanie reczne zakonczone.")
        )

    def on_pause(self) -> None:
        with self._state_lock:
            if self._paused or self._quitting:
                return
            self.sorter.stop()
            self.notifier.stop()
            self._paused = True
            self._sync_paused_state()
        self._log_threadsafe("Monitorowanie wstrzymane.")

    def on_resume(self) -> None:
        with self._state_lock:
            if not self._paused or self._quitting:
                return
            try:
                self.sorter.start()
            except Exception as exc:  # noqa: BLE001
                self._log_threadsafe(f"Nie mozna wznowic monitorowania: {exc}")
                return
            self.notifier = Notifier()
            self._paused = False
            self._sync_paused_state()
        self._log_threadsafe("Monitorowanie wznowione.")

    def on_show(self) -> None:
        try:
            self.window.root.after(0, self.window.show)
            self.window.root.after(120, self.window.show)
        except Exception:  # noqa: BLE001
            pass

    def on_quit(self) -> None:
        with self._state_lock:
            if self._quitting:
                return
            self._quitting = True
            self.notifier.stop()
            self.sorter.stop()
            self.tray.stop()
        self.window.root.after(0, self.window.root.destroy)

    def on_event(self, message: str) -> None:
        self._log_threadsafe(message)
        with self._state_lock:
            should_notify = not self._paused and not self._quitting
        if should_notify:
            self.notifier.notify(message)

    def run(self) -> None:
        self.window.log("Aplikacja uruchomiona. Monitorowanie aktywne.")

        try:
            self.sorter.start()
        except Exception as exc:  # noqa: BLE001
            self.window.log(f"Nie mozna uruchomic monitorowania: {exc}")
            self._paused = True

        try:
            self.tray.start()
        except Exception as exc:  # noqa: BLE001
            self.window.log(f"Nie mozna uruchomic ikony tray: {exc}")

        self._sync_paused_state()
        self._run_in_thread(self._run_sort_and_log)
        self.window.start()


if __name__ == "__main__":
    mutex_handle = _acquire_single_instance_mutex()
    if mutex_handle is None:
        sys.exit(0)

    try:
        App().run()
    finally:
        _release_single_instance_mutex(mutex_handle)
