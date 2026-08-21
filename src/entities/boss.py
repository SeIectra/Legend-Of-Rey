"""Boss temel sinifi - faz gecisli, can barli.

`docs/gdd.md` 8: dort buyuk boss (B6, B13, B14, B18) + her bolumde
mini-boss. Mini-boss mevcut dusmanin buyutulmus hali ve bir ek hamle;
boss'un kendi arenasi, kendi animasyon seti, ezberlenecek tell'leri var.

Prototipte iyi calisan iki sey buraya tasindi:

**Faz esikleri.** Can yuzdesi bir esigin altina dusunce faz degisir. Boss
o an yeni bir hamle acar ya da ritmini degistirir. Ezberlenen sey artik
gecersiz - oyuncu **yeniden ogrenmek** zorunda kalir ve dovus uzunlugu
degil, degisimi sayesinde akilda kalir.

**Faz zirhi.** Gecis aninda kisa bir dokunulmazlik. Yoksa oyuncu combo'nun
ortasinda iki fazi birden gecer ve gecisi hic gormez - boss'un en pahali
ani bosa gider.

## Can bari **yalnizca** boss'ta

Siradan dusmanda bar yok (CLAUDE.md 7): durum sendeleme, renk ve hizla
okunur. Boss'ta bar var cunku dovus uzun ve oyuncunun ilerleme olcusune
ihtiyaci oluyor. Bar ayni zamanda faz esiklerini **gosteriyor**: cizgiler
nerede oldugunu bilirsen ne zaman degisecegini de bilirsin.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.config import INTERNAL_WIDTH
from src.entities.enemy import Enemy, EnemyState

# Faz gecisinde dokunulmazlik - gecisi gormeden gecmek yok.
PHASE_ARMOR_FRAMES = 34

BAR_WIDTH = 220
BAR_HEIGHT = 6
BAR_Y = 16


class Boss(Enemy):
    """Faz gecisli buyuk dusman."""

    # Can yuzdesi esikleri, **buyukten kucuge**. (0.6, 0.3) = iki gecis.
    phases: tuple[float, ...] = (0.5,)
    boss_name_key: str = "boss.unknown"

    def __init__(self, scene, x: float, y: float) -> None:
        super().__init__(scene, x, y)
        self.phase = 0
        self.phase_armor = 0

    # --- Hasar --------------------------------------------------------------
    def take_damage(self, box, direction):
        if self.phase_armor > 0:
            # Gecis sirasinda vurulmaz. Vurus **bosa gitmis** gibi
            # gorunmesin diye sahne yine de bir tepki verebilir.
            on_blocked = getattr(self.scene, "on_boss_armor", None)
            if on_blocked:
                on_blocked(self)
            from src.combat.hitbox import DamageResult
            return DamageResult(hit=False)

        result = super().take_damage(box, direction)
        if result.hit and not result.killed:
            self._check_phase()
        return result

    def _check_phase(self) -> None:
        ratio = self.health_ratio
        index = self.phase
        while index < len(self.phases) and ratio <= self.phases[index]:
            index += 1
        if index != self.phase:
            self.phase = index
            self.phase_armor = PHASE_ARMOR_FRAMES
            self._set_state(EnemyState.STAGGER)
            self.scene.tokens.force_release(self)
            self.on_phase_change(index)

    def on_phase_change(self, phase: int) -> None:
        """Faz degisti. Alt sinif yeni hamleyi burada acar."""
        on_change = getattr(self.scene, "on_boss_phase", None)
        if on_change:
            on_change(self, phase)

    # --- Dongu --------------------------------------------------------------
    def update(self) -> None:
        if self.phase_armor > 0:
            self.phase_armor -= 1
        super().update()

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset) -> None:
        from src.entities.enemy_render import draw_enemy
        draw_enemy(self, surface, offset)

    def draw_health_bar(self, surface: pygame.Surface) -> None:
        """Ekranin ustunde, sabit. Sahne cagirir - dusman kendi cizmez.

        Bar faz esiklerini de gosteriyor: oyuncu ne zaman degisecegini
        gorebilsin.
        """
        x = INTERNAL_WIDTH // 2 - BAR_WIDTH // 2
        rect = pygame.Rect(x, BAR_Y, BAR_WIDTH, BAR_HEIGHT)

        surface.fill(palette.color("void"), rect.inflate(4, 4))
        surface.fill(palette.color("ink"), rect)

        filled = int(BAR_WIDTH * max(0.0, self.health_ratio))
        if filled > 0:
            colour = (palette.color("danger_bright") if self.phase_armor > 0
                      else palette.color("blood_bright"))
            surface.fill(colour, (x, BAR_Y, filled, BAR_HEIGHT))

        # Faz cizgileri - esiklerin nerede oldugu gorunsun.
        for threshold in self.phases:
            mark = x + int(BAR_WIDTH * threshold)
            surface.fill(palette.color("bone"), (mark, BAR_Y - 1, 1,
                                                 BAR_HEIGHT + 2))

        pygame.draw.rect(surface, palette.outline(), rect, 1)

    def debug_lines(self) -> list[str]:
        return [f"boss faz {self.phase}/{len(self.phases)}  "
                f"zirh {self.phase_armor}  can {self.health}/{self.max_health}"]
