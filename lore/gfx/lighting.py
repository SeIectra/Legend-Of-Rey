"""Dinamik 2B isiklandirma.

Yontem klasik ve hizli: sahne cizildikten sonra bir "isik haritasi" olusturulur
ve sahnenin uzerine **carpilarak** uygulanir.

    sonuc = sahne * isik_haritasi

Isik haritasi ortam rengiyle doldurulur (karanlik), sonra her isik kaynagi
toplamali (additive) olarak icine cizilir. Bir pikselin uzerinde isik yoksa
ortam rengiyle carpilir, yani kararir.

Radyal degradeler yaricapa gore onbelleklenir; kare basina tek bir blit'e
duserler. 30-40 isik kaynagi hicbir sey hissettirmez.

Isik sadece guzellik degil, **yon bulma araci**: mesaleler gidilecek yolu,
Echo Shrine'lar guvenli noktayi, dusman gozleri tehdidi isaretler.
"""
from __future__ import annotations


import numpy as np
import pygame

from lore.constants import VIRTUAL_H, VIRTUAL_W

# Act'lere gore ortam isigi. Deger ne kadar dusukse dunya o kadar karanlik.
AMBIENT: dict[int, tuple[int, int, int]] = {
    1: (128, 132, 158),
    2: (158, 166, 146),
    3: (92, 116, 150),
    4: (126, 110, 104),
    5: (100, 84, 132),
}


class LightMap:
    def __init__(self) -> None:
        self.surface = pygame.Surface((VIRTUAL_W, VIRTUAL_H)).convert()
        self.ambient: tuple[int, int, int] = AMBIENT[1]
        self.enabled = True
        self._cache: dict[tuple[int, tuple], pygame.Surface] = {}
        self._lights: list[tuple[float, float, float, tuple, float]] = []

    def set_act(self, act: int) -> None:
        self.ambient = AMBIENT.get(act, AMBIENT[1])

    def begin(self) -> None:
        self._lights.clear()

    def add(self, x: float, y: float, radius: float,
            color: tuple = (255, 220, 170), intensity: float = 1.0) -> None:
        self._lights.append((x, y, radius, color, intensity))

    # --- Degrade uretimi ----------------------------------------------------
    def _gradient(self, radius: int, color: tuple) -> pygame.Surface:
        key = (radius, color)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        size = radius * 2
        # Mesafeye gore dusen parlaklik. Ust: 1/(1+d^2) benzeri yumusak dusus;
        # kenarda tam sifira inmesi sart, yoksa isik dairesi kare kenariyla
        # kesilir ve "spot" gibi gorunur.
        yy, xx = np.mgrid[0:size, 0:size]
        dx = xx - radius + 0.5
        dy = yy - radius + 0.5
        dist = np.sqrt(dx * dx + dy * dy) / max(1.0, radius)
        falloff = np.clip(1.0 - dist, 0.0, 1.0) ** 1.9

        rgb = np.zeros((size, size, 3), dtype=np.uint8)
        for i in range(3):
            rgb[:, :, i] = (falloff * color[i]).astype(np.uint8)

        surface = pygame.Surface((size, size)).convert()
        pygame.surfarray.pixels3d(surface)[:] = np.transpose(rgb, (1, 0, 2))
        if len(self._cache) > 96:
            self._cache.clear()
        self._cache[key] = surface
        return surface

    # --- Uygulama -----------------------------------------------------------
    def render(self, target: pygame.Surface, camera) -> None:
        if not self.enabled:
            return
        self.surface.fill(self.ambient)
        ox, oy = camera.offset
        view = camera.view_rect

        for x, y, radius, color, intensity in self._lights:
            r = int(radius)
            if r <= 0:
                continue
            # Ekran disindaki isiklari atla.
            if not (view.left - r <= x <= view.right + r
                    and view.top - r <= y <= view.bottom + r):
                continue
            tinted = color
            if intensity < 1.0:
                tinted = tuple(int(c * intensity) for c in color)
            gradient = self._gradient(r, tinted)
            self.surface.blit(gradient, (int(x) - r - ox, int(y) - r - oy),
                              special_flags=pygame.BLEND_RGB_ADD)

        target.blit(self.surface, (0, 0), special_flags=pygame.BLEND_RGB_MULT)


class GlowLayer:
    """Isik yayan piksellerin uzerine eklenen yumusak parlama (bloom).

    Gercek bloom pahali; burada ucuz bir taklidini yapiyoruz: parlayan
    pikseller kucultulup buyutuluyor (bulaniklik yerine gecer) ve toplamali
    olarak geri ekleniyor.
    """

    def __init__(self, scale: int = 4) -> None:
        self.scale = scale
        self.layer = pygame.Surface((VIRTUAL_W, VIRTUAL_H)).convert()
        self.small = pygame.Surface(
            (VIRTUAL_W // scale, VIRTUAL_H // scale)).convert()
        self.enabled = True

    def begin(self) -> None:
        self.layer.fill((0, 0, 0))

    def add_surface(self, image: pygame.Surface, pos: tuple[int, int]) -> None:
        self.layer.blit(image, pos, special_flags=pygame.BLEND_RGB_ADD)

    def add_point(self, x: int, y: int, radius: int, color: tuple) -> None:
        pygame.draw.circle(self.layer, color, (x, y), radius)

    def render(self, target: pygame.Surface, strength: float = 0.7) -> None:
        if not self.enabled:
            return
        pygame.transform.scale(self.layer, self.small.get_size(), self.small)
        blurred = pygame.transform.smoothscale(self.small, (VIRTUAL_W, VIRTUAL_H))
        if strength < 1.0:
            # BLEND_RGB_ADD alfayi yok sayar; siddeti renkleri kisarak
            # ayarliyoruz. set_alpha burada hicbir sey yapmazdi.
            k = int(255 * max(0.0, min(1.0, strength)))
            blurred.fill((k, k, k), special_flags=pygame.BLEND_RGB_MULT)
        target.blit(blurred, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
