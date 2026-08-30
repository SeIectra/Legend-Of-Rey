"""Ayna ve isin - Bolum 11'in mekanigi.

`docs/yapi.md` mekanik havuzu 7: *"Isini yonlendir, golge yaratiklari
yak."* B11: *"Aynalari cevirerek isini yaratiklara yonlendir."*

## Isin **isiktan yapiliyor**

Yeni bir isik turu eklenmedi. `LightState` dairesel kaynaklar tutuyor
(`radius_at`, `in_light`) ve butun oyun onu boyle soruyor - ozellikle
`ShadowShambler`, Bolum 3'ten beri *"isikta miyim"* diye ona bakiyor.

Isin, yolu boyunca dizilmis **kucuk dairesel kaynaklardan** olusuyor.
Kazanc buyuk:

    * `in_light` degismiyor -> golge yaratigi bedavaya calisiyor
    * `art/lighting.render` degismiyor -> isin gorunuyor
    * bir "isin sekli" matematigi hic yazilmiyor

Alternatif bir `BeamSource` tipi yazip iki yerde daha dallanmakti.
Isini isiktan yapmak hem daha az kod hem daha dogru: isin zaten isik.

## Tile bazli izleme

`docs/yapi.md` 113: *"Vana, plaka, ayna, can - hepsi tile bazli durum
makinesi."* Isin da oyle: tile tile ilerliyor, aynaya carpinca yon
degistiriyor, duvara carpinca duruyor.

Kayan noktali bir isin/duvar kesisimi yazmak daha "dogru" olurdu ve
daha kotu: piksel artta 16 piksellik bir izgara zaten var, ve oyuncu
bulmacayi tile olarak dusunuyor.

## Dongu koruması

Iki ayna birbirine bakiyorsa isin sonsuza kadar gider. `MAX_STEPS`
onu kesiyor - ve bu bir hata durumu degil **gecerli bir bulmaca
durumu**: oyuncu iki aynayi karsi karsiya getirebilir ve isin
"kaybolur". Cozum degil ama cokme de degil.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.config import TILE_SIZE

# Isinin en fazla kac tile ilerledigi. Odalar ~30 tile; 200 hem
# yansimalara hem donguye karsi bol bir sinir.
MAX_STEPS = 200

# Isin boyunca kac tile'da bir isik kaynagi konuyor ve yaricapi ne.
# Bir tile'da bir kaynak: bosluk kalmiyor, sayi da makul (bir isin en
# fazla 200 kaynak, `LightState` sozluk tutuyor).
BEAM_LIGHT_RADIUS = 13.0

# Yonler: (dx, dy) tile cinsinden.
RIGHT = (1, 0)
LEFT = (-1, 0)
UP = (0, -1)
DOWN = (0, 1)

# Ayna yansimalari. Iki tur var, dort degil: 16 pikselde dort yonlu bir
# ayna okunmuyor ve oyuncu hangisine baktigini anlamiyor.
#
#   "/"  saga giden yukari doner
#   "\"  saga giden asagi doner
SLASH = "/"
BACKSLASH = "\\"

_REFLECT = {
    SLASH: {RIGHT: UP, UP: RIGHT, LEFT: DOWN, DOWN: LEFT},
    BACKSLASH: {RIGHT: DOWN, DOWN: RIGHT, LEFT: UP, UP: LEFT},
}


@dataclass
class Mirror:
    """Cevrilebilir ayna. Iki durumu var."""

    tile_x: int
    tile_y: int
    kind: str = SLASH
    # Sabit aynalar cevrilemiyor - bulmacanin degismeyen parcalari.
    fixed: bool = False
    # Cevirme animasyonu icin kalan kare.
    spin: int = 0

    @property
    def rect_topleft(self) -> tuple[int, int]:
        return (self.tile_x * TILE_SIZE, self.tile_y * TILE_SIZE)

    def rotate(self) -> bool:
        """Aynayi cevirir. Sabitse False."""
        if self.fixed:
            return False
        self.kind = BACKSLASH if self.kind is SLASH else SLASH
        self.spin = SPIN_FRAMES
        return True

    def update(self) -> None:
        if self.spin > 0:
            self.spin -= 1

    def reflect(self, direction: tuple[int, int]) -> tuple[int, int] | None:
        return _REFLECT[self.kind].get(direction)


# Ayna cevirme animasyonu (kare).
SPIN_FRAMES = 12


@dataclass
class BeamPath:
    """Isinin izledigi yol - tile listesi + kirilma noktalari."""

    tiles: list[tuple[int, int]] = field(default_factory=list)
    # Yansidigi aynalarin tile konumlari - cizim bunlari vurguluyor.
    bounces: list[tuple[int, int]] = field(default_factory=list)
    # Isin bir hedefe vardi mi (`targets` verildiyse).
    hit: set[tuple[int, int]] = field(default_factory=set)


def trace(tilemap, mirrors, start: tuple[int, int],
          direction: tuple[int, int],
          targets: set[tuple[int, int]] | None = None) -> BeamPath:
    """Isini tile tile izler.

    `start` kaynagin tile'i (isin ondan **sonraki** tile'dan basliyor),
    `direction` baslangic yonu. Duvara carpinca duruyor, aynaya
    carpinca donuyor.
    """
    lookup = {(m.tile_x, m.tile_y): m for m in mirrors}
    path = BeamPath()
    x, y = start
    dx, dy = direction

    for _ in range(MAX_STEPS):
        x, y = x + dx, y + dy
        if not (0 <= x < tilemap.width and 0 <= y < tilemap.height):
            break
        mirror = lookup.get((x, y))
        if mirror is not None:
            path.tiles.append((x, y))
            path.bounces.append((x, y))
            turned = mirror.reflect((dx, dy))
            if turned is None:
                break                       # aynanin arkasi - isin oluyor
            dx, dy = turned
            continue
        if tilemap.is_solid(x, y):
            break                           # duvar
        path.tiles.append((x, y))
        if targets and (x, y) in targets:
            path.hit.add((x, y))
    return path


def apply_light(light, path: BeamPath, key_prefix: str = "beam") -> None:
    """Isini `LightState`'e **kaynak dizisi** olarak yaziyor.

    Once eski isinin kaynaklari siliniyor: isin her karede yeniden
    izleniyor ve bayat kaynaklar kalirsa ayna cevrildikten sonra eski
    yol aydinlik kalirdi - golge yaratigi yanlis yerde olurdu.
    """
    clear_light(light, key_prefix)
    for index, (x, y) in enumerate(path.tiles):
        light.set_static(f"{key_prefix}{index}",
                         x * TILE_SIZE + TILE_SIZE * 0.5,
                         y * TILE_SIZE + TILE_SIZE * 0.5,
                         BEAM_LIGHT_RADIUS)


def clear_light(light, key_prefix: str = "beam") -> None:
    light.remove_prefix(key_prefix)
