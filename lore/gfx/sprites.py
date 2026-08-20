"""Karakter sprite'larinin prosedurel uretimi.

Tek bir insansi iskelet (rig) tum karakterleri besliyor. Bir karakter iki seyden
ibaret:

  * **CharSpec** - oranlar (boy, kafa yaricapi, uzuv kalinligi), palet rampalari
    ve ozellikler (kukulete, boynuz, pelerin, silah).
  * **Pose**     - eklem acilari. Animasyon, poz ureten bir fonksiyondan ibaret.

Bu ayrimin bedeli dusuk, getirisi buyuk: yeni bir dusman eklemek 6 satirlik bir
CharSpec demek. Ayni iskelet Rey'i de, iskeleti de, boss'u da ciziyor; hareket
dili bu yuzden tum oyunda tutarli.

Cizim sirasi onemli: arka uzuvlar -> govde -> on uzuvlar. Arka uzuvler bir
basamak koyu cizilir; derinlik hissi bundan geliyor.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

import pygame

from lore.gfx.forge import Canvas, flip_h

TAU = math.tau


# --- Karakter tanimi --------------------------------------------------------
@dataclass
class CharSpec:
    name: str
    cell_w: int = 32
    cell_h: int = 32
    foot_y: int = 29            # Taban cizgisi (hucre icinde)

    # Oranlar
    head_r: float = 4.0
    torso_h: float = 7.0
    torso_w: float = 7.0
    thigh: float = 4.5
    shin: float = 4.5
    upper_arm: float = 4.0
    fore_arm: float = 4.0
    limb_w: float = 2.6
    shoulder_w: float = 5.0

    # Palet rampalari
    skin: str = "flesh"
    skin_step: int = 3          # Ten tonu: rampanin kacinci basamagi (0 koyu, 4 acik)
    cloth: str = "azure"
    cloth_dark: str = "ink"
    armor: str = "stone"
    hair: str = "earth"
    hair_step: int = 2
    accent: str = "ember"

    # Ozellikler
    hood: bool = False
    horns: bool = False
    skull: bool = False
    long_hair: bool = False     # Sirta dokulen sac perdesi
    hair_length: float = 0.0    # Kac piksel asagi iner (long_hair ile birlikte)
    eye_ramp: str = "ink"       # Goz rengi rampasi
    eye_step: int = 0
    almond_eyes: bool = False   # Tek piksel yerine 2 piksellik badem goz
    hem: float = 0.0            # Belden asagi acilan tunik etegi (genislik)
    hem_len: float = 4.0
    tattoo: str = ""            # "deer" -> gogse kucuk bir isaret
    cape: bool = False
    tail: bool = False
    pointed_ears: bool = False
    shoulder_pads: bool = False
    one_eye: bool = False
    glow_eyes: int = 0          # 0 = kapali, >0 = parlaklik
    weapon: str = "none"        # none sword knife bow club staff scythe
    scale: float = 1.0


@dataclass
class Pose:
    """Bir karenin eklem durumu. Acilar radyan, 0 = saga, pi/2 = asagi."""
    dx: float = 0.0
    dy: float = 0.0
    lean: float = 0.0           # Govde egimi (+ ileri)
    head_dx: float = 0.0
    head_dy: float = 0.0
    squash: float = 1.0         # <1 basik, >1 uzun

    # (kalca acisi, diz bukumu)
    leg_back: tuple[float, float] = (math.pi / 2, 0.0)
    leg_front: tuple[float, float] = (math.pi / 2, 0.0)
    # (omuz acisi, dirsek bukumu)
    arm_back: tuple[float, float] = (math.pi / 2, 0.15)
    arm_front: tuple[float, float] = (math.pi / 2, 0.15)

    weapon_angle: float = 0.0
    weapon_hand: str = "front"  # front | back | both
    cape_sway: float = 0.0


# --- Cizim ------------------------------------------------------------------
def _draw_leg(c: Canvas, hx: float, hy: float, hip_a: float, knee_a: float,
              spec: CharSpec, ramp: str, step: int) -> tuple[float, float]:
    kx, ky = c.limb(hx, hy, hip_a, spec.thigh, spec.limb_w, ramp, step)
    fx, fy = c.limb(kx, ky, hip_a + knee_a, spec.shin, spec.limb_w * 0.9, ramp, step)
    # Ayak: kisa yatay parca
    c.line(fx - 1.0, fy, fx + 1.6, fy, spec.limb_w * 0.8, spec.cloth_dark, step)
    return fx, fy


def _draw_arm(c: Canvas, sx: float, sy: float, sh_a: float, el_a: float,
              spec: CharSpec, ramp: str, step: int) -> tuple[float, float]:
    ex, ey = c.limb(sx, sy, sh_a, spec.upper_arm, spec.limb_w * 0.85, ramp, step)
    # On kol ten rengi. Arka koldaki bir basamak koyu tutuluyor ki derinlik
    # siralamasi ten renginde de bozulmasin.
    skin_step = spec.skin_step if step >= 3 else max(0, spec.skin_step - 1)
    hx, hy = c.limb(ex, ey, sh_a + el_a, spec.fore_arm, spec.limb_w * 0.75,
                    spec.skin, skin_step)
    return hx, hy


def _draw_weapon(c: Canvas, hx: float, hy: float, angle: float,
                 spec: CharSpec) -> None:
    kind = spec.weapon
    if kind == "none":
        return
    if kind == "sword":
        tip_x = hx + math.cos(angle) * 13
        tip_y = hy + math.sin(angle) * 13
        c.taper(hx, hy, tip_x, tip_y, 3.2, 0.9, "stone", 4)
        # Kabza ve balcak
        guard = angle + math.pi / 2
        c.line(hx + math.cos(guard) * 2, hy + math.sin(guard) * 2,
               hx - math.cos(guard) * 2, hy - math.sin(guard) * 2, 1.8, "gold", 3)
        c.line(hx, hy, hx - math.cos(angle) * 3, hy - math.sin(angle) * 3,
               2.0, "earth", 2)
    elif kind == "knife":
        tip_x = hx + math.cos(angle) * 7
        tip_y = hy + math.sin(angle) * 7
        c.taper(hx, hy, tip_x, tip_y, 2.4, 0.8, "bone", 4)
        c.line(hx, hy, hx - math.cos(angle) * 2, hy - math.sin(angle) * 2,
               2.0, "earth", 1)
    elif kind == "club":
        tip_x = hx + math.cos(angle) * 11
        tip_y = hy + math.sin(angle) * 11
        c.taper(hx, hy, tip_x, tip_y, 2.2, 4.6, "earth", 2)
        c.disc(tip_x, tip_y, 2.6, "earth", 3)
        for i in range(3):
            a = angle + i * TAU / 3
            c.px(int(tip_x + math.cos(a) * 3), int(tip_y + math.sin(a) * 3),
                 "bone", 4)
    elif kind == "bow":
        for i in range(-4, 5):
            t = i / 4.0
            bow_a = angle + t * 1.5
            bx = hx + math.cos(bow_a) * 6
            by = hy + math.sin(bow_a) * 6
            c.px(int(bx), int(by), "earth", 3)
        c.line(hx + math.cos(angle + 1.5) * 6, hy + math.sin(angle + 1.5) * 6,
               hx + math.cos(angle - 1.5) * 6, hy + math.sin(angle - 1.5) * 6,
               1.0, "bone", 3)
    elif kind == "staff":
        tip_x = hx + math.cos(angle) * 14
        tip_y = hy + math.sin(angle) * 14
        c.line(hx, hy, tip_x, tip_y, 2.0, "earth", 2)
        c.disc(tip_x, tip_y, 2.4, "violet", 4, glow=200)
    elif kind == "scythe":
        mid_x = hx + math.cos(angle) * 14
        mid_y = hy + math.sin(angle) * 14
        c.line(hx, hy, mid_x, mid_y, 2.0, "ink", 3)
        for i in range(8):
            t = i / 7.0
            a = angle - 1.6 + t * 1.9
            c.px(int(mid_x + math.cos(a) * 7), int(mid_y + math.sin(a) * 7),
                 "bone", 4)
            c.px(int(mid_x + math.cos(a) * 6), int(mid_y + math.sin(a) * 6),
                 "bone", 3)


def _draw_back_hair(c: Canvas, cx: float, cy: float, spec: CharSpec,
                    sway: float) -> None:
    """Sirta dokulen sac perdesi.

    **Govdeden once cizilir.** Sonra cizersek sac gogsun onune duser ve
    karakter kocaman siyah bir bloga doner - ilk denemede tam olarak bu oldu.
    Once cizilince govde sacin on kismini kapatir, geriye sadece omuzlarin
    disinda kalan kisim gorunur; dogru olan da budur.

    Duz sac: kivrim yok, genislik asagi dogru cok az daralir, uc kut biter.
    Salinim asagi indikce artar (t^2) - sacin ucu kokunden daha cok savrulur.
    """
    if not spec.long_hair or spec.skull:
        return
    r = spec.head_r
    length = max(4.0, spec.hair_length)
    for i in range(int(length)):
        t = i / max(1.0, length - 1)
        yy = cy + r * 0.15 + i
        # Merkez geriye kayar: sac ensenin arkasindan dokulur, yandan degil.
        xx = cx - r * 0.40 - sway * t * t * 2.0
        # Kafadan dar tutulur. Genis birakinca sac kafayi cerceveliyor ve
        # kukulete gibi okunuyor; siluetin tepesi sac degil, kafa olmali.
        half = r * (0.72 - 0.16 * t)
        # Her ucuncu satirda bir basamak acik: duz sacta isigin olusturdugu
        # dikey parlama seridi. Tek renk kutle "peruk" gibi duruyor.
        step = spec.hair_step + (1 if i % 3 == 1 else 0)
        c.fill_rect(int(xx - half), int(yy), max(2, int(half * 2)), 1,
                    spec.hair, min(4, step))


def _draw_head(c: Canvas, cx: float, cy: float, spec: CharSpec,
               facing_squint: bool = False, hair_sway: float = 0.0) -> None:
    r = spec.head_r

    if spec.skull:
        c.disc(cx, cy, r, "bone", 3)
        c.disc(cx + r * 0.35, cy + r * 0.1, r * 0.28, "ink", 0)     # goz cukuru
        c.disc(cx - r * 0.45, cy + r * 0.1, r * 0.24, "ink", 0)
        c.fill_rect(int(cx - r * 0.5), int(cy + r * 0.55), int(r), 1, "ink", 0)
    else:
        c.disc(cx, cy, r, spec.skin, spec.skin_step)
        if spec.hood:
            # Kukuletenin agzi: yuzun ust yarisi karanlikta kalir.
            c.disc(cx, cy - r * 0.25, r * 1.12, spec.cloth, 2)
            c.disc(cx + r * 0.25, cy + r * 0.15, r * 0.75, "ink", 1)
        else:
            # Sac: kafanin ust yarisi
            for y in range(int(cy - r), int(cy)):
                for x in range(int(cx - r), int(cx + r + 1)):
                    dx, dy = x + 0.5 - cx, y + 0.5 - cy
                    if dx * dx + dy * dy <= r * r:
                        c.px(x, y, spec.hair, spec.hair_step)
            if spec.long_hair:
                # Yuzu cerceveleyen tek piksellik tutamlar. Kafanin *kenarina*
                # cizilir, yuzun uzerine degil - iki piksel genislik yuzu
                # kapatiyor ve maske gibi gorunuyordu.
                c.fill_rect(int(cx + r * 0.80), int(cy - r * 0.35), 1,
                            max(2, int(r * 0.9)), spec.hair, spec.hair_step + 1)
                c.fill_rect(int(cx - r * 1.00), int(cy - r * 0.45), 1,
                            max(2, int(r * 1.1)), spec.hair, spec.hair_step)
        if spec.pointed_ears:
            c.taper(cx - r * 0.9, cy, cx - r * 1.7, cy - r * 0.8, 2.0, 0.8,
                    spec.skin, 2)
            c.taper(cx + r * 0.9, cy, cx + r * 1.7, cy - r * 0.8, 2.0, 0.8,
                    spec.skin, 3)

    # Gozler
    if spec.glow_eyes:
        c.px(int(cx + r * 0.35), int(cy + r * 0.05), spec.accent, 4,
             glow=spec.glow_eyes)
        if not spec.one_eye:
            c.px(int(cx - r * 0.45), int(cy + r * 0.05), spec.accent, 4,
                 glow=spec.glow_eyes)
    elif not spec.skull:
        eye_y = int(cy + r * 0.05)
        if spec.almond_eyes:
            # Badem goz: 2 piksel genis, ustunde bir piksel kirpik/kas cizgisi.
            # Tek piksel goz "nokta" okunur; ikinci piksel bakisa yon verir.
            near_x = int(cx + r * 0.25)
            c.fill_rect(near_x, eye_y, 2, 1, spec.eye_ramp, spec.eye_step)
            c.px(near_x + 1, eye_y - 1, spec.hair, spec.hair_step)
            if not (spec.one_eye or facing_squint):
                c.px(int(cx - r * 0.6), eye_y, spec.eye_ramp, spec.eye_step)
        else:
            c.px(int(cx + r * 0.35), eye_y, spec.eye_ramp, spec.eye_step)
            if not (spec.one_eye or facing_squint):
                c.px(int(cx - r * 0.45), eye_y, spec.eye_ramp, spec.eye_step)

    if spec.horns:
        c.taper(cx - r * 0.6, cy - r * 0.7, cx - r * 1.4, cy - r * 1.9,
                2.2, 0.8, "bone", 3)
        c.taper(cx + r * 0.6, cy - r * 0.7, cx + r * 1.4, cy - r * 1.9,
                2.2, 0.8, "bone", 4)


def draw_character(spec: CharSpec, pose: Pose) -> Canvas:
    """Bir pozu tam sprite'a cevirir."""
    c = Canvas(spec.cell_w, spec.cell_h)

    cx = spec.cell_w * 0.5 + pose.dx
    foot_y = spec.foot_y + pose.dy

    leg_len = (spec.thigh + spec.shin) * pose.squash
    hip_y = foot_y - leg_len
    torso_h = spec.torso_h * pose.squash
    shoulder_y = hip_y - torso_h
    shoulder_x = cx + pose.lean * 2.5
    head_x = cx + pose.head_dx
    head_y = shoulder_y - spec.head_r + 1.5 + pose.head_dy

    # --- Pelerin (en arkada) -----------------------------------------------
    if spec.cape:
        sway = pose.cape_sway
        points = [
            (shoulder_x - spec.shoulder_w * 0.7, shoulder_y),
            (shoulder_x + spec.shoulder_w * 0.7, shoulder_y),
            (shoulder_x + spec.shoulder_w * 0.4 - sway * 3, hip_y + 5),
            (shoulder_x - spec.shoulder_w * 0.9 - sway * 5, hip_y + 4),
        ]
        c.polygon(points, spec.accent, 1)

    # --- Sirt saci (govdeden once: gogsun onune dusmesin) -------------------
    _draw_back_hair(c, head_x, head_y, spec, pose.cape_sway)

    # --- Arka uzuvlar (bir basamak koyu = derinlik) ------------------------
    _draw_leg(c, cx, hip_y, *pose.leg_back, spec, spec.cloth_dark, 1)
    back_hand = _draw_arm(c, shoulder_x - 1, shoulder_y + 1, *pose.arm_back,
                          spec, spec.cloth, 1)
    if spec.weapon != "none" and pose.weapon_hand in ("back", "both"):
        _draw_weapon(c, back_hand[0], back_hand[1], pose.weapon_angle, spec)

    # --- Govde --------------------------------------------------------------
    c.polygon([
        (shoulder_x - spec.shoulder_w * 0.5, shoulder_y),
        (shoulder_x + spec.shoulder_w * 0.5, shoulder_y),
        (cx + spec.torso_w * 0.36, hip_y + 1),
        (cx - spec.torso_w * 0.36, hip_y + 1),
    ], spec.cloth, 3)

    if spec.shoulder_pads:
        c.disc(shoulder_x - spec.shoulder_w * 0.55, shoulder_y + 0.5, 2.4,
               spec.armor, 4)
        c.disc(shoulder_x + spec.shoulder_w * 0.55, shoulder_y + 0.5, 2.4,
               spec.armor, 3)

    # Gogusteki dovme: sag kopruck kemiginin altinda. Govde bu olcekte 7
    # piksel yuksek, yani bir geyigi tanınır cizmek fiziksel olarak mumkun
    # degil - burada sadece koyu bir isaret var. Geyigin kendisi prologda ve
    # yanki gorunumlerinde tam boyutta ciziliyor (bkz. forge.build_deer).
    if spec.tattoo:
        tx = int(shoulder_x + spec.shoulder_w * 0.18)
        ty = int(shoulder_y + 2)
        c.px(tx, ty, spec.accent, 4)
        c.px(tx, ty + 1, spec.accent, 3)
        c.px(tx + 1, ty - 1, spec.accent, 3)

    # Kemer: govdeyi bacaktan ayirir, siluet okunurlugu artar.
    c.fill_rect(int(cx - spec.torso_w * 0.4), int(hip_y - 1),
                int(spec.torso_w * 0.8) + 1, 1, spec.armor, 2)

    # --- On uzuvlar ---------------------------------------------------------
    _draw_leg(c, cx, hip_y, *pose.leg_front, spec, spec.cloth, 3)

    # Tunik etegi: belden asagi acilan bol kumas. Bacaklardan sonra cizilir ki
    # ustlerine dususun; rahat, feminen bir siluet bundan cikiyor.
    if spec.hem > 0.0:
        sway = pose.cape_sway * 0.6
        c.polygon([
            (cx - spec.torso_w * 0.38, hip_y - 1),
            (cx + spec.torso_w * 0.38, hip_y - 1),
            (cx + spec.hem * 0.5 - sway, hip_y + spec.hem_len),
            (cx - spec.hem * 0.5 - sway, hip_y + spec.hem_len),
        ], spec.cloth, 2)

    _draw_head(c, head_x, head_y, spec, hair_sway=pose.cape_sway)
    front_hand = _draw_arm(c, shoulder_x + 1, shoulder_y + 1, *pose.arm_front,
                           spec, spec.cloth, 3)
    if spec.weapon != "none" and pose.weapon_hand in ("front", "both"):
        _draw_weapon(c, front_hand[0], front_hand[1], pose.weapon_angle, spec)

    if spec.tail:
        c.taper(cx - spec.torso_w * 0.3, hip_y, cx - spec.torso_w * 0.3 - 6,
                hip_y + 3, 2.4, 0.8, spec.skin, 2)

    c.shade()
    c.outline("ink", 0)
    return c


