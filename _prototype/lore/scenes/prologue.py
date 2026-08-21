"""Prolog: Rey'in kim oldugunu anlatan acilis.

Tasarim karari: oyuncuya bir metin duvari okutmuyoruz. Metin harf harf yaziliyor
ve **kendi yankisini birakiyor** - her satirin sonunda solmus bir kopyasi
geride kaliyor. Anlatinin merkezindeki fikri (gecmis tamamen gitmez, yanki
olarak kalir) oyuncu okumadan once *goruyor*.

Geyik son sahnede beliriyor. Sprite olceginde (26 piksel) bir geyik okunmaz;
bu yuzden Rey'in gogsundeki dovme oyunda yalnizca koyu bir isaret, geyigin
kendisi ise burada tam boyutta.

Atlanabilir: Esc ya da Enter. Kimse acilisi ikinci kez izlemek zorunda degil.
"""
from __future__ import annotations

import math
import random

import pygame

from lore.constants import VIRTUAL_H, VIRTUAL_W
from lore.core.input import Action
from lore.core.mathx import clamp, ease_out_cubic
from lore.core.scene import Scene
from lore.gfx import text as gfx_text
from lore.gfx.forge import build_deer, flip_h
from lore.gfx.palette import RAMPS, UI_TEXT, UI_TEXT_DIM, UI_TEXT_HILITE
from lore.gfx.particles import ParticleField

# Her sahne: (satirlar, sure, gorsel)
# Metin 480 piksel genisligine gore kirildi; satir basina ~52 karakter.
PANELS: list[dict] = [
    {
        "lines": [
            "Bolunme gunu dunya bir kez catirdadi",
            "ve bir daha hic susmadi.",
        ],
        "visual": "crack",
        "hold": 3.6,
    },
    {
        "lines": [
            "Kirilan her sey ardinda bir yanki birakti.",
            "Bir adim, bir soz, bir veda.",
            "Cogu insan onlari yalnizca ugultu olarak duyar.",
        ],
        "visual": "motes",
        "hold": 4.6,
    },
    {
        "lines": [
            "Rey duymakla kalmaz.",
            "Yankilar ona cevap verir.",
        ],
        "visual": "listen",
        "hold": 3.8,
    },
    {
        "lines": [
            "Cocukken ormanda kayboldugunda",
            "bir geyik onu evine goturdu.",
            "Geyik uc kis once olmustu.",
        ],
        "visual": "deer",
        "hold": 5.2,
    },
    {
        "lines": [
            "O gunden beri isareti gogsunde tasir",
            "ve hicbir zaman gercekten yalniz kalmaz.",
        ],
        "visual": "deer_close",
        "hold": 4.4,
    },
    {
        "lines": [
            "Bu gece Kul Korosu kardesi Ardo'yu aldi.",
            "Ev sessiz. Ama ev bos degil.",
            "",
            "Bir yanki fisildiyor:  onlar batiya gitti.",
        ],
        "visual": "call",
        "hold": 5.6,
    },
]

TYPE_SPEED = 34.0           # Saniyede kac harf
LINE_PAUSE = 0.32           # Satirlar arasi duraklama
FADE = 0.7


class ProloguePanel:
    """Tek bir anlatim sahnesinin daktilo durumu."""

    def __init__(self, data: dict) -> None:
        self.lines = data["lines"]
        self.visual = data.get("visual", "motes")
        self.hold = data.get("hold", 4.0)
        self.revealed = 0.0
        self.line_index = 0
        self.pause = 0.0
        self.done_typing = False
        self.hold_timer = 0.0

    @property
    def total_chars(self) -> int:
        return sum(len(line) for line in self.lines)

    def update(self, dt: float) -> bool:
        """True donerse sahne bitti."""
        if not self.done_typing:
            if self.pause > 0.0:
                self.pause -= dt
                return False
            self.revealed += TYPE_SPEED * dt
            current = self.lines[self.line_index]
            if self.revealed >= len(current):
                self.revealed = 0.0
                self.line_index += 1
                self.pause = LINE_PAUSE
                if self.line_index >= len(self.lines):
                    self.done_typing = True
                    self.line_index = len(self.lines)
            return False

        self.hold_timer += dt
        return self.hold_timer >= self.hold

    def skip_typing(self) -> None:
        self.done_typing = True
        self.line_index = len(self.lines)
        self.revealed = 0.0

    def visible_lines(self) -> list[str]:
        out = []
        for i, line in enumerate(self.lines):
            if i < self.line_index:
                out.append(line)
            elif i == self.line_index:
                out.append(line[:int(self.revealed)])
            else:
                break
        return out


