"""Uygulama cekirdegi: pencere, sabit zaman adimi, olcekleme, kuresel zaman.

Uc karar bu dosyada dugumleniyor:

1. **Sabit zaman adimi.** Fizik her zaman 1/60'lik adimlarla ilerler; makine
   yavassa birden fazla adim, hizliysa bekleme yapilir. Eski koddaki "her sey
   60 FPS varsayimina gomulu" sorunu boylece kokten cozulur.

2. **Sanal cozunurluk.** Her sey 480x270'e cizilir, sonra tam sayi katiyla
   buyutulur. Pixel art keskin kalir, her ekranda ayni miktarda dunya gorunur.

3. **Kuresel zaman olcegi.** `hitstop` ve `slowmo` burada yasar; vurus aninda
   oyunu birkac kare dondurmak, "AAA hissi"nin en ucuz ve en etkili aracidir.
"""
from __future__ import annotations

import sys
import time

import pygame

from lore.constants import (
    FIXED_DT, GAME_TITLE, MAX_FRAME_SKIP, TICK_RATE,
    VIRTUAL_H, VIRTUAL_W, WINDOW_H, WINDOW_W,
)
from lore.core.assets import Assets
from lore.core.audio import AudioEngine
from lore.core.config import Config
from lore.core.input import Action, InputManager
from lore.core.paths import user_data_root
from lore.core.scene import SceneManager


