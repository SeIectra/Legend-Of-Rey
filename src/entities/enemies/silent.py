"""Sessiz - Katman 3'un ilk uyesi.

`docs/gdd.md` 7: *"Sessiz - **Yanki onu gostermez**."*
Katman 3'un sorusu: *"yardimci sisteminin ihanetiyle yuzles."*

## Ilk ihanet: eksiklik

Katman 1 ve 2 dusmani **oyuncuya** saldiriyordu. Katman 3 oyuncunun
**araclarina** saldiriyor ve Sessiz bunun en sade bicimi: hicbir yeni
hamlesi yok, yalnizca Yanki onu gostermiyor.

Rey on bir bolumdur Yanki'yi acip odayi taradi ve gordugu her sey
oradaydi. Burada gormedigi bir sey var - ve bunu ancak vurulunca
ogreniyor.

## Gorunmezlik bir SIR degil bir EKSIKLIK

Sessiz gercekten gorunmez degil: ekranda duruyor, sprite'i ciziliyor.
Yalnizca **Yanki'nin siluetinde** yok. Yani oyuncu ona gozuyle
bakabilir; guvenmemesi gereken sey gozu degil arayuzu.

Bu ayrim onemli. Gercekten gorunmez bir dusman haksizlik olurdu;
"aracin gostermedigi" bir dusman bir ders.

## Karanlikta bekliyor

Yavas ve sabirli: pusuda duruyor, oyuncu yaklasinca kalkiyor.
`SILENT_AMBUSH_RANGE`'a kadar uyanmiyor - adi da oradan.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.config import (
    SILENT_ACTIVE_FRAMES, SILENT_AMBUSH_RANGE, SILENT_DAMAGE, SILENT_HEALTH,
    SILENT_POISE, SILENT_REACH, SILENT_RECOVER_FRAMES, SILENT_SPEED,
    SILENT_TELL_FRAMES,
)
from src.entities.enemies.shambler import Shambler


class Silent(Shambler):
    """Yanki'nin gostermedigi sey."""

    sprite_name = "silent"
    max_health = SILENT_HEALTH
    poise = SILENT_POISE
    move_speed = SILENT_SPEED
    contact_range = SILENT_REACH
    tell_frames = SILENT_TELL_FRAMES
    active_frames = SILENT_ACTIVE_FRAMES
    recover_frames = SILENT_RECOVER_FRAMES
    damage = SILENT_DAMAGE
    body_colour = "ink_soft"
    # NOT: burada bir `silhouette_scale = 1.0` alani vardi ve
    # `Enemy.silhouette_scale()` **metodunu** goelgeliyordu. Sonuc:
    # `enemy_render` onu cagirinca `TypeError`, yani dusman ekrana
    # girdigi an oyun cokuyordu - ve cokmeseydi bile tell sirasindaki
    # siluet sismesi olurdu, ki o `CLAUDE.md` 10'un renk korlugu
    # garantisi: *"tehlike asla sadece renkle anlatilmaz"*.

    # **Katman 3'un ilk ihaneti.** Gerekce modul basliginda.
    echo_visible = False

    def __init__(self, scene, x: float, y: float) -> None:
        super().__init__(scene, x, y)
        self.animator = Animator(self.sprite_name)
        self.sprite_foot_y = CHARACTERS[self.sprite_name].foot_y
        # Pusudan kalkti mi. Bir kez kalkinca bir daha yatmiyor:
        # "gizlenen dusman" bir bilmece, "surekli kaybolan dusman"
        # bir sinir bozuklugu.
        self.roused = False

    def _update_awareness(self) -> None:
        """Pusu: oyuncu **cok yaklasana** kadar uyanmiyor.

        `Enemy._update_awareness` normal gorus menzilini kullaniyor.
        Sessiz onu ezmek zorunda, yoksa odanin obur ucundan kosarak
        gelir ve "pusu" diye bir sey kalmaz.
        """
        if self.roused:
            super()._update_awareness()
            return
        # **Uyuyorsa pusu da kurmuyor.** `asleep` sahnenin koydugu bir
        # kural (Bolum 15'in uyuyan surusu) ve her dusman ona uymali;
        # Sessiz `_update_awareness`i ezdigi icin buraya elle yazmak
        # gerekti. Olmasaydi uyuyan bir Sessiz yaklasan oyuncuyu
        # yakalardi - yani gizlilik bolumunde sessiz yurumenin bir
        # anlami kalmazdi.
        if self.asleep:
            self._update_alert()
            return
        player = self.player
        if player is None:
            return
        if self.distance_to(player) <= SILENT_AMBUSH_RANGE:
            self.roused = True
            self.aware = True
            on_rouse = getattr(self.scene, "on_silent_rouse", None)
            if on_rouse:
                on_rouse(self)

    def draw_extra(self, surface: pygame.Surface, offset) -> None:
        """Pusudayken yalnizca **iki goz**.

        Govde zaten ciziliyor ama koyu (`ink_soft`) - karanlik bir
        odada goze carpan sey bu iki nokta oluyor. Yani oyuncunun onu
        bulmasi mumkun; yalnizca Yanki yardim etmiyor.
        """
        if self.roused:
            return
        ox, oy = offset
        x = int(self.body.center_x) - ox
        y = int(self.body.center_y) - oy - 6
        surface.fill(palette.color("violet_bright"), (x - 3, y, 2, 2))
        surface.fill(palette.color("violet_bright"), (x + 2, y, 2, 2))
