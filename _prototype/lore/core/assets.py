"""Kaynak yoneticisi: her sey bir kez yuklenir/uretilir ve onbellege alinir.

Eski kodda `boss.py` her karede diskten PNG yukluyordu ve her dusman kendi ses
nesnesini ayri ayri aciyordu. Burada tek bir kapi var: `Assets.image(...)`,
`Assets.sound(...)`, `Assets.font(...)`.

Prosedurel sanat da ayni onbellegi kullanir: `Assets.generated(key, factory)`
verilen anahtar icin uretici fonksiyonu yalnizca ilk cagirmada calistirir.
"""
from __future__ import annotations

from typing import Callable

import pygame

from lore.core.paths import resource


class Assets:
    def __init__(self) -> None:
        self._images: dict[str, pygame.Surface] = {}
        self._sounds: dict[str, pygame.mixer.Sound | None] = {}
        self._fonts: dict[tuple[str, int, bool], pygame.font.Font] = {}
        self._generated: dict[str, object] = {}
        self._missing: set[str] = set()

    # --- Gorseller ----------------------------------------------------------
    def image(self, path: str, alpha: bool = True) -> pygame.Surface:
        """Diskten gorsel yukler. Bulunamazsa gorunur bir "eksik doku" doner.

        Cokmek yerine mor-siyah dama deseni donduruyoruz: eksik dosya oyunu
        durdurmaz ama gozden de kacmaz.
        """
        key = f"{path}|{alpha}"
        cached = self._images.get(key)
        if cached is not None:
            return cached
        try:
            surface = pygame.image.load(str(resource(path)))
            surface = surface.convert_alpha() if alpha else surface.convert()
        except (pygame.error, FileNotFoundError):
            if path not in self._missing:
                self._missing.add(path)
                print(f"[assets] eksik gorsel: {path}")
            surface = self._placeholder()
        self._images[key] = surface
        return surface

    @staticmethod
    def _placeholder(size: int = 16) -> pygame.Surface:
        surface = pygame.Surface((size, size)).convert()
        half = size // 2
        surface.fill((255, 0, 220))
        pygame.draw.rect(surface, (20, 20, 20), (0, 0, half, half))
        pygame.draw.rect(surface, (20, 20, 20), (half, half, half, half))
        return surface

    @staticmethod
    def exists(path: str) -> bool:
        """Bir kaynak dosyasi diskte var mi? (Tur farketmez.)"""
        return resource(path).is_file()

    # --- Uretilmis icerik ---------------------------------------------------
    def generated(self, key: str, factory: Callable[[], object]):
        """Prosedurel uretimi onbellege alir.

        Sprite uretimi pahali; her cagirmada yeniden uretmek kabul edilemez.
        Anahtari uretim parametrelerini icerecek sekilde kur.
        """
        value = self._generated.get(key)
        if value is None:
            value = factory()
            self._generated[key] = value
        return value

    def put(self, key: str, value: object) -> None:
        self._generated[key] = value

    # --- Sesler -------------------------------------------------------------
    def sound(self, path: str) -> pygame.mixer.Sound | None:
        if path in self._sounds:
            return self._sounds[path]
        sound: pygame.mixer.Sound | None = None
        if pygame.mixer.get_init():
            try:
                sound = pygame.mixer.Sound(str(resource(path)))
            except (pygame.error, FileNotFoundError):
                if path not in self._missing:
                    self._missing.add(path)
                    print(f"[assets] eksik ses: {path}")
        self._sounds[path] = sound
        return sound

    def put_sound(self, key: str, sound: pygame.mixer.Sound | None) -> None:
        self._sounds[key] = sound

    # --- Yazi tipleri -------------------------------------------------------
    def font(self, name: str = "", size: int = 8, bold: bool = False) -> pygame.font.Font:
        key = (name, size, bold)
        cached = self._fonts.get(key)
        if cached is not None:
            return cached
        font: pygame.font.Font | None = None
        if name:
            candidate = resource("assets", "fonts", name)
            if candidate.is_file():
                try:
                    font = pygame.font.Font(str(candidate), size)
                except pygame.error:
                    font = None
        if font is None:
            font = pygame.font.SysFont("consolas,dejavusansmono,couriernew", size, bold=bold)
        self._fonts[key] = font
        return font

    # --- Bakim --------------------------------------------------------------
    def clear_generated(self) -> None:
        """Act degisiminde uretilmis dokulari birak: bellek sisip kalmaz."""
        self._generated.clear()

    def stats(self) -> str:
        return (f"gorseller={len(self._images)} sesler={len(self._sounds)} "
                f"uretilmis={len(self._generated)} eksik={len(self._missing)}")
