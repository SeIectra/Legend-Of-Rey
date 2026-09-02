"""Susturma - Yanki'yi kalici olarak kapatmak.

`docs/yapi.md` B18: *"Rey sesi susturmayi **secer** - sessizlikte,
yardimsiz savasir (Ardo'nun butun oyun boyunca oynadigi sekilde)."*

## On sekiz bolumluk bir alisverisin sonu

Yanki hep bir pazarlikti: gorus ve hasar veriyor, karsiliginda savunma
aliyor (`ECHO_DAMAGE_TAKEN_MULTIPLIER`) ve kademe dustukce yalan
soyluyor. B14'te ogrenildi ki veren de alan da ayni sey - asagidaki
yaratik.

B18 pazarligi bitiriyor. Susturmak:

    kaybediyorsun    gorus, hasar carpani, soru sorma
    kazaniyorsun     Cagiran artik OLEBILIYOR

Ikincisi olmadan bolum bitmiyor (`Caller.undying`). Yani bu bir
"isterse yapar" degil, oyunun son kapisi - ve kapinin anahtari
oyuncunun butun oyun boyunca guvendigi seyi birakmasi.

## Neden BASILI TUTMA

Tek basis bir refleks olurdu. Iki saniye boyunca hicbir sey yapmadan
durmak - hem de bir boss dovusunun ortasinda - oyuncuya ne verdigini
dusunecek zaman birakiyor. B16'nin kaldirmasiyla ayni dil, ama iki
buçuk kati sure: orada birini kaldiriyordun, burada bir seyi
birakiyorsun.

## Geri alinamaz

`EchoState.restore()` bu bolumde cagrilmiyor ve `done` bir daha
False olmuyor. Geri alinabilseydi karar bir dugmeye donerdi ve
"sectim" hissi kaybolurdu.
"""
from __future__ import annotations

from src.config import ECHO_TIER_SILENT, SILENCE_HOLD_FRAMES

# Susturma animasyonu/sesi bu kadar kare surer.
HUSH_FRAMES = 40


class SilenceState:
    """Yanki'yi susturma karari. Basili tut, birak gitsin."""

    __slots__ = ("unlocked", "hold", "done", "frames")

    def __init__(self, unlocked: bool = False) -> None:
        # Boss ikinci faza gecince aciliyor: oncesinde oyuncu Cagiran'in
        # olmedigini daha gormemis olur ve karar anlamsiz gelirdi.
        self.unlocked = unlocked
        self.hold = 0
        self.done = False
        self.frames = 0

    @property
    def progress(self) -> float:
        """0..1 - HUD halkasi bunu ciziyor."""
        if SILENCE_HOLD_FRAMES <= 0:
            return 0.0
        return min(1.0, self.hold / SILENCE_HOLD_FRAMES)

    @property
    def active(self) -> bool:
        """Susturma ani oynuyor mu."""
        return self.frames > 0

    def cancel(self) -> None:
        """Ilerleme sifirlanir - tusu birakmak ya da vurulmak."""
        self.hold = 0

    def update(self, echo, holding: bool, hurt: bool = False) -> bool:
        """Bir kare ilerlet. Susturma **bu karede** olduysa True.

        `hurt` vurulduysa: ilerleme sifirlaniyor. Bedelsiz olsaydi
        oyuncu dayak yiyerek de susturabilirdi ve "bir bosluk bul"
        karari anlamsizlasirdi.
        """
        if self.frames > 0:
            self.frames -= 1
        if self.done or not self.unlocked or echo is None:
            return False
        if hurt or not holding:
            self.cancel()
            return False

        self.hold += 1
        if self.hold < SILENCE_HOLD_FRAMES:
            return False

        # Tamam. Kademe dibe iniyor ve **orada kaliyor.**
        self.hold = 0
        self.done = True
        self.frames = HUSH_FRAMES
        echo.tier = ECHO_TIER_SILENT
        return True
