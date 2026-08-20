"""Prosedurel pixel art atolyesi.

Temel fikir: **renkle degil, palet indeksiyle cizeriz.**

Her piksel iki sayi tutar - hangi rampa (`ink`, `ember`, `stone`...) ve o
rampanin kacinci basamagi (0 en koyu, 4 en acik). Cizim bittikten sonra:

  * `shade()`  isik yonune bakan kenarlarin basamagini +1, ters kenarlarin -1
                yapar. Elle golge boyamak yok; tek satirda hacim olusur.
  * `outline()` siluetin cevresine `ink` cerceve cizer.
  * `resolve()` indeks ciftlerini gercek renklere cevirip Surface uretir.

Bunun bedava getirdikleri:
  * Ayni goblin sprite'i `moss` yerine `ash` rampasiyla cozulunce Act IV'un
    kul goblinine donusur - yeniden cizim yok.
  * Palet degisince tum oyun degisir, tek dosyadan.
  * Golgeleme her varlikta tutarli; el emegi tutarsizligi olusmaz.
"""
from __future__ import annotations

import math

import numpy as np
import pygame

from lore.gfx.palette import RAMPS

# Rampa adlarini sabit bir sirayla indeksliyoruz; uint8 tamponda saklamak icin.
RAMP_NAMES: tuple[str, ...] = tuple(RAMPS.keys())
RAMP_INDEX: dict[str, int] = {name: i for i, name in enumerate(RAMP_NAMES)}
EMPTY = 255                             # "burada piksel yok" isareti

# Cozunmus renk tablosu: [rampa][basamak] -> RGB. Bir kez kurulur.
_LUT = np.zeros((len(RAMP_NAMES), 5, 3), dtype=np.uint8)
for _i, _name in enumerate(RAMP_NAMES):
    for _s, _c in enumerate(RAMPS[_name]):
        _LUT[_i, _s] = _c

# Isik yonu: sol-ust. Tum oyun boyunca degismez, tutarlilik buradan gelir.
LIGHT_DX, LIGHT_DY = -1, -1


