"""Bitmap yazi motoru.

Sanal cozunurluk 480x270. Bu olcekte sistem yazi tipleri bulanik ve karaktersiz
kalir, bu yuzden oyunun kendi 5x11 pixel fontu var. Tabloda olmayan bir karakter
gelirse (nadir Unicode, emoji) sessizce sistem yazi tipine dusuyoruz - metin
asla kaybolmuyor.

Hucre duzeni (11 satir):
    satir 0-1   ust aksanlar (breve, umlaut, nokta)
    satir 2-8   buyuk harf yuksekligi (7 satir); kucuk x-yuksekligi 4-8
    satir 9-10  alt uzantilar (g, j, p, q, y) ve sedilla (c, s)
"""
from __future__ import annotations

import unicodedata

import pygame

from lore.gfx.palette import UI_SHADOW, UI_TEXT



def nfc(text: str) -> str:
    """Metni NFC bicimine sabitler.

    Turkce harfler kaynak dosyaya ayristirilmis (NFD) yazilabiliyor:
    "C" + birlesik sedilla gibi. Tek bicime indirgemezsek tablo aramasi
    kacirir ve harfler sistem yazi tipine duser.
    """
    return unicodedata.normalize("NFC", text)


GLYPH_W = 5
GLYPH_H = 11
BASELINE = 9            # 8. satirdan sonra taban cizgisi
TRACKING = 1            # Harfler arasi bosluk
LINE_GAP = 2

