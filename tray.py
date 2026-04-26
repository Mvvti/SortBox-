"""Obsluga ikony zasobnika systemowego przez PyQt6."""

from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


class TrayIcon:
    """Zarzadza ikona tray i menu kontekstowym."""

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

        self._tray: QSystemTrayIcon | None = None
        self._menu: QMenu | None = None
        self._toggle_action: QAction | None = None
        self._show_action: QAction | None = None
        self._quit_action: QAction | None = None

    def _create_icon(self) -> QIcon:
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#A78BFA"))
        painter.drawRoundedRect(QRect(0, 0, 64, 64), 14, 14)

        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Segoe UI", 34, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(QRect(0, 0, 64, 64), Qt.AlignmentFlag.AlignCenter, "S")
        painter.end()

        return QIcon(pixmap)

    def _toggle_label(self) -> str:
        return "Wznów" if self._paused else "Wstrzymaj"

    def _handle_show(self) -> None:
        self._on_show()

    def _handle_toggle(self) -> None:
        if self._paused:
            self._on_resume()
        else:
            self._on_pause()

    def _handle_quit(self) -> None:
        self._on_quit()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._on_show()

    def start(self) -> None:
        if self.is_running():
            return
        if not QSystemTrayIcon.isSystemTrayAvailable():
            raise RuntimeError("Zasobnik systemowy nie jest dostepny.")

        app = QApplication.instance()
        if app is None:
            raise RuntimeError("QApplication nie jest uruchomione.")

        self._menu = QMenu()
        self._show_action = QAction("Otwórz", self._menu)
        self._show_action.triggered.connect(self._handle_show)
        self._menu.addAction(self._show_action)
        self._menu.setDefaultAction(self._show_action)

        self._toggle_action = QAction(self._toggle_label(), self._menu)
        self._toggle_action.triggered.connect(self._handle_toggle)
        self._menu.addAction(self._toggle_action)

        self._menu.addSeparator()

        self._quit_action = QAction("Wyjdź", self._menu)
        self._quit_action.triggered.connect(self._handle_quit)
        self._menu.addAction(self._quit_action)

        self._tray = QSystemTrayIcon(self._create_icon(), app)
        self._tray.setToolTip("SortBox")
        self._tray.setContextMenu(self._menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def stop(self) -> None:
        if self._tray is not None:
            self._tray.hide()
            self._tray.deleteLater()

        if self._menu is not None:
            self._menu.deleteLater()

        self._tray = None
        self._menu = None
        self._toggle_action = None
        self._show_action = None
        self._quit_action = None

    def set_paused(self, paused: bool) -> None:
        self._paused = paused
        if self._toggle_action is not None:
            self._toggle_action.setText(self._toggle_label())

    def is_running(self) -> bool:
        return self._tray is not None