# --- Animasyon uretimi ------------------------------------------------------
def _idle(spec: CharSpec, t: float) -> Pose:
    """Nefes alma: kucuk dikey salinim + kollarin gecikmeli takibi."""
    breath = math.sin(t * TAU)
    return Pose(
        dy=-0.5 + breath * 0.5,
        squash=1.0 + breath * 0.02,
        head_dy=breath * 0.3,
        leg_back=(math.pi / 2 + 0.10, 0.05),
        leg_front=(math.pi / 2 - 0.08, 0.05),
        arm_back=(math.pi / 2 + 0.18, 0.22 + breath * 0.05),
        arm_front=(math.pi / 2 - 0.14, 0.20 - breath * 0.05),
        weapon_angle=math.pi / 2 + 0.35,
        cape_sway=breath * 0.4,
    )


def _run(spec: CharSpec, t: float) -> Pose:
    """Kosu dongusu.

    Bacaklar zit fazda; govde adim basina bir kez zipladigi icin dikey salinim
    iki kat frekansta. Bu detay olmadan kosu "kayiyor" gibi gorunur.
    """
    a = t * TAU
    bob = abs(math.sin(a)) * 1.4
    return Pose(
        dy=-bob,
        lean=0.55,
        head_dx=0.6,
        head_dy=bob * 0.2,
        leg_front=(math.pi / 2 + math.sin(a) * 0.85, max(0.0, math.cos(a)) * 0.75),
        leg_back=(math.pi / 2 + math.sin(a + math.pi) * 0.85,
                  max(0.0, math.cos(a + math.pi)) * 0.75),
        arm_front=(math.pi / 2 + math.sin(a + math.pi) * 0.75, 0.55),
        arm_back=(math.pi / 2 + math.sin(a) * 0.75, 0.55),
        weapon_angle=math.pi / 2 + 0.6,
        cape_sway=1.2 + math.sin(a) * 0.4,
    )


