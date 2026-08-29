"""Iz Surme'nin gorsel dili - Yanki'nin aynadaki hali.

`echo_view.py`'nin kardesi. Ayni sozlesme: **kazanc ve bedel ayni
egriden** (`TrackingState.strength`) besleniyor, yani biri olmadan digeri
gorunemiyor.

    kazanc  gecmisin izleri beliriyor, gizli gecitler parliyor
    bedel   yasayan dusmanlar soluyor - simdiyi net goremiyorsun

## Renk: mor degil KEMIK

Yanki'nin ucu de mor (ses, vinyet, ortaya cikanlar) ve bu bilincli bir
karardi - "mor olan sey sana gosteriyor". Iz Surme ondan **acikca**
ayrilmali, yoksa iki karakter ayni yetenegin iki kopyasi gibi okunur.

Kemik/kul tonu (`bone`, `bone_pale` zinciri) secildi: soluk, sicak degil,
"ölü" cagristiran tek aile. Renk korlugu icin ayrica **parlaklik** olarak
da ayrisiyor (mor koyu, kemik acik) ve **sekil** olarak da - Yanki dolu
siluetler cizer, Iz Surme kucuk ayak izleri ve ic ice halkalar.

## Ekran KARARMIYOR

Yanki acilinca dunya kararir (bedel). Iz Surme'de karartma yok; bedel
dusmanlarin solmasi. Ikisi ayni gorseli kullansaydi "Ardo'nun Yankisi"
gibi okunurdu - oysa mesele tam olarak farkli bir duyu olmasi.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.glow import radial_glow
from src.systems.tracking import BLOOD, FOOT, SCORCH

# Ize gore renk. Hepsi ayni ailenin tonlari - "gecmis" tek bir dil
# konusmali, tur farki parlaklikla anlatiliyor.
TRACE_COLOUR = {
    FOOT: "bone",
    BLOOD: "blood_dark",
    SCORCH: "ember_dark",
}

# Iz kac piksel genisliginde cizilir.
FOOT_WIDTH = 3
FOOT_HEIGHT = 2


def draw_wash(surface: pygame.Surface, tracking) -> None:
    """Dunya **soluyor** - "gecmise bakiyorsun" sinyali.

    Yanki acilinca dunya KARARIR; Iz Surme acilinca AGARIR. Ikisi de
    ekranin tamamina dokunuyor ama zit yonde, o yuzden iki karakterin
    ekrani bir bakista ayrilabiliyor - ayni efektin iki tonu olsaydi
    "Ardo'nun Yankisi" gibi okunurdu.

    Bu bir bedel degil bir **isaret**: bedel dusmanlarin solmasi
    (`TrackingState.enemy_fade`). Isaret olmadan oyuncu yetenegin acik
    olup olmadigini bilmiyordu - ilk surumde yalnizca izler beliriyordu
    ve iz bulunmayan bir koridorda tusa basmak hicbir sey yapmiyor gibi
    gorunuyordu.
    """
    if not tracking.active:
        return
    veil = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    veil.fill((*palette.color("bone"), int(30 * tracking.strength)))
    surface.blit(veil, (0, 0))


def draw_traces(surface: pygame.Surface, offset: tuple[int, int],
                tracking, player, field) -> None:
    """Menzildeki izler. Yasa gore soluyor, uzaklikla siliniyor."""
    if not tracking.active or field is None:
        return
    reach = tracking.range
    if reach <= 0.0:
        return
    ox, oy = offset
    px, py = player.body.center_x, player.body.center_y
    now = field.frame

    for trace in field.near(px, py, reach):
        distance = math.hypot(trace.x - px, trace.y - py)
        # Iki ayri solma carpani: **uzaklik** (menzilin kenarinda kaybolur)
        # ve **yas** (eski iz soluk). Ikisi ayri bilgi tasiyor - tek bir
        # carpanda birlestirilseydi "yakin ve eski" ile "uzak ve taze"
        # ayni gorunurdu, oysa oyuncuya soyledikleri zit.
        near_fade = 1.0 - (distance / reach) ** 2
        age_fade = 1.0 - trace.age(now)
        alpha = int(200 * near_fade * age_fade * tracking.strength)
        if alpha <= 6:
            continue
        colour = palette.color(TRACE_COLOUR.get(trace.kind, "bone"))
        if trace.kind == FOOT:
            _draw_foot(surface, trace, ox, oy, colour, alpha)
        else:
            _draw_mark(surface, trace, ox, oy, colour, alpha)


def _draw_foot(surface: pygame.Surface, trace, ox: int, oy: int,
               colour, alpha: int) -> None:
    """Ayak izi - **yonu** var.

    `docs/derinlestirme.md` 2.4: *"ayak izleri KIMIN, NE ZAMAN gectigini
    gosterir"*. Yonu kaybedersek iz "burada biri vardi" der; yonuyle
    birlikte "buraya dogru gitti" der - ikincisi bir ipucu, birincisi
    sadece dekor.
    """
    x = int(trace.x) - ox
    y = int(trace.y) - oy - FOOT_HEIGHT
    mark = pygame.Surface((FOOT_WIDTH + 2, FOOT_HEIGHT + 2), pygame.SRCALPHA)
    # Topuk koyu, burun parlak: iki tonlu olunca uc piksellik bir leke
    # "ayak izi" gibi okunuyor, tek tonlu olunca "zemin cizigi" gibi.
    # Yon ayrica bir piksel one tasan burunla vurgulaniyor - `docs/
    # derinlestirme.md` 2.4 izin KIMIN, NE ZAMAN gectigini soylemesini
    # istiyor; yonu kaybedersek iz dekora dusuyor.
    heel = int(alpha * 0.55)
    mark.fill((*colour, heel), (0, 1, FOOT_WIDTH, FOOT_HEIGHT))
    mark.fill((*colour, alpha),
              (1 if trace.facing > 0 else 0, 0, FOOT_WIDTH, 1))
    surface.blit(mark, (x - FOOT_WIDTH // 2 - 1, y))
    tip = pygame.Surface((1, 1), pygame.SRCALPHA)
    tip.fill((*colour, alpha))
    surface.blit(tip, (x + (FOOT_WIDTH // 2 + 1) * (1 if trace.facing > 0
                                                    else -1), y))


def _draw_mark(surface: pygame.Surface, trace, ox: int, oy: int,
               colour, alpha: int) -> None:
    """Kan/patlama izi - ic ice iki halka, "burada bir sey oldu"."""
    x = int(trace.x) - ox
    y = int(trace.y) - oy
    ring = pygame.Surface((9, 9), pygame.SRCALPHA)
    pygame.draw.circle(ring, (*colour, alpha), (4, 4), 4, 1)
    pygame.draw.circle(ring, (*colour, alpha // 2), (4, 4), 2, 1)
    surface.blit(ring, (x - 4, y - 4))


def draw_cracks(surface: pygame.Surface, offset: tuple[int, int],
                tracking, player, walls=()) -> None:
    """Kirilabilir duvarlar - Yanki ile ayni bilgi, farkli gerekce.

    Rey duvarin **arkasini duyuyor**, Ardo duvardan birinin **gectigini
    goruyor**. Ayni sir, iki hikaye. Bolum verisine tek satir eklemeden
    iki karakter de gizli odalari bulabiliyor - `CLAUDE.md` 3 sirasi
    gelmemis icerik yazmayi yasakladigi icin esitligin YAPISAL olmasi
    sarttı.
    """
    if not tracking.active or tracking.range <= 0.0:
        return
    ox, oy = offset
    px, py = player.body.center_x, player.body.center_y
    reach = tracking.range
    for wall in walls:
        rect = wall.rect
        if math.hypot(rect.centerx - px, rect.centery - py) > reach:
            continue
        screen = rect.move(-ox, -oy)
        glow = radial_glow(max(6, screen.width // 2),
                           palette.color("bone"),
                           int(120 * tracking.strength))
        surface.blit(glow, (screen.centerx - glow.get_width() // 2,
                            screen.centery - glow.get_height() // 2),
                     special_flags=pygame.BLEND_RGBA_ADD)
        pygame.draw.rect(surface, palette.color("bone"), screen, 1)
