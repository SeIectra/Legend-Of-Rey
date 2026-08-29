"""Metin: Turkce dogru bitmap font ve buyuk/kucuk harf donusumu.

**Neden kendi fontumuz var:** 480x270 ic cozunurlukte sistem yazi tipleri
bulanik ve karaktersiz kalir. Elle cizilmis 5x11 glif tablosu (font_data.py)
hem keskin hem Turkce'nin tamamini kapsiyor.

**Turkce buyuk/kucuk harf kritik:** Python'un `str.upper()` fonksiyonu Turkce
icin yanlistir. Noktasiz i ile noktali i ayri harflerdir:

    "isik".upper()      -> "ISIK"   (yanlis - noktali I olmali)
    tr_upper("isik")    -> dogru sonuc
    "IRMAK".lower()     -> "irmak"  (yanlis - noktasiz i olmali)

Menude buyuk harf kullanilan her yerde `tr_upper()` cagrilir, `str.upper()`
asla. Dogrulama: tests/test_text.py
"""
from __future__ import annotations

import unicodedata

import pygame

from src.art import palette
from src.ui.font_data import (
    ALIASES, GLYPH_HEIGHT, GLYPH_WIDTH, GLYPHS, LINE_GAP, TRACKING,
)

# --- Turkce buyuk/kucuk harf ------------------------------------------------
# Yalnizca Python'un yanlis yaptigi dort harf ozel islem gorur; gerisini
# standart upper/lower dogru cevirir.
_UPPER_MAP = str.maketrans({
    "i": "İ",   # i -> noktali I
    "ı": "I",   # noktasiz i -> I
})
_LOWER_MAP = str.maketrans({
    "I": "ı",   # I -> noktasiz i
    "İ": "i",   # noktali I -> i
})


def tr_upper(value: str) -> str:
    """Turkce'ye dogru buyuk harf donusumu."""
    return value.translate(_UPPER_MAP).upper()


def tr_lower(value: str) -> str:
    """Turkce'ye dogru kucuk harf donusumu."""
    return value.translate(_LOWER_MAP).lower()


def nfc(value: str) -> str:
    """Metni NFC bicimine sabitler.

    Turkce harfler kaynak dosyaya ayristirilmis (NFD) yazilabiliyor: "C" +
    birlesik sedilla gibi. Tek bicime indirgemezsek tablo aramasi kacirir ve
    harfler bozuk gorunur.
    """
    return unicodedata.normalize("NFC", value)


# --- Font -------------------------------------------------------------------
class BitmapFont:
    """Glif maskelerini bir kez cozer, her renk icin onbellekler."""

    CACHE_LIMIT = 900

    def __init__(self) -> None:
        self._masks: dict[str, list[str]] = {}
        for char, pattern in GLYPHS.items():
            rows = pattern.split("/")
            if len(rows) != GLYPH_HEIGHT:
                raise ValueError(
                    f"glif {char!r} {len(rows)} satir, {GLYPH_HEIGHT} olmali")
            self._masks[nfc(char)] = rows
        self._cache: dict[tuple, pygame.Surface] = {}
        self._missing: set[str] = set()

    def has(self, char: str) -> bool:
        return self._resolve(char) is not None

    def _resolve(self, char: str) -> list[str] | None:
        return self._masks.get(ALIASES.get(char, char))

    def measure(self, value: str, tracking: int = TRACKING) -> tuple[int, int]:
        if not value:
            return 0, GLYPH_HEIGHT
        lines = nfc(value).split("\n")
        width = max(max(0, len(line) * (GLYPH_WIDTH + tracking) - tracking)
                    for line in lines)
        height = len(lines) * (GLYPH_HEIGHT + LINE_GAP) - LINE_GAP
        return width, height

    def render(self, value: str, color: palette.RGB,
               tracking: int = TRACKING) -> pygame.Surface:
        key = (value, color, tracking)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        lines = nfc(value).split("\n")
        width, height = self.measure(value, tracking)
        surface = pygame.Surface((max(1, width), max(1, height)), pygame.SRCALPHA)
        surface = surface.convert_alpha()

        step = GLYPH_WIDTH + tracking
        line_step = GLYPH_HEIGHT + LINE_GAP
        for row_index, line in enumerate(lines):
            origin_y = row_index * line_step
            for column, char in enumerate(line):
                mask = self._resolve(char)
                if mask is None:
                    self._note_missing(char)
                    continue
                origin_x = column * step
                for y, row in enumerate(mask):
                    for x, cell in enumerate(row):
                        if cell == "#":
                            surface.set_at((origin_x + x, origin_y + y), color)

        # HUD'da her kare degisen sayaclar var; onbellek sinirsiz buyumesin.
        if len(self._cache) > self.CACHE_LIMIT:
            self._cache.clear()
        self._cache[key] = surface
        return surface

    def _note_missing(self, char: str) -> None:
        if char not in self._missing:
            self._missing.add(char)
            print(f"[text] fontta olmayan karakter: {char!r} (U+{ord(char):04X})")


