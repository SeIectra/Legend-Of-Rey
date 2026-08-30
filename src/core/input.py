"""Aksiyon tabanli girdi ve 8 karelik tampon.

Oyun kodu asla `pygame.K_j` gormez; `Action.ATTACK` gorur. Klavye, gamepad ve
fare tek noktada cozulur; tus yeniden atama bedava gelir (CLAUDE.md 10).

**Girdi tamponu (CLAUDE.md 8):** Saldiri ya da zipla tusu uygun andan
`INPUT_BUFFER_FRAMES` kare *once* basilirsa hafizada tutulur ve an gelince
calisir. Oyuncuya soylenmez; oyun sadece "adil" hisseder.

`pressed` (bu kare basildi) ile `held` (basili tutuluyor) ayridir - zincir
penceresi ve degisken ziplama yuksekligi bu ayrima dayanir.
"""
from __future__ import annotations

from enum import Enum, auto

import pygame

from src.config import INPUT_BUFFER_FRAMES

STICK_DEADZONE = 0.35


class Action(Enum):
    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()
    JUMP = auto()
    ATTACK = auto()
    DODGE = auto()
    ECHO = auto()           # Yanki - basili tutulur
    ECHO_ASK = auto()       # Yanki'ya soru sor
    INTERACT = auto()
    # Yoldasa "burada bekle / pesimden gel" komutu. Arda (30.08.2026):
    # *"Bir tusa bastigimizda orada bekleyecegi bir komut ekleyelim."*
    # INTERACT'e binmiyor: o zaten plaka/vana/sandik icin kullaniliyor
    # ve yoldasin yaninda bir sandik varsa hangisinin olacagi belirsiz
    # olurdu.
    COMPANION_WAIT = auto()
    PAUSE = auto()
    CONFIRM = auto()
    CANCEL = auto()
    NEXT_TAB = auto()       # Ayarlar ekrani - sekmeler arasi DOGRUDAN gecis
    # Hata ayiklama
    DEBUG_OVERLAY = auto()
    DEBUG_SILHOUETTE = auto()
    FULLSCREEN = auto()
    SCREENSHOT = auto()


DEFAULT_KEYBOARD: dict[Action, tuple[int, ...]] = {
    Action.LEFT: (pygame.K_LEFT, pygame.K_a),
    Action.RIGHT: (pygame.K_RIGHT, pygame.K_d),
    Action.UP: (pygame.K_UP, pygame.K_w),
    Action.DOWN: (pygame.K_DOWN, pygame.K_s),
    # Yukari/W de ziplatir. DIKKAT: merdiven tirmanma eklenirse yukari tusu
    # orada gerekecek - o zaman baglantiyi kaldirmak degil, merdivendeyken
    # tirmanmaya oncelik vermek gerekir.
    Action.JUMP: (pygame.K_SPACE, pygame.K_w, pygame.K_UP, pygame.K_z),
    Action.ATTACK: (pygame.K_j, pygame.K_x),
    Action.DODGE: (pygame.K_LSHIFT, pygame.K_l, pygame.K_c),
    Action.ECHO: (pygame.K_k, pygame.K_q),
    Action.ECHO_ASK: (pygame.K_f,),
    Action.INTERACT: (pygame.K_e,),
    Action.COMPANION_WAIT: (pygame.K_u,),
    Action.PAUSE: (pygame.K_ESCAPE,),
    Action.CONFIRM: (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e),
    Action.CANCEL: (pygame.K_ESCAPE, pygame.K_BACKSPACE),
    Action.NEXT_TAB: (pygame.K_TAB,),
    Action.DEBUG_OVERLAY: (pygame.K_F3,),
    Action.DEBUG_SILHOUETTE: (pygame.K_F4,),
    Action.FULLSCREEN: (pygame.K_F11,),
    Action.SCREENSHOT: (pygame.K_F12,),
}

DEFAULT_GAMEPAD: dict[Action, tuple[int, ...]] = {
    Action.JUMP: (0,),          # A
    Action.ATTACK: (2,),        # X
    Action.DODGE: (1, 5),       # B / RB
    Action.ECHO: (4,),          # LB
    Action.ECHO_ASK: (3,),      # Y
    Action.INTERACT: (0,),
    Action.COMPANION_WAIT: (6,),    # Back
    Action.PAUSE: (7,),         # Start
    Action.CONFIRM: (0,),
    Action.CANCEL: (1,),
    Action.NEXT_TAB: (5,),      # RB - ayarlar ekraninda sekme degistirir
}

# Oyuncuya gosterilecek tus adlari. `pygame.key.name()` "left shift" gibi
# seyler dondurur; arayuzde "Shift" daha okunur.
# Hepsi dil anahtari tutar - istisnasiz. Shift/Enter/Esc/Tab su an her dilde
# ayni yazilsa da tabloda duruyor: birini metin, digerini anahtar yapmak
# cozumleyicide "bu anahtar mi, metin mi?" tahmini gerektirirdi.
KEY_LABELS: dict[int, str] = {
    pygame.K_LSHIFT: "keys.shift", pygame.K_RSHIFT: "keys.shift",
    pygame.K_SPACE: "keys.space", pygame.K_RETURN: "keys.enter",
    pygame.K_ESCAPE: "keys.esc", pygame.K_TAB: "keys.tab",
    pygame.K_LEFT: "keys.left", pygame.K_RIGHT: "keys.right",
    pygame.K_UP: "keys.up", pygame.K_DOWN: "keys.down",
}

