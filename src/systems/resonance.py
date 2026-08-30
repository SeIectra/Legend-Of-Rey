"""Yanki Rezonansi - sesin **fiziksel** oldugu mekanik.

`docs/yapi.md` mekanik havuzu 5: *"Sesle kristal kir, can cal, uzaktaki
kapiyi ac."* B8'de ogreniliyor, B9'un can bulmacasi bunun uzerine
biniyor.

## Neden `EchoState`'in icinde degil

Yanki bir **algi** araci: duvarin ardini gosteriyor, soru cevapliyor,
sonar atiyor. Rezonans bir **etki**: dunyadaki nesneyi kiriyor.

Ve daha onemlisi: `docs/yapi.md` B8 *"Ardo ona sesi silah olarak
kullanmayi **gosterir**"* diyor. Yani tekniği bilen Ardo. Ama Ardo'nun
Yanki'si yok (`docs/gdd.md` 3, kanon) - rezonans `EchoState`'e
gomulseydi ogreten karakter onu kullanamazdi.

O yuzden ayri ve **iki karaktere de ait**. Ayrilan sey yalnizca nasil
uretildigi:

    Rey    sesiyle - Yanki'nin kendi camgobegi
    Ardo   kiliciyla taşa vurarak - bir nota, mor degil turuncu

Sayilar ayni. `EchoState`/`TrackingState` ciftindeki ayni ilke: esitlik
yapisal, renk ve gerekce farkli.

## Halka, patlama degil

Darbe anlik bir alan taramasi degil, **genisleyen bir halka**. Fark
oynanista: uzaktaki bir kristal hemen degil, ses oraya varinca
kiriliyor. Bu bir saniyelik gecikme mekanigi "ses" gibi hissettiren tek
sey - anlik olsaydi gorunmez bir el olurdu.

Nesne halkanin **on kenari** uzerinden gecerken vuruluyor; halka
gectikten sonra bir daha vurmuyor (`_struck` kumesi). Yoksa tek darbe
kirk kare boyunca ayni kristali kirk kez kirardi.
"""
from __future__ import annotations

import math

from src.config import FPS

# Halkanin genisleme suresi (kare). 40 kare = ~0.66 sn: bir "ses gitti
# ve vardi" hissi olusturacak kadar uzun, oyunu bekletmeyecek kadar kisa.
PULSE_FRAMES = 40

# Azami yaricap (piksel). 96 = 6 tile. Odanin yarisi kadar: oyuncu nereye
# durdugunu **secmek** zorunda, her yerden her seye ulasamiyor.
PULSE_RANGE = 96.0

# Iki darbe arasi bekleme. Cooldown olmasaydi oyuncu tusa basili tutar,
# halka surekli olur ve konumlanma karari yok olurdu.
PULSE_COOLDOWN = 75

# Halkanin kalinligi (piksel). Nesne bu bant icindeyken vuruluyor -
# tek piksellik bir cember hizli genislerken nesneleri atlardi.
BAND = 10.0


class ResonanceState:
    """Genisleyen ses halkasi. Iki karakterde de ayni sayilarla."""

    __slots__ = ("cooldown", "frames", "x", "y", "_struck", "unlocked",
                 "pulses")

    def __init__(self, unlocked: bool = False) -> None:
        # B8'de ogreniliyor; oncesinde tus hicbir sey yapmiyor.
        self.unlocked = unlocked
        self.cooldown = 0
        self.frames = 0                 # kalan genisleme karesi
        self.x = 0.0
        self.y = 0.0
        self._struck: set[int] = set()
        self.pulses = 0                 # toplam - ogretici bunu sayiyor

    # --- Sorgular -----------------------------------------------------------
    @property
    def active(self) -> bool:
        return self.frames > 0

    @property
    def ready(self) -> bool:
        return self.unlocked and self.cooldown <= 0 and not self.active

    @property
    def progress(self) -> float:
        """0 -> 1 arasi genisleme orani."""
        if not self.active:
            return 0.0
        return 1.0 - self.frames / PULSE_FRAMES

    @property
    def radius(self) -> float:
        return PULSE_RANGE * self.progress

    # --- Denetim ------------------------------------------------------------
    def pulse(self, x: float, y: float) -> bool:
        """Darbeyi baslatir. Hazir degilse False."""
        if not self.ready:
            return False
        self.x, self.y = float(x), float(y)
        self.frames = PULSE_FRAMES
        self.cooldown = PULSE_COOLDOWN
        self._struck.clear()
        self.pulses += 1
        return True

    def update(self) -> None:
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.frames > 0:
            self.frames -= 1

    def reaches(self, target) -> bool:
        """Halkanin on kenari su an bu nesnenin uzerinde mi?

        Nesne bir kez vuruluyor: `id` ile isaretleniyor ve halka
        gectikten sonra bir daha secilmiyor.
        """
        if not self.active:
            return False
        key = id(target)
        if key in self._struck:
            return False
        rect = target.rect
        distance = math.hypot(rect.centerx - self.x, rect.centery - self.y)
        if abs(distance - self.radius) > BAND:
            return False
        self._struck.add(key)
        return True

    def restore(self) -> None:
        """Nefes bolumu / kontrol noktasi - darbe hemen hazir olsun."""
        self.cooldown = 0
        self.frames = 0
        self._struck.clear()


# Ogretici ipucu bu kadar darbeden sonra bir daha gosterilmiyor: oyuncu
# mekanigi kullandiysa ogrenmistir, tekrarlamak ogut olur.
HINT_AFTER_PULSES = 2
# Ipucunun ekranda kalma suresi.
HINT_FRAMES = int(3.0 * FPS)