class Canvas:
    """Indeks tabanli cizim yuzeyi."""

    def __init__(self, width: int, height: int) -> None:
        self.w = width
        self.h = height
        self.ramp = np.full((height, width), EMPTY, dtype=np.uint8)
        self.step = np.zeros((height, width), dtype=np.uint8)
        self.glow = np.zeros((height, width), dtype=np.uint8)   # isik yayan pikseller

    # --- Yardimcilar --------------------------------------------------------
    def _ri(self, ramp: str) -> int:
        return RAMP_INDEX.get(ramp, RAMP_INDEX["stone"])

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.w and 0 <= y < self.h

    def px(self, x: int, y: int, ramp: str, step: int, glow: int = 0) -> None:
        if self.in_bounds(x, y):
            self.ramp[y, x] = self._ri(ramp)
            self.step[y, x] = max(0, min(4, step))
            if glow:
                self.glow[y, x] = glow

    def clear(self) -> None:
        self.ramp[:] = EMPTY
        self.step[:] = 0
        self.glow[:] = 0

    # --- Ilkel sekiller -----------------------------------------------------
    def fill_rect(self, x: int, y: int, w: int, h: int, ramp: str, step: int,
                  glow: int = 0) -> None:
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        self.ramp[y0:y1, x0:x1] = self._ri(ramp)
        self.step[y0:y1, x0:x1] = max(0, min(4, step))
        if glow:
            self.glow[y0:y1, x0:x1] = glow

    def rect(self, x: int, y: int, w: int, h: int, ramp: str, step: int) -> None:
        self.fill_rect(x, y, w, 1, ramp, step)
        self.fill_rect(x, y + h - 1, w, 1, ramp, step)
        self.fill_rect(x, y, 1, h, ramp, step)
        self.fill_rect(x + w - 1, y, 1, h, ramp, step)

    def disc(self, cx: float, cy: float, radius: float, ramp: str, step: int,
             glow: int = 0) -> None:
        r2 = radius * radius
        y0, y1 = int(cy - radius) - 1, int(cy + radius) + 2
        x0, x1 = int(cx - radius) - 1, int(cx + radius) + 2
        for y in range(max(0, y0), min(self.h, y1)):
            dy = y + 0.5 - cy
            for x in range(max(0, x0), min(self.w, x1)):
                dx = x + 0.5 - cx
                if dx * dx + dy * dy <= r2:
                    self.px(x, y, ramp, step, glow)

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, ramp: str,
                step: int, glow: int = 0) -> None:
        if rx <= 0 or ry <= 0:
            return
        for y in range(max(0, int(cy - ry) - 1), min(self.h, int(cy + ry) + 2)):
            dy = (y + 0.5 - cy) / ry
            for x in range(max(0, int(cx - rx) - 1), min(self.w, int(cx + rx) + 2)):
                dx = (x + 0.5 - cx) / rx
                if dx * dx + dy * dy <= 1.0:
                    self.px(x, y, ramp, step, glow)

    def line(self, x0: float, y0: float, x1: float, y1: float, thickness: float,
             ramp: str, step: int, glow: int = 0) -> None:
        """Kalin cizgi; uclari yuvarlak. Uzuvlar bununla ciziliyor."""
        steps = max(2, int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1)
        radius = thickness * 0.5
        for i in range(steps + 1):
            t = i / steps
            cx = x0 + (x1 - x0) * t
            cy = y0 + (y1 - y0) * t
            if thickness <= 1.2:
                self.px(int(round(cx)), int(round(cy)), ramp, step, glow)
            else:
                self.disc(cx, cy, radius, ramp, step, glow)

    def limb(self, x0: float, y0: float, angle: float, length: float,
             thickness: float, ramp: str, step: int) -> tuple[float, float]:
        """Aciyla uzuv cizer ve uc noktayi doner (zincirleme icin)."""
        x1 = x0 + math.cos(angle) * length
        y1 = y0 + math.sin(angle) * length
        self.line(x0, y0, x1, y1, thickness, ramp, step)
        return x1, y1

    def polygon(self, points: list[tuple[float, float]], ramp: str, step: int,
                glow: int = 0) -> None:
        """Tarama cizgisi ile dolu cokgen."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for y in range(max(0, int(min(ys))), min(self.h, int(max(ys)) + 1)):
            crossings: list[float] = []
            for i in range(len(points)):
                ax, ay = points[i]
                bx, by = points[(i + 1) % len(points)]
                if (ay <= y < by) or (by <= y < ay):
                    crossings.append(ax + (y - ay) / (by - ay) * (bx - ax))
            crossings.sort()
            for i in range(0, len(crossings) - 1, 2):
                self.fill_rect(int(crossings[i]), y,
                               max(1, int(crossings[i + 1]) - int(crossings[i]) + 1),
                               1, ramp, step, glow)

    def taper(self, x0: float, y0: float, x1: float, y1: float,
              w0: float, w1: float, ramp: str, step: int,
              glow: int = 0) -> None:
        """Bir uctan digerine incelen sekil (bicak agzi, boynuz, kuyruk)."""
        steps = max(2, int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1)
        for i in range(steps + 1):
            t = i / steps
            cx = x0 + (x1 - x0) * t
            cy = y0 + (y1 - y0) * t
            radius = (w0 + (w1 - w0) * t) * 0.5
            if radius < 0.6:
                self.px(int(round(cx)), int(round(cy)), ramp, step, glow)
            else:
                self.disc(cx, cy, radius, ramp, step, glow)

    # --- Doku ---------------------------------------------------------------
    def noise(self, seed: int, amount: float = 0.35, ramp: str | None = None) -> None:
        """Dolu piksellerin basamagini rastgele +-1 oynatir: yuzey dokusu.

        Deterministik seed sart - ayni sprite her calistirmada ayni gorunmeli,
        yoksa animasyon kareleri arasinda doku titrer.
        """
        rng = np.random.default_rng(seed)
        mask = self.ramp != EMPTY
        if ramp is not None:
            mask &= self.ramp == self._ri(ramp)
        roll = rng.random(self.ramp.shape)
        up = mask & (roll < amount * 0.5)
        down = mask & (roll > 1.0 - amount * 0.5)
        self.step[up] = np.minimum(self.step[up] + 1, 4)
        self.step[down] = np.maximum(self.step[down].astype(np.int16) - 1, 0)

    def dither(self, x: int, y: int, w: int, h: int, ramp: str,
               step: int, density: int = 2) -> None:
        """Sahmat deseni: iki rampa arasinda yumusak gecis izlenimi."""
        for yy in range(max(0, y), min(self.h, y + h)):
            for xx in range(max(0, x), min(self.w, x + w)):
                if (xx + yy) % density == 0:
                    self.px(xx, yy, ramp, step)

    # --- Golgeleme ----------------------------------------------------------
    def shade(self, strength: int = 1) -> None:
        """Isik yonune gore kenar basamaklarini oynatir.

        Sol-ustu bos olan piksel isik alir (basamak +1), sag-altta bosluk goren
        piksel golgede kalir (-1). Bu tek gecis, duz siluetlere hacim verir.
        """
        solid = self.ramp != EMPTY
        # Sol-ust komsu bos mu? (kenar = isik)
        lit = np.zeros_like(solid)
        lit[1:, 1:] = solid[1:, 1:] & ~solid[:-1, :-1]
        lit[0, :] = solid[0, :]
        lit[:, 0] |= solid[:, 0]
        # Sag-alt komsu bos mu? (kenar = golge)
        dark = np.zeros_like(solid)
        dark[:-1, :-1] = solid[:-1, :-1] & ~solid[1:, 1:]
        dark[-1, :] |= solid[-1, :]
        dark[:, -1] |= solid[:, -1]

        s = self.step.astype(np.int16)
        s[lit & ~dark] += strength
        s[dark & ~lit] -= strength
        self.step = np.clip(s, 0, 4).astype(np.uint8)

    def ambient_occlusion(self) -> None:
        """Ic kose kararmasi: farkli rampalarin bulustugu yerde golge."""
        solid = self.ramp != EMPTY
        diff = np.zeros_like(solid)
        diff[1:, :] |= solid[1:, :] & solid[:-1, :] & (self.ramp[1:, :] != self.ramp[:-1, :])
        s = self.step.astype(np.int16)
        s[diff] -= 1
        self.step = np.clip(s, 0, 4).astype(np.uint8)

    def outline(self, ramp: str = "ink", step: int = 0, diagonal: bool = False) -> None:
        """Siluetin disina 1 piksel cerceve. Pixel art okunurlugunun temeli."""
        solid = self.ramp != EMPTY
        grown = np.zeros_like(solid)
        grown[1:, :] |= solid[:-1, :]
        grown[:-1, :] |= solid[1:, :]
        grown[:, 1:] |= solid[:, :-1]
        grown[:, :-1] |= solid[:, 1:]
        if diagonal:
            grown[1:, 1:] |= solid[:-1, :-1]
            grown[:-1, :-1] |= solid[1:, 1:]
            grown[1:, :-1] |= solid[:-1, 1:]
            grown[:-1, 1:] |= solid[1:, :-1]
        edge = grown & ~solid
        self.ramp[edge] = self._ri(ramp)
        self.step[edge] = max(0, min(4, step))

    def recolor(self, source: str, target: str) -> None:
        """Bir rampayi digeriyle degistir (ayni sprite, farkli tur)."""
        self.ramp[self.ramp == self._ri(source)] = self._ri(target)

    # --- Donusumler ---------------------------------------------------------
    def offset(self, dx: int, dy: int) -> None:
        self.ramp = np.roll(np.roll(self.ramp, dy, axis=0), dx, axis=1)
        self.step = np.roll(np.roll(self.step, dy, axis=0), dx, axis=1)
        self.glow = np.roll(np.roll(self.glow, dy, axis=0), dx, axis=1)

    def copy(self) -> "Canvas":
        clone = Canvas(self.w, self.h)
        clone.ramp = self.ramp.copy()
        clone.step = self.step.copy()
        clone.glow = self.glow.copy()
        return clone

    def blit(self, other: "Canvas", x: int, y: int) -> None:
        """Baska bir canvas'i uzerine yapistirir (bos pikseller atlanir)."""
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + other.w), min(self.h, y + other.h)
        if x1 <= x0 or y1 <= y0:
            return
        sx0, sy0 = x0 - x, y0 - y
        sub = other.ramp[sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)]
        mask = sub != EMPTY
        self.ramp[y0:y1, x0:x1][mask] = sub[mask]
        self.step[y0:y1, x0:x1][mask] = other.step[sy0:sy0 + (y1 - y0),
                                                   sx0:sx0 + (x1 - x0)][mask]
        self.glow[y0:y1, x0:x1][mask] = other.glow[sy0:sy0 + (y1 - y0),
                                                   sx0:sx0 + (x1 - x0)][mask]

    # --- Cikti --------------------------------------------------------------
    def resolve(self, alpha: int = 255) -> pygame.Surface:
        """Indeks tamponunu gercek renklere cevirip Surface uretir."""
        rgb = np.zeros((self.h, self.w, 3), dtype=np.uint8)
        solid = self.ramp != EMPTY
        if solid.any():
            ramps = self.ramp[solid].astype(np.int32)
            steps = self.step[solid].astype(np.int32)
            rgb[solid] = _LUT[ramps, steps]

        surface = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        # pygame dizileri (genislik, yukseklik) sirali, numpy ise (satir, sutun):
        # her aktarimda eksenleri cevirmek zorundayiz.
        arr = pygame.surfarray.pixels3d(surface)
        arr[:] = np.transpose(rgb, (1, 0, 2))
        del arr
        alpha_arr = pygame.surfarray.pixels_alpha(surface)
        alpha_arr[:] = np.transpose(np.where(solid, alpha, 0).astype(np.uint8), (1, 0))
        del alpha_arr
        return surface

    def glow_mask(self) -> pygame.Surface | None:
        """Isik yayan piksellerin maskesi; lighting katmani kullanir."""
        if not self.glow.any():
            return None
        surface = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        arr = pygame.surfarray.pixels3d(surface)
        solid = self.ramp != EMPTY
        rgb = np.zeros((self.h, self.w, 3), dtype=np.uint8)
        if solid.any():
            rgb[solid] = _LUT[self.ramp[solid].astype(np.int32),
                              self.step[solid].astype(np.int32)]
        arr[:] = np.transpose(rgb, (1, 0, 2))
        del arr
        alpha_arr = pygame.surfarray.pixels_alpha(surface)
        alpha_arr[:] = np.transpose(self.glow, (1, 0))
        del alpha_arr
        return surface


