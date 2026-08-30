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


def _land(t: float) -> Pose:
    """Inis - dizler bukulur, govde cokup toparlanir.

    Gecis karesi: `fall` ile `idle` arasindaki bosluk. Olmadiginda
    karakter havadan zemine ANINDA gecip hicbir agirlik hissettirmiyordu -
    inisin bedeli yalnizca squash'la anlatiliyordu, poz sabit kaliyordu.
    """
    # Ilk yaride cok, sonra hizla toparlanir: bir kavis degil, bir DARBE.
    dip = math.sin(min(1.0, t * 1.6) * math.pi) if t < 0.62 else 0.0
    return Pose(
        dy=dip * 2.4, squash=1.0 - dip * 0.22, lean=0.25 * dip,
        head_dy=dip * 1.2,
        leg_front=(math.pi / 2 - 0.30 * dip, 0.85 * dip),
        leg_back=(math.pi / 2 + 0.34 * dip, 0.80 * dip),
        arm_front=(math.pi / 2 - 0.55 * dip, 0.35),
        arm_back=(math.pi / 2 + 0.50 * dip, 0.30),
        weapon_angle=math.pi / 2 + 0.5,
        cape_sway=1.6 * (1.0 - dip),      # kumas govdeden sonra oturur
    )


def _turn(t: float) -> Pose:
    """Donus - hizli yon degistirirken ayak kaydirma (pivot).

    Kosarken yon degistirmek eskiden ANINDA aynalanmayla oluyordu:
    karakter tek karede ters donuyordu ve hareket "kayiyor" gibi
    okunuyordu. Bu poz o bir kareyi uc kareye yayiyor.
    """
    lean = -0.9 * (1.0 - t)          # once geri yaslanir, sonra duzelir
    return Pose(
        dy=-0.4, lean=lean, head_dx=lean * 1.1, squash=1.0 + 0.05 * (1.0 - t),
        leg_front=(math.pi / 2 + 0.55 * (1.0 - t), 0.20),
        leg_back=(math.pi / 2 - 0.45 * (1.0 - t), 0.55),
        arm_front=(math.pi / 2 - 0.75 * (1.0 - t), 0.30),
        arm_back=(math.pi / 2 + 0.65 * (1.0 - t), 0.35),
        weapon_angle=math.pi / 2 + 0.7,
        cape_sway=2.4 * (1.0 - t),        # pelerin donuse en gec uyar
    )


