"""Dosya yollari: kaynaklar (salt okunur) ve kullanici verisi (yazilabilir).

PyInstaller ile paketlendiginde kaynaklar gecici bir dizine acilir; kayitlar
oraya yazilamaz. Bu ikisini bastan ayirmak sonradan cikan bir suru hatayi onler.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from lore.constants import SAVE_DIR_NAME


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def resource_root() -> Path:
    """Salt okunur oyun kaynaklarinin kok dizini."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parents[2]


def resource(*parts: str) -> Path:
    return resource_root().joinpath(*parts)


def user_data_root() -> Path:
    """Kayit dosyalari, ayarlar, ekran goruntuleri icin yazilabilir dizin."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = base / SAVE_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def user_file(name: str) -> Path:
    return user_data_root() / name
