"""Okno zarzadzania niestandardowymi regulami sortowania."""

from __future__ import annotations

import customtkinter as ctk

from rules import Rule, RulesManager

_LABEL_TO_CONDITION = {
    "zawiera": "contains",
    "zaczyna się od": "startswith",
    "kończy się na": "endswith",
}

_CONDITION_TO_LABEL = {value: key for key, value in _LABEL_TO_CONDITION.items()}


class RulesWindow:
    def __init__(self, parent, rules_manager: RulesManager) -> None:
        self.parent = parent
        self.rules_manager = rules_manager

        self.window: ctk.CTkToplevel | None = None
        self.condition_menu: ctk.CTkOptionMenu | None = None
        self.value_entry: ctk.CTkEntry | None = None
        self.folder_entry: ctk.CTkEntry | None = None
        self.rules_frame: ctk.CTkScrollableFrame | None = None

    def show(self) -> None:
        if self.window is not None and self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            self._refresh_rules_list()
            return

        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("SortBox — Reguły")
        self.window.geometry("520x560")
        self.window.minsize(520, 560)
        self.window.protocol("WM_DELETE_WINDOW", self._hide)

        container = ctk.CTkFrame(self.window, corner_radius=12)
        container.pack(fill="both", expand=True, padx=16, pady=16)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(2, weight=1)

        header = ctk.CTkLabel(
            container,
            text="Reguły sortowania",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        header.grid(row=0, column=0, sticky="w", padx=14, pady=(14, 12))

        form = ctk.CTkFrame(container)
        form.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
        form.grid_columnconfigure(0, weight=1)

        self.condition_menu = ctk.CTkOptionMenu(
            form,
            values=list(_LABEL_TO_CONDITION.keys()),
        )
        self.condition_menu.set("zawiera")
        self.condition_menu.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 8))

        self.value_entry = ctk.CTkEntry(form, placeholder_text="np. faktura")
        self.value_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=8)

        self.folder_entry = ctk.CTkEntry(form, placeholder_text="np. Faktury")
        self.folder_entry.grid(row=2, column=0, sticky="ew", padx=10, pady=8)

        add_button = ctk.CTkButton(form, text="Dodaj regułę", command=self._add_rule)
        add_button.grid(row=3, column=0, sticky="ew", padx=10, pady=(8, 10))

        self.rules_frame = ctk.CTkScrollableFrame(container)
        self.rules_frame.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 12))
        self.rules_frame.grid_columnconfigure(0, weight=1)

        close_button = ctk.CTkButton(
            container,
            text="Zamknij",
            fg_color="#374151",
            hover_color="#4B5563",
            command=self._hide,
        )
        close_button.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 14))

        self._refresh_rules_list()
        self.window.lift()
        self.window.focus_force()

    def _hide(self) -> None:
        if self.window is not None and self.window.winfo_exists():
            self.window.withdraw()

    def _add_rule(self) -> None:
        if self.condition_menu is None or self.value_entry is None or self.folder_entry is None:
            return

        value = self.value_entry.get().strip()
        folder = self.folder_entry.get().strip()
        if not value or not folder:
            return

        label = self.condition_menu.get()
        condition = _LABEL_TO_CONDITION.get(label, "contains")

        rules = self.rules_manager.load()
        rules.append(Rule(condition=condition, value=value, folder=folder))
        try:
            self.rules_manager.save(rules)
        except Exception:  # noqa: BLE001
            return

        self.value_entry.delete(0, "end")
        self.folder_entry.delete(0, "end")
        self._refresh_rules_list()

    def _remove_rule(self, index: int) -> None:
        rules = self.rules_manager.load()
        if 0 <= index < len(rules):
            rules.pop(index)
            try:
                self.rules_manager.save(rules)
            except Exception:  # noqa: BLE001
                return
        self._refresh_rules_list()

    def _refresh_rules_list(self) -> None:
        if self.rules_frame is None:
            return

        for child in self.rules_frame.winfo_children():
            child.destroy()

        rules = self.rules_manager.load()
        for idx, rule in enumerate(rules):
            row = ctk.CTkFrame(self.rules_frame)
            row.grid(row=idx, column=0, sticky="ew", padx=4, pady=4)
            row.grid_columnconfigure(0, weight=1)

            label_text = f"[{_CONDITION_TO_LABEL.get(rule.condition, rule.condition)}] {rule.value} → {rule.folder}"
            label = ctk.CTkLabel(row, text=label_text, anchor="w")
            label.grid(row=0, column=0, sticky="w", padx=(10, 6), pady=8)

            remove_button = ctk.CTkButton(
                row,
                text="Usuń",
                width=72,
                fg_color="#7F1D1D",
                hover_color="#991B1B",
                command=lambda i=idx: self._remove_rule(i),
            )
            remove_button.grid(row=0, column=1, sticky="e", padx=(6, 10), pady=8)
