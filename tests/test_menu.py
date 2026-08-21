"""Menu ve kayit sistemi dogrulamasi.

`docs/menu-ui.md` ve `CLAUDE.md` 9'daki UX kurallarinin kodda gercekten
tuttugunu kanitlar. Ozellikle **kayit guvenligi**: yazma sirasinda cokme
olursa yedekten donulmeli.

Test gercek kullanici dizinine dokunmaz - gecici bir klasore yonlendirilir.

Calistir:
    python tests/test_menu.py
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Kayitlari gecici dizine yonlendir - gercek kaydi bozmayalim.
_TEMP = Path(tempfile.mkdtemp(prefix="lore_test_"))
os.environ["APPDATA"] = str(_TEMP)
os.environ["XDG_DATA_HOME"] = str(_TEMP)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from src.config import MENU_TRANSITION_MAX_FRAMES  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.systems.save import (  # noqa: E402
    SaveData, backup_path, delete_save, has_save, read_save, save_path,
    write_save,
)
from src.systems.settings import DISPLAY_OPTIONS, Settings, TABS  # noqa: E402
from src.ui import i18n  # noqa: E402
from src.ui.widgets import CONFIRM_FLASH_FRAMES, SELECT_ANIM_FRAMES  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def make_game() -> Game:
    game = Game()
    return game


def step(game, count: int = 1, keys: tuple[int, ...] = ()) -> None:
    for index in range(count):
        game.input.begin_frame()
        if index == 0:
            for key in keys:
                game.input.handle_event(
                    pygame.event.Event(pygame.KEYDOWN, key=key))
        game.input.end_frame()
        game.scenes.update()
        game.scenes._flush()


def main() -> int:
    # Test gorunen metni dogruluyor; dili acikca sabitle ki makinede kayitli
    # ayar ne olursa olsun ayni sonucu versin.
    i18n.set_language("tr")

    # --- 1. Kayit guvenligi -------------------------------------------------
    print("--- kayit guvenligi ---")
    delete_save()
    check(not has_save(), "baslangicta kayit yok")

    data = SaveData(chapter=2, chapter_name="İlk İniş", gold=310,
                    playtime_frames=60 * 60 * 34, secrets_found=1,
                    secrets_total=1)
    check(write_save(data), "kayit yazildi")
    check(has_save(), "kayit var")

    loaded, status = read_save()
    check(status == "ok" and loaded is not None, "kayit okundu", status)
    check(loaded.gold == 310 and loaded.chapter == 2, "kayit icerigi dogru",
          f"bolum {loaded.chapter}, {loaded.gold} altin")
    check(loaded.playtime_text == "34dk", "sure metni dogru",
          loaded.playtime_text)

    # Ikinci yazma yedek olusturmali.
    data.gold = 420
    write_save(data)
    check(backup_path().is_file(), "ikinci yazmada yedek olustu")

    # Ana kaydi boz - yedekten donulmeli.
    save_path().write_text("{bozuk json", encoding="utf-8")
    recovered, status = read_save()
    check(status == "backup" and recovered is not None,
          "bozuk kayitta yedekten donuldu", status)
    check(recovered.gold == 310, "yedek onceki surumu tasiyor",
          f"{recovered.gold} altin")

    # Iki dosya da bozuksa cokmemeli.
    backup_path().write_text("bu da bozuk", encoding="utf-8")
    nothing, status = read_save()
    check(nothing is None and status == "none",
          "iki dosya da bozuksa temiz basarisizlik", status)

    delete_save()

    # --- 2. Ayarlar ---------------------------------------------------------
    print("\n--- ayarlar ---")
    settings = Settings()
    check(len(TABS) == 3, "uc sekme", ", ".join(t[0] for t in TABS))

    shake_option = next(o for o in DISPLAY_OPTIONS
                        if getattr(o, "key", "") == "screen_shake")
    check(settings.get("screen_shake") == 1.0, "sarsinti varsayilani Normal")
    settings.cycle(shake_option, 1)
    check(settings.get("screen_shake") == 0.0, "sarsinti kapatilabiliyor",
          str(settings.get("screen_shake")))

    # Diske yazilmali - "Kaydet" butonu yok.
    reloaded = Settings()
    check(reloaded.get("screen_shake") == 0.0, "ayar diske yazildi")

    labels = [o.label for o in TABS[2][1]]
    check(not any("Kolay" in label for label in labels),
          "hicbir ayar 'Kolay Mod' diye etiketlenmemis")

    settings.reset_to_defaults()

    # --- 3. Ana menu --------------------------------------------------------
    print("\n--- ana menu ---")
    from src.ui.menu import MainMenuScene

    game = make_game()
    game.scenes.set_root(MainMenuScene, transition=False)
    game.scenes._flush()
    menu_scene = game.scenes.current
    step(game, 2)

    devam = menu_scene.menu.items[0]
    check(devam.text == "DEVAM ET", "DEVAM ET en ustte")
    check(not devam.visible, "kayit yokken DEVAM ET GORUNMEZ (gri degil)")
    check(menu_scene.menu.selected.text == "YENİ OYUN",
          "kayit yokken YENI OYUN secili", menu_scene.menu.selected.text)

    cikis = menu_scene.menu.items[-1]
    check(cikis.text == "ÇIKIŞ" and cikis.gap_before,
          "CIKIS en altta ve boslukla ayrilmis")

    # Kayit varken DEVAM ET gorunur ve onceden secili olmali.
    write_save(SaveData(chapter=3, chapter_name="Meşale Mahzeni", gold=120))
    menu_scene.on_resume()
    check(menu_scene.menu.items[0].visible, "kayit varken DEVAM ET gorunur")
    check(menu_scene.menu.selected.text == "DEVAM ET",
          "kayit varken DEVAM ET onceden secili",
          menu_scene.menu.selected.text)

    # --- 4. Uzerine yazma uyarisi -------------------------------------------
    print("\n--- uzerine yazma ---")
    menu_scene.menu.index = 1               # YENI OYUN
    menu_scene.menu.activate()
    check(menu_scene.confirm_overwrite is not None,
          "kayit varken YENI OYUN onay soruyor")
    check(menu_scene.confirm_overwrite.selected.text == "İPTAL",
          "yikici eylemde varsayilan secim IPTAL",
          menu_scene.confirm_overwrite.selected.text)
    check(menu_scene.confirm_overwrite.items[1].danger,
          "yikici secenek tehlike olarak isaretli")
    menu_scene.confirm_overwrite.activate()  # IPTAL
    check(menu_scene.confirm_overwrite is None, "IPTAL uyariyi kapatti")

    # --- 5. Gecis sureleri --------------------------------------------------
    print("\n--- gecis sureleri ---")
    check(SELECT_ANIM_FRAMES <= MENU_TRANSITION_MAX_FRAMES,
          f"secim animasyonu <= {MENU_TRANSITION_MAX_FRAMES} kare",
          f"{SELECT_ANIM_FRAMES}")
    check(CONFIRM_FLASH_FRAMES <= MENU_TRANSITION_MAX_FRAMES,
          f"onay flasi <= {MENU_TRANSITION_MAX_FRAMES} kare",
          f"{CONFIRM_FLASH_FRAMES}")
    check(game.scenes.transition.frames <= MENU_TRANSITION_MAX_FRAMES,
          "sahne gecisi siniri asmiyor",
          f"{game.scenes.transition.frames}")

    # --- 6. Gezinme gorunmezi atliyor mu ------------------------------------
    print("\n--- gezinme ---")
    delete_save()
    menu_scene.on_resume()
    labels_seen = []
    for _ in range(5):
        labels_seen.append(menu_scene.menu.selected.text)
        menu_scene.menu.move(1)
    check("DEVAM ET" not in labels_seen,
          "gezinme gorunmez ogeyi atliyor", str(labels_seen))
    check("EKSTRALAR" not in labels_seen,
          "gezinme kapali ogeyi atliyor")

    # --- 7. Karakter secimi -------------------------------------------------
    print("\n--- karakter secimi ---")
    from src.ui.character_select import CHARACTERS, CharacterSelectScene

    game.scenes.set_root(CharacterSelectScene, transition=False)
    game.scenes._flush()
    select = game.scenes.current
    step(game, 2)
    check(len(CHARACTERS) == 2, "iki karakter")
    check(CHARACTERS[0].key == "rey" and CHARACTERS[0].has_echo,
          "Rey'in Yankisi var")
    check(CHARACTERS[1].key == "ardo" and not CHARACTERS[1].has_echo,
          "Ardo'nun Yankisi yok")

    select.index = 1
    select._confirm()
    saved, _ = read_save()
    check(saved is not None and saved.character == "ardo",
          "secilen karakter kaydedildi",
          saved.character if saved else "kayit yok")
    check(saved.max_health == 120, "Ardo'nun cani 120", str(saved.max_health))

    # --- 8. Ayarlar ekrani --------------------------------------------------
    print("\n--- ayarlar ekrani ---")
    from src.ui.settings_scene import SettingsScene

    game.scenes.set_root(SettingsScene, transition=False)
    game.scenes._flush()
    settings_scene = game.scenes.current
    step(game, 2)
    check(settings_scene.tabs.index == 0, "ilk sekme GORUNTU")

    before = game.settings.get("colorblind")
    settings_scene.row = 3                   # Renk koru modu
    settings_scene._adjust(1)
    check(game.settings.get("colorblind") != before,
          "renk koru modu degistirilebiliyor",
          str(game.settings.get("colorblind")))

    settings_scene.tabs.index = 1            # SES
    settings_scene.row = 0
    volume_before = game.settings.get("volume_master")
    settings_scene._adjust(-1)
    check(game.settings.get("volume_master") < volume_before,
          "ses seviyesi kisilabiliyor",
          f"{volume_before} -> {game.settings.get('volume_master')}")

    # --- 9. Duraklatma ------------------------------------------------------
    print("\n--- duraklatma ---")
    from src.scenes.combat_room import CombatRoomScene
    from src.ui.pause import PauseScene

    game.scenes.set_root(CombatRoomScene, transition=False)
    game.scenes._flush()
    step(game, 3)
    game.scenes.push(PauseScene, save_data=read_save()[0])
    game.scenes._flush()
    pause = game.scenes.current
    check(isinstance(pause, PauseScene), "duraklatma acildi")
    check(len(game.scenes.stack) == 2, "oyun yiginda kaldi",
          f"{len(game.scenes.stack)} sahne")
    check(pause.blocks_update and not pause.blocks_draw,
          "oyun donar ama gorunur kalir")

    pause._ask_quit()
    check(pause.saved_notice > 0,
          "ana menuye donmeden once kaydedildi ve bildiriliyor")
    check(pause.confirm_quit.selected.text == "İPTAL",
          "ana menu onayinda varsayilan IPTAL")

    game.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Menu, kayit ve ayarlar belgedeki UX kurallarina uyuyor.")
    return 0


try:
    code = main()
finally:
    shutil.rmtree(_TEMP, ignore_errors=True)
raise SystemExit(code)