class PrologueScene(Scene):
    def on_enter(self, save=None, index=None, **kwargs) -> None:
        self.save = save
        self.index = index
        self.time = 0.0
        self.panel_index = 0
        self.panel = ProloguePanel(PANELS[0])
        self.fade_in = 0.0
        self.finished = False
        self.particles = ParticleField(420)
        self.deer = self.app.assets.generated("prologue:deer", build_deer)
        self.deer_flipped = self.app.assets.generated(
            "prologue:deer_flip", lambda: flip_h(self.deer))
        self._last_typed_line = -1
        self.app.audio.play_music("assets/background_music.wav")

    # --- Girdi --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._finish()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._advance()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._advance()

    def _advance(self) -> None:
        """Once yaziyi tamamla, ikinci basista sonraki sahneye gec."""
        if not self.panel.done_typing:
            self.panel.skip_typing()
        else:
            self._next_panel()

    def _next_panel(self) -> None:
        self.panel_index += 1
        if self.panel_index >= len(PANELS):
            self._finish()
            return
        self.panel = ProloguePanel(PANELS[self.panel_index])
        self.fade_in = 0.0
        self._last_typed_line = -1
        self.app.audio.play("echo_voice", volume=0.5)

    def _finish(self) -> None:
        if self.finished:
            return
        self.finished = True
        from lore.scenes.play import PlayScene
        level_id = self.save.level_id if self.save else ""
        self.manager.replace(PlayScene, level_id=level_id, save=self.save,
                             index=self.index)

    # --- Guncelleme ---------------------------------------------------------
    def update(self, dt: float) -> None:
        self.time += dt
        self.fade_in = min(1.0, self.fade_in + dt / FADE)
        self.particles.update(dt)

        # Yanki zerreleri: ekranda hep hafif bir hareket olsun.
        if random.random() < dt * 14.0:
            self.particles.emit(
                random.uniform(0, VIRTUAL_W), VIRTUAL_H + 4, 1,
                speed=(4.0, 14.0), angle=(-math.pi * 0.65, -math.pi * 0.35),
                life=(2.2, 4.5), gravity=-3.0, drag=0.35,
                ramp="azure", glow=120, size=(1.0, 1.6))

        # Her yeni satir bir yanki sesi birakir.
        if self.panel.line_index != self._last_typed_line:
            self._last_typed_line = self.panel.line_index
            if 0 < self.panel.line_index <= len(self.panel.lines):
                self.app.audio.play("echo_voice", volume=0.34,
                                    pitch=-2.0 + self.panel.line_index * 1.5)

        if self.panel.update(dt):
            self._next_panel()

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(RAMPS["ink"][0])
        self._draw_visual(surface)
        self.particles.draw(surface, _StaticCamera())
        self._draw_text(surface)
        self._draw_footer(surface)

    def _draw_visual(self, surface: pygame.Surface) -> None:
        kind = self.panel.visual
        alpha = int(255 * ease_out_cubic(self.fade_in))
        cx, cy = VIRTUAL_W // 2, 96

        if kind == "crack":
            # Ekrani boydan boya gecen bir catlak: Bolunme.
            t = clamp(self.time * 0.6, 0.0, 1.0)
            for i in range(int(60 * t)):
                x = int(i * VIRTUAL_W / 60)
                y = int(cy + math.sin(i * 0.7) * 9 + math.sin(i * 2.3) * 4)
                color = RAMPS["violet"][4] if i % 3 else RAMPS["azure"][4]
                surface.fill(color, (x, y, 2, 2))
        elif kind == "motes":
            for i in range(26):
                a = self.time * 0.5 + i * 0.618 * math.tau
                rad = 30 + (i % 5) * 11
                x = int(cx + math.cos(a) * rad * 1.9)
                y = int(cy + math.sin(a * 1.3) * rad * 0.5)
                step = 4 if i % 4 == 0 else 2
                surface.fill(RAMPS["azure"][step], (x, y, 2, 2))
        elif kind == "listen":
            # Genisleyen halkalar: dinlemek.
            for ring in range(4):
                phase = (self.time * 0.55 + ring * 0.25) % 1.0
                radius = int(8 + phase * 62)
                fade = int(200 * (1.0 - phase))
                if fade <= 8:
                    continue
                colour = RAMPS["azure"][3]
                points = max(16, radius * 3)
                for p in range(points):
                    ang = p * math.tau / points
                    px = int(cx + math.cos(ang) * radius)
                    py = int(cy + math.sin(ang) * radius * 0.55)
                    if 0 <= px < VIRTUAL_W and 0 <= py < VIRTUAL_H:
                        surface.set_at((px, py), colour)
        elif kind in ("deer", "deer_close"):
            image = self.deer_flipped
            scale = 1.0 if kind == "deer" else 1.5
            bob = math.sin(self.time * 1.2) * 2.0
            w = int(image.get_width() * scale)
            h = int(image.get_height() * scale)
            shown = pygame.transform.scale(image, (w, h)) if scale != 1.0 else image
            shown = shown.copy()
            shown.set_alpha(min(alpha, 210))
            surface.blit(shown, (cx - w // 2, int(cy - h * 0.55 + bob)))
        elif kind == "call":
            # Batiya uzanan bir isik cizgisi.
            for i in range(70):
                t = i / 70.0
                x = int(VIRTUAL_W * 0.5 - t * VIRTUAL_W * 0.45)
                y = int(cy + math.sin(t * 6.0 + self.time * 2.0) * 5)
                step = 4 if (i + int(self.time * 20)) % 6 < 2 else 2
                surface.fill(RAMPS["ember"][step], (x, y, 2, 2))

    def _draw_text(self, surface: pygame.Surface) -> None:
        lines = self.panel.visible_lines()
        base_y = 168
        for i, line in enumerate(lines):
            if not line:
                continue
            y = base_y + i * 16
            # Yanki: metnin solmus kopyalari geride kalir. Anlatinin fikrini
            # okumadan once gosteren detay bu.
            gfx_text.draw_text(surface, line, VIRTUAL_W // 2 + 2, y + 1,
                               color=RAMPS["azure"][1], align="center",
                               alpha=90)
            gfx_text.draw_text(surface, line, VIRTUAL_W // 2 + 1, y,
                               color=RAMPS["violet"][2], align="center",
                               alpha=130)
            gfx_text.draw_text(surface, line, VIRTUAL_W // 2, y,
                               color=UI_TEXT, align="center")

        # Yazan satirin ucunda imlec
        if not self.panel.done_typing and int(self.time * 3) % 2 == 0:
            idx = self.panel.line_index
            if idx < len(self.panel.lines):
                shown = self.panel.lines[idx][:int(self.panel.revealed)]
                width = gfx_text.text_width(shown)
                gfx_text.draw_text(surface, "_", VIRTUAL_W // 2 + width // 2 + 3,
                                   base_y + idx * 16, color=UI_TEXT_HILITE)

    def _draw_footer(self, surface: pygame.Surface) -> None:
        hint = ("[Enter] devam    [Esc] atla" if self.panel.done_typing
                else "[Enter] hizlandir    [Esc] atla")
        gfx_text.draw_text(surface, hint, VIRTUAL_W // 2, VIRTUAL_H - 18,
                           color=UI_TEXT_DIM, align="center")

        # Ilerleme noktalari
        total = len(PANELS)
        start = VIRTUAL_W // 2 - (total * 6) // 2
        for i in range(total):
            colour = UI_TEXT_HILITE if i <= self.panel_index else RAMPS["ink"][3]
            surface.fill(colour, (start + i * 6, VIRTUAL_H - 30, 3, 2))


class _StaticCamera:
    """Prologda dunya yok; parcaciklar dogrudan ekran uzayinda cizilir."""

    offset = (0, 0)

    @property
    def view_rect(self) -> pygame.Rect:
        return pygame.Rect(0, 0, VIRTUAL_W, VIRTUAL_H)
