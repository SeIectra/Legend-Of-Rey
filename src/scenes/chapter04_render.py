"""Bolum 4'un cizimi - kamp, kelimesiz gunluk, yarim harita, kolye.

`chapter01_render.py` ile ayni desen: ilk parametre `scene`, metot degil
serbest fonksiyon. Sahne MANTIGI `chapter04.py`'de kaliyor; burasi
yalnizca o durumun nasil gorundugunu biliyor.

## Hicbiri sprite dosyasi degil

Kamp ogeleri (iskelet, sonmus ates, dagilmis esya) prosedurel ciziliyor -
`village_backdrop.py` evleri ve `cave_backdrop.py` mesaleleri nasil
ciziyorsa oyle. Bir kez kullanilacak dekor icin PNG uretmek hem asset
kaydini sisirir hem de paletten kacma riski acar (CLAUDE.md 6).

## Gunluk **kelimesiz**

`docs/yapi.md` B4: *"gunluk (resimli, kelimesiz)"*. Bu bir kisitlama
degil, bolumun anlatim bicimi: onceki maceraci ne yasadigini dort resimle
anlatiyor. Bu yuzden panelde tek bir metin **yok** - sayfa okunu bile
piktogram. Ikonlar `src/ui/balloon.py` deseninin buyutulmus hali: '#'
dolu, '.' bos, tek renkle damgalaniyor.

Sayfa cevirme icin de tus yok - panel yaklasinca acilir, sayfalar kendi
cevrilir, uzaklasinca kapanir. Kelimesiz bir gunluk "X ile cevir" yazamaz;
yazsaydik kendi kuralimizi bozardik.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.glow import radial_glow
from src.config import (
    INTERNAL_WIDTH, JOURNAL_PAGE_FRAMES, TILE_SIZE,
)
from src.ui import balloon
from src.ui.widgets import panel

# --- Piktogram sozlugu ------------------------------------------------------
# '#' dolu, '.' bos. Hepsi tek renkle damgalaniyor - anlam **siluetten**
# cikmali (CLAUDE.md 6, siluet testi). Renk yalnizca vurgu.
GLYPHS: dict[str, tuple[str, ...]] = {
    # Ayakta duran insan. Bas / omuz / govde / bacak - dort kademe.
    "figure": (
        ".###.",
        ".###.",
        ".###.",
        "#####",
        ".###.",
        ".###.",
        ".#.#.",
        ".#.#.",
        "##.##",
    ),
    # Curuyen. Kambur ve kollari uzun - Katman 1'in siluet imzasi.
    "creature": (
        "..###..",
        ".#####.",
        "..###..",
        ".#####.",
        "#######",
        ".#####.",
        ".#.#.#.",
        ".#...#.",
    ),
    "flame": (
        "..#..",
        "..#..",
        ".###.",
        ".###.",
        "#####",
        ".###.",
    ),
    "arrow_down": (
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "#####",
        ".###.",
        "..#..",
    ),
    # Ucu **sagda**. Ilk halinde ucgen solda kalmisti ve ok ekranda arti
    # isareti gibi okunuyordu - piktogramda yon anlamin yarisi. Ikinci
    # halde uc dogru yerdeydi ama fazla kucuktu, ekran goruntusunde hala
    # arti gibi duruyordu; ucgen buyutuldu.
    "arrow_right": (
        "....#....",
        "....##...",
        "....###..",
        "#########",
        "....###..",
        "....##...",
        "....#....",
    ),
    # Gecit - asagi inen yol.
    "gate": (
        ".#####.",
        "#######",
        "#.....#",
        "#.....#",
        "#.....#",
        "#.....#",
        "#.....#",
        "#..#..#",
        "#######",
    ),
    # Yarim harita: sag kenari yirtik. Odadaki buluntunun **ayni** sekli -
    # oyuncu gunlukte gordugu seyi sonra yerde bulunca baglantiyi kuruyor.
    "map_half": (
        "#######..",
        "#.....##.",
        "#.##...#.",
        "#....#..#",
        "#..##...#",
        "#.....##.",
        "#######..",
    ),
    "skull": (
        ".#####.",
        "#######",
        "#..#..#",
        "#..#..#",
        "#######",
        ".#####.",
        ".#.#.#.",
    ),
}

# --- Gunlugun dort sayfasi --------------------------------------------------
# (piktogram, x, y, renk). Koordinatlar sayfa tuvalinde (44x10 hucre).
# Anlati sirasi: indim -> ates tasidim, geldiler -> yolu cizdim -> donmedim.
PAGES: tuple[tuple[tuple[str, int, int, str], ...], ...] = (
    (("figure", 4, 1, "bone"),
     ("arrow_down", 16, 3, "stone"),
     ("gate", 31, 1, "stone")),
    (("figure", 3, 1, "bone"),
     ("flame", 13, 3, "ember"),
     ("creature", 24, 2, "blood_dark"),
     ("creature", 34, 2, "blood_dark")),
    (("figure", 3, 1, "bone"),
     ("map_half", 15, 2, "bone"),
     ("arrow_right", 32, 3, "stone")),
    # Son sayfa tek bir goruntu: kafatasi ve **sonmus** alev. Alevin rengi
    # otekilerden farkli (kul grisi) - "ates sondu" cumlesini renk
    # kuruyor, cizgi degil.
    (("skull", 12, 2, "bone"),
     ("flame", 26, 3, "stone_dark")),
)

PAGE_CELLS_W = 44
PAGE_CELLS_H = 10
PAGE_SCALE = 4
PANEL_WIDTH = PAGE_CELLS_W * PAGE_SCALE + 16
PANEL_HEIGHT = PAGE_CELLS_H * PAGE_SCALE + 22
PANEL_TOP = 54


def page_count() -> int:
    """Gunlukteki sayfa sayisi. Sahne sayfa cevirirken buna soruyor -
    sayfa listesi burada yasadigi icin sayisi da burada bilinmeli."""
    return len(PAGES)


def _stamp(surface: pygame.Surface, name: str, x: int, y: int,
           scale: int, colour: palette.RGB) -> None:
    """Bir piktogrami `scale` katinda damgalar. (x, y) sol ust, piksel."""
    pattern = GLYPHS.get(name)
    if pattern is None:
        return
    for row, line in enumerate(pattern):
        for col, cell in enumerate(line):
            if cell == "#":
                surface.fill(colour,
                             (x + col * scale, y + row * scale, scale, scale))


# --- Kamp -------------------------------------------------------------------
def draw_camp(scene, surface: pygame.Surface, offset) -> None:
    """Onceki maceracinin kampi. Carpisma yok - tamami dekor."""
    from src.world.rooms.chapter04 import (
        FIRE_TILE, GEAR_TILES, JOURNAL_TILE, SKELETON_TILE,
    )
    ox, oy = offset
    frame = scene.game.frame

    for tile_x, tile_y, kind in GEAR_TILES:
        x = tile_x * TILE_SIZE - ox
        base = (tile_y + 1) * TILE_SIZE - oy
        if x < -32 or x > INTERNAL_WIDTH + 32:
            continue                     # Gorunmeyeni cizme
        _draw_gear(surface, kind, x, base)

    _draw_fire(scene, surface, FIRE_TILE[0] * TILE_SIZE - ox,
               (FIRE_TILE[1] + 1) * TILE_SIZE - oy, frame)
    _draw_skeleton(surface, SKELETON_TILE[0] * TILE_SIZE - ox,
                   (SKELETON_TILE[1] + 1) * TILE_SIZE - oy)
    _draw_journal_book(scene, surface, JOURNAL_TILE[0] * TILE_SIZE - ox,
                       (JOURNAL_TILE[1] + 1) * TILE_SIZE - oy, frame)


# Oturan iskelet. '#' kemik, 'o' goz/agiz cukuru, '.' bos.
#
# Ilk hali `surface.fill` cagrilariyla ciziliyordu ve ekran goruntusunde
# **kucuk beyaz bir merdiven** gibi okunuyordu: kaburgalari donusumlu
# koyu/acik yapmak onlari serit haline getirmisti, kafatasi da govdeye
# gore cok kucuktu. Desen olarak yazmak siluetin tamamini bir bakista
# gorunur kiliyor - CLAUDE.md 6'nin siluet testi tam olarak bunu istiyor.
#
# **Yatan degil oturan**: yatan bir iskelet zeminde bir leke gibi okunuyor,
# oturan bir siluet "burada biri oturdu ve kalkmadi" diyor.
SKELETON: tuple[str, ...] = (
    "...#####......",
    "..#######.....",
    "..#oo#oo#.....",
    "..#oo#oo#.....",
    "..#######.....",
    "...#o#o#......",     # cene
    "....###.......",     # boyun
    "..#######.....",     # kopruck kemigi
    "..#.###.##....",     # kaburga + omuzdan sarkan kol
    "..#.###.#.#...",
    "..#.###.#..#..",
    "...#####...#..",
    "....###....##.",     # legen + yere degen el
    "...####.......",
    "...#..########",     # bacaklar one uzanmis
    "...####.....##",     # ayak
)


def _draw_skeleton(surface: pygame.Surface, x: int, base: int) -> None:
    """Oturan iskelet. Desen `SKELETON`, iki renk: kemik ve cukur."""
    bone = palette.color("bone")
    hollow = palette.color("stone_darkest")
    top = base - len(SKELETON)
    for row, line in enumerate(SKELETON):
        for col, cell in enumerate(line):
            if cell == "#":
                surface.fill(bone, (x + col, top + row, 1, 1))
            elif cell == "o":
                surface.fill(hollow, (x + col, top + row, 1, 1))
    # Altinda tek bir golge cizgisi - stil sozlesmesi her karakterin
    # altina bir elips istiyor; bu olcekte karsiligi bir cizgi.
    surface.fill(palette.color("stone_darkest"), (x + 2, base - 1, 12, 1))


def _draw_fire(scene, surface: pygame.Surface, x: int, base: int,
               frame: int) -> None:
    """Ates cukuru. Sonmusken kul, yakildiginda alev.

    Sonmus hal **isik vermiyor**: bir isik kaynagi gorunuyor ama ortaligi
    aydinlatmiyorsa oyuncu onu "sonmus" diye okur. Ates yakilinca ayni
    yere hale geliyor - degisimi oyuncu gozuyle gormeli, yazidan degil.
    """
    # Tas halka - bes tas, ortadaki ucu alcak. Isik **sol ustten**
    # (CLAUDE.md 6): her tasin ust satiri acik, govdesi orta ton.
    for dx, w, h in ((-8, 3, 3), (-4, 3, 2), (0, 3, 2), (4, 3, 2), (8, 3, 3)):
        surface.fill(palette.color("stone_dark"), (x + 8 + dx, base - h, w, h))
        surface.fill(palette.color("stone"), (x + 8 + dx, base - h, w, 1))

    # Yanmis odun - capraz iki kutuk.
    surface.fill(palette.color("earth_dark"), (x + 3, base - 4, 10, 2))
    surface.fill(palette.color("ink"), (x + 5, base - 6, 6, 2))

    if not scene.fire_lit:
        # Kul: soguk gri, hareketsiz. Hicbir hale yok.
        surface.fill(palette.color("stone_darkest"), (x + 5, base - 7, 6, 1))
        return

    flicker = (frame // 6) % 3
    surface.fill(palette.color("ember_dark"), (x + 4, base - 8, 8, 3))
    surface.fill(palette.color("ember"), (x + 5, base - 10 - flicker, 6, 4))
    surface.fill(palette.color("gold"), (x + 7, base - 9 - flicker, 2, 3))
    glow = radial_glow(34, palette.color("ember"),
                       peak=0.44 + 0.05 * math.sin(frame * 0.08))
    surface.blit(glow, (x + 8 - 34, base - 8 - 34),
                 special_flags=pygame.BLEND_RGB_ADD)


def _draw_gear(surface: pygame.Surface, kind: str, x: int, base: int) -> None:
    """Dagilmis esya. Dordu de kucuk - siluet degil **doku** isi goruyorlar."""
    if kind == "bedroll":
        surface.fill(palette.color("earth_dark"), (x, base - 4, 14, 4))
        surface.fill(palette.color("earth"), (x, base - 4, 14, 1))
        surface.fill(palette.color("ink"), (x + 4, base - 3, 1, 3))
    elif kind == "flask":
        # Kirik: govde duruyor, boynu yana devrilmis.
        surface.fill(palette.color("echo_dark"), (x + 1, base - 5, 4, 5))
        surface.fill(palette.color("echo"), (x + 1, base - 5, 4, 1))
        surface.fill(palette.color("echo_dark"), (x + 5, base - 1, 3, 1))
    elif kind == "pack":
        surface.fill(palette.color("earth_dark"), (x, base - 8, 9, 8))
        surface.fill(palette.color("earth"), (x, base - 8, 9, 2))
        surface.fill(palette.color("ink"), (x + 3, base - 6, 3, 4))  # kapak
    else:   # "sword" - zemine saplanmis, egilmis kilic
        surface.fill(palette.color("stone"), (x + 3, base - 13, 1, 12))
        surface.fill(palette.color("stone_light"), (x + 3, base - 13, 1, 3))
        surface.fill(palette.color("gold"), (x + 1, base - 5, 5, 1))
        surface.fill(palette.color("earth_dark"), (x + 3, base - 4, 1, 4))


def _draw_journal_book(scene, surface: pygame.Surface, x: int, base: int,
                       frame: int) -> None:
    """Yerdeki gunluk. Yaklasinca parliyor - okunabilir oldugu boyle belli."""
    surface.fill(palette.color("earth_dark"), (x, base - 5, 11, 5))
    surface.fill(palette.color("bone"), (x + 1, base - 4, 9, 3))
    surface.fill(palette.color("earth_dark"), (x + 5, base - 4, 1, 3))  # sirt
    if scene.journal_alpha > 0.02:
        glow = radial_glow(16, palette.color("gold"),
                           peak=0.18 * scene.journal_alpha
                           + 0.04 * math.sin(frame * 0.06))
        surface.blit(glow, (x + 5 - 16, base - 3 - 16),
                     special_flags=pygame.BLEND_RGB_ADD)


# --- Kelimesiz gunluk paneli ------------------------------------------------
def draw_journal_panel(scene, surface: pygame.Surface) -> None:
    """Dort resimli sayfa. **Tek kelime yok.**"""
    if scene.journal_alpha <= 0.02:
        return
    alpha = max(0.0, min(1.0, scene.journal_alpha))
    rect = pygame.Rect(INTERNAL_WIDTH // 2 - PANEL_WIDTH // 2, PANEL_TOP,
                       PANEL_WIDTH, PANEL_HEIGHT)

    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    panel(layer, pygame.Rect(0, 0, rect.width, rect.height))

    page = PAGES[scene.journal_page % len(PAGES)]
    origin_x = 8
    origin_y = 8
    for name, cx, cy, tone in page:
        _stamp(layer, name, origin_x + cx * PAGE_SCALE,
               origin_y + cy * PAGE_SCALE, PAGE_SCALE, palette.color(tone))

    _draw_page_dots(scene, layer, rect)

    layer.set_alpha(int(255 * alpha))
    surface.blit(layer, rect.topleft)


def _draw_page_dots(scene, layer: pygame.Surface, rect: pygame.Rect) -> None:
    """Sayfa gostergesi - nokta dizisi.

    Metin yerine nokta: hem kelimesizlik kurali bozulmuyor hem de oyuncu
    gunlugun bitip bitmedigini goruyor. Aktif nokta bir tik buyuk; renk
    korlugu icin fark **sadece renk degil boyut** (CLAUDE.md 10).
    """
    count = len(PAGES)
    current = scene.journal_page % count
    total_w = count * 7 - 3
    x = rect.width // 2 - total_w // 2
    y = rect.height - 9
    for i in range(count):
        if i == current:
            layer.fill(palette.role("ui_text_bright"), (x + i * 7, y - 1, 4, 4))
        else:
            layer.fill(palette.role("ui_text_dim"), (x + i * 7 + 1, y, 2, 2))
    # Ince bir ilerleme cizgisi: sayfanin ne zaman cevrilecegi.
    span = max(1, int(rect.width - 16))
    filled = int(span * (scene.journal_frames % JOURNAL_PAGE_FRAMES)
                 / JOURNAL_PAGE_FRAMES)
    layer.fill(palette.role("ui_border"), (8, rect.height - 4, filled, 1))


# --- Yarim harita -----------------------------------------------------------
def draw_half_map(scene, surface: pygame.Surface, offset) -> None:
    """Sahanlikta duran yarim harita. Alinmadan once suzulur ve parildar."""
    if scene.map_taken:
        return
    from src.world.rooms.chapter04 import HALF_MAP_TILE
    ox, oy = offset
    x = HALF_MAP_TILE[0] * TILE_SIZE - ox
    base = (HALF_MAP_TILE[1] + 1) * TILE_SIZE - oy
    bob = int(round(math.sin(scene.game.frame * 0.05) * 1.5))
    y = base - 6 + bob

    glow = radial_glow(14, palette.color("gold"), peak=0.28)
    surface.blit(glow, (x + 4 - 14, y + 3 - 14),
                 special_flags=pygame.BLEND_RGB_ADD)
    # Yirtik parsomen: sol kenar duz, sag kenar tirtikli. Gunlugun
    # ucuncu sayfasindaki `map_half` ile ayni siluet.
    surface.fill(palette.color("bone"), (x, y, 9, 7))
    surface.fill(palette.color("stone_dark"), (x, y, 9, 1))
    surface.fill(palette.color("earth_dark"), (x + 2, y + 2, 4, 1))
    surface.fill(palette.color("earth_dark"), (x + 4, y + 4, 3, 1))
    for i, cut in enumerate((0, 2, 1, 3, 1, 2, 0)):
        surface.fill(palette.color("abyss_dark"), (x + 9 - cut, y + i, cut, 1))


# --- Kolye ani --------------------------------------------------------------
def draw_necklace(scene, surface: pygame.Surface, offset) -> None:
    """Rey kolyeyi cevirir. Kelimesiz.

    `chapter01_render.draw_necklace` ile ayni gorsel dil - kolye Bolum
    1'de nasil ciziliyorsa oyle. Fark **cevirme**: zincirin genisligi bir
    sinus boyunca daralip aciliyor, yani nesne ekseninde donuyor. Bu
    olcekte gercek rotasyon bulanik piksel demek (DEVIR.md 6/23'un ayni
    dersi: iki yerde ayni matematik yazmak yerine ayni jesti tekrarla).
    """
    if scene.necklace_frames <= 0:
        return
    ox, oy = offset
    body = scene.player.body
    wx, wy = body.center_x, body.center_y - 5.0
    x = int(round(wx)) - ox
    y = int(round(wy)) - oy

    # An ilerledikce parlaklik yukselip sonda sabitleniyor.
    ratio = min(1.0, scene.necklace_frames / 90.0)
    spin = math.sin(scene.necklace_frames * 0.09)
    peak = 0.20 + 0.30 * ratio + 0.06 * math.sin(scene.game.frame * 0.07)

    glow = radial_glow(12, palette.color("gold"), peak=peak)
    surface.blit(glow, (x - 12, y - 12), special_flags=pygame.BLEND_RGB_ADD)
    span = max(1, int(round(1 + abs(spin) * 3)))
    surface.fill(palette.color("gold"), (x - span, y - 2, span * 2 + 1, 1))
    surface.fill(palette.color("gold"), (x, y - 1, 1, 2))
    surface.fill(palette.color("white_flash"), (x, y - 1, 1, 1))

    # Balon: kolye ikonu. Konusma degil **jest** - kutunun icinde metin yok.
    # `body.y` govdenin TEPESI (Body'de `top` diye bir ozellik yok, `bottom`
    # var) - balon oradan yukari dogru cizilir.
    head_top = int(body.y) - oy
    balloon.draw(surface, "necklace", x, head_top, frame=scene.game.frame,
                 colour=palette.color("gold"),
                 alpha=int(255 * min(1.0, ratio * 1.6)))
