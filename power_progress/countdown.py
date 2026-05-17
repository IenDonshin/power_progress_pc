from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import os
from typing import Any
from uuid import uuid4


DATETIME_FORMAT = "%Y-%m-%d %H:%M"
DATETIME_FORMAT_LABEL = "YYYY-MM-DD HH:MM"


def default_storage_path() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "PowerProgressPC" / "countdowns.json"
    return Path.home() / ".power_progress_pc" / "countdowns.json"


@dataclass(frozen=True)
class CountdownEvent:
    title: str
    target: datetime
    id: str = field(default_factory=lambda: uuid4().hex)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "title": self.title,
            "target": self.target.isoformat(timespec="minutes"),
            "created_at": self.created_at.isoformat(timespec="seconds"),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CountdownEvent":
        return cls(
            id=str(data["id"]),
            title=str(data["title"]),
            target=datetime.fromisoformat(str(data["target"])),
            created_at=datetime.fromisoformat(str(data.get("created_at", datetime.now().isoformat()))),
        )


@dataclass(frozen=True)
class CountdownSnapshot:
    is_past: bool
    days: int
    hours: int
    minutes: int
    seconds: int

    def label(self) -> str:
        return f"{self.days}D {self.hours}H {self.minutes}M"


def parse_target(value: str) -> datetime:
    try:
        return datetime.strptime(value.strip(), DATETIME_FORMAT)
    except ValueError as exc:
        raise ValueError(f"请按 {DATETIME_FORMAT_LABEL} 格式输入时间") from exc


def countdown_snapshot(target: datetime, now: datetime | None = None) -> CountdownSnapshot:
    now = now or datetime.now()
    delta = target - now
    is_past = delta.total_seconds() < 0
    total_seconds = abs(int(delta.total_seconds()))

    days, remainder = divmod(total_seconds, 24 * 60 * 60)
    hours, remainder = divmod(remainder, 60 * 60)
    minutes, seconds = divmod(remainder, 60)

    return CountdownSnapshot(
        is_past=is_past,
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
    )


class CountdownStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_storage_path()

    def load(self) -> list[CountdownEvent]:
        if not self.path.exists():
            return []

        with self.path.open("r", encoding="utf-8") as file:
            raw = json.load(file)

        if not isinstance(raw, list):
            raise ValueError("倒数日数据文件格式无效")

        events = [CountdownEvent.from_dict(item) for item in raw if isinstance(item, dict)]
        return sorted(events, key=lambda event: event.target)

    def save(self, events: list[CountdownEvent]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump([event.to_dict() for event in events], file, ensure_ascii=False, indent=2)
