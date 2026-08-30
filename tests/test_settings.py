"""Ayarlar - ozellikle **oyun kolu** ayari.

Bu test bir olcume dayaniyor. Arda 30.08.2026'da oyunun acilmasinin cok
uzun surdugunu soyledi. Olctum:

    pygame.joystick.init()  ->  40.30 saniye, 0 kol buldu

Sebep oyun degil, bu makinedeki bir surucu/yazilim (NGENUITY / HyperX).
Yedi ayri SDL ipucu denendi, hicbiri ise yaramadi. Ayri bir is parcaciğina
almak da imkansiz: olctum, ana is parcacigi 40 saniyede **tek bir dongu
turu** attı - GIL birakilmiyor.

Cozum tasarimsal: kol destegi bir **ayar** ve varsayilani kapali. Kolu
olan oyuncu bir kez aciyor, kayda yaziliyor, bir daha ugrasmiyor. Kolu
olmayan (cogunluk) hicbir bedel odemiyor.

Bu testin korudugu sey: **varsayilan bir daha acilmasin.** Birisi
`Option("gamepad", ..., (True, False))` diye siralayi ters cevirse ya da
`Game.__init__` icinde kosulsuz `set_gamepad_enabled(True)` cagirsa
acilis yeniden kirk saniyeye cikar ve bunu kimse fark etmez - cunku
gelistirici makinesinde ayni surucu yok.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Ayarlar Arda'nin gercek dosyasindan degil, bos bir dizinden okunsun.
# Iki sebep: (1) test kullanicinin ayarlarini bozmamali - bu betigi
# yazarken tam olarak onu yaptim, olcum icin `gamepad` acik birakildi ve
# testin kendisi kirk saniye taradi; (2) "varsayilan kapali" iddiasi
# ancak varsayilanlardan baslanirsa sinanabilir.
_SANDBOX = tempfile.mkdtemp(prefix="lore_settings_test_")
os.environ["APPDATA"] = _SANDBOX
os.environ["XDG_DATA_HOME"] = _SANDBOX
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame  # noqa: E402

from src.core.game import Game  # noqa: E402
from src.core.input import DEFAULT_KEYBOARD, Action  # noqa: E402
from src.systems import bindings as binds  # noqa: E402
from src.systems.bindings import ResetBindings  # noqa: E402
from src.systems.settings import ALL_ENTRIES, TABS, Option  # noqa: E402
from src.ui.i18n import t  # noqa: E402
from src.ui.settings_scene import CONTROL_ROWS, SettingsScene  # noqa: E402

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"   {name}")
    else:
        failures.append(f"{name}  {detail}")
        print(f"!! {name}  {detail}")


def gamepad_option() -> Option | None:
    for entry in ALL_ENTRIES:
        if isinstance(entry, Option) and entry.key == "gamepad":
            return entry
    return None


def main() -> int:
    print("=== oyun kolu ayari ===")
    entry = gamepad_option()
    check("ayar var", entry is not None)
    if entry is None:
        return 1

    check("varsayilan KAPALI", entry.values[0] is False,
          f"ilk deger {entry.values[0]!r} - acilis 40 sn'ye cikar")
    check("iki degerli", len(entry.values) == 2, str(entry.values))

    game = Game()
    try:
        # --- Acilista taranmiyor mu? ---
        # Asil kanit bu: joystick alt sistemi hic acilmamis olmali.
        check("acilista joystick alt sistemi kapali",
              not pygame.joystick.get_init())
        check("acilista kol destegi kapali",
              game.input.gamepad_enabled is False)
        check("acilista kol listesi bos", game.input.joysticks == [])

        # --- Ayar degisince girdi katmanina ulasiyor mu? ---
        # Ayar ile girdi katmani arasindaki kablo. Kopuk olsa oyuncu
        # ayari acar, hicbir sey olmaz ve nedenini anlamaz.
        game.input.gamepad_enabled = False
        game._on_setting_changed("gamepad", True)
        check("ayar acilinca girdi katmani haberdar",
              game.input.gamepad_enabled is True)
        game._on_setting_changed("gamepad", False)
        check("ayar kapaninca kol listesi bosaltiliyor",
              game.input.gamepad_enabled is False
              and game.input.joysticks == [])

        # --- Uyari yazisi ---
        # `settings.cycle` blokli cagriyi ANINDA tetikliyor. Yazi ondan
        # once ekrana basilmazsa oyuncu kirk saniye donmus bir ekrana
        # bakar - Arda'nin tam ekran hatasinda tarif ettigi gorunum.
        check("tarama yazisi dil tablosunda",
              t("settings.gamepad_scanning") != "settings.gamepad_scanning")

        game.settings.set("gamepad", False)
        game.scenes.push(SettingsScene)
        game.scenes.update()
        scene = game.scenes.current
        assert scene is not None

        before = pygame.transform.average_color(game.canvas)
        scene._warn_if_slow(entry, +1)          # kapali -> acik
        after = pygame.transform.average_color(game.canvas)
        check("acarken ekrana yazi basiliyor", before != after)

        # Kapatirken bekleme yok, dolayisiyla yazi da olmamali.
        game.settings.set("gamepad", True)
        game.canvas.fill((0, 0, 0))
        quiet_before = pygame.transform.average_color(game.canvas)
        scene._warn_if_slow(entry, +1)          # acik -> kapali
        check("kapatirken yazi yok",
              pygame.transform.average_color(game.canvas) == quiet_before)
    finally:
        game.shutdown()

    test_bindings()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("Ayarlar saglam: acilis hizli, tuslar atanabiliyor.")
    return 0


def test_bindings() -> None:
    """Tus yeniden atama - `CLAUDE.md` 10'un zorunlu tuttugu ekran.

    Korunan kurallar (gerekceler `src/systems/bindings.py`'de):
      * ESC atanamaz - menuden cikis ona bagli
      * Baska bir aksiyonun SON tusu calinamaz
      * Atama canli girdi katmanina ANINDA gecer
      * Sifirlama da canli katmana geciyor (bir donem gecmiyordu)
    """
    print("\n=== tus yeniden atama ===")
    game = Game()
    try:
        game.scenes.push(SettingsScene)
        game.scenes._flush()
        scene = game.scenes.current
        assert scene is not None

        controls = next(i for i, (key, _) in enumerate(TABS)
                        if key == "settings.tab_controls")
        scene.tabs.index = controls
        scene.row = 0
        check("tus sekmesi var", scene.controls_tab)
        # Sayi sabit yazilmiyor: her yeni aksiyon (ornegin
        # `COMPANION_WAIT`) listeyi uzatiyor. Onemli olan **hepsinin
        # panele sigmasi** - kaydirma yok, gorunmeyen satir olmamali.
        check("butun satirlar iki sutuna sigiyor",
              len(scene.entries) <= CONTROL_ROWS * 2,
              f"{len(scene.entries)} satir / {CONTROL_ROWS * 2} yuva")

        # Iki sutun: ilk satir ile ikinci sutunun ilki ayni yukseklikte.
        first, second = scene._row_rect(0), scene._row_rect(CONTROL_ROWS)
        check("iki sutun yan yana",
              first.y == second.y and first.x < second.x,
              f"{first.topleft} / {second.topleft}")

        def row_for(action: Action) -> int:
            return next(i for i, e in enumerate(scene.entries)
                        if getattr(e, "action", None) is action)

        def press(key: int) -> None:
            scene._capture_event(pygame.event.Event(pygame.KEYDOWN, key=key))

        # --- Normal atama ---
        scene.row = row_for(Action.JUMP)
        scene._adjust(1)
        check("yakalama basliyor", scene.capturing is not None)
        press(pygame.K_k)
        table = binds.read(game.settings)
        check("tus atandi", table[Action.JUMP] == (pygame.K_k,),
              binds.labels_for(table, Action.JUMP))
        check("yakalama kapandi", scene.capturing is None)
        check("canli girdi katmani guncellendi",
              game.input.keyboard[Action.JUMP] == (pygame.K_k,))
        # K, Yanki'da da vardi (K/Q): oradan silinmis ama Q durmali.
        check("catisan tus oteki aksiyondan alindi",
              pygame.K_k not in table[Action.ECHO]
              and pygame.K_q in table[Action.ECHO],
              binds.labels_for(table, Action.ECHO))

        # --- ESC reddi ---
        scene.row = row_for(Action.ATTACK)
        scene._adjust(1)
        press(pygame.K_ESCAPE)
        check("ESC yakalamayi IPTAL ediyor, atanmiyor",
              scene.capturing is None
              and pygame.K_ESCAPE not in binds.read(game.settings)[Action.ATTACK])

        # --- Son tus calinamaz ---
        # ECHO_ASK'in tek tusu F; onu baskasina vermeye calis.
        scene.row = row_for(Action.INTERACT)
        scene._adjust(1)
        press(pygame.K_f)
        table = binds.read(game.settings)
        check("son tus calinamiyor",
              bool(scene.capture_error) and table[Action.ECHO_ASK] == (pygame.K_f,),
              scene.capture_error)
        check("reddedilince kutu ACIK kaliyor", scene.capturing is not None)
        scene._end_capture()

        # --- Sifirlama ---
        scene.row = len(scene.entries) - 1
        check("son satir sifirlama",
              isinstance(scene.current, ResetBindings))
        scene._adjust(1)
        table = binds.read(game.settings)
        check("sifirlama varsayilani geri getirdi",
              table[Action.JUMP] == DEFAULT_KEYBOARD[Action.JUMP],
              binds.labels_for(table, Action.JUMP))
        # Bir donem `apply_bindings` yalnizca uzerine yaziyordu ve
        # sifirlama ancak oyun yeniden acilinca goruluyordu.
        check("sifirlama CANLI katmana da gecti",
              game.input.keyboard[Action.JUMP] == DEFAULT_KEYBOARD[Action.JUMP],
              str(game.input.keyboard[Action.JUMP]))

        # --- Uzun listeler tasmasin ---
        long_label = binds.labels_for(binds.read(game.settings), Action.JUMP)
        check("uzun tus listesi kisaltiliyor",
              long_label.count("/") < len(DEFAULT_KEYBOARD[Action.JUMP]) - 1,
              long_label)
    finally:
        game.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
