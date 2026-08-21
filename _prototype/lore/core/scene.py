"""Sahne yigini ve gecisler.

Eski koddaki en buyuk yapisal hata, ayarlar menusunun kendi `while` dongusunu
acmasiydi: ana dongu duruyor, pencere kapanmiyor, ESC calismiyordu. Burada tek
bir dongu var; menuler yigina *binen* sahneler.

Yigin semantigi:
  * `push`  - ustune bindir (altaki sahne durur ama gorunur kalabilir: pause)
  * `pop`   - ustekini kaldir
  * `replace` - ustekini degistir (menu -> oyun)
  * `set_root` - yigini tamamen sifirla
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from lore.core.mathx import clamp

if TYPE_CHECKING:
    from lore.core.app import App


class Scene:
    """Tum sahnelerin temeli.

    `blocks_update` / `blocks_draw`: bu sahne altindakini durdurur/gizler mi?
    Pause menusu guncellemeyi durdurur ama cizimi durdurmaz - oyun arkada
    donmus halde gorunur.
    """

    blocks_update = True
    blocks_draw = True
    transparent_bg = False

    def __init__(self, app: "App") -> None:
        self.app = app
        self.manager: SceneManager = app.scenes
        self.alive = True

    # Yasam dongusu kancalari
    def on_enter(self, **kwargs) -> None: ...
    def on_exit(self) -> None: ...
    def on_pause(self) -> None: ...
    def on_resume(self) -> None: ...

    # Kare dongusu
    def handle_event(self, event: pygame.event.Event) -> None: ...
    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...


class Transition:
    """Iki sahne arasindaki perde.

    Iki asama: `out` (karartma, sahne degisimi burada olur) ve `in` (acilma).
    """

    def __init__(self, duration: float = 0.35, color: tuple[int, int, int] = (8, 6, 14)) -> None:
        self.duration = duration
        self.color = color
        self.timer = 0.0
        self.phase = "idle"             # idle | out | in
        self._pending = None
        self._surface: pygame.Surface | None = None

    @property
    def active(self) -> bool:
        return self.phase != "idle"

    def start(self, action) -> None:
        self._pending = action
        self.phase = "out"
        self.timer = 0.0

    def update(self, dt: float) -> None:
        if self.phase == "idle":
            return
        self.timer += dt
        if self.timer < self.duration * 0.5:
            return
        if self.phase == "out":
            if self._pending:
                self._pending()
                self._pending = None
            self.phase = "in"
            self.timer = 0.0
        elif self.timer >= self.duration * 0.5:
            self.phase = "idle"
            self.timer = 0.0

    def draw(self, surface: pygame.Surface) -> None:
        if self.phase == "idle":
            return
        half = self.duration * 0.5
        t = clamp(self.timer / half, 0.0, 1.0)
        alpha = int(255 * (t if self.phase == "out" else 1.0 - t))
        if alpha <= 0:
            return
        if self._surface is None or self._surface.get_size() != surface.get_size():
            self._surface = pygame.Surface(surface.get_size()).convert()
            self._surface.fill(self.color)
        self._surface.set_alpha(alpha)
        surface.blit(self._surface, (0, 0))


class SceneManager:
    def __init__(self, app: "App") -> None:
        self.app = app
        self.stack: list[Scene] = []
        self.transition = Transition()
        # Sahne degisiklikleri kare sonuna ertelenir: bir sahne kendi
        # update'i icinde yigini degistirirse liste altindan kaymaz.
        self._queue: list[tuple[str, object, dict]] = []

    # --- Sorgular -----------------------------------------------------------
    @property
    def current(self) -> Scene | None:
        return self.stack[-1] if self.stack else None

    def __bool__(self) -> bool:
        return bool(self.stack)

    def find(self, scene_type: type) -> Scene | None:
        for scene in reversed(self.stack):
            if isinstance(scene, scene_type):
                return scene
        return None

    # --- Kuyruga alinan islemler --------------------------------------------
    def push(self, scene_cls, transition: bool = False, **kwargs) -> None:
        self._enqueue("push", scene_cls, kwargs, transition)

    def pop(self, transition: bool = False) -> None:
        self._enqueue("pop", None, {}, transition)

    def replace(self, scene_cls, transition: bool = True, **kwargs) -> None:
        self._enqueue("replace", scene_cls, kwargs, transition)

    def set_root(self, scene_cls, transition: bool = True, **kwargs) -> None:
        self._enqueue("root", scene_cls, kwargs, transition)

    def _enqueue(self, op: str, scene_cls, kwargs: dict, transition: bool) -> None:
        action = lambda: self._queue.append((op, scene_cls, kwargs))  # noqa: E731
        if transition:
            self.transition.start(action)
        else:
            action()

    def _flush(self) -> None:
        while self._queue:
            op, scene_cls, kwargs = self._queue.pop(0)
            if op == "push":
                self._do_push(scene_cls, kwargs)
            elif op == "pop":
                self._do_pop()
            elif op == "replace":
                self._do_pop()
                self._do_push(scene_cls, kwargs)
            elif op == "root":
                while self.stack:
                    self._do_pop()
                self._do_push(scene_cls, kwargs)

    def _do_push(self, scene_cls, kwargs: dict) -> None:
        if self.stack:
            self.stack[-1].on_pause()
        scene = scene_cls(self.app)
        self.stack.append(scene)
        scene.on_enter(**kwargs)
        self.app.input.clear()          # Eski tus basisi yeni sahneye sizmasin

    def _do_pop(self) -> None:
        if not self.stack:
            return
        scene = self.stack.pop()
        scene.alive = False
        scene.on_exit()
        if self.stack:
            self.stack[-1].on_resume()
        self.app.input.clear()

    # --- Kare dongusu -------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if self.transition.active:
            return                      # Perde inikken girdi yutulur
        if self.stack:
            self.stack[-1].handle_event(event)

    def update(self, dt: float) -> None:
        self.transition.update(dt)
        self._flush()
        if not self.stack:
            return
        # Ustten asagi in; ilk `blocks_update` gorunce dur.
        start = len(self.stack) - 1
        while start > 0 and not self.stack[start].blocks_update:
            start -= 1
        for scene in self.stack[start:]:
            if scene.alive:
                scene.update(dt)
        self._flush()

    def draw(self, surface: pygame.Surface) -> None:
        if not self.stack:
            surface.fill((0, 0, 0))
            return
        start = len(self.stack) - 1
        while start > 0 and (self.stack[start].transparent_bg
                             or not self.stack[start].blocks_draw):
            start -= 1
        for scene in self.stack[start:]:
            scene.draw(surface)
        self.transition.draw(surface)

    def shutdown(self) -> None:
        while self.stack:
            self._do_pop()
