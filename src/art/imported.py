"""Disaridan gelen sanat - portreler ve ara sahne panelleri.

Elle cizilmis (ya da AI ile uretilip `tools/import_art.py`den gecmis)
PNG'ler kod uretimini **gecersiz kiliyor**: dosya varsa o kullaniliyor,
yoksa prosedurel uretim devam ediyor.

## Renk korlugu remap'i - bu modulun asil sebebi

Arda 31.08.2026'da portreleri koydu ve acilista sahte bir uyari cikti:
*"4158 piksel palet disi"*. Dosyalar quantize edilmisti; hata
kontroldeydi - **aktif** palete bakiyordu, oysa sanat **taban** palette
uretiliyor.

Ama uyarinin altindan daha buyuk bir sey cikti: o makinede renk korlugu
modu acikti (`protanopia`) ve elle cizilmis portreler o moda **hic
cevrilmiyordu**. Prosedurel sanat ceviriliyor (zincirlerden uretiliyor,
`palette.COLORS` degisince yeniden ciziliyor); disaridan gelen PNG ise
diskteki haliyle kaliyordu.

Sonuc sessiz bir erisilebilirlik acigi: renk koru bir oyuncu
sprite'lari uyarlanmis, portreleri uyarlanmamis goruyordu - yani
`CLAUDE.md` 10'un *"renk koru modu: 3 palet varyanti"* maddesi yarim
calisiyordu.

Cozum burada: yuklenen her piksel **taban renginden adina**, adindan
da **aktif varyantin rengine** cevriliyor. Palet modu degisince
onbellek atiliyor (`src/art/caches.py`) ve dosya yeniden esleniyor.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pygame

from src.art import palette

# Palet disi renk bulununca bir kez uyar - her karede degil.
_warned: set[str] = set()


def base_palette_lookup() -> dict[tuple[int, int, int], str]:
    """Taban renk -> ad. Sanat bu palette uretiliyor."""
    return {tuple(rgb): name
            for name, rgb in palette._BASE_COLORS.items()}


def off_palette(image: pygame.Surface) -> int:
    """Kac piksel **taban** paletin disinda. Sifir olmali.

    Aktif palete bakmak yanlis: renk korlugu modu acikken her piksel
    "disarida" gorunur ve uyari her acilista yanar. Bir uyari her
    zaman yaniyorsa uyari degildir.
    """
    rgb = pygame.surfarray.array3d(image)
    alpha = pygame.surfarray.array_alpha(image)
    solid = rgb[alpha > 8]
    if solid.size == 0:
        return 0
    allowed = base_palette_lookup()
    unique = np.unique(solid.reshape(-1, 3), axis=0)
    missing = [tuple(int(v) for v in c) for c in unique
               if tuple(int(v) for v in c) not in allowed]
    if not missing:
        return 0
    # Kac PIKSEL etkileniyor - kac renk degil. Tek bir yanlis renk
    # binlerce pikseli boyayabilir ve rapor bunu gostermeli.
    count = 0
    for colour in missing:
        count += int((solid == np.array(colour)).all(axis=-1).sum())
    return count


def remap_to_active(image: pygame.Surface) -> pygame.Surface:
    """Taban paletteki gorseli **aktif** palete cevirir.

    Renk korlugu modu kapaliyken hicbir sey degismiyor ve kopya bile
    alinmiyor - varsayilan durumda maliyeti sifir.
    """
    if palette.active_mode() == "none":
        return image

    lookup = base_palette_lookup()
    result = image.copy()
    rgb = pygame.surfarray.pixels3d(result)
    unique = np.unique(rgb.reshape(-1, 3), axis=0)
    for colour in unique:
        key = tuple(int(v) for v in colour)
        name = lookup.get(key)
        if name is None:
            continue
        target = palette.color(name)
        if target == key:
            continue
        mask = (rgb == np.array(key)).all(axis=-1)
        rgb[mask] = target
    del rgb
    return result


def load_art(path: Path, name: str, expect: tuple[int, int] | None = None,
             alpha: bool = True) -> pygame.Surface | None:
    """Bir varlik PNG'si yukler, dogrular ve aktif palete cevirir.

    Dosya yoksa `None` - cagiran prosedurel uretime devam ediyor.
    Bozuk dosya da `None`: bir varligin okunamamasi oyunu durdurmamali.
    """
    if not path.exists():
        return None
    try:
        image = pygame.image.load(str(path))
        image = image.convert_alpha() if alpha else image.convert()
    except pygame.error:
        return None

    if expect is not None and image.get_size() != expect and name not in _warned:
        _warned.add(name)
        print(f"[sanat] {path.name}: {image.get_size()} - beklenen {expect}. "
              f"Oyun kullaniyor ama olcek kayabilir. Duzeltmek icin: "
              f"python tools/import_art.py {path} --tur portre --ad {name}")

    if name not in _warned:
        count = off_palette(image)
        if count:
            _warned.add(name)
            print(f"[sanat] {path.name}: {count} piksel TABAN paletin "
                  f"disinda. Duzeltmek icin: "
                  f"python tools/quantize.py {path}")

    return remap_to_active(image)


def clear_warnings() -> None:
    _warned.clear()
