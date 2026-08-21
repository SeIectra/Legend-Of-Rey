"""Animasyon pozlari ve karakter kutuphanesi.

Bir animasyon, **poz ureten bir fonksiyondur**: `t` (0..1) alir, `Pose` doner.
Kare listesi bu fonksiyonun orneklenmesiyle olusur. Elle kare cizmek yerine
matematikle uretmek, yeni bir karakterin tum animasyonlarini bedava yapar.

Hiz: animasyon hissi 8 FPS (her sanat karesi ~7 oyun karesi). Saldirilar
istisna - onlar dovus belgesindeki kare butcesine (`4/3/8` gibi) yayilir,
yani ilerleme oranina gore ornerklenir.
"""
from __future__ import annotations

import math
from dataclasses import replace

import pygame

from src.art.spritegen import CharSpec, Pose, draw_humanoid

TAU = math.tau

# Her sanat karesi kac oyun karesi durur (8 FPS hissi).
FRAMES_PER_ART_FRAME = 7


# --- Poz ureticileri --------------------------------------------------------
def _idle(t: float) -> Pose:
    """Nefes alma: kucuk dikey salinim, kollarin gecikmeli takibi."""
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


def _run(t: float) -> Pose:
    """Kosu dongusu.

    Bacaklar zit fazda; govde adim basina bir kez ziplar, bu yuzden dikey
    salinim iki kat frekansta. Bu detay olmadan kosu "kayiyor" gibi gorunur.
    """
    angle = t * TAU
    bob = abs(math.sin(angle)) * 1.4
    return Pose(
        dy=-bob,
        lean=0.55,
        head_dx=0.6,
        head_dy=bob * 0.2,
        leg_front=(math.pi / 2 + math.sin(angle) * 0.85,
                   max(0.0, math.cos(angle)) * 0.75),
        leg_back=(math.pi / 2 + math.sin(angle + math.pi) * 0.85,
                  max(0.0, math.cos(angle + math.pi)) * 0.75),
        arm_front=(math.pi / 2 + math.sin(angle + math.pi) * 0.75, 0.55),
        arm_back=(math.pi / 2 + math.sin(angle) * 0.75, 0.55),
        weapon_angle=math.pi / 2 + 0.6,
        cape_sway=1.2 + math.sin(angle) * 0.4,
    )


def _jump(t: float) -> Pose:
    return Pose(
        dy=-1.0, lean=0.3, squash=1.06,
        leg_front=(math.pi / 2 - 0.55, 0.85),
        leg_back=(math.pi / 2 + 0.30, 0.35),
        arm_front=(math.pi / 2 - 0.95, 0.25),
        arm_back=(math.pi / 2 - 0.55, 0.30),
        weapon_angle=math.pi / 2 + 0.9,
        cape_sway=1.8,
    )


def _fall(t: float) -> Pose:
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


def _dodge(t: float) -> Pose:
    return Pose(
        dy=-1.0, lean=1.5, squash=0.92, head_dx=1.5,
        leg_front=(math.pi / 2 + 0.95, 0.25),
        leg_back=(math.pi / 2 - 0.75, 0.95),
        arm_front=(math.pi / 2 + 1.15, 0.15),
        arm_back=(math.pi / 2 - 1.15, 0.25),
        weapon_angle=0.15,
        cape_sway=3.2,
    )


def _hurt(t: float) -> Pose:
    return Pose(
        dy=-0.8, lean=-1.3, head_dx=-1.4, head_dy=-0.5, squash=1.05,
        leg_front=(math.pi / 2 - 0.35, 0.45),
        leg_back=(math.pi / 2 + 0.55, 0.30),
        arm_front=(math.pi / 2 - 1.7, 0.5),
        arm_back=(math.pi / 2 - 1.3, 0.6),
        weapon_angle=math.pi + 0.5,
        cape_sway=-2.0,
    )


def _death(t: float) -> Pose:
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


def _attack_swing(t: float) -> Pose:
    """Yatay savurma - zincirin 1. vurusu. Geriden yukle, hizli gec."""
    if t < 0.35:
        k = t / 0.35
        angle = -2.5 + k * 0.4
        lean = -0.6 * k
    else:
        k = (t - 0.35) / 0.65
        angle = -2.1 + k * 3.2
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


