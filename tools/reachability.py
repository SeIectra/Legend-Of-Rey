"""Bolum erisilebilirlik dogrulayicisi - "su platforma zıplayabiliyor muyum?"

Prototipte bir bolumun **cikis kapisina ulasilamiyordu** ve bu ancak elle
oynayınca fark edildi. Dikkatli olmaya guvenmek bu hata sinifini
engellemiyor: bir odada 30 basilabilir nokta varsa hepsinin ulasilabilir
oldugunu gozle dogrulamak mumkun degil.

## Nasil calisir

1. **Basilabilir noktalar** bulunur: altinda kati ya da platform olan,
   ustunde oyuncu boyu kadar bosluk bulunan her tile.
2. Aralarina kenar cekilir - yuru, zipla, dus.
3. Dogum noktasindan **BFS** yapilir.
4. Ulasilamayan nokta kalirsa rapor edilir.

## Zarf nereden geliyor

`MAX_JUMP_GAP_TILES` ve `MAX_JUMP_HEIGHT_TILES` - ikisi de
`tools/measure_jump.py` ile **olculmus** degerler, tahmin degil. O yuzden
`PLAYER_JUMP_SPEED` degisirse once measure_jump, sonra config, sonra bu
arac calistirilir.

## Muhafazakar olmak

Dogrulayici gercek fizigi taklit etmiyor; olculmus zarfin **icinde** kalan
kenarlar ceker. Yani "gecilebilir" dedigi bir yer gercekten gecilebilir,
ama cok dar bir gecisi "gecilemez" sayabilir. Bu yon bilincli: yanlis
alarm bir bolumu gereksiz kolaylastirir, kacirilan hata oyunu bitirilemez
yapar.

Kullanim:
    python tools/reachability.py                 # dahili odalari dogrular
    python tools/reachability.py --ayrinti       # ulasilamayan noktalari yaz
"""
from __future__ import annotations

import sys
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import (  # noqa: E402
    MAX_JUMP_GAP_TILES, MAX_JUMP_HEIGHT_TILES, TILE_SIZE,
)

# Oyuncu govdesi 10x22 piksel -> 22/16 = 1.375, yani iki tile bosluk gerek.
PLAYER_TILE_HEIGHT = 2

Spot = tuple[int, int]          # (tx, ty) - oyuncunun UZERINDE durdugu tile


@dataclass
class Report:
    name: str
    spots: set[Spot] = field(default_factory=set)
    reachable: set[Spot] = field(default_factory=set)
    spawn: Spot | None = None

    @property
    def unreachable(self) -> set[Spot]:
        return self.spots - self.reachable

    @property
    def ok(self) -> bool:
        return not self.unreachable and self.spawn in self.reachable

    def summary(self) -> str:
        if self.spawn not in self.reachable:
            return f"{self.name}: dogum noktasi basilabilir degil {self.spawn}"
        if self.unreachable:
            islands = sorted(self.unreachable)
            return (f"{self.name}: {len(islands)} nokta ulasilamiyor "
                    f"(orn. {islands[:4]})")
        return f"{self.name}: {len(self.spots)} noktanin hepsi ulasilabilir"


class Grid:
    """Sadece dogrulama icin gereken tilemap sorgulari."""

    def __init__(self, rows: list[str]) -> None:
        self.rows = rows
        self.height = len(rows)
        self.width = max(len(r) for r in rows) if rows else 0

    def _char(self, tx: int, ty: int) -> str:
        if not (0 <= ty < self.height):
            return "."
        row = self.rows[ty]
        if not (0 <= tx < len(row)):
            return "#"          # Harita disi yanlar kati (tilemap ile ayni)
        return row[tx]

    def solid(self, tx: int, ty: int) -> bool:
        return self._char(tx, ty) == "#"

    def breakable(self, tx: int, ty: int) -> bool:
        """Kirilabilir duvar - Yanki ile bulunup kilicla yikilir.

        Erisilebilirlik acisindan **gecilebilir** sayiliyor: arkasina
        ulasilabiliyor, sadece bir adim gerekiyor. Kati saysaydik
        dogrulayici her gizli gecidi "ulasilamaz" diye raporlardi ve
        gercek hatalar bu gurultunun icinde kaybolurdu.

        Bir varsayim var: oyuncu oraya varana kadar kilici almis oluyor.
        Bolum tasariminda kilic her zaman ilk kirilabilir duvardan **once**
        durmali.
        """
        return self._char(tx, ty) == "B"

    def platform(self, tx: int, ty: int) -> bool:
        return self._char(tx, ty) == "="

    def blocking(self, tx: int, ty: int) -> bool:
        """Icinden gecilemeyen. Platformlar **altindan gecilebilir**."""
        return self.solid(tx, ty)

    def supports(self, tx: int, ty: int) -> bool:
        return self.solid(tx, ty) or self.platform(tx, ty)

    def clear_column(self, tx: int, ty: int, height: int) -> bool:
        """(tx, ty) ve uzerindeki `height` tile bos mu?"""
        return all(not self.blocking(tx, ty - i) for i in range(height))


