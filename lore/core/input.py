"""Aksiyon tabanli girdi.

Oyun kodu asla pygame.K_z gormez; Action.ATTACK gorur. Boylece klavye, gamepad
ve yeniden tus atama tek bir yerde cozulur.

Iki ozellik oyunun "his" kalitesini dogrudan belirler:
  * Buffer: Zipla tusuna yere inmeden birkac kare once basildiysa, inince zipla.
  * Edge algilama: pressed (bu kare basildi) ile held (basili tutuluyor) ayridir.
"""
from __future__ import annotations

from enum import Enum, auto

import pygame

# Zipla/saldiri gibi aksiyonlarin kac saniye "hatirlanacagi".
BUFFER_TIME = 0.13
STICK_DEADZONE = 0.35


class Action(Enum):
    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()
    JUMP = auto()
    ATTACK = auto()
    HEAVY = auto()
    DASH = auto()
    SPELL = auto()
    SPELL_NEXT = auto()
    INTERACT = auto()
    PAUSE = auto()
    MAP = auto()
    CONFIRM = auto()
    CANCEL = auto()
    # Hata ayiklama
    DEBUG_TOGGLE = auto()
    FULLSCREEN = auto()
    SCREENSHOT = auto()


DEFAULT_KEYBOARD: dict[Action, tuple[int, ...]] = {
    Action.LEFT: (pygame.K_LEFT, pygame.K_a),
    Action.RIGHT: (pygame.K_RIGHT, pygame.K_d),
    Action.UP: (pygame.K_UP, pygame.K_w),
    Action.DOWN: (pygame.K_DOWN, pygame.K_s),
    # Yukari/W de ziplatir. Bu tuslar oynanista baska hicbir sey yapmiyor
    # (menu gezinmesi Action.UP'i ayri okur, cakisma olmaz).
    # DIKKAT: merdiven tirmanma eklenirse (tilemap'te LADDER tile'i hazir)
    # yukari tusu orada gerekecek - o zaman merdivendeyken ziplamayi
    # bastirmak, yani baglantiyi kaldirmak degil, oncelik vermek gerekir.
    Action.JUMP: (pygame.K_SPACE, pygame.K_w, pygame.K_UP, pygame.K_z,
                  pygame.K_k),
    Action.ATTACK: (pygame.K_j, pygame.K_x),
    Action.HEAVY: (pygame.K_u, pygame.K_c),
    Action.DASH: (pygame.K_LSHIFT, pygame.K_l),
    Action.SPELL: (pygame.K_i, pygame.K_v),
    Action.SPELL_NEXT: (pygame.K_TAB,),
    Action.INTERACT: (pygame.K_e,),
    Action.PAUSE: (pygame.K_ESCAPE,),
    Action.MAP: (pygame.K_m,),
    Action.CONFIRM: (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e),
    Action.CANCEL: (pygame.K_ESCAPE, pygame.K_BACKSPACE),
    Action.DEBUG_TOGGLE: (pygame.K_F3,),
    Action.FULLSCREEN: (pygame.K_F11,),
    Action.SCREENSHOT: (pygame.K_F12,),
}

DEFAULT_GAMEPAD: dict[Action, tuple[int, ...]] = {
    Action.JUMP: (0,),          # A
    Action.ATTACK: (2,),        # X
    Action.HEAVY: (3,),         # Y
    Action.DASH: (1, 5),        # B / RB
    Action.SPELL: (4,),         # LB
    Action.INTERACT: (0,),
    Action.PAUSE: (7,),         # Start
    Action.MAP: (6,),           # Back
    Action.CONFIRM: (0,),
    Action.CANCEL: (1,),
    Action.SPELL_NEXT: (9,),
}


# Oyuncuya gosterilecek tus adlari. pygame.key.name() "left shift" gibi
# seyler dondurur; arayuzde "Shift" daha okunur.
KEY_LABELS: dict[int, str] = {
    pygame.K_LSHIFT: "Shift", pygame.K_RSHIFT: "Shift",
    pygame.K_LCTRL: "Ctrl", pygame.K_RCTRL: "Ctrl",
    pygame.K_LALT: "Alt", pygame.K_RALT: "Alt",
    pygame.K_SPACE: "Space", pygame.K_RETURN: "Enter",
    pygame.K_ESCAPE: "Esc", pygame.K_TAB: "Tab",
    pygame.K_BACKSPACE: "Backspace",
    pygame.K_LEFT: "Sol", pygame.K_RIGHT: "Sag",
    pygame.K_UP: "Yukari", pygame.K_DOWN: "Asagi",
}

GAMEPAD_LABELS: dict[int, str] = {
    0: "A", 1: "B", 2: "X", 3: "Y",
    4: "LB", 5: "RB", 6: "Back", 7: "Start",
}


