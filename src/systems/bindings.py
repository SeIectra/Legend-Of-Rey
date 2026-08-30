"""Tus yeniden atama - model katmani.

`CLAUDE.md` 10 bunu bastan zorunlu tutuyordu: *"Tam tus yeniden atama
(klavye + gamepad)."* Girdi katmani da bastan hazirdi - `InputManager`
`Action` ile calisiyor ve `apply_bindings()` zaten var. Eksik olan
yalnizca oyuncunun onu degistirebilecegi yerdi.

Arda 30.08.2026'da kol destegini bir ayara cevirirken *"Tuslari falan da
ayarlara getiririz"* dedi; sirasi geldi.

## Neden ayri dosya

`settings.py` "deger sec" isini yapiyor (`Option`, `Slider`). Tus atama
farkli bir sey: **catisma**, **geri alinamazlik** ve **kilitlenme riski**
var. O kurallari `settings.py`'ye karistirmak iki isi de bulandirirdi.

## Uc guvenlik kurali

1. **ESC atanamaz.** `Action.CANCEL` onu tutuyor ve CANCEL yeniden
   atanabilir DEGIL - menuden cikmanin her zaman calisan bir yolu
   olmali. ESC baska bir seye baglanabilseydi menude hem iptal eder hem
   o seyi yapardi.
2. **Son tus calinamaz.** Yeni tus baska bir aksiyonda kayitliysa oradan
   silinir - ama o aksiyonun tek tusuysa atama **reddedilir**. Yoksa
   oyuncu farkinda olmadan ziplamayi tamamen kaybedebilirdi.
3. **Hata ayiklama tuslari (F3/F4/F11/F12) ve menu tuslari (CONFIRM,
   CANCEL, NEXT_TAB) listede yok.** Oyunu oynamak icin gereken tuslar
   atanabilir; oyunu *yonetmek* icin gerekenler sabit.

## Atama tek tus birakir

Varsayilanlarda bir aksiyonun birden fazla tusu var (JUMP: Space/W/Yukari/Z).
Yeniden atayinca **yalnizca yeni tus** kaliyor. Sebep: "zipla artik K" diyen
oyuncu Space'in de calismaya devam etmesini beklemiyor, ve calisirsa
"atama tutmadi" saniyor. Varsayilanlara donmek alternatifleri geri getiriyor.
"""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from src.core.input import (
    DEFAULT_GAMEPAD, DEFAULT_KEYBOARD, GAMEPAD_LABELS, KEY_LABELS, Action,
)
from src.ui.i18n import t

# Kayitta bu anahtar altinda duruyor: {"JUMP": [32], ...}
SETTINGS_KEY = "bindings"
GAMEPAD_SETTINGS_KEY = "pad_bindings"

# Atanamayan tus. Gerekce modul basliginda (kural 1).
RESERVED_KEYS: frozenset[int] = frozenset({pygame.K_ESCAPE})


@dataclass(frozen=True)
class Binding:
    """Ayarlar ekranindaki tek bir tus satiri.

    `Option`/`Slider` ile ayni sozlesme: `label` cizim aninda, o anki
    dilde cozuluyor (dil degistirilebiliyor, metin import aninda
    pismemelidir).
    """

    action: Action
    label_key: str
    note_key: str = ""

    @property
    def key(self) -> str:
        """`Action` adi - kayitta bu dize duruyor."""
        return self.action.name

    @property
    def label(self) -> str:
        return t(self.label_key)

    @property
    def note(self) -> str:
        return t(self.note_key) if self.note_key else ""


@dataclass(frozen=True)
class ResetBindings:
    """"Varsayilanlara don" satiri. Bir tus degil, bir eylem."""

    label_key: str = "controls.reset"
    note_key: str = "controls.reset_note"

    @property
    def label(self) -> str:
        return t(self.label_key)

    @property
    def note(self) -> str:
        return t(self.note_key)


# Oynanis tuslari - sira ekranda gorunen sira. Yon tuslari once, sonra
# eylem, en sonda duraklat: oyuncunun elini ogrendigi sira.
REBINDABLE: tuple[Binding, ...] = (
    Binding(Action.LEFT, "controls.left"),
    Binding(Action.RIGHT, "controls.right"),
    Binding(Action.UP, "controls.up"),
    Binding(Action.DOWN, "controls.down"),
    Binding(Action.JUMP, "controls.jump"),
    Binding(Action.ATTACK, "controls.attack"),
    Binding(Action.DODGE, "controls.dodge"),
    Binding(Action.ECHO, "controls.echo"),
    Binding(Action.ECHO_ASK, "controls.echo_ask"),
    Binding(Action.INTERACT, "controls.interact"),
    Binding(Action.COMPANION_WAIT, "controls.companion_wait"),
    Binding(Action.PAUSE, "controls.pause"),
)

