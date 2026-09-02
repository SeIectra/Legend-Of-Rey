"""Kaldirma - diz cokmus yoldasi ayaga kaldirmak.

`docs/yapi.md` B16: *"Ardo geri doner, havali giris. Ama bu sefer **Rey
de onu kurtarir.** Karsilikli."*
`docs/gdd.md` 11: *"B16 | Esitlik | Sen onu kurtariyorsun."*

## Bolumun tezi bir tus degil, bir TERSINE CEVIRME

B6'dan beri iliski tek yonluydu ve bu koda yazilmisti: yoldas diz
coker (`Companion.downed`), bir sure sonra **kendi kendine** kalkar,
oyuncu hicbir sey yapmaz. B7'de Ardo Rey'i aralıktan cekti, B9'da onu
yukari firlatti, B12'de yolu isaretleyen oydu. Oyuncu hep tasinan
taraftı.

B16 bunu ceviriyor. Orada yoldas **yalnizca sen kaldirirsan** kalkiyor
(`Companion.self_recovers = False`) - yani iliskinin esitlendigi an bir
ara sahnede anlatilmiyor, oyuncunun parmaklarinda yasaniyor.

## Neden BASILI TUTMA

Tek basis olsaydi kaldirmak bir refleks olurdu; kaldirmanin bedeli
olmali. Basili tutmak dovusun ortasinda **kipirdamadan durmak** demek:
oyuncu once etrafi temizlemek ya da bir bosluk bulmak zorunda. Risk
alarak birini kaldiriyorsun - anin butun anlami bu.

Ilerleme sifirlaniyor:

  * uzaklasirsan   - yaninda durmak sart
  * vurulursan     - risk gercek olmali
  * tusu birakirsan

## Neden bir "sistem"

Tek bir sayac gibi gorunuyor ama uc sey durum tutuyor: ilerleme,
toplam kaldirma sayisi (ogretici ve bolum sonu odulu bunu okuyor) ve
son kaldirmanin karesi (parcacik/ses icin). B18 ayni ani geri
getiriyor; sahneye dagitilsaydi iki kopya olurdu.
"""
from __future__ import annotations

from src.config import RESCUE_HEALTH, RESCUE_HOLD_FRAMES, RESCUE_RANGE

# Kaldirma animasyonu/sesi bu kadar kare sonra biter.
LIFT_FRAMES = 16

# Ogretici ipucu bu kadar kaldirmadan sonra bir daha gosterilmiyor.
HINT_AFTER = 1


class RescueState:
    """Kaldirma ilerlemesi ve sayaci."""

    __slots__ = ("unlocked", "hold", "frames", "count")

    def __init__(self, unlocked: bool = False) -> None:
        # B16'da ogreniliyor; oncesinde tus hicbir sey yapmiyor.
        self.unlocked = unlocked
        self.hold = 0           # kac karedir tutuluyor
        self.frames = 0         # son kaldirmanin kalan karesi
        self.count = 0          # toplam kaldirma

    @property
    def active(self) -> bool:
        """Su an kaldirma animasyonu oynuyor mu."""
        return self.frames > 0

    @property
    def progress(self) -> float:
        """0..1 - HUD halkasi bunu ciziyor."""
        if RESCUE_HOLD_FRAMES <= 0:
            return 0.0
        return min(1.0, self.hold / RESCUE_HOLD_FRAMES)

    def reach(self, player, companion) -> bool:
        """Kaldirma su an mumkun mu?

        Uc sart, ucu de oynanistan:
          * yoldas **diz cokmus** - ayaktakini kaldirmak anlamsiz
          * **yakin** - yaninda durmak sart
          * **ikisi de yerde** - havada birini kaldiramazsin
        """
        if not self.unlocked or self.active:
            return False
        if player is None or companion is None:
            return False
        if not companion.downed or player.dead:
            return False
        if not player.body.grounded or not companion.body.grounded:
            return False
        return abs(player.body.center_x
                   - companion.body.center_x) <= RESCUE_RANGE

    def cancel(self) -> None:
        """Ilerleme sifirlanir - uzaklasma, vurulma, tusu birakma."""
        self.hold = 0

    def update(self, player, companion, holding: bool) -> bool:
        """Bir kare ilerlet. Kaldirma **bu karede** tamamlandiysa True.

        Donen deger bir kez True olur; sahne parcacigi, sesi ve kalp
        balonunu ona bagliyor.
        """
        if self.frames > 0:
            self.frames -= 1

        if not holding or not self.reach(player, companion):
            self.cancel()
            return False

        self.hold += 1
        if self.hold < RESCUE_HOLD_FRAMES:
            return False

        # Tamam - yoldas kalkiyor.
        self.hold = 0
        self.frames = LIFT_FRAMES
        self.count += 1
        companion.lift(RESCUE_HEALTH)
        return True