def _walk(spec: CharSpec, t: float) -> Pose:
    a = t * TAU
    return Pose(
        dy=-abs(math.sin(a)) * 0.7,
        lean=0.2,
        leg_front=(math.pi / 2 + math.sin(a) * 0.5, max(0.0, math.cos(a)) * 0.4),
        leg_back=(math.pi / 2 + math.sin(a + math.pi) * 0.5,
                  max(0.0, math.cos(a + math.pi)) * 0.4),
        arm_front=(math.pi / 2 + math.sin(a + math.pi) * 0.4, 0.3),
        arm_back=(math.pi / 2 + math.sin(a) * 0.4, 0.3),
        weapon_angle=math.pi / 2 + 0.4,
        cape_sway=0.6,
    )


def _jump(spec: CharSpec, t: float) -> Pose:
    return Pose(
        dy=-1.0, lean=0.3, squash=1.06,
        leg_front=(math.pi / 2 - 0.55, 0.85),
        leg_back=(math.pi / 2 + 0.30, 0.35),
        arm_front=(math.pi / 2 - 0.95, 0.25),
        arm_back=(math.pi / 2 - 0.55, 0.30),
        weapon_angle=math.pi / 2 + 0.9,
        cape_sway=1.8,
    )


def _fall(spec: CharSpec, t: float) -> Pose:
    flap = math.sin(t * TAU) * 0.15
    return Pose(
        lean=-0.2, squash=1.04,
        leg_front=(math.pi / 2 + 0.30 + flap, 0.30),
        leg_back=(math.pi / 2 - 0.15, 0.55),
        arm_front=(math.pi / 2 - 1.25 + flap, 0.35),
        arm_back=(math.pi / 2 - 1.05 - flap, 0.40),
        weapon_angle=math.pi / 2 + 1.1,
        cape_sway=2.2,
    )


