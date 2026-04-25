"""Obsluga ikony aplikacji w zasobniku systemowym."""

from __future__ import annotations

import threading
from typing import Callable

try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont

    _TRAY_IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as exc:
    pystray = None  # type: ignore[assignment]
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]
    _TRAY_IMPORT_ERROR = exc


class TrayIcon:
    """Zarzadza ikona tray i jej menu kontekstowym."""

    def __init__(
        self,
        on_show: Callable[[], None],
        on_pause: Callable[[], None],
        on_resume: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self._on_show = on_show
        self._on_pause = on_pause
        self._on_resume = on_resume
        self._on_quit = on_quit
        self._paused = False
        self._lock = threading.Lock()

        self._icon = None
        self._thread: threading.Thread | None = None

    def _create_image(self):
        image = Image.new("RGBA", (64, 64), (36, 112, 255, 255))
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.truetype("arial.ttf", 42)
        except OSError:
            font = ImageFont.load_default()

        text = "F"
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        text_width = right - left
        text_height = bottom - top
        x = (64 - text_width) / 2 - left
        y = (64 - text_height) / 2 - top
        draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
        return image

    def _pause_resume_label(self, _item) -> str:
        return "Wznów" if self._paused else "Wstrzymaj"

    def _handle_show(self, _icon, _item) -> None:
        self._on_show()

    def _handle_pause_resume(self, _icon, _item) -> None:
        if self._paused:
            self._on_resume()
        else:
            self._on_pause()

    def _handle_quit(self, _icon, _item) -> None:
        self._on_quit()

    def _build_menu(self):
        return pystray.Menu(
            pystray.MenuItem("Otwórz", self._handle_show, default=True),
            pystray.MenuItem(self._pause_resume_label, self._handle_pause_resume),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Wyjdź", self._handle_quit),
        )

    def start(self) -> None:
        if _TRAY_IMPORT_ERROR is not None:
            raise RuntimeError(
                "Brak zaleznosci 'pystray' lub 'Pillow'. Zainstaluj requirements.txt."
            ) from _TRAY_IMPORT_ERROR

        with self._lock:
            if self._thread and self._thread.is_alive():
                return

            self._icon = pystray.Icon(
                "folder-sorter",
                self._create_image(),
                "Folder Sorter",
                self._build_menu(),
            )
            self._thread = threading.Thread(target=self._icon.run, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        with self._lock:
            icon = self._icon
            thread = self._thread

        if icon is not None:
            icon.stop()

        current_thread = threading.current_thread()
        if thread is not None and thread.is_alive() and thread is not current_thread:
            thread.join(timeout=2)

        with self._lock:
            self._icon = None
            self._thread = None

    def set_paused(self, paused: bool) -> None:
        self._paused = paused
        if self._icon is not None:
            self._icon.update_menu()