_font: BitmapFont | None = None


def font() -> BitmapFont:
    """Modul duzeyinde tek font ornegi."""
    global _font
    if _font is None:
        _font = BitmapFont()
    return _font


# --- Cizim ------------------------------------------------------------------
def clear_cache() -> None:
    """Ekran yeniden kurulunca cagriliyor (`src/art/caches.py`).

    Yazi yuzeyleri `convert_alpha()` gormus durumda; ekran bicimi
    degisince menuler ve HUD de yavaslamaya dahil oluyor.
    """
    font()._cache.clear()


def measure(value: str, tracking: int = TRACKING) -> tuple[int, int]:
    return font().measure(value, tracking)


def text_width(value: str, tracking: int = TRACKING) -> int:
    return measure(value, tracking)[0]


def draw(surface: pygame.Surface, value: str, x: int, y: int,
         color: palette.RGB | None = None, align: str = "left",
         shadow: bool = False, outline: bool = False,
         tracking: int = TRACKING, alpha: int = 255) -> pygame.Rect:
    """Metin cizer, kapladigi dikdortgeni doner.

    `align`: left | center | right - x o hizanin referans noktasidir.
    `shadow`: 1 piksel saga-asagi koyu golge.
    `outline`: 4 yone kontur - parlak arka planlarda okunurluk icin sart.
    """
    color = color or palette.role("ui_text")
    glyphs = font().render(value, color, tracking)
    width, height = glyphs.get_size()
    if align == "center":
        x -= width // 2
    elif align == "right":
        x -= width

    if outline or shadow:
        dark = font().render(value, palette.outline(), tracking)
        if alpha < 255:
            dark = dark.copy()
            dark.set_alpha(alpha)
        offsets = ((-1, 0), (1, 0), (0, -1), (0, 1)) if outline else ((1, 1),)
        for dx, dy in offsets:
            surface.blit(dark, (x + dx, y + dy))

    if alpha < 255:
        glyphs = glyphs.copy()
        glyphs.set_alpha(alpha)
    surface.blit(glyphs, (x, y))
    return pygame.Rect(x, y, width, height)


def wrap(value: str, max_width: int, tracking: int = TRACKING) -> list[str]:
    """Metni verilen piksel genisligine gore satirlara boler."""
    step = GLYPH_WIDTH + tracking
    max_chars = max(1, (max_width + tracking) // step)
    lines: list[str] = []
    for paragraph in nfc(value).split("\n"):
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for word in paragraph.split(" "):
            candidate = f"{current} {word}".strip()
            if len(candidate) <= max_chars:
                current = candidate
                continue
            if current:
                lines.append(current)
            # Tek basina sigmayan uzun kelimeyi zorla kir.
            while len(word) > max_chars:
                lines.append(word[:max_chars])
                word = word[max_chars:]
            current = word
        if current:
            lines.append(current)
    return lines