def _land(spec: CharSpec, t: float) -> Pose:
    """Inise carpma: sert basik kare, sonra toparlanma."""
    k = 1.0 - t
    return Pose(
        dy=1.6 * k, squash=1.0 - 0.22 * k, lean=0.25 * k,
        leg_front=(math.pi / 2 - 0.35 * k, 0.9 * k),
        leg_back=(math.pi / 2 + 0.35 * k, 0.9 * k),
        arm_front=(math.pi / 2 - 0.7 * k, 0.5),
        arm_back=(math.pi / 2 + 0.5 * k, 0.5),
        weapon_angle=math.pi / 2 + 0.5,
    )


def _crouch(spec: CharSpec, t: float) -> Pose:
    return Pose(
        dy=2.0, squash=0.62, lean=0.5, head_dy=0.5,
        leg_front=(math.pi / 2 - 0.6, 1.25),
        leg_back=(math.pi / 2 + 0.5, 1.25),
        arm_front=(math.pi / 2 + 0.35, 0.7),
        arm_back=(math.pi / 2 + 0.15, 0.7),
        weapon_angle=math.pi / 2 + 0.2,
    )


def _dash(spec: CharSpec, t: float) -> Pose:
    return Pose(
        dy=-1.0, lean=1.5, squash=0.92, head_dx=1.5,
        leg_front=(math.pi / 2 + 0.95, 0.25),
        leg_back=(math.pi / 2 - 0.75, 0.95),
        arm_front=(math.pi / 2 + 1.15, 0.15),
        arm_back=(math.pi / 2 - 1.15, 0.25),
        weapon_angle=0.15,
        cape_sway=3.2,
    )


