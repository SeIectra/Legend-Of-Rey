"""Saldiri hakki - kalabalik dovusun okunabilirliginin temeli.

**Aynı anda en fazla iki dusman saldirabilir** (docs/dovus-sistemi.md 6,
BAGLAYICI). Kalani kusatma yorungesinde dolanir ve sirasini bekler.

Bu kural olmadan alti dusmanli bir oda "kaotik" olur: oyuncu neye tepki
verecegini secemez, olum haksiz hissettirir. Kuralla birlikte ayni oda
"yogun" hissettirir - izlenecek iki tehdit, gerisi baski. Batman: Arkham,
Assassin's Creed, Shadow of Mordor; hepsi bunu kullanir.

Uc detay bu sistemi calisir kilar, uc de bozar:

  * **Asgari tutma suresi.** Hak alan dusman hemen birakmaz; yoksa haklar
    kareler arasi el degistirir ve altisi da titresir.
  * **Azami tutma suresi.** Oyuncunun ulasamadigi bir dusman hakki sonsuza
    kadar tutarsa dovus durur. Sure dolunca birakir.
  * **Birakma bekleme suresi.** Birakan hemen geri istemezse sira gercekten
    doner.

Yonetici **niyeti** bilmez, yalnizca kimin hakki oldugunu bilir. Saldirip
saldirmamaya dusman kendi karar verir; burasi sadece "izin var mi?" sorusunu
cevaplar.
"""
from __future__ import annotations

from src.config import (
    MAX_SIMULTANEOUS_ATTACKERS, TOKEN_COOLDOWN_FRAMES, TOKEN_HOLD_MAX_FRAMES,
    TOKEN_HOLD_MIN_FRAMES,
)


class AttackTokenManager:
    """Saldiri haklarini dagitir. Sahne basina bir tane."""

    def __init__(self, limit: int = MAX_SIMULTANEOUS_ATTACKERS) -> None:
        self.limit = limit
        self._holders: dict[int, int] = {}       # id(dusman) -> tutulan kare
        self._cooldowns: dict[int, int] = {}     # id(dusman) -> kalan kare
        self._entities: dict[int, object] = {}   # id -> dusman (temizlik icin)

    # --- Sorgular -----------------------------------------------------------
    @property
    def active_count(self) -> int:
        return len(self._holders)

    def holds(self, enemy: object) -> bool:
        return id(enemy) in self._holders

    def available(self) -> int:
        return max(0, self.limit - len(self._holders))

    # --- Dagitim ------------------------------------------------------------
    def request(self, enemy: object) -> bool:
        """Saldiri izni ister. Verildiyse True.

        Zaten hakki olan tekrar isterse True doner - cagiran her karede
        sormaktan cekinmesin.
        """
        key = id(enemy)
        if key in self._holders:
            return True
        if self._cooldowns.get(key, 0) > 0:
            return False
        if len(self._holders) >= self.limit:
            return False
        self._holders[key] = 0
        self._entities[key] = enemy
        return True

    def release(self, enemy: object, cooldown: int = TOKEN_COOLDOWN_FRAMES) -> None:
        """Hakki birakir. Asgari sure dolmadiysa birakmaz.

        Erken birakma engeli bilincli: saldirisi iptal olan dusman hakki
        aninda birakip aninda geri alabilseydi sira hic donmezdi.
        """
        key = id(enemy)
        held = self._holders.get(key)
        if held is None:
            return
        if held < TOKEN_HOLD_MIN_FRAMES:
            return
        del self._holders[key]
        self._entities.pop(key, None)
        self._cooldowns[key] = cooldown

    def force_release(self, enemy: object,
                      cooldown: int = TOKEN_COOLDOWN_FRAMES) -> None:
        """Asgari sureyi dinlemeden birakir - olum ve sendeleme icin.

        Olen dusmanin hakki aninda geri donmeli, yoksa oyuncu bosluga
        saldirmis gibi hisseder.
        """
        key = id(enemy)
        if self._holders.pop(key, None) is not None:
            self._entities.pop(key, None)
            self._cooldowns[key] = cooldown

    # --- Dongu --------------------------------------------------------------
    def update(self) -> None:
        for key in list(self._cooldowns):
            self._cooldowns[key] -= 1
            if self._cooldowns[key] <= 0:
                del self._cooldowns[key]

        for key in list(self._holders):
            entity = self._entities.get(key)
            # Olen ya da sahneden cikan hakki birakir - kimse siraya kilit
            # vurmasin.
            if entity is None or getattr(entity, "dead", False) \
                    or getattr(entity, "remove", False):
                self.force_release(entity if entity is not None else key)
                self._holders.pop(key, None)
                self._entities.pop(key, None)
                continue

            self._holders[key] += 1
            if self._holders[key] > TOKEN_HOLD_MAX_FRAMES:
                # Ulasilamayan dusman dovusu kilitlemesin.
                del self._holders[key]
                self._entities.pop(key, None)
                self._cooldowns[key] = TOKEN_COOLDOWN_FRAMES

    def clear(self) -> None:
        self._holders.clear()
        self._cooldowns.clear()
        self._entities.clear()