class App:
    def __init__(self) -> None:
        pygame.init()

        self.config = Config()
        self.assets = Assets()
        self.audio = AudioEngine(self.config, self.assets)
        self.input = InputManager(self.config)
        self.scenes = SceneManager(self)

        self.running = False
        self.debug = False

        # --- Zaman ----------------------------------------------------------
        self.clock = pygame.time.Clock()
        self.time = 0.0                 # Oyun zamani (donmalardan etkilenir)
        self.real_time = 0.0            # Gercek zaman (asla durmaz)
        self.frame = 0
        self.fps = 0.0
        self._accumulator = 0.0
        self._last = time.perf_counter()

        self.time_scale = 1.0           # Kalici yavaslatma (ornegin bullet-time)
        self._hitstop = 0.0             # Kisa donma, saniye
        self._slowmo_timer = 0.0
        self._slowmo_scale = 1.0

        # --- Ekran ----------------------------------------------------------
        # Pencere once acilmali: convert()/convert_alpha() bir ekran bicimi
        # olmadan calismaz ve pygame hata firlatir.
        self.screen: pygame.Surface | None = None
        self.scale = 1
        self.viewport = pygame.Rect(0, 0, WINDOW_W, WINDOW_H)
        self._create_window()
        self.canvas = pygame.Surface((VIRTUAL_W, VIRTUAL_H)).convert_alpha()

        self.audio.apply_config()

    # --- Pencere ------------------------------------------------------------
    def _create_window(self) -> None:
        fullscreen = bool(self.config.get("fullscreen"))
        flags = pygame.SCALED | pygame.RESIZABLE
        if fullscreen:
            flags |= pygame.FULLSCREEN

        size = (WINDOW_W, WINDOW_H)
        if not fullscreen:
            configured = int(self.config.get("scale") or 0)
            scale = configured or self._best_scale()
            size = (VIRTUAL_W * scale, VIRTUAL_H * scale)

        vsync = 1 if self.config.get("vsync") else 0
        try:
            self.screen = pygame.display.set_mode(size, flags, vsync=vsync)
        except pygame.error:
            # vsync bazi surucularde reddedilir; onsuz tekrar dene.
            self.screen = pygame.display.set_mode(size, flags)

        pygame.display.set_caption(GAME_TITLE)
        self._set_icon()
        self._recompute_viewport()

    def _best_scale(self) -> int:
        """Ekrana sigan en buyuk tam sayi kat (kenarlarda biraz pay birakarak)."""
        try:
            info = pygame.display.Info()
            avail_w, avail_h = info.current_w, info.current_h - 80
        except pygame.error:
            return 3
        scale = min(avail_w // VIRTUAL_W, avail_h // VIRTUAL_H)
        return max(1, min(scale, 8))

    def _set_icon(self) -> None:
        from lore.gfx.forge import make_icon
        try:
            pygame.display.set_icon(make_icon())
        except Exception:               # Ikon kritik degil, oyunu durdurmasin
            pass

    def _recompute_viewport(self) -> None:
        """Canvas'i pencereye ortalayan, en-boy oranini koruyan dikdortgen."""
        if self.screen is None:
            return
        sw, sh = self.screen.get_size()
        if self.config.get("pixel_perfect", True):
            scale = max(1, min(sw // VIRTUAL_W, sh // VIRTUAL_H))
        else:
            scale = min(sw / VIRTUAL_W, sh / VIRTUAL_H)
        self.scale = scale
        w, h = int(VIRTUAL_W * scale), int(VIRTUAL_H * scale)
        self.viewport = pygame.Rect((sw - w) // 2, (sh - h) // 2, w, h)

    def toggle_fullscreen(self) -> None:
        self.config.toggle("fullscreen")
        self.config.save()
        self._create_window()

    def rebuild_window(self) -> None:
        """Pencereyi mevcut ayarlarla yeniden kurar (vsync, olcek degisimi)."""
        self._create_window()

    def screenshot(self) -> None:
        path = user_data_root() / f"lore_{int(time.time())}.png"
        try:
            pygame.image.save(self.canvas, str(path))
            print(f"[app] ekran goruntusu: {path}")
        except pygame.error as exc:
            print(f"[app] ekran goruntusu alinamadi: {exc}")

    # --- Zaman kontrolu -----------------------------------------------------
    def hitstop(self, seconds: float) -> None:
        """Vurus aninda oyunu dondurur. En uzun istek kazanir, birikmez."""
        self._hitstop = max(self._hitstop, seconds)

    def slowmo(self, scale: float, duration: float) -> None:
        self._slowmo_scale = scale
        self._slowmo_timer = max(self._slowmo_timer, duration)

    @property
    def frozen(self) -> bool:
        return self._hitstop > 0.0

    # --- Ana dongu ----------------------------------------------------------
    def run(self, first_scene) -> None:
        self.scenes.set_root(first_scene, transition=False)
        self.running = True
        self._last = time.perf_counter()

        try:
            while self.running:
                self._tick()
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def _tick(self) -> None:
        now = time.perf_counter()
        frame_time = min(now - self._last, FIXED_DT * MAX_FRAME_SKIP)
        self._last = now
        self.real_time += frame_time
        self.fps = self.clock.get_fps()

        self.input.begin_frame(frame_time)
        self.audio.begin_frame()
        self._pump_events()

        # Donma ve yavaslatma gercek zamanda islenir, oyun zamaninda degil -
        # yoksa donma kendini asla bitiremez.
        if self._hitstop > 0.0:
            self._hitstop = max(0.0, self._hitstop - frame_time)
            frame_time = 0.0
        elif self._slowmo_timer > 0.0:
            self._slowmo_timer = max(0.0, self._slowmo_timer - frame_time)
            frame_time *= self._slowmo_scale

        self._accumulator += frame_time * self.time_scale
        steps = 0
        while self._accumulator >= FIXED_DT and steps < MAX_FRAME_SKIP:
            self.input.end_frame()
            self.scenes.update(FIXED_DT)
            self.time += FIXED_DT
            self._accumulator -= FIXED_DT
            steps += 1
        if steps == 0:
            # Donma sirasinda bile girdi okunmali; yoksa tuslar yutulur.
            self.input.end_frame()
            self.scenes.update(0.0)

        self._render()
        self.frame += 1
        self.clock.tick(TICK_RATE if self.config.get("vsync") else 0)

    def _pump_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
                return
            if event.type == pygame.VIDEORESIZE:
                self._recompute_viewport()
                continue
            self.input.handle_event(event)

            if event.type == pygame.KEYDOWN:
                if self.input.pressed(Action.FULLSCREEN):
                    self.toggle_fullscreen()
                    continue
                if self.input.pressed(Action.SCREENSHOT):
                    self.screenshot()
                    continue
                if self.input.pressed(Action.DEBUG_TOGGLE):
                    self.debug = not self.debug
                    continue
            self.scenes.handle_event(event)

    def _render(self) -> None:
        if self.screen is None:
            return
        self.canvas.fill((0, 0, 0, 255))
        self.scenes.draw(self.canvas)

        if self.debug or self.config.get("show_fps"):
            self._draw_debug()

        self.screen.fill((0, 0, 0))
        if self.scale == 1 and self.viewport.size == self.canvas.get_size():
            self.screen.blit(self.canvas, self.viewport.topleft)
        else:
            # Tam sayi olceklemede `scale` en hizli ve en keskin yol.
            scaled = pygame.transform.scale(self.canvas, self.viewport.size)
            self.screen.blit(scaled, self.viewport.topleft)
        pygame.display.flip()

    def _draw_debug(self) -> None:
        from lore.gfx.text import draw_text
        scene = self.scenes.current
        lines = [
            f"FPS {self.fps:4.1f}",
            f"SCN {type(scene).__name__ if scene else '-'} x{len(self.scenes.stack)}",
        ]
        if self.debug and scene is not None:
            lines.append(self.assets.stats())
            extra = getattr(scene, "debug_lines", None)
            if callable(extra):
                lines.extend(extra())
        for i, line in enumerate(lines):
            draw_text(self.canvas, line, 4, 4 + i * 9, color=(120, 255, 180), shadow=True)

    # --- Kapanis ------------------------------------------------------------
    def quit(self) -> None:
        self.running = False

    def shutdown(self) -> None:
        self.config.save()
        self.scenes.shutdown()
        self.audio.shutdown()
        pygame.quit()


def main() -> int:
    from lore.scenes.boot import BootScene
    app = App()
    app.run(BootScene)
    return 0


if __name__ == "__main__":
    sys.exit(main())
