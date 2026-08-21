"""Sahne yigini ve gecisler.

Yigin semantigi:
    push      - ustune bindir (altaki durur ama gorunur kalabilir: duraklatma)
    pop       - ustekini kaldir
    replace   - ustekini degistir
    set_root  - yigini tamamen sifirla

**Tek dongu kurali:** Hicbir sahne kendi `while` dongusunu acmaz. Menuler
yigina *binen* sahnelerdir. Ayri dongu acmak Esc'i, pencere kapatmayi ve
muzigi bozar - prototipte tam olarak bu olmustu.

Gecis sureleri kare cinsindendir ve `MENU_TRANSITION_MAX_FRAMES` ile sinirlidir:
menu hizli hissetmeli (CLAUDE.md 9).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pygame

from src.art import palette
from src.config import MENU_TRANSITION_MAX_FRAMES

if TYPE_CHECKING:
    from src.core.game import Game


class Scene:
    """Tum sahnelerin temeli.

    `blocks_update` / `blocks_draw`: bu sahne altindakini durdurur/gizler mi?
    Duraklatma menusu guncellemeyi durdurur ama cizimi durdurmaz - oyun
    arkada donmus halde gorunur.
    """

    blocks_update: bool = True
    blocks_draw: bool = True

    def __init__(self, game: "Game") -> None:
        self.game = game
        self.scenes: "SceneManager" = game.scenes
        self.alive = True

    # Yasam dongusu kancalari
    def on_enter(self, **kwargs: object) -> None: ...
    def on_exit(self) -> None: ...
    def on_pause(self) -> None: ...
    def on_resume(self) -> None: ...

    # Kare dongusu - `frame` birimi kare, saniye degil
    def handle_event(self, event: pygame.event.Event) -> None: ...
    def update(self) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...


class Transition:
    """Iki sahne arasindaki perde. Yariya gelince sahne degisir."""

    def __init__(self, frames: int = MENU_TRANSITION_MAX_FRAMES) -> None:
        self.frames = frames
        self.elapsed = 0
        self.phase = "idle"          # idle | out | in
        self._pending: Callable[[], None] | None = None
        self._veil: pygame.Surface | None = None

    @property
    def active(self) -> bool:
        return self.phase != "idle"

    def start(self, action: Callable[[], None]) -> None:
        self._pending = action
        self.phase = "out"
        self.elapsed = 0

    def update(self) -> None:
        if self.phase == "idle":
            return
        self.elapsed += 1
        half = max(1, self.frames // 2)
        if self.elapsed < half:
            return
        if self.phase == "out":
            if self._pending is not None:
                self._pending()
                self._pending = None
            self.phase = "in"
            self.elapsed = 0
        else:
            self.phase = "idle"
            self.elapsed = 0

    def draw(self, surface: pygame.Surface) -> None:
        if self.phase == "idle":
            return
        half = max(1, self.frames // 2)
        ratio = min(1.0, self.elapsed / half)
        alpha = int(255 * (ratio if self.phase == "out" else 1.0 - ratio))
        if alpha <= 0:
            return
        if self._veil is None or self._veil.get_size() != surface.get_size():
            self._veil = pygame.Surface(surface.get_size()).convert()
            self._veil.fill(palette.color("void"))
        self._veil.set_alpha(alpha)
        surface.blit(self._veil, (0, 0))


class SceneManager:
    def __init__(self, game: "Game") -> None:
        self.game = game
        self.stack: list[Scene] = []
        self.transition = Transition()
        # Sahne degisiklikleri kare sonuna ertelenir: bir sahne kendi
        # update'i icinde yigini degistirirse liste altindan kaymaz.
        self._queue: list[tuple[str, type[Scene] | None, dict]] = []

    # --- Sorgular -----------------------------------------------------------
    @property
    def current(self) -> Scene | None:
        return self.stack[-1] if self.stack else None

    def find(self, scene_type: type) -> Scene | None:
        for scene in reversed(self.stack):
            if isinstance(scene, scene_type):
                return scene
        return None

    # --- Kuyruga alinan islemler --------------------------------------------
    def push(self, scene_cls: type[Scene], transition: bool = False,
             **kwargs: object) -> None:
        self._enqueue("push", scene_cls, kwargs, transition)

    def pop(self, transition: bool = False) -> None:
        self._enqueue("pop", None, {}, transition)

    def replace(self, scene_cls: type[Scene], transition: bool = True,
                **kwargs: object) -> None:
        self._enqueue("replace", scene_cls, kwargs, transition)

    def set_root(self, scene_cls: type[Scene], transition: bool = True,
                 **kwargs: object) -> None:
        self._enqueue("root", scene_cls, kwargs, transition)

    def _enqueue(self, op: str, scene_cls: type[Scene] | None, kwargs: dict,
                 transition: bool) -> None:
        def action() -> None:
            self._queue.append((op, scene_cls, kwargs))

        if transition:
            self.transition.start(action)
        else:
            action()

    def _flush(self) -> None:
        while self._queue:
            op, scene_cls, kwargs = self._queue.pop(0)
            if op == "push" and scene_cls is not None:
                self._do_push(scene_cls, kwargs)
            elif op == "pop":
                self._do_pop()
            elif op == "replace" and scene_cls is not None:
                self._do_pop()
                self._do_push(scene_cls, kwargs)
            elif op == "root" and scene_cls is not None:
                while self.stack:
                    self._do_pop()
                self._do_push(scene_cls, kwargs)

    def _do_push(self, scene_cls: type[Scene], kwargs: dict) -> None:
        if self.stack:
            self.stack[-1].on_pause()
        scene = scene_cls(self.game)
        self.stack.append(scene)
        scene.on_enter(**kwargs)
        self.game.input.clear()      # Eski tus basisi yeni sahneye sizmasin

    def _do_pop(self) -> None:
        if not self.stack:
            return
        scene = self.stack.pop()
        scene.alive = False
        scene.on_exit()
        if self.stack:
            self.stack[-1].on_resume()
        self.game.input.clear()

    # --- Kare dongusu -------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if self.transition.active:
            return                   # Perde inikken girdi yutulur
        if self.stack:
            self.stack[-1].handle_event(event)

    def update(self) -> None:
        self.transition.update()
        self._flush()
        if not self.stack:
            return
        start = len(self.stack) - 1
        while start > 0 and not self.stack[start].blocks_update:
            start -= 1
        for scene in self.stack[start:]:
            if scene.alive:
                scene.update()
        self._flush()

    def draw(self, surface: pygame.Surface) -> None:
        if not self.stack:
            surface.fill(palette.color("void"))
            return
        start = len(self.stack) - 1
        while start > 0 and not self.stack[start].blocks_draw:
            start -= 1
        for scene in self.stack[start:]:
            scene.draw(surface)
        self.transition.draw(surface)

    def shutdown(self) -> None:
        while self.stack:
            self._do_pop()
