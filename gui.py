"""Interfejs GUI aplikacji Folder Sorter."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

import customtkinter as ctk


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MainWindow:
    """Glowne okno aplikacji."""

    def __init__(
        self,
        on_sort_now: Callable[[], None],
        on_pause: Callable[[], None],
        on_resume: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self._on_sort_now = on_sort_now
        self._on_pause = on_pause
        self._on_resume = on_resume
        self._on_quit = on_quit
        self._paused = False

        self.root = ctk.CTk()
        self.root.title("Folder Sorter")
        self.root.geometry("480x600")
        self.root.minsize(480, 600)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)

        self._center_window(480, 600)
        self._build_ui()
        self.set_status(running=True)
        self.set_paused(paused=False)

    def _center_window(self, width: int, height: int) -> None:
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = int((screen_width - width) / 2)
        y = int((screen_height - height) / 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self) -> None:
        container = ctk.CTkFrame(self.root, corner_radius=14)
        container.pack(fill="both", expand=True, padx=18, pady=18)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(2, weight=1)

        self.title_label = ctk.CTkLabel(
            container,
            text="Folder Sorter",
            font=ctk.CTkFont(size=32, weight="bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="w", padx=18, pady=(18, 10))

        self.status_label = ctk.CTkLabel(
            container,
            text="● Aktywny",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#22C55E",
        )
        self.status_label.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 14))

        log_frame = ctk.CTkFrame(container, fg_color="transparent")
        log_frame.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 16))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_columnconfigure(1, weight=0)
        log_frame.grid_rowconfigure(0, weight=1)

        self.log_text = ctk.CTkTextbox(
            log_frame,
            wrap="word",
            corner_radius=10,
            font=ctk.CTkFont(size=13),
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_scrollbar = ctk.CTkScrollbar(log_frame, command=self.log_text.yview)
        self.log_scrollbar.grid(row=0, column=1, sticky="ns", padx=(8, 0))
        self.log_text.configure(yscrollcommand=self.log_scrollbar.set)
        self.log_text.configure(state="disabled")

        self.sort_button = ctk.CTkButton(
            container,
            text="Sortuj teraz",
            height=40,
            command=self._on_sort_now,
        )
        self.sort_button.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 10))

        self.pause_button = ctk.CTkButton(
            container,
            text="Wstrzymaj",
            height=40,
            command=self._handle_pause_resume,
        )
        self.pause_button.grid(row=4, column=0, sticky="ew", padx=18, pady=(0, 10))

        self.minimize_button = ctk.CTkButton(
            container,
            text="Minimalizuj do tray",
            height=40,
            fg_color="#374151",
            hover_color="#4B5563",
            command=self.hide,
        )
        self.minimize_button.grid(row=5, column=0, sticky="ew", padx=18, pady=(0, 10))

        self.quit_button = ctk.CTkButton(
            container,
            text="Zamknij aplikację",
            height=40,
            fg_color="#7F1D1D",
            hover_color="#991B1B",
            command=self._on_quit,
        )
        self.quit_button.grid(row=6, column=0, sticky="ew", padx=18, pady=(0, 18))

    def _handle_pause_resume(self) -> None:
        if self._paused:
            self._on_resume()
        else:
            self._on_pause()

    def show(self) -> None:
        self.root.state("normal")
        self.root.deiconify()
        self.root.lift()
        # Windows: chwilowe topmost pomaga przywrocic okno ponad inne.
        self.root.attributes("-topmost", True)
        self.root.after(50, lambda: self.root.attributes("-topmost", False))
        self.root.focus_force()

    def hide(self) -> None:
        self.root.withdraw()

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}\n"
        self.log_text.configure(state="normal")
        self.log_text.insert("end", entry)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def set_status(self, running: bool) -> None:
        if running:
            self.status_label.configure(text="● Aktywny", text_color="#22C55E")
        else:
            self.status_label.configure(text="● Wstrzymany", text_color="#EAB308")

    def set_paused(self, paused: bool) -> None:
        self._paused = paused
        self.pause_button.configure(text="Wznów" if paused else "Wstrzymaj")

    def start(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    def demo_sort_now() -> None:
        print("Sortuj teraz kliknięte")
        window.log("Ręczne sortowanie uruchomione.")


    def demo_pause() -> None:
        print("Wstrzymano")
        window.log("Monitorowanie wstrzymane.")


    def demo_resume() -> None:
        print("Wznowiono")
        window.log("Monitorowanie wznowione.")


    def demo_quit() -> None:
        print("Zamykanie aplikacji")
        window.root.destroy()


    window = MainWindow(
        on_sort_now=demo_sort_now,
        on_pause=demo_pause,
        on_resume=demo_resume,
        on_quit=demo_quit,
    )
    window.log("Aplikacja uruchomiona.")
    window.start()
