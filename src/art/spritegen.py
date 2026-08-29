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
    weapon: str = "none"             # none sword knife club staff spear bow axe

    # --- Siluet kirici ek parcalar ------------------------------------------
    # Olculdu (22.08.2026): prototipin dusmanlari okunur cunku HEPSININ
    # siluetten disari tasan bir parcasi var (bicak, yay, boynuz, kafatasi).
    # Bizim uc dusmanimizin ucunde de `weapon="none"` idi ve hicbir cikinti
    # yoktu - dikdortgen bir lekeye donuyorlardi ("karisik cizgilerden
    # ibaret", Arda). Asagidakiler o cikintiyi saglar.
    shield: bool = False             # Arka kolda kalkan - onden vurulmaz okunur
    shield_chain: str = "steel"
    claws: float = 0.0               # Parmak uclarindan uzayan pence (piksel)
    claw_chain: str = "bone_pale"
    spikes: int = 0                  # Sirttan cikan diken sayisi
    crest: float = 0.0               # Miğfer tepeligi/ibik yuksekligi
    crest_chain: str = ""            # Bos ise `accent`
    tail: float = 0.0                # Arkadan uzanan kuyruk uzunlugu
    hunch: float = 0.0               # Omuz cizgisini one egen kamburluk


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


# Her silahin elden uca uzunlugu (piksel). `_draw_weapon` ve `weapon_tip`
# AYNI sozlugu okuyor: iki yerde ayri sayi olsaydi silah izi kilictan
# kayardi ve bunu ancak ekran goruntusune bakinca fark ederdik.
WEAPON_LENGTH: dict[str, float] = {
    "sword": 13.0, "knife": 7.0, "club": 11.0, "staff": 14.0,
    "spear": 19.0, "axe": 10.0, "bow": 0.0, "none": 0.0,
}


def _draw_weapon(canvas: Canvas, hx: float, hy: float, angle: float,
                 spec: CharSpec) -> None:
    kind = spec.weapon
    if kind == "none":
        return
    chain = spec.weapon_chain
    reach = WEAPON_LENGTH.get(kind, 0.0)
    if kind == "sword":
        tip_x = hx + math.cos(angle) * reach
        tip_y = hy + math.sin(angle) * reach
        canvas.taper(hx, hy, tip_x, tip_y, 3.2, 0.9, chain, 3)
        guard = angle + math.pi / 2
        canvas.line(hx + math.cos(guard) * 2, hy + math.sin(guard) * 2,
                    hx - math.cos(guard) * 2, hy - math.sin(guard) * 2,
                    1.8, "brass", 2)
        canvas.line(hx, hy, hx - math.cos(angle) * 3, hy - math.sin(angle) * 3,
                    2.0, "leather", 2)
    elif kind == "knife":
        tip_x = hx + math.cos(angle) * reach
        tip_y = hy + math.sin(angle) * reach
        canvas.taper(hx, hy, tip_x, tip_y, 2.4, 0.8, "bone_pale", 2)
        canvas.line(hx, hy, hx - math.cos(angle) * 2, hy - math.sin(angle) * 2,
                    2.0, "leather", 1)
    elif kind == "club":
        tip_x = hx + math.cos(angle) * reach
        tip_y = hy + math.sin(angle) * reach
        canvas.taper(hx, hy, tip_x, tip_y, 2.2, 4.6, "leather", 1)
        canvas.disc(tip_x, tip_y, 2.6, "leather", 2)
    elif kind == "staff":
        tip_x = hx + math.cos(angle) * reach
        tip_y = hy + math.sin(angle) * reach
        canvas.line(hx, hy, tip_x, tip_y, 2.0, "leather", 1)
        canvas.disc(tip_x, tip_y, 2.4, "arcane", 3, glow=200)
    elif kind == "spear":
        # Uzun sap + parlak uc. Silueti YATAY olarak kiran tek silah -
        # "yaklasma" tehdidi bir bakista okunsun (Mizrakli'nin butun
        # ogretisi mesafe).
        tip_x = hx + math.cos(angle) * reach
        tip_y = hy + math.sin(angle) * reach
        canvas.line(hx - math.cos(angle) * 5, hy - math.sin(angle) * 5,
                    tip_x, tip_y, 1.6, "leather", 1)
        canvas.taper(tip_x - math.cos(angle) * 4, tip_y - math.sin(angle) * 4,
                     tip_x, tip_y, 2.6, 0.8, "bone_pale", 3)
    elif kind == "bow":
        # Yay govdeye DIK duran genis bir kavis - hicbir yakin dovus silahi
        # bu silueti vermez, "uzaktan vurur" ondan once anlasilir.
        perp = angle + math.pi / 2
        span = 9.0
        ax, ay = hx + math.cos(perp) * span, hy + math.sin(perp) * span
        bx, by = hx - math.cos(perp) * span, hy - math.sin(perp) * span
        bulge = 3.4
        mx = hx + math.cos(angle) * bulge
        my = hy + math.sin(angle) * bulge
        canvas.taper(ax, ay, mx, my, 1.0, 1.8, "leather", 2)
        canvas.taper(mx, my, bx, by, 1.8, 1.0, "leather", 2)
        canvas.line(ax, ay, bx, by, 1.0, "bone_pale", 2)      # kiris
    elif kind == "axe":
        haft_x = hx + math.cos(angle) * reach
        haft_y = hy + math.sin(angle) * reach
        canvas.line(hx, hy, haft_x, haft_y, 1.8, "leather", 1)
        perp = angle + math.pi / 2
        canvas.polygon([
            (haft_x, haft_y),
            (haft_x + math.cos(perp) * 4.6 + math.cos(angle) * 1.5,
             haft_y + math.sin(perp) * 4.6 + math.sin(angle) * 1.5),
            (haft_x + math.cos(perp) * 4.0 - math.cos(angle) * 3.5,
             haft_y + math.sin(perp) * 4.0 - math.sin(angle) * 3.5),
        ], chain, 3)