# --- Glif tablosu -----------------------------------------------------------
# Her glif "/" ile ayrilmis 11 satir; "#" dolu, "." bos.
_G: dict[str, str] = {
    " ": "...../...../...../...../...../...../...../...../...../...../.....",
    # Buyuk harfler ---------------------------------------------------------
    "A": "...../...../.###./#...#/#...#/#####/#...#/#...#/#...#/...../.....",
    "B": "...../...../####./#...#/#...#/####./#...#/#...#/####./...../.....",
    "C": "...../...../.###./#...#/#..../#..../#..../#...#/.###./...../.....",
    "D": "...../...../####./#...#/#...#/#...#/#...#/#...#/####./...../.....",
    "E": "...../...../#####/#..../#..../####./#..../#..../#####/...../.....",
    "F": "...../...../#####/#..../#..../####./#..../#..../#..../...../.....",
    "G": "...../...../.###./#...#/#..../#.###/#...#/#...#/.###./...../.....",
    "H": "...../...../#...#/#...#/#...#/#####/#...#/#...#/#...#/...../.....",
    "I": "...../...../.###./..#../..#../..#../..#../..#../.###./...../.....",
    "J": "...../...../..###/...#./...#./...#./...#./#..#./.##../...../.....",
    "K": "...../...../#...#/#..#./#.#../##.../#.#../#..#./#...#/...../.....",
    "L": "...../...../#..../#..../#..../#..../#..../#..../#####/...../.....",
    "M": "...../...../#...#/##.##/#.#.#/#...#/#...#/#...#/#...#/...../.....",
    "N": "...../...../#...#/##..#/#.#.#/#..##/#...#/#...#/#...#/...../.....",
    "O": "...../...../.###./#...#/#...#/#...#/#...#/#...#/.###./...../.....",
    "P": "...../...../####./#...#/#...#/####./#..../#..../#..../...../.....",
    "Q": "...../...../.###./#...#/#...#/#...#/#.#.#/#..#./.##.#/...../.....",
    "R": "...../...../####./#...#/#...#/####./#.#../#..#./#...#/...../.....",
    "S": "...../...../.####/#..../#..../.###./....#/....#/####./...../.....",
    "T": "...../...../#####/..#../..#../..#../..#../..#../..#../...../.....",
    "U": "...../...../#...#/#...#/#...#/#...#/#...#/#...#/.###./...../.....",
    "V": "...../...../#...#/#...#/#...#/#...#/#...#/.#.#./..#../...../.....",
    "W": "...../...../#...#/#...#/#...#/#.#.#/#.#.#/##.##/#...#/...../.....",
    "X": "...../...../#...#/#...#/.#.#./..#../.#.#./#...#/#...#/...../.....",
    "Y": "...../...../#...#/#...#/.#.#./..#../..#../..#../..#../...../.....",
    "Z": "...../...../#####/....#/...#./..#../.#.../#..../#####/...../.....",
    # Turkce buyuk harfler --------------------------------------------------
    "Ç": "...../...../.###./#...#/#..../#..../#..../#...#/.###./..#../.##..",
    "Ğ": "#...#/.###./.###./#...#/#..../#.###/#...#/#...#/.###./...../.....",
    "İ": "...../..#../.###./..#../..#../..#../..#../..#../.###./...../.....",
    "Ö": "...../.#.#./.###./#...#/#...#/#...#/#...#/#...#/.###./...../.....",
    "Ş": "...../...../.####/#..../#..../.###./....#/....#/####./..#../.##..",
    "Ü": "...../.#.#./#...#/#...#/#...#/#...#/#...#/#...#/.###./...../.....",
    # Kucuk harfler ---------------------------------------------------------
    "a": "...../...../...../...../.###./....#/.####/#...#/.####/...../.....",
    "b": "...../...../#..../#..../####./#...#/#...#/#...#/####./...../.....",
    "c": "...../...../...../...../.###./#...#/#..../#...#/.###./...../.....",
    "d": "...../...../....#/....#/.####/#...#/#...#/#...#/.####/...../.....",
    "e": "...../...../...../...../.###./#...#/#####/#..../.###./...../.....",
    "f": "...../...../..##./.#.../####./.#.../.#.../.#.../.#.../...../.....",
    "g": "...../...../...../...../.####/#...#/#...#/.####/....#/#...#/.###.",
    "h": "...../...../#..../#..../####./#...#/#...#/#...#/#...#/...../.....",
    "i": "...../..#../...../...../.##../..#../..#../..#../.###./...../.....",
    "j": "...../...#./...../...../..##./...#./...#./...#./...#./#..#./.##..",
    "k": "...../...../#..../#..../#..#./#.#../##.../#.#../#..#./...../.....",
    "l": "...../...../.##../..#../..#../..#../..#../..#../.###./...../.....",
    "m": "...../...../...../...../##.#./#.#.#/#.#.#/#...#/#...#/...../.....",
    "n": "...../...../...../...../####./#...#/#...#/#...#/#...#/...../.....",
    "o": "...../...../...../...../.###./#...#/#...#/#...#/.###./...../.....",
    "p": "...../...../...../...../####./#...#/#...#/####./#..../#..../#....",
    "q": "...../...../...../...../.####/#...#/#...#/.####/....#/....#/....#",
    "r": "...../...../...../...../#.##./##.../#..../#..../#..../...../.....",
    "s": "...../...../...../...../.####/#..../.###./....#/####./...../.....",
    "t": "...../...../.#.../.#.../####./.#.../.#.../.#..#/..##./...../.....",
    "u": "...../...../...../...../#...#/#...#/#...#/#...#/.####/...../.....",
    "v": "...../...../...../...../#...#/#...#/#...#/.#.#./..#../...../.....",
    "w": "...../...../...../...../#...#/#...#/#.#.#/#.#.#/.#.#./...../.....",
    "x": "...../...../...../...../#...#/.#.#./..#../.#.#./#...#/...../.....",
    "y": "...../...../...../...../#...#/#...#/#...#/.####/....#/#...#/.###.",
    "z": "...../...../...../...../#####/...#./..#../.#.../#####/...../.....",
    # Turkce kucuk harfler --------------------------------------------------
    "ç": "...../...../...../...../.###./#...#/#..../#...#/.###./..#../.##..",
    "ğ": "...../...../#...#/.###./.####/#...#/#...#/.####/....#/#...#/.###.",
    "ı": "...../...../...../...../.##../..#../..#../..#../.###./...../.....",
    "ö": "...../...../.#.#./...../.###./#...#/#...#/#...#/.###./...../.....",
    "ş": "...../...../...../...../.####/#..../.###./....#/####./..#../.##..",
    "ü": "...../...../.#.#./...../#...#/#...#/#...#/#...#/.####/...../.....",
    # Rakamlar ---------------------------------------------------------------
    "0": "...../...../.###./#...#/#..##/#.#.#/##..#/#...#/.###./...../.....",
    "1": "...../...../..#../.##../..#../..#../..#../..#../.###./...../.....",
    "2": "...../...../.###./#...#/....#/...#./..#../.#.../#####/...../.....",
    "3": "...../...../#####/...#./..##./....#/....#/#...#/.###./...../.....",
    "4": "...../...../...#./..##./.#.#./#..#./#####/...#./...#./...../.....",
    "5": "...../...../#####/#..../####./....#/....#/#...#/.###./...../.....",
    "6": "...../...../..##./.#.../#..../####./#...#/#...#/.###./...../.....",
    "7": "...../...../#####/....#/...#./..#../.#.../.#.../.#.../...../.....",
    "8": "...../...../.###./#...#/#...#/.###./#...#/#...#/.###./...../.....",
    "9": "...../...../.###./#...#/#...#/.####/....#/...#./.##../...../.....",
    # Noktalama --------------------------------------------------------------
    ".": "...../...../...../...../...../...../...../.##../.##../...../.....",
    ",": "...../...../...../...../...../...../...../.##../.##../.#.../#....",
    "!": "...../...../..#../..#../..#../..#../..#../...../..#../...../.....",
    "?": "...../...../.###./#...#/....#/...#./..#../...../..#../...../.....",
    ":": "...../...../...../.##../.##../...../.##../.##../...../...../.....",
    ";": "...../...../...../.##../.##../...../.##../.##../.#.../#..../.....",
    "'": "...../...../..#../..#../...../...../...../...../...../...../.....",
    '"': "...../...../.#.#./.#.#./...../...../...../...../...../...../.....",
    "-": "...../...../...../...../...../.###./...../...../...../...../.....",
    "+": "...../...../...../..#../..#../#####/..#../..#../...../...../.....",
    "=": "...../...../...../...../#####/...../#####/...../...../...../.....",
    "*": "...../...../...../..#../#.#.#/.###./#.#.#/..#../...../...../.....",
    "/": "...../...../....#/....#/...#./..#../.#.../#..../#..../...../.....",
    "\\": "...../...../#..../#..../.#.../..#../...#./....#/....#/...../.....",
    "(": "...../...../...#./..#../.#.../.#.../.#.../..#../...#./...../.....",
    ")": "...../...../.#.../..#../...#./...#./...#./..#../.#.../...../.....",
    "[": "...../...../..###/..#../..#../..#../..#../..#../..###/...../.....",
    "]": "...../...../###../..#../..#../..#../..#../..#../###../...../.....",
    "<": "...../...../...#./..#../.#.../#..../.#.../..#../...#./...../.....",
    ">": "...../...../.#.../..#../...#./....#/...#./..#../.#.../...../.....",
    "%": "...../...../##..#/##.#./...#./..#../.#.##/#..##/...../...../.....",
    "&": "...../...../.##../#..#./#.#../.#.../#.#.#/#..#./.##.#/...../.....",
    "#": "...../...../.#.#./.#.#./#####/.#.#./#####/.#.#./.#.#./...../.....",
    "@": "...../...../.###./#...#/#.###/#.#.#/#.###/#..../.###./...../.....",
    "_": "...../...../...../...../...../...../...../...../...../#####/.....",
    "|": "...../...../..#../..#../..#../..#../..#../..#../..#../...../.....",
    "^": "...../...../..#../.#.#./#...#/...../...../...../...../...../.....",
    "~": "...../...../...../...../.#..#/#.#.#/#..#./...../...../...../.....",
    "•": "...../...../...../...../.###./.###./.###./...../...../...../.....",
    "…": "...../...../...../...../...../...../...../#.#.#/#.#.#/...../.....",
}