def _wall_slide(spec: CharSpec, t: float) -> Pose:
    return Pose(
        lean=-0.6, head_dx=-0.8,
        leg_front=(math.pi / 2 + 0.25, 0.5),
        leg_back=(math.pi / 2 - 0.35, 0.85),
        arm_front=(math.pi / 2 - 1.5, 0.1),
        arm_back=(math.pi / 2 + 0.4, 0.4),
        weapon_angle=math.pi / 2 + 0.3,
        cape_sway=-1.4,
    )


def _hurt(spec: CharSpec, t: float) -> Pose:
    return Pose(
        dy=-0.8, lean=-1.3, head_dx=-1.4, head_dy=-0.5, squash=1.05,
        leg_front=(math.pi / 2 - 0.35, 0.45),
        leg_back=(math.pi / 2 + 0.55, 0.30),
        arm_front=(math.pi / 2 - 1.7, 0.5),
        arm_back=(math.pi / 2 - 1.3, 0.6),
        weapon_angle=math.pi + 0.5,
        cape_sway=-2.0,
    )


def _death(spec: CharSpec, t: float) -> Pose:
    """Yere yigilma: govde basiklasir, kafa one duser."""
    return Pose(
        dy=t * 5.0, squash=max(0.18, 1.0 - t * 0.85), lean=-1.2 * t,
        head_dx=-2.5 * t, head_dy=1.5 * t,
        leg_front=(math.pi / 2 + 1.2 * t, 0.9 * t),
        leg_back=(math.pi / 2 - 1.0 * t, 1.1 * t),
        arm_front=(math.pi / 2 - 1.9 * t, 0.3),
        arm_back=(math.pi / 2 + 1.6 * t, 0.3),
        weapon_angle=math.pi / 2 + 1.6 * t,
        cape_sway=-1.0,
    )


