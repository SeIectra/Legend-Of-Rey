"""Bolum verisi - tek ASCII haritadan zemin ve yerlesim.

Bir odayi iki ayri yerde tanimlamak (once tilemap, sonra "dusman su
koordinatta") kacinilmaz olarak kayar: biri duzenlenir, digeri unutulur ve
dusman duvarin icinde dogar. Burada **tek kaynak** var - haritaya bakan
yerlesimi de gormus olur.

    ##############
    ##..R.....s.##      R oyuncu   s Suruklenen
    ##############

Isaretler zeminden ayri tutulur: `terrain_rows` yalnizca `#`, `=` ve `.`
icerir, isaretlerin oldugu yer bosluga cevrilir. Yani bir dusmani
tasidiginda zemin degismez.

Bir odanin ne oldugunu **gorerek** anlamak, koordinat listesi okumaktan
hizli. Bolum sayisi 18'e cikinca bu fark buyuyor.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.config import TILE_SIZE

# Zemin karakterleri - tilemap bunlari kendi cozer.
TERRAIN = frozenset("#=.^B")

# Yerlesim isaretleri. Zeminde bosluk birakirlar.
MARKERS: dict[str, str] = {
    "R": "player",
    "C": "cemo",
    "s": "shambler",
    "t": "climber",      # tavana tutunur
    "b": "bloated",
    "d": "dummy",
    "K": "pickup_necklace",
    "W": "pickup_sword",
    "$": "chest",
    "M": "miniboss",
    "X": "exit",
    "!": "trigger",      # bolume ozel tetikleyici
    "g": "shadow_shambler",   # Golge Suruklenen - yalniz Bolum 3
    "N": "candle_keeper",     # Mum Bekcisi - yalniz Bolum 3
    "k": "shieldbearer",      # Kalkanli - Katman 2, B5'te tek ornekle taniticiyor
    "m": "spearman",          # Mizrakli - Katman 2, B10'da geliyor
    # Katman 2'nin son ikisi. B13'te birlikte geliyorlar cunku ikisi de
    # "once beni hallet" diye bagiran dusmanlar - ve B13'un zaman
    # kapisi tam olarak durmanin cezali oldugu oda.
    "a": "archer",            # Okcu
    "c": "commander",         # Komutan
    # --- Bolum 13: zaman kapilari (`src/systems/timegate.py`) -----------
    "L": "lever",             # Kol - kapiyi acar
    # Surgunun ASILI durdugu satir. Kapi buradan zemine kadar iniyor,
    # yani harita tek karakterle bir sutunu tarif ediyor.
    "T": "timegate",
    "F": "brazier",           # Mangal - B13 arenasinin isik ekonomisi
    "Z": "gaoler",            # Zindanci - BOSS 2
}


@dataclass(frozen=True)
class Placement:
    """Haritadan okunan tek bir yerlesim."""

    kind: str
    tile_x: int
    tile_y: int

    @property
    def x(self) -> float:
        """Tile'in yatay merkezi - piksel."""
        return self.tile_x * TILE_SIZE + TILE_SIZE * 0.5

    @property
    def feet_y(self) -> float:
        """Tile'in **altı** - varliklar buraya basar."""
        return (self.tile_y + 1) * TILE_SIZE


@dataclass
class Level:
    """Bir odanin zemini ve yerlesimi."""

    name: str
    terrain_rows: list[str] = field(default_factory=list)
    placements: list[Placement] = field(default_factory=list)

    def of(self, kind: str) -> list[Placement]:
        return [p for p in self.placements if p.kind == kind]

    def first(self, kind: str) -> Placement | None:
        found = self.of(kind)
        return found[0] if found else None


def join_rooms(*blocks: list[str]) -> list[str]:
    """Odalari **yan yana** birlestirir.

    Sekiz odalik bir bolum tek ASCII blogu olarak yazilsa 300+ sutun olur ve
    okunamaz. Her oda kendi kucuk blogu olarak yaziliyor, burada
    birlestiriliyor: harita hem gorulebiliyor hem uzun olabiliyor.

    Butun bloklarin **satir sayisi ayni** olmali; degilse hangi odanin
    kaydigini bulmak zor olur, o yuzden burada acikca hata veriyoruz.
    """
    if not blocks:
        return []
    height = len(blocks[0])
    for index, block in enumerate(blocks):
        if len(block) != height:
            raise ValueError(
                f"oda {index} {len(block)} satir, digerleri {height} - "
                "butun odalar ayni yukseklikte olmali")
    return ["".join(block[row] for block in blocks) for row in range(height)]


def parse(name: str, rows: list[str]) -> Level:
    """ASCII haritayi zemine ve yerlesime ayirir."""
    terrain: list[str] = []
    placements: list[Placement] = []

    for ty, row in enumerate(rows):
        clean: list[str] = []
        for tx, char in enumerate(row):
            kind = MARKERS.get(char)
            if kind is not None:
                placements.append(Placement(kind, tx, ty))
                clean.append(".")           # Isaretin oldugu yer bos
            elif char in TERRAIN:
                clean.append(char)
            else:
                raise ValueError(
                    f"{name}: bilinmeyen harita karakteri {char!r} "
                    f"({tx}, {ty}). Zemin: {''.join(sorted(TERRAIN))}  "
                    f"Isaret: {''.join(sorted(MARKERS))}")
        terrain.append("".join(clean))

    return Level(name=name, terrain_rows=terrain, placements=placements)