GAMEPAD_LABELS: dict[int, str] = {
    0: "A", 1: "B", 2: "X", 3: "Y", 4: "LB", 5: "RB", 6: "Back", 7: "Start",
}


class InputManager:
    def __init__(self, bindings: dict[str, list[int]] | None = None,
                 pad_bindings: dict[str, list[int]] | None = None) -> None:
        # Tuple, set degil: ilk eleman "birincil" tus sayilir ve arayuzde
        # oyuncuya o gosterilir.
        self.keyboard = {a: tuple(k) for a, k in DEFAULT_KEYBOARD.items()}
        self.gamepad = {a: tuple(b) for a, b in DEFAULT_GAMEPAD.items()}
        if bindings:
            self.apply_bindings(bindings)
        if pad_bindings:
            self.apply_bindings(pad_bindings, gamepad=True)

        self._held: set[Action] = set()
        self._pressed: set[Action] = set()
        self._released: set[Action] = set()
        self._buffer: dict[Action, int] = {}     # aksiyon -> kalan kare

        self.axis_x = 0.0
        self.axis_y = 0.0
        self.last_device = "keyboard"
        self.mouse_moved = False

        self.joysticks: list[pygame.joystick.Joystick] = []
        # Kol destegi **acilista kurulmuyor** - ayardan aciliyor
        # (`set_gamepad_enabled`). Gerekce orada yazili.
        self.gamepad_enabled = False

    # --- Kurulum ------------------------------------------------------------
    def apply_bindings(self, bindings: dict[str, list[int]],
                       gamepad: bool = False) -> None:
        """Atamalari uygular. **Once varsayilanlara doner, sonra bindirir.**

        Bir donem yalnizca uzerine yaziyordu ve iki sessiz hata veriyordu:

          * "varsayilanlara don" canli oyuna yansimiyordu (bos sozluk
            hicbir seyi geri almiyor, eski atama yerinde kaliyordu)
          * kayit yalnizca DEGISEN aksiyonlari tutuyor
            (`bindings._write`), yani bir tus varsayilanina donunce
            sozlukten dusuyor - ve dusen sey geri yuklenmiyordu

        Ikisi de ancak oyunu kapatip acinca duzeliyordu.
        """
        table = DEFAULT_GAMEPAD if gamepad else DEFAULT_KEYBOARD
        target = {action: tuple(codes) for action, codes in table.items()}
        for name, keys in bindings.items():
            try:
                action = Action[name]
            except KeyError:
                continue        # Eski surumden kalan bilinmeyen aksiyon
            target[action] = tuple(keys)
        if gamepad:
            self.gamepad = target
        else:
            self.keyboard = target

    def _init_joysticks(self) -> None:
        """Bagli kollari acar. Alt sistem hazir degilse **hicbir sey yapmaz**.

        `pygame.joystick.init()` burada CAGRILMIYOR - o cagri bu makinede
        40 saniye suruyor (bkz. `Game.__init__`). Acilis arka planda
        (`_begin_joystick_init`); burasi yalnizca acilmis bir alt sistemin
        cihazlarini topluyor.
        """
        if not pygame.joystick.get_init():
            return
        self.joysticks = []
        for index in range(pygame.joystick.get_count()):
            try:
                stick = pygame.joystick.Joystick(index)
                stick.init()
                self.joysticks.append(stick)
            except pygame.error:
                pass

    def set_gamepad_enabled(self, enabled: bool) -> None:
        """Kol destegini acar/kapatir. Ayar degisince cagriliyor.

        **Acmak BLOKLAR.** `pygame.joystick.init()` bu makinede 40.3
        saniye suruyor ve bunu kacinmanin yolu yok:

          * yedi SDL ayari denendi (HIDAPI, RAWINPUT, WGI, DIRECTINPUT,
            XINPUT, THREAD) - hicbiri sureyi degistirmedi,
          * arka plan is parcacigi da ise yaramadi: cagri **GIL'i
            birakmiyor**, 40 saniyede ana is parcacigi 1 tur donebildi.

        O yuzden cozum teknik degil **tasarimsal**: oyuncu istedigi zaman
        oduyor. Ayar varsayilan kapali; acan bir kez bekliyor ve o
        oturumda kolu calisiyor.

        Ayarlar ekrani bu cagridan ONCE "kol araniyor" yazisini ciziyor
        (`settings_scene`), yoksa donma bir hata gibi gorunurdu.
        """
        self.gamepad_enabled = bool(enabled)
        if not enabled:
            self.joysticks = []
            return
        if not pygame.joystick.get_init():
            try:
                pygame.joystick.init()
            except pygame.error:
                return
        self._init_joysticks()

    def rebind(self, action: Action, keys: tuple[int, ...]) -> None:
        self.keyboard[action] = tuple(keys)

    def binding_label(self, action: Action) -> str:
        """Aksiyonun birincil tusunun okunabilir adi.

        Bir yetenegi acip tusunu soylememek oyuncuyu menuye bakmaya zorlar;
        ad ile tus hep birlikte gider.
        """
        from src.ui.i18n import t      # gec import: cekirdek katmani arayuze
                                       # baglanmasin, yalnizca burada gerekli
        if self.last_device == "gamepad":
            buttons = self.gamepad.get(action)
            if buttons:
                label = GAMEPAD_LABELS.get(buttons[0])
                return label or t("keys.gamepad_button", number=buttons[0])
        keys = self.keyboard.get(action)
        if not keys:
            return t("keys.unbound")
        key = keys[0]
        if key in KEY_LABELS:
            return t(KEY_LABELS[key])
        try:
            return pygame.key.name(key).upper()
        except pygame.error:
            return t("keys.unbound")

    # --- Kare dongusu -------------------------------------------------------
    def begin_frame(self) -> None:
        """Her karenin basinda: edge kumelerini temizle, tamponu eskit."""
        self._pressed.clear()
        self._released.clear()
        self.mouse_moved = False
        for action in list(self._buffer):
            self._buffer[action] -= 1
            if self._buffer[action] <= 0:
                del self._buffer[action]

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            self.last_device = "keyboard"
            self._dispatch(self.keyboard, event.key, pressed=True)
        elif event.type == pygame.KEYUP:
            self._dispatch(self.keyboard, event.key, pressed=False)
        elif event.type == pygame.JOYBUTTONDOWN:
            self.last_device = "gamepad"
            self._dispatch(self.gamepad, event.button, pressed=True)
        elif event.type == pygame.JOYBUTTONUP:
            self._dispatch(self.gamepad, event.button, pressed=False)
        elif event.type == pygame.JOYHATMOTION:
            self.last_device = "gamepad"
            hat_x, hat_y = event.value
            self._set_digital(Action.LEFT, hat_x < 0)
            self._set_digital(Action.RIGHT, hat_x > 0)
            self._set_digital(Action.UP, hat_y > 0)
            self._set_digital(Action.DOWN, hat_y < 0)
        elif event.type == pygame.MOUSEMOTION:
            self.mouse_moved = True
            self.last_device = "mouse"
        elif event.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
            # Yalnizca destek acikken: kapaliyken alt sistem zaten
            # kurulmadigi icin bu olaylar hic gelmiyor, ama gelirse de
            # 40 saniyelik taramayi tetiklememeli.
            if self.gamepad_enabled:
                self._init_joysticks()

    def _dispatch(self, table: dict[Action, tuple[int, ...]], code: int,
                  pressed: bool) -> None:
        for action, codes in table.items():
            if code in codes:
                if pressed:
                    self._activate(action)
                else:
                    self._deactivate(action)

    def _activate(self, action: Action) -> None:
        if action not in self._held:
            self._pressed.add(action)
            self._buffer[action] = INPUT_BUFFER_FRAMES
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
        """Analog cubugu okur, yatay/dikey ekseni tek sayiya indirir."""
        axis_x = axis_y = 0.0
        for stick in self.joysticks:
            try:
                raw_x, raw_y = stick.get_axis(0), stick.get_axis(1)
            except (pygame.error, IndexError):
                continue
            if abs(raw_x) > STICK_DEADZONE:
                axis_x = raw_x
                self.last_device = "gamepad"
            if abs(raw_y) > STICK_DEADZONE:
                axis_y = raw_y
                self.last_device = "gamepad"

        # Cubuk bostaysa tuslara dus. Ters yonler birbirini gotursun ki iki
        # tusa ayni anda basinca karakter titremesin.
        if axis_x == 0.0:
            axis_x = float(self.held(Action.RIGHT)) - float(self.held(Action.LEFT))
        if axis_y == 0.0:
            axis_y = float(self.held(Action.DOWN)) - float(self.held(Action.UP))
        self.axis_x, self.axis_y = axis_x, axis_y

    # --- Sorgular -----------------------------------------------------------
    def held(self, action: Action) -> bool:
        return action in self._held

    def pressed(self, action: Action) -> bool:
        return action in self._pressed

    def released(self, action: Action) -> bool:
        return action in self._released

    def buffered(self, action: Action) -> bool:
        """Aksiyon son `INPUT_BUFFER_FRAMES` kare icinde istendi mi?"""
        return action in self._buffer

    def consume(self, action: Action) -> bool:
        """Tamponu tuketerek okur. Tuketmezsen tek tus basisi birkac kare
        boyunca tekrar tetiklenir."""
        if action in self._buffer:
            del self._buffer[action]
            return True
        return False

    def clear(self) -> None:
        self._held.clear()
        self._pressed.clear()
        self._released.clear()
        self._buffer.clear()
        self.axis_x = self.axis_y = 0.0

    def rumble(self, low: float, high: float, milliseconds: int) -> None:
        for stick in self.joysticks:
            try:
                stick.rumble(low, high, milliseconds)
            except (pygame.error, AttributeError):
                pass