def _attack_swing(spec: CharSpec, t: float) -> Pose:
    """Yatay savurma: geriden yukleme (t<0.35), sonra hizli gecis."""
    if t < 0.35:
        k = t / 0.35
        angle = -2.5 + k * 0.4               # geriye yuklen
        lean = -0.6 * k
    else:
        k = (t - 0.35) / 0.65
        angle = -2.1 + k * 3.2               # ileri savur
        lean = 0.4 + k * 0.9
    return Pose(
        dy=-0.5, lean=lean, head_dx=lean * 0.8,
        leg_front=(math.pi / 2 - 0.25, 0.35),
        leg_back=(math.pi / 2 + 0.45, 0.30),
        arm_front=(angle, 0.15),
        arm_back=(math.pi / 2 + 0.5, 0.5),
        weapon_angle=angle - 0.25,
        weapon_hand="front",
        cape_sway=lean,
    )


def _attack_overhead(spec: CharSpec, t: float) -> Pose:
    """Tepeden indirme: kombonun ikinci vurusu."""
    if t < 0.35:
        k = t / 0.35
        angle = -math.pi / 2 - k * 0.9
        lean = -0.5 * k
    else:
        k = (t - 0.35) / 0.65
        angle = -math.pi / 2 - 0.9 + k * 2.6
        lean = 0.3 + k * 1.0
    return Pose(
        dy=-0.8 + (0.6 if t > 0.4 else 0.0), lean=lean,
        leg_front=(math.pi / 2 - 0.35, 0.45),
        leg_back=(math.pi / 2 + 0.55, 0.35),
        arm_front=(angle, 0.1),
        arm_back=(angle + 0.4, 0.3),
        weapon_angle=angle,
        weapon_hand="both",
        cape_sway=lean * 1.2,
    )


