"""Ikon balonu - diyalogsuz anlatimin tasiyicisi.

Oyunda **hicbir replik yok** (docs/gdd.md 2). Duygu ve niyet jest, statik
panel ve ikon balonuyla anlatiliyor. Balon bu isin en sik kullanilan
parcasi: B6'da Ardo'yla ilk karsilasmada soru isareti, B16'da kalp, B1'de
Cemo'nun kolyeyi uzatmasi.

Ikonlar font glifi degil, **kucuk piksel desenleri**. Sebep: bir soru
isareti balonunun icinde metin fontu kullanmak onu "arayuz" gibi gosterir;
elle cizilmis bir ikon "dunyanin icinde" durur. Ayrica kalp, kolye gibi
seylerin font karsiligi yok.

Balon **kaynagin ustunde** durur ve kucuk bir yay ile ona baglanir; kimin
konustugu boylece bakisla anlasilir.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette

# Ikon desenleri - 7x7, '#' dolu, '.' bos.
ICONS: dict[str, tuple[str, ...]] = {
    "question": (
        ".###...",
        "#...#..",
        "....#..",
        "...#...",
        "...#...",
        ".......",
        "...#...",
    ),
    "alert": (
        "...#...",
        "...#...",
        "...#...",
        "...#...",
        "...#...",
        ".......",
        "...#...",
    ),
    "heart": (
        ".##.##.",
        "#######",
        "#######",
        "#######",
        ".#####.",
        "..###..",
        "...#...",
    ),
    # Kolye: zincir ve tas. Bolum 1'in tasidigi nesne.
    "necklace": (
        "..###..",
        ".#...#.",
        "#.....#",
        "#.....#",
        ".#...#.",
        "..###..",
        "...#...",
    ),
    # --- Jestler (`src/ui/gesture.py`, Bolum 16) ------------------------
    # `docs/derinlestirme.md` 3.3: *"Bir anda uc ikon cikar (elini uzat /
    # basini salla / geri cekil). Secimin iliskiyi sekillendirir."*
    # Kelime yok, o yuzden ikonun kendisi okunabilir olmali - ucu de
    # farkli SILUET (parmakli el, dikey ok, yatay ok), yalnizca farkli
    # sekil degil (`CLAUDE.md` 10).
    "hand": (
        "#.#.#..",
        "#######",
        "#######",
        ".#####.",
        "..###..",
        "...#...",
        "...#...",
    ),
    # Cift asagi cevron - "asagi, asagi" yani basini sallamak. Ilk
    # surum kucuk bir kafa dairesi + asagi ok idi ve 7x7'de okunmayan
    # bir kumeye donusuyordu (render edilip bakildi). Bu haliyle hem
    # okunuyor hem de oteki iki ikondan farkli siluet: el organik,
    # geri cekilme YATAY bir ok, bu DIKEY bir hareket.
    "nod": (
        "#.....#",
        ".#...#.",
        "..#.#..",
        "...#...",
        "#.....#",
        ".#...#.",
        "..#.#..",
    ),
    "back": (
        "...#...",
        "..##...",
        ".###...",
        "#######",
        ".###...",
        "..##...",
        "...#...",
    ),
    "echo": (
        "...#...",
        "..#.#..",
        ".#...#.",
        "#..#..#",
        ".#...#.",
        "..#.#..",
        "...#...",
    ),
}

ICON_SIZE = 7
PADDING = 3
TAIL_HEIGHT = 3
FLOAT_PERIOD = 90          # Balon yavasca suzulur - "canli" durur


def draw(surface: pygame.Surface, icon: str, x: int, y: int,
         frame: int = 0, colour: palette.RGB | None = None,
         alpha: int = 255) -> None:
    """Balonu (x, y) noktasinin **ustune** cizer.

    (x, y) kaynagin tepesi; balon oranin biraz uzerinde durur ve yay ona
    dogru bakar.
    """
    pattern = ICONS.get(icon)
    if pattern is None:
        return

    colour = colour or palette.role("ui_text")
    width = ICON_SIZE + PADDING * 2
    height = ICON_SIZE + PADDING * 2

    # Yavas suzulme - sabit duran balon cikartma gibi gorunur.
    drift = int(round(math.sin(frame * math.tau / FLOAT_PERIOD)))
    top = y - height - TAIL_HEIGHT - 3 + drift
    left = x - width // 2

    body = pygame.Surface((width, height + TAIL_HEIGHT), pygame.SRCALPHA)
    body.fill((*palette.color("ink"), 235), (0, 0, width, height))
    pygame.draw.rect(body, palette.role("ui_border"),
                     pygame.Rect(0, 0, width, height), 1)
    # Yay: asagi daralan uc parca.
    for i in range(TAIL_HEIGHT):
        span = TAIL_HEIGHT - i
        body.fill((*palette.color("ink"), 235),
                  (width // 2 - span, height + i, span * 2, 1))

    for row, line in enumerate(pattern):
        for col, cell in enumerate(line):
            if cell == "#":
                body.set_at((PADDING + col, PADDING + row), colour)

    if alpha < 255:
        body.set_alpha(alpha)
    surface.blit(body, (left, top))


def height_of() -> int:
    """Balonun kapladigi toplam yukseklik - yerlesim hesabi icin."""
    return ICON_SIZE + PADDING * 2 + TAIL_HEIGHT + 3
