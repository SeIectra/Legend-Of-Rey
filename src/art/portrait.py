"""Karakter portreleri - 64x96 bust, gercek yuz anatomisiyle.

## Neden ayri bir varlik sinifi

Arda (29.08.2026): *"Gozleri sadece iki piksel nokta olarak birakma. Goz
kapagi, iris/pupil hissi ve kucuk highlight kullan. Burun icin kucuk ama
gercekci bir pixel cluster. Agiz tek bir yatay cizgi gibi gorunmesin."*

Bu **oyun ici sprite'ta fiziksel olarak imkansiz** ve bu tahmin degil,
olculdu:

    Rey oyun icinde 14x29 piksel ciziliyor, kafasi 8 piksel.
    Oyunun en dar gecidi 2 tile = 32 piksel (Bolum 1 ve 2'de olculdu).
    Oyuncu govdesi 10x22.

Sprite'i buyutmek koridorlardan gecemez hale getirirdi: bes bolumun oda
geometrisi, ziplama zarfi ve `tools/reachability.py` dogrulamasi birden
gecersiz olurdu. 8 piksellik bir kafada 8 satirin tamami alin, goz, burun
ve ceneyi paylasiyor - goz kapagi + iris + highlight + burun kumesi +
dudak oraya sigmiyor.

Cozum, iyi retro RPG'lerin coktan buldugu cozum (Chrono Trigger, Octopath,
Blasphemous): **kucuk alan sprite'i + buyuk portre.** Yuz burada yasiyor.

## Oranlar klasik yuz semasindan

Rastgele degil, cizim anatomisinin standart semasi:

    goz cizgisi kafanin (kafatasi dahil) DIKEY ORTASINDA
    iki goz arasi mesafe = BIR goz genisligi
    burun tabani goz ile cene arasinin ~yarisinda
    agiz burun tabani ile cene arasinin ust ucte birinde
    kafa genisligi = yuksekligin ~0.72'si

Ilk surumde kafa 29x46 (oran 0.63) idi ve "uzun surat" gibi okunuyordu;
gozler 8 piksel arayla duruyordu ve sasi gorunuyordu. Sema disina cikinca
yuz hemen bozuluyor - o yuzden asagidaki satir sabitleri semadan turuyor,
elle ayarlanmiyor.

## Cizim sirasi bilincli

    1. arka sac kutlesi     (yuzun arkasinda kalan hacim)
    2. boyun + omuz + yaka
    3. kafa formu           (kafatasi + elmacik + cene - DAIRE DEGIL)
    4. yuz detaylari        kas, goz, burun, agiz - ELLE
    5. on sac               sac cizgisi, perce, tutamlar, highlight
    6. outline()

**`shade()` cagrilmiyor.** Ilk surumde cagriliyordu ve yuzu lekeli
yapiyordu: o gecis tum tuvale bakip sol-ust kenarlari aciyor, sag-alti
koyultuyor - buyuk formlar icin mukemmel ama gozun highlight'ini ya da
burnun kanat golgesini "kenar" sanip eziyor. Yuzdeki her piksel bir
ANLAM tasiyor, bir egim degil; hepsi elle konuyor.

## Isik yonu

`forge.Canvas` isigi sol-usttan aliyor, tum oyunda sabit (`CLAUDE.md` 6).
Portre de ayni: sol alin, sol elmacik ve burun sirtinin solu aydinlik;
sag yanak, cene alti ve burnun sag kanadi golgede.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import pygame

from src.art import palette
from src.art.forge import Canvas

# Portre tuvali. 64x96 Arda'nin verdigi olcu.
WIDTH = 64
HEIGHT = 96

FACE_CX = 31.0

# --- Yuz semasi (mutlak satirlar) -------------------------------------------
# Kafa 40 satir (7..47), genislik ~29 -> oran 0.72, klasik sema.
#
# Bust kompozisyonu: kafa karenin ~%42'si, boyun kisa, omuzlar genis
# taban. Ilk surumde kafa 36 satir ve boyun 17 satirdi - portre
# "uzun boyunlu" gorunuyordu, cunku gercek bir boyun cenenin altindan
# omuza kadar kafanin ancak dortte biri kadardir.
CROWN = 7           # kafatasinin tepesi
HAIRLINE = 17       # sac cizgisi - alnin ustu
BROW = 24           # kas cizgisi
EYE = 27            # goz cizgisi ~ kafanin dikey ortasi (7+47)/2 = 27
CHEEK = 32          # elmacik kemigi hizasi
NOSE_BASE = 36      # burun tabani
MOUTH = 41          # agiz - burun ile cene arasinin ust ucte biri
JAW = 43            # cene koseleri
CHIN = 47           # cenenin ucu
NECK_TOP = 46
SHOULDER = 57       # kisa boyun: cene ile omuz arasi 10 satir


@dataclass(frozen=True)
class PortraitSpec:
    """Bir portrenin oranlari, egimleri ve zincirleri.

    Sayilar **piksel**. Sema disina cikan degerler yuzu hemen bozuyor, o
    yuzden buradaki alanlar semanin etrafinda kucuk sapmalar icin -
    karakteri ayiran sey birkac piksel.
    """

    name: str

    # --- Kafa formu ---------------------------------------------------------
    skull_width: int = 26          # kulak hizasi, en genis yer
    cheek_width: int = 25          # elmacik kemigi
    jaw_width: int = 19            # cene hatti
    chin_width: int = 8            # cenenin ucu

    # --- Goz ----------------------------------------------------------------
    # `eye_gap` ic kosenin merkeze uzakligi. Sema: iki goz arasi = BIR goz
    # genisligi, yani eye_gap = eye_width / 2.
    eye_width: int = 5
    eye_height: int = 3
    eye_gap: int = 3
    eye_drop: int = 0              # semadan sapma (+ asagi)
    eye_tilt: int = 1              # dis kose ic koseden bu kadar yukarida
    lid_weight: int = 1            # ust kapak kalinligi
    iris_chain: str = "leather"
    iris_step: int = 2

    # --- Kas ----------------------------------------------------------------
    brow_thickness: int = 1
    brow_length: int = 7
    # Ic ucun dis uca gore yuksekligi. Negatif = ic uc asagida = catik.
    brow_angle: int = 1
    brow_drop: int = 0             # semadan sapma

    # --- Burun --------------------------------------------------------------
    nose_width: int = 3
    nose_bridge: int = 4           # sirtin ustten kac piksel gorundugu

    # --- Agiz ---------------------------------------------------------------
    mouth_width: int = 7
    lip_fullness: int = 1

    # --- Sac ----------------------------------------------------------------
    hair_volume: int = 4           # kafatasinin ustune binen hacim
    hair_length: int = 0           # omuz hizasina inen uzunluk (0 = kisa)
    hair_side: int = 0             # yuzun yanindan inen tutam uzunlugu
    fringe_depth: int = 3          # percenin alna inisi
    sweep: int = -1                # saçin savruldugu yon (-1 sol, +1 sag)
    curly: bool = False

    # --- Golge --------------------------------------------------------------
    face_shadow: int = 0           # yuzun sag yarisi bu kadar koyulasir
    stubble: int = 0

    # --- Govde --------------------------------------------------------------
    # Omuzlarin tuvalin kenarina dogru ne kadar acildigi. Anatomiyi tek
    # basina bu sayi tasiyor: Rey dar ve dengeli, Ardo genis ve agir.
    shoulder_span: int = 20

    # --- Zincirler ----------------------------------------------------------
    skin: str = "skin_tan"
    hair: str = "hair_dark"
    cloth: str = "cloth_blue"
    accent: str = "gore"
    shoulder_pads: bool = False
    shoulder_chain: str = "bone_pale"
    tattoo: bool = False


# =============================================================================
# Kafa formu
# =============================================================================
def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _half_width(spec: PortraitSpec, y: int) -> float:
    """Kafanin `y` satirindaki yari genisligi.

    Bes dugum: tepe (yuvarlak), kulak (en genis), elmacik, cene kosesi,
    cene ucu. Arda'nin "kafayi basit bir kare veya oval blok olarak
    cizme" istegi buradan karsilaniyor - bu profil bir elips DEGIL.
    """
    if y < CROWN or y > CHIN:
        return 0.0
    ear = BROW + 1

    if y <= ear:
        span = max(1, ear - CROWN)
        t = (y - CROWN) / span
        # sqrt egrisi: tepede yuvarlak, kulak hizasinda duzlesir.
        return spec.skull_width * 0.5 * (t * (2.0 - t)) ** 0.5
    if y <= CHEEK:
        t = (y - ear) / max(1, CHEEK - ear)
        return _lerp(spec.skull_width, spec.cheek_width, t) * 0.5
    if y <= JAW:
        t = (y - CHEEK) / max(1, JAW - CHEEK)
        return _lerp(spec.cheek_width, spec.jaw_width, t) * 0.5
    t = (y - JAW) / max(1, CHIN - JAW)
    # Cene ucu yuvarlak: ussu 0.7 ile daralma yavas basliyor.
    return _lerp(spec.jaw_width, spec.chin_width, t ** 0.7) * 0.5


def _draw_head(canvas: Canvas, spec: PortraitSpec) -> None:
    """Kafanin dolu formu + yuzeyi takip eden golge.

    Uc-dort basamak, hepsi FORMU anlatiyor:
      3  sol alin ve sol elmacik  - isigin dogrudan vurdugu yer
      2  yuzun on duzlemi         - taban ton
      1  sag yanak, sakaklar      - isik acili geliyor
      0  cene alti, kenar         - isik hic gelmiyor
    """
    skin = spec.skin
    for y in range(CROWN, CHIN + 1):
        half = _half_width(spec, y)
        if half < 0.5:
            continue
        x0 = int(round(FACE_CX - half))
        x1 = int(round(FACE_CX + half))
        for x in range(x0, x1 + 1):
            u = (x + 0.5 - FACE_CX) / max(1.0, half)   # -1 sol .. +1 sag
            v = (y - CROWN) / max(1, CHIN - CROWN)     # 0 tepe .. 1 cene

            step = 2
            if u < -0.30 and 0.25 < v < 0.75:
                step = 3                      # sol alin + sol elmacik
            if u > 0.30:
                step = 1                      # sag yanak
            if abs(u) > 0.80:
                step = 1                      # sakak/kenar
            if v > 0.93:
                step = 1                      # cene alti - golgede ama TEN
            # **En koyu basamak yalnizca kenar konturunda.**
            #
            # Arda (30.08.2026): *"Rey yaptigin golgelendirmeden dolayi
            # sakalli gibi duruyor."* Sebep buydu: cene alti ve sag cene
            # kamasi `step=0` ile boyaniyordu ve `skin_tan`'in 0. basamagi
            # `earth_dark` - yani `hair_dark` zincirinin ust ucuyla ayni
            # renk ailesi. Cenenin genisce bir bolgesi sac rengine
            # boyaniyordu; goz o lekeyi golge diye degil **sakal** diye
            # okuyor.
            #
            # Golge silinmedi, bir basamak yukseltildi: cene hala
            # koyu (`flesh_dark`) ama hala TEN. En koyu ton bir
            # piksellik cerceveye cekildi - orada zaten kontur isi
            # goruyor.
            #
            # Ardo'nun sert cenesi bundan etkilenmiyor: onunki
            # `stubble=1` + `face_shadow=1` ile ayrica ciziliyor ve
            # ikisi de yerinde duruyor.
            if abs(u) > 0.93:
                step = 0
            canvas.px(x, y, skin, step)

    # Elmacik kemigi vurgusu - yuze hacim veren tek ayrinti.
    # Iki yan **ayni degil**: sol isik aliyor, sag almiyor. Simetrik
    # olsaydi yuz duz bir maske gibi okunurdu.
    canvas.fill_rect(int(FACE_CX - spec.cheek_width * 0.36), CHEEK - 1,
                     3, 2, skin, 3)
    canvas.fill_rect(int(FACE_CX + spec.cheek_width * 0.24), CHEEK,
                     3, 1, skin, 1)

    # Sakak cukurlari - kafatasi ile elmacik arasindaki gecis.
    canvas.px(int(FACE_CX - spec.skull_width * 0.46), BROW - 1, skin, 1)
    canvas.px(int(FACE_CX + spec.skull_width * 0.46), BROW - 1, skin, 1)

    # Kulaklar - siluete kucuk bir cikinti; onsuz kafa "yumurta" oluyor.
    for side in (-1, 1):
        ear_x = int(FACE_CX + side * (spec.skull_width * 0.5))
        canvas.fill_rect(ear_x, BROW + 1, 1, 4, skin, 1 if side > 0 else 2)
        canvas.px(ear_x, BROW + 2, skin, 0)


def _shade_skin(canvas: Canvas, spec: PortraitSpec, x0: int, x1: int,
                y: int, delta: int) -> None:
    """Yalnizca TEN pikselleri bir basamak koyultur/aciklastirir.

    Zincir kontrolu sart: sac, goz ve dudak pikselleri de bu
    dikdortgenlerin icinde kaliyor ve onlari kaydirmak yuzu bozar -
    ilk surumde kaslar aciliyor ve karakter saskin gorunuyordu.
    """
    skin_id = Canvas._chain_id(spec.skin)
    for x in range(int(x0), int(x1) + 1):
        if not canvas.in_bounds(x, y):
            continue
        if canvas.chain[y, x] != skin_id:
            continue
        canvas.step[y, x] = max(0, min(3, int(canvas.step[y, x]) + delta))


def _apply_face_planes(canvas: Canvas, spec: PortraitSpec) -> None:
    """Yuzun **anatomik** isik/golge duzlemleri.

    ## Neden yeniden yazildi

    Onceki surum (`_apply_face_shadow`) yuzun sag yarisini toptan bir
    basamak koyultuyordu. Sonuc ekranda "yuzun yarisi karanlik" gibi
    okunuyordu - ve daha kotusu, `_draw_head`in dort basamakla kurdugu
    formu **siliyordu**: elmacik vurgusu, sakak cukuru, cene alti,
    hepsi ayni tona iniyordu.

    Arda 31.08.2026'da referans getirdi ve istenen sey listeydi:
    *"Yuzde kemik yapisi: elmacik, burun koprusu, cene hatti"*,
    *"Isik yonu net, yuz formu okunuyor"*.

    Golge artik bir **yari** degil, adlandirilmis kucuk sekiller
    toplami. Her biri gercek bir anatomik duzlem:

        sakak         kafatasi ile elmacik arasi ceker
        goz cukuru    kasin altinda, gozun ustunde
        elmacik alti  cikintinin ALTI - yuze hacim veren tek sey
        burun yani    sirtin sagi koyu, solu acik
        burun kanadi  kanatlarin altinda kucuk koyu nokta
        dudak alti    alt dudagin golgesi - agzi hacimli yapan
        cene alti     boyuna dusen

    ## Neden bu kadar kucuk parcalar

    Yuzde bir sey "genel olarak koyu" degildir; her golge bir kemigin
    ya da bir bosluğun sonucudur. Genis lekeler yuzu duzlestirir cunku
    hicbir sey **anlatmazlar**. Ayni gerekce dosya basliginda `shade()`
    icin de yazili: yuzdeki her piksel bir ANLAM tasir, bir egim degil.
    """
    force = max(1, spec.face_shadow)   # Ardo'da 1'den buyuk: sert kontrast
    cheek = spec.cheek_width
    jaw = spec.jaw_width
    skull = spec.skull_width

    # --- Sakaklar: kafatasi ile elmacik arasindaki cekilme -------------
    for y in range(HAIRLINE + 1, BROW + 2):
        half = _half_width(spec, y)
        _shade_skin(canvas, spec, FACE_CX + half * 0.55, FACE_CX + half,
                    y, -force)
        _shade_skin(canvas, spec, FACE_CX - half, FACE_CX - half * 0.72,
                    y, -1)

    # --- Alin isigi: sol-ust, isigin geldigi yer ------------------------
    for k in range(3):
        y = HAIRLINE + 1 + k
        _shade_skin(canvas, spec, FACE_CX - skull * 0.34 + k,
                    FACE_CX - skull * 0.05 + k, y, +1)

    # --- Goz cukuru: kasin altinda gozun ustunde -----------------------
    # Gozu bir **delige** oturtan sey. Onsuz gozler yuzeye yapistirilmis
    # gibi duruyor.
    for side in (-1, 1):
        inner = FACE_CX + side * spec.eye_gap
        outer = inner + side * (spec.eye_width + 1)
        lo, hi = sorted((inner, outer))
        for k in range(2):
            _shade_skin(canvas, spec, lo, hi,
                        EYE + spec.eye_drop - 2 - k,
                        -force if side > 0 else -1)

    # --- ★ Elmacik ALTI: yuze hacim veren tek golge ---------------------
    # Cikintinin kendisi `_draw_head`te aydinlik; burasi onun ALTI ve
    # asagi-ice dogru egik - agiz kosesine dogru kaybolur. Duz yatay
    # olsaydi "yanakta bant" gibi okunurdu.
    for k in range(4):
        y = CHEEK + 1 + k
        inset = k * 1.2
        _shade_skin(canvas, spec, FACE_CX + cheek * 0.20 + inset,
                    FACE_CX + cheek * 0.50 - k * 0.5, y, -force)
        # Sol taraf isik aliyor, o yuzden yalnizca bir basamak.
        _shade_skin(canvas, spec, FACE_CX - cheek * 0.50 + k * 0.5,
                    FACE_CX - cheek * 0.26 - inset * 0.4, y, -1)

    # --- Burun: koprunun iki yani ayri duzlem ---------------------------
    # Referansin *"burun koprusu ve ucu ayrimi onemli"* maddesi.
    bridge_top = EYE + spec.eye_drop - 1
    for y in range(bridge_top, NOSE_BASE):
        _shade_skin(canvas, spec, FACE_CX - spec.nose_width * 0.5 - 1,
                    FACE_CX - 1, y, +1)          # sirtin solu: isik
        _shade_skin(canvas, spec, FACE_CX + 1,
                    FACE_CX + spec.nose_width * 0.5 + 1, y, -force)
    # Kanat golgeleri - burnun tabanini yuzden ayiran sey.
    _shade_skin(canvas, spec, FACE_CX - spec.nose_width - 1,
                FACE_CX - spec.nose_width, NOSE_BASE, -1)
    _shade_skin(canvas, spec, FACE_CX + spec.nose_width,
                FACE_CX + spec.nose_width + 1, NOSE_BASE, -force)

    # --- Dudak alti: agzi hacimli yapan --------------------------------
    _shade_skin(canvas, spec, FACE_CX - spec.mouth_width * 0.28,
                FACE_CX + spec.mouth_width * 0.34,
                MOUTH + spec.lip_fullness + 1, -force)

    # --- Cene hatti ve alti ---------------------------------------------
    # `docs` disi bir uyari: burasi bir zamanlar `step=0` ile
    # boyaniyordu ve Rey **sakalli** gorunuyordu (Arda, 30.08.2026).
    # `_draw_head` o dersi ogrendi; burada da bir basamaktan fazla
    # inilmiyor.
    for y in range(JAW, CHIN + 1):
        half = _half_width(spec, y)
        _shade_skin(canvas, spec, FACE_CX + half * 0.35, FACE_CX + half,
                    y, -1)
    # Cenenin ucu isik aliyor - yuzu one cikaran son vurgu.
    _shade_skin(canvas, spec, FACE_CX - spec.chin_width * 0.30,
                FACE_CX + spec.chin_width * 0.10, CHIN - 1, +1)

    # --- Cok hafif genel yon ---------------------------------------------
    # Isigin sol-ustten geldigi hala okunmali ama yuzu **ikiye
    # bolmemeli**: yalnizca en dis serit, tek basamak.
    for y in range(BROW, JAW):
        half = _half_width(spec, y)
        _shade_skin(canvas, spec, FACE_CX + half * 0.80, FACE_CX + half,
                    y, -1)


# =============================================================================
# Yuz detaylari
# =============================================================================
def _draw_brows(canvas: Canvas, spec: PortraitSpec) -> None:
    """Kas - ifadenin tasiyicisi.

    `brow_angle` isareti karakteri belirliyor: ic uc YUKARIDA = acik ve
    sempatik (Rey), ic uc ASAGIDA = catik ve ciddi (Ardo). Tek sayinin
    isareti, iki farkli ifade.
    """
    y0 = BROW + spec.brow_drop
    for side in (-1, 1):
        for i in range(spec.brow_length):
            x = int(FACE_CX + side * (spec.eye_gap - 1 + i))
            t = i / max(1, spec.brow_length - 1)
            # Ic uc: `brow_angle` kadar kaydir; dis uca dogru duzelt.
            y = y0 - int(round(spec.brow_angle * (1.0 - t)))
            # Dis uc hafif asagi kivrilir - duz kas "cizgi" gibi durur.
            y += int(t * t * 1.6)
            for k in range(spec.brow_thickness):
                # Ic yarisi kalin/koyu, dis yarisi incelir - gercek kas
                # boyle. Sabit kalinlik "kalem cizgisi" gibi okunuyor.
                if t > 0.75 and k > 0:
                    continue
                canvas.px(x, y + k, spec.hair, 0 if t < 0.5 else 1)


def _draw_eyes(canvas: Canvas, spec: PortraitSpec) -> None:
    """Goz: kapak + sklera + iris + pupil + highlight.

    Bes katman, her biri ayri bir is yapiyor:
      * **ust kapak**  koyu cizgi - bakisin agirligi buradan
      * **sklera**     acik alan; gozu "delik" degil "kure" yapar
      * **iris**       renk - karakterin kimligi
      * **pupil**      irisin icinde tek koyu piksel
      * **highlight**  sol-ustte tek parlak piksel - CANLILIK bu

    Highlight sol-ustte cunku isik orada (`forge` LIGHT_DX/DY). Isikla
    tutarsiz bir highlight gozu cam boncuga cevirir.
    """
    y0 = EYE + spec.eye_drop
    for side in (-1, 1):
        # Dogal hafif asimetri: sag goz bir piksel asagida.
        base = y0 + (1 if side > 0 else 0)
        inner = int(FACE_CX + side * spec.eye_gap)

        for i in range(spec.eye_width):
            x = inner + side * i
            t = i / max(1, spec.eye_width - 1)
            top = base - int(round(spec.eye_tilt * t))
            # Sklera - uclarda bir piksel kisalir (badem sekli).
            height = spec.eye_height - (1 if t > 0.82 else 0)
            for y in range(top, top + max(1, height)):
                canvas.px(x, y, "bone_pale", 2)
            # Ust kapak / kirpik
            for k in range(spec.lid_weight):
                canvas.px(x, top - 1 - k, spec.hair, 0)
            # Alt kapak: tenden bir ton koyu, siyah DEGIL - siyah olsaydi
            # goz cerceveli ve yorgun okunurdu.
            canvas.px(x, top + max(1, height), spec.skin, 1)

        # Iris: ic koseye hafif kaymis (bakis one dogru).
        iris_x = inner + side * max(1, spec.eye_width // 2)
        iris_top = base - int(round(spec.eye_tilt * 0.5))
        iris_h = max(2, spec.eye_height - 1)
        canvas.fill_rect(iris_x - 1, iris_top, 2, iris_h,
                         spec.iris_chain, spec.iris_step)
        # Pupil - irisin ortasinda.
        canvas.px(iris_x, iris_top + iris_h // 2, "shadow", 0)
        # Highlight - TEK piksel, sol ustte.
        canvas.px(iris_x - 1, iris_top, "bone_pale", 3)

        # Dis kose: gozu kapatan koyu piksel.
        canvas.px(inner + side * spec.eye_width,
                  base - spec.eye_tilt, spec.hair, 1)
        # Goz cukurunun golgesi - kasin altinda, gozun ustunde.
        canvas.px(inner + side * (spec.eye_width // 2),
                  base - spec.lid_weight - 2, spec.skin, 1)


def _draw_nose(canvas: Canvas, spec: PortraitSpec) -> None:
    """Burun: kisa sirt + uc kumesi + kanat golgeleri.

    Arda: *"Burun icin kucuk ama gercekci bir pixel cluster kullan."*
    Ilk surumde sirt 8 piksel boyunca iki dikey cizgiydi ve "cubuk" gibi
    okunuyordu. Gercek cozum: **sirt kisa ve yalnizca GOLGE tarafi
    ciziliyor**, hacmi uc kumesi veriyor.

    Isik sol-ustten geldigi icin burnun solunda hicbir sey cizmiyoruz -
    orasi zaten yuzun aydinlik duzlemi. Sag tarafta tek piksellik bir
    golge sutunu burnu yuzden ayirmaya yetiyor.
    """
    cx = int(FACE_CX)
    top = NOSE_BASE - spec.nose_bridge
    # Sirtin golge tarafi - kisa, ve asagi indikce disa aciliyor.
    for i in range(spec.nose_bridge):
        y = top + i
        offset = 1 + i // 3
        canvas.px(cx + offset, y, spec.skin, 1)

    # Uc: kucuk acik kume (isik burnun ucunda toplanir).
    canvas.fill_rect(cx - 1, NOSE_BASE - 1, 2, 1, spec.skin, 3)
    canvas.px(cx, NOSE_BASE, spec.skin, 2)

    # Kanatlar - iki yanda birer koyu piksel. Burnu "cizik" olmaktan
    # cikaran sey bu iki piksel.
    half = max(1, spec.nose_width // 2)
    canvas.px(cx - half - 1, NOSE_BASE, spec.skin, 1)
    canvas.px(cx + half + 1, NOSE_BASE, spec.skin, 0)
    # Burun altinin golgesi - filtrum'un ustu.
    canvas.fill_rect(cx - half, NOSE_BASE + 1, spec.nose_width, 1, spec.skin, 1)


def _draw_mouth(canvas: Canvas, spec: PortraitSpec) -> None:
    """Agiz: ust dudak + acilma cizgisi + alt dudak + cene golgesi.

    Arda: *"Agiz tek bir yatay cizgi gibi gorunmesin; dudak ve golge
    ayrimi cok kucuk piksel kumeleriyle verilsin."*

    Dort satir, her biri bir is yapiyor:
      -1  ust dudak      isigi az alir (yuze dik durur)
       0  acilma cizgisi en koyu; ortada kalin, uclarda incelir
      +1  alt dudak      isigi ALIR - hacmi bu veriyor
      +2  dudak alti     golge; ceneyi one cikarir
    """
    half = spec.mouth_width // 2
    cx = int(FACE_CX)         # asimetri agizda degil gozde - ikisi birden
    y = MOUTH                 # olursa yuz "carpik" okunuyor

    # Acilma cizgisi TEN ZINCIRINDE degil `leather` step 0'da: ten
    # zincirinin en koyusu (`earth_dark`) yanaktan yalnizca bir basamak
    # koyu ve agiz kayboluyordu. Dudak bosluğu tenden ayri bir madde -
    # ayri zincir dogru okunuyor.
    for i in range(-half, half + 1):
        t = abs(i) / max(1, half)
        x = cx + i
        # Ust dudak yalnizca ORTADA ve bir ton acik: nerdeyse tam
        # genislikte ve koyu oldugunda acilma cizgisiyle birlesip
        # "biyik" gibi kalin bir bant okunuyordu.
        if t < 0.68:
            canvas.px(x, y - 1, spec.skin, 2)          # ust dudak
        # Acilma: ortada koyu, uclarda incelip tene karisiyor.
        # `leather` step 1 (step 0 degil): 0 neredeyse siyahti ve agiz
        # "biyik" gibi kalin bir cubuk okunuyordu. 1 hala tenden acikca
        # koyu ama dudak gibi duruyor.
        if t < 0.58:
            canvas.px(x, y, "leather", 1)
        else:
            canvas.px(x, y, spec.skin, 1)
        if t < 0.70:
            for k in range(spec.lip_fullness):
                canvas.px(x, y + 1 + k, spec.skin, 3)  # alt dudak (isikli)
        if t < 0.52:
            canvas.px(x, y + 1 + spec.lip_fullness, spec.skin, 1)

    # Koseler - agza ifade veren iki piksel.
    canvas.px(cx - half - 1, y, "leather", 1)
    canvas.px(cx + half + 1, y, "leather", 0)


def _draw_stubble(canvas: Canvas, spec: PortraitSpec) -> None:
    """Cene sakali golgesi - cene hattini sertlestirir.

    **Seyrek dagilim**, dikey cizgiler degil: ilk surumde `x*7+y*3` deseni
    dikey seritler uretiyordu ve "parmaklik" gibi okunuyordu.
    """
    if spec.stubble <= 0:
        return
    skin_id = Canvas._chain_id(spec.skin)
    for y in range(MOUTH + 2, CHIN + 1):
        half = _half_width(spec, y)
        for x in range(int(FACE_CX - half) + 1, int(FACE_CX + half)):
            if canvas.chain[y, x] != skin_id:
                continue
            # Sahte-rastgele ama SABIT desen; dikey/yatay hizalanmiyor.
            if ((x * 13 + y * 29) % 7) < 3:
                canvas.step[y, x] = max(0, int(canvas.step[y, x]) - 1)
    # Ust dudak golgesi - biyik izi.
    for x in range(int(FACE_CX) - 3, int(FACE_CX) + 4):
        if ((x * 5) % 3) < 2:
            canvas.px(x, MOUTH - 2, spec.skin, 1)


# =============================================================================
# Sac
# =============================================================================
def _hair_half(spec, y: int) -> float:
    """Sac kutlesinin `y` satirindaki yari genisligi.

    Kafanin profilini takip eder ama **kalinlik** ekler - sac derisi
    ustunde duran bir hacim. Tepede kalinlik en fazla (sac orada
    kabariyor), sakaklarda azaliyor.
    """
    top = CROWN - spec.hair_volume
    if y < top:
        return 0.0
    if y < CROWN:
        # Kafatasinin ustundeki kubbe.
        t = (y - top) / max(1, CROWN - top)
        base = _half_width(spec, CROWN) + spec.hair_volume * 0.7
        return base * (t * (2.0 - t)) ** 0.5
    thick = spec.hair_volume * 0.55 if y < BROW else spec.hair_volume * 0.35
    return _half_width(spec, y) + thick


def _draw_hair_back(canvas: Canvas, spec: PortraitSpec) -> None:
    """Yuzun ARKASINDA kalan kutle - uzun sac omuzlara iner.

    Once ciziliyor ki yuz ve govde onun uzerine binsin. Kutle cene
    hizasinda **toplanip** omuzlarda tekrar aciliyor: dik bir dikdortgen
    "sac" degil "pelerin" gibi okunur.
    """
    if spec.hair_length <= 0:
        return
    bottom = min(HEIGHT - 1, CHIN + spec.hair_length)
    for y in range(CROWN - spec.hair_volume, bottom + 1):
        if y <= CHIN:
            half = _hair_half(spec, y) + 1.5
        else:
            t = (y - CHIN) / max(1, bottom - CHIN)
            half = spec.skull_width * 0.5 + 2.5 - 2.0 * t + 9.0 * t * t
        if half < 1.0:
            continue
        for x in range(int(FACE_CX - half), int(FACE_CX + half) + 1):
            u = (x + 0.5 - FACE_CX) / max(1.0, half)
            step = 1
            if u < -0.50:
                step = 2
            if u > 0.55:
                step = 0
            canvas.px(x, y, spec.hair, step)

    # Alt uc tutamlara ayriliyor - duz kesilmis bir kenar peruk gibi.
    for i in range(-3, 4):
        x = int(FACE_CX + i * 5)
        depth = 3 - abs(i) // 2
        for k in range(depth):
            canvas.px(x, bottom + 1 + k, spec.hair, 0)


def _draw_hair_front(canvas: Canvas, spec: PortraitSpec) -> None:
    """Kafatasinin uzeri, sac cizgisi, perce, tutamlar, highlight.

    Arda: *"Saci tek renk buyuk bir blok halinde cizme. Buyuk sac
    kutlesini olusturduktan sonra birkac ayri sac tutami ekle. Ana renk +
    shadow + light + kucuk highlight kullan. Sac cizgisi yuzle dogal
    birlessin."*

    Iki tur once burada kafatasindan yukari cikan bir "ayrim olugu"
    ciziliyordu ve portre kaskli/antenli gorunuyordu. Kaldirildi: sacin
    yonunu artik highlight yayi ve percenin egimi soyluyor - gercek sacta
    da yonu veren sey isigin nereden kaydigidir.

    Sac cizgisi bir YAY: alnin ortasi acik, sakaklar kapali. Duz bir
    cizgi peruk gibi okunuyor.
    """
    hair = spec.hair
    top = CROWN - spec.hair_volume

    # --- Ana kutle: kafatasi + sakaklar ---
    for y in range(top, BROW):
        half = _hair_half(spec, y)
        if half < 1.0:
            continue
        for x in range(int(FACE_CX - half), int(FACE_CX + half) + 1):
            u = (x + 0.5 - FACE_CX) / max(1.0, half)
            if y >= HAIRLINE:
                # Alin acikligi: sac cizgisinden asagi indikce daralan bir
                # pencere, `sweep` yonunde hafif kayik - perce oraya duser.
                depth = (y - HAIRLINE) / max(1, BROW - HAIRLINE)
                window = 0.86 - depth * 0.30
                if abs(u - spec.sweep * 0.10) < window:
                    continue
            step = 1
            if u < -0.45:
                step = 2
            if u > 0.50:
                step = 0
            canvas.px(x, y, hair, step)

    if spec.curly:
        # Kivircik: kutlenin uzerine BINEN tepe cikintilari. Siluette
        # tirtikli bir ust hat birakir - duz sactan bir bakista ayrilir.
        #
        # Kubbeler kutlenin **icine** oturuyor (yaricap kadar asagida) ve
        # birbirine deger halde. Ilk surumde ustunde ve ayrik duruyorlardi
        # ve "kafaya takilmis fiyonk" gibi okunuyordu.
        for i in range(-3, 4):
            bx = FACE_CX + i * 3.4
            by = top + 3 + abs(i) * 0.7
            canvas.disc(bx, by, 2.6, hair, 2 if i % 2 else 1)

    # --- Perce: alna dusen uc tutam ---
    # Alni TAMAMEN kapatmiyor: alin gorunmezse yuz kisalir ve karakter
    # cocuk gibi okunur (Arda: "cocuk gibi veya chibi gorunmesin").
    for i in range(3):
        sx = int(FACE_CX + spec.sweep * (2 + i * 4))
        for k in range(spec.fringe_depth + i):
            x = sx - spec.sweep * (k // 2)
            canvas.px(x, HAIRLINE - 1 + k, hair, 1 if k % 2 else 2)

    # --- Highlight yayi: kafatasinin egrisini takip eder ---
    # Duz cizgi "beyaz serit" olur; egri olunca "parlak sac" okunur.
    for i in range(11):
        t = i / 10.0
        hx = int(FACE_CX + spec.sweep * (2 + t * 11))
        hy = int(top + 1 + t * t * 8)
        canvas.px(hx, hy, hair, 3)
        canvas.px(hx, hy + 1, hair, 2)

    # --- Yandan inen tutamlar: yuzu cerceveler ---
    # Govdenin ONUNDE duruyor, o yuzden `_draw_body`'den SONRA ciziliyor.
    if spec.hair_side > 0:
        for side in (-1, 1):
            base_x = FACE_CX + side * (spec.skull_width * 0.5 + 1)
            for k in range(spec.hair_side):
                t = k / max(1, spec.hair_side - 1)
                x = int(base_x + side * (t * t * 3))     # asagida disa acilir
                y = HAIRLINE + 1 + k
                canvas.px(x, y, hair, 2 if k < 2 else 1)
                canvas.px(x + side, y, hair, 0)


# =============================================================================
# Govde
# =============================================================================
def _draw_body(canvas: Canvas, spec: PortraitSpec) -> None:
    """Boyun, omuzlar, yaka - portrenin tasiyicisi.

    Omuz genisligi anatomiyi soyluyor: Rey dar ve dengeli, Ardo genis ve
    agir. Bust'un alt kenari kesilmis gibi bitiyor - bu bir kadraj, tam
    boy figur degil.

    Omuz cizgisi duz degil, kola dogru yuvarlanan bir yay: duz bir trapez
    "dag" gibi okunuyordu.
    """
    # Boyun **dar**: cene genisliginin altinda kalmali. Genis bir boyun
    # portreyi "agac govdesi" gibi okutuyor. Ust kismi cene golgesinde,
    # asagi indikce isik aliyor - duz koyu bir sutun hacimsiz duruyordu.
    neck_half = max(3, spec.chin_width // 2)
    for y in range(NECK_TOP, SHOULDER + 2):
        v = (y - NECK_TOP) / max(1, SHOULDER + 2 - NECK_TOP)
        for x in range(int(FACE_CX - neck_half), int(FACE_CX + neck_half) + 1):
            u = (x + 0.5 - FACE_CX) / neck_half
            step = 1 if u < 0.0 else 0
            if v > 0.55 and u < -0.3:
                step = 2                 # cene golgesinin altinda isik
            canvas.px(x, y, spec.skin, step)
    # Cenenin boyuna dusen golgesi - kafayi one cikaran sey.
    canvas.fill_rect(int(FACE_CX - neck_half), NECK_TOP, neck_half * 2 + 1, 2,
                     spec.skin, 0)
    # Boyun kirisi: bir piksellik acik cizgi. Boynu silindir yapan sey.
    for k in range(SHOULDER + 2 - NECK_TOP - 2):
        canvas.px(int(FACE_CX - neck_half + 1), NECK_TOP + 2 + k,
                  spec.skin, 2)
    # Trapez kasi: boynu omuza baglayan egik cizgi. Onsuz kafa govdeye
    # "yapistirilmis" gorunuyor.
    for side in (-1, 1):
        for k in range(6):
            canvas.px(int(FACE_CX + side * (neck_half + k)),
                      SHOULDER - 4 + k, spec.skin, 0)

    # --- Omuzlar ---
    span = spec.shoulder_span
    for y in range(SHOULDER, HEIGHT):
        t = (y - SHOULDER) / max(1, HEIGHT - SHOULDER)
        # Ust kismi hizli acilir (trapez), sonra yavaslar (kol basi).
        half = 9 + span * (t ** 0.45)
        for x in range(max(0, int(FACE_CX - half)),
                       min(WIDTH, int(FACE_CX + half) + 1)):
            u = (x + 0.5 - FACE_CX) / max(1.0, half)
            step = 1
            if u < -0.30:
                step = 2
            if u > 0.40:
                step = 0
            if abs(u) > 0.88:
                step = 0                    # kolun dis kenari
            canvas.px(x, y, spec.cloth, step)

    # Yaka - boynun iki yanindan inen V. Ic kenari acik ki kumasin
    # katlandigi okunsun.
    for k in range(11):
        for side in (-1, 1):
            x = int(FACE_CX + side * (neck_half + 1 + k * 0.6))
            canvas.px(x, SHOULDER + k, spec.cloth, 0)
            canvas.px(x - side, SHOULDER + k, spec.cloth, 2)

    if spec.shoulder_pads:
        # Omuzluk bir **kapak**: omzun tepesine oturan kucuk, yuvarlak
        # bir parca. Iki tur once bust'un altina kadar iniyordu ve iki dev
        # beyaz serit gibi gorunuyordu; sonra genisligi tuvali tasip
        # dikdortgene kirpilmisti. Artik omuz cizgisinin GECTIGI yere
        # oturan bir elips - once o nokta hesaplaniyor, sonra kapak
        # oraya konuyor.
        pad_cy = SHOULDER + 7
        t_at = (pad_cy - SHOULDER) / max(1, HEIGHT - SHOULDER)
        edge = 9 + span * (t_at ** 0.45)      # omzun dis kenari
        # Kapak omzun UZERINE biniyor: merkezi kenardan iceride, yani
        # yarisi govdeyle cakisiyor. Kenarda dursaydi "havada top" gibi
        # ayri okunurdu - once oyle cizildi ve tam oyle gorundu.
        pad_cx = edge - 6.0
        rx, ry = 6.5, 5.0
        for side in (-1, 1):
            for dy in range(-int(ry), int(ry) + 1):
                for dx in range(-int(rx), int(rx) + 1):
                    n = (dx / rx) ** 2 + (dy / ry) ** 2
                    if n > 1.0:
                        continue
                    x = int(FACE_CX + side * (pad_cx + dx))
                    y = pad_cy + dy
                    # Kurk dokusu: ust-ic acik, alt-dis koyu.
                    step = 2 if side < 0 else 1
                    if n > 0.66:
                        step = 0
                    elif dy < -1 and dx < 1:
                        step = 3
                    canvas.px(x, y, spec.shoulder_chain, step)

    if spec.tattoo:
        # Sag kopruculuk altinda geyik dovmesi (DEVIR 3.7 kanonu).
        # Portrede bir isaret; tam sekil bu olcude okunmaz.
        for dx, dy in ((0, 2), (1, 1), (2, 0), (3, 1), (4, 2),
                       (2, 1), (2, 2), (2, 3)):
            canvas.px(int(FACE_CX + 8 + dx), SHOULDER + 9 + dy,
                      spec.accent, 2)


def draw_portrait(spec: PortraitSpec) -> Canvas:
    """Bir portreyi tam olarak cizer. Sira modul basliginda acikliniyor."""
    canvas = Canvas(WIDTH, HEIGHT)

    _draw_hair_back(canvas, spec)
    _draw_body(canvas, spec)
    _draw_head(canvas, spec)
    _apply_face_planes(canvas, spec)

    _draw_brows(canvas, spec)
    _draw_eyes(canvas, spec)
    _draw_nose(canvas, spec)
    _draw_mouth(canvas, spec)
    _draw_stubble(canvas, spec)

    _draw_hair_front(canvas, spec)

    canvas.outline("shadow", 0)
    return canvas


# =============================================================================
# Kadro
# =============================================================================
# Rey - zarif, genc yetiskin, yumusak ama guclu hatlar.
#
# Ayarlar karakteri tasiyor: dar cene + yuksek elmacik (zarif), yukari
# cekik badem goz (canli), ic ucu YUKARIDA kas (acik/sempatik), dolgun
# alt dudak. Uzun koyu sac, mavi kiyafet - DEVIR 3.7 kanonu.
REY_PORTRAIT = PortraitSpec(
    name="rey",
    skull_width=29, cheek_width=28, jaw_width=20, chin_width=8,
    eye_width=5, eye_height=3, eye_gap=3, eye_tilt=1, lid_weight=1,
    iris_chain="leather", iris_step=2,      # sicak kahve - esmer kanonu
    brow_thickness=1, brow_length=7, brow_angle=1,
    nose_width=3, nose_bridge=4,
    mouth_width=7, lip_fullness=2,
    hair_volume=5, hair_length=26, hair_side=22, fringe_depth=3, sweep=-1,
    face_shadow=0, shoulder_span=18,
    skin="skin_tan", hair="hair_dark", cloth="cloth_blue", accent="gore",
    tattoo=True,
)

# Ardo - yakisikli ama sert; guclu cene, dar ve golgeli bakis.
#
# Zit ayarlar: genis cene (kare hat), duz ve kalin kapakli goz (agir
# bakis), ic ucu ASAGIDA kas (catik), ince dudak, sakal golgesi.
# `face_shadow=1` yuzun sag yarisini bir basamak dusuruyor - "yuzun bir
# kismi golgede, gizemli ve tehlikeli".
#
# Kukulete YOK (DEVIR 3.7): golge yuzden geliyor, kapusondan degil.
ARDO_PORTRAIT = PortraitSpec(
    name="ardo",
    skull_width=31, cheek_width=30, jaw_width=25, chin_width=12,
    eye_width=5, eye_height=2, eye_gap=4, eye_tilt=0, lid_weight=2,
    eye_drop=1,
    iris_chain="steel", iris_step=2,        # soguk gri - mesafeli bakis
    brow_thickness=2, brow_length=8, brow_angle=-1, brow_drop=1,
    nose_width=4, nose_bridge=5,
    mouth_width=8, lip_fullness=1,
    hair_volume=3, hair_length=0, hair_side=5, fringe_depth=2, sweep=1,
    face_shadow=1, stubble=1, shoulder_span=26,
    skin="skin_tan", hair="hair_dark", cloth="cloth_grey", accent="leather",
    shoulder_pads=True, shoulder_chain="bone_pale",
)

# Cemo - Rey'in kucuk kardesi. Cocuk hatlari ama **chibi degil**: goz
# biraz iri, cene daha yumusak, burun kisa. Kivircik sac (DEVIR 3.7).
CEMO_PORTRAIT = replace(
    REY_PORTRAIT,
    name="cemo",
    skull_width=28, cheek_width=27, jaw_width=21, chin_width=10,
    eye_width=6, eye_height=4, eye_gap=3, eye_tilt=1,
    brow_thickness=1, brow_length=6, brow_angle=1, brow_drop=1,
    nose_width=3, nose_bridge=3,
    mouth_width=6, lip_fullness=1,
    hair_volume=6, hair_length=0, hair_side=4, fringe_depth=4, sweep=1,
    curly=True, shoulder_span=14,
    cloth="leather", tattoo=False,
)

PORTRAITS: dict[str, PortraitSpec] = {
    "rey": REY_PORTRAIT,
    "ardo": ARDO_PORTRAIT,
    "cemo": CEMO_PORTRAIT,
}

_cache: dict[str, pygame.Surface] = {}


# Elle cizilmis portrelerin arandigi yer. Dosya varsa **prosedurel
# uretimin yerine gecer**.
HAND_DRAWN_DIR = Path(__file__).resolve().parents[2] / "assets" / "portraits"

# Palet disi piksel bulununca bir kez uyar - her karede degil.
_warned: set[str] = set()


def _load_hand_drawn(name: str) -> pygame.Surface | None:
    """`assets/portraits/<ad>.png` varsa onu yukler.

    ## Neden bir gecersiz kilma yolu var

    Arda 31.08.2026'da referans getirdi ve prosedurel portrelerin
    tavani gorundu: bir iskeletten turetilen yuz, elle cizilmis bir
    yuzun tasidigi **niyeti** tasiyamiyor. Kas kaldirmak, dudak
    kenarini kirmak, gozun icine ucuncu bir ton koymak - bunlar
    kural degil karar.

    O yuzden kod uretimi **taban** oldu, elle cizim **ust**: dosya
    yoksa oyun calisiyor (hicbir sey bozulmuyor), dosya varsa daha
    iyi gorunuyor. Bir portre cizilene kadar oteki karakterler
    prosedurel kaliyor - hepsini birden bitirmek gerekmiyor.

    `CLAUDE.md` 6 baglayici: *"Kaynagi ne olursa olsun - kod, elle
    cizim, harici arac - her gorsel `tools/quantize.py` filtresinden
    gecer."* Burada dosya **degistirilmiyor** ama palet disi renk
    varsa uyariliyor: sessizce kabul etmek o kurali delerdi,
    calisma zamaninda quantize etmek ise her acilista maliyet olurdu.
    """
    path = HAND_DRAWN_DIR / f"{name}.png"
    if not path.exists():
        return None
    try:
        image = pygame.image.load(str(path)).convert_alpha()
    except pygame.error:
        return None

    if image.get_size() != (WIDTH, HEIGHT) and name not in _warned:
        _warned.add(name)
        print(f"[portre] {path.name}: {image.get_size()} - beklenen "
              f"{(WIDTH, HEIGHT)}. Oyun yine de kullaniyor ama olcek "
              f"kayabilir.")

    if name not in _warned:
        off = _off_palette(image)
        if off:
            _warned.add(name)
            print(f"[portre] {path.name}: {off} piksel palet disi. "
                  f"Duzeltmek icin: python tools/quantize.py "
                  f"assets/portraits/{name}.png")
    return image


def _off_palette(image: pygame.Surface) -> int:
    """Kac piksel 37 rengin disinda. Sifir olmali."""
    import numpy as np
    rgb = pygame.surfarray.array3d(image)
    alpha = pygame.surfarray.array_alpha(image)
    allowed = {tuple(c) for c in palette.COLORS.values()}
    solid = rgb[alpha > 8]
    if solid.size == 0:
        return 0
    return sum(1 for c in solid if tuple(int(v) for v in c) not in allowed)


def portrait(name: str) -> pygame.Surface | None:
    """Bir karakterin portresi. Elle cizilmis varsa o, yoksa uretilmis.

    Sonuc onbellege aliniyor; `clear_cache()` (palet/dil degisimi)
    ikisini birden temizliyor.
    """
    cached = _cache.get(name)
    if cached is not None:
        return cached

    drawn = _load_hand_drawn(name)
    if drawn is not None:
        _cache[name] = drawn
        return drawn

    spec = PORTRAITS.get(name)
    if spec is None:
        return None
    surface = draw_portrait(spec).resolve()
    _cache[name] = surface
    return surface

def clear_cache() -> None:
    _cache.clear()
