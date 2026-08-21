"""Ana menu.

Arka planda oynanmayan bir sahne var: kayan parallax, suzulen kul zerreleri ve
mesale isigi. Menu ekrani da oyunun dunyasindan bir parca olmali; duz renk bir
arka plan "ucuz" hissettirir.
"""
from __future__ import annotations

import math

import pygame

from lore.constants import GAME_SHORT, GAME_VERSION, VIRTUAL_H, VIRTUAL_W
from lore.core.input import Action
from lore.core.save import SLOT_COUNT, SaveData, list_slots, save_slot
from lore.core.scene import Scene
from lore.gfx import text as gfx_text
from lore.gfx.palette import RAMPS, UI_TEXT, UI_TEXT_DIM, UI_TEXT_HILITE
from lore.gfx.particles import ParticleField
from lore.gfx.ui import Menu, MenuItem, panel
from lore.world.parallax import Parallax, Weather


class _BackdropCamera:
    """Menu arka planini kaydirmak icin sahte kamera."""

    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0

    @property
    def offset(self) -> tuple[int, int]:
        return (int(self.x), int(self.y))

    @property
    def view_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), VIRTUAL_W, VIRTUAL_H)


class TitleScene(Scene):
    def on_enter(self, **kwargs) -> None:
        self.timer = 0.0
        self.camera = _BackdropCamera()
        self.parallax = Parallax("hollow", self.app.assets)
        self.weather = Weather("ash", 70)
        self.particles = ParticleField(300)
        self.mode = "main"          # main | slots
        self.slots = list_slots()
        self.slot_index = 0
        self._build_menu()
        self.app.audio.play_music("assets/background_music.wav")

    def _build_menu(self) -> None:
        has_save = any(s is not None for s in self.slots)
        self.menu = Menu([
            MenuItem("Devam Et", self._continue, enabled=has_save,
                     hint="En son kaydedilen yankidan devam et"),
            MenuItem("Yeni Oyun", self._open_slots,
                     hint="Rey'in hikayesini bastan basla"),
            MenuItem("Ayarlar", self._open_settings,
                     hint="Ses, goruntu ve erisilebilirlik"),
            MenuItem("Cikis", self.app.quit),
        ], VIRTUAL_W // 2, 150)

    # --- Eylemler -----------------------------------------------------------
    def _latest_slot(self) -> int:
        best, best_time = -1, -1.0
        for i, data in enumerate(self.slots):
            if data is not None and data.updated_at > best_time:
                best, best_time = i, data.updated_at
        return best

    def _continue(self) -> None:
        slot = self._latest_slot()
        if slot < 0:
            return
        data = self.slots[slot]
        data.slot = slot
        self._start(data)

    def _open_slots(self) -> None:
        self.mode = "slots"
        self.slot_index = 0

    def _open_settings(self) -> None:
        from lore.scenes.settings import SettingsScene
        self.manager.push(SettingsScene)

    def _start(self, data: SaveData) -> None:
        from lore.scenes.play import PlayScene
        self.manager.replace(PlayScene, level_id=data.level_id, save=data)

    def _start_new(self, slot: int) -> None:
        data = SaveData()
        data.slot = slot
        save_slot(slot, data)
        self._start(data)

    # --- Girdi --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.mode == "main":
                self.menu.click(self.app, self.app.audio)

    def update(self, dt: float) -> None:
        self.timer += dt
        # Arka plan yavasca kayar: ekran hicbir zaman tamamen durmaz.
        self.camera.x = self.timer * 11.0
        self.weather.update(dt)
        self.particles.update(dt)
        if int(self.timer * 6) % 3 == 0:
            self.particles.emit(
                self.camera.x + VIRTUAL_W * 0.5, VIRTUAL_H + 4, 1,
                speed=(6.0, 18.0), angle=(-math.pi * 0.7, -math.pi * 0.3),
                life=(1.4, 2.6), gravity=-6.0, drag=0.5, ramp="ember", glow=90)

        inp = self.app.input
        if self.mode == "main":
            self.menu.update(dt)
            self.menu.handle_mouse(self.app, self.app.audio)
            self.menu.handle_input(inp, self.app.audio)
        else:
            self._update_slots(inp)

    def _update_slots(self, inp) -> None:
        if inp.pressed(Action.UP):
            self.slot_index = (self.slot_index - 1) % SLOT_COUNT
            self.app.audio.play("ui_move")
        elif inp.pressed(Action.DOWN):
            self.slot_index = (self.slot_index + 1) % SLOT_COUNT
            self.app.audio.play("ui_move")
        if inp.pressed(Action.CONFIRM):
            self.app.audio.play("ui_select")
            self._start_new(self.slot_index)
        elif inp.pressed(Action.CANCEL):
            self.app.audio.play("ui_back")
            self.mode = "main"
            self.slots = list_slots()
            self._build_menu()

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        self.parallax.draw(surface, self.camera)
        self.weather.draw(surface)
        self.particles.draw(surface, self.camera)

        # Karartma: menu metni her zaman okunur kalsin.
        veil = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        veil.fill((*RAMPS["ink"][0], 130))
        surface.blit(veil, (0, 0))

        self._draw_logo(surface)

        if self.mode == "main":
            self.menu.draw(surface)
        else:
            self._draw_slots(surface)

        gfx_text.draw_text(surface, f"v{GAME_VERSION}", VIRTUAL_W - 6,
                           VIRTUAL_H - 12, color=RAMPS["stone"][2], align="right")

    def _draw_logo(self, surface: pygame.Surface) -> None:
        cx = VIRTUAL_W // 2
        bob = math.sin(self.timer * 1.4) * 1.5
        gfx_text.draw_text(surface, GAME_SHORT, cx, int(48 + bob),
                           color=UI_TEXT_HILITE, align="center", outline=True,
                           tracking=6)
        gfx_text.draw_text(surface, "LEGEND OF REY", cx, int(66 + bob),
                           color=UI_TEXT, align="center", shadow=True, tracking=3)
        gfx_text.draw_text(surface, "E C H O E S", cx, int(80 + bob),
                           color=RAMPS["violet"][4], align="center", shadow=True,
                           tracking=2)
        # Ayrac cizgisi: glif hucresi 11 piksel yuksek, alt uzanti payi da var.
        # 94'te ustu cizili gibi gorunuyordu; 98 net bir ayrac birakiyor.
        pygame.draw.line(surface, RAMPS["gold"][2],
                         (cx - 62, int(98 + bob)), (cx + 62, int(98 + bob)))

    def _draw_slots(self, surface: pygame.Surface) -> None:
        gfx_text.draw_text(surface, "KAYIT YUVASI SEC", VIRTUAL_W // 2, 118,
                           color=UI_TEXT, align="center", shadow=True)
        for i in range(SLOT_COUNT):
            rect = pygame.Rect(VIRTUAL_W // 2 - 92, 134 + i * 30, 184, 26)
            selected = i == self.slot_index
            panel(surface, rect, alpha=200,
                  accent=UI_TEXT_HILITE if selected else RAMPS["stone"][2])
            data = self.slots[i]
            label = f"Yuva {i + 1}"
            if data is None:
                detail = "-- bos --"
            else:
                minutes = int(data.playtime // 60)
                detail = (f"Act {data.act}  {data.level_id}  "
                          f"{minutes}dk  {data.essence}oz")
            gfx_text.draw_text(surface, label, rect.x + 8, rect.y + 4,
                               color=UI_TEXT_HILITE if selected else UI_TEXT)
            gfx_text.draw_text(surface, detail, rect.x + 8, rect.y + 15,
                               color=UI_TEXT_DIM)
            if data is not None and selected:
                gfx_text.draw_text(surface, "uzerine yazilacak", rect.right - 8,
                                   rect.y + 15, color=RAMPS["blood"][3],
                                   align="right")
        gfx_text.draw_text(surface, "[Enter] basla    [Esc] geri",
                           VIRTUAL_W // 2, VIRTUAL_H - 24, color=UI_TEXT_DIM,
                           align="center")