def _attack_thrust(spec: CharSpec, t: float) -> Pose:
    """Sapla: kombonun bitiricisi, ileri atilma ile."""
    if t < 0.4:
        k = t / 0.4
        reach = -2.0 * k
        lean = -0.4 * k
    else:
        k = (t - 0.4) / 0.6
        reach = -2.0 + k * 6.0
        lean = 0.2 + k * 1.3
    return Pose(
        dx=reach * 0.35, dy=-0.6, lean=lean,
        leg_front=(math.pi / 2 + 0.55, 0.15),
        leg_back=(math.pi / 2 - 0.45, 0.85),
        arm_front=(0.05, 0.0),
        arm_back=(math.pi / 2 + 0.6, 0.6),
        weapon_angle=0.0,
        weapon_hand="front",
        cape_sway=lean * 1.4,
    )


def _cast(spec: CharSpec, t: float) -> Pose:
    lift = math.sin(min(1.0, t) * math.pi)
    return Pose(
        dy=-lift * 1.5, lean=-0.3,
        leg_front=(math.pi / 2 - 0.15, 0.2),
        leg_back=(math.pi / 2 + 0.25, 0.2),
        arm_front=(-math.pi / 2 - 0.3, 0.2),
        arm_back=(-math.pi / 2 + 0.4, 0.3),
        weapon_angle=-math.pi / 2,
        cape_sway=lift * 1.5,
    )


# state -> (poz fonksiyonu, kare sayisi, donguselligi)
ANIMATIONS: dict[str, tuple] = {
    "idle": (_idle, 6, True),
    "walk": (_walk, 8, True),
    "run": (_run, 8, True),
    "jump": (_jump, 1, False),
    "fall": (_fall, 4, True),
    "land": (_land, 3, False),
    "crouch": (_crouch, 1, False),
    "dash": (_dash, 2, False),
    "wall_slide": (_wall_slide, 2, True),
    "hurt": (_hurt, 2, False),
    "death": (_death, 6, False),
    "attack1": (_attack_swing, 5, False),
    "attack2": (_attack_overhead, 5, False),
    "attack3": (_attack_thrust, 5, False),
    "cast": (_cast, 4, False),
}


def build_animation(spec: CharSpec, state: str) -> list[pygame.Surface]:
    entry = ANIMATIONS.get(state)
    if entry is None:
        entry = ANIMATIONS["idle"]
    pose_fn, count, looping = entry
    frames: list[pygame.Surface] = []
    for i in range(count):
        # Donguseller [0,1) araligini tarar (son kare ilkine esit olmasin);
        # tek seferlikler [0,1] tam araligi tarar.
        t = i / count if looping else (i / max(1, count - 1))
        frames.append(draw_character(spec, pose_fn(spec, t)).resolve())
    return frames


def build_sprite_set(spec: CharSpec,
                     states: tuple[str, ...] | None = None) -> dict[str, list[pygame.Surface]]:
    """Bir karakterin tum animasyonlarini uretir (saga bakar halde)."""
    wanted = states or tuple(ANIMATIONS.keys())
    return {state: build_animation(spec, state) for state in wanted}


def mirror_set(sprite_set: dict[str, list[pygame.Surface]]) -> dict[str, list[pygame.Surface]]:
    return {state: [flip_h(f) for f in frames] for state, frames in sprite_set.items()}


