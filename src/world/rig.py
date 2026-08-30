"""Ardo'nun duzenegi - Bolum 12'nin inis kafesi.

`docs/gdd.md` 9 mekanik havuzunun **11. maddesi** (Arda, 30.08.2026).
Soru soyle gelmisti: *"jetpack, helikopter, araba veya tank gibi
surulebilir bisey ekleyip bir bolumu de oyle oynatmak istiyorum ama
cok absurt mu kacar?"*

Dordu de reddedildi ve sebep "araç" degil **cag**: zindanda mesale,
zincir, kafes ve anahtar var; oraya bir tank koymak surpriz degil
tutarsizlik olurdu. Ama istegin kendisi dogruydu - oyun kendi
dongusunu zaten dort kez bilerek kiriyor (B4/B8/B12 nefes, B15
gizlilik, B17 ikili kontrol). Degisen sey yalnizca araç oldu.

## Neden bir NEFES bolumune araç

Ilk bakista ters: araç hizlandirir, nefes bolumu yavaslatir. Cozum
aracin **kime ait oldugunda**.

`docs/yapi.md` B12: *"Ardo'nun gectigi yoldan gidiyorsun. Kamp
kalintilari, onun cizdigi isaretler, senin icin birakilmis erzak."*
Duzenek de o birakilanlardan biri - kuyuya o kurdu, sen biniyorsun.
Yani araç bolumun temasini bozmuyor, **tasiyor**: onun yaptigi bir
seyin seni tasimasi, "yoklukta yakinlik"in en dogrudan hali.

## Tek kontrol: fren

Kafes kendi iniyor. Oyuncunun elinde tek sey var - yavaslatmak.
Duvarlarda Ardo'nun isaretleri var ve yalnizca yavasken okunuyor.

Ceza yok. Olum yok. Basarisizlik yok. Degisen tek sey **onun ne
kadarini gordugun**. Bir nefes bolumunun olcusu beceri degil
yakinlik olmali.

Gerilim tek bir kuraldan geliyor: **yukari cikilmiyor.** Gectigin
isaret bir daha gelmiyor. Sifir satir kod, ve oyunun butun cumlesi.

## Fizik motoru yok

`docs/yapi.md` "Pygame Uygulama Notlari" team-up firlatma icin
*"tek seferlik impulse + animasyon state, fizik motoru gerekmez"*
diyor. Ayni ilke: kafes bir hiz degeri, oyuncunun ayaklari her karede
ona yaziliyor. Hareketli platform carpismasi yazmaya gerek yok - ve
yazsaydik oyuncu kenardan kayip kuyuya dusebilirdi.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.config import (
    MARK_READ_RANGE, MARK_READ_SPEED, RIG_ACCEL, RIG_BRAKE_SPEED,
    RIG_FALL_SPEED, RIG_WIDTH_TILES, TILE_SIZE,
)


@dataclass
class Mark:
    """Ardo'nun duvara biraktigi tek bir sey.

    `side` -1 sol duvar, +1 sag duvar. Isaretlerin iki duvara
    dagilmasi kafes uzerinde saga sola yurumeyi bir **secim** yapiyor:
    hangi tarafa bakiyorsun. Tek duvarda olsalardi yurumenin bir
    anlami kalmazdi.
    """

    tile_y: int
    side: int
    # Iki ayri anahtar, ikisi de **duz dize**. Tek anahtar tutup
    # `key + "_ardo"` uretmek `tests/test_lang.py`nin goremedigi bir
    # sey olurdu - bu bolumde tam olarak o hata yapildi ve on iki
    # replik "olu" diye raporlandi.
    key: str
    ardo_key: str
    kind: str = "mark"          # mark | cache | camp | figure
    found: bool = False

    @property
    def y(self) -> float:
        return self.tile_y * TILE_SIZE + TILE_SIZE * 0.5


class Rig:
    """Karsi agirlikli inis kafesi.

    Konumu `y` (kafesin **ust yuzeyi** - oyuncu buraya basiyor).
    Yatayda sabit: kuyu dar, kafes ortada.
    """

    def __init__(self, center_x: float, top_y: float,
                 bottom_y: float) -> None:
        self.center_x = center_x
        self.y = top_y
        self.bottom_y = bottom_y
        self.speed = 0.0
        self.braking = False
        # Inise baslamadan once oyuncu kafese binmeli.
        self.running = False

    @property
    def width(self) -> float:
        return RIG_WIDTH_TILES * TILE_SIZE

    @property
    def left(self) -> float:
        return self.center_x - self.width * 0.5

    @property
    def right(self) -> float:
        return self.center_x + self.width * 0.5

    @property
    def landed(self) -> bool:
        return self.y >= self.bottom_y

    @property
    def slow(self) -> bool:
        """Isaret okunacak kadar yavas mi."""
        return self.speed <= MARK_READ_SPEED

    def start(self) -> None:
        self.running = True

    def update(self, braking: bool) -> None:
        """Bir kare. `braking` frenin basili olup olmadigi.

        Hiz **yumusak** degisiyor: ani duran bir kafes asansor degil
        tuzak gibi hissettiriyordu. Ivme iki yonde de ayni - fren
        birakilinca da hemen hizlanmiyor.
        """
        self.braking = braking
        if not self.running:
            self.speed = 0.0
            return
        target = RIG_BRAKE_SPEED if braking else RIG_FALL_SPEED
        if self.speed < target:
            self.speed = min(target, self.speed + RIG_ACCEL)
        else:
            self.speed = max(target, self.speed - RIG_ACCEL)

        self.y += self.speed
        if self.y >= self.bottom_y:
            # **Yukari cikilmiyor** ve dibe carpilmiyor: kafes
            # dayaniyor. Bir nefes bolumunun sonu bir carpma olmamali.
            self.y = self.bottom_y
            self.speed = 0.0
            self.running = False

    def carry(self, body) -> None:
        """Oyuncunun ayaklarini kafese yaziyor.

        Yatayda serbest ama kafesin **disina cikamiyor** - kuyuya
        dusmek bir nefes bolumunde anlamsiz bir olum olurdu, ve
        `docs/derinlestirme.md`nin oyuncu affi ilkesine de aykiri.
        """
        body.gravity_scale = 0.0
        body.vy = 0.0
        half = body.width * 0.5
        x = min(max(body.center_x, self.left + half), self.right - half)
        body.set_feet(x, self.y)

    def release(self, body) -> None:
        """Kafesten inildi - yercekimi geri geliyor."""
        body.gravity_scale = 1.0

    # --- Isaretler -----------------------------------------------------------
    def reads(self, mark: Mark, body) -> bool:
        """Bu isaret su an okunuyor mu.

        Uc kosul: kafes yavas, isaret hizada, ve oyuncu **dogru
        tarafta**. Ucuncusu olmasa yan yurumek bir jest olurdu, secim
        degil.
        """
        if mark.found or not self.slow:
            return False
        if abs(body.center_y - mark.y) > MARK_READ_RANGE:
            return False
        offset = body.center_x - self.center_x
        return (offset * mark.side) > 0
