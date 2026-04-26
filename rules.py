"""Model i obsluga niestandardowych regul sortowania."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

RULES_PATH = Path(__file__).parent / "rules.json"
_VALID_CONDITIONS = {"contains", "startswith", "endswith"}


@dataclass
class Rule:
    condition: str
    value: str
    folder: str


class RulesManager:
    def __init__(self, rules_path: Path) -> None:
        self.rules_path = rules_path

    def load(self) -> list[Rule]:
        try:
            if not self.rules_path.exists():
                return []

            data = json.loads(self.rules_path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                return []

            rules: list[Rule] = []
            for item in data:
                if not isinstance(item, dict):
                    continue

                condition = item.get("condition")
                value = item.get("value")
                folder = item.get("folder")

                if (
                    not isinstance(condition, str)
                    or not isinstance(value, str)
                    or not isinstance(folder, str)
                ):
                    continue
                if condition not in _VALID_CONDITIONS:
                    continue

                rules.append(Rule(condition=condition, value=value, folder=folder))

            return rules
        except Exception:  # noqa: BLE001
            return []

    def save(self, rules: list[Rule]) -> None:
        payload = [asdict(rule) for rule in rules]
        self.rules_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def match(self, filename: str, rules: list[Rule]) -> Rule | None:
        filename_l = filename.lower()

        for rule in rules:
            if rule.condition not in _VALID_CONDITIONS:
                continue

            value_l = rule.value.lower()
            if rule.condition == "contains" and value_l in filename_l:
                return rule
            if rule.condition == "startswith" and filename_l.startswith(value_l):
                return rule
            if rule.condition == "endswith" and filename_l.endswith(value_l):
                return rule

        return None
