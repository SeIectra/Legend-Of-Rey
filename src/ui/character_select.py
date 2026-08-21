"""Karakter secim ekrani.

Gorsel dil (docs/menu-ui.md 4): secili karakter **buyuk, aydinlik,
animasyonlu**; digeri kucuk, karanlik, hareketsiz. Bu, "secmedigin kisi
hikayede olacak" fikrini gorsel olarak kurar.

Detay: Rey seciliyken arkada fisilti duyulur, Ardo seciliyken **tam
sessizlik** - oynanis farkini duyarak anlarsin. (Ses Gorev 10'da; dikis
`game.play_ui_sound` uzerinden hazir.)

Ilk oynayista kucuk bir not: "Ilk kez oynuyorsan Rey onerilir." Zorlamaz,
yonlendirir.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.art.animator import Animator
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.input import Action
from src.core.scene import Scene
from src.systems.save import SaveData, write_save
from src.ui import text
from src.ui.font_data import GLYPH_HEIGHT
from src.ui.widgets import panel

SELECTED_SCALE = 3
UNSELECTED_SCALE = 2
PORTRAIT_Y = 112
LEFT_X = INTERNAL_WIDTH // 2 - 92
RIGHT_X = INTERNAL_WIDTH // 2 + 92


class CharacterInfo:
    def __init__(self, key: str, name: str, tagline: str, traits: tuple[str, ...],
                 echo: str, health: int) -> None:
        self.key = key
        self.name = name
        self.tagline = tagline
        self.traits = traits
        self.echo = echo
        self.health = health


CHARACTERS = (
    CharacterInfo("rey", "REY", "\"Kafasının içinde sesler var.\"",
                  ("Hızlı", "Kırılgan"), "VAR", 80),
    CharacterInfo("ardo", "ARDO", "\"Sessizlikte savaşır.\"",
                  ("Ağır", "Dayanıklı"), "YOK", 120),
)


class CharacterSelectScene(Scene):
    def on_enter(self, **kwargs: object) -> None:
        self.index = 0
        self.frame = 0
        self.animators = {info.key: Animator(info.key) for info in CHARACTERS}
        for animator in self.animators.values():
            animator.play("idle")

    # --- Girdi --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._click()

    def _click(self) -> None:
        mx, my = pygame.mouse.get_pos()
        view = self.game.viewport
        if not view.collidepoint(mx, my) or self.game.scale <= 0:
            return
        vx = (mx - view.x) / self.game.scale
        chosen = 0 if vx < INTERNAL_WIDTH // 2 else 1
        if chosen == self.index:
            self._confirm()
        else:
            self._select(chosen)

    def _select(self, index: int) -> None:
        if index == self.index:
            return
        self.index = index
        self.game.play_ui_sound("tick")

    def update(self) -> None:
        self.frame += 1
        inp = self.game.input

        if inp.pressed(Action.LEFT):
            self._select(0)
        elif inp.pressed(Action.RIGHT):
            self._select(1)
        if inp.pressed(Action.CONFIRM):
            self._confirm()
        elif inp.pressed(Action.CANCEL):
            self.game.play_ui_sound("back")
            self.scenes.pop()

        # Yalnizca secili karakter animasyonlu - digeri durgun.
        self.animators[CHARACTERS[self.index].key].update()

    def _confirm(self) -> None:
        info = CHARACTERS[self.index]
        self.game.play_ui_sound("confirm")

        data = SaveData(character=info.key,
                        max_health=info.health, health=info.health)
        write_save(data)

        from src.scenes.combat_room import CombatRoomScene
        self.scenes.set_root(CombatRoomScene, character=info.key)

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(palette.color("abyss_dark"))
        text.draw(surface, text.tr_upper("Kimi oynayacaksın?"),
                  INTERNAL_WIDTH // 2, 34,
                  color=palette.role("ui_text"), align="center", tracking=2)

        for index, info in enumerate(CHARACTERS):
            self._draw_character(surface, index, info)

        self._draw_details(surface, CHARACTERS[self.index])
        self._draw_footer(surface)

    def _draw_character(self, surface: pygame.Surface, index: int,
                        info: CharacterInfo) -> None:
        selected = index == self.index
        centre_x = LEFT_X if index == 0 else RIGHT_X
        scale = SELECTED_SCALE if selected else UNSELECTED_SCALE

        image = self.animators[info.key].render(
            1 if index == 0 else -1,
            # Secili olmayan karanlikta kalir - siluete yakin.
            tint_colour=None if selected else palette.color("stone_darkest"),
        )
        if image is None:
            return
        big = pygame.transform.scale(
            image, (image.get_width() * scale, image.get_height() * scale))
        if not selected:
            big = big.copy()
            big.set_alpha(150)

        rect = big.get_rect()
        rect.midbottom = (centre_x, PORTRAIT_Y + 60)

        if selected:
            frame = rect.inflate(10, 8)
            panel(surface, frame, alpha=140)
        surface.blit(big, rect.topleft)

        colour = (palette.role("ui_text_bright") if selected
                  else palette.color("stone_dark"))
        text.draw(surface, info.name, centre_x, PORTRAIT_Y + 66,
                  color=colour, align="center", tracking=2,
                  outline=selected)

    def _draw_details(self, surface: pygame.Surface,
                      info: CharacterInfo) -> None:
        y = PORTRAIT_Y + 86
        text.draw(surface, info.tagline, INTERNAL_WIDTH // 2, y,
                  color=palette.role("ui_text"), align="center")
        y += GLYPH_HEIGHT + 5

        traits = " · ".join(info.traits)
        text.draw(surface, traits, INTERNAL_WIDTH // 2, y,
                  color=palette.role("ui_text_dim"), align="center")
        y += GLYPH_HEIGHT + 2

        echo_colour = (palette.color("echo_bright") if info.echo == "VAR"
                       else palette.color("stone_dark"))
        text.draw(surface, f"Yankı: {info.echo}", INTERNAL_WIDTH // 2, y,
                  color=echo_colour, align="center")

    def _draw_footer(self, surface: pygame.Surface) -> None:
        if self.index == 0:
            text.draw(surface, "İlk kez oynuyorsan Rey önerilir.",
                      INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 34,
                      color=palette.color("stone_dark"), align="center")
        text.draw(surface, "[◂ ▸] seç    [Enter] onayla    [Esc] geri",
                  INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 18,
                  color=palette.role("ui_text_dim"), align="center")

    def debug_lines(self) -> list[str]:
        return [f"seçili: {CHARACTERS[self.index].name}"]
