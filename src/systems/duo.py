"""Ikili kontrol - iki oynanabilir karakter, bir isaretci.

`docs/yapi.md` mekanik 10: *"**Ikili kontrol** | B17 | Karakterler arasi
gecis, biri kolu tutar biri gecer."*
`docs/gdd.md` 11: *"B17 | Bagimlilik | Biri olmadan gecilmiyor."*

## Mimari BELGEDE yaziyor

`docs/yapi.md` 119, uygulama notu:

    "Ikili kontrol (B17): iki `Player` nesnesi, aktif olani
     `active_player` isaretcisiyle degistir. Kamera hedefi degisir.
     Mevcut kodun buyuk kismi yeniden kullanilir."

Ve olculdu: dogru. `scene.player` disaridan yalnizca iki yerde
okunuyor; elli bir kullanimin hepsi `PlayScene`in kendi icinde. Yani
isaretciyi cevirmek **kamerayi, HUD'u, dusman hedeflemesini ve kayit
yazmayi birlikte** ceviriyor. Ikinci bir "aktif oyuncu" kavrami
tanimlamak gerekmedi.

## Pasif karakter yasamaya devam ediyor

Kontrol edilmeyen `Player` durdurulmuyor - `NEUTRAL_INPUT` ile
suruluyor (`src/core/input.py`). Yer cekimi, animasyon, dokunulmazlik
sayaci, ayak sesi: hepsi isliyor, yalnizca komut gelmiyor.

Bu bir ayrinti degil, **bulmacanin temeli**: plakanin ustunde
birakilan karakter orada durmaya devam ediyor ve kapiyi acik tutuyor.
Pasif olani dondursaydik plaka mantigi ("ustunde biri var mi")
calismazdi.

## Pasif karakter zarar GORMUYOR

Dusmanlar `scene.player`i hedefliyor, yani her zaman aktif olani.
Bu bir eksiklik degil bir **kural**: bakmadigin karakter, kontrol
edemedigin karakter. Onun kontrol disi olurken dovulmesi
`docs/ekonomi-uretim.md`nin B17 icin verdigi "bulmaca agirlikli"
tanimiyla da celisirdi.

## Kamera kesmiyor, KAYIYOR

Gecis aninda kamera hedefi degisiyor ve mevcut yumusatma onu
0,45-0,58 saniyede oturtuyor (olculdu). Sert kesme yerine kayma,
`CLAUDE.md` 9'un sinematik kuralinin ayni ruhu: gecis gorulmeli.
Ayrica kayma iki karakterin **ayni kulede** oldugunu gosteriyor -
kesme onlari iki ayri yer gibi gosterirdi.
"""
from __future__ import annotations

from src.config import SWITCH_COOLDOWN


class DuoState:
    """Iki `Player`, biri aktif. `switch()` isaretciyi ceviriyor."""

    __slots__ = ("players", "index", "cooldown", "switches")

    def __init__(self, first, second) -> None:
        self.players = (first, second)
        self.index = 0
        self.cooldown = 0
        self.switches = 0
        self.apply()

    # --- Sorgular -----------------------------------------------------------
    @property
    def active(self):
        return self.players[self.index]

    @property
    def other(self):
        return self.players[1 - self.index]

    @property
    def can_switch(self) -> bool:
        """Gecis su an mumkun mu.

        Tek sart bekleme. Havada ya da saldiri ortasinda gecisi
        yasaklamak dusunuldu ve **birakildi**: bu bir dovus bolumu
        degil, ve "su an degistiremezsin" diyen sessiz bir kural
        bulmacayi cozmeye calisan oyuncuyu bir hata yaptigina
        inandirirdi.
        """
        return self.cooldown <= 0

    # --- Akis ---------------------------------------------------------------
    def apply(self) -> None:
        """Kontrol bayraklarini isaretciye gore kurar.

        Tek yerde: iki oyuncunun bayragini ayri ayri yazmak, birinde
        `controlled = False` demeyi unutunca **iki karakterin ayni anda
        hareket etmesine** yol acardi.
        """
        for index, player in enumerate(self.players):
            player.controlled = index == self.index

    def update(self) -> None:
        if self.cooldown > 0:
            self.cooldown -= 1

    def switch(self) -> bool:
        """Isaretciyi cevirir. Gecis olduysa True."""
        if not self.can_switch:
            return False
        self.index = 1 - self.index
        self.cooldown = SWITCH_COOLDOWN
        self.switches += 1
        self.apply()
        return True

    def select(self, index: int) -> bool:
        """Belirli birine gecer - ara sahneler ve testler icin."""
        if index == self.index or not 0 <= index < len(self.players):
            return False
        return self.switch()
