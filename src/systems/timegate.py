"""Zaman kapilari - `docs/gdd.md` mekanik 8, Bolum 13'te taniticiyor.

`docs/yapi.md`: *"Kolu cevir, X saniyede kos - **dovuserek degil
kacarak**."*

## Bu mekanigin asil isi bir ALISKANLIGI bozmak

On iki bolumdur oyuncu tek bir cumleyi ogrendi: *odayi temizle, sonra
gec.* Dusman gorunce durmak dogru refleks oldu, cunku hep dogruydu.

Zaman kapisi bunu tersine ceviriyor. Kol cevrilince surgu aciliyor ve
kapanmaya basliyor; yolda bir Okcu varsa onu oldurmeye harcanan sure
kapiyi kapatiyor. **Dogru cevap gecmek.** Odada birakilan dusman bir
basarisizlik degil, bir secim.

Bu yuzden Bolum 13'un odalarina Okcu ve Komutan konuyor: ikisi de
"once beni hallet" diye bagiran dusmanlar. Kendi dersleri oyuncuya
karsi kullaniliyor - `docs/gdd.md` 9'un *"yeni mekanik + eski mekanik
= yeni bulmaca"* kuralinin en dogrudan hali.

## Sayac bir cubuk DEGIL, kapinin kendisi

Kalan sure ekranin kosesinde bir cizgi olarak gosterilebilirdi. Onun
yerine surgu **fiziksel olarak iniyor**: zaman gectikce bosluk
alcaliyor, ve bosluk oyuncunun boyundan kisalinca gecis kapaniyor.

Kazanc iki tane. Birincisi oyuncunun gozu koridorda kaliyor, kosede
degil (CLAUDE.md 9: "diegetik tercih et"). Ikincisi aciliyet
**ogretilmeden** hissediliyor: alcalan bir kapiya kosmak, azalan bir
sayiya bakmaktan baska bir sey.

Bunun bir bedeli var ve bilerek odendi: surgu inerken son dilim
gecilemez oluyor, yani **kullanilabilir sure nominalin ~%60'i**.
`config.py`'deki degerler bu kayip hesaba katilarak secildi.

## Yumusak kilit YOK

Kol her zaman yeniden cevrilebilir (`LEVER_COOLDOWN` yalnizca cift
basmayi engelliyor). Kapanan surgunun altinda kalan oyuncu ezilmiyor,
itiliyor. Bir zaman bulmacasinin cezasi **zaman** olmali; olum ya da
kilitlenme degil. Bu ders projede pahaliya ogrenildi (bkz. `DEVIR.md`
"yumusak kilit").
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.config import (
    LEVER_COOLDOWN, TILE_SIZE, TIMEGATE_FRAMES, TIMEGATE_WARN_FRAMES,
)
from src.world.tilemap import EMPTY, SOLID

# Oyuncunun gecebilmesi icin gereken bosluk (tile). Govde ~26 piksel,
# yani iki tile. Bunun altinda surgu fiilen kapali.
PASSABLE_TILES = 2


@dataclass
class TimeGate:
    """Yukaridan inen bir surgu.

    `top_row` bosken surgunun asili durdugu satir; `floor_row` zeminin
    ilk kati satiri (surgu oraya kadar iniyor). Kapi kapaliyken
    `top_row`..`floor_row-1` arasi tamamen dolu.
    """

    tile_x: int
    top_row: int
    floor_row: int
    frames: int = TIMEGATE_FRAMES
    name: str = ""

    remaining: int = 0
    _filled: int = -1               # su an kac satir dolu (-1 = bilinmiyor)

    @property
    def height(self) -> int:
        """Surgunun toplam satir sayisi."""
        return max(1, self.floor_row - self.top_row)

    @property
    def is_open(self) -> bool:
        return self.remaining > 0

    @property
    def passable(self) -> bool:
        """Bosluk gercekten gecilebilir mi.

        `is_open` ile ayni sey DEGIL: surgu inerken kapi hala "acik"
        sayilir ama bosluk oyuncunun boyundan kisalmistir. Aradaki
        fark mekanigin gerilimi.
        """
        return self.gap_tiles >= PASSABLE_TILES

    @property
    def progress(self) -> float:
        """0 = yeni acildi, 1 = tamamen kapandi."""
        if self.frames <= 0:
            return 1.0
        return 1.0 - max(0, self.remaining) / self.frames

    @property
    def urgency(self) -> bool:
        """Son uyari dilimi - renk **ve** ses degisiyor."""
        return 0 < self.remaining <= TIMEGATE_WARN_FRAMES

    @property
    def filled_rows(self) -> int:
        """Yukaridan kac satir doldu."""
        if self.remaining <= 0:
            return self.height
        return int(self.height * self.progress)

    @property
    def gap_tiles(self) -> int:
        return self.height - self.filled_rows

    def open(self) -> bool:
        """Kol cevrildi. Zaten aciksa sureyi **bastan** baslatiyor."""
        was_open = self.is_open
        self.remaining = self.frames
        return not was_open

    def close(self) -> None:
        self.remaining = 0

    def update(self) -> None:
        if self.remaining > 0:
            self.remaining -= 1

    # --- Tilemap ------------------------------------------------------------
    def apply(self, tilemap) -> bool:
        """Surgunun su anki halini zemine yaziyor.

        Yalnizca **degistiginde** yaziyor: her karede 12 tile yazmak
        ucuz ama gereksiz, ve `_filled` ayrica "bu kare kapandi mi"
        sorusuna da cevap veriyor.
        """
        filled = self.filled_rows
        if filled == self._filled:
            return False
        self._filled = filled
        for index in range(self.height):
            row = self.top_row + index
            tilemap.set_tile(self.tile_x, row,
                             SOLID if index < filled else EMPTY)
        return True

    # --- Piksel yardimcilari -------------------------------------------------
    @property
    def center_x(self) -> float:
        return self.tile_x * TILE_SIZE + TILE_SIZE * 0.5

    @property
    def mouth_y(self) -> float:
        """Bosluğun ust kenari - piksel. Surgu indikce asagi kayiyor."""
        return (self.top_row + self.filled_rows) * TILE_SIZE

    def blocks(self, x: float) -> bool:
        """Bu yatay konum surgunun sutununda mi."""
        return abs(x - self.center_x) < TILE_SIZE


@dataclass
class Lever:
    """Bir ya da daha cok kapiyi acan kol.

    Kolun kendisi **durum tutmuyor** - yalnizca hangi kapilari actigini
    biliyor. Ayni ayrim `plate.py` ve aynalarda da var: girdi burada,
    sonuc baska yerde.

    `gates` bir dizi, tek bir ad degil: Bolum 13'un son bulmacasi tek
    kolla iki surgu aciyor ve ikisi **ayni sayaci** paylasiyor. Iki
    ayri kol koysaydik her biri kendi sayacini baslatirdi, yani ikinci
    kapi icin acele etmek gerekmezdi - bir zincir degil bir sira
    olurdu.
    """

    tile_x: int
    tile_y: int
    gates: tuple[str, ...] = ()
    cooldown: int = 0
    pulls: int = 0
    # Cevrilmis kol yerine oturana kadar donuyor - saf gorsel.
    spin: int = 0

    def update(self) -> None:
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.spin > 0:
            self.spin -= 1

    @property
    def ready(self) -> bool:
        return self.cooldown <= 0

    def pull(self) -> bool:
        if not self.ready:
            return False
        self.cooldown = LEVER_COOLDOWN
        self.spin = 12
        self.pulls += 1
        return True

    @property
    def center_x(self) -> float:
        return self.tile_x * TILE_SIZE + TILE_SIZE * 0.5

    @property
    def center_y(self) -> float:
        return self.tile_y * TILE_SIZE + TILE_SIZE * 0.5


class GateBank:
    """Bir odanin kapilari ve kollari.

    Sahne bunlari tek tek yonetebilirdi; bir arada tutmak `update`
    sirasini tek yerde sabitliyor - kol cevrilmesi, surgunun inmesi ve
    zemine yazilmasi hep ayni sirada olsun diye. Ilk surumde kol
    cevrildigi kare kapi henuz zemine yazilmamisti ve oyuncu bir kare
    boyunca kapali kapiya kosuyordu.
    """

    def __init__(self) -> None:
        self.gates: dict[str, TimeGate] = {}
        self.levers: list[Lever] = []

    def add_gate(self, gate: TimeGate) -> TimeGate:
        self.gates[gate.name] = gate
        return gate

    def add_lever(self, lever: Lever) -> Lever:
        self.levers.append(lever)
        return lever

    def gates_of(self, lever: Lever) -> list[TimeGate]:
        return [self.gates[name] for name in lever.gates
                if name in self.gates]

    def pull(self, lever: Lever) -> list[TimeGate]:
        """Kolu cevirip bagli kapilari aciyor.

        Kapilar **ayni karede** aciliyor, yani sayaclari senkron. Tek
        kolun iki kapiyi ayni sure icinde acmasi Oda 6'nin tamami.
        """
        if not lever.pull():
            return []
        opened = self.gates_of(lever)
        for gate in opened:
            gate.open()
        return opened

    def seal_all(self, tilemap) -> None:
        """Bolum kurulurken hepsi kapali baslar.

        ASCII haritada kapi sutunu **bos** duruyor. Sebep
        `tools/reachability.py`: BFS dogrulamasi oda geometrisini
        (ziplama zarfi, erisilebilirlik) olcmeli, bulmacanin o anki
        durumunu degil. Kapali kapiyi haritaya yazsaydik arac her
        bolumde yanlis alarm verirdi.
        """
        for gate in self.gates.values():
            gate.close()
            gate._filled = -1
            gate.apply(tilemap)

    def update(self, tilemap) -> list[TimeGate]:
        """Bir kare ilerlet. Bu karede **kapanan** kapilari dondurur."""
        for lever in self.levers:
            lever.update()
        closed: list[TimeGate] = []
        for gate in self.gates.values():
            was_passable = gate.passable
            gate.update()
            gate.apply(tilemap)
            if was_passable and not gate.passable:
                closed.append(gate)
        return closed

    def lever_near(self, x: float, y: float, reach: float) -> Lever | None:
        for lever in self.levers:
            if (abs(lever.center_x - x) <= reach
                    and abs(lever.center_y - y) <= reach):
                return lever
        return None