# Tabloda karsiligi olmayan ama gorsel esdegeri bulunan karakterler.
# Akilli tirnaklar ve uzun tireler kopyala-yapistir ile metne siklikla sizar.
_ALIASES = {
    '‘': "'", '’': "'", '“': '"', '”': '"',
    '–': '-', '—': '-', '\xa0': ' ',
}


class BitmapFont:
    """Glif maskelerini bir kez cozup her renk icin onbellekler."""

    def __init__(self) -> None:
        self._masks: dict[str, list[str]] = {}
        for char, pattern in _G.items():
            rows = pattern.split("/")
            if len(rows) != GLYPH_H:
                raise ValueError(f"glif '{char}' {len(rows)} satir, {GLYPH_H} olmali")
            self._masks[nfc(char)] = rows
        self._cache: dict[tuple, pygame.Surface] = {}
        self._fallback: pygame.font.Font | None = None

    def _resolve(self, char: str) -> list[str] | None:
        char = _ALIASES.get(char, char)
        return self._masks.get(char)

    def has(self, char: str) -> bool:
        return self._resolve(char) is not None

    def measure(self, text: str, tracking: int = TRACKING) -> tuple[int, int]:
        if not text:
            return 0, GLYPH_H
        lines = nfc(text).split("\n")
        width = max(
            max(0, len(line) * (GLYPH_W + tracking) - tracking) for line in lines
        )
        height = len(lines) * (GLYPH_H + LINE_GAP) - LINE_GAP
        return width, height

    def render(self, text: str, color=UI_TEXT, tracking: int = TRACKING) -> pygame.Surface:
        key = (text, color, tracking)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        lines = nfc(text).split("\n")
        width, height = self.measure(text, tracking)
        surface = pygame.Surface((max(1, width), max(1, height)), pygame.SRCALPHA)

        step = GLYPH_W + tracking
        line_step = GLYPH_H + LINE_GAP
        for row_index, line in enumerate(lines):
            oy = row_index * line_step
            for col, char in enumerate(line):
                mask = self._resolve(char)
                ox = col * step
                if mask is None:
                    self._blit_fallback(surface, char, ox, oy, color)
                    continue
                for y, row in enumerate(mask):
                    for x, cell in enumerate(row):
                        if cell == "#":
                            surface.set_at((ox + x, oy + y), color)

        # Onbellek sinirsiz buyumesin: HUD'da her kare degisen sayaclar var.
        if len(self._cache) > 900:
            self._cache.clear()
        self._cache[key] = surface
        return surface

    def _blit_fallback(self, surface, char: str, ox: int, oy: int, color) -> None:
        """Tabloda olmayan karakter: sistem yazi tipiyle, kenar yumusatmasiz."""
        if self._fallback is None:
            self._fallback = pygame.font.SysFont(
                "consolas,dejavusansmono,couriernew", GLYPH_H
            )
        try:
            glyph = self._fallback.render(char, False, color)
        except pygame.error:
            return
        surface.blit(glyph, (ox, oy + 1))


