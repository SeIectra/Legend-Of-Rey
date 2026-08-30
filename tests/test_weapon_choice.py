"""Bolum 2 silah secimi - odul GERCEKTEN veriliyor ve KALICI mi.

`docs/bolum-02.md`: *"Odul: 55 altin + **ilk silah secimi**: Hancer (hizli,
kisa) veya Balta (yavas, zirh deler)."* Bu DEVIR'in acik maddesiydi:
altyapi (`src/combat/weapons.py`) hazirdi, secim ekrani/akisi yoktu.

Korunan kurallar:

  * Secim boss oldukten sonra **kendiliginden** aciliyor
  * Oyuncu **olurse acilmiyor** - bu bir zafer odulu
  * Secim zincir tablosunu gercekten degistiriyor (hasar/kare)
  * Secim **kayda** yaziliyor ve sonraki bolume tasiniyor
  * Kaydedilmis silah **Bolum 1'i bozmuyor** (orada yumrukla baslaniyor)
  * Panel sayilari uydurulmuyor - `config.py`'den okunuyor

Calistir:
    python tests/test_weapon_choice.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

# `pygame.init()` DEGIL. O, joystick alt sistemini de acar ve bu
# makinede 40 SANIYE surer (olculdu 30.08.2026 - bir surucu sorunu,
# kodla ilgisi yok). 21 test paketi bunu ayri ayri odedigi icin butun
# paket 14 dakikayi asiyordu.
#
# `src/core/game.py` de tam olarak bu yolu izliyor; test oyunla ayni
# sekilde acilsin. Ses gerekirse `synth.init_mixer()` cagrilir.
pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.combat import weapons  # noqa: E402
from src.config import AXE_CHAIN, DAGGER_CHAIN  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.scenes.chapter02 import WEAPON_CHOICE_DELAY, Chapter02Scene  # noqa: E402
from src.systems.save import SaveData  # noqa: E402
from src.ui.weapon_choice import CHOICES, WeaponChoiceScene  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def step(game, count: int = 1) -> None:
    for _ in range(count):
        game.input.begin_frame()
        game.input.end_frame()
        game.scenes.update()
        game.frame += 1


def main() -> int:
    game = Game()

    # --- 1. Sprite'lar gercekten ayri ---------------------------------------
    # Bir ara Hancer ve Balta kilicla AYNI sprite'i kullaniyordu. Secim bir
    # karar ekrani; secilen sey elde gorunmuyorsa karar geri bildirimsiz.
    print("--- silahlarin kendi gorunumu var ---")
    from src.art.animation import CHARACTERS
    for name in ("rey_dagger", "rey_axe", "ardo_dagger", "ardo_axe"):
        check(name in CHARACTERS, f"{name} spec'i kayitli")
    check(weapons.get(weapons.DAGGER).sprite_suffix
          != weapons.get(weapons.AXE).sprite_suffix,
          "Hancer ve Balta ayni sprite'i kullanmiyor")

    # --- 2. Zincirler gercekten farkli --------------------------------------
    print("\n--- iki secenek gercekten farkli ---")
    check(len(DAGGER_CHAIN) > len(AXE_CHAIN),
          "Hancer daha uzun zincir (hizli, kisa vuruslar)",
          f"{len(DAGGER_CHAIN)} > {len(AXE_CHAIN)}")
    check(AXE_CHAIN[-1].damage > DAGGER_CHAIN[-1].damage,
          "Balta bitiricisi daha agir (zirh deler)",
          f"{AXE_CHAIN[-1].damage} > {DAGGER_CHAIN[-1].damage}")
    check(set(CHOICES) == {weapons.DAGGER, weapons.AXE},
          "ekranda tam iki secenek var", str(CHOICES))

    # --- 3. Boss olunce secim ACILIYOR --------------------------------------
    #
    # `PlayScene.on_enter` kaydi HER ZAMAN diskten okuyor (`read_save()`),
    # disaridan `save_data` almiyor. Test bu yuzden sahnenin KENDI kayit
    # nesnesiyle calisiyor; ilk surum disaridan bir `SaveData` geciriyordu
    # ve "kayda yazilmadi" diye yanlis alarm veriyordu - hata koddaydi
    # sanildi, oysa TESTTEYDI. Diske de yazmiyoruz: Arda'nin gercek
    # kaydini bir test ezmemeli.
    print("\n--- boss olunce acilir ---")
    game.scenes.set_root(Chapter02Scene, transition=False, character="rey")
    game.scenes._flush()
    scene = game.scenes.current
    if scene.save_data is None:
        scene.save_data = SaveData()
    save = scene.save_data
    original_weapon = save.weapon

    scene.arena_sealed = True
    scene._open_arena()          # boss yenildi yolu
    check(scene.weapon_choice_frames > 0, "sayac kuruldu",
          str(scene.weapon_choice_frames))
    check(not scene.weapon_offered,
          "ekran HEMEN acilmadi - zafer ani kesilmiyor")

    step(game, WEAPON_CHOICE_DELAY + 2)
    game.scenes._flush()
    check(scene.weapon_offered, "gecikme sonunda secim acildi")
    check(isinstance(game.scenes.current, WeaponChoiceScene),
          "ustteki sahne silah secimi",
          type(game.scenes.current).__name__)

    # --- 4. Secim zinciri ve kaydi degistiriyor -----------------------------
    print("\n--- secim gercekten uyguluyor ---")
    choice = game.scenes.current
    before = len(scene.player.chain.chain_table)
    choice.index = list(CHOICES).index(weapons.AXE)
    choice._choose()
    game.scenes._flush()
    check(save.weapon == weapons.AXE, "kayda yazildi", save.weapon)
    check(scene.player.weapon == weapons.AXE, "oyuncu kusandi",
          scene.player.weapon)
    check(scene.player.chain.chain_table is AXE_CHAIN,
          "zincir tablosu GERCEKTEN degisti",
          f"{before} vurus -> {len(scene.player.chain.chain_table)}")
    check(scene.player.animator.character == "rey_axe",
          "sprite de degisti", scene.player.animator.character)

    # --- 5. Sonraki bolume tasiniyor ----------------------------------------
    # `_equip_saved_weapon()` dogrudan sinaniyor: kaydi diske yazip yeni
    # sahnenin okumasini beklemek gercek kayit dosyasini ezerdi.
    print("\n--- sonraki bolume tasiniyor ---")
    from src.scenes.chapter05 import Chapter05Scene
    game.scenes.set_root(Chapter05Scene, transition=False, character="rey")
    game.scenes._flush()
    later = game.scenes.current
    if later.save_data is None:
        later.save_data = SaveData()
    later.save_data.weapon = weapons.AXE
    later._equip_saved_weapon()
    check(later.player.weapon == weapons.AXE,
          "Bolum 5'e Balta ile giriliyor", later.player.weapon)
    check(later.player.chain.chain_table is AXE_CHAIN,
          "tasinan silahin zinciri de dogru")

    # --- 6. Bolum 1'i BOZMUYOR ----------------------------------------------
    # `SaveData.weapon` varsayilani "sword"; kosulsuz kusandirsaydik
    # Bolum 1'de yumrukla baslamasi gereken Rey kilicla baslar ve o
    # bolumun anlati ani ("kilici buluyor") cope giderdi.
    print("\n--- Bolum 1 bozulmuyor ---")
    fresh = SaveData()
    check(fresh.weapon == weapons.SWORD,
          "kaydin varsayilani hala 'sword'", fresh.weapon)
    from src.scenes.chapter01 import Chapter01Scene
    game.scenes.set_root(Chapter01Scene, transition=False, character="rey")
    game.scenes._flush()
    first = game.scenes.current
    if first.save_data is None:
        first.save_data = SaveData()
    first.save_data.weapon = weapons.SWORD
    first._equip_saved_weapon()
    check(first.player.weapon == weapons.FISTS,
          "Rey Bolum 1'e YUMRUKLA basliyor - 'sword' degeri ezmiyor",
          first.player.weapon)

    # --- 7. Olum odul vermiyor ----------------------------------------------
    print("\n--- olmek odul degil ---")
    game.scenes.set_root(Chapter02Scene, transition=False, character="rey")
    game.scenes._flush()
    dead_run = game.scenes.current
    dead_run.arena_sealed = True
    dead_run.on_player_died(dead_run.player)
    check(dead_run.weapon_choice_frames == 0,
          "olen oyuncuya silah secimi ACILMIYOR",
          str(dead_run.weapon_choice_frames))
    check(not dead_run.arena_sealed,
          "ama arena kapisi yine de aciliyor - kilitli kalmiyor")

    save.weapon = original_weapon      # bellekteki kaydi geri al
    game.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Silah secimi: aciliyor, uyguluyor, kalici, ve olumle alinmiyor.")
    return 0


raise SystemExit(main())