class InputManager:
    def __init__(self, config=None) -> None:
        self.config = config
        # Tuple, set degil: ilk eleman "birincil" tus sayilir ve arayuzde
        # oyuncuya o gosterilir. Kume sirayi kaybederdi.
        self.keyboard = {a: tuple(keys) for a, keys in DEFAULT_KEYBOARD.items()}
        self.gamepad = {a: tuple(btns) for a, btns in DEFAULT_GAMEPAD.items()}
        self._apply_custom_bindings()

        self._held: set[Action] = set()
        self._pressed: set[Action] = set()
        self._released: set[Action] = set()
        self._buffer: dict[Action, float] = {}

        self.axis_x = 0.0
        self.axis_y = 0.0
        self.last_device = "keyboard"

        self.joysticks: list[pygame.joystick.Joystick] = []
        self._init_joysticks()

    # --- Kurulum ------------------------------------------------------------
    def _apply_custom_bindings(self) -> None:
        if not self.config:
            return
        custom = self.config.get("bindings") or {}
        for name, keys in custom.items():
            try:
                action = Action[name]
            except KeyError:
                continue                # Eski surumden kalan bilinmeyen aksiyon
            self.keyboard[action] = tuple(keys)

    def _init_joysticks(self) -> None:
        if not pygame.joystick.get_init():
            pygame.joystick.init()
        self.joysticks = []
        for i in range(pygame.joystick.get_count()):
            try:
                js = pygame.joystick.Joystick(i)
                js.init()
                self.joysticks.append(js)
            except pygame.error:
                pass

    def rebind(self, action: Action, keys: tuple[int, ...]) -> None:
        self.keyboard[action] = tuple(keys)
        if self.config:
            bindings = dict(self.config.get("bindings") or {})
            bindings[action.name] = list(keys)
            self.config.set("bindings", bindings)

    def binding_label(self, action: Action) -> str:
        """Aksiyonun birincil tusunun okunabilir adi.

        Arayuz mesajlarinda kullanilir: "Atilma ogrenildi!  [Shift]".
        Bir yetenegi acip tusunu soylememek, oyuncuyu menuye bakmaya zorlar.
        Son kullanilan aygita gore klavye ya da kol etiketi doner.
        """
        if self.last_device == "gamepad":
            buttons = self.gamepad.get(action)
            if buttons:
                return GAMEPAD_LABELS.get(buttons[0], f"Dugme {buttons[0]}")
        keys = self.keyboard.get(action)
        if not keys:
            return "?"
        key = keys[0]
        if key in KEY_LABELS:
            return KEY_LABELS[key]
        try:
            return pygame.key.name(key).upper()
        except pygame.error:
            return "?"

    # --- Kare dongusu -------------------------------------------------------
    def begin_frame(self, dt: float) -> None:
        """Her karenin basinda cagrilir: edge kumelerini ve buffer'i tazeler."""
        self._pressed.clear()
        self._released.clear()
        for action in list(self._buffer):
            self._buffer[action] -= dt
            if self._buffer[action] <= 0.0:
                del self._buffer[action]

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            self.last_device = "keyboard"
            for action, keys in self.keyboard.items():
                if event.key in keys:
                    self._activate(action)
        elif event.type == pygame.KEYUP:
            for action, keys in self.keyboard.items():
                if event.key in keys:
                    self._deactivate(action)
        elif event.type == pygame.JOYBUTTONDOWN:
            self.last_device = "gamepad"
            for action, btns in self.gamepad.items():
                if event.button in btns:
                    self._activate(action)
        elif event.type == pygame.JOYBUTTONUP:
            for action, btns in self.gamepad.items():
                if event.button in btns:
                    self._deactivate(action)
        elif event.type == pygame.JOYHATMOTION:
            self.last_device = "gamepad"
            hx, hy = event.value
            self._set_digital(Action.LEFT, hx < 0)
            self._set_digital(Action.RIGHT, hx > 0)
            self._set_digital(Action.UP, hy > 0)
            self._set_digital(Action.DOWN, hy < 0)
        elif event.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
            self._init_joysticks()

    def _activate(self, action: Action) -> None:
        if action not in self._held:
            self._pressed.add(action)
            self._buffer[action] = BUFFER_TIME
        self._held.add(action)

    def _deactivate(self, action: Action) -> None:
        if action in self._held:
            self._released.add(action)
        self._held.discard(action)

    def _set_digital(self, action: Action, active: bool) -> None:
        if active:
            self._activate(action)
        else:
            self._deactivate(action)

    def end_frame(self) -> None:
        """Analog cubugu okur ve yatay/dikey ekseni tek bir sayiya indirir."""
        ax = ay = 0.0
        for js in self.joysticks:
            try:
                jx, jy = js.get_axis(0), js.get_axis(1)
            except (pygame.error, IndexError):
                continue
            if abs(jx) > STICK_DEADZONE:
                ax = jx
                self.last_device = "gamepad"
            if abs(jy) > STICK_DEADZONE:
                ay = jy
                self.last_device = "gamepad"

        # Cubuk bostaysa tuslara dus. Ters yonler birbirini gotursun ki iki
        # tusa ayni anda basinca karakter titremesin.
        if ax == 0.0:
            ax = float(self.held(Action.RIGHT)) - float(self.held(Action.LEFT))
        if ay == 0.0:
            ay = float(self.held(Action.DOWN)) - float(self.held(Action.UP))
        self.axis_x, self.axis_y = ax, ay

    # --- Sorgular -----------------------------------------------------------
    def held(self, action: Action) -> bool:
        return action in self._held

    def pressed(self, action: Action) -> bool:
        return action in self._pressed

    def released(self, action: Action) -> bool:
        return action in self._released

    def buffered(self, action: Action) -> bool:
        """Aksiyon son BUFFER_TIME icinde istendi mi?"""
        return action in self._buffer

    def consume(self, action: Action) -> bool:
        """Buffer'i tuketerek okur. Ziplama gibi tek seferlik aksiyonlar icin.

        Tuketmezsen tek tus basisi birkac kare boyunca tekrar tetiklenir.
        """
        if action in self._buffer:
            del self._buffer[action]
            return True
        return False

    def clear(self) -> None:
        """Sahne gecislerinde cagrilir: eski girdi yeni sahneye sizmasin."""
        self._held.clear()
        self._pressed.clear()
        self._released.clear()
        self._buffer.clear()
        self.axis_x = self.axis_y = 0.0

    def rumble(self, low: float, high: float, ms: int) -> None:
        if self.config and not self.config.get("rumble"):
            return
        for js in self.joysticks:
            try:
                js.rumble(low, high, ms)
            except (pygame.error, AttributeError):
                pass
