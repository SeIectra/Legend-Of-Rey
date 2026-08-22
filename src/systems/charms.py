"""Tilsimlar - kosullu, pasif guclendirmeler.

Ilk tilsim Bolum 2'nin gizli sandiginda veriliyor ("Kanli Bileme"), o
yuzden sistem burada dogdu. Ekonomi belgesi tilsimlari oyunun ilerleyen
bolumlerinde ana ilerleme kaynagi yapiyor; altyapiyi bastan genis kurmak
sonradan her tilsim icin yeni bir kanca acmaktan ucuz.

## Kosullu olmalari tesadufi degil

"Hasar +%15" duz bir tilsim olsaydi karar vermezdin - takar, unuturdun.
"5+ combo'da hasar +%15" ise oynayis bicimini odullendiriyor: saldirgan
oynayana calisiyor, cekingen oynayana calismiyor. Tilsim boylece bir sayi
degil bir **tercih** oluyor.

## Carpani vurus **uretilirken** biniyor

Hasar hesaplandiktan sonra duzeltmek olum esigini kaydirir ve "iki vurusta
oluyordu, simdi uc" gibi bulmasi zor dengesizlikler yaratir. Tek nokta:
`Player._spawn_attack_hitbox`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from src.config import FENER_DARK_DAMAGE_BONUS, FENER_LIGHT_RADIUS_BONUS

# Tilsim kimlikleri. Kayit dosyasina **bu dizeler** yaziliyor, o yuzden
# degistirilemezler - eski kayitlar tilsimlarini kaybeder.
BLOODY_WHET = "bloody_whet"
FENER = "fener"                  # Bolum 3 mini-boss odulu

# "Kanli Bileme" bu combo sayisindan itibaren calisir.
WHET_COMBO = 5
WHET_BONUS = 0.15


@dataclass(frozen=True)
class Charm:
    """Tek bir tilsim.

    `label_key` ve `desc_key` dil anahtari tutar, hazir metin degil -
    kayit ve arayuz dilden bagimsiz kalsin.
    """

    key: str
    label_key: str
    desc_key: str
    # Oyuncunun **o andaki** durumuna bakar. Kosullu olmasinin karsiligi bu:
    # tilsim her karede yeniden karar veriyor.
    damage_scale: Callable[[object], float] = lambda player: 1.0
    # Fener'in isik yaricapi bonusu icin ayri kanal - hasarla ayni
    # carpan olsaydi "karanlikta hasar" ile "isik yaricapi" birbirine
    # karisirdi (iki farkli soruya iki farkli sayi).
    light_scale: Callable[[object], float] = lambda player: 1.0

    def active_for(self, player: object) -> bool:
        return self.damage_scale(player) != 1.0


def _bloody_whet(player: object) -> float:
    combo = getattr(player, "combo", None)
    count = getattr(combo, "count", 0)
    return 1.0 + WHET_BONUS if count >= WHET_COMBO else 1.0


def _fener_dark_damage(player: object) -> float:
    """Karanlikta hasar +%10. Isikta hicbir sey yapmaz."""
    light = getattr(getattr(player, "scene", None), "light", None)
    if light is None:
        return 1.0
    body = getattr(player, "body", None)
    if body is None:
        return 1.0
    if light.in_light(body.center_x, body.center_y):
        return 1.0
    return 1.0 + FENER_DARK_DAMAGE_BONUS


def _fener_light_radius(player: object) -> float:
    return 1.0 + FENER_LIGHT_RADIUS_BONUS


# Anahtarlar **acikca** yazili: f-string ile kurulan dil anahtarini
# tests/test_lang.py kaynak taramasinda goremiyor ve "olu anahtar" sayiyor.
CHARMS: dict[str, Charm] = {
    BLOODY_WHET: Charm(
        key=BLOODY_WHET,
        label_key="charm.bloody_whet",
        desc_key="charm.bloody_whet_desc",
        damage_scale=_bloody_whet,
    ),
    FENER: Charm(
        key=FENER,
        label_key="charm.fener",
        desc_key="charm.fener_desc",
        damage_scale=_fener_dark_damage,
        light_scale=_fener_light_radius,
    ),
}


def get(key: str) -> Charm | None:
    return CHARMS.get(key)


def label_key(key: str) -> str:
    charm = CHARMS.get(key)
    return charm.label_key if charm else "charm.unknown"


def desc_key(key: str) -> str:
    charm = CHARMS.get(key)
    return charm.desc_key if charm else "charm.unknown"


def damage_scale(keys: Iterable[str], player: object) -> float:
    """Takili tilsimlarin hasar carpanlarini birlestirir.

    Carpanlar **carpilarak** birlesiyor, toplanarak degil: iki %15'lik
    tilsim %30 degil %32 veriyor. Toplama secilseydi tilsim sayisi artinca
    hasar dogrusal patlar; carpma dogal bir azalan getiri sagliyor.
    """
    total = 1.0
    for key in keys:
        charm = CHARMS.get(key)
        if charm is not None:
            total *= charm.damage_scale(player)
    return total


def light_scale(keys: Iterable[str], player: object) -> float:
    """Takili tilsimlarin isik yaricapi carpanlarini birlestirir (Fener)."""
    total = 1.0
    for key in keys:
        charm = CHARMS.get(key)
        if charm is not None:
            total *= charm.light_scale(player)
    return total
