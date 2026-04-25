"""Powiadomienia toast Windows 11 z grupowaniem zdarzen."""

from __future__ import annotations

import subprocess
import threading


class Notifier:
    """Wysyla zbiorcze powiadomienia po krotkim oknie czasowym."""

    def __init__(self, delay: float = 3.0) -> None:
        self._delay = delay
        self._lock = threading.Lock()
        self._messages: list[str] = []
        self._timer: threading.Timer | None = None
        self._stopped = False

    def notify(self, message: str) -> None:
        with self._lock:
            if self._stopped:
                return

            self._messages.append(message)
            if self._timer is not None:
                self._timer.cancel()

            self._timer = threading.Timer(self._delay, self._flush)
            self._timer.daemon = True
            self._timer.start()

    def _flush(self) -> None:
        with self._lock:
            if self._stopped or not self._messages:
                self._timer = None
                return

            messages = self._messages[:]
            self._messages.clear()
            self._timer = None

        body = self._build_body(messages)
        self._send_toast_async(body)

    def _build_body(self, messages: list[str]) -> str:
        count = len(messages)
        if count == 1:
            return messages[0]
        if 2 <= count <= 4:
            return "\n".join(messages)
        return f"Posortowano {count} plików"

    def _send_toast_async(self, body: str) -> None:
        def _runner() -> None:
            try:
                def _ps_escape(value: str) -> str:
                    return value.replace("'", "''")

                title_value = _ps_escape("Folder Sorter")
                body_lines = body.replace("\r\n", "\n").replace("\r", "\n").split("\n")
                body_parts = [f"'{_ps_escape(line)}'" for line in body_lines]
                if not body_parts:
                    body_expr = "''"
                elif len(body_parts) == 1:
                    body_expr = body_parts[0]
                else:
                    body_expr = ' + "`n" + '.join(body_parts)

                script = (
                    "& {\n"
                    f"$title='{title_value}'\n"
                    f"$body={body_expr}\n"
                    "[Windows.UI.Notifications.ToastNotificationManager,Windows.UI.Notifications,ContentType=WindowsRuntime]|Out-Null\n"
                    "[Windows.Data.Xml.Dom.XmlDocument,Windows.Data.Xml.Dom.XmlDocument,ContentType=WindowsRuntime]|Out-Null\n"
                    "$escapedTitle=[System.Security.SecurityElement]::Escape($title)\n"
                    "$escapedBody=[System.Security.SecurityElement]::Escape($body)\n"
                    "$xml=New-Object Windows.Data.Xml.Dom.XmlDocument\n"
                    "$xml.LoadXml(\"<toast><visual><binding template='ToastGeneric'><text>$escapedTitle</text><text>$escapedBody</text></binding></visual></toast>\")\n"
                    "$appId='Microsoft.Windows.Explorer'\n"
                    "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show([Windows.UI.Notifications.ToastNotification]::new($xml))\n"
                    "}\n"
                )
                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-NonInteractive",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-Command",
                        script,
                    ],
                    shell=False,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    timeout=5,
                    check=False,
                )
            except Exception:  # noqa: BLE001
                return

        thread = threading.Thread(target=_runner, daemon=True)
        thread.start()

    def stop(self) -> None:
        with self._lock:
            self._stopped = True
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            self._messages.clear()