def _attack_overhead(t: float) -> Pose:
    """Tepeden indirme - zincirin 2. vurusu."""
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


def _attack_thrust(t: float) -> Pose:
    """Sapla - bitirici. Ileri atilma ile."""
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


# state -> (poz fonksiyonu, kare sayisi, dongusel mu)
ANIMATIONS: dict[str, tuple] = {
    "idle": (_idle, 6, True),
    "run": (_run, 8, True),
    "jump": (_jump, 1, False),
    "fall": (_fall, 4, True),
    "dodge": (_dodge, 2, False),
    "hurt": (_hurt, 2, False),
    "death": (_death, 6, False),
    "attack1": (_attack_swing, 5, False),
    "attack2": (_attack_overhead, 5, False),
    "attack3": (_attack_thrust, 5, False),
}


def build_animation(spec: CharSpec, state: str) -> list[pygame.Surface]:
    """Bir durumun tum karelerini uretir (saga bakar halde)."""
    pose_fn, count, looping = ANIMATIONS.get(state, ANIMATIONS["idle"])
    frames: list[pygame.Surface] = []
    for index in range(count):
        # Donguseller [0,1) tarar (son kare ilkine esit olmasin);
        # tek seferlikler [0,1] tam araligi tarar.
        t = index / count if looping else index / max(1, count - 1)
        frames.append(draw_humanoid(spec, pose_fn(t)).resolve())
    return frames


def build_sprite_set(spec: CharSpec) -> dict[str, list[pygame.Surface]]:
    """Bir karakterin tum animasyonlari. Baslangicta bir kez uretilir."""
    return {state: build_animation(spec, state) for state in ANIMATIONS}


# --- Karakter kutuphanesi ---------------------------------------------------
# Rey - Yankisoyleyen. Esmer, uzun gur duz koyu kahve sacli.
# Sag kopruck kemiginin altinda geyik isareti.
REY_SPEC = CharSpec(
    name="rey",
    cell_width=48, cell_height=40, foot_y=34,
    head_radius=4.0, torso_height=7.2, torso_width=6.4,
    thigh=4.8, shin=4.8, upper_arm=4.0, fore_arm=4.0,
    limb_width=2.4, shoulder_width=5.2,
    skin="skin_tan", hair="hair_dark", cloth="cloth_blue",
    cloth_dark="shadow", armor="brass", accent="gore",
    long_hair=True, hair_length=11.0,
    hem=11.5, hem_length=6.0, tattoo=True, cape=True,
    weapon="sword",
)

# Ardo - yabanci. Daha agir, kapusonlu, Yanki'si yok.
#
# Siluet ayrimi bilincli: Rey ince, uzun sacli, etegi acilan; Ardo genis
# omuzlu, sivri kukuleteli, etegi olmayan. Tek renge indirildiginde bile
# hangisinin kim oldugu anlasilmali (docs/asset-plani.md 4).
ARDO_SPEC = replace(
    REY_SPEC,
    name="ardo",
    torso_height=8.0, torso_width=8.2, shoulder_width=7.6, limb_width=2.9,
    thigh=4.4, shin=4.4,          # Daha kisa bacak, daha agir duruş
    skin="skin_tan", hair="hair_dark", cloth="cloth_grey",
    armor="steel", accent="leather",
    long_hair=False, hair_length=0.0, hem=0.0, tattoo=False,
    hood=True, cape=True, shoulder_pads=True,
    weapon="sword",
)

# Katman 1 dusmani - Suruklenen. Curuyen, yavas, tek saldiri.
SHAMBLER_SPEC = CharSpec(
    name="shambler",
    cell_width=40, cell_height=36, foot_y=31,
    head_radius=3.6, torso_height=6.0, torso_width=6.4,
    thigh=3.8, shin=3.8, upper_arm=3.6, fore_arm=3.6,
    limb_width=2.6, shoulder_width=5.4,
    skin="rot", hair="shadow", cloth="rot",
    cloth_dark="shadow", armor="leather", accent="rot",
    glow_eyes=170,
    weapon="none",
)

CHARACTERS: dict[str, CharSpec] = {
    "rey": REY_SPEC,
    "ardo": ARDO_SPEC,
    "shambler": SHAMBLER_SPEC,
}
