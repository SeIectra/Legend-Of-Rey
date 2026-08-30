"""Kaynak - BOSS 3, Bolum 14.

`docs/gdd.md` 8: *"3 | B14 | Yanki'nin kaynagi"*.
`docs/yapi.md` B14: *"Rey anlar: Yanki lanet degil, asagidaki seyin
sesi. Hep yardim ediyordu cunku onu cagiriyordu."*

## Uc boss, uc katmanin sinavi - ve bu ucuncusu

Curumus Olan (B6) Katman 1'in uc dusmanini geri getiriyordu, Zindanci
(B13) Katman 2'nin dordunu. Kaynak ayni isi Katman 3 icin yapiyor -
ama bir farkla: **onlar onun cocuklari.** Oteki iki boss katmanini
ozetliyordu; bu, katmanini DOGURUYOR.

    Faz 0  SESSIZ'in izi      Yanki onu gostermiyor
    Faz 1  YANKILAYAN'in izi  sahte suretler cikariyor
    Faz 2  BOLUNEN'in izi     gercekten boluniyor

## Tezin tek satiri

`echo_visible = False`, ve **sahte suretlerin `echo_visible = True`**.

Yani Yanki'yi acan oyuncu ekranda uc silüet goruyor ve ucu de yalan;
gercegini yalnizca **gozuyle** bulabiliyor. On uc bolumdur "duvarin
ardini goster" diye kullanilan arac, ilk kez oyuncuya karsi calisiyor.

Bolumun tezi bu iki satirda: **arac bozuk degil, SENIN DEGIL.**

## Ardo'da ayni dovus, baska kurgu

Ardo'nun Yankisi yok, Iz Surme'si var. Sahte suretler ona da
gorunuyor - cunku onlar gercekten oradalar, yalnizca bos. Onun
twist'i "sesler benim degil" degil, **"izler benim icin birakilmis"**.
Kodda tek istisna yazilmadi; degisen sey replikler.

## Yerde durmuyor

`hover` ile suzuluyor ve golgesi yok. Sprite bir insansi iskeletten
cikiyor (butun kadro oyle) ama yere basmayan bir sey **hemen** baska
bir tur olarak okunuyor. Bir sesin ayagi olmaz.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.combat.hitbox import Hitbox, Team, melee_rect
from src.config import (
    SOURCE_CONTACT_RANGE, SOURCE_CRUSH_DAMAGE, SOURCE_CRUSH_REACH,
    SOURCE_HEALTH, SOURCE_MIMIC_COUNT, SOURCE_MIMIC_HEALTH,
    SOURCE_MIMIC_LIFE, SOURCE_MIMIC_RANGE, SOURCE_POISE,
    SOURCE_REACH_DAMAGE, SOURCE_REACH_LENGTH, SOURCE_SPEED,
    SOURCE_SPLIT_COUNT, SOURCE_SPLIT_LIMIT, SOURCE_WAIL_DAMAGE,
    SOURCE_WAIL_REACH, TILE_SIZE,
)
from src.entities.boss import Boss
from src.entities.enemy import Enemy, EnemyState

# --- Hamle siralari - **sabit**, ogrenilebilir -------------------------------
# `docs/derinlestirme.md` 4.2: rastgele bir boss ogrenilemez.
MOVES = {
    0: ("wail", "reach", "wail"),
    1: ("mimic", "wail", "reach", "mimic"),
    2: ("split", "crush", "wail", "split"),
}

TELL = {"wail": 30, "reach": 22, "mimic": 26, "crush": 34, "split": 28}
ACTIVE = {"wail": 8, "reach": 6, "mimic": 2, "crush": 8, "split": 2}
RECOVER = {"wail": 40, "reach": 28, "mimic": 30, "crush": 44, "split": 34}

# Suzulme genligi (piksel) ve hizi.
HOVER_AMPLITUDE = 3.5
HOVER_SPEED = 0.045


class Mimic(Enemy):
    """Kaynak'in sahte sureti - **bos bir ses.**

    Uc ozelligi var ve ucu de bilerek:

      * `echo_visible = True` - Yanki onu GOSTERIYOR (gercegini
        gostermiyor). Bolumun tezi bu tersliktе.
      * Tek canli: bir vurusla dagiliyor. Ceza hasar degil **zaman**;
        oyuncu yanlis hedefe vurdugu icin gercek olani dovemiyor.
      * Hicbir saldirisi yok. Zarar veren bir yalan bir tuzak olurdu;
        zarar vermeyen bir yalan bir **soru**.
    """

    sprite_name = "source"
    max_health = SOURCE_MIMIC_HEALTH
    poise = 0
    move_speed = 0.22
    contact_range = 0.0          # asla saldirmaz
    tell_frames = 20             # kullanilmiyor ama alt sinir baglayici
    active_frames = 2
    recover_frames = 20
    damage = 0
    body_width = 22
    body_height = 40
    body_colour = "arcane"
    echo_visible = True          # ★ gercegi gizli, YALANI gorunur
    # **Gozle bakinca yari saydam.** Oyuncuya durust bir isaret
    # borcluyuz: Yanki yalan soyluyor ama oyun soylemiyor. Yeterince
    # dikkatli bakan gercegi bulabilmeli, yoksa bu bir bilmece degil
    # zar atmak olurdu.
    #
    # Ve terslik tam burada tamamlaniyor: Yanki'da bu suretler KATI
    # gorunuyor, gercek olan hic gorunmuyor. Yani arac ne kadar cok
    # kullanilirsa o kadar yaniltiyor.
    render_alpha = 0.62

    def __init__(self, scene, x: float, y: float) -> None:
        super().__init__(scene, x, y)
        self.animator = Animator(self.sprite_name)
        self.sprite_foot_y = CHARACTERS[self.sprite_name].foot_y
        self.life = SOURCE_MIMIC_LIFE
        self.body.gravity_scale = 0.0

    def _can_attack(self) -> bool:
        return False             # bos bir ses vurmaz

    def update(self) -> None:
        self.life -= 1
        if self.life <= 0 and not self.dead:
            # Kendiliginden de soluyor: oyuncu hepsini oldurmek
            # zorunda kalmamali, yoksa yalan bir angarya olur.
            self.health = 0
            self.die()
        super().update()
        self.body.vy = 0.0
        self.animator.play("idle")
        self.animator.update()

    def draw_extra(self, surface: pygame.Surface, offset) -> None:
        """Titresim - saydamligin ustune ikinci bir kanal.

        `CLAUDE.md` 10: bir sey asla yalnizca **tek** kanalla
        anlatilmaz. Saydamlik renk/parlaklik kanali; bu, hareket
        kanali. Karanlik bir odada ya da renk gormeyen bir oyuncuda
        biri otekini tasiyor.
        """
        if self.dead:
            return
        ox, oy = offset
        x = int(self.body.center_x) - ox
        y = int(self.body.top) - oy
        jitter = int(math.sin(self.frames * 0.9) * 3)
        colour = palette.color("echo_bright")
        surface.fill(colour, (x - 11 + jitter, y + 6, 4, 1))
        surface.fill(colour, (x + 8 - jitter, y + 18, 4, 1))
        surface.fill(colour, (x - 9 + jitter, y + 30, 4, 1))


class Source(Boss):
    """Kaynak - Katman 3'un atasi. Yanki onu gostermez."""

    body_width = 26
    body_height = 46
    max_health = SOURCE_HEALTH
    poise = SOURCE_POISE

    tell_frames = TELL["wail"]
    active_frames = ACTIVE["wail"]
    recover_frames = RECOVER["wail"]
    attack_damage = SOURCE_WAIL_DAMAGE
    attack_reach = SOURCE_WAIL_REACH
    attack_height = 34
    attack_knockback = 3.8
    move_speed = SOURCE_SPEED
    contact_range = SOURCE_CONTACT_RANGE

    phases = (0.66, 0.33)
    sprite_name = "source"
    body_colour = "arcane"
    boss_name_key = "boss.source"
    tell_sound = "echo_open"
    death_sound = "echo_close"

    # ★ **Yanki onu gostermiyor** - Sessiz'in dersi boss olcusunde, ve
    # bolumun tezinin yarisi. Oteki yarisi `Mimic.echo_visible = True`.
    echo_visible = False

    def __init__(self, scene, x: float, y: float) -> None:
        super().__init__(scene, x, y)
        self.animator = Animator(self.sprite_name)
        self.sprite_foot_y = CHARACTERS[self.sprite_name].foot_y
        self.move_index = 0
        self.move = "wail"
        self.split_count = 0
        self.mimics: list[Mimic] = []
        # Yerde durmuyor - gerekce modul basliginda.
        self.body.gravity_scale = 0.0
        self.hover_base = self.body.feet[1]

    # --- Suzulme -------------------------------------------------------------
    def update(self) -> None:
        super().update()
        self.body.vy = 0.0
        offset = math.sin(self.frames * HOVER_SPEED) * HOVER_AMPLITUDE
        self.body.set_feet(self.body.center_x, self.hover_base + offset)
        self.mimics = [m for m in self.mimics if not m.dead]
        self._update_animation()

    def _update_animation(self) -> None:
        if self.dead:
            self.animator.play("death")
        elif self.state is EnemyState.STAGGER:
            self.animator.play("hurt")
        elif self.state in (EnemyState.TELL, EnemyState.ATTACK):
            self.animator.play("attack3" if self.move in ("wail", "split")
                               else "attack1")
        else:
            self.animator.play("idle")
        self.animator.update()

    # --- Hamle secimi ---------------------------------------------------------
    def _next_move(self) -> str:
        order = MOVES.get(min(self.phase, 2), MOVES[0])
        move = order[self.move_index % len(order)]
        self.move_index += 1
        # **Bos tell yok** - yapilamayacak bir hamlenin tell'i oyuncuya
        # sistemi yanlis ogretir (ayni ders Zindanci'da yazildi).
        if move == "split" and self.split_count >= SOURCE_SPLIT_LIMIT:
            move = "crush"
        elif move == "mimic" and len(self.mimics) >= SOURCE_MIMIC_COUNT * 2:
            move = "wail"
        return move

    def _begin_tell(self) -> None:
        self.move = self._next_move()
        self.tell_frames = TELL[self.move]
        super()._begin_tell()

    def _begin_attack(self) -> None:
        self.active_frames = ACTIVE[self.move]
        self.recover_frames = RECOVER[self.move]
        super()._begin_attack()

    def on_phase_change(self, phase: int) -> None:
        super().on_phase_change(phase)
        self.move_index = 0

    # --- Hamleler -------------------------------------------------------------
    def _spawn_attack(self) -> None:
        handler = {
            "wail": self._do_wail, "reach": self._do_reach,
            "mimic": self._do_mimic, "crush": self._do_crush,
            "split": self._do_split,
        }.get(self.move)
        if handler is not None:
            handler()

    def _do_wail(self) -> None:
        """Feryat - yonsuz. **Uzaklasarak** gecilir, kacinmayla degil.

        Yonu olmayan bir saldiri kacinmanin yonunu ise yaramaz
        kiliyor; tek cozum menzil disina cikmak. Ayni ders Curumus
        Olan'in patlamasindaydi - boss'lar birbirine cevap veriyor.
        """
        reach = SOURCE_WAIL_REACH
        rect = pygame.Rect(int(self.body.center_x - reach),
                           int(self.body.center_y - reach),
                           reach * 2, reach * 2)
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.PLAYER,
            damage=SOURCE_WAIL_DAMAGE, active_frames=ACTIVE["wail"],
            knockback=4.4, knockback_up=1.4,
        ))
        self.scene.particles.burst(self.body.center_x, self.body.center_y, 22,
                                   path="echo", speed=(1.0, 3.0))
        self._notify("source_wail")

    def _do_reach(self) -> None:
        """Uzanma - uzun kol. Menzil uzun ama tell de uzun."""
        rect = melee_rect(self.body, self.facing, SOURCE_REACH_LENGTH, 20)
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.PLAYER,
            damage=SOURCE_REACH_DAMAGE, active_frames=ACTIVE["reach"],
            knockback=3.2,
        ))
        self._notify("source_reach")

    def _do_crush(self) -> None:
        rect = pygame.Rect(int(self.body.center_x - SOURCE_CRUSH_REACH),
                           int(self.body.center_y - 10),
                           SOURCE_CRUSH_REACH * 2, 40)
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.PLAYER,
            damage=SOURCE_CRUSH_DAMAGE, active_frames=ACTIVE["crush"],
            knockback=4.8, knockback_up=2.0,
        ))
        self._notify("source_crush")

    def _do_mimic(self) -> None:
        """Sahte suretler - **Yanki onlari gosteriyor.**

        Bolumun tezi burada calisiyor: oyuncu Yanki'yi aciyor, uc
        silüet goruyor, ve gercegini yalnizca gozuyle bulabiliyor.
        """
        for index in range(SOURCE_MIMIC_COUNT):
            side = -1 if index % 2 == 0 else 1
            x = self.body.center_x + side * SOURCE_MIMIC_RANGE
            spot = self.scene.free_spot_near(x, self.hover_base, self.body)
            mimic = Mimic(self.scene, spot[0], spot[1])
            mimic.aware = True
            self.scene.enemies.append(mimic)
            self.mimics.append(mimic)
            self.scene.particles.burst(spot[0], spot[1] - 20, 12,
                                       path="echo", speed=(0.4, 1.6))
        self.scene.game.play_sound("echo_reveal")
        self._notify("source_mimic")

    def _do_split(self) -> None:
        """Gercekten boluniyor - cagirdiklari **kendi cocuklari**.

        Yankilayan: *"sesini taklit eder, sahte ipucu verir."* Onlari
        buranin dogurdugu B14'ten sonra geriye donuk anlam kazaniyor -
        Katman 3'un tamami bu odada basliyor.
        """
        from src.entities.enemies.echoing import Echoing
        for index in range(SOURCE_SPLIT_COUNT):
            if self.split_count >= SOURCE_SPLIT_LIMIT:
                break
            side = -1 if index % 2 == 0 else 1
            x = self.body.center_x + side * TILE_SIZE * 3
            spot = self.scene.free_spot_near(x, self.hover_base, self.body)
            child = Echoing(self.scene, spot[0], spot[1])
            child.aware = True
            self.scene.enemies.append(child)
            self.split_count += 1
            self.scene.particles.burst(spot[0], spot[1] - 10, 14,
                                       path="violet", speed=(0.6, 2.2))
        self.scene.game.play_sound("rift_open")
        self._notify("source_split")

    def _notify(self, name: str) -> None:
        hook = getattr(self.scene, "on_boss_move", None)
        if hook:
            hook(self, name)

    # --- Cizim ---------------------------------------------------------------
    def draw_extra(self, surface: pygame.Surface, offset) -> None:
        """Golge yerine bir **halka**, ve feryat sirasinda genisliyor.

        Yerde durmayan bir seyin golgesi olmaz ama zeminle bir iliskisi
        olmali, yoksa "arka planda yuzuyor" gibi okunuyor. Halka onu
        odaya baglıyor.

        Feryatta buyumesi tell'in gorsel kanali: `CLAUDE.md` 7 her
        saldirinin 14 kare onceden okunmasini istiyor, ve bu boss'un
        hamleleri yonsuz - **yalnizca renk** yetmezdi.
        """
        if self.dead:
            return
        ox, oy = offset
        x = int(self.body.center_x) - ox
        y = int(self.hover_base) - oy
        pulse = 0.6 + 0.4 * math.sin(self.frames * 0.07)
        telling = self.state in (EnemyState.TELL, EnemyState.ATTACK)
        grow = self.tell_progress if self.state is EnemyState.TELL else 1.0
        width = int(18 + 26 * grow) if telling else 18
        base = palette.color("danger_bright" if telling else "echo_bright")
        colour = tuple(int(c * pulse) for c in base)
        surface.fill(colour, (x - width // 2, y - 1, width, 1))
        for step in range(3):
            alpha = tuple(int(c * (0.5 - step * 0.14)) for c in colour)
            surface.fill(alpha, (x - width // 2 - step * 3, y - 3 - step * 2,
                                 width + step * 6, 1))

    def debug_lines(self) -> list[str]:
        return super().debug_lines() + [
            f"hamle {self.move}  suret {len(self.mimics)}  "
            f"bolunme {self.split_count}"
        ]
