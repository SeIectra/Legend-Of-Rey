#!/usr/bin/env python3
"""Legend of Rey (LORE) — Ardeko Studios

Calistirmak icin:
    python main.py

Hata ayiklama tuslari:
    F3   hata ayiklama katmani (FPS, sahne yigini, sahneye ozel bilgi)
    F4   siluet modu - her sey duz kutuya doner, dovus hissi boyle test edilir
    F11  tam ekran
    F12  ekran goruntusu
"""
from __future__ import annotations

import sys
from pathlib import Path

# Depo kokunu import yoluna ekle: oyun her dizinden calistirilabilsin.
sys.path.insert(0, str(Path(__file__).resolve().parent))


SCENES = {
    # Varsayilan akis: intro -> menunun kurulmasi -> menu. Uculu tek bir
    # kesintisiz kamera hareketi (docs/menu-ui.md 0).
    "intro": ("src.scenes.intro", "IntroScene"),
    "menu": ("src.ui.menu", "MainMenuScene"),
    # Acilis prologu - Rey'in Yankisini anlatan kisa film.
    "prolog": ("src.scenes.prologue", "ReyPrologue"),
    "prolog-ardo": ("src.scenes.prologue", "ArdoPrologue"),
    "bolum1": ("src.scenes.chapter01", "Chapter01Scene"),
    "bolum2": ("src.scenes.chapter02", "Chapter02Scene"),
    # Bolum 1 -> 2 gecisi (yariktan dusus). Ayrica dogrudan
    # acilabilsin: ara sahneyi tek basina ayarlamak icin.
    "inis": ("src.scenes.chapter02_cinematics", "DescentCinematic"),
    "bolum3": ("src.scenes.chapter03", "Chapter03Scene"),
    # Bolum 4 - "Kayit Odasi". ★nefes: dovus yok (docs/yapi.md B4).
    "bolum6": ("src.scenes.chapter06", "Chapter06Scene"),
    "bolum5": ("src.scenes.chapter05", "Chapter05Scene"),
    "bolum4": ("src.scenes.chapter04", "Chapter04Scene"),
    "bolum7": ("src.scenes.chapter07", "Chapter07Scene"),
    # Bolum 7'nin acilis ara sahnesi ayri girdi: sahneyi tek
    # basina denemek isteyen "bolum7" yaziyor, gecisi gormek
    # isteyen "bolum7-muhur".
    "bolum7-muhur": ("src.scenes.chapter07_cinematics", "SealCinematic"),
    "bolum7-el": ("src.scenes.chapter07_cinematics", "HandCinematic"),
    "bolum8": ("src.scenes.chapter08", "Chapter08Scene"),
    "bolum8-ates": ("src.scenes.chapter08_cinematics", "FiresideCinematic"),
    "bolum8-fisilti": ("src.scenes.chapter08_cinematics", "WhisperCinematic"),
    "bolum9": ("src.scenes.chapter09", "Chapter09Scene"),
    "bolum9-guven": ("src.scenes.chapter09_cinematics", "TrustCinematic"),
    "bolum10": ("src.scenes.chapter10", "Chapter10Scene"),
    "bolum10-ayrilik": ("src.scenes.chapter10_cinematics", "PartingCinematic"),
    "bolum10-yalan": ("src.scenes.chapter10_cinematics", "LieCinematic"),
    "bolum11": ("src.scenes.chapter11", "Chapter11Scene"),
    # Bolum 12 "Mektup" - nefes bolumu + Ardo'nun inis duzenegi
    # (mekanik havuzunun 11. maddesi).
    "bolum12": ("src.scenes.chapter12", "Chapter12Scene"),
    "bolum12-kamp": ("src.scenes.chapter12_cinematics", "CampCinematic"),
    "bolum12-mektup": ("src.scenes.chapter12_cinematics", "LetterCinematic"),
    "bolum13": ("src.scenes.chapter13", "Chapter13Scene"),
    # B13'un dort ara sahnesi ayri ayri acilabilsin - sahneleme
    # ayarlamak icin bolumu bastan oynamak gerekmesin.
    "bolum13-kafes": ("src.scenes.chapter13_cinematics", "CageCinematic"),
    "bolum13-isaret": ("src.scenes.chapter13_cinematics", "MarkCinematic"),
    "bolum13-zindanci": ("src.scenes.chapter13_cinematics", "GaolerCinematic"),
    "bolum13-kapi": ("src.scenes.chapter13_cinematics", "GateCinematic"),
    # Bolum 14 "Yanki'nin Kaynagi" - twist + BOSS 3. Katman 3 burada
    # basliyor ve Yanki tersine doner.
    "bolum14": ("src.scenes.chapter14", "Chapter14Scene"),
    "bolum14-kaynak": ("src.scenes.chapter14_cinematics", "SourceCinematic"),
    "bolum14-arena": ("src.scenes.chapter14_cinematics", "ArenaCinematic"),
    "bolum14-olmedi": ("src.scenes.chapter14_cinematics", "AfterCinematic"),
    # Bolum 15 "Sessizlik" - gizlilik. B14'un ihaneti on kosulu zaten
    # kurdu: duyuyu acmak suruyu uyandiriyor.
    "bolum15": ("src.scenes.chapter15", "Chapter15Scene"),
    "bolum15-gectin": ("src.scenes.chapter15_cinematics", "PassedCinematic"),
    # Bolum 16 "Sirt Sirta" - en uzun team-up. Yoldas burada kendi
    # kendine kalkmiyor; kaldirma mekanigi "bolum16-kaldir" sahnesinde
    # ogretiliyor.
    "bolum16": ("src.scenes.chapter16", "Chapter16Scene"),
    "bolum16-donus": ("src.scenes.chapter16_cinematics", "ReturnCinematic"),
    "bolum16-kaldir": ("src.scenes.chapter16_cinematics", "LiftCinematic"),
    "bolum16-kalp": ("src.scenes.chapter16_cinematics", "HeartCinematic"),
    # Bolum 17 "Ikili Kule" - iki oynanabilir karakter, `Y` ile gecis.
    "bolum17": ("src.scenes.chapter17", "Chapter17Scene"),
    "bolum17-kapi": ("src.scenes.chapter17_cinematics", "HeldDoorCinematic"),
    "dovus": ("src.scenes.combat_room", "CombatRoomScene"),
    "temel": ("src.scenes.foundation_check", "FoundationCheckScene"),
}
DEFAULT_SCENE = "intro"


def main() -> int:
    import importlib

    name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SCENE
    if name not in SCENES:
        print(f"bilinmeyen sahne: {name}")
        print(f"secenekler: {', '.join(SCENES)}")
        return 1

    from src.core.game import Game

    module_name, class_name = SCENES[name]
    scene_cls = getattr(importlib.import_module(module_name), class_name)

    game = Game()
    game.run(scene_cls)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
