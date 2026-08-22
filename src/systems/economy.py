"""Altin harcama - Mum Bekcisi ticareti icin.

GOREVLER.md Gorev 4'un atladigi bir gorevdi (`src/systems/economy.py`
Bolum 2'de listelenmisti ama hic yazilmadi; altin akisi o zaman
`chapter02.py` icine elle gomulmustu). Mum Bekcisi B7/B12/B16'da tekrar
cikacagi icin (docs/bolum-03.md) burada gercek, kucuk bir modul olarak
yaziyoruz - dorduncu kullanimda tekrar kopyalanmasin.

Asiri muhendislik yok: tek ihtiyac "yeterli altin var mi, harcarsak ne
olur" sorusu. Bir magaza arayuzu, envanter sistemi falan degil.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TradeOffer:
    """Sabit fiyatli, tekil bir teklif (Mum Bekcisi'nin tabagindaki)."""

    key: str            # save.flags icinde tekil satin alma bayragi
    cost: int
    label_key: str       # dil anahtari


def can_afford(save_data, cost: int) -> bool:
    return save_data is not None and save_data.gold >= cost


def spend(save_data, cost: int) -> bool:
    """Altini dusur. Yetersizse hicbir sey yapmaz, `False` doner."""
    if not can_afford(save_data, cost):
        return False
    save_data.gold -= cost
    return True


def already_bought(save_data, offer: TradeOffer) -> bool:
    """Tekil satin alimlar icin (Sonmez Fitil gibi) - iki kez alinamaz."""
    return bool(save_data is not None and save_data.flags.get(offer.key))


def mark_bought(save_data, offer: TradeOffer) -> None:
    if save_data is not None:
        save_data.flags[offer.key] = True
