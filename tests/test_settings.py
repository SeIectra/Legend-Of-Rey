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
from src.systems.settings import ALL_ENTRIES, Option  # noqa: E402
from src.ui.i18n import t  # noqa: E402
from src.ui.settings_scene import SettingsScene  # noqa: E402

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

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("Oyun kolu ayari saglam - acilis hizli kaliyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
