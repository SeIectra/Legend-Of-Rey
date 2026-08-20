"""Kalici oyuncu ayarlari (JSON).

Eski kodda ayarlar global degiskenlerde yasiyordu ve oyun kapaninca kayboluyordu.
Burada tek bir sozluk var, diske yaziliyor, eksik anahtarlar varsayilana duser.
"""
from __future__ import annotations

import json
from typing import Any

from lore.core.paths import user_file

_DEFAULTS: dict[str, Any] = {
    # Goruntu
    "scale": 0,                 # 0 = otomatik (ekrana sigan en buyuk tam sayi kat)
    "fullscreen": False,
    "vsync": True,
    "show_fps": False,
    "screen_shake": 1.0,        # 0.0 kapali - erisilebilirlik
    "flash_intensity": 1.0,     # Isik cakmalari - fotosensitivite icin kisilabilir
    "pixel_perfect": True,
    # Ses
    "master_volume": 0.9,
    "music_volume": 0.6,
    "sfx_volume": 0.8,
    # Oynanis
    "language": "tr",
    "rumble": True,
    "aim_assist": False,
    "damage_numbers": True,
    # Tus atamalari (bkz. core/input.py)
    "bindings": {},
}


class Config:
    def __init__(self) -> None:
        self._path = user_file("settings.json")
        self._data: dict[str, Any] = dict(_DEFAULTS)
        self._dirty = False
        self.load()

    # --- Erisim -------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, _DEFAULTS.get(key, default))

    def set(self, key: str, value: Any) -> None:
        if self._data.get(key) != value:
            self._data[key] = value
            self._dirty = True

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def toggle(self, key: str) -> bool:
        new = not bool(self.get(key))
        self.set(key, new)
        return new

    # --- Kalicilik ----------------------------------------------------------
    def load(self) -> None:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return                      # Ilk calistirma ya da bozuk dosya
        if isinstance(raw, dict):
            # Bilinmeyen anahtarlari yok say, eksikleri varsayilanda birak:
            # eski surumden gelen kayit dosyasi oyunu kirmaz.
            for key in _DEFAULTS:
                if key in raw:
                    self._data[key] = raw[key]

    def save(self, force: bool = False) -> None:
        if not (self._dirty or force):
            return
        try:
            self._path.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            self._dirty = False
        except OSError as exc:
            print(f"[config] kaydedilemedi: {exc}")