# --- Yuzey duzeyinde yardimcilar --------------------------------------------
def flip_h(surface: pygame.Surface) -> pygame.Surface:
    return pygame.transform.flip(surface, True, False)


def tint(surface: pygame.Surface, color, strength: float) -> pygame.Surface:
    """Sprite'i bir renge dogru karistirir. Zehir, donma, buyu auralari icin.

    Alfa kanalina dokunmadan sadece RGB'yi kaydirir; siluet bozulmaz.
    """
    out = surface.copy()
    strength = max(0.0, min(1.0, strength))
    if strength <= 0.0:
        return out
    rgb = pygame.surfarray.pixels3d(out).astype(np.float32)
    target = np.array(color, dtype=np.float32)
    rgb += (target - rgb) * strength
    pygame.surfarray.pixels3d(out)[:] = rgb.astype(np.uint8)
    return out


def silhouette(surface: pygame.Surface, color=(255, 255, 255)) -> pygame.Surface:
    """Tek renkli siluet: hasar flasi icin en okunur bicim."""
    out = surface.copy()
    arr = pygame.surfarray.pixels3d(out)
    arr[:, :, 0] = color[0]
    arr[:, :, 1] = color[1]
    arr[:, :, 2] = color[2]
    del arr
    return out


def outline_surface(surface: pygame.Surface, color=(255, 255, 255),
                    thickness: int = 1) -> pygame.Surface:
    """Yuzeyin cevresine cerceve ekler (hedef vurgusu, etkilesim ipucu)."""
    w, h = surface.get_size()
    pad = thickness
    out = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    mask = silhouette(surface, color)
    for dx in range(-thickness, thickness + 1):
        for dy in range(-thickness, thickness + 1):
            if dx or dy:
                out.blit(mask, (pad + dx, pad + dy))
    out.blit(surface, (pad, pad))
    return out


