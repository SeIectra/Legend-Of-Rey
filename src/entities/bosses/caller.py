"""BOSS 4 - "Cagiran". Bolum 18, oyunun sonu.

`docs/yapi.md` B18: *"Yaratik, Yanki'yi kullanarak **Cemo'nun sesiyle**
konusur. Rey sesi susturmayi secer - sessizlikte, yardimsiz savasir."*
`docs/gdd.md` 1: *"...o sesler ona yardim ederken, aslinda onu
cagiriyordur."*

## Tez iki satirda

    Caller.undying      Yanki acikken OLMUYOR
    Caller._do_call()   ve Cemo'nun sesiyle cagiriyor

On sekiz bolumdur Yanki oyuncunun araciydi: gorus, hasar, ipucu. B14
onun bir cagri oldugunu soyledi. Burada bu bir **kurala** donuyor -
oyuncunun kendi araci dusmani ayakta tutuyor. Cani bitiyor, diz
cokuyor, sonra kalkiyor.

Kazanmanin tek yolu sesi susturmak (`src/systems/silence.py`), ve
susturmak gorusu de hasari da goturuyor. Belgenin "yardimsiz" kelimesi
boylece bir anlatim degil bir **oynanis**.

B14'te Kaynak *"olmuyor, dusuyor"* diye yazilmisti ve bu onun geri
gelecegi anlamina geliyordu. Iste geldi - ama bu sefer olebilir, tek
sart var.

## Cemo'nun sesi bir HAMLE

`call` ekrana bir **yem** koyuyor: Yanki'nin gosterdigi, Cemo'ya
benzeyen bir sekil. Yaklasan oyuncu hasar aliyor. Yem yalnizca Yanki
acikken var - sustuktan sonra `call` bos donuyor ve bu goruluyor:
yaratik cagirmaya devam ediyor ama artik kimse duymuyor.

Bu, oyunun ilk saatinden beri kurulan sorunun cevabi: sesler yardim
mi ediyordu, cagiriyor muydu? Ikisi de.

## Hamle siralari sabit

`docs/derinlestirme.md` 4.2: rastgele bir boss ogrenilemez. Uc faz, uc
sira, ve ucuncu faz **yalnizca sustuktan sonra** aciliyor - yani
oyuncunun ogrendigi sey once "nasil hayatta kalinir", sonra "nasil
kazanilir".
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.combat.hitbox import Hitbox, Team
from src.config import (
    CALLER_CALL_DAMAGE, CALLER_CALL_RANGE, CALLER_HEALTH, CALLER_LURE_FRAMES,
    CALLER_RISE_FRAMES, CALLER_SPEED, CALLER_UNDYING_FLOOR, SOURCE_CONTACT_RANGE,
    SOURCE_POISE, SOURCE_REACH_DAMAGE, SOURCE_REACH_LENGTH, SOURCE_WAIL_DAMAGE,
    SOURCE_WAIL_REACH, TILE_SIZE,
)
from src.entities.boss import Boss
from src.entities.enemy import EnemyState

# --- Hamle siralari - **sabit**, ogrenilebilir -------------------------------
#
#   faz 0  taniyorsun         - yalnizca fiziksel hamleler
#   faz 1  cagirmaya basliyor - "call" giriyor, Cemo'nun sesi
#   faz 2  SUSTUKTAN SONRA    - cagirma bos donuyor, kalan saf dovus
MOVES = {
    0: ("reach", "wail", "reach"),
    1: ("call", "wail", "reach", "call", "crush"),
    2: ("crush", "reach", "wail", "crush", "reach"),
}

TELL = {"wail": 28, "reach": 20, "call": 36, "crush": 32}
ACTIVE = {"wail": 8, "reach": 6, "call": 4, "crush": 8}
RECOVER = {"wail": 38, "reach": 26, "call": 34, "crush": 42}

HOVER_AMPLITUDE = 4.0
HOVER_SPEED = 0.038

# Yemin cizim olculeri - Cemo boyunda, kucuk bir figur.
LURE_WIDTH = 10
LURE_HEIGHT = 18


class Lure:
    """Cemo'ya benzeyen sekil. **Yalnizca Yanki acikken var.**

    Bir `Enemy` degil: dovusmuyor, vurulamiyor, yalnizca duruyor ve
    yaklasani yakiyor. Dusman yapmak onu bir hedefe cevirirdi -
    oysa anin butun acisi **vurulamayacak olmasi**: ekranda kardesin
    duruyor ve ona yaklasamiyorsun.
    """

    __slots__ = ("x", "y", "frames", "hit_cooldown")

    def __init__(self, x: float, y: float) -> None:
        self.x = float(x)
        self.y = float(y)
        self.frames = CALLER_LURE_FRAMES
        self.hit_cooldown = 0

    @property
    def alive(self) -> bool:
        return self.frames > 0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x) - LURE_WIDTH // 2,
                           int(self.y) - LURE_HEIGHT,
                           LURE_WIDTH, LURE_HEIGHT)

    def update(self) -> None:
        if self.frames > 0:
            self.frames -= 1
        if self.hit_cooldown > 0:
            self.hit_cooldown -= 1

    def draw(self, surface: pygame.Surface, offset, frame: int) -> None:
        """Cemo'nun siluetı - **titrek ve yari saydam.**

        Gercek olmadigi goruluyor ama yeterince benziyor. B14'un
        `Mimic`iyle ayni dil (`render_alpha`), bu sefer bir dusmanin
        degil bir **kardesin** uzerinde.
        """
        ox, oy = offset
        rect = self.rect.move(-ox, -oy)
        wobble = int(math.sin(frame * 0.19) * 1.5)
        rect.x += wobble
        fade = min(1.0, self.frames / 30.0)
        body = pygame.Surface(rect.size, pygame.SRCALPHA)
        body.fill((*palette.color("echo"), int(150 * fade)))
        # Kafa - kucuk bir figur oldugunu soyleyen tek ayrinti.
        body.fill((*palette.color("echo_bright"), int(190 * fade)),
                  (LURE_WIDTH // 2 - 3, 0, 6, 6))
        surface.blit(body, rect.topleft)


class Caller(Boss):
    """Cagiran - on sekiz bolumdur seslenen sey."""

    body_width = 30
    body_height = 52
    max_health = CALLER_HEALTH
    poise = SOURCE_POISE

    tell_frames = TELL["wail"]
    active_frames = ACTIVE["wail"]
    recover_frames = RECOVER["wail"]
    attack_damage = SOURCE_WAIL_DAMAGE
    attack_reach = SOURCE_WAIL_REACH
    attack_height = 38
    attack_knockback = 4.2
    move_speed = CALLER_SPEED
    contact_range = SOURCE_CONTACT_RANGE

    phases = (0.60, 0.28)
    sprite_name = "source"
    body_colour = "arcane"
    boss_name_key = "boss.caller"
    tell_sound = "echo_open"
    death_sound = "echo_close"

    # Kaynak gibi: gercegini Yanki gostermiyor. Ayni sey, buyumus hali.
    echo_visible = False

    def __init__(self, scene, x: float, y: float) -> None:
        super().__init__(scene, x, y)
        self.animator = Animator(self.sprite_name)
        self.sprite_foot_y = CHARACTERS[self.sprite_name].foot_y
        self.move_index = 0
        self.move = "reach"
        self.lures: list[Lure] = []
        self.rise_frames = 0
        self.rises = 0          # kac kez geri kalkti - sahne bunu okuyor
        self.body.gravity_scale = 0.0
        self.hover_base = self.body.feet[1]

    # --- Olmezlik ★ ---------------------------------------------------------
    @property
    def undying(self) -> bool:
        """Yanki acikken olmuyor - **bolumun tezi.**

        Sahnenin `silence.done`una bakiyor, `EchoState`e degil:
        oyuncunun kademesi bolum boyunca baska sebeplerle de dusebilir
        (`echo.weaken`), ve o dususler bir KARAR degil. Olmezligi
        kaldiran sey kademe degil, oyuncunun sesi birakmayi
        **secmesi**.
        """
        silence = getattr(self.scene, "silence", None)
        return silence is None or not silence.done

    @property
    def kneeling(self) -> bool:
        """Cani bitti ama olemedi - diz cokmus, kalkacak."""
        return self.rise_frames > 0

    def _kneel(self) -> None:
        """Olemedi - diz cokuyor. **Iki yol da buradan geciyor.**

        Ilk surumde `take_damage` ve `die()` ayri ayri yaziliyordu ve
        `die()` sahne kancasini cagirmayi unutuyordu. Sonuc: yaratik
        diz cokuyordu ama susturma **hic acilmiyordu** - yani bolum
        bitirilemiyordu. Uctan uca oynatilinca yakalandi.

        Gercek yol `die()`den geciyor: `Actor.take_damage` can sifira
        inince kendisi `die()` cagiriyor, yani ozel durum oraya
        yazilmali. Ayni ders B16'da `Companion._stand` icin yazilmisti;
        iki cikis yolu olan her seyde tek bir govde olmali.
        """
        self.health = max(self.health, CALLER_UNDYING_FLOOR)
        if self.rise_frames > 0:
            return
        self.rise_frames = CALLER_RISE_FRAMES
        self.rises += 1
        on_kneel = getattr(self.scene, "on_caller_kneel", None)
        if on_kneel:
            on_kneel(self)

    def take_damage(self, box, direction):
        result = super().take_damage(box, direction)
        if result.hit and self.undying:
            # Olum `super()` icinde `die()`dan gecti ve orada geri
            # cevrildi; burada yalnizca sonucu duzeltiyoruz ki cagiran
            # "oldurdum" sanmasin.
            result.killed = False
        return result

    def die(self) -> None:
        """Yanki acikken olum **geri cevriliyor.**

        Bolumun tezi: `docs/yapi.md` B18'in "sesi susturmayi secer"
        cumlesi burada bir kurala doniyor. Susturulmadikca yaratik
        oluyor gibi yapip kalkiyor.
        """
        if self.undying:
            self._kneel()
            return
        super().die()

    # --- Dongu --------------------------------------------------------------
    def update(self) -> None:
        if self.kneeling:
            self.rise_frames -= 1
            self.body.vx = 0.0
            self.frames += 1
            if self.rise_frames == 0:
                # Kalkarken canin bir kismi geri geliyor - yoksa aninda
                # tekrar diz cokerdi ve dovus bir dongu olurdu.
                self.health = max(1, self.max_health // 4)
                on_rose = getattr(self.scene, "on_caller_rise", None)
                if on_rose:
                    on_rose(self)
            self._hover()
            self._update_animation()
            self._update_lures()
            return

        super().update()
        self._hover()
        self._update_animation()
        self._update_lures()

    def _hover(self) -> None:
        self.body.vy = 0.0
        offset = math.sin(self.frames * HOVER_SPEED) * HOVER_AMPLITUDE
        self.body.set_feet(self.body.center_x, self.hover_base + offset)

    def _update_lures(self) -> None:
        """Yemler yalnizca **Yanki acikken** yasiyor.

        Sustuktan sonra hepsi aninda kayboluyor - ve bu goruluyor:
        yaratik cagirmaya devam ediyor ama artik kimse duymuyor.
        """
        if not self.undying:
            self.lures.clear()
            return
        for lure in self.lures:
            lure.update()
            self._lure_touch(lure)
        self.lures = [lure for lure in self.lures if lure.alive]

    def _lure_touch(self, lure: Lure) -> None:
        player = self.player
        if player is None or player.dead or lure.hit_cooldown > 0:
            return
        if not lure.rect.colliderect(player.body.rect):
            return
        lure.hit_cooldown = 30
        self.scene.hitboxes.spawn(Hitbox(
            rect=lure.rect.copy(), owner=self, targets=Team.PLAYER,
            damage=CALLER_CALL_DAMAGE, active_frames=2, knockback=2.0,
        ))

    def _update_animation(self) -> None:
        if self.dead:
            self.animator.play("death")
        elif self.kneeling:
            self.animator.play("hurt")
        elif self.state is EnemyState.STAGGER:
            self.animator.play("hurt")
        elif self.state in (EnemyState.TELL, EnemyState.ATTACK):
            self.animator.play("attack3" if self.move in ("wail", "call")
                               else "attack1")
        else:
            self.animator.play("idle")
        self.animator.update()

    # --- Hamleler -----------------------------------------------------------
    def _next_move(self) -> str:
        order = MOVES.get(min(self.phase, 2), MOVES[0])
        move = order[self.move_index % len(order)]
        self.move_index += 1
        return move

    def _begin_tell(self) -> None:
        self.move = self._next_move()
        self.tell_frames = TELL[self.move]
        self.active_frames = ACTIVE[self.move]
        self.recover_frames = RECOVER[self.move]
        super()._begin_tell()

    def on_phase_change(self, phase: int) -> None:
        super().on_phase_change(phase)
        self.move_index = 0
        on_phase = getattr(self.scene, "on_caller_phase", None)
        if on_phase:
            on_phase(self, phase)

    def _spawn_attack(self) -> None:
        if self.move == "call":
            self._do_call()
        elif self.move == "reach":
            self._do_reach()
        elif self.move == "crush":
            self._do_crush()
        else:
            self._do_wail()

    def _do_wail(self) -> None:
        """Radyal cigli - yakindaki her seye."""
        rect = pygame.Rect(0, 0, SOURCE_WAIL_REACH * 2, self.attack_height * 2)
        rect.center = (int(self.body.center_x), int(self.body.center_y))
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.PLAYER,
            damage=SOURCE_WAIL_DAMAGE, active_frames=ACTIVE["wail"],
            knockback=self.attack_knockback,
        ))

    def _do_reach(self) -> None:
        """Uzanan kol - tek yone, uzun."""
        width = SOURCE_REACH_LENGTH
        rect = pygame.Rect(0, 0, width, self.attack_height)
        if self.facing > 0:
            rect.midleft = (int(self.body.center_x), int(self.body.center_y))
        else:
            rect.midright = (int(self.body.center_x), int(self.body.center_y))
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.PLAYER,
            damage=SOURCE_REACH_DAMAGE, active_frames=ACTIVE["reach"],
            knockback=3.0,
        ))

    def _do_crush(self) -> None:
        """Yukaridan iniyor - genis ve agir."""
        rect = pygame.Rect(0, 0, TILE_SIZE * 5, TILE_SIZE * 3)
        rect.midtop = (int(self.body.center_x), int(self.body.center_y))
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.PLAYER,
            damage=SOURCE_WAIL_DAMAGE + 4, active_frames=ACTIVE["crush"],
            knockback=5.0,
        ))
        self.scene.particles.burst(self.body.center_x, self.body.feet[1],
                                   14, path="dust")

    def _do_call(self) -> None:
        """**Cemo'nun sesi.** Yanki susmussa bos donuyor.

        Yem oyuncunun **oteki tarafinda** cikiyor: cagri onu Cagiran'dan
        uzaga degil, kendinden uzaga cekiyor. Yaninda ciksaydi bir
        saldiri olurdu; uzakta cikinca bir **davet** oluyor.
        """
        player = self.player
        if player is None:
            return
        if not self.undying:
            # Cagiriyor ama kimse duymuyor. Sessiz bir hamle - ve
            # oyuncunun kazandigi seyin resmi.
            on_empty = getattr(self.scene, "on_caller_empty_call", None)
            if on_empty:
                on_empty(self)
            return
        away = 1 if player.body.center_x > self.body.center_x else -1
        x = player.body.center_x + away * CALLER_CALL_RANGE * 0.4
        self.lures.append(Lure(x, player.body.feet[1]))
        self.scene.game.play_sound("echo_answer_partial")
        on_call = getattr(self.scene, "on_caller_call", None)
        if on_call:
            on_call(self)

    # --- Cizim --------------------------------------------------------------
    def draw_extra(self, surface: pygame.Surface, offset) -> None:
        for lure in self.lures:
            lure.draw(surface, offset, self.frames)
        if not self.kneeling:
            return
        # Diz cokmusken etrafinda toplanan is - "olmedi, topariyor".
        ox, oy = offset
        cx = int(self.body.center_x) - ox
        cy = int(self.body.center_y) - oy
        for step in range(6):
            angle = self.frames * 0.08 + step * math.tau / 6
            radius = 16 + int(math.sin(self.frames * 0.1 + step) * 4)
            surface.fill(palette.color("echo_dark"),
                         (cx + int(math.cos(angle) * radius),
                          cy + int(math.sin(angle) * radius), 2, 2))
