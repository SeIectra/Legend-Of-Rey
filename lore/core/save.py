"""Kayit slotlari.

Uc slot, her biri bagimsiz JSON. Kayit atomik yazilir (once .tmp, sonra replace)
- oyun kaydederken kapanirsa eski kayit bozulmaz.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any

from lore.constants import GAME_VERSION
from lore.core.paths import user_file

SLOT_COUNT = 3


@dataclass
class SaveData:
    """Bir oyun kaydinin tam icerigi."""

    version: str = GAME_VERSION
    slot: int = 0               # Hangi yuvadan geldigi; kaydederken kullanilir
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    playtime: float = 0.0

    # Ilerleme
    act: int = 1
    level_id: str = "act1_01"
    checkpoint: str = ""
    levels_cleared: list[str] = field(default_factory=list)

    # Oyuncu durumu
    max_health: int = 6            # Yarim kalp = 1 birim, yani 3 kalp
    health: int = 6
    essence: int = 0
    heart_shards: int = 0

    # Kilit acilanlar
    has_blade: bool = False
    abilities: list[str] = field(default_factory=list)   # dash, double_jump, wall_jump...
    spells: list[str] = field(default_factory=list)      # ember, aegis, blink, quake
    charms: list[str] = field(default_factory=list)
    charms_equipped: list[str] = field(default_factory=list)
    skill_points: int = 0
    skills: dict[str, int] = field(default_factory=dict)

    # Kesif
    lore_fragments: list[str] = field(default_factory=list)
    secrets_found: list[str] = field(default_factory=list)
    flags: dict[str, Any] = field(default_factory=dict)

    # Istatistik
    deaths: int = 0
    kills: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SaveData":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in raw.items() if k in known})


def slot_path(slot: int):
    return user_file(f"save_{slot}.json")


def load_slot(slot: int) -> SaveData | None:
    try:
        raw = json.loads(slot_path(slot).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    try:
        return SaveData.from_dict(raw)
    except TypeError:
        return None


def save_slot(slot: int, data: SaveData) -> bool:
    data.updated_at = time.time()
    path = slot_path(slot)
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(
            json.dumps(data.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        tmp.replace(path)               # Atomik: yarim kayit dosyasi olusmaz
        return True
    except OSError as exc:
        print(f"[save] slot {slot} yazilamadi: {exc}")
        return False


def delete_slot(slot: int) -> None:
    try:
        slot_path(slot).unlink(missing_ok=True)
    except OSError:
        pass


def list_slots() -> list[SaveData | None]:
    return [load_slot(i) for i in range(SLOT_COUNT)]