# --- Karakter kutuphanesi ---------------------------------------------------
# Rey - Yankisoyleyen.
#
# Uzun, gur, duz ve neredeyse siyah sac; koyu kahve badem gozler; esmer ve
# purcuksuz ten; rahat dokumlu bir tunik. Sag kopruck kemiginin altinda
# geyik dovmesi.
#
# Bu olcekte (26 piksel boy) yuz ayrintisi kaybolur; karakteri tasiyan sey
# siluettir: sirta dokulen agir sac, dar omuz ve acilan etek. Dovme burada
# yalnizca koyu bir isaret - geyigin kendisi prologda tam boyutta cikiyor.
REY_UNARMED = CharSpec(
    name="rey", cell_w=40, cell_h=40, foot_y=33,
    head_r=4.0, torso_h=7.2, torso_w=6.4,
    thigh=4.8, shin=4.8, upper_arm=4.0, fore_arm=4.0,
    limb_w=2.4, shoulder_w=5.2,
    skin="flesh", skin_step=2,          # esmer, purcuksuz (gurultu uygulanmaz)
    cloth="azure", cloth_dark="ink", armor="gold",
    hair="ink", hair_step=3,            # gur, duz, neredeyse siyah (parlak tel)
    accent="ember",
    long_hair=True, hair_length=10.0,
    eye_ramp="earth", eye_step=0, almond_eyes=True,   # koyu kahve badem goz
    hem=9.0, hem_len=5.0,               # rahat, dokumlu tunik
    tattoo="deer",
    cape=True, weapon="none",
)

REY_ARMED = replace(REY_UNARMED, name="rey_armed", weapon="sword",
                    shoulder_pads=True, armor="stone")

GOBLIN = CharSpec(
    name="goblin", cell_w=32, cell_h=32, foot_y=27,
    head_r=3.6, torso_h=5.4, torso_w=6.0,
    thigh=3.4, shin=3.4, upper_arm=3.2, fore_arm=3.4,
    limb_w=2.4, shoulder_w=5.0,
    skin="moss", cloth="earth", cloth_dark="ink", armor="earth",
    hair="ink", accent="blood",
    pointed_ears=True, weapon="knife",
)

ARCHER = replace(GOBLIN, name="archer", weapon="bow", cloth="moss",
                 armor="earth", hood=True, cell_w=34, cell_h=34, foot_y=29)

SKELETON = CharSpec(
    name="skeleton", cell_w=38, cell_h=38, foot_y=30,
    head_r=3.8, torso_h=6.4, torso_w=5.4,
    thigh=4.2, shin=4.2, upper_arm=3.8, fore_arm=3.8,
    limb_w=2.0, shoulder_w=5.2,
    skin="bone", cloth="bone", cloth_dark="ink", armor="stone",
    hair="ink", accent="azure",
    skull=True, glow_eyes=180, weapon="sword",
)

BRUTE = CharSpec(
    name="brute", cell_w=52, cell_h=52, foot_y=44,
    head_r=4.6, torso_h=10.0, torso_w=12.0,
    thigh=6.0, shin=6.0, upper_arm=6.0, fore_arm=6.0,
    limb_w=4.4, shoulder_w=11.0,
    skin="earth", cloth="stone", cloth_dark="ink", armor="stone",
    hair="ink", accent="blood",
    horns=True, shoulder_pads=True, one_eye=True, weapon="club",
)

ASSASSIN = CharSpec(
    name="assassin", cell_w=34, cell_h=34, foot_y=29,
    head_r=3.6, torso_h=6.2, torso_w=5.6,
    thigh=4.4, shin=4.4, upper_arm=3.8, fore_arm=3.8,
    limb_w=2.2, shoulder_w=5.0,
    skin="ash", cloth="ink", cloth_dark="ink", armor="violet",
    hair="ink", accent="violet",
    hood=True, cape=True, glow_eyes=160, weapon="knife",
)

MAGE = CharSpec(
    name="mage", cell_w=42, cell_h=42, foot_y=34,
    head_r=3.8, torso_h=7.5, torso_w=7.5,
    thigh=4.0, shin=4.0, upper_arm=4.0, fore_arm=4.0,
    limb_w=2.8, shoulder_w=6.0,
    skin="flesh", cloth="violet", cloth_dark="ink", armor="gold",
    hair="ash", accent="violet",
    hood=True, cape=True, glow_eyes=200, weapon="staff",
)

GAOLER = CharSpec(
    name="gaoler", cell_w=72, cell_h=72, foot_y=60,
    head_r=5.4, torso_h=13.0, torso_w=15.0,
    thigh=7.5, shin=7.5, upper_arm=7.5, fore_arm=7.5,
    limb_w=5.4, shoulder_w=14.0,
    skin="ash", cloth="stone", cloth_dark="ink", armor="stone",
    hair="ink", accent="ember",
    hood=True, shoulder_pads=True, glow_eyes=220, weapon="scythe",
)

ARCHETYPES: dict[str, CharSpec] = {
    "rey": REY_UNARMED,
    "rey_armed": REY_ARMED,
    "goblin": GOBLIN,
    "archer": ARCHER,
    "skeleton": SKELETON,
    "brute": BRUTE,
    "assassin": ASSASSIN,
    "mage": MAGE,
    "gaoler": GAOLER,
}