def standing_spots(grid: Grid) -> set[Spot]:
    """Oyuncunun ustunde durabilecegi tile'lar."""
    spots: set[Spot] = set()
    for ty in range(grid.height):
        for tx in range(grid.width):
            if not grid.supports(tx, ty):
                continue
            # Oyuncunun kaplayacagi hucreler **harita icinde** olmali.
            # Yoksa dis duvarin ustu de "basilabilir" sayiliyor: harita
            # disi ty<0 bos donduruyor, tepe seridi bosta duruyormus gibi
            # gorunuyor ve her odada onlarca sahte uyari uretiyordu.
            if ty - PLAYER_TILE_HEIGHT < 0:
                continue
            # Ustunde oyuncu boyu kadar bosluk olmali.
            if grid.clear_column(tx, ty - 1, PLAYER_TILE_HEIGHT):
                spots.add((tx, ty))
    return spots


def _path_clear(grid: Grid, ax: int, ay: int, bx: int, by: int) -> bool:
    """Iki nokta arasinda kaba bir gecis kontrolu.

    Gercek yay degil, muhafazakar bir yaklasim: yolun her sutununda
    oyuncunun sigacagi bir bosluk var mi? Zipla-gec eden bir duvarin
    ustunden gectigini varsaymiyoruz.
    """
    top = min(ay, by) - MAX_JUMP_HEIGHT_TILES
    step = 1 if bx >= ax else -1
    for tx in range(ax, bx + step, step):
        # Sutunda, tavan ile hedef arasinda oyuncunun gecebilecegi bir
        # acikllik olmali.
        opening = False
        for ty in range(max(0, top), max(ay, by) + 1):
            if grid.clear_column(tx, ty, PLAYER_TILE_HEIGHT):
                opening = True
                break
        if not opening:
            return False
    return True


def build_edges(grid: Grid, spots: set[Spot]) -> dict[Spot, set[Spot]]:
    """Basilabilir noktalar arasi gecisler."""
    edges: dict[Spot, set[Spot]] = {s: set() for s in spots}
    gap = MAX_JUMP_GAP_TILES
    rise = MAX_JUMP_HEIGHT_TILES

    for spot in spots:
        sx, sy = spot
        for other in spots:
            if other == spot:
                continue
            ox, oy = other
            dx = abs(ox - sx)
            # N genisligindeki bosluk, kenardaki tile'lar arasinda N+1 yol.
            if dx > gap + 1:
                continue

            climb = sy - oy          # pozitif = yukari cikiyor
            if climb > rise:
                continue             # Cok yuksek - ziplama yetmez
            # Asagi inmek serbest: dusmek bedava. Yatay mesafe yine sinirli.
            if not _path_clear(grid, sx, sy, ox, oy):
                continue
            edges[spot].add(other)
    return edges


def validate(rows: list[str], spawn_tile: Spot, name: str = "oda") -> Report:
    """Bir odayi dogrular. `spawn_tile` oyuncunun **uzerinde durdugu** tile."""
    grid = Grid(rows)
    spots = standing_spots(grid)
    report = Report(name=name, spots=spots, spawn=spawn_tile)

    if spawn_tile not in spots:
        return report

    edges = build_edges(grid, spots)
    seen = {spawn_tile}
    queue = deque([spawn_tile])
    while queue:
        current = queue.popleft()
        for nxt in edges.get(current, ()):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    report.reachable = seen
    return report


# --- Dahili odalar ----------------------------------------------------------
def _known_rooms() -> list[tuple[str, list[str], Spot]]:
    """Dogrulanacak odalar. **Yeni bolum eklendiginde buraya eklenir.**"""
    from src.scenes.combat_room import ROOM_ROWS, SPAWN_TILE
    from src.world.rooms import chapter01

    rooms = [("dovus odasi", ROOM_ROWS,
              (SPAWN_TILE[0], SPAWN_TILE[1] + 1))]

    # Bolum odalari isaretleri de tasiyor; dogrulayici zemine bakar.
    spawn = chapter01.LEVEL.first("player")
    rooms.append(("bolum 1 - koy", chapter01.LEVEL.terrain_rows,
                  (spawn.tile_x, spawn.tile_y + 1)))

    from src.world.rooms import chapter02
    spawn2 = chapter02.LEVEL.first("player")
    rooms.append(("bolum 2 - ilk inis", chapter02.LEVEL.terrain_rows,
                  (spawn2.tile_x, spawn2.tile_y + 1)))
    return rooms


def main() -> int:
    verbose = "--ayrinti" in sys.argv
    print(f"ziplama zarfi: {MAX_JUMP_GAP_TILES} tile bosluk, "
          f"{MAX_JUMP_HEIGHT_TILES} tile yukseklik "
          f"({TILE_SIZE}px tile)\n")

    failures = 0
    for name, rows, spawn in _known_rooms():
        report = validate(rows, spawn, name)
        mark = "OK " if report.ok else "!! "
        print(mark + report.summary())
        if not report.ok:
            failures += 1
            if verbose:
                for spot in sorted(report.unreachable):
                    print(f"     ulasilamaz: {spot}")
    if failures:
        print(f"\n{failures} oda dogrulanamadi.")
        return 1
    print("\nTum odalar gecilebilir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