# --- Modul duzeyinde tekil ---------------------------------------------------
_font: BitmapFont | None = None


def font() -> BitmapFont:
    global _font
    if _font is None:
        _font = BitmapFont()
    return _font


def measure(text: str, tracking: int = TRACKING) -> tuple[int, int]:
    return font().measure(text, tracking)


def text_width(text: str, tracking: int = TRACKING) -> int:
    return measure(text, tracking)[0]


def draw_text(surface: pygame.Surface, text: str, x: int, y: int,
              color=UI_TEXT, align: str = "left", shadow: bool = False,
              outline: bool = False, tracking: int = TRACKING,
              alpha: int = 255) -> pygame.Rect:
    """Metin cizer ve kapladigi dikdortgeni doner.

    `align`: left | center | right  (x o hizanin referans noktasidir)
    `shadow`: 1 piksel asagi-saga koyu golge - arka plan uzerinde okunurluk
    `outline`: 4 yone koyu cerceve - parlak arka planlarda sart
    """
    glyphs = font().render(text, color, tracking)
    w, h = glyphs.get_size()
    if align == "center":
        x -= w // 2
    elif align == "right":
        x -= w

    if outline:
        dark = font().render(text, UI_SHADOW, tracking)
        if alpha < 255:
            dark = dark.copy()
            dark.set_alpha(alpha)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(dark, (x + dx, y + dy))
    elif shadow:
        dark = font().render(text, UI_SHADOW, tracking)
        if alpha < 255:
            dark = dark.copy()
            dark.set_alpha(alpha)
        surface.blit(dark, (x + 1, y + 1))

    if alpha < 255:
        glyphs = glyphs.copy()
        glyphs.set_alpha(alpha)
    surface.blit(glyphs, (x, y))
    return pygame.Rect(x, y, w, h)


def wrap(text: str, max_width: int, tracking: int = TRACKING) -> list[str]:
    """Metni verilen piksel genisligine gore satirlara boler."""
    step = GLYPH_W + tracking
    max_chars = max(1, (max_width + tracking) // step)
    lines: list[str] = []
    for paragraph in nfc(text).split("\n"):
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for word in paragraph.split(" "):
            candidate = f"{current} {word}".strip()
            if len(candidate) <= max_chars:
                current = candidate
            else:
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
