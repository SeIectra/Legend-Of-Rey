"""Atmosfer katmani - toz zerreleri, sis, isik huzmesi, damla.

`particles.py` **olaylar** icin (vurus, patlama, olum): bir demet fiskirir
ve soner. Burasi ise **surekli** olan sey: oda hic bir sey olmasa bile
yasiyor gorunmeli. Ikisi ayri dosyada cunku omur donguleri farkli - biri
tetiklenir, oteki hic durmaz.

Prototip kiyaslamasinda (23.08.2026) bulunan bosluk: kare hareketsizken
tamamen olu duruyordu. Sprite ve isik iyilesse bile bosluktaki hicligi
kapatmiyorlar; asil eksik havanin kendisiydi.

## Kamera ile birlikte kaymalar, ama tam olarak degil

Her zerre kendi `depth` degerine sahip (0..1). Kamera kayinca zerre
`depth` orani kadar kayiyor - yakin toz hizli, uzak toz yavas.
Bu parallax olmadan zerreler ekrana yapisik durur ve "cam uzerinde leke"
gibi okunur.

## Sinirli sayi

Ekranda en fazla `AMBIENCE_MAX` zerre (CLAUDE.md 4: parcacik ust siniri
200 - bu katman onun bir dilimini kullanir, dovus parcaciklarina yer
birakir). Ekrandan cikan zerre olmuyor, **karsi kenardan geri giriyor**:
sabit sayida nesne, sifir tahsis.

## Tam sayi cizim

Zerreler `int(round(...))` ile ciziliyor. Ondalik konumda cizilen bir
piksel titrer - projenin en cok tekrarlanan hatasi (CLAUDE.md 9).
"""
from __future__ import annotations

import math
import random

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH

AMBIENCE_MAX = 64

# Atmosfer tipleri: (parcacik rengi, sayi, dikey hiz araligi, yatay
# suruklenme, boyut agirligi, isik huzmesi var mi).
#
# "dust"  - kapali mekan tozu, agir agir asagi suzulur (B2, B3)
# "night" - kucuk kar/tohum benzeri gece zerreleri, yana savrulur (B1)
# "ember" - yukari suzulen kor (mesale odalari)
PRESETS: dict[str, dict] = {
    # `max_step`: zincirin kacinci basamagina kadar cikabilir. Ust sinir
    # olmadan toz zerreleri "white_flash"e kadar cikiyor ve magarada
    # YILDIZ gibi okunuyordu - hava degil gokyuzu.
    "dust":  {"chain": "bone_pale", "count": 40, "vy": (0.06, 0.22),
              "drift": 0.18, "shafts": True, "max_step": 1},
    "night": {"chain": "steel", "count": 30, "vy": (0.05, 0.14),
              "drift": 0.42, "shafts": False, "max_step": 2},
    "ember": {"chain": "torchlight", "count": 26, "vy": (-0.30, -0.10),
              "drift": 0.22, "shafts": True, "max_step": 2},
}


class _Mote:
    __slots__ = ("x", "y", "vy", "phase", "depth", "step", "size")

    def __init__(self, rng: random.Random, preset: dict) -> None:
        self.x = rng.uniform(0, INTERNAL_WIDTH)
        self.y = rng.uniform(0, INTERNAL_HEIGHT)
        low, high = preset["vy"]
        self.vy = rng.uniform(low, high)
        self.phase = rng.uniform(0.0, math.tau)
        # Derinlik hem parallax hem parlaklik belirliyor: uzak zerre hem
        # yavas kayar hem soluk kalir. Tek degerin iki isi yapmasi
        # tutarliligi bedavaya getiriyor.
        self.depth = rng.uniform(0.25, 1.0)
        top = preset.get("max_step", 2)
        self.step = max(0, top - (0 if self.depth > 0.8 else
                                  (1 if self.depth > 0.5 else 2)))
        self.size = 1 if self.depth < 0.8 else rng.choice((1, 1, 2))


class Ambience:
    """Bir odanin havasi. Sahne basina bir tane."""

    def __init__(self, preset: str = "dust", seed: int = 1337) -> None:
        self.preset_name = preset
        self.preset = PRESETS.get(preset, PRESETS["dust"])
        self._rng = random.Random(seed)
        count = min(AMBIENCE_MAX, self.preset["count"])
        self.motes = [_Mote(self._rng, self.preset) for _ in range(count)]
        self.frame = 0
        # Kameranin bir onceki konumu - parallax farkla hesaplaniyor.
        self._last_cam = (0.0, 0.0)

    # --- Dongu --------------------------------------------------------------
    def update(self, camera_offset: tuple[float, float] = (0.0, 0.0)) -> None:
        self.frame += 1
        cx, cy = camera_offset
        dx = cx - self._last_cam[0]
        dy = cy - self._last_cam[1]
        self._last_cam = (cx, cy)

        drift = self.preset["drift"]
        for mote in self.motes:
            mote.y += mote.vy * mote.depth
            mote.x += math.sin(self.frame * 0.013 + mote.phase) * drift
            # Kamera kaymasi: yakin zerre cok, uzak zerre az kayar.
            mote.x -= dx * mote.depth * 0.35
            mote.y -= dy * mote.depth * 0.35
            # Sarma: ekrandan cikan karsi kenardan girer. Yeni nesne
            # uretmiyoruz - sabit sayi, sifir tahsis.
            if mote.x < -2:
                mote.x += INTERNAL_WIDTH + 4
            elif mote.x > INTERNAL_WIDTH + 2:
                mote.x -= INTERNAL_WIDTH + 4
            if mote.y < -2:
                mote.y += INTERNAL_HEIGHT + 4
            elif mote.y > INTERNAL_HEIGHT + 2:
                mote.y -= INTERNAL_HEIGHT + 4

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        chain = self.preset["chain"]
        for mote in self.motes:
            # Yanip sonme: her zerre kendi fazinda nabiz atiyor. Sabit
            # parlaklikta zerreler "gurultu" gibi okunuyordu.
            pulse = 0.5 + 0.5 * math.sin(self.frame * 0.05 + mote.phase)
            if pulse < 0.22:
                continue
            step = mote.step if pulse > 0.55 else max(0, mote.step - 1)
            colour = palette.chain_color(chain, step)
            x = int(round(mote.x))
            y = int(round(mote.y))
            surface.fill(colour, (x, y, mote.size, mote.size))

    def draw_shafts(self, surface: pygame.Surface,
                    sources: tuple[tuple[float, float], ...]) -> None:
        """Isik huzmesi - bir kaynaktan asagi acilan soluk koni.

        `sources` ekran koordinatinda (x, y) listesi; genelde mesaleler.
        Huzme **toplamali** (`BLEND_RGB_ADD`) ciziliyor: karanligi
        aydinlatiyor, uzerine boya surmuyor.
        """
        if not self.preset["shafts"] or not sources:
            return
        tone = palette.chain_color(self.preset["chain"], 1)
        for sx, sy in sources:
            x = int(round(sx))
            y = int(round(sy))
            height = 46
            if x < -30 or x > INTERNAL_WIDTH + 30:
                continue
            shaft = pygame.Surface((30, height), pygame.SRCALPHA)
            for row in range(height):
                t = row / height
                half = int(2 + t * 11)
                # Ucta soner - keskin biten bir huzme "cizim" gibi okunur.
                alpha = int(26 * (1.0 - t) * (1.0 - t))
                if alpha <= 0:
                    continue
                shaft.fill((*tone, alpha), (15 - half, row, half * 2, 1))
            surface.blit(shaft, (x - 15, y), special_flags=pygame.BLEND_RGB_ADD)
