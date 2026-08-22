"""Prosedurel karakter uretimi - tek iskelet, cok karakter.

Sprite'lar PNG olarak elle cizilmez; burada **fonksiyon olarak** uretilir
(CLAUDE.md 6). Rey, Ardo ve insansi dusmanlar ayni iskeletten cikar:
tutarlilik garanti, varyasyon ucuz.

Bir karakter iki seyden ibaret:
  * **CharSpec** - oranlar, golge zincirleri, ozellikler (sac, pelerin, silah)
  * **Pose**     - eklem acilari. Animasyon, poz ureten bir fonksiyondur.

Stil sozlesmesi (CLAUDE.md 6) burada otomatik uygulanir:
  * Isik sol ustten          -> `Canvas.shade()`
  * Kontur en koyu 2. renk   -> `Canvas.outline("shadow", 1)`
  * Yuz: 2 piksel goz, agiz yok
  * Golge: karakterin altinda 1 elips
  * Animasyon hissi 8 FPS    -> her sanat karesi ~7 oyun karesi

Cizim sirasi: golge -> sirt saci -> arka uzuvlar -> govde -> on uzuvlar ->
kafa -> silah. Arka uzuvler bir basamak koyu cizilir; derinlik bundan gelir.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from src.art.forge import Canvas

TAU = math.tau


@dataclass(frozen=True)
class CharSpec:
    """Bir karakterin oranlari, renkleri ve ozellikleri."""

    name: str
    # Hucre karakterden buyuktur: silahin savrulmasina yer birakir.
    cell_width: int = 48
    cell_height: int = 40
    foot_y: int = 34                 # Taban cizgisi (hucre icinde)

    # Oranlar (piksel)
    head_radius: float = 4.0
    torso_height: float = 7.2
    torso_width: float = 6.4
    thigh: float = 4.8
    shin: float = 4.8
    upper_arm: float = 4.0
    fore_arm: float = 4.0
    limb_width: float = 2.4
    shoulder_width: float = 5.2

    # Golge zincirleri
    skin: str = "skin_tan"
    hair: str = "hair_dark"
    cloth: str = "cloth_blue"
    cloth_dark: str = "shadow"
    armor: str = "steel"
    accent: str = "gore"
    weapon_chain: str = "steel"

    # Ozellikler
    long_hair: bool = False
    curly_hair: bool = False
    hair_length: float = 0.0
    hood: bool = False
    skull: bool = False
    cape: bool = False
    horns: bool = False
    pointed_ears: bool = False
    shoulder_pads: bool = False
    # Omuzluklarin rengi - bos ise `armor` kullanilir. Ayri tutulmasinin
    # sebebi: Ardo'nun omuzlugu KURK (acik/soluk gri), zirhi (armor)
    # koyu celik - ayni zincir olsaydi omuzluk siluette armor'la
    # birlesip "kurklu" hissi kaybolurdu.
    shoulder_chain: str = ""
    hem: float = 0.0                 # Belden asagi acilan tunik etegi
    hem_length: float = 5.0
    tattoo: bool = False
    glow_eyes: int = 0
    weapon: str = "none"             # none sword knife club staff


@dataclass
class Pose:
    """Bir karenin eklem durumu. Acilar radyan, 0 = saga, pi/2 = asagi."""

    dx: float = 0.0
    dy: float = 0.0
    lean: float = 0.0
    head_dx: float = 0.0
    head_dy: float = 0.0
    squash: float = 1.0

    leg_back: tuple[float, float] = (math.pi / 2, 0.0)
    leg_front: tuple[float, float] = (math.pi / 2, 0.0)
    arm_back: tuple[float, float] = (math.pi / 2, 0.15)
    arm_front: tuple[float, float] = (math.pi / 2, 0.15)

    weapon_angle: float = 0.0
    weapon_hand: str = "front"
    cape_sway: float = 0.0


# --- Parca cizicileri -------------------------------------------------------
def _draw_shadow(canvas: Canvas, cx: float, foot_y: float,
                 width: float) -> None:
    """Karakterin altinda tek elips - stil sozlesmesi geregi."""
    canvas.ellipse(cx, foot_y + 1, width * 0.75, 1.6, "shadow", 1)


def _draw_leg(canvas: Canvas, hx: float, hy: float, hip_angle: float,
              knee_angle: float, spec: CharSpec, chain: str,
              step: int) -> tuple[float, float]:
    kx, ky = canvas.limb(hx, hy, hip_angle, spec.thigh, spec.limb_width,
                         chain, step)
    fx, fy = canvas.limb(kx, ky, hip_angle + knee_angle, spec.shin,
                         spec.limb_width * 0.9, chain, step)
    canvas.line(fx - 1.0, fy, fx + 1.6, fy, spec.limb_width * 0.8,
                spec.cloth_dark, max(0, step))
    return fx, fy


def _draw_arm(canvas: Canvas, sx: float, sy: float, shoulder_angle: float,
              elbow_angle: float, spec: CharSpec, chain: str,
              step: int) -> tuple[float, float]:
    ex, ey = canvas.limb(sx, sy, shoulder_angle, spec.upper_arm,
                         spec.limb_width * 0.85, chain, step)
    skin_step = 2 if step >= 2 else 1
    hx, hy = canvas.limb(ex, ey, shoulder_angle + elbow_angle, spec.fore_arm,
                         spec.limb_width * 0.75, spec.skin, skin_step)
    return hx, hy


def _draw_weapon(canvas: Canvas, hx: float, hy: float, angle: float,
                 spec: CharSpec) -> None:
    kind = spec.weapon
    if kind == "none":
        return
    chain = spec.weapon_chain
    if kind == "sword":
        tip_x = hx + math.cos(angle) * 13
        tip_y = hy + math.sin(angle) * 13
        canvas.taper(hx, hy, tip_x, tip_y, 3.2, 0.9, chain, 3)
        guard = angle + math.pi / 2
        canvas.line(hx + math.cos(guard) * 2, hy + math.sin(guard) * 2,
                    hx - math.cos(guard) * 2, hy - math.sin(guard) * 2,
                    1.8, "brass", 2)
        canvas.line(hx, hy, hx - math.cos(angle) * 3, hy - math.sin(angle) * 3,
                    2.0, "leather", 2)
    elif kind == "knife":
        tip_x = hx + math.cos(angle) * 7
        tip_y = hy + math.sin(angle) * 7
        canvas.taper(hx, hy, tip_x, tip_y, 2.4, 0.8, "bone_pale", 2)
        canvas.line(hx, hy, hx - math.cos(angle) * 2, hy - math.sin(angle) * 2,
                    2.0, "leather", 1)
    elif kind == "club":
        tip_x = hx + math.cos(angle) * 11
        tip_y = hy + math.sin(angle) * 11
        canvas.taper(hx, hy, tip_x, tip_y, 2.2, 4.6, "leather", 1)
        canvas.disc(tip_x, tip_y, 2.6, "leather", 2)
    elif kind == "staff":
        tip_x = hx + math.cos(angle) * 14
        tip_y = hy + math.sin(angle) * 14
        canvas.line(hx, hy, tip_x, tip_y, 2.0, "leather", 1)
        canvas.disc(tip_x, tip_y, 2.4, "arcane", 3, glow=200)


def _draw_back_hair(canvas: Canvas, cx: float, cy: float, spec: CharSpec,
                    sway: float) -> None:
    """Sirta dokulen sac perdesi. **Govdeden once cizilir.**

    Sonra cizilirse sac gogsun onune duser ve karakter kocaman koyu bir bloga
    doner. Once cizilince govde on kismi kapatir, geriye omuz disinda kalan
    kisim gorunur - dogru olan budur.
    """
    if not spec.long_hair or spec.skull:
        return
    radius = spec.head_radius
    length = max(4.0, spec.hair_length)
    for i in range(int(length)):
        t = i / max(1.0, length - 1)
        y = cy + radius * 0.15 + i
        # Uc kokten daha cok savrulur (t^2).
        x = cx - radius * 0.40 - sway * t * t * 2.0
        half = radius * (0.72 - 0.16 * t)
        # Her ucuncu satir bir basamak acik: duz sacta isik seridi.
        step = 2 if i % 3 == 1 else 1
        canvas.fill_rect(int(x - half), int(y), max(2, int(half * 2)), 1,
                         spec.hair, step)


def _draw_head(canvas: Canvas, cx: float, cy: float, spec: CharSpec) -> None:
    radius = spec.head_radius

    if spec.skull:
        canvas.disc(cx, cy, radius, "bone_pale", 2)
        canvas.disc(cx + radius * 0.35, cy + radius * 0.1, radius * 0.28,
                    "shadow", 0)
        canvas.disc(cx - radius * 0.45, cy + radius * 0.1, radius * 0.24,
                    "shadow", 0)
    else:
        canvas.disc(cx, cy, radius, spec.skin, 2)
        if spec.hood:
            # Kukulete **sivri ve arkaya uzanan** bir sekil olmali. Daire
            # cizince siluet uzun sacli kafadan ayirt edilemiyordu - siluet
            # testi bunu yakaladi. Karakterler tek renkte bile ayrilmali.
            canvas.polygon([
                (cx - radius * 1.35, cy + radius * 0.55),
                (cx - radius * 0.30, cy - radius * 1.55),   # tepe, geriye egik
                (cx + radius * 1.15, cy - radius * 0.35),
                (cx + radius * 1.05, cy + radius * 0.45),
            ], spec.cloth, 1)
            # Ensede sarkan uc - siluete belirgin bir cikinti verir.
            canvas.taper(cx - radius * 1.1, cy + radius * 0.2,
                         cx - radius * 1.9, cy + radius * 1.5,
                         radius * 0.9, radius * 0.35, spec.cloth, 0)
            # Kukuletenin golgesi: yuzun ust yarisi karanlikta kalir ama
            # **hepsi degil** - cene/yanak hatti gorunur kalmali, yoksa
            # kukulete bos bir kukuletiye degil govdeye baglanan sekilsiz
            # bir yuma donusuyor (Arda'nin geri bildirimi: "insana
            # benzemiyor"). Yaricap 0.72'den 0.5'e dusuruldu.
            canvas.disc(cx + radius * 0.30, cy + radius * 0.05, radius * 0.50,
                        "shadow", 1)
        else:
            for y in range(int(cy - radius), int(cy)):
                for x in range(int(cx - radius), int(cx + radius + 1)):
                    dx, dy = x + 0.5 - cx, y + 0.5 - cy
                    if dx * dx + dy * dy <= radius * radius:
                        canvas.px(x, y, spec.hair, 1)
            if spec.curly_hair:
                # Kivircik: duz kalotun uzerine tepe cikintilari. Siluette
                # tirtikli bir ust hat birakir - Rey'in duz sacindan bir
                # bakista ayrilir, ki siluet testi bunu istiyor.
                import math as _math
                for i in range(5):
                    angle = _math.pi + _math.pi * (i + 0.5) / 5.0
                    bump_x = cx + _math.cos(angle) * radius * 0.86
                    bump_y = cy + _math.sin(angle) * radius * 0.86
                    canvas.disc(bump_x, bump_y, radius * 0.36, spec.hair,
                                1 if i % 2 else 2)
            if spec.long_hair:
                # Yuzu cerceveleyen tek piksellik tutamlar - kafanin kenarina,
                # yuzun uzerine degil.
                canvas.fill_rect(int(cx + radius * 0.80),
                                 int(cy - radius * 0.35), 1,
                                 max(2, int(radius * 0.9)), spec.hair, 2)
                canvas.fill_rect(int(cx - radius * 1.00),
                                 int(cy - radius * 0.45), 1,
                                 max(2, int(radius * 1.1)), spec.hair, 1)

    _draw_eyes(canvas, cx, cy, spec)

    if spec.pointed_ears:
        # Yanlara ve hafif yukari uzanan sivri kulaklar. Siluete katkisi
        # kucuk ama belirleyici: yuvarlak kafayi kirar, boceksi/kurnaz
        # okunur. `horns`'tan farki yon - boynuz yukari, kulak yana gider.
        canvas.taper(cx - radius * 0.85, cy - radius * 0.15,
                     cx - radius * 1.75, cy - radius * 0.95, 2.0, 0.8,
                     spec.skin, 1)
        canvas.taper(cx + radius * 0.85, cy - radius * 0.15,
                     cx + radius * 1.75, cy - radius * 0.95, 2.0, 0.8,
                     spec.skin, 2)

    if spec.horns:
        canvas.taper(cx - radius * 0.6, cy - radius * 0.7,
                     cx - radius * 1.4, cy - radius * 1.9, 2.2, 0.8,
                     "bone_pale", 2)
        canvas.taper(cx + radius * 0.6, cy - radius * 0.7,
                     cx + radius * 1.4, cy - radius * 1.9, 2.2, 0.8,
                     "bone_pale", 3)


def _draw_eyes(canvas: Canvas, cx: float, cy: float, spec: CharSpec) -> None:
    """Iki piksel goz, agiz yok - stil sozlesmesi."""
    eye_y = int(cy + spec.head_radius * 0.05)
    if spec.glow_eyes:
        canvas.px(int(cx + spec.head_radius * 0.35), eye_y, spec.accent, 3,
                  glow=spec.glow_eyes)
        canvas.px(int(cx - spec.head_radius * 0.5), eye_y, spec.accent, 3,
                  glow=spec.glow_eyes)
        return
    if spec.skull:
        return
    if spec.hood:
        # Kukuletenin golgesi koyu; "hair_dark" gozler o golgeyle ayni
        # tonda kalip kayboluyordu (Arda: "insana benzemiyor" - gozsuz bir
        # kukulete govdeye baglanan sekilsiz bir yumdu). Parlamiyor - bu
        # bir canavar degil, golgede kalan bir insan - ama golgeden
        # **secilecek** kadar acik olmali: soluk bir "bone_pale" pareltisi.
        near_x = int(cx + spec.head_radius * 0.25)
        canvas.fill_rect(near_x, eye_y, 2, 1, "bone_pale", 3)
        canvas.px(int(cx - spec.head_radius * 0.6), eye_y, "bone_pale", 3)
        return
    # Badem goz: 2 piksel genis, ustunde kirpik cizgisi.
    near_x = int(cx + spec.head_radius * 0.25)
    canvas.fill_rect(near_x, eye_y, 2, 1, "hair_dark", 1)
    canvas.px(near_x + 1, eye_y - 1, spec.hair, 1)
    canvas.px(int(cx - spec.head_radius * 0.6), eye_y, "hair_dark", 1)


# --- Ana cizici -------------------------------------------------------------
def draw_humanoid(spec: CharSpec, pose: Pose) -> Canvas:
    """Bir pozu tam sprite'a cevirir."""
    canvas = Canvas(spec.cell_width, spec.cell_height)

    cx = spec.cell_width * 0.5 + pose.dx
    foot_y = spec.foot_y + pose.dy
    leg_length = (spec.thigh + spec.shin) * pose.squash
    hip_y = foot_y - leg_length
    torso_height = spec.torso_height * pose.squash
    shoulder_y = hip_y - torso_height
    shoulder_x = cx + pose.lean * 2.5
    head_x = cx + pose.head_dx
    head_y = shoulder_y - spec.head_radius + 1.5 + pose.head_dy

    _draw_shadow(canvas, spec.cell_width * 0.5, spec.foot_y, spec.torso_width)

    if spec.cape:
        sway = pose.cape_sway
        canvas.polygon([
            (shoulder_x - spec.shoulder_width * 0.7, shoulder_y),
            (shoulder_x + spec.shoulder_width * 0.7, shoulder_y),
            (shoulder_x + spec.shoulder_width * 0.4 - sway * 3, hip_y + 5),
            (shoulder_x - spec.shoulder_width * 0.9 - sway * 5, hip_y + 4),
        ], spec.accent, 1)

    _draw_back_hair(canvas, head_x, head_y, spec, pose.cape_sway)

    # Arka uzuvlar - bir basamak koyu, derinlik bundan gelir.
    _draw_leg(canvas, cx, hip_y, *pose.leg_back, spec, spec.cloth_dark, 1)
    back_hand = _draw_arm(canvas, shoulder_x - 1, shoulder_y + 1,
                          *pose.arm_back, spec, spec.cloth, 1)
    if spec.weapon != "none" and pose.weapon_hand in ("back", "both"):
        _draw_weapon(canvas, back_hand[0], back_hand[1], pose.weapon_angle, spec)

    # Govde
    canvas.polygon([
        (shoulder_x - spec.shoulder_width * 0.5, shoulder_y),
        (shoulder_x + spec.shoulder_width * 0.5, shoulder_y),
        (cx + spec.torso_width * 0.36, hip_y + 1),
        (cx - spec.torso_width * 0.36, hip_y + 1),
    ], spec.cloth, 2)

    if spec.shoulder_pads:
        shoulder_tone = spec.shoulder_chain or spec.armor
        canvas.disc(shoulder_x - spec.shoulder_width * 0.55, shoulder_y + 0.5,
                    2.6, shoulder_tone, 3)
        canvas.disc(shoulder_x + spec.shoulder_width * 0.55, shoulder_y + 0.5,
                    2.6, shoulder_tone, 2)

    if spec.tattoo:
        # Sag kopruck kemiginin altinda kucuk isaret. Bu olcekte bir geyik
        # cizilemez - geyik prologda tam boyutta cikar.
        tx = int(shoulder_x + spec.shoulder_width * 0.18)
        ty = int(shoulder_y + 2)
        canvas.px(tx, ty, spec.accent, 3)
        canvas.px(tx, ty + 1, spec.accent, 2)
        canvas.px(tx + 1, ty - 1, spec.accent, 2)

    canvas.fill_rect(int(cx - spec.torso_width * 0.4), int(hip_y - 1),
                     int(spec.torso_width * 0.8) + 1, 1, spec.armor, 1)

    # On uzuvlar
    _draw_leg(canvas, cx, hip_y, *pose.leg_front, spec, spec.cloth, 2)

    if spec.hem > 0.0:
        sway = pose.cape_sway * 0.6
        canvas.polygon([
            (cx - spec.torso_width * 0.38, hip_y - 1),
            (cx + spec.torso_width * 0.38, hip_y - 1),
            (cx + spec.hem * 0.5 - sway, hip_y + spec.hem_length),
            (cx - spec.hem * 0.5 - sway, hip_y + spec.hem_length),
        ], spec.cloth, 1)

    _draw_head(canvas, head_x, head_y, spec)
    front_hand = _draw_arm(canvas, shoulder_x + 1, shoulder_y + 1,
                           *pose.arm_front, spec, spec.cloth, 2)
    if spec.weapon != "none" and pose.weapon_hand in ("front", "both"):
        _draw_weapon(canvas, front_hand[0], front_hand[1], pose.weapon_angle,
                     spec)

    canvas.shade()
    canvas.outline("shadow", 1)
    return canvas
