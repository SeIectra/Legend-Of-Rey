"""Palet - 32 renk, tek gercek kaynak.

Bu modul renk **tanimlamaz**; `tools/palette.json` dosyasini okur. Boylece
oyun kodu ile asset boru hatti (quantize, shade, outline) ayni renkleri
kullanir ve tutarsizlik yapisal olarak imkansiz hale gelir.

Kod renk yerine **rol** ile konusur:

    palette.role("enemy_tell")     # dogru
    palette.color("danger")        # kabul edilebilir
    (216, 76, 34)                  # YASAK

Rol katmani sayesinde "dusman tell rengini degistir" tek satirlik bir
JSON degisikligi olur, kod hic degismez.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

RGB = tuple[int, int, int]

_PALETTE_PATH = Path(__file__).resolve().parents[2] / "tools" / "palette.json"
EXPECTED_COLOR_COUNT = 32


class PaletteError(RuntimeError):
    """Palet dosyasi bozuk ya da eksik."""


def _load_raw() -> dict:
    try:
        data = json.loads(_PALETTE_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PaletteError(f"palet dosyasi yok: {_PALETTE_PATH}") from exc
    except ValueError as exc:
        raise PaletteError(f"palet dosyasi bozuk: {exc}") from exc

    colors = data.get("colors")
    if not isinstance(colors, dict):
        raise PaletteError("palet dosyasinda 'colors' sozlugu yok")
    if len(colors) != EXPECTED_COLOR_COUNT:
        # Sessizce gecmiyoruz: 32 renk bir tasarim karari, kaza sonucu
        # 33'e cikmasi tutarlilik sozlesmesinin delindigi anlamina gelir.
        raise PaletteError(
            f"palet {len(colors)} renk iceriyor, {EXPECTED_COLOR_COUNT} olmali")
    return data


_RAW = _load_raw()

COLORS: dict[str, RGB] = {
    name: (int(v[0]), int(v[1]), int(v[2])) for name, v in _RAW["colors"].items()
}
RAMPS: dict[str, tuple[str, ...]] = {
    name: tuple(steps) for name, steps in _RAW.get("ramps", {}).items()
}
PARTICLE_PATHS: dict[str, tuple[str, ...]] = {
    name: tuple(steps) for name, steps in _RAW.get("particle_paths", {}).items()
}
# Golge zincirleri rampa asabilir: sac koyudan aciga giderken earth'ten
# flesh'e gecer. 32 renk sinirini bozmadan her govde parcasina 4 basamak
# tonlama saglar - sinirli palette karakter cizmenin dogru yolu budur.
SHADE_CHAINS: dict[str, tuple[str, ...]] = {
    name: tuple(steps) for name, steps in _RAW.get("shade_chains", {}).items()
}
ROLES: dict[str, str] = dict(_RAW.get("roles", {}))
OUTLINE_NAME: str = _RAW.get("outline", "ink")

# Sirali liste - quantize.py en yakin rengi bunun uzerinde arar.
ORDERED_NAMES: tuple[str, ...] = tuple(COLORS.keys())
ORDERED_COLORS: tuple[RGB, ...] = tuple(COLORS[n] for n in ORDERED_NAMES)


# --- Erisim -----------------------------------------------------------------
def color(name: str) -> RGB:
    """Ada gore renk. Bilinmeyen ad sessizce gecmez - yaziim hatasi
    yuzunden yanlis renk kullanmak, hata almaktan daha kotudur."""
    try:
        return COLORS[name]
    except KeyError as exc:
        raise PaletteError(f"palette disi renk: {name!r}") from exc


def role(name: str) -> RGB:
    """Anlamsal role gore renk (ornegin 'enemy_tell')."""
    try:
        return COLORS[ROLES[name]]
    except KeyError as exc:
        raise PaletteError(f"tanimsiz rol: {name!r}") from exc


def role_name(name: str) -> str:
    """Rolun isaret ettigi renk adi - shade/outline araclari icin."""
    try:
        return ROLES[name]
    except KeyError as exc:
        raise PaletteError(f"tanimsiz rol: {name!r}") from exc


def outline() -> RGB:
    """Kontur rengi: paletin en koyu 2. rengi. Siyah degil (CLAUDE.md 6)."""
    return color(OUTLINE_NAME)


def ramp(name: str) -> tuple[str, ...]:
    """Bir rampanin renk adlari, koyudan aciga."""
    try:
        return RAMPS[name]
    except KeyError as exc:
        raise PaletteError(f"tanimsiz rampa: {name!r}") from exc


def ramp_color(name: str, step: int) -> RGB:
    """Rampadan renk al; indeks tasarsa uca kirpilir."""
    steps = ramp(name)
    return color(steps[max(0, min(step, len(steps) - 1))])


def shade_step(ramp_name: str, step: int, delta: int) -> RGB:
    """Rampada `delta` kadar aydinlat (+) ya da koyulastir (-).

    shade.py'nin sol-ust isik kurali bunu kullanir: isik alan kenar +1,
    golgede kalan -1.
    """
    return ramp_color(ramp_name, step + delta)


def chain(name: str) -> tuple[str, ...]:
    """Golge zincirinin renk adlari, koyudan aciga."""
    try:
        return SHADE_CHAINS[name]
    except KeyError as exc:
        raise PaletteError(f"tanimsiz golge zinciri: {name!r}") from exc


def chain_color(name: str, step: int) -> RGB:
    """Zincirden renk al; indeks tasarsa uca kirpilir.

    Sprite uretimi bunu kullanir: parca adiyla (`hair_dark`) ve basamakla
    (0 en koyu, 3 en acik) calisir, gercek renk adini hic bilmez.
    """
    steps = chain(name)
    return color(steps[max(0, min(step, len(steps) - 1))])


def chain_depth(name: str) -> int:
    return len(chain(name))


def particle_path(name: str) -> tuple[RGB, ...]:
    """Parcacik renk yolu: omur boyunca izlenecek renk dizisi."""
    try:
        return tuple(color(n) for n in PARTICLE_PATHS[name])
    except KeyError as exc:
        raise PaletteError(f"tanimsiz parcacik yolu: {name!r}") from exc


def path_color(name: str, life_ratio: float) -> RGB:
    """Parcacik yolundan yasam oranina gore renk.

    `life_ratio` 1.0 = yeni dogmus (yolun basi), 0.0 = sonmek uzere (sonu).
    """
    steps = particle_path(name)
    if not steps:
        return color("bone")
    ratio = max(0.0, min(1.0, life_ratio))
    index = int((1.0 - ratio) * (len(steps) - 1) + 0.5)
    return steps[index]


# --- Yardimcilar ------------------------------------------------------------
@lru_cache(maxsize=4096)
def nearest_name(rgb: RGB) -> str:
    """Verilen renge en yakin palet rengi. quantize.py'nin cekirdegi.

    Oklid mesafesi kullaniyoruz - algisal olarak mukemmel degil ama piksel
    artta yeterli ve hizli. Onbellek sayesinde ayni renk bir kez hesaplanir.
    """
    red, green, blue = rgb
    best_name = ORDERED_NAMES[0]
    best_distance = float("inf")
    for name, (pr, pg, pb) in zip(ORDERED_NAMES, ORDERED_COLORS):
        distance = (red - pr) ** 2 + (green - pg) ** 2 + (blue - pb) ** 2
        if distance < best_distance:
            best_distance = distance
            best_name = name
    return best_name


def nearest(rgb: RGB) -> RGB:
    return COLORS[nearest_name(rgb)]


def luminance(rgb: RGB) -> float:
    """Algilanan parlaklik 0..1. En koyu 2. rengi bulmak icin kullanilir."""
    r, g, b = (channel / 255.0 for channel in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def darkest_names(count: int = 2) -> list[str]:
    """Paletin en koyu `count` rengi, koyudan aciga."""
    return sorted(ORDERED_NAMES, key=lambda n: luminance(COLORS[n]))[:count]


def with_alpha(rgb: RGB, alpha: int) -> tuple[int, int, int, int]:
    return (rgb[0], rgb[1], rgb[2], max(0, min(255, alpha)))


def describe() -> str:
    """Hata ayiklama ozeti."""
    return (f"{len(COLORS)} renk, {len(RAMPS)} rampa, "
            f"{len(PARTICLE_PATHS)} parcacik yolu, {len(ROLES)} rol · "
            f"kontur={OUTLINE_NAME}")
