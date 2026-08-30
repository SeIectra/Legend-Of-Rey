"""Karakter sprite'lari - oranlar ve **butce**.

Arda (29.08.2026): *"Karakterler basit pixel bloklarindan olusmus gibi
degil, ozenle cizilmis karakterler gibi gorunmeli. Cocuk gibi veya chibi
gorunmesin. Daha olgun, karizmatik ve estetik yuz oranlari kullan."*

Iki sey birden korunmali ve bunlar **birbirine karsi calisiyor**:

  * **Oran**: kafa/boy orani chibi (3.5) degil yetiskin tarafinda olmali.
  * **Butce**: sprite 32 pikseli gecemez. Bu tahmin degil, olculdu -
    oyunun en dar yurunebilir gecidi 2 tile = 32 piksel (Bolum 1 (20,11)
    ve Bolum 2 (26,13)). Gecerse karakter koridorlardan gecemez ve bes
    bolumun oda geometrisi + ziplama zarfi + `tools/reachability.py`
    dogrulamasi birden gecersiz olur.

Bu test o iki sinirin arasindaki daralan koridoru koruyor. Boy uzatarak
oran duzeltmek cazip - ve tam olarak bu yuzden butce burada yaziliyor:
elden gecirme sirasinda boy bir ara 35'e cikti ve ancak olculdugu icin
fark edildi.

Yuzun **gercek** detayi (kapak, iris, highlight, burun kumesi, dudak)
oyun ici sprite'ta imkansiz; o is `src/art/portrait.py`'de, kafanin 40
piksel oldugu yerde yapiliyor - `tests/test_portrait.py`.

Calistir:
    python tests/test_sprites.py
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

from src.art.animation import CHARACTERS  # noqa: E402
from src.art.animator import Animator  # noqa: E402
from src.config import TILE_SIZE  # noqa: E402

# Oyunun en dar yurunebilir gecidi: 2 tile.
SPRITE_BUDGET = TILE_SIZE * 2

# Bolumlere GERCEKTEN yerlestirilmis karakterler. Katman 2/3'un geri
# kalani (mizrakli, okcu, komutan, sessiz, yankilayan, bolunen) yalnizca
# sanat olarak var - hicbir odaya konmadi, yani butce onlari henuz
# baglamiyor. Sirasi gelince bu listeye eklenecekler.
PLACED = ("rey", "rey_armed", "ardo", "villager", "cemo",
          "shambler", "climber", "bloated", "shieldbearer")

# Silah tasiyanlarda olculen yukseklige silahin ucu de giriyor. Silah
# govde degil - ceza yazmiyoruz, ama tolerans da vermiyoruz: yalnizca
# hangi karakterlerde bunun beklendigini ISIMLENDIRIYORUZ.
ARMED = {"rey_armed", "ardo", "shieldbearer"}
ARMED_ALLOWANCE = 2

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def measure(name: str, pose: str = "idle"):
    animator = Animator(name)
    animator.play(pose)
    for _ in range(8):
        animator.update()
    image = animator.image
    return image.get_bounding_rect()


def main() -> int:
    print("--- butce: 2 tile koridor ---")
    for name in PLACED:
        box = measure(name)
        limit = SPRITE_BUDGET + (ARMED_ALLOWANCE if name in ARMED else 0)
        check(box.height <= limit,
              f"{name} butce icinde",
              f"{box.height} <= {limit}")

    print("\n--- oran: chibi degil ---")
    # 3.5 kafa = chibi (eski Rey tam buydu). 4.5+ stilize yetiskin.
    # 7-8 gercekci; bu olcekte imkansiz ve zaten hedef degil.
    for name in ("rey", "ardo"):
        box = measure(name)
        head = CHARACTERS[name].head_radius * 2
        ratio = box.height / head
        check(ratio >= 4.4,
              f"{name} chibi oraninin uzerinde",
              f"{ratio:.1f} kafa boyu (chibi 3.5)")

    print("\n--- Rey ve Ardo ayni iskeletten ama AYRI ---")
    rey, ardo = CHARACTERS["rey"], CHARACTERS["ardo"]
    check(ardo.shoulder_width > rey.shoulder_width,
          "Ardo daha genis omuzlu",
          f"{ardo.shoulder_width} > {rey.shoulder_width}")
    check(ardo.limb_width > rey.limb_width,
          "Ardo daha kalin uzuvlu",
          f"{ardo.limb_width} > {rey.limb_width}")
    check(ardo.thigh < rey.thigh,
          "Ardo daha kisa bacakli - agir durus",
          f"{ardo.thigh} < {rey.thigh}")
    check(ardo.brow_tilt < 0 < rey.brow_tilt,
          "kas egimleri ZIT - Rey acik, Ardo catik",
          f"rey {rey.brow_tilt:+d} / ardo {ardo.brow_tilt:+d}")

    print("\n--- boyun: kafa, boyun, omuz ayri formlar ---")
    check(rey.neck > 0.0, "boyun bosluğu var", str(rey.neck))

    print("\n--- siluet testi (CLAUDE.md 6) ---")
    # "Her sprite tek renk siyaha cevrildiginde ne oldugu anlasilmali."
    #
    # Ilk surum siluet **kutularini** karsilastiriyordu ve bu kotu bir
    # vekildi: Suruklenen ile Tirmanan'in kutusu ayni (13x28) ama
    # siluetleri bambaska (biri dik, digeri kollari acik). Kutu esitligi
    # sekil esitligi DEGIL.
    #
    # Dogru olcu: maskeleri ust uste koyup **farkli piksel oranina**
    # bakmak. Iki siluet alanlarinin en az dortte biri kadar farkliysa
    # tek renkte de ayirt edilir.
    masks = {}
    for name in ("rey", "ardo", "shambler", "climber", "bloated"):
        animator = Animator(name)
        animator.play("idle")
        for _ in range(8):
            animator.update()
        image = animator.image
        mask = pygame.mask.from_surface(image)
        masks[name] = mask

    # Fark olcusu **simetrik** olmali: `kesisim / min(alan)` bir sekil
    # digerini KAPSADIGINDA sifir cikiyor ve Ardo Rey'i kapsiyordu -
    # ilk surum bu yuzden %8 gibi yaniltici bir sayi uretti. Dogrusu
    # kesisim/birlesim (IoU).
    names = list(masks)
    worst = 1.0
    worst_pair = ""
    for i, first in enumerate(names):
        for second in names[i + 1:]:
            a, b = masks[first], masks[second]
            overlap = a.overlap_area(b, (0, 0))
            union = a.count() + b.count() - overlap
            diff = 1.0 - (overlap / max(1, union))
            if diff < worst:
                worst, worst_pair = diff, f"{first}/{second}"
    # **Olculdu 29.08.2026:** en dar cift rey/ardo %25.3; butun dusman
    # ciftleri %30'un uzerinde. Rey ile Ardo'nun en yakin olmasi dogal -
    # ikisi de ayni iskeletten cikan iki insan; onlari ayiran sey uzun
    # sac / etek / pelerin ile genis omuz / omuzluk. Esik o olculen
    # degerin biraz altina konuldu: amac "daha da benzemesini" yakalamak,
    # mevcut tasarimi kutlamak degil.
    check(worst >= 0.22,
          "en benzer iki siluet bile yeterince farkli",
          f"{worst_pair} %{worst * 100:.1f} farkli (esik %22)")

    print("\n--- her karakterin butun pozlari cizilebiliyor ---")
    from src.art.animation import ANIMATIONS
    broken = []
    for name in PLACED:
        for state in ANIMATIONS:
            animator = Animator(name)
            animator.play(state)
            if animator.image is None:
                broken.append(f"{name}/{state}")
    check(not broken, "hicbir poz bos donmuyor", str(broken[:5]))

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Sprite'lar: butce icinde, chibi degil, karakterler ayrisiyor.")
    return 0


raise SystemExit(main())