def _antler_branch(c: Canvas, x: float, y: float, angle: float, length: float,
                   width: float, depth: int, ramp: str, step: int,
                   glow: int) -> None:
    """Ozyinelemeli boynuz dali.

    Geyik boynuzunu elle cizmek yerine dallandiriyoruz: her dal kendinden
    kisa ve ince iki dal doguruyor. Az kodla organik bir sekil cikiyor ve
    parametreleri oynatarak bambaska bir geyik elde edilebiliyor.
    """
    if depth <= 0 or length < 2.0:
        return
    ex = x + math.cos(angle) * length
    ey = y + math.sin(angle) * length
    c.taper(x, y, ex, ey, width, width * 0.7, ramp, step, glow)
    # Geriye dogru genis acili tine + govdeyi surduren dar acili dal.
    # Ikisinin acisi birbirine yakin olursa boynuz "catal" degil "cubuk"
    # okunur; bu yuzden ilk dal belirgin sekilde ayriliyor.
    _antler_branch(c, ex, ey, angle - 0.75, length * 0.66, width * 0.72,
                   depth - 1, ramp, step, glow)
    _antler_branch(c, ex, ey, angle + 0.22, length * 0.80, width * 0.78,
                   depth - 1, ramp, min(4, step), glow)


def build_deer(width: int = 104, height: int = 124, ramp: str = "azure",
               step: int = 4, glow: int = 210) -> pygame.Surface:
    """Yanki geyigi.

    Rey'in gogsundeki dovmenin ve prologda goruneN yankinin ayni sekli.
    Sprite olceginde (26 piksel) bir geyik okunmaz; bu yuzden geyik burada,
    tam boyutta yasiyor ve dovme oyunda yalnizca ona bir gonderme.

    Saga bakar; sola cevirmek icin `flip_h`.
    """
    c = Canvas(width, height)
    # Tasarim uzayi 104x124. Govde 0..92 araligina cizilir; ustteki 30
    # birimlik pay boynuzlara ayrilir. Bu payi birakmayinca boynuzlar
    # tuvalin disina tasip kirpiliyordu.
    sx, sy = width / 104.0, height / 124.0
    HEADROOM = 30.0

    def X(v: float) -> float:
        return v * sx

    def Y(v: float) -> float:
        """Dikey *konum* - bosluk payini icerir."""
        return (v + HEADROOM) * sy

    def H(v: float) -> float:
        """Dikey *uzunluk* - paya eklenmez. Yaricap ve boy icin bunu kullan;
        Y() ile karistirmak govdeyi devasa bir blob yapiyor."""
        return v * sy

    # Bacaklar (govdeden once: govde ust kismini kapatsin)
    for hip_x, foot_x in ((34, 30), (40, 44), (62, 58), (68, 72)):
        c.taper(X(hip_x), Y(58), X(foot_x), Y(84), 5.0 * sx, 2.2 * sx,
                ramp, step - 1, glow // 2)
        # Toynak
        c.taper(X(foot_x), Y(80), X(foot_x), Y(85), 3.0 * sx, 1.6 * sx,
                ramp, step, glow)

    # Govde
    c.ellipse(X(50), Y(52), X(22), H(12), ramp, step - 1, glow // 2)
    c.ellipse(X(62), Y(50), X(12), H(11), ramp, step - 1, glow // 2)

    # Boyun ve kafa
    c.taper(X(68), Y(44), X(80), Y(24), 13.0 * sx, 8.0 * sx, ramp, step, glow)
    c.ellipse(X(83), Y(21), X(8), H(5), ramp, step, glow)
    c.taper(X(88), Y(22), X(97), Y(25), 6.0 * sx, 3.0 * sx, ramp, step, glow)

    # Kulak
    c.taper(X(79), Y(17), X(73), Y(10), 4.0 * sx, 1.5 * sx, ramp, step, glow)

    # Boynuzlar: iki taca, biri hafif geride. Geyigi geyik yapan sey bunlar,
    # bu yuzden govdeye gore comertce buyukler.
    _antler_branch(c, X(81), Y(14), -1.25, 20.0 * sy, 5.0 * sx, 5,
                   ramp, step, glow)
    _antler_branch(c, X(76), Y(15), -1.95, 17.0 * sy, 4.2 * sx, 5,
                   ramp, step - 1, glow)

    # Kuyruk
    c.taper(X(29), Y(46), X(24), Y(40), 4.5 * sx, 1.8 * sx, ramp, step, glow)

    # Goz: karanlik bir nokta, yankinin bakisini verir
    c.px(int(X(85)), int(Y(20)), "ink", 0)

    c.shade()
    return c.resolve()


def make_icon(size: int = 32) -> pygame.Surface:
    """Pencere ikonu: Rey'in kilici ve yanki halkasi."""
    c = Canvas(size, size)
    cx = size // 2
    c.disc(cx, cx, size * 0.42, "violet", 1)
    c.disc(cx, cx, size * 0.32, "ink", 1)
    # Kilic: capraz, kabza asagida
    c.taper(cx - 7, cx + 8, cx + 6, cx - 9, 3.0, 1.0, "stone", 4)
    c.line(cx - 9, cx + 6, cx - 5, cx + 10, 3.0, "gold", 2)
    c.line(cx - 4, cx + 3, cx + 1, cx + 8, 2.0, "earth", 2)
    c.shade()
    c.outline("ink", 0)
    return c.resolve()
