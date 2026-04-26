"""Logika sortowania plikow w folderze Downloads."""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Callable

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
    _WATCHDOG_IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as exc:
    FileSystemEventHandler = object  # type: ignore[assignment,misc]
    Observer = None  # type: ignore[assignment]
    _WATCHDOG_IMPORT_ERROR = exc

from config import CATEGORIES, DOWNLOADS_PATH
from rules import RULES_PATH, Rule, RulesManager

TEMP_EXTENSIONS = {".crdownload", ".part", ".tmp", ".download", ".partial"}
DUPLICATES_DIR = DOWNLOADS_PATH / "Duplikaty"
_rules_manager = RulesManager(RULES_PATH)

_EXTENSION_TO_CATEGORY = {
    extension.lower(): category
    for category, extensions in CATEGORIES.items()
    if category != "Inne"
    for extension in extensions
}


def get_category(filename: str) -> str:
    """Zwroc kategorie na podstawie rozszerzenia pliku."""
    suffix = Path(filename).suffix.lower().lstrip(".")
    if not suffix:
        return "Inne"
    return _EXTENSION_TO_CATEGORY.get(suffix, "Inne")


def _get_unique_target_path(target_dir: Path, filename: str) -> Path:
    """Zwraca wolna sciezke docelowa, dodajac sufiks (1), (2), ... gdy potrzebne."""
    candidate = target_dir / filename
    if not candidate.exists():
        return candidate

    source = Path(filename)
    stem = source.stem
    suffix = source.suffix
    counter = 1

    while True:
        candidate = target_dir / f"{stem}({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _move_file(file_path: Path) -> str | None:
    """Przenies pojedynczy plik z glownego folderu Downloads do kategorii."""
    downloads_root = DOWNLOADS_PATH.resolve()

    try:
        resolved = file_path.resolve()
    except FileNotFoundError:
        return None

    # Sortujemy tylko pliki bezposrednio w glownym folderze Downloads.
    if resolved.parent != downloads_root or not resolved.is_file():
        return None
    if _is_temporary_file(resolved):
        return None

    # Nie ruszaj aktualnie uruchamianego modulu, jesli lezy w Downloads.
    try:
        current_file = Path(__file__).resolve()
    except FileNotFoundError:
        current_file = None
    if current_file and resolved == current_file:
        return None

    rules = _rules_manager.load()
    matched_rule: Rule | None = _rules_manager.match(resolved.name, rules)
    category = matched_rule.folder if matched_rule else get_category(resolved.name)
    target_dir = downloads_root / category
    target_dir.mkdir(exist_ok=True)
    is_duplicate = (target_dir / resolved.name).exists()
    if is_duplicate:
        DUPLICATES_DIR.mkdir(exist_ok=True)
        target_path = _get_unique_target_path(DUPLICATES_DIR, resolved.name)
    else:
        target_path = _get_unique_target_path(target_dir, resolved.name)

    try:
        shutil.move(str(resolved), str(target_path))
    except Exception:  # noqa: BLE001
        return None
    if is_duplicate:
        return f"{resolved.name} -> Duplikaty (duplikat)"
    if matched_rule is not None:
        return f"{resolved.name} -> {matched_rule.folder} (reguła)"
    return f"{resolved.name} -> {category}"


def _is_temporary_file(file_path: Path) -> bool:
    return file_path.suffix.lower() in TEMP_EXTENSIONS


def _wait_until_stable(
    file_path: Path,
    stable_for: float = 1.0,
    interval: float = 0.3,
    timeout: float = 60.0,
) -> bool:
    start = time.monotonic()
    last_size: int | None = None
    last_change = start

    while time.monotonic() - start < timeout:
        try:
            current_size = file_path.stat().st_size
        except FileNotFoundError:
            return False
        except OSError:
            return False

        now = time.monotonic()
        if last_size is None:
            last_size = current_size
            last_change = now
        elif current_size != last_size:
            last_size = current_size
            last_change = now
        elif now - last_change >= stable_for:
            return True

        time.sleep(interval)

    return False


def sort_existing_files() -> list[str]:
    """Jednorazowo sortuje wszystkie pliki bezposrednio w folderze Downloads."""
    messages: list[str] = []
    if not DOWNLOADS_PATH.exists():
        return messages

    for item in DOWNLOADS_PATH.iterdir():
        if not item.is_file():
            continue
        message = _move_file(item)
        if message:
            messages.append(message)
    return messages


class _DownloadsCreatedHandler(FileSystemEventHandler):
    """Handler watchdog reagujacy na nowo utworzone pliki."""

    def __init__(self, on_event: Callable[[str], None]) -> None:
        super().__init__()
        self._on_event = on_event

    def _try_move_with_retry(self, file_path: Path) -> None:
        if not _wait_until_stable(file_path):
            return

        for _ in range(5):
            message = _move_file(file_path)
            if message:
                self._on_event(message)
                return
            if not file_path.exists():
                return
            time.sleep(0.3)

    def on_created(self, event) -> None:
        try:
            if event.is_directory:
                return

            file_path = Path(event.src_path)
            if _is_temporary_file(file_path):
                return

            self._try_move_with_retry(file_path)
        except Exception:  # noqa: BLE001
            return

    def on_moved(self, event) -> None:
        try:
            if event.is_directory:
                return

            dest_path = Path(event.dest_path)
            if _is_temporary_file(dest_path):
                return

            downloads_root = DOWNLOADS_PATH.resolve()
            if dest_path.parent.resolve() != downloads_root:
                return

            self._try_move_with_retry(dest_path)
        except Exception:  # noqa: BLE001
            return


class FolderSorter:
    """Uruchamia i zatrzymuje monitorowanie folderu Downloads."""

    def __init__(self, on_event: Callable[[str], None]) -> None:
        self._on_event = on_event
        self._observer = None

    def start(self) -> None:
        if self.is_running():
            return
        if _WATCHDOG_IMPORT_ERROR is not None:
            raise RuntimeError(
                "Brak zaleznosci 'watchdog'. Zainstaluj pakiety z requirements.txt."
            ) from _WATCHDOG_IMPORT_ERROR

        DOWNLOADS_PATH.mkdir(parents=True, exist_ok=True)
        handler = _DownloadsCreatedHandler(self._on_event)
        observer = Observer()
        observer.schedule(handler, str(DOWNLOADS_PATH), recursive=False)
        observer.start()
        self._observer = observer

    def stop(self) -> None:
        if not self._observer:
            return

        self._observer.stop()
        self._observer.join(timeout=2)
        self._observer = None

    def is_running(self) -> bool:
        return self._observer is not None and self._observer.is_alive()
