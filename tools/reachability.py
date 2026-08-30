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


def validate(rows: list[str], spawn_tile: Spot, name: str = "oda",
             ignore: set[Spot] | None = None) -> Report:
    """Bir odayi dogrular. `spawn_tile` oyuncunun **uzerinde durdugu** tile.

    `ignore`: BILEREK yurunerek erisilemeyen noktalar. Bolum 5'in ust
    kati boyle - oraya yalnizca su yukselince yuzerek cikiliyor ve BFS
    suyu bilmiyor. Bu kume olmasaydi arac surekli kirmizi yanar,
    zamanla goz ardi edilir ve gercek bir hatayi kacirirdik.
    """
    grid = Grid(rows)
    spots = standing_spots(grid)
    if ignore:
        spots = {spot for spot in spots if spot not in ignore}
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

    # HER girdi dortlu: (ad, satirlar, dogum, bilerek_erisilemez).
    # Karisik uzunluk dondugu bir ara surumde `tests/test_level.py`
    # kirildi - sozlesme tek bicimli tutuluyor.
    rooms = [("dovus odasi", ROOM_ROWS,
              (SPAWN_TILE[0], SPAWN_TILE[1] + 1), set())]

    # Bolum odalari isaretleri de tasiyor; dogrulayici zemine bakar.
    spawn = chapter01.LEVEL.first("player")
    rooms.append(("bolum 1 - koy", chapter01.LEVEL.terrain_rows,
                  (spawn.tile_x, spawn.tile_y + 1), set()))

    from src.world.rooms import chapter02
    spawn2 = chapter02.LEVEL.first("player")
    rooms.append(("bolum 2 - ilk inis", chapter02.LEVEL.terrain_rows,
                  (spawn2.tile_x, spawn2.tile_y + 1), set()))

    from src.world.rooms import chapter03
    spawn3 = chapter03.LEVEL.first("player")
    rooms.append(("bolum 3 - mesale mahzeni", chapter03.LEVEL.terrain_rows,
                  (spawn3.tile_x, spawn3.tile_y + 1), set()))

    from src.world.rooms import chapter04
    spawn4 = chapter04.LEVEL.first("player")
    rooms.append(("bolum 4 - kayit odasi", chapter04.LEVEL.terrain_rows,
                  (spawn4.tile_x, spawn4.tile_y + 1), set()))

    from src.world.rooms import chapter06
    spawn6 = chapter06.LEVEL.first("player")
    # Bolum 6'nin ilk odasi bilerek CIKMAZ: oyuncu kosede sikisiyor ve
    # duvar ancak yoldas gelince aciliyor (`chapter06.py` `_open_corner`).
    # BFS o kapiyi bilmiyor, o yuzden dogrulama duvar ACIK haliyle
    # yapiliyor - oynanista da oyle oluyor.
    rows6 = list(chapter06.LEVEL.terrain_rows)
    for row_index in chapter06.CORNER_WALL_ROWS:
        line = list(rows6[row_index])
        line[chapter06.CORNER_WALL_TILE] = "."
        rows6[row_index] = "".join(line)
    rooms.append(("bolum 6 - ardo", rows6,
                  (spawn6.tile_x, spawn6.tile_y + 1), set()))

    # Bolum 5: yalnizca KURU hali dogrulaniyor.
    #
    # Ust kata su yukselince YUZEREK cikiliyor ve BFS suyu bilmiyor.
    # Once su yuzeyini "platform" sayan ikinci bir gecis denendi ve
    # YANLIS cikti: yuzmek "yuzeyde yurumek" degil, su hacminde
    # yukselmek. BFS'i o modele zorlamak araci yaniltici yapardi.
    #
    # Su yolu bunun yerine `tests/test_chapter05.py`'de GERCEK FIZIKLE
    # dogrulaniyor: oyuncu suyu yukseltip yuzuyor ve ust kata gercekten
    # cikiyor mu diye bakiliyor. Her arac yalnizca dogrulayabildigi seyi
    # dogruluyor - zorlanmis bir BFS'ten daha guclu bir kanit.
    from src.world.rooms import chapter05
    spawn5 = chapter05.LEVEL.first("player")
    dry_rows = list(chapter05.LEVEL.terrain_rows)
    upper = chapter05.UPPER_FLOOR_ROW
    rooms.append(("bolum 5 - sular (kuru)", dry_rows,
                  (spawn5.tile_x, spawn5.tile_y + 1),
                  {(x, upper) for x in range(len(dry_rows[0]))}))

    # Bolum 7: iki yer BFS'in bilmedigi bicimde aciliyor.
    #
    #   * **Kapi** - cark cevrilince (`chapter07.py` `_turn_winch`).
    #     Bolum 6'nin kose duvariyla ayni durum: dogrulama kapi ACIK
    #     haliyle yapiliyor.
    #   * **Cukur** - uzerinden atlanmiyor, oyuncu yoldasin eliyle
    #     cikariliyor (`HandCinematic` + `_place_after_hand`). Iki sinir
    #     da hesaplanarak konuldu: sag duvar 4 tile
    #     (`MAX_JUMP_HEIGHT_TILES` = 3), yatay aciklik 6 tile
    #     (`MAX_JUMP_GAP_TILES` = 4).
    #
    # Cukuru `ignore`'a atmak yerine **dolduruyoruz**: ignore edilseydi
    # otesindeki iki oda da (Gecit, Cikis) dogrulama disinda kalirdi -
    # yani bolumun yarisi. Doldurunca yalnizca senaryolu gecis
    # varsayiliyor, geri kalan her sey gercekten sinaniyor.
    from src.world.rooms import chapter07
    spawn7 = chapter07.LEVEL.first("player")
    rows7 = [list(row) for row in chapter07.LEVEL.terrain_rows]
    for row_index in chapter07.DOOR_ROWS:
        for column in chapter07.DOOR_TILES:
            rows7[row_index][column] = "."
    for row_index in chapter07.CHASM_ROWS:
        for column in chapter07.CHASM_TILES:
            rows7[row_index][column] = "#"
    rooms.append(("bolum 7 - dar gecit", ["".join(r) for r in rows7],
                  (spawn7.tile_x, spawn7.tile_y + 1), set()))

    # Bolum 8: iki engel de **sesle** aciliyor (`Action.RESONATE`) ve
    # BFS ses bilmiyor - yalnizca yurumeyi biliyor. Ikisi de acik
    # halde dogrulaniyor, Bolum 6'nin kose duvari ve Bolum 7'nin
    # kapisiyla ayni gerekce.
    #
    # Mandal odasi bilerek **erisilemez** kaliyor: mekanigin butun
    # noktasi oraya yuruyememek. `ignore` ile disarida birakiliyor -
    # doldurmak yanlis olurdu, orasi bir gecis degil bir hedef.
    from src.world.rooms import chapter08
    spawn8 = chapter08.LEVEL.first("player")
    rows8 = [list(row) for row in chapter08.LEVEL.terrain_rows]
    for row_index in chapter08.LATCH_DOOR_ROWS:
        rows8[row_index][chapter08.LATCH_DOOR_TILE] = "."
    gate_x, gate_y = chapter08.GATE_CRYSTAL_TILE
    for row_index in range(gate_y, gate_y + chapter08.GATE_CRYSTAL_HEIGHT):
        rows8[row_index][gate_x] = "."
    rooms.append(("bolum 8 - ates basi", ["".join(r) for r in rows8],
                  (spawn8.tile_x, spawn8.tile_y + 1), set()))

    # Bolum 9: **dikey** kule ve katlar arasi 8 tile - ziplama 3.8.
    # Yani kule tasarim geregi tek basina tirmanilamiyor; cikis
    # `Action.INTERACT` ile yoldasin firlatmasi (`src/systems/boost.py`).
    #
    # BFS firlatmayi bilmiyor, o yuzden her gecidin ortasina **gecici
    # bir basamak** konuyor. Ayni yaklasim Bolum 7'nin cukurunda da
    # var: senaryolu/mekanikli gecisi varsay, geri kalan her seyi
    # gercekten sina. Boylece kulede erisilemeyen bir cep ya da
    # kilitlenme varsa yine yakalaniyor.
    from src.world.rooms import chapter09
    spawn9 = chapter09.LEVEL.first("player")
    rows9 = [list(row) for row in chapter09.LEVEL.terrain_rows]
    for row_index in chapter09.EXIT_DOOR_ROWS:
        rows9[row_index][chapter09.EXIT_DOOR_COLUMN] = "."
    for index, floor_row in enumerate(chapter09.FLOOR_ROWS[1:]):
        left, right = chapter09.GAPS[index]
        middle = (left + right) // 2
        # **Iki** basamak: katlar arasi 8 tile ve tirmanma siniri 3
        # (`MAX_JUMP_HEIGHT_TILES`), yani tek basamak yetmiyor - ilk
        # denemede 72 nokta ulasilamaz cikti. Basamaklar 3'er arayla.
        for drop in (5, 2):
            rows9[floor_row + drop][middle] = "#"
    rooms.append(("bolum 9 - can kulesi", ["".join(r) for r in rows9],
                  (spawn9.tile_x, spawn9.tile_y + 1), set()))

    # Bolum 10: hicbir gecici duzenleme yok. Iki yol da tasarim geregi
    # **yuruyerek** gecilebilir olmali - yalan bir kilit degil bir
    # secim. Dogrulama bunu sinamanin en dogrudan yolu: bir yol
    # gercekten kapaliysa oyuncu ceza degil cikmaz yasar.
    #
    # Tuzak sonrasi da onemli: zemin coktukten sonra dusen oyuncu
    # asagidan devam edebilmeli. Burasi tuzak KAPALI haliyle
    # dogrulaniyor cunku tuzak yalnizca zemin **kaldiriyor** - acilan
    # her sey zaten erisilebilir kaliyor.
    from src.world.rooms import chapter10
    spawn10 = chapter10.LEVEL.first("player")
    rooms.append(("bolum 10 - ayrilik", chapter10.LEVEL.terrain_rows,
                  (spawn10.tile_x, spawn10.tile_y + 1), set()))

    # Bolum 11: salonun cikis kapisi bulmaca cozulunce aciliyor
    # (`chapter11.py` `_solve`). BFS isini bilmiyor - kapi ACIK halde
    # dogrulaniyor, Bolum 7/8/9 ile ayni gerekce.
    from src.world.rooms import chapter11
    spawn11 = chapter11.LEVEL.first("player")
    rows11 = [list(row) for row in chapter11.LEVEL.terrain_rows]
    for row_index in chapter11.HALL_DOOR_ROWS:
        rows11[row_index][chapter11.HALL_DOOR_TILE] = "."
    rooms.append(("bolum 11 - ayna salonu", ["".join(r) for r in rows11],
                  (spawn11.tile_x, spawn11.tile_y + 1), set()))

    # Bolum 13: zaman kapilari haritada ZATEN acik duruyor (`T` yalnizca
    # surgunun asili satirini isaretliyor, zemin orada bos). Yani burada
    # elle bir duzenleme gerekmiyor - Bolum 11'in aksine. Gerekce
    # `src/world/rooms/chapter13.py` basliginda: dogrulama oda
    # geometrisini olcmeli, bulmacanin o anki durumunu degil.
    #
    # Arena muhru de ayni: `chapter13.py` calisirken kapatiyor, harita
    # acik tutuyor.
    #
    # **Cemo'nun ust ledge'i bilerek erisilemez.** Zemine 6 tile
    # yukarida, ziplama zarfi 3 - bolumun tamami "ulasamiyorsun"
    # uzerine kurulu (`docs/yapi.md` B13: *"ulasamadan tasinir"*).
    # Erisilebilir olsaydi ara sahne yalan soylerdi.
    from src.world.rooms import chapter13
    spawn13 = chapter13.LEVEL.first("player")
    cemo13 = chapter13.LEVEL.first("cemo")
    # Nokta = **zemin tile'i**, isaretin durdugu satir degil (dogum da
    # `tile_y + 1` veriliyor). Cemo `tile_y=6`'da duruyor, bastigi
    # ledge 7'de.
    ledge = {(x, cemo13.tile_y + 1) for x in range(13, 22)}
    rooms.append(("bolum 13 - cemo", chapter13.LEVEL.terrain_rows,
                  (spawn13.tile_x, spawn13.tile_y + 1), ledge))
    return rooms


def main() -> int:
    verbose = "--ayrinti" in sys.argv
    print(f"ziplama zarfi: {MAX_JUMP_GAP_TILES} tile bosluk, "
          f"{MAX_JUMP_HEIGHT_TILES} tile yukseklik "
          f"({TILE_SIZE}px tile)\n")

    failures = 0
    for name, rows, spawn, ignore in _known_rooms():
        report = validate(rows, spawn, name, ignore)
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
