"""PyQt6 GUI aplikacji SortBox."""

from __future__ import annotations

import ctypes
import ctypes.wintypes
from datetime import datetime
from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from rules import Rule, RULES_PATH, RulesManager

_LABEL_TO_CONDITION = {
    "zawiera": "contains",
    "zaczyna się od": "startswith",
    "kończy się na": "endswith",
}
_CONDITION_TO_LABEL = {value: key for key, value in _LABEL_TO_CONDITION.items()}


class MainWindow(QMainWindow):
    """Główne okno aplikacji z zakładkami Monitor/Reguły."""

    def __init__(
        self,
        on_sort_now: Callable[[], None],
        rules_manager: RulesManager,
        on_pause: Callable[[], None],
        on_resume: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        super().__init__()
        self._on_sort_now = on_sort_now
        self._rules_manager = rules_manager
        self._on_pause = on_pause
        self._on_resume = on_resume
        self._on_quit = on_quit
        self._paused = False

        self._log_edit: QTextEdit | None = None
        self._status_label: QLabel | None = None
        self._pause_button: QPushButton | None = None
        self._rules_combo: QComboBox | None = None
        self._rules_value_edit: QLineEdit | None = None
        self._rules_folder_edit: QLineEdit | None = None
        self._rules_list_layout: QVBoxLayout | None = None

        self.setWindowTitle("SortBox")
        self.resize(500, 650)
        self.setMinimumSize(500, 650)
        self._center_on_screen()

        app = QApplication.instance()
        if app is not None:
            app.setFont(QFont("Segoe UI", 13, QFont.Weight.Medium))

        self._build_ui()
        self._apply_styles()
        self._apply_titlebar_color()
        self.set_status(True)
        self.set_paused(False)
        self._refresh_rules()

    def _center_on_screen(self) -> None:
        app = QApplication.instance()
        if app is None:
            return
        screen = app.primaryScreen()
        if screen is None:
            return
        geometry = screen.availableGeometry()
        x = geometry.x() + (geometry.width() - self.width()) // 2
        y = geometry.y() + (geometry.height() - self.height()) // 2
        self.move(x, y)

    def _apply_titlebar_color(self) -> None:
        """Ustawia kolor paska tytulu przez Windows DWM API (Windows 11)."""
        try:
            # COLORREF to format BGR: #F5F0FF (RGB) → 0x00FFF0F5 (BGR)
            color = ctypes.c_int(0x00FFF0F5)
            hwnd = int(self.winId())
            # DWMWA_CAPTION_COLOR = 35
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 35, ctypes.byref(color), ctypes.sizeof(color)
            )
        except Exception:  # noqa: BLE001
            pass

    def _apply_shadow(self, widget: QWidget) -> None:
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 8)
        shadow.setColor(Qt.GlobalColor.lightGray)
        widget.setGraphicsEffect(shadow)

    def _build_ui(self) -> None:
        central = QWidget(self)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(12)
        self.setCentralWidget(central)

        title = QLabel("SortBox", self)
        title.setObjectName("TitleLabel")
        root_layout.addWidget(title)

        tab_widget = QTabWidget(self)
        tab_widget.setObjectName("MainTabs")
        root_layout.addWidget(tab_widget, 1)

        monitor_tab = QWidget(self)
        rules_tab = QWidget(self)
        tab_widget.addTab(monitor_tab, "Monitor")
        tab_widget.addTab(rules_tab, "Reguły")

        self._build_monitor_tab(monitor_tab)
        self._build_rules_tab(rules_tab)

    def _build_monitor_tab(self, tab: QWidget) -> None:
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(6, 10, 6, 10)
        layout.setSpacing(10)

        self._status_label = QLabel("● Aktywny", tab)
        self._status_label.setObjectName("StatusLabel")
        layout.addWidget(self._status_label)

        log_card = QFrame(tab)
        log_card.setObjectName("Card")
        self._apply_shadow(log_card)
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(10, 10, 10, 10)

        self._log_edit = QTextEdit(log_card)
        self._log_edit.setReadOnly(True)
        self._log_edit.setObjectName("LogEdit")
        log_layout.addWidget(self._log_edit)
        layout.addWidget(log_card, 1)

        sort_btn = QPushButton("Sortuj teraz", tab)
        sort_btn.setObjectName("PrimaryButton")
        sort_btn.clicked.connect(self._on_sort_now)
        layout.addWidget(sort_btn)

        self._pause_button = QPushButton("Wstrzymaj", tab)
        self._pause_button.setObjectName("PrimaryButton")
        self._pause_button.clicked.connect(self._handle_pause_resume)
        layout.addWidget(self._pause_button)

        minimize_btn = QPushButton("Minimalizuj do tray", tab)
        minimize_btn.setObjectName("SecondaryButton")
        minimize_btn.clicked.connect(self.hide_window)
        layout.addWidget(minimize_btn)

        close_btn = QPushButton("Zamknij aplikację", tab)
        close_btn.setObjectName("DangerButton")
        close_btn.clicked.connect(self._on_quit)
        layout.addWidget(close_btn)

    def _build_rules_tab(self, tab: QWidget) -> None:
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(6, 10, 6, 10)
        layout.setSpacing(10)

        form_card = QFrame(tab)
        form_card.setObjectName("Card")
        self._apply_shadow(form_card)
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(12, 12, 12, 12)
        form_layout.setSpacing(8)

        self._rules_combo = QComboBox(form_card)
        self._rules_combo.addItems(list(_LABEL_TO_CONDITION.keys()))
        self._rules_combo.setObjectName("RuleInput")
        form_layout.addWidget(self._rules_combo)

        self._rules_value_edit = QLineEdit(form_card)
        self._rules_value_edit.setPlaceholderText("np. faktura")
        self._rules_value_edit.setObjectName("RuleInput")
        form_layout.addWidget(self._rules_value_edit)

        self._rules_folder_edit = QLineEdit(form_card)
        self._rules_folder_edit.setPlaceholderText("np. Faktury")
        self._rules_folder_edit.setObjectName("RuleInput")
        form_layout.addWidget(self._rules_folder_edit)

        add_btn = QPushButton("Dodaj regułę", form_card)
        add_btn.setObjectName("PrimaryButton")
        add_btn.clicked.connect(self._add_rule)
        form_layout.addWidget(add_btn)

        layout.addWidget(form_card)

        rules_card = QFrame(tab)
        rules_card.setObjectName("Card")
        self._apply_shadow(rules_card)
        rules_layout = QVBoxLayout(rules_card)
        rules_layout.setContentsMargins(8, 8, 8, 8)

        area = QScrollArea(rules_card)
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        list_container = QWidget()
        self._rules_list_layout = QVBoxLayout(list_container)
        self._rules_list_layout.setContentsMargins(4, 4, 4, 4)
        self._rules_list_layout.setSpacing(8)
        self._rules_list_layout.addStretch(1)
        area.setWidget(list_container)
        rules_layout.addWidget(area)
        layout.addWidget(rules_card, 1)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background: #F5F0FF;
                font-family: "Segoe UI";
                font-size: 13px;
                font-weight: 500;
                color: #4A4A6A;
            }
            QLabel#TitleLabel {
                font-family: "Segoe UI";
                font-size: 28px;
                font-weight: 700;
                color: #4A4A6A;
                background: transparent;
            }
            QTabWidget::pane {
                border: none;
                background: #F5F0FF;
            }
            QTabBar::tab {
                background: transparent;
                border: none;
                padding: 8px 14px;
                margin-right: 6px;
                color: #6A6A85;
            }
            QTabBar::tab:selected {
                color: #4A4A6A;
                border-bottom: 3px solid #A78BFA;
                font-weight: 600;
            }
            QFrame#Card {
                background: #FFFFFF;
                border: none;
                border-radius: 12px;
            }
            QTextEdit#LogEdit {
                background: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 8px;
            }
            QPushButton#PrimaryButton {
                background: #A78BFA;
                color: #FFFFFF;
                border: none;
                border-radius: 20px;
                padding: 10px;
                font-weight: 600;
            }
            QPushButton#PrimaryButton:hover {
                background: #8B5CF6;
            }
            QPushButton#SecondaryButton {
                background: #C4B5FD;
                color: #4A4A6A;
                border: none;
                border-radius: 20px;
                padding: 10px;
                font-weight: 600;
            }
            QPushButton#SecondaryButton:hover {
                background: #A78BFA;
            }
            QPushButton#DangerButton {
                background: #BE185D;
                color: #FFFFFF;
                border: none;
                border-radius: 20px;
                padding: 10px;
                font-weight: 600;
            }
            QPushButton#DangerButton:hover {
                background: #9D174D;
            }
            QLineEdit#RuleInput, QComboBox#RuleInput {
                background: #FFFFFF;
                border: 1px solid #C4B5FD;
                border-radius: 8px;
                padding: 6px;
            }
            QComboBox#RuleInput::drop-down {
                border: none;
                width: 20px;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            """
        )

    def _handle_pause_resume(self) -> None:
        if self._paused:
            self._on_resume()
        else:
            self._on_pause()

    def _add_rule(self) -> None:
        if self._rules_combo is None or self._rules_value_edit is None or self._rules_folder_edit is None:
            return

        value = self._rules_value_edit.text().strip()
        folder = self._rules_folder_edit.text().strip()
        if not value or not folder:
            return

        condition = _LABEL_TO_CONDITION.get(self._rules_combo.currentText(), "contains")
        rules = self._rules_manager.load()
        rules.append(Rule(condition=condition, value=value, folder=folder))
        try:
            self._rules_manager.save(rules)
        except Exception:  # noqa: BLE001
            return

        self._rules_value_edit.clear()
        self._rules_folder_edit.clear()
        self._refresh_rules()

    def _remove_rule(self, index: int) -> None:
        rules = self._rules_manager.load()
        if 0 <= index < len(rules):
            rules.pop(index)
            try:
                self._rules_manager.save(rules)
            except Exception:  # noqa: BLE001
                return
        self._refresh_rules()

    def _refresh_rules(self) -> None:
        if self._rules_list_layout is None:
            return

        while self._rules_list_layout.count():
            item = self._rules_list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        rules = self._rules_manager.load()
        for idx, rule in enumerate(rules):
            row = QFrame(self)
            row.setObjectName("Card")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 8, 10, 8)
            row_layout.setSpacing(8)

            label_text = (
                f"[{_CONDITION_TO_LABEL.get(rule.condition, rule.condition)}] "
                f"{rule.value} → {rule.folder}"
            )
            label = QLabel(label_text, row)
            label.setWordWrap(True)
            row_layout.addWidget(label, 1)

            remove_btn = QPushButton("Usuń", row)
            remove_btn.setObjectName("DangerButton")
            remove_btn.setFixedWidth(84)
            remove_btn.clicked.connect(lambda _=False, i=idx: self._remove_rule(i))
            row_layout.addWidget(remove_btn)

            self._rules_list_layout.addWidget(row)

        self._rules_list_layout.addStretch(1)

    def show_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def hide_window(self) -> None:
        self.hide()

    def log(self, message: str) -> None:
        if self._log_edit is None:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._log_edit.append(f"[{timestamp}] {message}")
        scrollbar = self._log_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def set_status(self, running: bool) -> None:
        if self._status_label is None:
            return
        if running:
            self._status_label.setText("● Aktywny")
            self._status_label.setStyleSheet("color: #22C55E; font-weight: 700;")
        else:
            self._status_label.setText("● Wstrzymany")
            self._status_label.setStyleSheet("color: #EAB308; font-weight: 700;")

    def set_paused(self, paused: bool) -> None:
        self._paused = paused
        if self._pause_button is not None:
            self._pause_button.setText("Wznów" if paused else "Wstrzymaj")

    def closeEvent(self, event: QCloseEvent) -> None:
        self.hide_window()
        event.ignore()

    def start(self) -> int:
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
            app.setFont(QFont("Segoe UI", 13, QFont.Weight.Medium))
            self._center_on_screen()

        self.show_window()
        return app.exec()


if __name__ == "__main__":
    def _demo_sort_now() -> None:
        print("Sortuj teraz")
        window.log("Ręczne sortowanie uruchomione.")

    def _demo_pause() -> None:
        print("Pause")
        window.set_paused(True)
        window.set_status(False)
        window.log("Monitorowanie wstrzymane.")

    def _demo_resume() -> None:
        print("Resume")
        window.set_paused(False)
        window.set_status(True)
        window.log("Monitorowanie wznowione.")

    def _demo_quit() -> None:
        app = QApplication.instance()
        if app is not None:
            app.quit()

    app = QApplication([])
    app.setFont(QFont("Segoe UI", 13, QFont.Weight.Medium))
    window = MainWindow(
        on_sort_now=_demo_sort_now,
        rules_manager=RulesManager(RULES_PATH),
        on_pause=_demo_pause,
        on_resume=_demo_resume,
        on_quit=_demo_quit,
    )
    window.show_window()
    app.exec()