def _draw_shield(canvas: Canvas, hx: float, hy: float,
                 spec: CharSpec) -> None:
    """Arka koldaki kalkan - govdenin onune tasar.

    Kalkanli'nin butun ogretisi "onden vurulmaz, arkaya gec". O bilgi
    siluetten okunmali: kalkan govdenin on hattini duz bir duvara cevirir,
    oyuncu daha ilk karede yanina gecmesi gerektigini anlar.
    """
    canvas.polygon([
        (hx - 1.0, hy - 5.0),
        (hx + 3.2, hy - 4.2),
        (hx + 3.6, hy + 3.0),
        (hx - 0.4, hy + 5.2),
    ], spec.shield_chain, 2)
    canvas.line(hx + 1.4, hy - 4.0, hx + 1.6, hy + 4.2, 1.0,
                spec.shield_chain, 3)          # ortadan gecen kabartma


def _draw_claws(canvas: Canvas, hx: float, hy: float, angle: float,
                spec: CharSpec) -> None:
    """Elden uzayan uc pence. Silahsiz yaratiga siluet cikintisi verir.

    **Kolun yonunde degil, ONE dogru aciliyor.** Ilk surumde dogrudan
    `angle` kullaniyordu; idle pozunda kollar govdenin yaninda asagi
    sarktigi icin penceler de asagi bakiyor ve govde sutununun icinde
    kayboluyordu - siluet testi bunu yakaladi (uc Curuyen de ayni
    ayirt edilemez sutun cikiyordu). Oneki 0.9 radyanlik sapma pencelerin
    dis hattan tasmasini garanti eder.
    """
    forward = angle - 0.9
    for offset in (-0.38, 0.0, 0.38):
        tip = forward + offset
        canvas.taper(hx, hy,
                     hx + math.cos(tip) * spec.claws,
                     hy + math.sin(tip) * spec.claws,
                     1.5, 0.6, spec.claw_chain, 3)


def _draw_spikes(canvas: Canvas, shoulder_x: float, shoulder_y: float,
                 hip_y: float, spec: CharSpec) -> None:
    """Sirttan cikan dikenler - ust hattı tirtiklastirir."""
    span = max(1.0, hip_y - shoulder_y)
    for i in range(spec.spikes):
        t = (i + 0.5) / spec.spikes
        base_y = shoulder_y + span * t
        base_x = shoulder_x - spec.torso_width * 0.34
        length = 3.4 - 1.4 * t
        canvas.taper(base_x, base_y, base_x - length, base_y - length * 0.7,
                     1.8, 0.6, spec.accent, 3)


