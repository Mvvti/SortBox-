"""Konfiguracja aplikacji folder sorter."""

from pathlib import Path

DOWNLOADS_PATH = Path.home() / "Downloads"

CATEGORIES = {
    "Obrazy": ["jpg", "jpeg", "png", "gif", "bmp", "svg", "webp", "ico", "tiff", "heic"],
    "Dokumenty": ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv", "rtf"],
    "Wideo": ["mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v", "mpeg"],
    "Muzyka": ["mp3", "wav", "flac", "aac", "ogg", "wma", "m4a"],
    "Archiwa": ["zip", "rar", "7z", "tar", "gz", "iso"],
    "Programy": ["exe", "msi", "apk"],
    "Kod": ["py", "js", "ts", "html", "css", "json", "xml", "yaml", "sql"],
    "Inne": [],  # fallback dla nierozpoznanych i bez rozszerzenia
}
