"""Kayit sistemi - **her zaman iki dosya.**

`save.json` yazilirken oyun cokerse dosya yarim kalir ve oyuncunun saatlerce
ilerlemesi gider. Bu affedilmez (docs/menu-ui.md 11). Bu yuzden:

  1. Once `save.tmp` yazilir
  2. Mevcut `save.json` varsa `save.bak.json`'a kopyalanir
  3. `save.tmp` atomik olarak `save.json` uzerine tasinir

Yukleme once `save.json`'u dener; bozuksa sessizce `save.bak.json`'a duser.
Iki dosya da bozuksa yeni oyun baslar - ama kullaniciya soylenir.

Kayit dizini oyun klasoru degil, kullanicinin veri klasorudur: PyInstaller
ile paketlendiginde oyun klasoru salt okunur olabilir.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.config import ECHO_TIER_CLEAR

SAVE_VERSION = 1
SAVE_NAME = "save.json"
BACKUP_NAME = "save.bak.json"
TEMP_NAME = "save.tmp"
SETTINGS_NAME = "settings.json"
APP_FOLDER = "LegendOfRey"


def user_data_dir() -> Path:
    """Yazilabilir kullanici veri dizini."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA",
                                   Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME",
                                   Path.home() / ".local" / "share"))
    path = base / APP_FOLDER
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass
class SaveData:
    """Bir oyun kaydinin tam icerigi."""

    version: int = SAVE_VERSION
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    # Ilerleme
    chapter: int = 1
    # Bolum adi dil anahtari tutar - kayit dosyasi dilden bagimsiz olmali.
    # Turkce kaydi acan Ingilizce oyuncu "Village" gormeli, "Koy" degil.
    chapter_name: str = "chapter.village"
    checkpoint: str = ""
    playtime_frames: int = 0

    # Karakter
    character: str = "rey"           # rey | ardo
    # Kazanilan yetenekler. **Liste**, bit maskesi degil: yeni yetenek
    # eklemek kayit surumunu degistirmiyor, eski kayitlar sadece ona sahip
    # olmuyor (src/systems/abilities.py).
    abilities: list = field(default_factory=list)
    max_health: int = 80
    health: int = 80

    # Ekonomi ve Yanki
    gold: int = 0
    echo_tier: int = ECHO_TIER_CLEAR

    # Kesif
    secrets_found: int = 0
    secrets_total: int = 0
    chapters_cleared: list[str] = field(default_factory=list)

    # Ekipman ve kilitler
    weapon: str = "sword"
    armor: str = "light"
    charms: list[str] = field(default_factory=list)
    abilities: list[str] = field(default_factory=list)

    # Bolum 3'un karari - B14'un twist sahnesini etkileyecek
    purple_flame_taken: bool = False

    # Istatistik
    deaths: int = 0
    best_combo: int = 0
    flags: dict[str, Any] = field(default_factory=dict)

    # --- Turetilmis ---------------------------------------------------------
    @property
    def playtime_text(self) -> str:
        """Menu kartinda gosterilecek sure: '3sa 12dk' / '3h 12m'."""
        from src.ui.i18n import t          # gec import: dongusel bagimlilik yok
        total_minutes = self.playtime_frames // (60 * 60)
        hours, minutes = divmod(total_minutes, 60)
        if hours:
            return t("save.playtime_hm", hours=hours, minutes=minutes)
        return t("save.playtime_m", minutes=minutes)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SaveData":
        known = set(cls.__dataclass_fields__)
        # Bilinmeyen alanlari yok say: eski surumden gelen kayit oyunu kirmaz.
        return cls(**{k: v for k, v in raw.items() if k in known})


# --- Dosya islemleri --------------------------------------------------------
def save_path() -> Path:
    return user_data_dir() / SAVE_NAME


def backup_path() -> Path:
    return user_data_dir() / BACKUP_NAME


def has_save() -> bool:
    """Menude DEVAM ET gorunecek mi? Yedegi de sayariz."""
    return save_path().is_file() or backup_path().is_file()


def write_save(data: SaveData) -> bool:
    """Kaydi guvenle yazar. Basarisizsa mevcut kayit bozulmaz."""
    data.updated_at = time.time()
    directory = user_data_dir()
    temp = directory / TEMP_NAME
    target = save_path()
    backup = backup_path()

    try:
        temp.write_text(
            json.dumps(data.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8")
        # Yeni kayit diske yazildiktan SONRA eskisini yedekle - once
        # yedekleyip sonra yazmak, yazma coktuğunde iki bozuk dosya birakir.
        if target.is_file():
            shutil.copy2(target, backup)
        temp.replace(target)         # Atomik
        return True
    except OSError as exc:
        print(f"[save] kaydedilemedi: {exc}")
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass
        return False


def _read(path: Path) -> SaveData | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    try:
        return SaveData.from_dict(raw)
    except TypeError:
        return None


def read_save() -> tuple[SaveData | None, str]:
    """Kaydi okur. (veri, durum) doner.

    durum: "ok" | "backup" | "none" - arayuz yedekten donuldugunu
    oyuncuya soyleyebilsin diye.
    """
    data = _read(save_path())
    if data is not None:
        return data, "ok"
    data = _read(backup_path())
    if data is not None:
        print("[save] ana kayit okunamadi, yedekten donuldu")
        return data, "backup"
    return None, "none"


def delete_save() -> None:
    for path in (save_path(), backup_path()):
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            print(f"[save] silinemedi {path.name}: {exc}")