def _draw_tail(canvas: Canvas, cx: float, hip_y: float,
               spec: CharSpec, sway: float) -> None:
    """Arkadan uzanan kuyruk. Insansi silueti bir bakista kirar."""
    steps = int(spec.tail)
    x, y = cx - spec.torso_width * 0.3, hip_y
    for i in range(steps):
        t = i / max(1.0, steps - 1.0)
        x -= 1.0
        y += math.sin(t * 2.2 + sway) * 0.9 + 0.25
        canvas.disc(x, y, max(0.8, 1.8 - t * 1.1), spec.cloth_dark,
                    2 if i % 2 else 1)


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

    if spec.crest > 0.0:
        # Migferin tepeliği: yukari dogru uzanan yelpaze. Komutan'i
        # kalabaligin icinde bir bakista bulmayi saglar - "once bunu
        # sustur" karari siluetten verilir.
        tone = spec.crest_chain or spec.accent
        for i in range(5):
            t = i / 4.0
            height = spec.crest * (0.55 + 0.45 * math.sin(t * math.pi))
            x = cx - radius * 0.8 + radius * 1.6 * t
            canvas.line(x, cy - radius * 0.85, x, cy - radius * 0.85 - height,
                        1.4, tone, 3 if i % 2 else 2)


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
    # Kamburluk omuz cizgisini one/asagi ceker - "cokmus/sinsi" duruslar
    # (Suruklenen, Sessiz) bundan okunur, ayri bir poz tablosu gerekmez.
    shoulder_x = cx + pose.lean * 2.5 + spec.hunch
    shoulder_y += spec.hunch * 0.45
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

    if spec.tail > 0.0:
        _draw_tail(canvas, cx, hip_y, spec, pose.cape_sway)

    _draw_back_hair(canvas, head_x, head_y, spec, pose.cape_sway)

    if spec.spikes:
        _draw_spikes(canvas, shoulder_x, shoulder_y, hip_y, spec)

    # Arka uzuvlar - bir basamak koyu, derinlik bundan gelir.
    _draw_leg(canvas, cx, hip_y, *pose.leg_back, spec, spec.cloth_dark, 1)
    back_hand = _draw_arm(canvas, shoulder_x - 1, shoulder_y + 1,
                          *pose.arm_back, spec, spec.cloth, 1)
    if spec.weapon != "none" and pose.weapon_hand in ("back", "both"):
        _draw_weapon(canvas, back_hand[0], back_hand[1], pose.weapon_angle, spec)
    if spec.claws > 0.0:
        _draw_claws(canvas, back_hand[0], back_hand[1],
                    pose.arm_back[0] + pose.arm_back[1], spec)

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
    if spec.claws > 0.0:
        _draw_claws(canvas, front_hand[0], front_hand[1],
                    pose.arm_front[0] + pose.arm_front[1], spec)
    # Kalkan **en son ciziliyor** - govdenin de silahin da onunde durmali,
    # yoksa "onden vurulmaz" bilgisi siluette kayboluyor.
    #
    # Konumu bir **ele degil govdeye** bagli, ve bu bilincli. Iki deneme
    # de yanlisti:
    #   * on el: kalkan bicakla birlikte savruluyor, saldiri karelerinde
    #     basin ustune cikiyordu - "kalkani firlatti" gibi okunuyordu.
    #   * arka el: kalkan arkada kaliyordu, yani tam ters bilgi.
    # Kalkan on kola kayisla bagli - kolun acisiyla degil govdenin
    # konumuyla hareket eder. Sabit on ofset hem dogru hem okunur:
    # Kalkanli ne yaparsa yapsin on hatti duz bir duvar.
    if spec.shield:
        _draw_shield(canvas, cx + spec.torso_width * 0.62,
                     shoulder_y + spec.torso_height * 0.55, spec)

    canvas.shade()
    canvas.outline("shadow", 1)
    return canvas


def weapon_tip(spec: CharSpec, pose: Pose) -> tuple[float, float] | None:
    """Silahin ucunun hucre icindeki konumu. Silah yoksa `None`.

    `draw_humanoid` ile **ayni** iskelet formullerini kullaniyor. Silah
    izi (`src/art/trail.py`) bunu okuyor: iz kilicin ucundan cikmali,
    yaklasik bir noktadan degil. Formulleri kopyalasaydik biri
    degistiginde oteki sessizce kayardi.
    """
    if spec.weapon == "none":
        return None
    reach = WEAPON_LENGTH.get(spec.weapon, 0.0)
    if reach <= 0.0:
        return None

    cx = spec.cell_width * 0.5 + pose.dx
    foot_y = spec.foot_y + pose.dy
    hip_y = foot_y - (spec.thigh + spec.shin) * pose.squash
    shoulder_y = hip_y - spec.torso_height * pose.squash + spec.hunch * 0.45
    shoulder_x = cx + pose.lean * 2.5 + spec.hunch

    # Silahi tutan kol: `weapon_hand` "back" ise arka omuzdan.
    if pose.weapon_hand == "back":
        sx, sy = shoulder_x - 1, shoulder_y + 1
        shoulder_angle, elbow_angle = pose.arm_back
    else:
        sx, sy = shoulder_x + 1, shoulder_y + 1
        shoulder_angle, elbow_angle = pose.arm_front

    # Ust kol -> on kol -> el (draw_humanoid._draw_arm ile ayni zincir).
    ex = sx + math.cos(shoulder_angle) * spec.upper_arm
    ey = sy + math.sin(shoulder_angle) * spec.upper_arm
    wrist = shoulder_angle + elbow_angle
    hx = ex + math.cos(wrist) * spec.fore_arm
    hy = ey + math.sin(wrist) * spec.fore_arm

    return (hx + math.cos(pose.weapon_angle) * reach,
            hy + math.sin(pose.weapon_angle) * reach)
