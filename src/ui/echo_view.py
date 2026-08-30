"""Yanki'nin gorsel dili - yardim ve bedel ayni anda.

Gorevin bitis olcutu: *"Yanki'yi actigimda hem yardim aldigimi hem bir sey
kaybettigimi AYNI ANDA hissetmeliyim."* O yuzden acildigi anda ekranda iki
sey birden oluyor:

    **kazanc**  duvar ardindaki dusmanlar beliriyor, gizli gecitler parliyor
    **bedel**   ekran kenari kararıyor, renkler kayiyor, savunma dusuyor

Ikisi ayni egriden besleniyor (`EchoState.strength`), yani biri olmadan
digeri gorunemiyor. Ayri degiskenlere baglansaydi bir gun biri "vinyeti
biraz azaltalim" der ve mekanigin kalbi sessizce olurdu.

## Kademe HUD cubugu degil

Kademe **vinyetin yogunluguyla** okunuyor (CLAUDE.md 9: diegetik tercih
et). BERRAK'ta kenar hafif kararir ve uzagi gorursun; BULANIK'ta daha cok
kararir ama az gorursun - kotu takas gozle hissedilir. Sol ustte kucuk bir
gosterge yalnizca kademe **degistiginde** beliriyor (asamali aciga
cikarma).
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.glow import radial_glow
from src.config import (
    ECHO_TIER_CLEAR, ECHO_TIER_MURKY, ECHO_TIER_SILENT, INTERNAL_HEIGHT,
    INTERNAL_WIDTH, SONAR_MAX_RADIUS,
)
from src.systems.echo import Answer

# Kademeye gore vinyet rengi. BULANIK daha bogucu - takas gozle okunsun.
TIER_TINT = {
    ECHO_TIER_CLEAR: "violet_dark",
    ECHO_TIER_MURKY: "abyss_dark",
    ECHO_TIER_SILENT: "void",
}

# Kromatik kayma: kanallar birer piksel ayrilir. Bir piksel yeter -
# fazlasi "bozuk ekran" gibi okunur, "baska bir sey duyuyorum" gibi degil.
CHROMA_SHIFT = 1

_vignette_cache: dict[tuple, pygame.Surface] = {}


def clear_cache() -> None:
    """Ekran yeniden kurulunca cagriliyor (`src/art/caches.py`).

    Vinyet yuzeyleri de `convert`li: ekran bicimi degisince bayatliyorlar
    ve her karede tek tek donusturulmeye baslaniyorlar.
    """
    _vignette_cache.clear()


def draw_reveal(surface: pygame.Surface, offset: tuple[int, int],
                echo, player, enemies, walls=()) -> None:
    """Kazanc tarafi: duvar ardindaki dusmanlar ve gizli gecitler.

    Menzil disindakiler **hic** cizilmez - Yanki her seyi gostermiyor,
    yakini gosteriyor. BULANIK'ta menzil 96 piksel: bir odanin yarisi.
    """
    if not echo.active or echo.sight_range <= 0.0:
        return
    ox, oy = offset
    px, py = player.body.center_x, player.body.center_y
    reach = echo.sight_range
    # Yetenek agacinin gorus carpani (YANKI dali: ERIM, KAVRAYIS).
    # `EchoState`'e koymadik - o sinif oyuncuyu tanimiyor ve durumu saf
    # kalmali. Menzili KULLANAN taraf carpani biniyor.
    skills = getattr(player, "skills", None)
    if skills:
        from src.systems import skilltree
        reach *= skilltree.echo_sight_scale(skills, player)

    for enemy in enemies:
        # **Sessiz gorunmuyor.** Katman 3'un ilk sorusu: yardimci
        # sistem her seyi gostermiyor.
        if not getattr(enemy, "echo_visible", True):
            continue
        distance = math.hypot(enemy.body.center_x - px,
                              enemy.body.center_y - py)
        if distance > reach:
            continue
        # Uzaktakiler daha silik: menzilin kenarinda kayboluyor.
        fade = 1.0 - (distance / reach) ** 2
        _draw_silhouette(surface, enemy, ox, oy, fade, echo)

    for wall in walls:
        if math.hypot(wall.rect.centerx - px, wall.rect.centery - py) > reach:
            continue
        _draw_crack(surface, wall, ox, oy, echo)


def _draw_silhouette(surface, enemy, ox: int, oy: int, fade: float,
                     echo) -> None:
    """Dusmanin siluetı - duvar ardindan gorunur."""
    rect = enemy.body.rect.move(-ox, -oy)
    # **Ortaya cikanlar MOR** (24.08.2026). Eskiden camgobegiydi
    # ("echo"/"echo_bright") ve Yanki'nin SESI mordu - iki farkli renk
    # ailesi. Oyuncu mor bir seyin fisildadigini goruyordu, sonra
    # camgobegi bir gorus yetenegi kazaniyordu ve ikisi arasinda hicbir
    # gorsel bag yoktu (Arda'nin tespiti: "mor konusan seyin senin yankin
    # oldugunu anlamasi lazim").
    #
    # Artik uc kanal da ayni renkte: ses mor, aktifken vinyet mor
    # (TIER_TINT), ortaya cikanlar mor. "Mor olan sey sana gosteriyor."
    colour = palette.color("violet_bright" if echo.tier == ECHO_TIER_CLEAR
                           else "violet")
    ghost = pygame.Surface(rect.size, pygame.SRCALPHA)
    ghost.fill((*colour, int(150 * fade * echo.strength)))
    surface.blit(ghost, rect.topleft)
    pygame.draw.rect(surface, colour, rect, 1)


def _draw_crack(surface, wall, ox: int, oy: int, echo) -> None:
    """Kirilabilir duvarin catlagi - yalnizca Yanki ile gorunur."""
    rect = wall.rect.move(-ox, -oy)
    glow = radial_glow(max(6, rect.width // 2),
                       palette.color("violet_bright"),
                       peak=0.35 * echo.strength)
    surface.blit(glow, (rect.centerx - glow.get_width() // 2,
                        rect.centery - glow.get_height() // 2),
                 special_flags=pygame.BLEND_RGB_ADD)
    pygame.draw.rect(surface, palette.color("violet_bright"), rect, 1)


def draw_sonar(surface: pygame.Surface, offset: tuple[int, int], echo,
               player, enemies, walls=()) -> None:
    """Ses haritasi: genisleyen bir halka, gordugu her seyi bir an
    beyaz kontura bogar (docs/bolum-03.md Oda 2, "sonar gibi").

    `draw_reveal`'dan ayri bir mekanik - o surekli, karanlik-menzilli bir
    goruntu; bu tek seferlik bir darbe. Ikisi ayni karede de aktif olabilir
    (biri Yanki kademesinden, digeri sonar tetiklenmesinden).
    """
    if not echo.sonar_active:
        return
    ox, oy = offset
    progress = echo.sonar_progress
    radius = max(1, int(SONAR_MAX_RADIUS * progress))
    fade = 1.0 - progress
    px = int(player.body.center_x) - ox
    py = int(player.body.center_y) - oy

    ring = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(ring, (*palette.color("bone"), int(210 * fade)),
                       (radius + 2, radius + 2), radius, 2)
    surface.blit(ring, (px - radius - 2, py - radius - 2))

    reach = radius + 8.0
    colour = palette.color("bone")
    for enemy in enemies:
        if not getattr(enemy, "echo_visible", True):
            continue                    # sonar da gostermiyor
        distance = math.hypot(enemy.body.center_x - player.body.center_x,
                              enemy.body.center_y - player.body.center_y)
        if distance <= reach:
            pygame.draw.rect(surface, colour, enemy.body.rect.move(-ox, -oy), 1)
    for wall in walls:
        distance = math.hypot(wall.rect.centerx - player.body.center_x,
                              wall.rect.centery - player.body.center_y)
        if distance <= reach:
            pygame.draw.rect(surface, colour, wall.rect.move(-ox, -oy), 1)


def draw_dim(surface: pygame.Surface, echo) -> None:
    """Bedel: dunya kararir. **Ortaya cikanlardan ONCE cizilir.**

    Sira onemli. Once bedeli sonra kazanci cizmistim ve Yanki acilinca ekran
    kararacagina **aydinlaniyordu**: siluetler ve duvar parlamalari
    karartmanin ustune biniyordu. Dogrusu dunyanin geri cekilmesi, gizli
    seylerin o karanligi **delerek** cikmasi. Kontrast da boyle olusuyor -
    parlamalar parlak oldugu icin degil, geri kalan sondugu icin one cikiyor.

    Iki katman: butun ekrana hafif bir sonme + kenarlarda vinyet.
    """
    if not echo.active:
        return

    # Genel sonme - carpimla, alfayla degil. Yanki dunyayi **geri cekiyor**.
    fade = int(255 * (1.0 - 0.22 * echo.strength))
    surface.fill((fade, fade, fade), special_flags=pygame.BLEND_RGB_MULT)

    strength = echo.vignette
    if strength <= 0.0:
        return
    key = (round(strength, 2), echo.tier)
    veil = _vignette_cache.get(key)
    if veil is None:
        veil = _build_vignette(strength, echo.tier)
        if len(_vignette_cache) > 48:
            _vignette_cache.clear()
        _vignette_cache[key] = veil
    surface.blit(veil, (0, 0))


def draw_fringe(surface: pygame.Surface, echo) -> None:
    """Kromatik kayma - en son, her seyin uzerine."""
    if echo.active:
        _draw_chroma(surface, echo)


def _build_vignette(strength: float, tier: int) -> pygame.Surface:
    veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
    colour = palette.color(TIER_TINT.get(tier, "void"))
    # Kenardan merkeze dogru zayiflayan cerceveler - ucuz gradyan.
    steps = 34
    for i in range(steps):
        alpha = int(255 * strength * (1.0 - i / steps) ** 2 * 0.55)
        if alpha <= 0:
            continue
        pygame.draw.rect(veil, (*colour, alpha),
                         pygame.Rect(i, i, INTERNAL_WIDTH - i * 2,
                                     INTERNAL_HEIGHT - i * 2), 1)
    return veil.convert_alpha()


def _draw_chroma(surface: pygame.Surface, echo) -> None:
    """Kromatik kayma - tek kanal, bir piksel.

    **Ilk hali ekrani aydinlatiyordu.** Tum goruntuyu `set_alpha` ile
    solduruğ iki kez eklemeli harmanliyordum; `BLEND_RGB_ADD` alfayi agirlik
    olarak kullanmiyor, RGB'yi oldugu gibi ekliyor. Sonuc: Yanki acilinca
    ekran kararacagina parliyordu - bedel tam tersine donmustu.

    Dogrusu **gercek kromatik sapma**: yalnizca mavi kanal bir piksel
    kaydiriliyor ve eklemeden once carpimla kisiliyor. Kenarlarda mor bir
    hale birakiyor, goruntuyu aydinlatmiyor.

    Bu ders projede ucuncu kez ogrenildi (DEVIR.md 10). `tests/test_echo.py`
    artik parlakligi olcup bekciligini yapiyor.
    """
    if echo.strength < 0.4:
        return
    ghost = surface.copy()
    # Kirmizi ve yesili sifirla, maviyi kis: geriye ince bir mor fringe kalir.
    level = int(90 * echo.strength)
    ghost.fill((0, 0, level), special_flags=pygame.BLEND_RGB_MULT)
    surface.blit(ghost, (CHROMA_SHIFT, 0), special_flags=pygame.BLEND_RGB_ADD)


def draw_answer(surface: pygame.Surface, offset: tuple[int, int],
                echo, player) -> None:
    """Yanki'nin cevabi - kelimesiz.

    Dogru cevap net bir ok; eksik cevap titrek bir ok; **yalan da net bir
    ok** cizer. Yalanin yalan oldugu ekranda yazmaz - oyuncu kademesini
    bilir ve riski kendi hesaplar. Yazsaydi mekanik anlamsizlasirdi.
    """
    if echo.answer_frames <= 0 or echo.last_answer is Answer.NONE:
        return
    ox, oy = offset
    x = int(player.body.center_x) - ox
    y = int(player.body.top) - oy - 16

    if echo.last_answer is Answer.PARTIAL:
        # Eksik cevap titrer - guvenilmezligi hareketiyle belli eder.
        x += int(math.sin(echo.answer_frames * 0.4) * 2)

    # Cevap oku da Yanki'nin isi - ayni mor.
    colour = palette.color("violet_bright")
    direction = echo.answer_direction if hasattr(echo, "answer_direction") else 1
    for i in range(7):
        width = 7 - i
        surface.fill(colour, (x + direction * i - width // 2, y - i, width, 1))
