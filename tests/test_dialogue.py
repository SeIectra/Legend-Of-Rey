"""Diyalog dogrulamasi.

Oyun bir donem **diyalogsuz** tasarlanmisti; Arda karari degistirdi
(22.08.2026). Konusma bir kanal **ekledi**, digerlerini degistirmedi.

Korunan kurallar:

  * **Yanki'nin kutusu yok.** Kafanin icindeki sesi cerceveli bir kutuya
    koymak onu "odadaki bir baska kisi" yapar ve tekinsizligini oldurur.
  * Kutu **tam metne** gore boyutlanir, yazilana gore degil - yoksa metin
    yazilirken kutu buyur ve satirlar zaplar.
  * Yazim hizlandirilabilir ama **atlanamaz** (sinematiklerle ayni kural).
  * Replikler dil anahtari tutar, hazir metin degil.

Calistir:
    python tests/test_dialogue.py
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

pygame.init()
pygame.display.set_mode((64, 64))

from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.ui import i18n  # noqa: E402
from src.ui.dialogue import (  # noqa: E402
    ECHO, MAX_LINES, SPEAKER_KEYS, Dialogue, Line, _wrap,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def pixels(surface: pygame.Surface) -> int:
    """Bos olmayan piksel sayisi - bir sey cizildi mi?"""
    import numpy as np
    return int(np.count_nonzero(pygame.surfarray.array3d(surface).sum(axis=2)))


def main() -> int:
    i18n.set_language("tr")
    game = Game()
    canvas = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))

    # --- 1. Temel akis ------------------------------------------------------
    print("--- akis ---")
    dlg = Dialogue()
    check(dlg.done, "bos diyalog bitmis sayilir")

    dlg.start((Line("cemo", "line.ch01_cemo_gift"),
               Line("rey", "line.ch01_rey_thanks")))
    check(not dlg.done, "baslatilinca aktif")
    check(dlg.current.speaker == "cemo", "ilk replik ilk konusmacinin")
    check(dlg.revealed == 0, "yazim sifirdan basliyor")

    # Yazim ilerliyor mu?
    for _ in range(6):
        game.input.begin_frame()
        game.input.end_frame()
        dlg.update(game)
    check(0 < dlg.revealed < len(dlg.full_text),
          "metin harf harf aciliyor", f"{int(dlg.revealed)} karakter")

    # --- 2. Atlanamaz, hizlandirilabilir ------------------------------------
    print("\n--- hizlandirma ---")
    slow = Dialogue()
    slow.start((Line("cemo", "line.ch01_cemo_gift"),))
    fast = Dialogue()
    fast.start((Line("cemo", "line.ch01_cemo_gift"),))

    def tick(target: Dialogue, hold: bool) -> None:
        """Bir kare ilerlet. `hold` False ise tus **birakiliyor**.

        Birakmazsak girdi yoneticisi tusu basili sayiyor ve sonraki
        KEYDOWN yeni bir basis kenari uretmiyor - bu tuzaga projede
        birkac kez dusuldu.
        """
        game.input.begin_frame()
        event = pygame.KEYDOWN if hold else pygame.KEYUP
        game.input.handle_event(
            pygame.event.Event(event, key=pygame.K_RETURN))
        game.input.end_frame()
        target.update(game)

    def press(target: Dialogue) -> None:
        """Tek bas-birak: yeni bir basis kenari uretir."""
        game.input.begin_frame()
        game.input.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        game.input.end_frame()
        target.update(game)
        game.input.begin_frame()
        game.input.handle_event(
            pygame.event.Event(pygame.KEYUP, key=pygame.K_RETURN))
        game.input.end_frame()

    for _ in range(5):
        tick(slow, hold=False)
    slow_progress = slow.revealed
    for _ in range(5):
        tick(fast, hold=True)
    fast_progress = fast.revealed

    check(fast_progress > slow_progress, "basili tutmak yazimi hizlandiriyor",
          f"{slow_progress:.0f} -> {fast_progress:.0f}")
    check(not fast.done, "hizlandirma repligi **atlamiyor**")

    # --- 3. Ilerletme -------------------------------------------------------
    print("\n--- ilerletme ---")
    seq = Dialogue()
    seq.start((Line("cemo", "line.ch01_cemo_gift"),
               Line("rey", "line.ch01_rey_thanks")))
    for _ in range(400):
        tick(seq, hold=False)
        if seq.complete:
            break
    check(seq.complete, "birinci replik tamamlandi")

    # Kilit dolana kadar ilerlemez - yanlislikla iki repligi birden gecme.
    first = seq.current.key
    press(seq)
    check(seq.current is not None and seq.current.key != first,
          "onayla ikinci replige gecildi", seq.current.key if seq.current else "-")

    for _ in range(600):
        tick(seq, hold=False)
        if seq.complete:
            press(seq)
        if seq.done:
            break
    check(seq.done, "son replikten sonra diyalog kapaniyor")

    # --- 4. Yanki'nin kutusu YOK (tasarim kurali) ---------------------------
    # Ayni repligi iki konusmaciyla cizip cizilen piksel sayisini
    # karsilastiriyoruz. Kutulu olan cerceve + panel dolgusu yuzunden
    # belirgin sekilde daha fazla piksel birakir.
    print("\n--- Yanki'nin kutusu yok ---")

    def render(speaker: str) -> int:
        one = Dialogue()
        one.start((Line(speaker, "line.ch01_cemo_gift"),))
        for _ in range(400):
            tick(one, hold=True)
            if one.complete:
                break
        canvas.fill((0, 0, 0))
        one.draw(canvas, frame=0)
        return pixels(canvas)

    boxed = render("cemo")
    voiced = render(ECHO)
    check(boxed > voiced * 2,
          "kutulu konusmaci cok daha fazla piksel birakiyor (cerceve var)",
          f"kutulu {boxed} / Yanki {voiced}")
    check(voiced > 0, "Yanki'nin metni yine de ciziliyor", str(voiced))

    # --- 5. Kutu tam metne gore boyutlaniyor --------------------------------
    print("\n--- kutu boyutu ---")
    short = Dialogue()
    short.start((Line("cemo", "line.ch01_rey_thanks"),))
    long_one = Dialogue()
    long_one.start((Line("cemo", "line.ch01_echo_alone"),))
    check(short._box_rect().height <= long_one._box_rect().height,
          "uzun replik en az kisa replik kadar yer kapliyor",
          f"{short._box_rect().height} <= {long_one._box_rect().height}")

    # Yazim sirasinda kutu **degismemeli**.
    grow = Dialogue()
    grow.start((Line("cemo", "line.ch01_echo_alone"),))
    start_height = grow._box_rect().height
    for _ in range(10):
        tick(grow, hold=False)
    check(grow._box_rect().height == start_height,
          "kutu yazilirken buyumuyor - metin zaplamiyor",
          f"{start_height}px sabit")

    # --- 6. Satir kirma -----------------------------------------------------
    print("\n--- satir kirma ---")
    rows = _wrap("bir iki uc dort bes alti yedi sekiz dokuz on", 12)
    check(all(len(r) <= 12 for r in rows), "satirlar genisligi asmiyor",
          str([len(r) for r in rows]))
    check(not any(r.startswith(" ") or r.endswith(" ") for r in rows),
          "satir baslari ve sonlari temiz")
    check(" ".join(rows) == "bir iki uc dort bes alti yedi sekiz dokuz on",
          "kelimeler ortadan bolunmuyor")
    check(MAX_LINES >= 2, "en az iki satir gosteriliyor", str(MAX_LINES))

    # --- 7. Konusmaci anahtarlari cozuluyor ---------------------------------
    print("\n--- konusmaci adlari ---")
    for speaker, key in SPEAKER_KEYS.items():
        resolved = i18n.t(key)
        check(resolved != f"[{key}]", f"{speaker} adi cozuluyor", resolved)

    game.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Diyalog sistemi tasarim kurallarina uyuyor.")
    return 0


raise SystemExit(main())