# state -> (poz fonksiyonu, kare sayisi, dongusel mu)
ANIMATIONS: dict[str, tuple] = {
    "land": (_land, 3, False),
    "turn": (_turn, 3, False),
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


# --- Ikincil hareket: sallanma varyantlari ----------------------------------
# Pelerin/sac/etek gercek ikincil harekette govdeyi GERIDEN takip eder ve
# durunca one savrulur. Sprite'lar onceden uretilip onbelleklendigi icin
# bunu cizim aninda yapamayiz - o yuzden ayni animasyonu uc farkli
# sallanma yanliligiyla uretip calisma zamaninda GECIKMELI olarak
# seciyoruz (bkz. `Animator.sway`).
#
# Yanliligin isareti onemli: `draw_humanoid` pelerinin alt kenarini
# `-sway*3` ile ceker, yani POZITIF sallanma pelerini SOLA - saga bakan
# bir karakterde ARKAYA - atar. Trailing = pozitif.
SWAY_BIASES: tuple[float, ...] = (-1.2, 0.0, 1.8)
SWAY_NEUTRAL = 1                      # SWAY_BIASES icindeki notr indeks


def build_animation(spec: CharSpec, state: str,
                    sway_bias: float = 0.0) -> list[pygame.Surface]:
    """Bir durumun tum karelerini uretir (saga bakar halde)."""
    pose_fn, count, looping = ANIMATIONS.get(state, ANIMATIONS["idle"])
    frames: list[pygame.Surface] = []
    for index in range(count):
        # Donguseller [0,1) tarar (son kare ilkine esit olmasin);
        # tek seferlikler [0,1] tam araligi tarar.
        t = index / count if looping else index / max(1, count - 1)
        pose = pose_fn(t)
        if sway_bias:
            pose = replace(pose, cape_sway=pose.cape_sway + sway_bias)
        frames.append(draw_humanoid(spec, pose).resolve())
    return frames


def build_sprite_set(spec: CharSpec,
                     sway_bias: float = 0.0) -> dict[str, list[pygame.Surface]]:
    """Bir karakterin tum animasyonlari. Baslangicta bir kez uretilir."""
    return {state: build_animation(spec, state, sway_bias)
            for state in ANIMATIONS}


def has_cloth(spec: CharSpec) -> bool:
    """Sallanacak bir seyi var mi? Yoksa varyant uretmek bos maliyet."""
    return bool(spec.cape or spec.long_hair or spec.hem or spec.tail)


# --- Karakter kutuphanesi ---------------------------------------------------
# Rey - Yankisoyleyen. Esmer, uzun gur duz koyu kahve sacli.
# Sag kopruck kemiginin altinda geyik isareti.
# **Oranlar 29.08.2026'da elden gecirildi.** Olculdu: eski Rey 14x29
# piksel ciziliyordu ve kafasi 8 piksseldi - yani **3.5 kafa boyu**, ki bu
# literal olarak chibi orani (gercekci yetiskin 7-8, kahraman oyun
# karakteri 6-7). Arda: *"Karakterler cocuk gibi veya chibi gorunmesin.
# Daha olgun, karizmatik ve estetik yuz oranlari kullan."*
#
# Kafa kucultuldu (8 -> 7), govde ve bacaklar uzatildi: ~4.4 kafa boyu.
# Daha fazlasi mumkun DEGIL ve bu tahmin degil, olculdu: oyunun en dar
# gecidi 2 tile = 32 piksel (Bolum 1 ve 2). Sprite 32'yi gecerse karakter
# koridorlardan gecemez ve bes bolumun oda geometrisi + ziplama zarfi +
# `tools/reachability.py` dogrulamasi birden gecersiz olur.
#
# Yuzun gercek detayi bu yuzden **portrede** yasiyor
# (`src/art/portrait.py`, kafa 40 piksel).
REY_SPEC = CharSpec(
    name="rey",
    cell_width=48, cell_height=40, foot_y=34,
    head_radius=3.4, torso_height=8.2, torso_width=6.2,
    thigh=4.9, shin=4.9, upper_arm=4.3, fore_arm=4.1,
    limb_width=2.3, shoulder_width=5.6, brow_tilt=1, neck=1.0,
    skin="skin_tan", hair="hair_dark", cloth="cloth_blue",
    cloth_dark="shadow", armor="brass", accent="gore",
    long_hair=True, hair_length=11.0,
    hem=11.5, hem_length=6.0, tattoo=True, cape=True,
    weapon="none",          # Bolum 1'de silahsiz; kilic sonradan bulunuyor
)

# Kilicli Rey. Bolum 1'de Rey **silahsiz** basliyor; kilic zindanda
# bulunuyor (src/systems/abilities.py). Ayni iskeletten ciktigi icin
# degisim bedava - tek fark silah.
REY_ARMED_SPEC = replace(REY_SPEC, name="rey_armed", weapon="sword")

# Bolum 2 mini-boss odulu: Hancer ya da Balta (`docs/bolum-02.md`).
# Ayni iskelet, yalnizca silah sekli degisiyor - tutarlilik bedava,
# varyasyon ucuz (CLAUDE.md 6). Sayilar `config.DAGGER_CHAIN`/`AXE_CHAIN`.
#
# Bunlar bir ara `sprite_suffix="_armed"` ile kilicla AYNI gorunuyordu ve
# bu bilerek boyleydi ("sanat Gorev 9'da gelecek"). Ama silah secimi bir
# KARAR ekrani; secilen sey elde gorunmuyorsa karar geri bildirimsiz
# kaliyor. Tek satirlik `replace` ile cozuluyorsa ertelemenin anlami yok.
REY_DAGGER_SPEC = replace(REY_SPEC, name="rey_dagger", weapon="knife")
REY_AXE_SPEC = replace(REY_SPEC, name="rey_axe", weapon="axe")

# Ardo - yabanci. Daha agir, genis omuzlu, Yanki'si yok.
#
# **Kukulete kaldirildi (22.08.2026).** Onceki tasarim kapusonluydu; Arda
# iki kez geri bildirdi ("insana benzemiyor", sonra acikca "kafasindaki o
# sey yuzunden yaratiga benziyor - havali ve yakisikli bir karakter ciz
# demistim"). Kukulete + golge + kucuk piksel tuvalinde bir kapusonu hem
# "insan" hem "havali" okutmak bu boyutta guvenilir olmadi - yuz acikca
# gorunmeyince yakisiklilik da okunamiyor. Cozum: yuzu Rey'inki gibi
# tamamen acik birak, gri/gumus kisa sac ile ("deneyimli savasci" - Rey'in
# koyu uzun sacindan hem renk hem siluet olarak ayri).
#
# Siluet ayrimi hala bilincli, baska eksenlerden: Rey ince/uzun sacli/
# etegi acik; Ardo genis omuzlu/kisa sacli/etegi yok/omuz zirhli. Tek
# renge indirildiginde bile hangisinin kim oldugu anlasilmali
# (docs/asset-plani.md 4) - degisiklikten sonra siluet testiyle
# (tools/sprite_sheet.py --siluet) dogrulandi.
ARDO_SPEC = replace(
    REY_SPEC,
    name="ardo",
    # Ayni sema, agir varyant: genis omuz, kalin uzuv, kisa bacak. Arda:
    # *"Ardo daha guclu, genis omuzlu ve agir bir anatomiye sahip olsun."*
    # `brow_tilt=-1`: kas ic ucu ASAGIDA = catik ve ciddi (Rey'de +1).
    torso_height=8.2, torso_width=8.0, shoulder_width=8.0, limb_width=2.8,
    thigh=4.6, shin=4.6, brow_tilt=-1,   # Daha kisa bacak, daha agir durus
    # Arda'nin referans gorseli koyu/siyaha yakin sac gosteriyordu - "steel"
    # (gri/gumus) o gorsele uymuyordu, sadece Rey'den ayrisin diye
    # secilmisti. Siluet testi zaten renge degil SEKLE bakiyor (duz siyaha
    # indiriliyor) - saci koyulastirmak siluet ayrimini bozmuyor, genis
    # omuz/kisa sac/kurk yaka zaten yeterli.
    skin="skin_tan", hair="hair_dark", cloth="cloth_grey",
    # Arka bacak/kol "cloth_dark" ile bir basamak koyu cizilir. Varsayilan
    # "shadow" zinciri "abyss_dark" arka planla neredeyse ayni koyulukta -
    # Ardo'nun etegi olmadigi icin (Rey'in aksine) bacaklar dogrudan
    # gorunuyor ve arka bacak kayboluyordu ("tek bacakli" gibi okunuyordu).
    # "steel" zaten zirhinin tonu - ayni aile, ama secilebilir.
    cloth_dark="steel",
    armor="steel", accent="leather",
    long_hair=False, hair_length=0.0, hem=0.0, tattoo=False,
    hood=False, cape=True, shoulder_pads=True,
    # Kurklu omuzluk (Arda'nin istegi): "bone_pale" - acik/soluk gri,
    # koyu "steel" zirhtan siluette hemen ayrisir. Ayni tonda olsaydi
    # omuzluk zirhla birlesip kurk hissi kayboluyordu.
    shoulder_chain="bone_pale",
    weapon="sword",
)

# Ardo da ayni secimi yapiyor - Bolum 2 iki karakterle de oynanabiliyor.
ARDO_DAGGER_SPEC = replace(ARDO_SPEC, name="ardo_dagger", weapon="knife")
ARDO_AXE_SPEC = replace(ARDO_SPEC, name="ardo_axe", weapon="axe")

# --- Katman 1: Curuyenler (docs/gdd.md 7) -----------------------------------
# Ucu de ayni iskeletten cikiyor ama **oranlari bilincli olarak zit**.
# Bir donem ucu de ayni spec'i paylasiyordu ve yalnizca rengi degisiyordu;
# uc dusman tipi degil, uc renkli tek dusman gibi okunuyordu. Siluet testi
# (F4) bunun sinavi: tek renge indirildiginde hangisi oldugu anlasilmali.
#
#   Suruklenen  uzun sarkan kollar, one egik - "surukleniyor"
#   Tirmanan    kucuk govde, upuzun ince uzuvlar, genis omuz - boceksi
#   Sismek      kocaman yuvarlak govde, minik kafa, gudук uzuvlar - balon

# Suruklenen - combo hedef tahtasi. Yavas, tek saldiri.
# ============================================================================
# DUSMAN KADROSU - docs/gdd.md 7, uc katman
# ============================================================================
# Olculmus tasarim kurali (23.08.2026, prototiple kiyaslama):
#
#   1. **Her dusmanin siluetten disari tasan bir parcasi olmali.** Prototipin
#      dusmanlari okunurdu cunku hepsinde vardi (bicak, yay, boynuz,
#      kafatasi). Bizim ilk uc dusmanimizin ucunde de `weapon="none"` idi ve
#      hicbir cikinti yoktu - Arda'nin "karisik cizgilerden ibaret, hicbir
#      sey anlasilmiyor" geri bildiriminin birinci sebebi buydu.
#   2. **Kafa govdeden ACIK olmali.** Prototipte yesil surat/beyaz kafatasi
#      koyu govdenin uzerinde duruyordu; bizimkinde kafa govdeyle ayni
#      koyuluktaydi ve Suruklenen'in kafasi gorunmuyordu bile.
#   3. **Govde parlaklik araligi >= 0.40 olmali.** Olculdu: Tirmanan 0.153
#      (hair+cloth+cloth_dark UCU DE "shadow" idi), prototip iskelet 0.722.
#      Ayni renk sayisi, dort kat az kontrast.
#   4. **Boyut hiyerarsisi gorunur olmali.** Uc dusmanimiz da 40x36 idi;
#      prototipte 32'den 72'ye yayiliyordu. Tehdit seviyesi siluetten
#      okunmali, can barindan degil (CLAUDE.md 7: dusman can bari yok).
#
# `rot` zinciri artik YESIL (23.08.2026). Eskiden ['ink_soft','echo_dark',
# 'echo','echo_bright'] idi - yani camgobegi, cunku palette hic yesil yoktu.
# Dusmanlarin turkuaz gorunmesinin sebebi buydu. Arda +5 renk onayladi.

# --- KATMAN 1 · Curuyenler --------------------------------------------------
# *Soru: combo kurmayi ogren* - yavas, okunur, affedici.

# Suruklenen - combo hedef tahtasi. Yavas, tek saldiri.
SHAMBLER_SPEC = CharSpec(
    name="shambler",
    cell_width=40, cell_height=36, foot_y=31,
    # Kollar bacaklardan uzun: yerde surunuyormus gibi sarkiyor.
    # Bacaklar bir donem 3.4'tu ve siluet bacaksiz bir sutuna donuyordu -
    # govdeyi kisaltip bacagi uzatmak ikisini de cozdu.
    thigh=4.4, shin=4.4, upper_arm=5.0, fore_arm=5.2,
    head_radius=3.4, torso_height=5.6, torso_width=6.0,
    limb_width=2.5, shoulder_width=5.0,
    # Deri ve giysi **ayri zincir**: bir donem ikisi de "rot" idi ve dusman
    # tek duz kutle gibi okunuyordu. Curuyen et uzerinde kahverengi pacavra.
    skin="rot", hair="shadow", cloth="leather",
    cloth_dark="shadow", armor="rock", accent="rot",
    glow_eyes=150,
    weapon="none",
    claws=3.4,          # Silahsiz ama silueti kiran uzun pence
    hunch=1.2,          # Cokmus omuz - "surukleniyor" duruştan okunur
)

# Tirmanan - dikey farkindalik. Tavanda bekler, tepeden iner.
CLIMBER_SPEC = CharSpec(
    name="climber",
    cell_width=44, cell_height=34, foot_y=28,
    # Minik govde + upuzun ince uzuv + genis omuz = orumceksi siluet.
    head_radius=2.7, torso_height=4.4, torso_width=4.2,
    thigh=5.4, shin=5.6, upper_arm=5.2, fore_arm=5.4,
    limb_width=1.7, shoulder_width=6.6,
    # DUZELTME: hair/cloth/cloth_dark UCU DE "shadow" idi - govde parlaklik
    # araligi 0.153, yani neredeyse duz siyah. Ekranda kalan sey gercekten
    # "karisik cizgiler"di. Govde artik "rock" (orta ton), uzuvlar "rot"
    # (yesil), sadece en derin golge "shadow".
    skin="rot", hair="shadow", cloth="rock",
    cloth_dark="shadow", armor="steel", accent="arcane",
    pointed_ears=True,
    glow_eyes=215,               # Karanlikta once gozleri gorunur
    weapon="none",
    claws=4.2,          # Tavana tutunan uzun pence - asili haldeyken de okunur
)

# Sismek - konumlandirma. Yaklasir, siser, patlar.
BLOATED_SPEC = CharSpec(
    name="bloated",
    cell_width=44, cell_height=40, foot_y=34,
    # Govde genis ve yuvarlak, uzuvlar gudук: balon gibi okunsun.
    # 11 genislik denendi - yaratik degil kutu gibi gorunuyordu ve minik
    # kafa tamamen kayboluyordu.
    head_radius=2.8, torso_height=8.0, torso_width=12.0,
    thigh=3.0, shin=3.0, upper_arm=2.6, fore_arm=2.6,
    limb_width=3.0, shoulder_width=7.4,
    # Sisen kese kirmizi: tehlike rengiyle akraba, "patlayacak" okunur.
    skin="rot", hair="shadow", cloth="gore",
    cloth_dark="shadow", armor="leather", accent="torchlight",
    glow_eyes=120,
    weapon="none",
    spikes=3,           # Sirttan cikan kabarcik dikenleri - "sisiyor" okunur
)

# --- BOSS 1: Curumus Olan (Bolum 6) -----------------------------------------
# `docs/gdd.md` 8: dort buyuk boss, ilki B6'da - "Ardo'yla ilk beraber
# dovus". Katman 1'in (Curuyenler, B1-B6) **finali**, o yuzden uc dusmanin
# da izini tasiyor: Suruklenen'in cokuk durusu (`hunch`), Tirmanan'in
# penceleri (`claws`), Sismek'in sisik govdesi (genis `torso_width`).
#
# Mini-boss'lardan (Sismis Olan, Sonmus Olan) ayrilmasi SART: onlar
# "buyutulmus dusman", bu bir boss - `docs/gdd.md` 8 "kendi arenasi, kendi
# animasyon seti". Ayrimi uc cikinti tasiyor: sirt dikenleri, uzun
# penceler, kuyruk. Tek renge indirildiginde hicbir Katman 1 dusmaniyla
# karistirilmiyor.
ROTTED_ONE_SPEC = CharSpec(
    name="rotted_one",
    cell_width=64, cell_height=56, foot_y=48,
    head_radius=4.2, torso_height=12.0, torso_width=13.0,
    thigh=7.0, shin=7.0, upper_arm=7.5, fore_arm=7.0,
    limb_width=4.2, shoulder_width=13.0, neck=1.0,
    skin="rot", hair="rot", cloth="gore", cloth_dark="shadow",
    armor="bone_pale", accent="gore",
    weapon="none",
    claws=5.0, claw_chain="bone_pale",
    spikes=5, hunch=2.2, tail=9.0,
    glow_eyes=3, brow_tilt=-1,
)

# --- KATMAN 2 · Lanetli Muhafizlar ------------------------------------------
# *Soru: combo'yu KIRMAYI ogren.* Her biri combo'yu farkli bir yerinden
# keser: Kalkanli onden, Mizrakli mesafeden, Okcu uzaktan, Komutan
# kalabalikla. Hepsi zirhli/askeri - Curuyenler'in pacavrasindan bir
# bakista ayrilir.
#
# Goblin kanonu: CLAUDE.md "Goblin ayri dusman olarak eklenmiyor; Katman
# 2'nin Kalkanli'si goblin'in ruhuyla yapilacak" diyor. Kalkanli bu yuzden
# yesil derili + sivri kulakli - prototipin goblin'inin devami.

SHIELDBEARER_SPEC = CharSpec(          # Kalkanli
    name="shieldbearer",
    cell_width=44, cell_height=40, foot_y=34,
    head_radius=3.5, torso_height=6.6, torso_width=7.0,
    thigh=4.4, shin=4.4, upper_arm=4.0, fore_arm=4.0,
    limb_width=2.7, shoulder_width=6.6,
    skin="moss", hair="hair_dark", cloth="leather",
    cloth_dark="shadow", armor="steel", accent="brass",
    shoulder_pads=True, shoulder_chain="steel",
    pointed_ears=True,          # goblin ruhu
    weapon="knife", shield=True, shield_chain="steel",
)

SPEARMAN_SPEC = CharSpec(              # Mizrakli
    name="spearman",
    cell_width=56, cell_height=40, foot_y=34,   # Mizrak icin genis hucre
    head_radius=3.4, torso_height=6.4, torso_width=6.0,
    thigh=5.0, shin=5.0, upper_arm=4.2, fore_arm=4.2,
    limb_width=2.4, shoulder_width=5.8,
    skin="moss", hair="hair_dark", cloth="cloth_grey",
    cloth_dark="shadow", armor="steel", accent="brass",
    pointed_ears=True,
    weapon="spear",
    crest=2.4, crest_chain="gore",      # Kisa migfer tepeligi
)

ARCHER_SPEC = CharSpec(                # Okcu
    name="archer",
    cell_width=48, cell_height=40, foot_y=34,
    head_radius=3.3, torso_height=6.0, torso_width=5.6,
    thigh=4.6, shin=4.6, upper_arm=4.0, fore_arm=4.0,
    limb_width=2.2, shoulder_width=5.4,
    skin="moss", hair="hair_dark", cloth="moss",
    cloth_dark="shadow", armor="leather", accent="rot",
    pointed_ears=True, hood=True,
    weapon="bow",
)

COMMANDER_SPEC = CharSpec(             # Komutan
    name="commander",
    cell_width=52, cell_height=48, foot_y=41,   # Kadronun en uzunu
    head_radius=3.8, torso_height=8.2, torso_width=8.0,
    thigh=5.6, shin=5.6, upper_arm=4.8, fore_arm=4.8,
    limb_width=3.0, shoulder_width=8.4,
    skin="moss", hair="hair_dark", cloth="cloth_grey",
    cloth_dark="shadow", armor="brass", accent="gore",
    shoulder_pads=True, shoulder_chain="brass", cape=True,
    pointed_ears=True,
    weapon="axe", weapon_chain="brass",
    crest=5.0, crest_chain="gore",      # Yuksek tepelik - kalabalikta bulunur
)

# --- KATMAN 3 · Yanki'nin Cocuklari -----------------------------------------
# *Soru: yardimci sisteminin ihanetiyle yuzles.* Hicbiri "et" degil -
# ucu de Yanki'nin morunu tasiyor ve insansi orandan bilincli olarak
# sapiyor. Katman 1/2'nin yanina konunca AYRI BIR TURDEN olduklari
# anlasilmali.

SILENT_SPEC = CharSpec(                # Sessiz - Yanki onu gostermez
    name="silent",
    cell_width=44, cell_height=40, foot_y=34,
    head_radius=3.0, torso_height=6.8, torso_width=5.0,
    thigh=5.2, shin=5.2, upper_arm=4.6, fore_arm=4.6,
    limb_width=2.0, shoulder_width=5.0,
    # Neredeyse tamamen koyu - ADI bu. Ama "shadow" tuzagina dusmuyoruz:
    # govde "rock", yalniz orta hat "shadow". Gozu YOK (glow_eyes=0):
    # kadronun tek gozsuz uyesi, siluetten taninir.
    skin="rock", hair="shadow", cloth="shadow",
    cloth_dark="shadow", armor="rock", accent="arcane",
    hood=True, cape=True,
    weapon="knife",
    claws=2.6,
)

ECHOING_SPEC = CharSpec(               # Yankilayan - sesini taklit eder
    name="echoing",
    cell_width=48, cell_height=42, foot_y=36,
    # Oyuncunun oranlarina KASITLI olarak yakin - "seni taklit ediyor"
    # rahatsizligi buradan gelir. Ama uzuvlar bir tik uzun: tam degil,
    # neredeyse. Tekinsiz vadi bilincli.
    head_radius=3.9, torso_height=7.4, torso_width=6.2,
    thigh=5.2, shin=5.2, upper_arm=4.4, fore_arm=4.6,
    limb_width=2.3, shoulder_width=5.4,
    skin="arcane", hair="arcane", cloth="arcane",
    cloth_dark="shadow", armor="arcane", accent="arcane",
    long_hair=True, hair_length=9.0, cape=True,
    glow_eyes=235,
    weapon="sword", weapon_chain="arcane",
)

SPLITTER_SPEC = CharSpec(              # Bolunen - vurunca ikiye ayrilir
    name="splitter",
    cell_width=48, cell_height=42, foot_y=36,
    head_radius=3.6, torso_height=7.0, torso_width=8.4,
    thigh=4.2, shin=4.2, upper_arm=4.0, fore_arm=4.0,
    limb_width=2.6, shoulder_width=7.8,
    skin="rot", hair="arcane", cloth="arcane",
    cloth_dark="shadow", armor="arcane", accent="rot",
    glow_eyes=200,
    weapon="none",
    claws=3.0,
    spikes=4,           # Bolunme cizgileri gibi okunan sirt dikenleri
    tail=5.0,           # Ikiye ayrilacak govdenin uzantisi
)

# Cemo - Rey'in kucuk kardesi. Esmer, kivircik sacli, tatli bir cocuk.
# **Cocuk oranlari:** kafa govdeye gore buyuk, uzuvlar kisa. Yetiskini
# kucultmek cocuk yapmaz - oran degismeli, yoksa "uzaktaki yetiskin" okunur.
# Bolum 1 ve 13 icerigi henuz yazilmadi; bu spec simdilik yalnizca menu
# 5. asamasinda (oyun bitti) kullaniliyor.
CEMO_SPEC = CharSpec(
    name="cemo",
    cell_width=40, cell_height=32, foot_y=27,
    head_radius=3.6, torso_height=4.6, torso_width=4.8,
    thigh=3.0, shin=3.0, upper_arm=2.8, fore_arm=2.8,
    limb_width=2.0, shoulder_width=4.0,
    skin="skin_tan", hair="hair_dark", cloth="leather",
    cloth_dark="shadow", armor="rock", accent="brass",
    curly_hair=True,
    weapon="none",
)

# Koylu - Bolum 1'in koyunu yasayan bir yer yapan pasif NPC.
# Kasitli olarak SILIK: oyuncu, Cemo ve dusmanlarla yarismamali. Sade
# giysi, aksesuar yok, silah yok. Kalabaligin bir uyesi gibi okunsun -
# tek tek karakter gibi degil. Farklilik `seed` ile gelen ritimden
# geliyor, sprite'tan degil (bes ayri sprite uretmek bu olcekte
# gorunmeyecek bir maliyet olurdu).
VILLAGER_SPEC = CharSpec(
    name="villager",
    cell_width=40, cell_height=38, foot_y=32,
    head_radius=3.5, torso_height=6.6, torso_width=5.6,
    thigh=4.6, shin=4.6, upper_arm=3.8, fore_arm=3.8,
    limb_width=2.3, shoulder_width=5.0,
    skin="skin_tan", hair="hair_dark", cloth="leather",
    cloth_dark="shadow", armor="rock", accent="earth_dark"
    if False else "leather",
    hem=6.0, hem_length=4.0,     # Basit tunik - koylu kiyafeti
    weapon="none",
)


# --- BOSS 2: Zindanci (Bolum 13) --------------------------------------------
# `docs/asset-listesi.md`: *"2 - Zindanci | B13 | 64x80"* - oyunun en
# buyuk sprite'i. Curumus Olan 64x56'ydi; buyume kasitli, cunku ikisi
# ayni odada olmasa bile ayni hafizada yarisiyor.
#
# ## Silueti Curumus Olan'in TAM ZITTI olmali
#
# BOSS 1 bir hayvan: cokuk (`hunch=2.2`), pencelı, kuyruklu, ortadan
# genis. Zindanci bir **adam**: dimdik, zirhli, omuzdan genis, kukuletali.
# Tek renge indirildiginde ilki "yerde surunen sey", ikincisi "ayakta
# duran sey" okunuyor - iki boss'u karistirmanin yolu yok.
#
# Bu ayrim anlatiyi da tasiyor. Katman 1 curumeydi (hastalik, kaza).
# Katman 2 **kasit**: bu zindani biri isletiyor, ve o biri Cemo'yu
# kafeste tutuyor. Bir canavar degil bir gorevli.
#
# ## Feneri burada YOK
#
# Fener sprite'a girmedi, `Gaoler.draw_extra` ciziyor. Sebep: fener
# dovus boyunca **degisiyor** (parlak -> catlak -> kirik) ve bir
# sprite karesine cakilirsa faz gecisi gorunmez olurdu. Sprite govdeyi
# anlatir, durumu degil.
GAOLER_SPEC = CharSpec(
    name="gaoler",
    cell_width=64, cell_height=80, foot_y=64,
    # Kafa kucuk, omuz cok genis: yetiskin oranin abartilmis hali.
    # `head_radius*2 = 8.4`, boy ~46 -> oran 5.5, chibi'nin cok uzagi.
    head_radius=4.2, torso_height=14.0, torso_width=12.0,
    thigh=8.0, shin=8.0, upper_arm=8.0, fore_arm=7.5,
    limb_width=4.4, shoulder_width=17.0, neck=1.0,
    # Demir ve tas - Katman 2'nin askeri dili, Curuyenler'in
    # pacavrasindan bir bakista ayrilir.
    #
    # Ilk deneme `cloth="leather"` + `cape=True` idi ve ekranda TURUNCU
    # BIR PANO cikti: pelerin genis bir dikdortgen olarak cizilince
    # siluet "kutu + iki bacak" oluyordu, yani `docs/asset-plani.md`
    # 4'un siluet testinden kaliyordu. Pelerin kalkti, yerine uzun
    # etek (`hem`) geldi - artik siluet dimdik bir SUTUN, ve Curumus
    # Olan'in cokuk-genis govdesiyle karistirilmasi imkansiz.
    skin="skin_tan", hair="shadow", cloth="rock",
    cloth_dark="shadow", armor="steel", accent="brass",
    hood=True,              # Yuzu gorunmuyor - gozler disinda
    cape=False,
    shoulder_pads=True,
    shoulder_chain="steel",
    # Uzun palto: bacaklari yutuyor. Bir gorevlinin uniformasi.
    hem=13.0, hem_length=13.0,
    # Balta SILUET ICIN secildi, hasar icin degil: saldiri pozunda
    # sapiyla birlikte govdenin disina cikan tek parca o. Duz bir
    # sutunun neye niyetlendigi ancak boyle okunuyor
    # (`docs/asset-plani.md`: *"silahin siluetten disari tasmasi tam
    # olarak bunun icin"*). Kilic ve mizrak da denendi; balta agirligi
    # en iyi tasiyan oldu.
    #
    # Zincir, anahtar demeti ve FENER sprite'ta YOK - `draw_extra`
    # ciziyor, cunku ucu de dovus boyunca degisiyor.
    weapon="axe", weapon_chain="steel",
    glow_eyes=210,          # Karanlikta once gozleri gorunur
    brow_tilt=-2,
    claws=0.0, spikes=0, tail=0.0, hunch=0.0,
    crest=0.0,
)


CHARACTERS: dict[str, CharSpec] = {
    # Oynanabilirler
    "rey": REY_SPEC,
    "rey_armed": REY_ARMED_SPEC,
    "rey_dagger": REY_DAGGER_SPEC,
    "rey_axe": REY_AXE_SPEC,
    "ardo": ARDO_SPEC,
    "ardo_dagger": ARDO_DAGGER_SPEC,
    "ardo_axe": ARDO_AXE_SPEC,
    "cemo": CEMO_SPEC,
    "villager": VILLAGER_SPEC,
    # Katman 1 - Curuyenler (B1-B6)
    "shambler": SHAMBLER_SPEC,
    "climber": CLIMBER_SPEC,
    "bloated": BLOATED_SPEC,
    # Katman 2 - Lanetli Muhafizlar (B7-B13)
    # SANAT hazir; hicbir bolume YERLESTIRILMEDI (CLAUDE.md 3: ileri bolum
    # icerigi sirasi gelmeden yazilmaz). Dovus test odasindan gorulebilir.
    "rotted_one": ROTTED_ONE_SPEC,
    # BOSS 2 - Bolum 13'un arenasinda, Katman 2'nin finali.
    "gaoler": GAOLER_SPEC,
    "shieldbearer": SHIELDBEARER_SPEC,
    "spearman": SPEARMAN_SPEC,
    "archer": ARCHER_SPEC,
    "commander": COMMANDER_SPEC,
    # Katman 3 - Yanki'nin Cocuklari (B14-B18) - ayni not
    "silent": SILENT_SPEC,
    "echoing": ECHOING_SPEC,
    "splitter": SPLITTER_SPEC,
}

# Katman uyeligi - kadro sayfasi ve ileride dusman havuzu secimi icin.
TIERS: dict[str, tuple[str, ...]] = {
    "curuyenler": ("shambler", "climber", "bloated"),
    "muhafizlar": ("shieldbearer", "spearman", "archer", "commander"),
    "yanki": ("silent", "echoing", "splitter"),
}