CONTROL_ENTRIES: tuple = REBINDABLE + (ResetBindings(),)


# --- Etiketler --------------------------------------------------------------
def key_label(code: int) -> str:
    """Tusun oyuncuya gosterilecek adi.

    `pygame.key.name()` "left shift" gibi seyler donduruyor; tabloda
    olanlar dil anahtarindan, olmayanlar buyuk harfe cevrilerek.
    """
    label_key = KEY_LABELS.get(code)
    if label_key:
        return t(label_key)
    from src.ui.text import tr_upper
    name = pygame.key.name(code)
    return tr_upper(name) if name else "?"


def pad_label(code: int) -> str:
    return GAMEPAD_LABELS.get(code, f"{code}")


# Satirda en fazla bu kadar tus yaziliyor. Varsayilanlarda dort tanesi
# olan var (JUMP: Bosluk/W/Yukari/Z) ve dordu birden sutuna sigmayip
# etiketin uzerine tasiyordu. Yeniden atanan tus zaten tek; bu sinir
# yalnizca varsayilanlari ilgilendiriyor.
MAX_SHOWN = 2


def labels_for(bindings: dict[Action, tuple[int, ...]], action: Action,
               gamepad: bool = False) -> str:
    """Aksiyonun tuslari, tek satirda. Bos ise bir tire."""
    codes = bindings.get(action, ())
    if not codes:
        return "—"
    render = pad_label if gamepad else key_label
    shown = " / ".join(render(code) for code in codes[:MAX_SHOWN])
    return shown + "…" if len(codes) > MAX_SHOWN else shown


# --- Okuma ------------------------------------------------------------------
def _defaults(gamepad: bool) -> dict[Action, tuple[int, ...]]:
    source = DEFAULT_GAMEPAD if gamepad else DEFAULT_KEYBOARD
    return {action: tuple(codes) for action, codes in source.items()}


def read(settings, gamepad: bool = False) -> dict[Action, tuple[int, ...]]:
    """Kayitli atamalar, varsayilanlarin uzerine bindirilmis."""
    result = _defaults(gamepad)
    stored = settings.get(GAMEPAD_SETTINGS_KEY if gamepad else SETTINGS_KEY)
    if not isinstance(stored, dict):
        return result
    for name, codes in stored.items():
        try:
            action = Action[name]
        except KeyError:
            continue            # Eski surumden kalan bilinmeyen aksiyon
        if isinstance(codes, (list, tuple)):
            result[action] = tuple(int(c) for c in codes)
    return result


def _write(settings, bindings: dict[Action, tuple[int, ...]],
           gamepad: bool) -> None:
    """**Yalnizca varsayilandan FARKLI olanlar** kayda yaziliyor.

    Tamamini yazmak da calisirdi ama ileride bir varsayilan degisirse
    (ornegin yeni bir alternatif tus eklenirse) eski kayitlar onu
    gormezdi - kullanici hic dokunmadigi bir tusu "ozellestirmis"
    sayilirdi.
    """
    defaults = _defaults(gamepad)
    changed = {action.name: list(codes)
               for action, codes in bindings.items()
               if tuple(codes) != defaults.get(action, ())}
    settings.set(GAMEPAD_SETTINGS_KEY if gamepad else SETTINGS_KEY, changed)


# --- Atama ------------------------------------------------------------------
def assign(settings, action: Action, code: int,
           gamepad: bool = False) -> str:
    """Tusu aksiyona baglar. Bos dize = basarili, aksi halde dil anahtari.

    Donen anahtar dogrudan ekranda gosteriliyor; cagiran tarafin hata
    metni uydurmasi gerekmiyor.
    """
    if not gamepad and code in RESERVED_KEYS:
        return "controls.err_reserved"

    bindings = read(settings, gamepad)
    if bindings.get(action, ()) == (code,):
        return ""                       # Zaten oyle - sessizce gec

    # Catisma: tus baska bir aksiyonda mi?
    owner = next((other for other, codes in bindings.items()
                  if other is not action and code in codes), None)
    if owner is not None:
        remaining = tuple(c for c in bindings[owner] if c != code)
        if not remaining:
            # Kural 2: son tusu calamayiz - o aksiyon oynanamaz hale gelir.
            return "controls.err_last_key"
        bindings[owner] = remaining

    bindings[action] = (code,)
    _write(settings, bindings, gamepad)
    return ""


def reset(settings) -> None:
    """Klavye ve kol atamalarinin ikisini birden varsayilana dondurur."""
    settings.set(SETTINGS_KEY, {})
    settings.set(GAMEPAD_SETTINGS_KEY, {})


def owner_of(settings, code: int, gamepad: bool = False) -> Action | None:
    """Bu tus su an kimde? Ekranda catismayi onceden gostermek icin."""
    for action, codes in read(settings, gamepad).items():
        if code in codes:
            return action
    return None
